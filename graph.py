import sys
import requests
import pandas as pd
import yfinance as yf
import mplfinance as mpf
import json
import math as m
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QLineEdit, QListWidget, QListWidgetItem, QLabel,
                             QStackedWidget, QHBoxLayout, QPushButton, QSplitter, QStyle,
                             QButtonGroup)
from PyQt6.QtCore import (Qt, QThread, pyqtSignal, QTimer, QSize)
from PyQt6.QtGui import (QMovie)

# Matplotlib integration for PyQt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

# --- 1. IMPORTA IL NUOVO MODULO ADD-ON ---
try:
    import rsi
except ImportError:
    print("ERRORE: Impossibile trovare il file 'rsi.py'. Assicurati che sia nella stessa cartella.")
    rsi = None

# --- STYLESHEET PROFESSIONALE ---
STYLESHEET = """
    /* ... (Stile identico, omesso per brevità) ... */
    QWidget {
        background-color: #1e1e1e;
        color: #dcdcdc;
        font-family: 'Segoe UI', Arial, sans-serif;
        font-size: 15px;
    }
    QMainWindow { border: 1px solid #333333; }
    QLineEdit {
        background-color: #2d2d2d;
        border: 1px solid #444444;
        border-radius: 5px;
        padding: 8px;
    }
    QLineEdit:focus { border: 1px solid #007acc; }
    QListWidget {
        background-color: #2d2d2d;
        border: 1px solid #444444;
        border-radius: 5px;
    }
    QListWidget::item { padding: 12px 8px; }
    QListWidget::item:hover { background-color: #3a3a3a; }
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
    QPushButton#RemoveButton { background-color: #5a2a27; }
    QPushButton#RemoveButton:hover { background-color: #7a3a37; }
    QLabel#TitleLabel {
        font-size: 28px;
        font-weight: bold;
        color: #f0f0f0;
        padding-top: 20px;
    }
    QLabel#InfoLabel { font-size: 18px; color: #888888; }
    QLabel#PanelTitle {
        font-size: 18px;
        font-weight: bold;
        padding: 8px 0px;
        border-bottom: 1px solid #444444;
    }
    QSplitter::handle { background-color: #333333; }
    QSplitter::handle:hover { background-color: #007acc; }
    
    /* Stile per i pulsanti Timeframe e ChartType */
    QPushButton#TimeframeButton {
        padding: 6px 10px;
        font-size: 13px;
        border-radius: 4px;
        border: 1px solid #333;
    }
    QPushButton#TimeframeButton:hover { background-color: #4a4a4a; }
    QPushButton#TimeframeButton:checked {
        background-color: #007acc;
        color: #ffffff;
        border-color: #007acc;
    }
"""

SETTINGS_FILE = 'settings.json'

# --- Worker Threads ---
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

# --- Matplotlib Canvas (Robusto) ---
class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        plt.style.use('dark_background')
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.fig.patch.set_facecolor('#1e1e1e')
        
        # --- 2. MODIFICA LAYOUT PER 3 PANNELLI ---
        # 5 righe totali: 3 per Prezzo, 1 per Volume, 1 per RSI
        gs = self.fig.add_gridspec(5, 1)
        self.ax_price = self.fig.add_subplot(gs[0:3, 0])
        self.ax_volume = self.fig.add_subplot(gs[3, 0], sharex=self.ax_price)
        self.ax_indicator = self.fig.add_subplot(gs[4, 0], sharex=self.ax_price) # <-- Nuovo pannello
        
        # Imposta colori e nascondi pannello indicatore
        self.ax_price.set_facecolor('#2d2d2d')
        self.ax_volume.set_facecolor('#2d2d2d')
        self.ax_indicator.set_facecolor('#2d2d2d')
        self.ax_indicator.set_visible(False)
        
        # Nascondi etichette assi X per pannelli superiori
        plt.setp(self.ax_price.get_xticklabels(), visible=False)
        plt.setp(self.ax_volume.get_xticklabels(), visible=False)
        # --- FINE MODIFICA 2 ---
        
        super(MplCanvas, self).__init__(self.fig)
        
        self.data = None
        self.chart_type = 'candle'
        self.timeframe = '1y'
        
        self.cross_hline = None
        self.cross_vline = None
        self.annot = None # Per il popup/tooltip
        
        # Connessioni
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
        # --- 3. MODIFICA TOOLTIP PER RSI ---
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

            # Costruisci la stringa del popup
            price_str = ""
            if self.chart_type == 'candle':
                price_str = (
                    f"O: {row.Open:<7.2f}   H: {row.High:<7.2f}\n"
                    f"L: {row.Low:<7.2f}   C: {row.Close:<7.2f}"
                )
            else: # 'line'
                price_str = f"Close: {row.Close:<7.2f}"
            
            # --- AGGIUNGI RSI AL TOOLTIP SE ESISTE ---
            if 'RSI' in self.data.columns and pd.notna(row['RSI']):
                price_str += f"\nRSI(14): {row['RSI']:.2f}"
            # --- FINE AGGIUNTA ---
            
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
        # --- FINE MODIFICA 3 ---
            
    def on_xlim_changed(self, ax):
        # --- 4. MODIFICA AUTOSCALE PER RSI ---
        if self.data is None or len(self.data) == 0:
            return
        
        xmin, xmax = ax.get_xlim()
        idx_min = int(m.floor(xmin))
        idx_max = int(m.ceil(xmax))
        idx_min = max(0, idx_min)
        idx_max = min(len(self.data), idx_max)

        if idx_min >= idx_max:
            return

        visible_data = self.data.iloc[idx_min:idx_max]
        
        if visible_data.empty:
            return
        
        ymin = visible_data['Low'].min()
        ymax = visible_data['High'].max()
        vmax = visible_data['Volume'].max()

        padding = (ymax - ymin) * 0.05
        if padding == 0:
            padding = ymin * 0.05 
        if pd.isna(ymin) or pd.isna(ymax): return # Salta se i dati non sono validi
        
        ax.set_ylim(ymin - padding, ymax + padding)
        self.ax_volume.set_ylim(0, vmax * 1.05)
        
        # Auto-scala anche il pannello RSI se è visibile
        if self.ax_indicator.get_visible() and 'RSI' in visible_data.columns:
            rsi_min = visible_data['RSI'].min()
            rsi_max = visible_data['RSI'].max()
            
            if pd.isna(rsi_min) or pd.isna(rsi_max): return # Dati RSI non ancora pronti
            
            rsi_padding = (rsi_max - rsi_min) * 0.1
            if rsi_padding == 0: rsi_padding = 5
            
            self.ax_indicator.set_ylim(max(0, rsi_min - rsi_padding), 
                                       min(100, rsi_max + rsi_padding))
        
        self.draw_idle()
        # --- FINE MODIFICA 4 ---

# --- Main Application Window ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("The Sentient")
        self.setGeometry(100, 100, 1400, 800)
        self.setStyleSheet(STYLESHEET)
        
        self.current_ticker = None
        self.current_timeframe = "1y"
        self.current_chart_type = "candle"
        
        # --- 5. AGGIUNGI STATO PER GLI INDICATORI ---
        self.indicators_state = {} # es: {'rsi': True}
        
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
        # --- FINE MODIFICA 5 ---

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QHBoxLayout(central_widget)
        central_widget.setLayout(self.main_layout)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_layout.addWidget(self.splitter)

        self.setup_left_panel()
        self.setup_right_panel()

        self.splitter.setSizes([350, 1050])
        self.setup_connections()

        self.load_settings()
        self.update_timeframe_buttons()
        self.update_chart_type_buttons()
        self.update_indicator_buttons() # <-- Nuovo

    def setup_left_panel(self):
        # ... (Codice identico a prima) ...
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
        
        # Gruppo Timeframe
        self.timeframe_group = QButtonGroup(self)
        self.timeframe_group.setExclusive(True)
        timeframes = ["1d", "5d", "1m", "3m", "6m", "1y", "5y"]
        for tf in timeframes:
            btn = QPushButton(tf)
            btn.setCheckable(True)
            btn.setObjectName("TimeframeButton")
            btn.clicked.connect(self.on_timeframe_changed)
            top_bar_layout.addWidget(btn)
            self.timeframe_group.addButton(btn)
            self.timeframe_buttons[tf] = btn
            
        top_bar_layout.addSpacing(30)

        # Gruppo Tipo Grafico
        self.chart_type_group = QButtonGroup(self)
        self.chart_type_group.setExclusive(True)
        chart_types = ["Candle", "Line"]
        for ct in chart_types:
            btn = QPushButton(ct)
            btn.setCheckable(True)
            btn.setObjectName("TimeframeButton")
            btn.clicked.connect(self.on_chart_type_changed)
            top_bar_layout.addWidget(btn)
            self.chart_type_group.addButton(btn)
            self.chart_type_buttons[ct.lower()] = btn
            
        # --- 6. AGGIUNGI PULSANTE INDICATORI ---
        top_bar_layout.addSpacing(30)
        
        self.rsi_button = QPushButton("RSI")
        self.rsi_button.setCheckable(True) # Non esclusivo
        self.rsi_button.setObjectName("TimeframeButton") # Riusa lo stile
        self.rsi_button.clicked.connect(self.on_indicator_changed)
        top_bar_layout.addWidget(self.rsi_button)
        # Disabilita se il modulo rsi.py non è stato trovato
        if rsi is None:
            self.rsi_button.setDisabled(True)
            self.rsi_button.setToolTip("File rsi.py non trovato")
        # --- FINE MODIFICA 6 ---
            
        top_bar_layout.addStretch()
        right_layout.addLayout(top_bar_layout)

        self.stacked_widget = QStackedWidget()
        right_layout.addWidget(self.stacked_widget)

        # ... (Setup di welcome_widget, loading_widget identico) ...
        welcome_widget = QWidget()
        welcome_layout = QVBoxLayout(welcome_widget)
        welcome_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title = QLabel("Portfolio Tracker", objectName="TitleLabel")
        info = QLabel("Add an asset from the search bar to begin.", objectName="InfoLabel")
        welcome_layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)
        welcome_layout.addWidget(info, alignment=Qt.AlignmentFlag.AlignCenter)
        self.stacked_widget.addWidget(welcome_widget)
        self.loading_widget = QWidget()
        loading_layout = QVBoxLayout(self.loading_widget)
        loading_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_label = QLabel("Fetching data...")
        self.loading_movie = QMovie("spinner.gif")
        self.loading_movie.setScaledSize(QSize(50, 50))
        spinner_label = QLabel()
        spinner_label.setMovie(self.loading_movie)
        loading_layout.addWidget(spinner_label, alignment=Qt.AlignmentFlag.AlignCenter)
        loading_layout.addWidget(self.loading_label, alignment=Qt.AlignmentFlag.AlignCenter)
        self.stacked_widget.addWidget(self.loading_widget)

        # Il canvas ora ha 3 pannelli
        self.chart_canvas = MplCanvas(self)
        self.stacked_widget.addWidget(self.chart_canvas)
        
        self.stacked_widget.setCurrentWidget(welcome_widget)
        self.splitter.addWidget(right_panel)

    def setup_connections(self):
        # ... (Codice identico a prima) ...
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.start_search)
        self.search_bar.textChanged.connect(lambda: self.search_timer.start(300))
        self.search_results_list.itemClicked.connect(self.add_to_watchlist)
        self.add_button.clicked.connect(self.add_top_search_result)
        self.watchlist.currentItemChanged.connect(self.on_watchlist_selection_changed)
        self.remove_button.clicked.connect(self.remove_selected_item)

    def start_search(self):
        # ... (Codice identico a prima) ...
        query = self.search_bar.text().strip()
        if not query:
            self.search_results_list.hide()
            return
        self.search_worker = SearchWorker(query)
        self.search_worker.results_ready.connect(self.show_search_results)
        self.search_worker.error.connect(self.show_error)
        self.search_worker.start()

    def show_search_results(self, results):
        # ... (Codice identico a prima) ...
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
        # ... (Codice identico a prima) ...
        if self.search_results_list.count() > 0:
            self.add_to_watchlist(self.search_results_list.item(0))
            
    def add_to_watchlist(self, item):
        # ... (Codice identico a prima) ...
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

    # --- 7. NUOVI HANDLER PER STATO UI ---
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
        """Gestisce tutti i pulsanti indicatore."""
        self.indicators_state['rsi'] = self.rsi_button.isChecked()
        self.save_settings()
        self.refresh_data()
            
    def update_timeframe_buttons(self):
        if self.current_timeframe in self.timeframe_buttons:
            self.timeframe_buttons[self.current_timeframe].setChecked(True)

    def update_chart_type_buttons(self):
        if self.current_chart_type in self.chart_type_buttons:
            self.chart_type_buttons[self.current_chart_type].setChecked(True)

    def update_indicator_buttons(self):
        """Imposta lo stato 'checked' dei pulsanti indicatore all'avvio."""
        if rsi is not None:
            rsi_active = self.indicators_state.get('rsi', False)
            self.rsi_button.setChecked(rsi_active)
    # --- FINE MODIFICA 7 ---

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
        # ... (Codice identico a prima) ...
        selected_items = self.watchlist.selectedItems()
        if not selected_items: return
        for item in selected_items:
            row = self.watchlist.row(item)
            self.watchlist.takeItem(row)
        self.save_settings()
        if self.watchlist.count() == 0:
            self.current_ticker = None
            self.stacked_widget.setCurrentWidget(self.stacked_widget.widget(0))

    def show_error(self, message):
            self.loading_movie.stop()
            self.loading_label.setText(str(message))
            self.stacked_widget.setCurrentWidget(self.loading_widget)

    def plot_data(self, data, ticker):
            self.loading_movie.stop()
            
            # Copia i dati per evitare SettingWithCopyWarning
            data = data.copy()
            
            # --- LOGICA DI PLOTTING DINAMICA ---
            
            # Pulisci tutti gli assi
            self.chart_canvas.ax_price.clear()
            self.chart_canvas.ax_volume.clear()
            self.chart_canvas.ax_indicator.clear()
            
            # Variabili per il plot
            add_plots = []
            
            # Nascondi etichette X del prezzo (sempre)
            plt.setp(self.chart_canvas.ax_price.get_xticklabels(), visible=False)
            
            # Controlla se l'RSI è attivo
            if rsi is not None and self.indicators_state.get('rsi', False):
                # Calcola e ottieni i plot RSI dal modulo
                try:
                    # --- MODIFICA CHIAVE QUI ---
                    # Passa l'asse (ax_indicator) invece di un ID pannello
                    rsi_plot_list = rsi.get_rsi_plot(data, ax_indicator=self.chart_canvas.ax_indicator)
                    add_plots.extend(rsi_plot_list)
                    
                    # Mostra il pannello indicatore
                    self.chart_canvas.ax_indicator.set_visible(True)
                    
                    # Nascondi etichette X del volume (verranno mostrate solo su RSI)
                    plt.setp(self.chart_canvas.ax_volume.get_xticklabels(), visible=False)
                except Exception as e:
                    print(f"Errore calcolo RSI: {e}")
                    self.chart_canvas.ax_indicator.set_visible(False)
                    plt.setp(self.chart_canvas.ax_volume.get_xticklabels(), visible=True)
            else:
                # Nascondi pannello RSI e mostra etichette volume
                self.chart_canvas.ax_indicator.set_visible(False)
                plt.setp(self.chart_canvas.ax_volume.get_xticklabels(), visible=True)
            
            # Ricrea mirino e annotazione sul pannello del prezzo
            self.chart_canvas.cross_hline = self.chart_canvas.ax_price.axhline(0, color='gray', linewidth=0.5, linestyle='--', visible=False)
            self.chart_canvas.cross_vline = self.chart_canvas.ax_price.axvline(0, color='gray', linewidth=0.5, linestyle='--', visible=False)
            self.chart_canvas.annot = self.chart_canvas.ax_price.annotate(
                "", xy=(0, 0), xytext=(15, 15), textcoords="offset points",
                bbox=dict(boxstyle='round', facecolor='#1e1e1e', edgecolor='#444'),
                color='#dcdcdc', fontsize=10, visible=False
            )
            
            # Passa i dati (ora con colonna RSI, se attiva) al canvas
            self.chart_canvas.set_data(data, self.current_chart_type, self.current_timeframe) 
            
            full_name = ""
            current_item = self.watchlist.currentItem()
            if current_item and current_item.data(Qt.ItemDataRole.UserRole)['symbol'] == ticker:
                full_name = current_item.data(Qt.ItemDataRole.UserRole)['name']
            
            custom_style = mpf.make_mpf_style(base_mpf_style='nightclouds',
                                            gridstyle='--',
                                            gridaxis='both')
            
            if self.current_timeframe in ['1d', '5d']:
                date_format = '%b %d %H:%M'
            else:
                date_format = '%Y-%m-%d'
            
            # Plot finale
            mpf.plot(data,
                    type=self.current_chart_type,
                    style=custom_style,
                    ax=self.chart_canvas.ax_price,         # Pannello 0
                    volume=self.chart_canvas.ax_volume,    # Pannello 1
                    addplot=add_plots,                     # Contiene i plot RSI per ax_indicator
                    # panel_ratios=... ,                   # <-- RIMOSSO: Questo causava l'errore
                    ylabel='Price (USD)',
                    mav=(20, 50) if self.current_timeframe not in ['1d', '5d'] else (),
                    # ylabel_lower='Volume',               # <-- RIMOSSO: Non valido in modalità assi esterni
                    show_nontrading=False,
                    datetime_format=date_format,
                    tight_layout=True 
                    )
            
            # --- AGGIUNTA ETICHETTA MANUALE ---
            # Dobbiamo impostare l'etichetta del volume manualmente
            self.chart_canvas.ax_volume.set_ylabel('Volume')
            
            title_str = f'{full_name} ({ticker}) - {self.current_timeframe} ({self.current_chart_type.capitalize()})'
            self.chart_canvas.ax_price.set_title(title_str)
            
            self.chart_canvas.draw()
            self.stacked_widget.setCurrentWidget(self.chart_canvas)
            
            # Attiva il primo auto-scale
            self.chart_canvas.on_xlim_changed(self.chart_canvas.ax_price)
    # --- 9. MODIFICHE SALVATAGGIO/CARICAMENTO ---
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
            'indicators': self.indicators_state # <-- Salva stato indicatori
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

            self.current_timeframe = settings.get('timeframe', '1y')
            self.current_chart_type = settings.get('chart_type', 'candle')
            self.indicators_state = settings.get('indicators', {}) # <-- Carica stato indicatori
            
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
            pass # Normale al primo avvio
        except Exception as e:
            print(f"Error loading settings: {e}")
    # --- FINE MODIFICA 9 ---
            
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

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())