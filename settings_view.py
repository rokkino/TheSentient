import sys
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QFrame, QScrollArea,
                             QDialog, QLineEdit, QDialogButtonBox, QFormLayout,
                             QSizePolicy, QSpinBox, QHBoxLayout, QPushButton,
                             QCheckBox, QTextEdit)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QPropertyAnimation, QRect, QTimer, pyqtProperty

from PyQt6.QtGui import QDesktopServices, QColor, QPixmap, QMovie
from PyQt6.QtWidgets import QGraphicsDropShadowEffect
from PyQt6.QtCore import QUrl

STYLESHEET = """
/* Stile per la Card della Notizia */
#NewsCard {
    background-color: rgba(30,30,30,0.92);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px;
    margin-bottom: 12px;
    padding: 16px;
    min-height: 140px;
}
#NewsCard:hover {
    background-color: #3a3a3a;
    border-color: #555555;
}
#NewsTitle {
    font-size: 17px;
    font-weight: 700;
    color: #ffffff;
    padding: 4px 0px;
}
#NewsInfo {
    font-size: 12px;
    color: #9aa3ad;
    font-style: italic;
    margin-top: 4px;
}
#NewsSummary {
    font-size: 15px;
    color: #d8d8d8;
    padding: 8px 0px;
    line-height: 1.6;
}
#TradingSignal {
    background-color: rgba(46, 46, 46, 0.7);
    border: 1px solid #3a3a3a;
    border-radius: 8px;
    padding: 10px;
    margin-top: 10px;
}
#TradingSignal.bearish {
    background-color: rgba(74, 42, 42, 0.7);
    border-color: #6a3a3a;
}
#SignalLabel {
    font-size: 13px;
    font-weight: 600;
    color: #dcdcdc;
    margin-bottom: 6px;
}
#SignalLabel.bearish {
    color: #ff6b6b;
}
#SignalInfo {
    font-size: 12px;
    color: #b0b0b0;
    line-height: 1.5;
}

/* Stile per la ScrollArea della Sidebar */
QScrollArea {
    border: none;
    background-color: #1e1e1e;
    border-radius: 8px;
}
#ScrollAreaWidget {
    background-color: #1e1e1e;
}
#PanelTitle {
    font-size: 18px;
    font-weight: bold;
    padding: 10px 0px;
    border-bottom: 2px solid #444444;
    border-radius: 4px;
}

#SectionTitle {
    color: #b9c1ca;
    font-size: 12px;
    letter-spacing: 1.2px;
    font-weight: 600;
    text-transform: uppercase;
    margin-top: 6px;
}

/* Scrollbar stile Apple */
QScrollBar:vertical {
    background: transparent;
    width: 8px;
    margin: 4px;
}
QScrollBar::handle:vertical {
    background: rgba(255,255,255,0.25);
    min-height: 28px;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover {
    background: rgba(255,255,255,0.35);
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: transparent;
}

/* Stile per il Pannello Impostazioni */
QDialog {
    background-color: #111111;
    color: #dcdcdc;
    border-radius: 12px;
}
QLineEdit, QSpinBox {
    background-color: #1e1e1e;
    border: 1px solid #444444;
    border-radius: 8px;
    padding: 6px;
    color: #dcdcdc;
}
QFormLayout > QLabel {
    font-weight: bold;
}
QPushButton#ViewToggleButton {
    background-color: #3c3c3c;
    border: 1px solid #555555;
    border-radius: 8px;
    padding: 6px 12px;
    color: #dcdcdc;
    font-size: 12px;
}
QPushButton#ViewToggleButton:hover {
    background-color: #4a4a4a;
    border-color: #666666;
}

/* Header custom del dialog */
#DialogHeader {
    background-color: #0d0d0d;
    border-top-left-radius: 12px;
    border-top-right-radius: 12px;
}
#DialogTitle {
    color: #f0f0f0;
    font-weight: 600;
}
#HeaderButton {
    background-color: transparent;
    border: 1px solid #333333;
    border-radius: 6px;
    padding: 4px 8px;
}
#HeaderButton:hover {
    background-color: #1f1f1f;
}

/* Toggle switch stile blu per QCheckBox */
QCheckBox[class="toggle"]::indicator {
    width: 44px;
    height: 22px;
}
QCheckBox[class="toggle"]::indicator:unchecked {
    border-radius: 11px;
    background: #3a3a3a;
}
QCheckBox[class="toggle"]::indicator:unchecked:hover {
    background: #4a4a4a;
}
QCheckBox[class="toggle"]::indicator:checked {
    border-radius: 11px;
    background: #007acc;
}
QCheckBox[class="toggle"]::indicator:checked:hover {
    background: #108ee9;
}
QCheckBox[class="toggle"]::indicator:unchecked::before,
QCheckBox[class="toggle"]::indicator:checked::before {
    content: "";
    position: absolute;
    width: 18px;
    height: 18px;
    margin: 2px;
    border-radius: 9px;
    background: #cccccc;
}
QCheckBox[class="toggle"]::indicator:checked::before {
    margin-left: 24px;
    background: #ffffff;
}
"""

class NewsCard(QFrame):
    """
    Un widget cliccabile che mostra una singola notizia con trading signals.
    """
    def __init__(self, news_item, parent=None):
        super().__init__(parent)
        self.setObjectName("NewsCard")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        # Soft shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(24)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 120))
        self.setGraphicsEffect(shadow)
        
        self.link = news_item.get('link')
        title = news_item.get('title', 'Nessun Titolo')
        publisher = news_item.get('publisher', 'Sconosciuto')
        timestamp = news_item.get('timestamp')
        ticker = news_item.get('ticker', '')

        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        
        title_label = QLabel(title)
        title_label.setObjectName("NewsTitle")
        title_label.setWordWrap(True)
        layout.addWidget(title_label)
        
        time_str = timestamp.strftime('%H:%M') if timestamp else ''
        info_str = f"{publisher} ({ticker}) - {time_str}"
        info_label = QLabel(info_str)
        info_label.setObjectName("NewsInfo")
        layout.addWidget(info_label)

        # Row with thumbnail and summary
        content_row = QHBoxLayout()
        content_row.setSpacing(10)
        # Thumbnail (optional)
        self.thumb_label = QLabel()
        self.thumb_label.setFixedSize(64, 64)
        self.thumb_label.setScaledContents(True)
        self.thumb_label.setStyleSheet("border-radius:8px; background:#262626;")
        self.thumb_label.hide()
        # Try to load thumbnail from news_item['image_url'] if present
        image_url = news_item.get('image_url') or news_item.get('image')
        if image_url and isinstance(image_url, str):
            try:
                import requests
                resp = requests.get(image_url, timeout=3)
                if resp.ok:
                    pix = QPixmap()
                    pix.loadFromData(resp.content)
                    if not pix.isNull():
                        self.thumb_label.setPixmap(pix)
                        self.thumb_label.show()
            except Exception:
                pass
        content_row.addWidget(self.thumb_label)
        # Summary text
        text_content = news_item.get('text', '')
        self.summary_label = QLabel(text_content)
        self.summary_label.setObjectName("NewsSummary")
        self.summary_label.setWordWrap(True)
        self.summary_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.summary_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        content_row.addWidget(self.summary_label, 1)
        layout.addLayout(content_row)

        # Trading signal area (always present, supports loading state)
        self.signal_frame = QFrame()
        self.signal_frame.setObjectName("TradingSignal")
        self.signal_layout = QVBoxLayout(self.signal_frame)
        self.signal_layout.setSpacing(4)
        self.signal_frame.setStyleSheet("#TradingSignal{border-radius:10px;}")
        # Small spinner for AI analysis state
        self.spinner_label = QLabel()
        self.spinner_movie = QMovie("spinner.gif")
        self.spinner_movie.setScaledSize(QSize(18, 18))
        self.spinner_label.setMovie(self.spinner_movie)
        self.spinner_label.hide()
        self.signal_layout.addWidget(self.spinner_label)

        self.signal_label = QLabel("")
        self.signal_label.setObjectName("SignalLabel")
        self.signal_info = QLabel("")
        self.signal_info.setObjectName("SignalInfo")
        self.signal_info.setVisible(False)
        self.signal_layout.addWidget(self.signal_label)
        self.signal_layout.addWidget(self.signal_info)
        layout.addWidget(self.signal_frame)

        # Initial render
        self.render_trading_signal(news_item.get('trading_signal'))

        self.setStyleSheet(STYLESHEET)
    
    def mousePressEvent(self, event):
        """Apre il link della notizia nel browser."""
        if self.link:
            QDesktopServices.openUrl(QUrl(self.link))
        event.accept()

    def render_trading_signal(self, trading_signal):
        """Rende la sezione del trading signal, supportando stato 'loading'."""
        # Reset classes
        self.signal_frame.setProperty("class", "")
        if not trading_signal or trading_signal.get('status') == 'loading':
            self.spinner_label.show()
            if self.spinner_movie.state() != QMovie.MovieState.Running:
                self.spinner_movie.start()
            self.signal_label.setText("Analisi del modello in corso...")
            self.signal_info.setVisible(False)
            return
        # stop spinner
        self.spinner_label.hide()
        if self.spinner_movie.state() == QMovie.MovieState.Running:
            self.spinner_movie.stop()
        direction = trading_signal.get('direction', 'NEUTRAL')
        confidence = trading_signal.get('confidence', 0)
        stop_loss = trading_signal.get('stop_loss')
        take_profit = trading_signal.get('take_profit')
        # Set style for bearish
        if direction == 'BEARISH':
            self.signal_frame.setProperty("class", "bearish")
            self.signal_label.setProperty("class", "bearish")
        else:
            self.signal_label.setProperty("class", "")
        self.signal_label.setText(f"{direction} - Confidence: {confidence}%")
        if stop_loss is not None and take_profit is not None:
            self.signal_info.setText(f"Stop Loss: {stop_loss}\nTake Profit: {take_profit}")
            self.signal_info.setVisible(True)
        else:
            self.signal_info.setVisible(False)
        # Re-apply stylesheet to reflect dynamic properties
        self.setStyleSheet(STYLESHEET)

    def update_trading_signal(self, trading_signal):
        """API pubblica per aggiornare il trading signal della card."""
        self.render_trading_signal(trading_signal)

class NewsSidebar(QFrame):
    """
    Una sidebar generica che può essere fissa (Sticky) o a comparsa (Flyout).
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFixedWidth(300) # Larghezza fissa
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)
        
        # Header con titolo e pulsante vista
        self.header_layout = QHBoxLayout()
        title_label = QLabel("Feed Notizie")
        title_label.setObjectName("PanelTitle")
        title_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.header_layout.addWidget(title_label)
        self.header_layout.addStretch()
        main_layout.addLayout(self.header_layout)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        scroll_widget = QWidget()
        scroll_widget.setObjectName("ScrollAreaWidget")
        
        self.card_container = QVBoxLayout(scroll_widget)
        self.card_container.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.card_container.setSpacing(8)
        
        self.scroll_area.setWidget(scroll_widget)
        main_layout.addWidget(self.scroll_area)
        
        self.setStyleSheet(STYLESHEET)

    def add_card(self, news_item):
        """Aggiunge una nuova card in cima al feed."""
        card = NewsCard(news_item)
        self.card_container.insertWidget(0, card)
        
        # Limita il numero di card
        max_cards = 50 
        while self.card_container.count() > max_cards:
            item = self.card_container.takeAt(max_cards)
            if item.widget():
                item.widget().deleteLater()
        
        return card # Restituisce la card creata

class FlyoutNewsFeed(NewsSidebar):
    """
    Una sidebar di notizie (Vista 3) che si anima e si nasconde automaticamente.
    Appare sul lato destro dello schermo.
    """
    view_toggle_requested = pyqtSignal()  # Signal per cambiare vista
    
    def __init__(self, popup_duration_ms, parent=None):
        super().__init__(parent)
        
        # Larghezza ridotta per il flyout
        self.setFixedWidth(280)
        
        self.popup_duration_ms = popup_duration_ms
        self.panel_width = 280
        self.is_visible = False
        
        # Aggiungi pulsante per cambiare vista
        self._add_view_toggle_button()
        
        # Animazione per la geometria
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(300) # 300ms per l'animazione
        
        # Timer per nascondere automaticamente il popup
        self.auto_hide_timer = QTimer(self)
        self.auto_hide_timer.setSingleShot(True)
        self.auto_hide_timer.timeout.connect(self.slide_out)
        
        # Permetti modalità floating con sfondo trasparente stile "notifica"
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setStyleSheet(self.styleSheet() + "\n#NewsCard { background-color: rgba(45,45,45,0.85); border: 1px solid rgba(255,255,255,0.06);} ")
        
        self.update_geometry(force_hide=True)
        self.hide()
    
    def _add_view_toggle_button(self):
        """Aggiunge un pulsante per cambiare vista nella header del flyout."""
        if hasattr(self, 'header_layout'):
            view_button = QPushButton("View")
            view_button.setObjectName("ViewToggleButton")
            view_button.setToolTip("Cambia modalità vista")
            view_button.clicked.connect(self.view_toggle_requested.emit)
            self.header_layout.addWidget(view_button)

    def update_geometry(self, force_hide=False):
        """Aggiorna la posizione della sidebar; se floating, aggancia al bordo destro dello schermo."""
        # Usa geometria dello schermo primario per ancorare a destra
        from PyQt6.QtWidgets import QApplication
        screen = QApplication.primaryScreen()
        geo = screen.availableGeometry() if screen else QRect(0, 0, 1280, 720)
        screen_x = geo.x()
        screen_y = geo.y()
        screen_w = geo.width()
        screen_h = geo.height()

        self.visible_geo = QRect(screen_x + screen_w - self.panel_width - 16, screen_y + 16,
                                 self.panel_width, screen_h - 32)
        self.hidden_geo = QRect(screen_x + screen_w + 8, screen_y + 16,
                                self.panel_width, screen_h - 32)
        
        if force_hide:
            self.setGeometry(self.hidden_geo)
            self.is_visible = False
        elif self.is_visible:
            self.setGeometry(self.visible_geo)
        else:
            self.setGeometry(self.hidden_geo)

    def slide_in(self):
        """Anima la sidebar per farla entrare in vista."""
        self.update_geometry()
        
        if self.is_visible:
            # Se è già visibile, riavvia il timer (es. per un nuovo popup)
            self.auto_hide_timer.start(self.popup_duration_ms)
            return
            
        self.animation.setStartValue(self.hidden_geo)
        self.animation.setEndValue(self.visible_geo)
        self.show()
        self.raise_()  # Porta il widget in primo piano
        self.activateWindow()  # Assicura che il widget sia attivo
        self.animation.start()
        self.is_visible = True
        # Avvia il timer per auto-hide dopo il popup_duration_ms
        self.auto_hide_timer.start(self.popup_duration_ms)

    def slide_out(self):
        """Anima la sidebar per farla uscire dalla vista."""
        if not self.is_visible:
            return
            
        self.update_geometry()
        self.animation.setStartValue(self.visible_geo)
        self.animation.setEndValue(self.hidden_geo)
        self.animation.start()
        self.is_visible = False

    def schedule_slide_out(self, delay_ms=500):
        """Programma l'uscita dopo un breve ritardo."""
        self.auto_hide_timer.start(delay_ms)

    def add_and_popup(self, news_item):
        """Aggiunge una card E mostra il pannello come notifica."""
        card = self.add_card(news_item)
        self.slide_in()
        # Avvia il timer per nascondere automaticamente
        self.auto_hide_timer.start(self.popup_duration_ms)
        return card

    def enterEvent(self, event):
        """Quando il mouse entra nel pannello, annulla il timer di auto-hide."""
        self.auto_hide_timer.stop()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Quando il mouse esce, programma un'uscita ritardata."""
        self.schedule_slide_out(500) # Nascondi dopo 0.5s
        super().leaveEvent(event)


class SettingsDialog(QDialog):
    """
    Finestra di dialogo per le impostazioni dell'applicazione.
    """
    def __init__(self, current_settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Impostazioni")
        self.setMinimumWidth(520)
        self.setStyleSheet(STYLESHEET)
        # Rimuovi barra di Windows e usa dialogo frameless con drag
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint)
        self._drag_pos = None
        
        self.current_settings = current_settings
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header custom
        header = QFrame()
        header.setObjectName("DialogHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(10, 8, 10, 8)
        title_lbl = QLabel("Impostazioni")
        title_lbl.setObjectName("DialogTitle")
        header_layout.addWidget(title_lbl)
        header_layout.addStretch()
        btn_min = QPushButton("–")
        btn_min.setObjectName("HeaderButton")
        btn_min.clicked.connect(self.showMinimized)
        btn_close = QPushButton("✕")
        btn_close.setObjectName("HeaderButton")
        btn_close.clicked.connect(self.reject)
        header_layout.addWidget(btn_min)
        header_layout.addWidget(btn_close)
        layout.addWidget(header)
        form_layout = QFormLayout()
        form_layout.setVerticalSpacing(10)
        form_layout.setHorizontalSpacing(12)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        # --- Impostazioni Notizie ---
        layout.addWidget(QLabel("News", objectName="SectionTitle"))
        news_tickers_str = ", ".join(current_settings.get('news_tickers', []))
        self.tickers_input = QLineEdit(news_tickers_str)
        self.tickers_input.setToolTip("Lista di ticker separati da virgola (es. NVDA, GC=F, AAPL)")
        form_layout.addRow(QLabel("Ticker per Notizie:"), self.tickers_input)
        
        # --- Filtri feed ---
        self.only_watchlist_checkbox = QCheckBox()
        self.only_watchlist_checkbox.setProperty("class", "toggle")
        self.only_watchlist_checkbox.setChecked(current_settings.get('news_only_watchlist', False))
        form_layout.addRow(QLabel("Mostra solo notizie della watchlist:"), self.only_watchlist_checkbox)

        # --- Sorgenti news ---
        self.enable_yahoo_checkbox = QCheckBox()
        self.enable_yahoo_checkbox.setProperty("class", "toggle")
        self.enable_yahoo_checkbox.setChecked(current_settings.get('enable_yahoo_news', True))
        form_layout.addRow(QLabel("Abilita Yahoo News:"), self.enable_yahoo_checkbox)

        self.enable_x_checkbox = QCheckBox()
        self.enable_x_checkbox.setProperty("class", "toggle")
        self.enable_x_checkbox.setChecked(current_settings.get('enable_x_news', False))
        form_layout.addRow(QLabel("Abilita X (Twitter) News:"), self.enable_x_checkbox)

        self.x_api_token_input = QLineEdit(current_settings.get('x_api_token', ''))
        self.x_api_token_input.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow(QLabel("X API Token:"), self.x_api_token_input)

        self.x_profiles_input = QTextEdit("\n".join(current_settings.get('x_profiles', [])))
        self.x_profiles_input.setPlaceholderText("https://x.com/user1\nhttps://x.com/user2")
        self.x_profiles_input.setFixedHeight(80)
        form_layout.addRow(QLabel("Profili X da monitorare (uno per riga):"), self.x_profiles_input)

        # --- Indicatori grafico ---
        layout.addWidget(QLabel("Indicatori", objectName="SectionTitle"))
        self.show_rsi_checkbox = QCheckBox()
        self.show_rsi_checkbox.setProperty("class", "toggle")
        self.show_rsi_checkbox.setChecked(current_settings.get('show_rsi_indicator', current_settings.get('indicators', {}).get('rsi', False)))
        form_layout.addRow(QLabel("Mostra RSI:"), self.show_rsi_checkbox)

        self.show_volume_checkbox = QCheckBox()
        self.show_volume_checkbox.setProperty("class", "toggle")
        self.show_volume_checkbox.setChecked(current_settings.get('show_volume_panel', True))
        form_layout.addRow(QLabel("Mostra Volumi:"), self.show_volume_checkbox)

        # Moving Averages
        self.show_ma13_checkbox = QCheckBox()
        self.show_ma13_checkbox.setProperty("class", "toggle")
        self.show_ma13_checkbox.setChecked(current_settings.get('indicators', {}).get('ma13', False) or current_settings.get('show_ma13', False))
        form_layout.addRow(QLabel("Mostra MA 13:"), self.show_ma13_checkbox)

        self.show_ma50_checkbox = QCheckBox()
        self.show_ma50_checkbox.setProperty("class", "toggle")
        self.show_ma50_checkbox.setChecked(current_settings.get('indicators', {}).get('ma50', False) or current_settings.get('show_ma50', False))
        form_layout.addRow(QLabel("Mostra MA 50:"), self.show_ma50_checkbox)

        self.show_ma200_checkbox = QCheckBox()
        self.show_ma200_checkbox.setProperty("class", "toggle")
        self.show_ma200_checkbox.setChecked(current_settings.get('indicators', {}).get('ma200', False) or current_settings.get('show_ma200', False))
        form_layout.addRow(QLabel("Mostra MA 200:"), self.show_ma200_checkbox)

        self.show_ma800_checkbox = QCheckBox()
        self.show_ma800_checkbox.setProperty("class", "toggle")
        self.show_ma800_checkbox.setChecked(current_settings.get('indicators', {}).get('ma800', False) or current_settings.get('show_ma800', False))
        form_layout.addRow(QLabel("Mostra MA 800:"), self.show_ma800_checkbox)

        # --- Modello ---
        layout.addWidget(QLabel("Modello AI", objectName="SectionTitle"))
        self.use_cuda_checkbox = QCheckBox()
        self.use_cuda_checkbox.setProperty("class", "toggle")
        self.use_cuda_checkbox.setChecked(current_settings.get('use_cuda', False))
        form_layout.addRow(QLabel("Usa CUDA (NVIDIA):"), self.use_cuda_checkbox)

        # Modello: spunte separate
        self.model_use_rsi_checkbox = QCheckBox()
        self.model_use_rsi_checkbox.setProperty("class", "toggle")
        self.model_use_rsi_checkbox.setChecked(current_settings.get('model_use_rsi', False) or current_settings.get('model_use_indicators', False))
        form_layout.addRow(QLabel("Il modello usa RSI:"), self.model_use_rsi_checkbox)

        self.model_use_volume_checkbox = QCheckBox()
        self.model_use_volume_checkbox.setProperty("class", "toggle")
        self.model_use_volume_checkbox.setChecked(current_settings.get('model_use_volume', False) or current_settings.get('model_use_indicators', False))
        form_layout.addRow(QLabel("Il modello usa Volumi:"), self.model_use_volume_checkbox)

        self.model_use_mas_checkbox = QCheckBox()
        self.model_use_mas_checkbox.setProperty("class", "toggle")
        self.model_use_mas_checkbox.setChecked(current_settings.get('model_use_mas', False))
        form_layout.addRow(QLabel("Il modello usa Moving Averages:"), self.model_use_mas_checkbox)
        
        ##### INIZIO MODIFICA SSL #####
        
        # --- Impostazione SSL ---
        layout.addWidget(QLabel("Sicurezza", objectName="SectionTitle"))
        self.ssl_verify_checkbox = QCheckBox()
        self.ssl_verify_checkbox.setToolTip(
            "Disabilita questa opzione SOLO se sei su una rete aziendale\n"
            "che causa problemi di certificato SSL.\n"
            "ATTENZIONE: Rende la connessione insicura."
        )
        # Imposta lo stato_corrente. True = Sicuro (Verifica Abilitata)
        self.ssl_verify_checkbox.setChecked(current_settings.get('ssl_verify', True))
        form_layout.addRow(QLabel("Abilita Verifica SSL (Sicuro):"), self.ssl_verify_checkbox)
        
        ##### FINE MODIFICA SSL #####
        
        layout.addLayout(form_layout)
        
        # Pulsanti OK / Cancella
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    # Drag per finestra frameless
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        super().mouseReleaseEvent(event)

    def get_settings(self):
        """Restituisce le impostazioni aggiornate."""
        tickers_list = [ticker.strip().upper() for ticker in self.tickers_input.text().split(',') if ticker.strip()]
        x_profiles = [line.strip() for line in self.x_profiles_input.toPlainText().splitlines() if line.strip()]
        return {
            'news_tickers': tickers_list,
            'ssl_verify': self.ssl_verify_checkbox.isChecked(),
            'use_cuda': self.use_cuda_checkbox.isChecked(),
            'enable_yahoo_news': self.enable_yahoo_checkbox.isChecked(),
            'enable_x_news': self.enable_x_checkbox.isChecked(),
            'x_api_token': self.x_api_token_input.text(),
            'x_profiles': x_profiles,
            'news_only_watchlist': self.only_watchlist_checkbox.isChecked(),
            'show_rsi_indicator': self.show_rsi_checkbox.isChecked(),
            'show_volume_panel': self.show_volume_checkbox.isChecked(),
            'show_ma13': self.show_ma13_checkbox.isChecked(),
            'show_ma50': self.show_ma50_checkbox.isChecked(),
            'show_ma200': self.show_ma200_checkbox.isChecked(),
            'show_ma800': self.show_ma800_checkbox.isChecked(),
            'model_use_rsi': self.model_use_rsi_checkbox.isChecked(),
            'model_use_volume': self.model_use_volume_checkbox.isChecked(),
            'model_use_mas': self.model_use_mas_checkbox.isChecked(),
        }
    
class SettingsDialog(QDialog):
    """
    Finestra di dialogo per le impostazioni dell'applicazione.
    """
    def __init__(self, current_settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Impostazioni")
        self.setMinimumWidth(400)
        self.setStyleSheet(STYLESHEET)
        
        self.current_settings = current_settings
        
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        # --- Impostazioni Notizie ---
        news_tickers_str = ", ".join(current_settings.get('news_tickers', []))
        self.tickers_input = QLineEdit(news_tickers_str)
        self.tickers_input.setToolTip("Lista di ticker separati da virgola (es. NVDA, GC=F, AAPL)")
        form_layout.addRow(QLabel("Ticker per Notizie:"), self.tickers_input)
        # --- Filtri feed ---
        self.only_watchlist_checkbox = QCheckBox()
        self.only_watchlist_checkbox.setChecked(current_settings.get('news_only_watchlist', False))
        form_layout.addRow(QLabel("Mostra solo notizie della watchlist:"), self.only_watchlist_checkbox)

        # --- Sorgenti news ---
        self.enable_yahoo_checkbox = QCheckBox()
        self.enable_yahoo_checkbox.setChecked(current_settings.get('enable_yahoo_news', True))
        form_layout.addRow(QLabel("Abilita Yahoo News:"), self.enable_yahoo_checkbox)

        self.enable_x_checkbox = QCheckBox()
        self.enable_x_checkbox.setChecked(current_settings.get('enable_x_news', False))
        form_layout.addRow(QLabel("Abilita X (Twitter) News:"), self.enable_x_checkbox)

        self.x_api_token_input = QLineEdit(current_settings.get('x_api_token', ''))
        self.x_api_token_input.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow(QLabel("X API Token:"), self.x_api_token_input)

        self.x_profiles_input = QTextEdit("\n".join(current_settings.get('x_profiles', [])))
        self.x_profiles_input.setPlaceholderText("https://x.com/user1\nhttps://x.com/user2")
        self.x_profiles_input.setFixedHeight(80)
        form_layout.addRow(QLabel("Profili X da monitorare (uno per riga):"), self.x_profiles_input)

        # --- Indicatori grafico ---
        self.show_rsi_checkbox = QCheckBox()
        self.show_rsi_checkbox.setChecked(current_settings.get('show_rsi_indicator', current_settings.get('indicators', {}).get('rsi', False)))
        form_layout.addRow(QLabel("Mostra RSI:"), self.show_rsi_checkbox)

        self.show_volume_checkbox = QCheckBox()
        self.show_volume_checkbox.setChecked(current_settings.get('show_volume_panel', True))
        form_layout.addRow(QLabel("Mostra Volumi:"), self.show_volume_checkbox)

        # --- Modello ---
        self.use_cuda_checkbox = QCheckBox()
        self.use_cuda_checkbox.setChecked(current_settings.get('use_cuda', False))
        form_layout.addRow(QLabel("Usa CUDA (NVIDIA):"), self.use_cuda_checkbox)

        self.model_use_indicators_checkbox = QCheckBox()
        self.model_use_indicators_checkbox.setChecked(current_settings.get('model_use_indicators', False))
        form_layout.addRow(QLabel("Il modello usa RSI/Volumi nella predizione:"), self.model_use_indicators_checkbox)

        ##### INIZIO MODIFICA SSL #####
        
        # --- Impostazione SSL ---
        self.ssl_verify_checkbox = QCheckBox()
        self.ssl_verify_checkbox.setToolTip(
            "Disabilita questa opzione SOLO se sei su una rete aziendale\n"
            "che causa problemi di certificato SSL.\n"
            "ATTENZIONE: Rende la connessione insicura."
        )
        # Imposta lo stato_corrente. True = Sicuro (Verifica Abilitata)
        self.ssl_verify_checkbox.setChecked(current_settings.get('ssl_verify', True))
        form_layout.addRow(QLabel("Abilita Verifica SSL (Sicuro):"), self.ssl_verify_checkbox)
        
        ##### FINE MODIFICA SSL #####
        
        layout.addLayout(form_layout)
        
        # Pulsanti OK / Cancella
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_settings(self):
        """Restituisce le impostazioni aggiornate."""
        tickers_list = [ticker.strip().upper() for ticker in self.tickers_input.text().split(',') if ticker.strip()]
        x_profiles = [line.strip() for line in self.x_profiles_input.toPlainText().splitlines() if line.strip()]
        return {
            'news_tickers': tickers_list,
            'ssl_verify': self.ssl_verify_checkbox.isChecked(),
            'use_cuda': self.use_cuda_checkbox.isChecked(),
            'enable_yahoo_news': self.enable_yahoo_checkbox.isChecked(),
            'enable_x_news': self.enable_x_checkbox.isChecked(),
            'x_api_token': self.x_api_token_input.text(),
            'x_profiles': x_profiles,
            'news_only_watchlist': self.only_watchlist_checkbox.isChecked(),
            'show_rsi_indicator': self.show_rsi_checkbox.isChecked(),
            'show_volume_panel': self.show_volume_checkbox.isChecked(),
            'model_use_indicators': self.model_use_indicators_checkbox.isChecked(),
        }