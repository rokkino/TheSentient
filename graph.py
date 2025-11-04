import sys
import requests
import pandas as pd
import yfinance as yf
import mplfinance as mpf
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QLineEdit, QListWidget, QListWidgetItem, QLabel,
                             QStackedWidget, QHBoxLayout, QPushButton, QSplitter, QStyle)
from PyQt6.QtCore import (Qt, QThread, pyqtSignal, QTimer, QSize)
from PyQt6.QtGui import (QMovie)

# Matplotlib integration for PyQt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

# --- STYLESHEET PROFESSIONALE ---
# Una palette di colori grigio antracite, ispirata alle moderne piattaforme di trading
STYLESHEET = """
    QWidget {
        background-color: #1e1e1e; /* Sfondo principale molto scuro */
        color: #dcdcdc; /* Testo quasi bianco, ma non abbagliante */
        font-family: 'Segoe UI', Arial, sans-serif;
        font-size: 15px;
    }
    QMainWindow {
        border: 1px solid #333333;
    }
    QLineEdit {
        background-color: #2d2d2d; /* Sfondo leggermente più chiaro per i campi */
        border: 1px solid #444444;
        border-radius: 5px;
        padding: 8px;
    }
    QLineEdit:focus {
        border: 1px solid #007acc; /* Accento blu per l'elemento attivo */
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
        background-color: #5a2a27; /* Rosso desaturato per l'azione di rimozione */
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
        color: #888888; /* Grigio più scuro per testo informativo */
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
"""

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
            response = requests.get(url, headers=headers)
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
    def __init__(self, ticker):
        super().__init__()
        self.ticker = ticker

    def run(self):
        try:
            data = yf.download(self.ticker, period="1y", interval="1d", auto_adjust=True)

            if data.empty:
                raise ValueError("No data returned from yfinance.")

            # --- ROBUST FIX FOR ValueError ---
            # 1. Define the columns that MUST be numeric for plotting.
            ohlcv_columns = ['Open', 'High', 'Low', 'Close', 'Volume']

            # 2. Force conversion to numeric.
            #    'coerce' will turn any non-numeric values (like strings) into NaN.
            for col in ohlcv_columns:
                if col in data.columns:
                    data[col] = pd.to_numeric(data[col], errors='coerce')

            # 3. Now, drop any rows that have NaN values (either original or from coercion).
            data.dropna(inplace=True)

            # 4. Final check to see if any data remains after cleaning.
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
        self.fig.patch.set_facecolor('#1e1e1e') # Sfondo del grafico coordinato
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor('#2d2d2d') # Sfondo dell'area di plotting
        super(MplCanvas, self).__init__(self.fig)

# --- Main Application Window ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Professional Portfolio Tracker")
        self.setGeometry(100, 100, 1400, 800)
        self.setStyleSheet(STYLESHEET)
        
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

    def setup_left_panel(self):
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(10, 10, 10, 10) # Aggiunge spazio interno
        left_layout.setSpacing(10) # Spazio tra i widget

        # Layout orizzontale per ricerca e pulsante Add
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
        left_layout.addWidget(self.watchlist, 1) # Il '1' fa espandere la lista

        self.remove_button = QPushButton(" Remove")
        self.remove_button.setObjectName("RemoveButton")
        self.remove_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon))
        left_layout.addWidget(self.remove_button)

        self.splitter.addWidget(left_panel)

    def setup_right_panel(self):
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_panel.setLayout(right_layout)
        
        self.stacked_widget = QStackedWidget()
        right_layout.addWidget(self.stacked_widget)

        # Welcome Screen
        welcome_widget = QWidget()
        welcome_layout = QVBoxLayout(welcome_widget)
        welcome_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title = QLabel("Portfolio Tracker", objectName="TitleLabel")
        info = QLabel("Add an asset from the search bar to begin.", objectName="InfoLabel")
        welcome_layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)
        welcome_layout.addWidget(info, alignment=Qt.AlignmentFlag.AlignCenter)
        self.stacked_widget.addWidget(welcome_widget)

        # Loading Screen
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

        # Chart Canvas
        self.chart_canvas = MplCanvas(self)
        self.stacked_widget.addWidget(self.chart_canvas)
        
        self.stacked_widget.setCurrentWidget(welcome_widget)
        self.splitter.addWidget(right_panel)

    def setup_connections(self):
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.start_search)
        self.search_bar.textChanged.connect(lambda: self.search_timer.start(300))
        
        self.search_results_list.itemClicked.connect(self.add_to_watchlist)
        self.add_button.clicked.connect(self.add_top_search_result)

        self.watchlist.currentItemChanged.connect(self.on_watchlist_selection_changed)
        self.remove_button.clicked.connect(self.remove_selected_item)

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
        
        # Previene duplicati
        for i in range(self.watchlist.count()):
            if self.watchlist.item(i).data(Qt.ItemDataRole.UserRole)['symbol'] == symbol:
                self.search_bar.clear()
                self.search_results_list.hide()
                return

        list_item = QListWidgetItem(f"{symbol}\n  {name}")
        list_item.setData(Qt.ItemDataRole.UserRole, {'symbol': symbol, 'name': name})
        self.watchlist.addItem(list_item)
        self.watchlist.setCurrentItem(list_item)
        
        self.search_bar.clear()
        self.search_results_list.hide()

    def on_watchlist_selection_changed(self, current_item, previous_item):
        if not current_item:
            return
        data = current_item.data(Qt.ItemDataRole.UserRole)
        ticker = data['symbol']
        self.loading_label.setText(f"Fetching data for {ticker}...")
        self.stacked_widget.setCurrentWidget(self.loading_widget)
        self.loading_movie.start()
        
        self.data_worker = DataWorker(ticker)
        self.data_worker.data_ready.connect(self.plot_data)
        self.data_worker.error.connect(self.show_error)
        self.data_worker.start()

    def remove_selected_item(self):
        selected_items = self.watchlist.selectedItems()
        if not selected_items: return
        for item in selected_items:
            row = self.watchlist.row(item)
            self.watchlist.takeItem(row)
        if self.watchlist.count() == 0:
            self.stacked_widget.setCurrentWidget(self.stacked_widget.widget(0))

    def plot_data(self, data, ticker):
        self.loading_movie.stop()
        self.chart_canvas.ax.clear()
        full_name = ""
        current_item = self.watchlist.currentItem()
        if current_item:
            full_name = current_item.data(Qt.ItemDataRole.UserRole)['name']
        
        # Stile del grafico migliorato
        mpf.plot(data,
                 type='candle',
                 style='nightclouds',
                 ax=self.chart_canvas.ax,
                 title=f'{full_name} ({ticker})',
                 ylabel='Price (USD)',
                 mav=(20, 50),
                 volume=True,
                 panel_ratios=(3, 1),
                 gridstyle='--',
                 gridaxis='both')
        
        self.chart_canvas.fig.tight_layout()
        self.chart_canvas.draw()
        self.stacked_widget.setCurrentWidget(self.chart_canvas)

    def show_error(self, message):
        self.loading_movie.stop()
        self.loading_label.setText(message)
        self.stacked_widget.setCurrentWidget(self.loading_widget)

# --- Entry Point ---
if __name__ == '__main__':
    try:
        with open("spinner.gif", "rb"): pass
    except FileNotFoundError:
        print("\nERROR: spinner.gif not found.")
        print("Download a spinner from https://i.imgur.com/O15wS1E.gif and save it as 'spinner.gif'")
        sys.exit(1)

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())