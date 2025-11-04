import sys
import requests
import pandas as pd
import yfinance as yf
import mplfinance as mpf
import json
import math as m
import time
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QLineEdit, QListWidget, QListWidgetItem, QLabel,
                             QStackedWidget, QHBoxLayout, QPushButton, QSplitter, QStyle,
                             QButtonGroup, QScrollArea, QDialog)
from PyQt6.QtCore import (Qt, QThread, pyqtSignal, QTimer, QSize, QUrl, pyqtSlot, 
                          QRect, QEvent) # Aggiunto QRect, QEvent, pyqtSlot
from PyQt6.QtGui import (QMovie, QIcon, QDesktopServices)

# Matplotlib integration for PyQt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

# --- 1. IMPORTA MODULI ADD-ON ---
try:
    import rsi
except ImportError:
    print("ERRORE: Impossibile trovare il file 'rsi.py'.")
    rsi = None

try:
    import news # Importa il modulo news.py
except ImportError:
    print("ERRORE: Impossibile trovare il file 'news.py'.")
    news = None

# Lazy import per model - verrà caricato solo quando necessario
# Questo evita errori di import se PyTorch non è disponibile o ha problemi
model = None
def load_model():
    """Carica il modulo model.py in modo lazy."""
    global model
    if model is not None:
        return model
    try:
        import model as _model
        model = _model
        return model
    except ImportError:
        print("AVVISO: Impossibile trovare il file 'model.py'. L'analisi delle notizie sarà disabilitata.")
        model = None
        return None
    except Exception as e:
        print(f"AVVISO: Errore durante il caricamento del modulo 'model.py': {e}")
        print("L'analisi delle notizie sarà disabilitata.")
        model = None
        return None
    
try:
    # Importa i nuovi widget UI dal file settings_view.py
    from settings_view import SettingsDialog, NewsSidebar, NewsCard, FlyoutNewsFeed
except ImportError:
    print("ERRORE: Impossibile trovare il file 'settings_view.py'.")
    sys.exit()

# --- STYLESHEET PROFESSIONALE (COMPLETO) ---
STYLESHEET = """
    QWidget {
        background-color: #1e1e1e;
        color: #dcdcdc;
        font-family: 'Segoe UI', Arial, sans-serif;
        font-size: 15px;
    }
    QMainWindow {
        border: 1px solid #333333;
    }
    QLineEdit {
        background-color: #2d2d2d;
        border: 1px solid #444444;
        border-radius: 5px;
        padding: 8px;
    }
    QLineEdit:focus {
        border: 1px solid #007acc;
    }
    QListWidget {
        background-color: #2d2d2d;
        border: 1px solid #444444;
        border-radius: 5px;
    }
    QListWidget::item {
        padding: 12px 8px;
    }
    QListWidget::item:hover {
        background-color: #3a3a3a;
    }
    QListWidget::item:selected {
        background-color: #007acc;
        color: #ffffff;
    }
    QPushButton {
        background-color: #3c3c3c;
        color: #dcdcdc;
        border: 1px solid #555555;
        padding: 8px 16px;
        border-radius: 5px;
    }
    QPushButton:hover {
        background-color: #4a4a4a;
        border-color: #666666;
    }
    QPushButton#RemoveButton {
        background-color: #5a2a27;
    }
    QPushButton#RemoveButton:hover {
        background-color: #7a3a37;
    }
    QLabel#TitleLabel {
        font-size: 28px;
        font-weight: bold;
        color: #f0f0f0;
        padding-top: 20px;
    }
    QLabel#InfoLabel {
        font-size: 18px;
        color: #888888;
    }
    QLabel#PanelTitle {
        font-size: 18px;
        font-weight: bold;
        padding: 8px 0px;
        border-bottom: 1px solid #444444;
    }
    QSplitter::handle {
        background-color: #333333;
    }
    QSplitter::handle:hover {
        background-color: #007acc;
    }
    
    /* Stile per i pulsanti Timeframe e ChartType */
    QPushButton#TimeframeButton {
        padding: 6px 10px;
        font-size: 13px;
        border-radius: 4px;
        border: 1px solid #333;
    }
    QPushButton#TimeframeButton:hover {
        background-color: #4a4a4a;
    }
    QPushButton#TimeframeButton:checked {
        background-color: #007acc;
        color: #ffffff;
        border-color: #007acc;
    }
    
    /* Stile per pulsanti Icona */
    QPushButton#IconButton {
        padding: 5px;
        border-radius: 4px;
        border: 1px solid #333;
    }
    QPushButton#IconButton:hover {
        background-color: #4a4a4a;
    }
    QPushButton#IconButton:checked {
        background-color: #007acc;
        border-color: #007acc;
    }
"""

SETTINGS_FILE = 'settings.json'

# --- Worker Threads (SearchWorker, DataWorker, NewsWorker) ---
class SearchWorker(QThread):
    results_ready = pyqtSignal(list)
    error = pyqtSignal(str)
    def __init__(self, query):
        super().__init__()
        self.query = query
    def run(self):
        if not self.query:
            self.results_ready.emit([])
            return
        try:
            url = f"https://query1.finance.yahoo.com/v1/finance/search?q={self.query}"
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            results = [
                quote for quote in data.get('quotes', [])
                if quote.get('quoteType') in ['EQUITY', 'ETF', 'CRYPTOCURRENCY', 'FUTURE']
            ]
            self.results_ready.emit(results)
        except Exception as e:
            self.error.emit(f"Search failed: {e}")

class DataWorker(QThread):
    data_ready = pyqtSignal(pd.DataFrame, str)
    error = pyqtSignal(str)
    
    def __init__(self, ticker, timeframe_params):
        super().__init__()
        self.ticker = ticker
        self.timeframe_params = timeframe_params
    def run(self):
        try:
            tk = yf.Ticker(self.ticker)
            data = tk.history(**self.timeframe_params)
            
            if data.empty:
                raise ValueError("No data returned from yfinance.")
            if self.timeframe_params.get("interval", "1d").endswith(("m", "h")):
                try:
                    data.index = data.index.tz_convert(None)
                except TypeError:
                    pass
            ohlcv_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            for col in ohlcv_columns:
                if col in data.columns:
                    data[col] = pd.to_numeric(data[col], errors='coerce')
            data.dropna(inplace=True)
            if data.empty:
                raise ValueError("No valid data found for this ticker after cleaning.")
            self.data_ready.emit(data, self.ticker)
        except Exception as e:
            self.error.emit(f"Failed to get data for {self.ticker}: {e}")

class NewsAnalysisWorker(QThread):
    """Worker thread per analizzare le notizie con il modello AI."""
    analysis_complete = pyqtSignal(dict)  # Emette il news_item con trading_signal aggiunto
    
    def __init__(self, news_item, trading_model=None):
        super().__init__()
        self.news_item = news_item
        self.trading_model = trading_model
    
    def run(self):
        if not self.trading_model or not self.trading_model.model:
            # Se il modello non è disponibile, emetti il news_item senza analisi
            self.analysis_complete.emit(self.news_item)
            return
        
        try:
            # Ottieni il testo della notizia
            news_text = self.news_item.get('text', '')
            news_link = self.news_item.get('link', '')
            ticker = self.news_item.get('ticker', '')
            
            # Se non c'è testo, prova a recuperarlo dall'URL
            if not news_text and news_link:
                news_text = self.trading_model.check_url(news_link)
            
            # Se ancora non c'è testo, usa il titolo
            if not news_text:
                news_text = self.news_item.get('title', '')
            
            # Analizza il trading signal
            if news_text:
                trading_signal = self.trading_model.analyze_trading_signal(news_text, ticker)
                self.news_item['trading_signal'] = trading_signal
                print(f"[NewsAnalysis] Analisi completata per {ticker}: {trading_signal.get('direction')} ({trading_signal.get('confidence')}%)")
            
            self.analysis_complete.emit(self.news_item)
        except Exception as e:
            print(f"[NewsAnalysis] Errore durante l'analisi: {e}")
            # Emetti il news_item senza analisi in caso di errore
            self.analysis_complete.emit(self.news_item)

class NewsWorker(QThread):
    new_news_signal = pyqtSignal(dict)
    
    def __init__(self, tickers):
        super().__init__()
        self.tickers = tickers
        self.running = True
        self.seen_links = set()
        self.is_first_run = True
        
    def run(self):
        if not news: 
            print("[NewsWorker] Modulo 'news.py' non trovato. Thread interrotto.")
            return
            
        print(f"[NewsWorker] Avviato. Controllo per {len(self.tickers)} ticker ogni 5 minuti.")
        
        while self.running:
            try:
                data_pool = news.fetch_all_news(self.tickers)
                
                new_items_found = []
                for item in data_pool:
                    link = item.get('link')
                    if link and link not in self.seen_links:
                        new_items_found.append(item)
                        self.seen_links.add(link)
                
                if self.is_first_run:
                    items_to_emit = new_items_found[:3]
                    print(f"[NewsWorker] Primo avvio. Trovate {len(items_to_emit)} notizie iniziali.")
                    self.is_first_run = False
                else:
                    items_to_emit = new_items_found
                    if items_to_emit:
                        print(f"[NewsWorker] Trovate {len(items_to_emit)} NUOVE notizie.")

                for item in reversed(items_to_emit):
                    if not self.running: break
                    self.new_news_signal.emit(item)
                    time.sleep(0.1) 
                
                for _ in range(300): # Attesa 5 minuti (300 sec)
                    if not self.running: break
                    time.sleep(1)
                    
            except Exception as e:
                print(f"[NewsWorker] Errore: {e}")
                time.sleep(60)

    def stop(self):
        self.running = False


# --- Matplotlib Canvas (Robusto) ---
class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        plt.style.use('dark_background')
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.fig.patch.set_facecolor('#1e1e1e')
        gs = self.fig.add_gridspec(5, 1)
        self.ax_price = self.fig.add_subplot(gs[0:3, 0])
        self.ax_volume = self.fig.add_subplot(gs[3, 0], sharex=self.ax_price)
        self.ax_indicator = self.fig.add_subplot(gs[4, 0], sharex=self.ax_price)
        self.ax_price.set_facecolor('#2d2d2d')
        self.ax_volume.set_facecolor('#2d2d2d')
        self.ax_indicator.set_facecolor('#2d2d2d')
        self.ax_indicator.set_visible(False)
        plt.setp(self.ax_price.get_xticklabels(), visible=False)
        plt.setp(self.ax_volume.get_xticklabels(), visible=False)
        super(MplCanvas, self).__init__(self.fig)
        self.data = None
        self.chart_type = 'candle'
        self.timeframe = '1y'
        self.cross_hline = None
        self.cross_vline = None
        self.annot = None
        self.fig.canvas.mpl_connect('motion_notify_event', self.on_motion)
        self.fig.canvas.mpl_connect('axes_leave_event', self.on_leave)
        self.ax_price.callbacks.connect('xlim_changed', self.on_xlim_changed)
        
    def set_data(self, data, chart_type, timeframe):
        self.data = data
        self.chart_type = chart_type
        self.timeframe = timeframe 

    def on_leave(self, event):
        if self.cross_hline and self.cross_hline.get_visible():
            self.cross_hline.set_visible(False)
            self.cross_vline.set_visible(False)
            self.draw_idle()
        if self.annot and self.annot.get_visible():
            self.annot.set_visible(False)
            self.draw_idle()

    def on_motion(self, event):
        if event.inaxes != self.ax_price or self.data is None or len(self.data) == 0 or self.annot is None:
            self.on_leave(event)
            return
        try:
            idx = int(round(event.xdata))
        except ValueError:
            self.on_leave(event)
            return
        if 0 <= idx < len(self.data):
            row = self.data.iloc[idx]
            if isinstance(row.name, pd.Timestamp):
                if self.timeframe in ['1d', '5d']:
                     date_str = row.name.strftime('%Y-%m-%d %H:%M')
                else:
                     date_str = row.name.strftime('%Y-%m-%d')
            else:
                date_str = str(row.name)
            price_str = ""
            if self.chart_type == 'candle':
                price_str = (f"O: {row.Open:<7.2f}   H: {row.High:<7.2f}\n"
                             f"L: {row.Low:<7.2f}   C: {row.Close:<7.2f}")
            else:
                price_str = f"Close: {row.Close:<7.2f}"
            if 'RSI' in self.data.columns and pd.notna(row['RSI']):
                price_str += f"\nRSI(14): {row['RSI']:.2f}"
            self.annot.set_text(f"{date_str}\n{price_str}")
            self.annot.xy = (idx, row.Close)
            self.annot.set_visible(True)
            self.cross_hline.set_ydata([row.Close])
            self.cross_vline.set_xdata([idx])
            self.cross_hline.set_visible(True)
            self.cross_vline.set_visible(True)
            self.draw_idle()
        else:
            self.on_leave(event)
            
    def on_xlim_changed(self, ax):
        if self.data is None or len(self.data) == 0: return
        xmin, xmax = ax.get_xlim()
        idx_min = int(m.floor(xmin)); idx_max = int(m.ceil(xmax))
        idx_min = max(0, idx_min); idx_max = min(len(self.data), idx_max)
        if idx_min >= idx_max: return
        visible_data = self.data.iloc[idx_min:idx_max]
        if visible_data.empty: return
        ymin = visible_data['Low'].min(); ymax = visible_data['High'].max()
        vmax = visible_data['Volume'].max()
        padding = (ymax - ymin) * 0.05
        if padding == 0: padding = ymin * 0.05 
        if pd.isna(ymin) or pd.isna(ymax): return
        ax.set_ylim(ymin - padding, ymax + padding)
        self.ax_volume.set_ylim(0, vmax * 1.05)
        if self.ax_indicator.get_visible() and 'RSI' in visible_data.columns:
            rsi_min = visible_data['RSI'].min(); rsi_max = visible_data['RSI'].max()
            if pd.isna(rsi_min) or pd.isna(rsi_max): return
            rsi_padding = (rsi_max - rsi_min) * 0.1
            if rsi_padding == 0: rsi_padding = 5
            self.ax_indicator.set_ylim(max(0, rsi_min - rsi_padding), min(100, rsi_max + rsi_padding))
        self.draw_idle()

# --- Main Application Window ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("The Sentient")
        try:
            self.setWindowIcon(QIcon("icona.ico"))
        except:
            print("Nessun file 'icona.ico' trovato. Icona predefinita usata.")
            
        self.setGeometry(100, 100, 1400, 800)
        self.setStyleSheet(STYLESHEET)
        
        # Abilita il tracking del mouse per la vista 3
        self.setMouseTracking(True)
        
        self.current_ticker = None
        self.current_timeframe = "1y"
        self.current_chart_type = "candle"
        self.indicators_state = {}
        self.news_worker = None
        self.analysis_workers = []  # Lista dei worker di analisi attivi
        self.trading_model = None  # Istanza condivisa del modello
        # Il modello verrà caricato in modo lazy solo quando necessario (quando arriva una notizia)
        
        # Impostazioni predefinite
        self.current_view_mode = 1 # 1:Grafico, 2:Grafico+Notizie, 3:Grafico+Flyout Notizie
        self.news_tickers = ['GC=F', 'CL=F', '^GSPC', 'NVDA', 'MSFT', 'GOOGL']
        self.flyout_popup_duration_ms = 5000  # 5 secondi per auto-hide
        
        self.timeframe_buttons = {}
        self.chart_type_buttons = {}
        
        self.timeframe_map = {
            "1d": {"period": "1d", "interval": "2m"},
            "5d": {"period": "5d", "interval": "15m"},
            "1m": {"period": "1mo", "interval": "1d"},
            "3m": {"period": "3mo", "interval": "1d"},
            "6m": {"period": "6mo", "interval": "1d"},
            "1y": {"period": "1y", "interval": "1d"},
            "5y": {"period": "5y", "interval": "1wk"},
        }

        # --- Layout Principale ---
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QHBoxLayout(central_widget)
        central_widget.setLayout(self.main_layout)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_layout.addWidget(self.splitter) 

        self.setup_left_panel()
        self.setup_right_panel()

        self.splitter.setSizes([350, 1050])
        
        # Crea la sidebar delle notizie (per vista 2)
        self.news_feed_sidebar = NewsSidebar(self)
        self.main_layout.addWidget(self.news_feed_sidebar)
        
        # Crea il flyout delle notizie (per vista 3)
        # Il flyout viene creato come widget sopra la finestra principale
        self.flyout_news_feed = FlyoutNewsFeed(self.flyout_popup_duration_ms, self)
        self.flyout_news_feed.view_toggle_requested.connect(self.on_view_toggled)
        self.flyout_news_feed.hide()

        self.setup_connections()

        # Carica le impostazioni e applica la vista
        self.load_settings()
        
        self.update_ui_states()
        
        # Avvia il worker delle notizie
        self.start_news_worker()

    def setup_left_panel(self):
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(10, 10, 10, 10)
        left_layout.setSpacing(10)
        search_layout = QHBoxLayout()
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search to add to watchlist...")
        search_layout.addWidget(self.search_bar)
        self.add_button = QPushButton()
        self.add_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton))
        self.add_button.setToolTip("Add selected to watchlist")
        search_layout.addWidget(self.add_button)
        left_layout.addLayout(search_layout)
        self.search_results_list = QListWidget()
        self.search_results_list.hide()
        left_layout.addWidget(self.search_results_list)
        watchlist_title = QLabel("My Watchlist", objectName="PanelTitle")
        left_layout.addWidget(watchlist_title)
        self.watchlist = QListWidget()
        left_layout.addWidget(self.watchlist, 1)
        self.remove_button = QPushButton(" Remove")
        self.remove_button.setObjectName("RemoveButton")
        self.remove_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon))
        left_layout.addWidget(self.remove_button)
        self.splitter.addWidget(left_panel)

    def setup_right_panel(self):
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_panel.setLayout(right_layout)
        top_bar_layout = QHBoxLayout()
        self.timeframe_group = QButtonGroup(self)
        self.timeframe_group.setExclusive(True)
        timeframes = ["1d", "5d", "1m", "3m", "6m", "1y", "5y"]
        for tf in timeframes:
            btn = QPushButton(tf); btn.setCheckable(True); btn.setObjectName("TimeframeButton")
            btn.clicked.connect(self.on_timeframe_changed); top_bar_layout.addWidget(btn)
            self.timeframe_group.addButton(btn); self.timeframe_buttons[tf] = btn
        top_bar_layout.addSpacing(30)
        self.chart_type_group = QButtonGroup(self)
        self.chart_type_group.setExclusive(True)
        chart_types = ["Candle", "Line"]
        for ct in chart_types:
            btn = QPushButton(ct); btn.setCheckable(True); btn.setObjectName("TimeframeButton")
            btn.clicked.connect(self.on_chart_type_changed); top_bar_layout.addWidget(btn)
            self.chart_type_group.addButton(btn); self.chart_type_buttons[ct.lower()] = btn
        top_bar_layout.addSpacing(30)
        self.rsi_button = QPushButton("RSI"); self.rsi_button.setCheckable(True)
        self.rsi_button.setObjectName("TimeframeButton"); self.rsi_button.clicked.connect(self.on_indicator_changed)
        top_bar_layout.addWidget(self.rsi_button)
        if rsi is None:
            self.rsi_button.setDisabled(True); self.rsi_button.setToolTip("File rsi.py non trovato")
        top_bar_layout.addStretch()
        
        self.view_button = QPushButton()
        self.view_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DesktopIcon)) # Icona default
        self.view_button.setObjectName("IconButton")
        self.view_button.setToolTip("Cambia modalità vista")
        self.view_button.clicked.connect(self.on_view_toggled)
        top_bar_layout.addWidget(self.view_button)
        
        self.settings_button = QPushButton()
        self.settings_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView))
        self.settings_button.setObjectName("IconButton")
        self.settings_button.setToolTip("Apri impostazioni")
        self.settings_button.clicked.connect(self.open_settings)
        top_bar_layout.addWidget(self.settings_button)
        right_layout.addLayout(top_bar_layout)
        
        self.stacked_widget = QStackedWidget(); right_layout.addWidget(self.stacked_widget)
        welcome_widget = QWidget(); welcome_layout = QVBoxLayout(welcome_widget)
        welcome_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title = QLabel("Portfolio Tracker", objectName="TitleLabel")
        info = QLabel("Add an asset from the search bar to begin.", objectName="InfoLabel")
        welcome_layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)
        welcome_layout.addWidget(info, alignment=Qt.AlignmentFlag.AlignCenter)
        self.stacked_widget.addWidget(welcome_widget)
        self.loading_widget = QWidget(); loading_layout = QVBoxLayout(self.loading_widget)
        loading_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_label = QLabel("Fetching data..."); self.loading_movie = QMovie("spinner.gif")
        self.loading_movie.setScaledSize(QSize(50, 50)); spinner_label = QLabel()
        spinner_label.setMovie(self.loading_movie)
        loading_layout.addWidget(spinner_label, alignment=Qt.AlignmentFlag.AlignCenter)
        loading_layout.addWidget(self.loading_label, alignment=Qt.AlignmentFlag.AlignCenter)
        self.stacked_widget.addWidget(self.loading_widget)
        self.chart_canvas = MplCanvas(self); self.stacked_widget.addWidget(self.chart_canvas)
        self.stacked_widget.setCurrentWidget(welcome_widget)
        self.splitter.addWidget(right_panel)

    def setup_connections(self):
        self.search_timer = QTimer(self); self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.start_search)
        self.search_bar.textChanged.connect(lambda: self.search_timer.start(300))
        self.search_results_list.itemClicked.connect(self.add_to_watchlist)
        self.add_button.clicked.connect(self.add_top_search_result)
        self.watchlist.currentItemChanged.connect(self.on_watchlist_selection_changed)
        self.remove_button.clicked.connect(self.remove_selected_item)

    # --- Eventi di Mouse/Finestra per Vista 3 ---
    def mouseMoveEvent(self, event):
        """Rileva quando il mouse è vicino al bordo destro per mostrare il flyout."""
        if self.current_view_mode == 3 and hasattr(self, 'flyout_news_feed'):
            window_width = self.width()
            mouse_x = event.position().x()
            edge_threshold = 50  # Pixel dal bordo destro
            
            # Se il mouse è vicino al bordo destro
            if mouse_x >= window_width - edge_threshold:
                if not self.flyout_news_feed.is_visible:
                    self.flyout_news_feed.slide_in()
                else:
                    # Se già visibile, riavvia il timer per mantenerlo visibile
                    self.flyout_news_feed.auto_hide_timer.stop()
                    self.flyout_news_feed.auto_hide_timer.start(self.flyout_popup_duration_ms)
            # Se il mouse è lontano dal flyout e dal bordo, nascondi dopo un delay
            elif mouse_x < window_width - self.flyout_news_feed.panel_width - edge_threshold:
                if self.flyout_news_feed.is_visible:
                    # Non nascondere se il mouse è sopra il flyout stesso
                    flyout_rect = self.flyout_news_feed.geometry()
                    if not flyout_rect.contains(event.position().toPoint()):
                        self.flyout_news_feed.schedule_slide_out(500)
        
        super().mouseMoveEvent(event)
    
    def resizeEvent(self, event):
        """Aggiorna la geometria del flyout quando la finestra viene ridimensionata."""
        super().resizeEvent(event)
        if hasattr(self, 'flyout_news_feed') and self.flyout_news_feed:
            if self.current_view_mode == 3:
                self.flyout_news_feed.update_geometry()

    def start_search(self):
        query = self.search_bar.text().strip()
        if not query:
            self.search_results_list.hide()
            return
        self.search_worker = SearchWorker(query)
        self.search_worker.results_ready.connect(self.show_search_results)
        self.search_worker.error.connect(self.show_error)
        self.search_worker.start()

    def show_search_results(self, results):
        self.search_results_list.clear()
        if results:
            for item in results:
                symbol = item.get('symbol', 'N/A')
                name = item.get('longname', item.get('shortname', 'No Name'))
                list_item_text = f"{symbol} - {name}"
                list_item = QListWidgetItem(list_item_text)
                list_item.setData(Qt.ItemDataRole.UserRole, item)
                self.search_results_list.addItem(list_item)
            self.search_results_list.show()
        else:
            self.search_results_list.hide()

    def add_top_search_result(self):
        if self.search_results_list.count() > 0:
            self.add_to_watchlist(self.search_results_list.item(0))
            
    def add_to_watchlist(self, item):
        data = item.data(Qt.ItemDataRole.UserRole)
        symbol = data.get('symbol')
        name = data.get('longname', data.get('shortname', 'No Name'))
        for i in range(self.watchlist.count()):
            if self.watchlist.item(i).data(Qt.ItemDataRole.UserRole)['symbol'] == symbol:
                self.search_bar.clear()
                self.search_results_list.hide()
                return
        list_item = QListWidgetItem(f"{symbol}\n  {name}")
        list_item.setData(Qt.ItemDataRole.UserRole, {'symbol': symbol, 'name': name})
        self.watchlist.addItem(list_item)
        self.save_settings()
        self.watchlist.setCurrentItem(list_item)
        self.search_bar.clear()
        self.search_results_list.hide()
        
        # Se siamo in vista 3, riavvia il news worker con i nuovi ticker
        if self.current_view_mode == 3:
            self.start_news_worker()

    # --- Gestione UI (Modificato per Vista 3) ---
    
    def on_timeframe_changed(self):
        checked_btn = self.timeframe_group.checkedButton()
        if checked_btn:
            self.current_timeframe = checked_btn.text()
            self.save_settings()
            self.refresh_data()
    
    def on_chart_type_changed(self):
        checked_btn = self.chart_type_group.checkedButton()
        if checked_btn:
            self.current_chart_type = checked_btn.text().lower()
            self.save_settings()
            self.refresh_data()
            
    def on_indicator_changed(self):
        self.indicators_state['rsi'] = self.rsi_button.isChecked()
        self.save_settings()
        self.refresh_data()
            
    def on_view_toggled(self):
        """Cicla tra le modalità di visualizzazione: 1 -> 2 -> 3 -> 1"""
        self.current_view_mode = (self.current_view_mode % 3) + 1
        self.apply_view_mode()
        self.save_settings()
        
    def apply_view_mode(self):
        """Applica la modalità di visualizzazione corrente."""
        icon_map = {
            1: QStyle.StandardPixmap.SP_DesktopIcon,       # Vista 1: Solo Grafico
            2: QStyle.StandardPixmap.SP_DirOpenIcon,       # Vista 2: Grafico + Sidebar Notizie
            3: QStyle.StandardPixmap.SP_FileIcon           # Vista 3: Grafico + Flyout Notizie
        }
        
        if self.current_view_mode == 1:
            # VISTA 1: Solo Grafico
            self.splitter.show()
            self.news_feed_sidebar.hide()
            self.flyout_news_feed.hide()
            
        elif self.current_view_mode == 2:
            # VISTA 2: Grafico + Sidebar Notizie
            self.splitter.show()
            self.news_feed_sidebar.show()
            self.flyout_news_feed.hide()
            
        elif self.current_view_mode == 3:
            # VISTA 3: Grafico + Flyout Notizie (a destra)
            self.splitter.show()  # Keep splitter visible
            self.news_feed_sidebar.hide()
            # Flyout starts hidden, will show on hover or new news
            self.flyout_news_feed.update_geometry(force_hide=True)
            self.flyout_news_feed.hide()
            # Riavvia il news worker con i ticker della watchlist
            self.start_news_worker()
        
        self.view_button.setIcon(self.style().standardIcon(icon_map.get(self.current_view_mode)))


    def open_settings(self):
        """Apre il dialogo delle impostazioni."""
        current_settings = {
            'news_tickers': self.news_tickers
            # Rimosso: 'view_popup_duration_s'
        }
        dialog = SettingsDialog(current_settings, self)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_settings = dialog.get_settings()
            
            # Aggiorna le impostazioni e salva
            self.news_tickers = new_settings.get('news_tickers', self.news_tickers)
            self.save_settings()
            
            # Riavvia il news worker con i nuovi ticker
            self.start_news_worker()

    def update_ui_states(self):
        """Aggiorna tutti i pulsanti (timeframe, tipo, indicatori, vista) all'avvio."""
        if self.current_timeframe in self.timeframe_buttons:
            self.timeframe_buttons[self.current_timeframe].setChecked(True)
        if self.current_chart_type in self.chart_type_buttons:
            self.chart_type_buttons[self.current_chart_type].setChecked(True)
        if rsi is not None:
            rsi_active = self.indicators_state.get('rsi', False)
            self.rsi_button.setChecked(rsi_active)
        self.apply_view_mode() # Applica la modalità di vista caricata

    def start_news_worker(self):
        """Avvia (o riavvia) il thread che recupera le notizie."""
        if self.news_worker and self.news_worker.isRunning():
            self.news_worker.stop()
            self.news_worker.wait()
        
        if news:
            # In vista 3, usa i ticker della watchlist se disponibili, altrimenti usa news_tickers
            if self.current_view_mode == 3:
                watchlist_tickers = self.get_watchlist_tickers()
                tickers_to_use = watchlist_tickers if watchlist_tickers else self.news_tickers
            else:
                tickers_to_use = self.news_tickers
            
            self.news_worker = NewsWorker(tickers_to_use)
            self.news_worker.new_news_signal.connect(self.add_news_card)
            self.news_worker.start()
        else:
            print("Impossibile avviare NewsWorker: modulo 'news.py' non trovato.")

    def get_watchlist_tickers(self):
        """Restituisce una lista di ticker dalla watchlist."""
        tickers = []
        for i in range(self.watchlist.count()):
            item = self.watchlist.item(i)
            if item:
                data = item.data(Qt.ItemDataRole.UserRole)
                if data and 'symbol' in data:
                    tickers.append(data['symbol'])
        return tickers
    
    def _ensure_trading_model(self):
        """Carica il modello trading solo quando necessario (lazy loading)."""
        if self.trading_model is not None:
            # Se il modello è già caricato, verifica che sia valido
            return hasattr(self.trading_model, 'model') and self.trading_model.model is not None
        
        # Prova a caricare il modello solo ora
        try:
            model_module = load_model()
            if model_module:
                print("[MainWindow] Caricamento modello AI per analisi notizie...")
                try:
                    self.trading_model = model_module.TradingModel()
                    if self.trading_model.model is None:
                        print("[MainWindow] Modello non caricato. Analisi notizie disabilitata.")
                        self.trading_model = None
                        return False
                    else:
                        print("[MainWindow] Modello caricato con successo.")
                        return True
                except Exception as e:
                    print(f"[MainWindow] Errore durante il caricamento del modello: {e}")
                    self.trading_model = None
                    return False
            else:
                return False
        except Exception as e:
            print(f"[MainWindow] Errore durante l'import del modulo model: {e}")
            self.trading_model = None
            return False
    
    @pyqtSlot(dict)
    def add_news_card(self, news_item):
        """Slot per ricevere una nuova notizia. La invia alla sidebar corretta."""
        # Filtra le notizie per ticker della watchlist
        watchlist_tickers = self.get_watchlist_tickers()
        news_ticker = news_item.get('ticker', '')
        
        # Se la vista è 3, mostra solo notizie della watchlist
        if self.current_view_mode == 3:
            if not watchlist_tickers or news_ticker not in watchlist_tickers:
                return  # Ignora notizie non correlate alla watchlist
        
        # Prova a caricare il modello se non è già caricato
        model_available = self._ensure_trading_model()
        
        # Avvia l'analisi della notizia in background
        if model_available and self.trading_model and self.trading_model.model:
            analysis_worker = NewsAnalysisWorker(news_item.copy(), self.trading_model)
            analysis_worker.analysis_complete.connect(self._on_news_analyzed)
            analysis_worker.start()
            self.analysis_workers.append(analysis_worker)
        else:
            # Se il modello non è disponibile, aggiungi direttamente
            self._on_news_analyzed(news_item)
    
    def _on_news_analyzed(self, news_item):
        """Callback quando l'analisi della notizia è completata."""
        # Aggiunge la notizia alla sidebar (vista 2) o al flyout (vista 3)
        if self.current_view_mode == 2:
            self.news_feed_sidebar.add_card(news_item)
        elif self.current_view_mode == 3:
            # Aggiunge al flyout e lo mostra
            self.flyout_news_feed.add_and_popup(news_item)

    # --- Funzioni di gestione dati (identiche) ---
    def on_watchlist_selection_changed(self, current_item, previous_item):
        if not current_item:
            self.current_ticker = None
            return
        data = current_item.data(Qt.ItemDataRole.UserRole)
        self.current_ticker = data['symbol']
        self.refresh_data()

    def refresh_data(self):
        if not self.current_ticker:
            return
        self.loading_label.setText(f"Fetching {self.current_timeframe} data for {self.current_ticker}...")
        self.stacked_widget.setCurrentWidget(self.loading_widget)
        self.loading_movie.start()
        timeframe_params = self.timeframe_map.get(self.current_timeframe, 
                                                  self.timeframe_map["1y"])
        self.data_worker = DataWorker(self.current_ticker, timeframe_params)
        self.data_worker.data_ready.connect(self.plot_data)
        self.data_worker.error.connect(self.show_error)
        self.data_worker.start()

    def remove_selected_item(self):
        selected_items = self.watchlist.selectedItems()
        if not selected_items: return
        for item in selected_items:
            row = self.watchlist.row(item)
            self.watchlist.takeItem(row)
        self.save_settings()
        if self.watchlist.count() == 0:
            self.current_ticker = None
            self.stacked_widget.setCurrentWidget(self.stacked_widget.widget(0))
        
        # Se siamo in vista 3, riavvia il news worker con i nuovi ticker
        if self.current_view_mode == 3:
            self.start_news_worker()

    def show_error(self, message):
        self.loading_movie.stop()
        self.loading_label.setText(str(message))
        self.stacked_widget.setCurrentWidget(self.loading_widget)

    def plot_data(self, data, ticker):
        self.loading_movie.stop()
        data = data.copy()
        self.chart_canvas.ax_price.clear()
        self.chart_canvas.ax_volume.clear()
        self.chart_canvas.ax_indicator.clear()
        add_plots = []
        plt.setp(self.chart_canvas.ax_price.get_xticklabels(), visible=False)
        if rsi is not None and self.indicators_state.get('rsi', False):
            try:
                rsi_plot_list = rsi.get_rsi_plot(data, ax_indicator=self.chart_canvas.ax_indicator)
                add_plots.extend(rsi_plot_list)
                self.chart_canvas.ax_indicator.set_visible(True)
                plt.setp(self.chart_canvas.ax_volume.get_xticklabels(), visible=False)
            except Exception as e:
                print(f"Errore calcolo RSI: {e}")
                self.chart_canvas.ax_indicator.set_visible(False)
                plt.setp(self.chart_canvas.ax_volume.get_xticklabels(), visible=True)
        else:
            self.chart_canvas.ax_indicator.set_visible(False)
            plt.setp(self.chart_canvas.ax_volume.get_xticklabels(), visible=True)
        self.chart_canvas.cross_hline = self.chart_canvas.ax_price.axhline(0, color='gray', linewidth=0.5, linestyle='--', visible=False)
        self.chart_canvas.cross_vline = self.chart_canvas.ax_price.axvline(0, color='gray', linewidth=0.5, linestyle='--', visible=False)
        self.chart_canvas.annot = self.chart_canvas.ax_price.annotate(
            "", xy=(0, 0), xytext=(15, 15), textcoords="offset points",
            bbox=dict(boxstyle='round', facecolor='#1e1e1e', edgecolor='#444'),
            color='#dcdcdc', fontsize=10, visible=False
        )
        self.chart_canvas.set_data(data, self.current_chart_type, self.current_timeframe) 
        full_name = ""
        current_item = self.watchlist.currentItem()
        if current_item and current_item.data(Qt.ItemDataRole.UserRole)['symbol'] == ticker:
             full_name = current_item.data(Qt.ItemDataRole.UserRole)['name']
        custom_style = mpf.make_mpf_style(base_mpf_style='nightclouds', gridstyle='--', gridaxis='both')
        if self.current_timeframe in ['1d', '5d']:
            date_format = '%b %d %H:%M'
        else:
            date_format = '%Y-%m-%d'
        mpf.plot(data,
                 type=self.current_chart_type,
                 style=custom_style,
                 ax=self.chart_canvas.ax_price,
                 volume=self.chart_canvas.ax_volume,
                 addplot=add_plots,
                 ylabel='Price (USD)',
                 mav=(20, 50) if self.current_timeframe not in ['1d', '5d'] else (),
                 show_nontrading=False,
                 datetime_format=date_format,
                 tight_layout=True 
                )
        self.chart_canvas.ax_volume.set_ylabel('Volume')
        title_str = f'{full_name} ({ticker}) - {self.current_timeframe} ({self.current_chart_type.capitalize()})'
        self.chart_canvas.ax_price.set_title(title_str)
        self.chart_canvas.draw()
        self.stacked_widget.setCurrentWidget(self.chart_canvas)
        self.chart_canvas.on_xlim_changed(self.chart_canvas.ax_price)

    # --- SALVATAGGIO/CARICAMENTO AGGIORNATO ---
    def save_settings(self):
        watchlist_data = []
        for i in range(self.watchlist.count()):
            item = self.watchlist.item(i)
            data = item.data(Qt.ItemDataRole.UserRole)
            watchlist_data.append(data)
            
        settings = {
            'watchlist': watchlist_data,
            'timeframe': self.current_timeframe,
            'chart_type': self.current_chart_type,
            'indicators': self.indicators_state,
            'view_mode': self.current_view_mode,
            'news_tickers': self.news_tickers
            # Rimosso: 'view_popup_duration_s'
        }
        
        try:
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(settings, f, indent=4)
        except Exception as e:
            print(f"Error saving settings: {e}") 

    def load_settings(self):
        try:
            with open(SETTINGS_FILE, 'r') as f:
                settings = json.load(f)
            
            if not isinstance(settings, dict):
                return

            # Carica impostazioni
            self.current_timeframe = settings.get('timeframe', '1y')
            self.current_chart_type = settings.get('chart_type', 'candle')
            self.indicators_state = settings.get('indicators', {})
            self.current_view_mode = settings.get('view_mode', 1)
            default_tickers = ['GC=F', 'CL=F', '^GSPC', 'NVDA', 'MSFT', 'GOOGL']
            self.news_tickers = settings.get('news_tickers', default_tickers)
            # Rimosso: self.view_popup_duration_s
            
            # Carica watchlist
            watchlist_data = settings.get('watchlist', [])
            self.watchlist.clear()
            for data in watchlist_data:
                symbol = data.get('symbol')
                name = data.get('name')
                if symbol and name:
                    list_item = QListWidgetItem(f"{symbol}\n  {name}")
                    list_item.setData(Qt.ItemDataRole.UserRole, data)
                    self.watchlist.addItem(list_item)
            
            if self.watchlist.count() > 0:
                self.watchlist.setCurrentRow(0)
        
        except FileNotFoundError:
            pass 
        except Exception as e:
            print(f"Error loading settings: {e}")
            
    # --- Gestione chiusura finestra ---
    def closeEvent(self, event):
        """Assicura che i thread in background vengano chiusi."""
        print("Chiusura dell'applicazione... Arresto dei worker.")
        if self.news_worker:
            self.news_worker.stop()
            self.news_worker.wait()
        event.accept()
            
# --- Entry Point ---
if __name__ == '__main__':
    try:
        with open("spinner.gif", "rb"): pass
    except FileNotFoundError:
        print("\nERROR: spinner.gif not found.")
        print("Download a spinner from https://i.imgur.com/O15wS1E.gif and save it as 'spinner.gif'")
        sys.exit(1)
        
    if rsi is None:
        print("AVVISO: il modulo 'rsi.py' non è stato trovato. L'indicatore RSI sarà disabilitato.")
    if news is None:
        print("AVVISO: il modulo 'news.py' non è stato trovato. Il feed notizie sarà disabilitato.")
    if model is None:
        print("AVVISO: il modulo 'model.py' non è stato trovato. L'analisi AI delle notizie sarà disabilitata.")

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
