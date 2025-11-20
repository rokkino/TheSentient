import sys
import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QFrame, QScrollArea,
                             QDialog, QLineEdit, QDialogButtonBox, QFormLayout,
                             QSizePolicy, QSpinBox, QHBoxLayout, QPushButton,
                             QTextEdit)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QPropertyAnimation, QRect, QTimer, pyqtProperty, QEasingCurve

from PyQt6.QtGui import QDesktopServices, QColor, QPixmap, QMovie, QIcon
from PyQt6.QtWidgets import QGraphicsDropShadowEffect, QGraphicsOpacityEffect
from PyQt6.QtCore import QUrl

STYLESHEET = """
/* Stile per la Card della Notizia */
#NewsCard {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                stop:0 rgba(48,48,48,0.96),
                                stop:1 rgba(30,30,30,0.98));
    border: 1px solid rgba(80,140,220,0.35);
    border-radius: 20px;
    margin-bottom: 22px;
    padding: 22px;
    min-height: 220px;
}
#NewsCard:hover {
    border-color: rgba(90,155,255,0.7);
}
#AccentBar {
    background-color: #2f84ff;
    border-radius: 5px;
}
#MetaChip {
    background-color: rgba(255,255,255,0.12);
    border: 1px solid rgba(255,255,255,0.2);
    border-radius: 14px;
    color: #f6f8ff;
    font-size: 11px;
    font-weight: 600;
    padding: 4px 14px;
    letter-spacing: 0.5px;
}
#MetaTime {
    color: #b6becd;
    font-size: 11px;
    padding-left: 10px;
}
#SummaryDivider {
    background-color: rgba(255,255,255,0.14);
    border: none;
    height: 1px;
    margin: 10px 0px 8px;
}
#ReadButton {
    background-color: #2d72d9;
    color: #f4f6fb;
    border: none;
    border-radius: 10px;
    padding: 6px 14px;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.4px;
}
#ReadButton:hover {
    background-color: #3a86ff;
}
#ReadButton:pressed {
    background-color: #205bb2;
}
#NewsTitle {
    font-size: 18px;
    font-weight: 700;
    color: #ffffff;
    padding: 2px 0px 8px;
    line-height: 1.32;
}
#NewsSummary {
    font-size: 15px;
    font-weight: 500;
    color: #f3f6ff;
    padding: 6px 0px 8px;
    line-height: 1.72;
}
#TradingSignal {
    background-color: rgba(16,16,16,0.9);
    border: 1px solid rgba(0,122,204,0.35);
    border-radius: 15px;
    padding: 16px;
    margin-top: 16px;
}
#TradingSignal.bearish {
    background-color: rgba(78, 34, 34, 0.9);
    border-color: rgba(255,92,92,0.45);
}
#SignalLabel {
    font-size: 14px;
    font-weight: 600;
    color: #fdfdff;
    margin-bottom: 10px;
}
#SignalLabel.bearish {
    color: #ff8a8a;
}
#SignalInfo {
    font-size: 12px;
    color: #d5d9e2;
    line-height: 1.65;
}
#LoadingText {
    font-size: 13px;
    color: #e1e5f0;
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

QPushButton#SettingToggle {
    background-color: #2f2f2f;
    border: 1px solid #454545;
    border-radius: 12px;
    padding: 4px 18px;
    min-width: 92px;
    color: #bfc2c9;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.6px;
}
QPushButton#SettingToggle:hover {
    border-color: #5a5a5a;
    color: #e2e5eb;
}
QPushButton#SettingToggle:checked {
    background-color: #0a7cd3;
    border-color: #0a7cd3;
    color: #ffffff;
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
        self.setMinimumHeight(220)
        
        self.link = news_item.get('link')
        title = news_item.get('title', 'Nessun Titolo')
        publisher = news_item.get('publisher', 'Sconosciuto')
        timestamp = news_item.get('timestamp')
        ticker = news_item.get('ticker', '')

        outer_layout = QHBoxLayout(self)
        outer_layout.setContentsMargins(12, 12, 12, 12)
        outer_layout.setSpacing(12)

        self.accent_bar = QFrame()
        self.accent_bar.setObjectName("AccentBar")
        self.accent_bar.setFixedWidth(5)
        outer_layout.addWidget(self.accent_bar)

        layout = QVBoxLayout()
        layout.setSpacing(12)
        outer_layout.addLayout(layout, 1)
        
        title_label = QLabel(title)
        title_label.setObjectName("NewsTitle")
        title_label.setWordWrap(True)
        layout.addWidget(title_label)

        meta_layout = QHBoxLayout()
        meta_layout.setSpacing(10)
        meta_layout.setContentsMargins(0, 0, 0, 0)
        if publisher:
            source_chip = QLabel(publisher)
            source_chip.setObjectName("MetaChip")
            meta_layout.addWidget(source_chip)
        if ticker:
            ticker_chip = QLabel(ticker)
            ticker_chip.setObjectName("MetaChip")
            meta_layout.addWidget(ticker_chip)
        time_str = timestamp.strftime('%H:%M') if timestamp else ''
        if time_str:
            time_label = QLabel(time_str)
            time_label.setObjectName("MetaTime")
            meta_layout.addWidget(time_label)
        meta_layout.addStretch()
        layout.addLayout(meta_layout)

        divider = QFrame()
        divider.setObjectName("SummaryDivider")
        divider.setFixedHeight(1)
        layout.addWidget(divider)

        # Row with thumbnail and summary
        content_row = QHBoxLayout()
        content_row.setSpacing(12)
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
        raw_summary = news_item.get('text') or news_item.get('summary') or ''
        summary_text = raw_summary.strip()
        if not summary_text:
            summary_text = news_item.get('title', '')
        if summary_text and len(summary_text) > 240:
            trimmed = summary_text[:237].rsplit(' ', 1)[0]
            summary_text = trimmed + "…" if trimmed else summary_text[:237] + "…"
        self.summary_label = QLabel(summary_text)
        self.summary_label.setObjectName("NewsSummary")
        self.summary_label.setWordWrap(True)
        self.summary_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.summary_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.summary_label.setMinimumHeight(60)
        self.summary_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        content_row.addWidget(self.summary_label, 1)
        layout.addLayout(content_row)

        actions_layout = QHBoxLayout()
        actions_layout.setContentsMargins(0, 10, 0, 0)
        actions_layout.setSpacing(8)
        self.read_button = QPushButton("Apri articolo")
        self.read_button.setObjectName("ReadButton")
        self.read_button.setVisible(bool(self.link))
        self.read_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.read_button.clicked.connect(self._on_read_clicked)
        actions_layout.addWidget(self.read_button)
        actions_layout.addStretch()
        layout.addLayout(actions_layout)

        # Trading signal area (always present, supports loading state)
        self.signal_frame = QFrame()
        self.signal_frame.setObjectName("TradingSignal")
        self.signal_layout = QVBoxLayout(self.signal_frame)
        self.signal_layout.setSpacing(4)
        self.signal_frame.setStyleSheet("#TradingSignal{border-radius:10px;}")
        # Small spinner for AI analysis state
        self.loading_container = QWidget()
        loading_layout = QHBoxLayout(self.loading_container)
        loading_layout.setContentsMargins(0, 0, 0, 0)
        loading_layout.setSpacing(8)
        loading_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.spinner_label = QLabel()
        self.spinner_movie = QMovie("spinner.gif")
        self.spinner_movie.setScaledSize(QSize(20, 20))
        self.spinner_label.setMovie(self.spinner_movie)
        loading_layout.addWidget(self.spinner_label)
        self.loading_text = QLabel("Analisi del modello in corso...")
        self.loading_text.setObjectName("LoadingText")
        loading_layout.addWidget(self.loading_text)
        loading_layout.addStretch()
        self.signal_layout.addWidget(self.loading_container)

        self.signal_label = QLabel("")
        self.signal_label.setObjectName("SignalLabel")
        self.signal_info = QLabel("")
        self.signal_info.setObjectName("SignalInfo")
        self.signal_label.hide()
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

    def _on_read_clicked(self):
        if self.link:
            QDesktopServices.openUrl(QUrl(self.link))

    def render_trading_signal(self, trading_signal):
        """Rende la sezione del trading signal, supportando stato 'loading'."""
        # Reset classes
        self.signal_frame.setProperty("class", "")
        neutral_color = "#2f84ff"
        self.accent_bar.setStyleSheet(f"#AccentBar {{ background-color: {neutral_color}; border-radius: 5px; }}")
        if not trading_signal or trading_signal.get('status') == 'loading':
            self.loading_container.show()
            self.signal_label.hide()
            self.signal_info.hide()
            if self.spinner_movie.state() != QMovie.MovieState.Running:
                self.spinner_movie.start()
            self.loading_text.setText("Analisi del modello in corso...")
            return
        # stop spinner
        self.loading_container.hide()
        if self.spinner_movie.state() == QMovie.MovieState.Running:
            self.spinner_movie.stop()
        self.signal_label.show()
        direction = trading_signal.get('direction', 'NEUTRAL')
        confidence = trading_signal.get('confidence', 0)
        stop_loss = trading_signal.get('stop_loss')
        take_profit = trading_signal.get('take_profit')
        # Set style for bearish
        if direction == 'BEARISH':
            self.signal_frame.setProperty("class", "bearish")
            self.signal_label.setProperty("class", "bearish")
            self.accent_bar.setStyleSheet("#AccentBar { background-color: #ff6b6b; border-radius: 5px; }")
        elif direction == 'BULLISH':
            self.signal_frame.setProperty("class", "")
            self.signal_label.setProperty("class", "")
            self.accent_bar.setStyleSheet("#AccentBar { background-color: #2ecc71; border-radius: 5px; }")
        else:
            self.signal_label.setProperty("class", "")
            self.accent_bar.setStyleSheet(f"#AccentBar {{ background-color: {neutral_color}; border-radius: 5px; }}")
        self.signal_label.setText(f"{direction} - Confidence: {confidence}%")
        info_lines = []
        if stop_loss is not None:
            info_lines.append(f"Stop Loss: {stop_loss}")
        if take_profit is not None:
            info_lines.append(f"Take Profit: {take_profit}")
        if info_lines:
            self.signal_info.setText("\n".join(info_lines))
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
        self.setFixedWidth(340)
        
        self.popup_duration_ms = popup_duration_ms
        self.panel_width = 280
        self.is_visible = False
        
        # Aggiungi pulsante per cambiare vista
        self._add_view_toggle_button()
        
        # Animazione per la geometria
        self.animation = QPropertyAnimation(self, b"pos")
        self.animation.setDuration(0)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.opacity_anim.setDuration(550)
        self.opacity_anim.setEasingCurve(QEasingCurve.Type.InOutCubic)

        # Timer per nascondere automaticamente il popup
        self.auto_hide_timer = QTimer(self)
        self.auto_hide_timer.setSingleShot(True)
        self.auto_hide_timer.timeout.connect(self.slide_out)
        
        # Permetti modalità floating con sfondo trasparente stile "notifica"
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setStyleSheet(self.styleSheet() + "\n#NewsCard { background-color: rgba(45,45,45,0.88); border: 1px solid rgba(255,255,255,0.08);} ")
        
        self.update_geometry(force_hide=True)
        self.hide()
    def _add_view_toggle_button(self):
        """Aggiunge un pulsante per cambiare vista nella header del flyout."""
        if hasattr(self, 'header_layout'):
            assets_dir = os.path.dirname(os.path.abspath(__file__))
            grid_icon_path = os.path.join(assets_dir, "grid.svg")

            view_button = QPushButton(" View")
            view_button.setObjectName("ViewToggleButton")
            if os.path.exists(grid_icon_path):
                view_button.setIcon(QIcon(grid_icon_path))
                view_button.setIconSize(QSize(16, 16))

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
        self.hidden_geo = QRect(screen_x + screen_w - self.panel_width - 16, screen_y + 16,
                                self.panel_width, screen_h - 32)
        
        if force_hide:
            self.setGeometry(self.hidden_geo)
            self.opacity_effect.setOpacity(0.0)
            self.is_visible = False
        elif self.is_visible:
            self.setGeometry(self.visible_geo)
            self.opacity_effect.setOpacity(1.0)
        else:
            self.setGeometry(self.hidden_geo)
            self.opacity_effect.setOpacity(0.0)

    def slide_in(self):
        """Anima la sidebar per farla entrare in vista."""
        self.update_geometry()
        
        if self.is_visible:
            # Se è già visibile, riavvia il timer (es. per un nuovo popup)
            self.auto_hide_timer.start(self.popup_duration_ms)
            return
            
        self.opacity_anim.stop()
        self.opacity_anim.setStartValue(0.0)
        self.opacity_anim.setEndValue(1.0)
        self.show()
        self.raise_()  # Porta il widget in primo piano
        self.activateWindow()  # Assicura che il widget sia attivo
        self.opacity_anim.start()
        self.is_visible = True
        # Avvia il timer per auto-hide dopo il popup_duration_ms
        self.auto_hide_timer.start(self.popup_duration_ms)

    def slide_out(self):
        """Anima la sidebar per farla uscire dalla vista."""
        if not self.is_visible:
            return
            
        self.update_geometry()
        self.opacity_anim.stop()
        self.opacity_anim.setStartValue(1.0)
        self.opacity_anim.setEndValue(0.0)
        self.opacity_anim.finished.connect(self._hide_after_fade)
        self.opacity_anim.start()
        self.is_visible = False

    def _hide_after_fade(self):
        if not self.is_visible:
            self.hide()
        try:
            self.opacity_anim.finished.disconnect(self._hide_after_fade)
        except Exception:
            pass

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

from PyQt6.QtGui import QIcon

class SettingsDialog(QDialog):
    """
    Finestra di dialogo per le impostazioni dell'applicazione.
    """

    @staticmethod
    def _update_toggle_text(button: QPushButton):
        button.setText("ON" if button.isChecked() else "OFF")

    def _create_toggle(self, initial_state: bool = False) -> QPushButton:
        btn = QPushButton()
        btn.setObjectName("SettingToggle")
        btn.setCheckable(True)
        btn.setChecked(initial_state)
        self._update_toggle_text(btn)
        btn.toggled.connect(lambda checked, b=btn: self._update_toggle_text(b))
        return btn

    def __init__(self, current_settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Impostazioni")
        self.setWindowIcon(QIcon("gear.svg"))
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
        self.only_watchlist_toggle = self._create_toggle(current_settings.get('news_only_watchlist', False))
        form_layout.addRow(QLabel("Mostra solo notizie della watchlist:"), self.only_watchlist_toggle)

        # --- Sorgenti news ---
        self.enable_yahoo_toggle = self._create_toggle(current_settings.get('enable_yahoo_news', True))
        form_layout.addRow(QLabel("Abilita Yahoo News:"), self.enable_yahoo_toggle)

        self.enable_x_toggle = self._create_toggle(current_settings.get('enable_x_news', False))
        form_layout.addRow(QLabel("Abilita X (Twitter) News:"), self.enable_x_toggle)

        self.x_api_token_input = QLineEdit(current_settings.get('x_api_token', ''))
        self.x_api_token_input.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow(QLabel("X API Token:"), self.x_api_token_input)

        self.x_profiles_input = QTextEdit("\n".join(current_settings.get('x_profiles', [])))
        self.x_profiles_input.setPlaceholderText("https://x.com/user1\nhttps://x.com/user2")
        self.x_profiles_input.setFixedHeight(80)
        form_layout.addRow(QLabel("Profili X da monitorare (uno per riga):"), self.x_profiles_input)

        # --- Indicatori grafico ---
        layout.addWidget(QLabel("Indicatori", objectName="SectionTitle"))
        self.show_rsi_toggle = self._create_toggle(current_settings.get('show_rsi_indicator', current_settings.get('indicators', {}).get('rsi', False)))
        form_layout.addRow(QLabel("Mostra RSI:"), self.show_rsi_toggle)

        self.show_volume_toggle = self._create_toggle(current_settings.get('show_volume_panel', True))
        form_layout.addRow(QLabel("Mostra Volumi:"), self.show_volume_toggle)

        self.show_volume_strength_toggle = self._create_toggle(current_settings.get('indicators', {}).get('vs', False) or current_settings.get('show_volume_strength', False))
        form_layout.addRow(QLabel("Mostra Volume Strength:"), self.show_volume_strength_toggle)

        self.show_run_toggle = self._create_toggle(current_settings.get('indicators', {}).get('run', False) or current_settings.get('show_run_indicator', False))
        form_layout.addRow(QLabel("Mostra Run (RSI Divergence):"), self.show_run_toggle)

        # Moving Averages
        self.show_ma13_toggle = self._create_toggle(current_settings.get('indicators', {}).get('ma13', False) or current_settings.get('show_ma13', False))
        form_layout.addRow(QLabel("Mostra MA 13:"), self.show_ma13_toggle)

        self.show_ma50_toggle = self._create_toggle(current_settings.get('indicators', {}).get('ma50', False) or current_settings.get('show_ma50', False))
        form_layout.addRow(QLabel("Mostra MA 50:"), self.show_ma50_toggle)

        self.show_ma200_toggle = self._create_toggle(current_settings.get('indicators', {}).get('ma200', False) or current_settings.get('show_ma200', False))
        form_layout.addRow(QLabel("Mostra MA 200:"), self.show_ma200_toggle)

        self.show_ma800_toggle = self._create_toggle(current_settings.get('indicators', {}).get('ma800', False) or current_settings.get('show_ma800', False))
        form_layout.addRow(QLabel("Mostra MA 800:"), self.show_ma800_toggle)

        # --- Modello ---
        layout.addWidget(QLabel("Modello AI", objectName="SectionTitle"))
        self.use_cuda_toggle = self._create_toggle(current_settings.get('use_cuda', False))
        form_layout.addRow(QLabel("Usa CUDA (NVIDIA):"), self.use_cuda_toggle)

        # Modello: spunte separate
        self.model_use_rsi_toggle = self._create_toggle(current_settings.get('model_use_rsi', False) or current_settings.get('model_use_indicators', False))
        form_layout.addRow(QLabel("Il modello usa RSI:"), self.model_use_rsi_toggle)

        self.model_use_volume_toggle = self._create_toggle(current_settings.get('model_use_volume', False) or current_settings.get('model_use_indicators', False))
        form_layout.addRow(QLabel("Il modello usa Volumi:"), self.model_use_volume_toggle)

        self.model_use_volume_strength_toggle = self._create_toggle(current_settings.get('model_use_volume_strength', False))
        form_layout.addRow(QLabel("Il modello usa Volume Strength:"), self.model_use_volume_strength_toggle)

        self.model_use_mas_toggle = self._create_toggle(current_settings.get('model_use_mas', False))
        form_layout.addRow(QLabel("Il modello usa Moving Averages:"), self.model_use_mas_toggle)
        
        ##### INIZIO MODIFICA SSL #####
        
        # --- Impostazione SSL ---
        layout.addWidget(QLabel("Sicurezza", objectName="SectionTitle"))
        self.ssl_verify_toggle = self._create_toggle(current_settings.get('ssl_verify', True))
        self.ssl_verify_toggle.setToolTip(
            "Disabilita questa opzione SOLO se sei su una rete aziendale\n"
            "che causa problemi di certificato SSL.\n"
            "ATTENZIONE: Rende la connessione insicura."
        )
        form_layout.addRow(QLabel("Abilita Verifica SSL (Sicuro):"), self.ssl_verify_toggle)
        
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
            'ssl_verify': self.ssl_verify_toggle.isChecked(),
            'use_cuda': self.use_cuda_toggle.isChecked(),
            'enable_yahoo_news': self.enable_yahoo_toggle.isChecked(),
            'enable_x_news': self.enable_x_toggle.isChecked(),
            'x_api_token': self.x_api_token_input.text(),
            'x_profiles': x_profiles,
            'news_only_watchlist': self.only_watchlist_toggle.isChecked(),
            'show_rsi_indicator': self.show_rsi_toggle.isChecked(),
            'show_volume_panel': self.show_volume_toggle.isChecked(),
            'show_volume_strength': self.show_volume_strength_toggle.isChecked(),
            'show_run_indicator': self.show_run_toggle.isChecked(),
            'show_ma13': self.show_ma13_toggle.isChecked(),
            'show_ma50': self.show_ma50_toggle.isChecked(),
            'show_ma200': self.show_ma200_toggle.isChecked(),
            'show_ma800': self.show_ma800_toggle.isChecked(),
            'model_use_rsi': self.model_use_rsi_toggle.isChecked(),
            'model_use_volume': self.model_use_volume_toggle.isChecked(),
            'model_use_volume_strength': self.model_use_volume_strength_toggle.isChecked(),
            'model_use_mas': self.model_use_mas_toggle.isChecked(),
        }
    