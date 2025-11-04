import sys
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QFrame, QScrollArea,
                             QDialog, QLineEdit, QDialogButtonBox, QFormLayout,
                             QSizePolicy, QSpinBox, QHBoxLayout, QPushButton,
                             QCheckBox) # <-- AGGIUNTO QCheckBox
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QPropertyAnimation, QRect, QTimer, pyqtProperty

from PyQt6.QtGui import QDesktopServices, QColor
from PyQt6.QtCore import QUrl

STYLESHEET = """
/* Stile per la Card della Notizia */
#NewsCard {
    background-color: #2d2d2d;
    border: 1px solid #444444;
    border-radius: 12px;
    margin-bottom: 12px;
    padding: 14px;
    min-height: 140px;
}
#NewsCard:hover {
    background-color: #3a3a3a;
    border-color: #555555;
}
#NewsTitle {
    font-size: 16px;
    font-weight: bold;
    color: #f0f0f0;
    padding: 4px 0px;
}
#NewsInfo {
    font-size: 12px;
    color: #888888;
    font-style: italic;
    margin-top: 4px;
}
#NewsSummary {
    font-size: 15px;
    color: #d0d0d0;
    padding: 8px 0px;
    line-height: 1.6;
}
#TradingSignal {
    background-color: #2a4a2a;
    border: 1px solid #3a6a3a;
    border-radius: 8px;
    padding: 10px;
    margin-top: 10px;
}
#TradingSignal.bearish {
    background-color: #4a2a2a;
    border-color: #6a3a3a;
}
#SignalLabel {
    font-size: 13px;
    font-weight: bold;
    color: #90ee90;
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

/* Stile per il Pannello Impostazioni */
QDialog {
    background-color: #2d2d2d;
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

        text_content = news_item.get('text', '')
        if text_content:
            summary_label = QLabel(text_content)
            summary_label.setObjectName("NewsSummary")
            summary_label.setWordWrap(True)
            summary_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
            summary_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            layout.addWidget(summary_label)

        # Aggiungi trading signal se disponibile
        trading_signal = news_item.get('trading_signal')
        if trading_signal:
            signal_frame = QFrame()
            signal_frame.setObjectName("TradingSignal")
            if trading_signal.get('direction') == 'BEARISH':
                signal_frame.setProperty("class", "bearish")
            
            signal_layout = QVBoxLayout(signal_frame)
            signal_layout.setSpacing(4)
            
            direction = trading_signal.get('direction', 'NEUTRAL')
            confidence = trading_signal.get('confidence', 0)
            stop_loss = trading_signal.get('stop_loss')
            take_profit = trading_signal.get('take_profit')
            
            signal_label = QLabel(f"{direction} - Confidence: {confidence}%")
            signal_label.setObjectName("SignalLabel")
            if direction == 'BEARISH':
                signal_label.setProperty("class", "bearish")
            signal_layout.addWidget(signal_label)
            
            if stop_loss and take_profit:
                signal_info = QLabel(f"Stop Loss: {stop_loss}\nTake Profit: {take_profit}")
                signal_info.setObjectName("SignalInfo")
                signal_layout.addWidget(signal_info)
            
            layout.addWidget(signal_frame)

        self.setStyleSheet(STYLESHEET)
    
    def mousePressEvent(self, event):
        """Apre il link della notizia nel browser."""
        if self.link:
            QDesktopServices.openUrl(QUrl(self.link))
        event.accept()

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
        header_layout = QHBoxLayout()
        title_label = QLabel("Feed Notizie")
        title_label.setObjectName("PanelTitle")
        title_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)
        
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
        
        # Imposta come widget senza parent (floating) per essere sopra la finestra principale
        if parent:
            self.setParent(parent)
            # Non impostare window flags qui, sarà gestito come widget normale sopra la finestra
        
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
        """Aggiorna la posizione della sidebar (nascosta o visibile) in base alla finestra principale."""
        if not self.parent(): 
            return
        
        # Ottieni la geometria della finestra principale
        parent_widget = self.parent()
        if hasattr(parent_widget, 'geometry'):
            parent_geo = parent_widget.geometry()
        else:
            parent_geo = parent_widget.rect()
        
        parent_width = parent_geo.width()
        parent_height = parent_geo.height()
        parent_x = parent_geo.x()
        parent_y = parent_geo.y()
        
        # Posizione visibile (dentro la finestra, sul lato destro)
        self.visible_geo = QRect(parent_x + parent_width - self.panel_width, parent_y,
                                 self.panel_width, parent_height)
        # Posizione nascosta (fuori dalla finestra, a destra)
        self.hidden_geo = QRect(parent_x + parent_width, parent_y,
                                self.panel_width, parent_height)
        
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
        self.add_card(news_item)
        self.slide_in()
        # Avvia il timer per nascondere automaticamente
        self.auto_hide_timer.start(self.popup_duration_ms)

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
        
        ##### INIZIO MODIFICA SSL #####
        
        # Rimosso: popup_duration_input (non era usato nel tuo graph.py,
        # ma puoi rimetterlo se ti serve)
        
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
        
        return {
            'news_tickers': tickers_list,
            # 'view_popup_duration_s': self.popup_duration_input.value(), # Decommenta se usi
            'ssl_verify': self.ssl_verify_checkbox.isChecked() # <-- Aggiunto
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
        
        ##### INIZIO MODIFICA SSL #####
        
        # Rimosso: popup_duration_input (non era usato nel tuo graph.py,
        # ma puoi rimetterlo se ti serve)
        
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
        
        return {
            'news_tickers': tickers_list,
            # 'view_popup_duration_s': self.popup_duration_input.value(), # Decommenta se usi
            'ssl_verify': self.ssl_verify_checkbox.isChecked() # <-- Aggiunto
        }