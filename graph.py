import sys
import requests
import pandas as pd
import yfinance as yf
import mplfinance as mpf
import json
import math as m
import time
import os
try:
    # Importa la sessione speciale richiesta da yfinance
    from curl_cffi.requests import Session as CurlSession
except ImportError:
    print("ERRORE: 'curl_cffi' non trovato. La ricezione dati non funzionerà.")
    print("Esegui: pip install curl_cffi")
    CurlSession = None
import ssl
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QLineEdit, QListWidget, QListWidgetItem, QLabel,
                             QStackedWidget, QHBoxLayout, QPushButton, QSplitter, QStyle,
                             QButtonGroup, QScrollArea, QDialog)
from PyQt6.QtCore import (Qt, QThread, pyqtSignal, QTimer, QSize, QUrl, pyqtSlot, 
                          QRect, QEvent) # Aggiunto QRect, QEvent, pyqtSlot
from PyQt6.QtGui import (QMovie, QIcon, QDesktopServices)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
try:
    import urllib3
    # Disabilita gli avvisi solo se la libreria è presente
except ImportError:
    urllib3 = None
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
    
    # --- MODIFICATO __init__ ---
    def __init__(self, query, session):
        super().__init__()
        self.query = query
        self.session = session # <-- Aggiunto

    def run(self):
        if not self.query:
            self.results_ready.emit([])
            return
        try:
            url = f"https://query1.finance.yahoo.com/v1/finance/search?q={self.query}"
            headers = {'User-Agent': 'Mozilla/5.0'}
            
            # --- MODIFICATA chiamata requests ---
            response = self.session.get(url, headers=headers, timeout=10) # <-- Usa self.session
            
            response.raise_for_status()
            data = response.json()
            
            # --- INIZIO LOGICA MANCANTE ---
            results = [
                quote for quote in data.get('quotes', [])
                if quote.get('quoteType') in ['EQUITY', 'ETF', 'CRYPTOCURRENCY', 'FUTURE']
            ]
            self.results_ready.emit(results)
            # --- FINE LOGICA MANCANTE ---
            
        except Exception as e:
            self.error.emit(f"Search failed: {e}")

class DataWorker(QThread):
    data_ready = pyqtSignal(pd.DataFrame, str)
    error = pyqtSignal(str)
    
    # --- MODIFICATO __init__ ---
    def __init__(self, ticker, timeframe_params, session): # <-- Riportato a 'session'
        super().__init__()
        self.ticker = ticker
        self.timeframe_params = timeframe_params
        self.session = session # <-- Riportato a 'session'

    def run(self):
        try:
            # --- MODIFICATA chiamata yf.Ticker ---
            # Rimuoviamo 'verify' e ripristiniamo 'session'
            # Ora passiamo la sessione curl_cffi (o None se non è installato)
            tk = yf.Ticker(self.ticker, session=self.session) 
            
            data = tk.history(**self.timeframe_params)
            
            # --- LOGICA RIPRISTINATA ---
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
            # --- FINE LOGICA ---
            
        except Exception as e:
            error_msg = str(e)
            if "Yahoo API requires curl_cffi" in error_msg:
                error_msg = "Errore yfinance: 'curl_cffi' non è installato. Esegui: pip install curl_cffi"
            elif "unexpected keyword argument 'verify'" in error_msg:
                 error_msg = "Errore di codice (Rimuovere 'verify' da Ticker)."
            self.error.emit(f"Failed to get data for {self.ticker}: {error_msg}")
class NewsAnalysisWorker(QThread):
    """Worker thread per analizzare le notizie con il modello AI."""
    analysis_complete = pyqtSignal(dict)  # Emette il news_item con trading_signal aggiunto
    
    # --- MODIFICATO __init__ (AGGIUNTO session=None) ---
    def __init__(self, news_item, trading_model=None, session=None):
        super().__init__()
        self.news_item = news_item
        self.trading_model = trading_model
        self.session = session # <-- Aggiunto
    
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
                # --- MODIFICATA chiamata check_url ---
                news_text = self.trading_model.check_url(news_link, session=self.session)
            
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
    
    # --- MODIFICATO __init__ ---
    def __init__(self, tickers, session):
        super().__init__()
        self.tickers = tickers
        self.session = session # <-- Aggiunto
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
                # --- MODIFICATO ---
                data_pool = news.fetch_all_news(self.tickers, session=self.session)
                
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

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__() # <-- Spostato all'inizio, è buona norma
        
        # --- MODIFICA SSL ---
        self.ssl_verify = True
        self.http_session = None # Useremo solo questa per tutto (sarà la CurlSession)
        # self.curl_session = None <-- RIMOSSO
        # --- FINE MODIFICA ---

        self.setWindowTitle("The Sentient")
        try:
            self.setWindowIcon(QIcon("icona.ico"))
        except:
            print("Nessun file 'icona.ico' trovato. Icona predefinita usata.")
            
        self.setGeometry(100, 100, 1400, 800)
        self.setStyleSheet(STYLESHEET)
        
        self.setMouseTracking(True)
        
        self.current_ticker = None
        self.current_timeframe = "1y"
        self.current_chart_type = "candle"
        self.indicators_state = {}
        self.news_worker = None
        self.analysis_workers = []
        self.trading_model = None 

        self.current_view_mode = 1 
        self.news_tickers = ['GC=F', 'CL=F', '^GSPC', 'NVDA', 'MSFT', 'GOOGL']
        self.flyout_popup_duration_ms = 5000 
        
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

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QHBoxLayout(central_widget)
        central_widget.setLayout(self.main_layout)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_layout.addWidget(self.splitter) 

        self.setup_left_panel()
        self.setup_right_panel()

        self.splitter.setSizes([350, 1050])
        
        self.news_feed_sidebar = NewsSidebar(self)
        self.main_layout.addWidget(self.news_feed_sidebar)
        
        self.flyout_news_feed = FlyoutNewsFeed(self.flyout_popup_duration_ms, self)
        self.flyout_news_feed.view_toggle_requested.connect(self.on_view_toggled)
        self.flyout_news_feed.hide()

        self.setup_connections()

        self.load_settings() # <-- Questo ora carica l'impostazione SSL e crea la sessione
        
        self.update_ui_states()
        
        self.start_news_worker()
        self.check_model_files()

    def check_model_files(self):
            """
            Controlla se i file del modello esistono. Se esistono, li carica.
            Se non esistono, chiede all'utente di scaricarli.
            """
            config_path = os.path.join("model", "config.json")
            
            if os.path.exists(config_path):
                print("File del modello trovati. Avvio caricamento in background...")
                self.start_model_loader() # Il modello esiste, caricalo
            else:
                print("File del modello non trovati. Chiedo all'utente.")
                # Il modello non esiste, mostra il pop-up
                reply = QMessageBox.question(
                    self,
                    'Modello AI Mancante',
                    "Non è stato trovato alcun modello AI locale (nella cartella 'model').\n\n"
                    "Vuoi scaricare il modello (circa 1.3 GB) da Hugging Face ora?\n\n"
                    "(L'analisi AI delle notizie sarà disabilitata finché il modello non sarà scaricato).",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    self.start_model_download()
                else:
                    print("L'utente ha rifiutato il download del modello.")

    def start_model_download(self):
        """Avvia il worker per scaricare il modello AI."""
        print("Avvio ModelDownloadWorker...")
        
        # Creiamo un dialog di progresso
        self.progress_dialog = QProgressDialog("Download del modello in corso...", "Annulla", 0, 100, self)
        self.progress_dialog.setWindowTitle("Download Modello")
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.show()

        self.model_downloader = ModelDownloadWorker(
            repo_id="deepseek-ai/deepseek-coder-1.3b-instruct",
            local_dir="./model"
        )
        
        self.model_downloader.download_progress.connect(self.on_download_progress)
        self.model_downloader.download_complete.connect(self.on_model_download_complete)
        self.model_downloader.download_error.connect(self.on_model_download_error)
        self.progress_dialog.canceled.connect(self.model_downloader.terminate) # Permette di annullare
        
        self.model_downloader.start()

    @pyqtSlot(str, int)
    def on_download_progress(self, message, value):
        """Aggiorna il dialog di progresso."""
        self.progress_dialog.setLabelText(message)
        self.progress_dialog.setValue(value)

    @pyqtSlot()
    def on_model_download_complete(self):
        """Chiamato al completamento del download."""
        self.progress_dialog.setValue(100)
        self.progress_dialog.close()
        print("Download modello completato.")
        QMessageBox.information(self, "Download Completato", "Modello AI scaricato con successo. Verrà ora caricato in background.")
        self.start_model_loader() # Ora che i file esistono, caricali

    @pyqtSlot(str)
    def on_model_download_error(self, error_message):
        """Chiamato se il download fallisce."""
        self.progress_dialog.close()
        print(f"ERRORE DOWNLOAD MODELLO: {error_message}")
        QMessageBox.critical(self, "Errore Download", f"Impossibile scaricare il modello:\n{error_message}")

    def start_model_loader(self):
            """Avvia il worker per caricare il modello AI."""
            if self.trading_model is not None:
                return # Già caricato
                
            print("Avvio ModelLoaderWorker...")
            # Passiamo la sessione HTTP al worker
            self.model_loader = ModelLoaderWorker(self.http_session) 
            self.model_loader.model_ready.connect(self.on_model_ready)
            self.model_loader.model_error.connect(self.on_model_error)
            self.model_loader.start()

    @pyqtSlot(object)
    def on_model_ready(self, model_instance):
        """Slot chiamato quando il modello AI è pronto."""
        self.trading_model = model_instance
        print("✅ Modello AI caricato con successo e pronto per l'analisi.")

    @pyqtSlot(str)
    def on_model_error(self, error_message):
        """Slot chiamato se il caricamento del modello fallisce."""
        print(f"❌ ERRORE CARICAMENTO MODELLO: {error_message}")
        self.trading_model = None

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
        title = QLabel("Tracker", objectName="TitleLabel")
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
            
            # --- MODIFICATO ---
            self.search_worker = SearchWorker(query, self.http_session)
            
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
            
            # --- MODIFICATO ---
            current_settings = {
                'news_tickers': self.news_tickers,
                'ssl_verify': self.ssl_verify  # <-- Passa l'impostazione corrente
            }
            dialog = SettingsDialog(current_settings, self)
            
            if dialog.exec() == QDialog.DialogCode.Accepted:
                new_settings = dialog.get_settings()
                
                # --- MODIFICATO ---
                self.news_tickers = new_settings.get('news_tickers', self.news_tickers)
                self.ssl_verify = new_settings.get('ssl_verify', True) # <-- Leggi la nuova impostazione
                
                self.create_http_session() # <-- Ricrea la sessione con la nuova impostazione
                
                self.save_settings() # <-- Salva tutto
                
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
            
            self.news_worker = NewsWorker(tickers_to_use, session=self.http_session)            
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
            """Controlla se il modello AI è stato caricato (non lo carica più)."""
            if self.trading_model is not None:
                # Il modello è stato caricato in background ed è pronto
                return True
            else:
                # Il modello è ancora in fase di caricamento o ha fallito
                return False
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
            # --- MODIFICATO ---
            analysis_worker = NewsAnalysisWorker(news_item.copy(), self.trading_model, session=self.http_session)
            
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
            # ... (codice per loading_label) ...
            timeframe_params = self.timeframe_map.get(self.current_timeframe, 
                                                    self.timeframe_map["1y"])
            
            # --- MODIFICATO ---
            # Passiamo la sessione curl_cffi unificata
            self.data_worker = DataWorker(self.current_ticker, timeframe_params, self.http_session)
            # --- FINE MODIFICA ---
            
            self.data_worker.data_ready.connect(self.plot_data)
            self.data_worker.error.connect(self.show_error)
            self.data_worker.start()
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
                'news_tickers': self.news_tickers,
                'ssl_verify': self.ssl_verify  # <-- Include l'impostazione SSL
            }
            
            try:
                with open(SETTINGS_FILE, 'w') as f:
                    json.dump(settings, f, indent=4)
            except Exception as e:
                print(f"Error saving settings: {e}")
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

    def create_http_session(self):
            """Crea o aggiorna la sessione HTTP condivisa in base alle impostazioni SSL."""
            if self.http_session:
                self.http_session.close()
                
            # Rimuovi la logica di self.curl_session, non è più necessaria
            
            if not CurlSession:
                print("ERRORE CRITICO: curl_cffi non è installato. Le richieste di rete falliranno.")
                self.http_session = requests.Session() # Fallback
                self.http_session.verify = self.ssl_verify
                return

            # --- MODALITÀ UNIFICATA con curl_cffi ---
            # Usiamo la sessione che impersona Chrome per TUTTE le richieste
            print("Creazione sessione curl_cffi (impersonate='chrome110')...")
            self.http_session = CurlSession(impersonate="chrome110")
            
            if self.ssl_verify:
                # --- MODALITÀ SICURA ---
                self.http_session.verify = True 
                print("Verifica SSL abilitata (Modalità Sicura).")
                if 'HF_HUB_DISABLE_CERT_CHECK' in os.environ:
                    del os.environ['HF_HUB_DISABLE_CERT_CHECK']
                    
            else:
                # --- MODALITÀ INSICURA ---
                self.http_session.verify = False # Per curl_cffi
                
                # Per transformers (model.py)
                os.environ['HF_HUB_DISABLE_CERT_CHECK'] = '1'

                if urllib3:
                    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                print("************************************************************")
                print("AVVISO: La verifica del certificato SSL è DISABILITATA.")
                print("************************************************************")

    def load_settings(self):
        try:
            with open(SETTINGS_FILE, 'r') as f:
                settings = json.load(f)
            
            if not isinstance(settings, dict):
                settings = {} # Evita errore se il file è corrotto

            # Carica impostazioni
            self.current_timeframe = settings.get('timeframe', '1y')
            self.current_chart_type = settings.get('chart_type', 'candle')
            self.indicators_state = settings.get('indicators', {})
            self.current_view_mode = settings.get('view_mode', 1)
            default_tickers = ['GC=F', 'CL=F', '^GSPC', 'NVDA', 'MSFT', 'GOOGL']
            self.news_tickers = settings.get('news_tickers', default_tickers)
            
            # --- MODIFICATO ---
            self.ssl_verify = settings.get('ssl_verify', True) # <-- Carica l'impostazione
            
            # Carica watchlist
            # ... (codice watchlist invariato) ...
            
        except FileNotFoundError:
            pass 
        except Exception as e:
            print(f"Error loading settings: {e}")
            
        # --- AGGIUNTO ALLA FINE ---
        # Crea la sessione DOPO aver caricato le impostazioni
        self.create_http_session()
            
    # --- Gestione chiusura finestra ---
    def closeEvent(self, event):
        """Assicura che i thread in background vengano chiusi."""
        print("Chiusura dell'applicazione... Arresto dei worker.")
        if self.news_worker:
            self.news_worker.stop()
            self.news_worker.wait()
        event.accept()
class ModelLoaderWorker(QThread):
    """Carica il pesante modello AI in un thread separato."""
    model_ready = pyqtSignal(object)
    model_error = pyqtSignal(str)
    
    def __init__(self, session):
        super().__init__()
        self.session = session
        
    def run(self):
        try:
            print("[ModelLoader] Avvio caricamento modello AI in background...")
            model_module = load_model()
            if model_module:
                model_instance = model_module.TradingModel(session=self.session)
                if model_instance.model:
                    self.model_ready.emit(model_instance)
                else:
                    self.model_error.emit("Caricamento modello fallito (istanza vuota).")
            else:
                self.model_error.emit("Modulo 'model.py' non trovato.")
        except Exception as e:
            self.model_error.emit(f"Errore caricamento modello: {e}")
class ModelDownloadWorker(QThread):
    """Scarica i file del modello da Hugging Face."""
    download_complete = pyqtSignal()
    download_error = pyqtSignal(str)
    download_progress = pyqtSignal(str, int) # Messaggio e percentuale

    def __init__(self, repo_id, local_dir):
        super().__init__()
        self.repo_id = repo_id
        self.local_dir = local_dir
        
        # Lazy import di huggingface_hub
        try:
            from huggingface_hub import snapshot_download, HfApi
            from huggingface_hub.utils import HfFolder
            self.snapshot_download = snapshot_download
        except ImportError:
            self.snapshot_download = None
            self.download_error.emit("Libreria 'huggingface_hub' non trovata. Esegui: pip install huggingface_hub")

    def run(self):
        if not self.snapshot_download:
            return
            
        try:
            print(f"[ModelDownloadWorker] Avvio download da '{self.repo_id}' a '{self.local_dir}'...")
            self.download_progress.emit("Download del modello in corso... (1.3GB)", 0)
            
            # Nota: snapshot_download non ha un callback di progresso facile.
            # Mostriamo un'indicazione generica.
            # Per un progresso reale, dovremmo scaricare i file manualmente,
            # ma questo è molto più robusto.
            
            self.snapshot_download(
                repo_id=self.repo_id,
                local_dir=self.local_dir,
                local_dir_use_symlinks=False,
                allow_patterns=["*.json", "*.txt", "*.safetensors"] # Scarica solo i file necessari
            )
            
            self.download_progress.emit("Download completato!", 100)
            self.download_complete.emit()
            
        except Exception as e:
            self.download_error.emit(f"Errore durante il download: {e}")
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
