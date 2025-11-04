import sys
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QFrame, QScrollArea,
                             QDialog, QLineEdit, QDialogButtonBox, QFormLayout,
                             QSizePolicy, QSpinBox)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QPropertyAnimation, QRect, QTimer, pyqtProperty
from PyQt6.QtGui import QDesktopServices, QColor
from PyQt6.QtCore import QUrl

STYLESHEET = """
/* Stile per la Card della Notizia */
#NewsCard {
    background-color: #2d2d2d;
    border: 1px solid #444444;
    border-radius: 5px;
    margin-bottom: 8px;
    min-height: 100px; /* Assicura un'altezza minima */
}
#NewsCard:hover {
    background-color: #3a3a3a;
}
#NewsTitle {
    font-size: 14px;
    font-weight: bold;
    color: #e0e0e0;
}
#NewsInfo {
    font-size: 12px;
    color: #888888;
    font-style: italic;
}
#NewsSummary {
    font-size: 13px;
    color: #b0b0b0;
}

/* Stile per la ScrollArea della Sidebar */
QScrollArea {
    border: none;
    background-color: #1e1e1e;
}
#ScrollAreaWidget {
    background-color: #1e1e1e;
}

/* Stile per il Pannello Impostazioni */
QDialog {
    background-color: #2d2d2d;
    color: #dcdcdc;
}
QLineEdit, QSpinBox {
    background-color: #1e1e1e;
    border: 1px solid #444444;
    border-radius: 5px;
    padding: 5px;
    color: #dcdcdc;
}
QFormLayout > QLabel {
    font-weight: bold;
}
"""

class NewsCard(QFrame):
    """
    Un widget cliccabile che mostra una singola notizia.
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
        
        title_label = QLabel(title)
        title_label.setObjectName("NewsTitle")
        title_label.setWordWrap(True)
        layout.addWidget(title_label)
        
        time_str = timestamp.strftime('%H:%M') if timestamp else ''
        info_str = f"{publisher} ({ticker}) - {time_str}"
        info_label = QLabel(info_str)
        info_label.setObjectName("NewsInfo")
        layout.addWidget(info_label)

        summary_label = QLabel(news_item.get('text'))
        summary_label.setObjectName("NewsSummary")
        summary_label.setWordWrap(True)
        layout.addStretch() # Spinge il contenuto in alto
        layout.addWidget(summary_label)

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
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        title_label = QLabel("Feed Notizie")
        title_label.setObjectName("PanelTitle")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)
        
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
    """
    def __init__(self, popup_duration_ms, parent=None):
        super().__init__(parent)
        
        self.popup_duration_ms = popup_duration_ms
        self.panel_width = self.width()
        self.is_visible = False
        
        # Animazione per la geometria
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(300) # 300ms per l'animazione
        
        # Timer per nascondere automaticamente il popup
        self.auto_hide_timer = QTimer(self)
        self.auto_hide_timer.setSingleShot(True)
        self.auto_hide_timer.timeout.connect(self.slide_out)
        
        self.update_geometry(force_hide=True)
        self.hide()

    def update_geometry(self, force_hide=False):
        """Aggiorna la posizione della sidebar (nascosta o visibile) in base alla finestra principale."""
        if not self.parent(): return
        
        parent_rect = self.parent().rect()
        
        # Posizione visibile (dentro la finestra)
        self.visible_geo = QRect(parent_rect.width() - self.panel_width, 0,
                                 self.panel_width, parent_rect.height())
        # Posizione nascosta (fuori dalla finestra)
        self.hidden_geo = QRect(parent_rect.width(), 0,
                                self.panel_width, parent_rect.height())
        
        if force_hide:
            self.setGeometry(self.hidden_geo)
            self.is_visible = False
        elif self.is_visible:
            self.setGeometry(self.visible_geo)
        else:
            self.setGeometry(self.hidden_geo)

    def slide_in(self):
        """Anima la sidebar per farla entrare in vista."""
        if self.is_visible:
            # Se è già visibile, riavvia il timer (es. per un nuovo popup)
            if self.auto_hide_timer.isActive():
                self.auto_hide_timer.start(self.popup_duration_ms)
            return
            
        self.update_geometry()
        self.animation.setStartValue(self.hidden_geo)
        self.animation.setEndValue(self.visible_geo)
        self.show()
        self.animation.start()
        self.is_visible = True

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
        
        # --- Impostazioni Vista ---
        self.popup_duration_input = QSpinBox()
        self.popup_duration_input.setRange(2, 30) # Da 2 a 30 secondi
        self.popup_duration_input.setSuffix(" sec")
        self.popup_duration_input.setValue(current_settings.get('view_popup_duration_s', 5))
        form_layout.addRow(QLabel("Durata Popup Notizie (Vista 3):"), self.popup_duration_input)

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
            'view_popup_duration_s': self.popup_duration_input.value()
        }