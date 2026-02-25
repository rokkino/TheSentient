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

# STYLESHEET RIMOSSO - ORA CARICATO DA FILE ESTERNO (style.qss)


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

        # --- LAYOUT SEMPLIFICATO ---
        outer_layout = QHBoxLayout(self)
        outer_layout.setContentsMargins(8, 8, 8, 8) # Reduced margins
        outer_layout.setSpacing(8)

        self.accent_bar = QFrame()
        self.accent_bar.setObjectName("AccentBar")
        # Width is handled in CSS
        outer_layout.addWidget(self.accent_bar)

        layout = QVBoxLayout()
        layout.setSpacing(4) # Reduced spacing
        outer_layout.addLayout(layout, 1)
        
        # Header: Title + Meta
        header_layout = QVBoxLayout()
        header_layout.setSpacing(2)
        
        title_label = QLabel(title)
        title_label.setObjectName("NewsTitle")
        title_label.setWordWrap(True)
        header_layout.addWidget(title_label)

        meta_layout = QHBoxLayout()
        meta_layout.setSpacing(6)
        meta_layout.setContentsMargins(0, 0, 0, 0)
        
        if ticker:
            ticker_chip = QLabel(ticker)
            ticker_chip.setObjectName("MetaChip")
            meta_layout.addWidget(ticker_chip)
            
        if publisher:
            source_chip = QLabel(publisher)
            source_chip.setObjectName("MetaChip")
            meta_layout.addWidget(source_chip)
            
        time_str = timestamp.strftime('%H:%M') if timestamp else ''
        if time_str:
            time_label = QLabel(time_str)
            time_label.setObjectName("MetaTime")
            meta_layout.addWidget(time_label)
            
        meta_layout.addStretch()
        header_layout.addLayout(meta_layout)
        layout.addLayout(header_layout)

        divider = QFrame()
        divider.setObjectName("SummaryDivider")
        divider.setFixedHeight(1)
        layout.addWidget(divider)

        # Content: Summary + Read Button
        self.summary_label = QLabel(news_item.get('summary') or news_item.get('text') or title)
        self.summary_label.setObjectName("NewsSummary")
        self.summary_label.setWordWrap(True)
        self.summary_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        # Limit height/lines via CSS or just let it flow, but we reduced min-height
        layout.addWidget(self.summary_label)
        
        self.read_button = QPushButton("Leggi tutto >")
        self.read_button.setObjectName("ReadButton")
        self.read_button.setVisible(bool(self.link))
        self.read_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.read_button.clicked.connect(self._on_read_clicked)
        layout.addWidget(self.read_button)

        # Trading signal area
        self.signal_frame = QFrame()
        self.signal_frame.setObjectName("TradingSignal")
        self.signal_layout = QVBoxLayout(self.signal_frame)
        self.signal_layout.setContentsMargins(8, 8, 8, 8)
        self.signal_layout.setSpacing(4)
        
        # Small spinner for AI analysis state
        self.loading_container = QWidget()
        loading_layout = QHBoxLayout(self.loading_container)
        loading_layout.setContentsMargins(0, 0, 0, 0)
        loading_layout.setSpacing(8)
        loading_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        self.spinner_label = QLabel()
        # Assicurati che spinner.gif esista o usa un testo
        if os.path.exists("spinner.gif"):
            self.spinner_movie = QMovie("spinner.gif")
            self.spinner_movie.setScaledSize(QSize(16, 16))
            self.spinner_label.setMovie(self.spinner_movie)
        else:
            self.spinner_label.setText("...")
            self.spinner_movie = None
            
        loading_layout.addWidget(self.spinner_label)
        self.loading_text = QLabel("Analisi AI...")
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
        
        # RIMOSSO setStyleSheet(STYLESHEET) - ora ereditato

    
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
        self.accent_bar.setProperty("class", "") # Reset accent bar class
        
        if not trading_signal or trading_signal.get('status') == 'loading':
            self.loading_container.show()
            self.signal_label.hide()
            self.signal_info.hide()
            if self.spinner_movie and self.spinner_movie.state() != QMovie.MovieState.Running:
                self.spinner_movie.start()
            self.loading_text.setText("Analisi AI...")
            return

        # stop spinner
        self.loading_container.hide()
        if self.spinner_movie and self.spinner_movie.state() == QMovie.MovieState.Running:
            self.spinner_movie.stop()
            
        self.signal_label.show()
        direction = trading_signal.get('direction', 'NEUTRAL')
        confidence = trading_signal.get('confidence', 0)
        stop_loss = trading_signal.get('stop_loss')
        take_profit = trading_signal.get('take_profit')

        # Set style for bearish/bullish via dynamic properties and CSS
        if direction == 'BEARISH':
            self.signal_frame.setProperty("class", "bearish")
            self.signal_label.setProperty("class", "bearish")
            self.accent_bar.setStyleSheet("#AccentBar { background-color: #ff6b6b; }") 
        elif direction == 'BULLISH':
            self.signal_frame.setProperty("class", "bullish")
            self.signal_label.setProperty("class", "bullish")
            self.accent_bar.setStyleSheet("#AccentBar { background-color: #2ecc71; }")
        else:
            self.signal_label.setProperty("class", "")
            self.accent_bar.setStyleSheet("#AccentBar { background-color: #007acc; }")

        self.signal_label.setText(f"{direction} ({confidence}%)")
        
        info_lines = []
        if stop_loss: info_lines.append(f"SL: {stop_loss}")
        if take_profit: info_lines.append(f"TP: {take_profit}")
        
        if info_lines:
            self.signal_info.setText(" | ".join(info_lines))
            self.signal_info.setVisible(True)
        else:
            self.signal_info.setVisible(False)
            
        # Force style update
        self.style().unpolish(self.signal_frame)
        self.style().polish(self.signal_frame)
        self.style().unpolish(self.signal_label)
        self.style().polish(self.signal_label)

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
        
        # self.setStyleSheet(STYLESHEET) RIMOSSO


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
        self.manually_moved = False # Flag per posizione manuale
        
        # Aggiungi pulsante per cambiare vista
        self._add_view_toggle_button()
        
        # Animazione per la geometria
        self.animation = QPropertyAnimation(self, b"pos")
        self.animation.setDuration(0)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        
        # Animazione Opacità (su windowOpacity invece di QGraphicsOpacityEffect)
        self.opacity_anim = QPropertyAnimation(self, b"windowOpacity")
        self.opacity_anim.setDuration(300)
        self.opacity_anim.setEasingCurve(QEasingCurve.Type.InOutCubic)

        # Timer per nascondere automaticamente il popup
        self.auto_hide_timer = QTimer(self)
        self.auto_hide_timer.setSingleShot(True)
        self.auto_hide_timer.timeout.connect(self.slide_out)
        
        # Permetti modalità floating con sfondo trasparente stile "notifica"
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
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

    def mousePressEvent(self, event):
        """Gestisce il click per il trascinamento (solo header)."""
        if event.button() == Qt.MouseButton.LeftButton:
            # Permetti trascinamento solo se si clicca nella parte alta (header)
            if event.position().y() < 60: 
                self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                self.auto_hide_timer.stop() # Ferma timer durante trascinamento
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Gestisce il movimento durante il trascinamento."""
        if hasattr(self, '_drag_pos') and self._drag_pos and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            self.manually_moved = True # Segna come spostato manualmente
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Gestisce il rilascio del mouse."""
        if hasattr(self, '_drag_pos') and self._drag_pos:
            self._drag_pos = None
            # Aggiorna la geometria visibile alla posizione corrente
            self.visible_geo = self.geometry()
            
            # Riavvia timer se necessario, o lascia che sia leaveEvent a gestirlo
            if not self.underMouse():
                self.schedule_slide_out(500)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def enterEvent(self, event):
        """Quando il mouse entra nel pannello, annulla il timer di auto-hide."""
        self.auto_hide_timer.stop()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Quando il mouse esce, programma un'uscita ritardata."""
        self.schedule_slide_out(500) # Nascondi dopo 0.5s
        super().leaveEvent(event)
        
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

    def slide_in(self, screen=None):
        """Anima la sidebar per farla entrare in vista."""
        self.update_geometry(screen=screen) # Aggiorna geometria per lo schermo target
        
        if self.is_visible:
            return
            
        self.is_visible = True
        self.show()
        self.raise_()
        
        self.animation.stop()
        self.animation.setStartValue(self.pos())
        self.animation.setEndValue(self.visible_geo.topLeft())
        self.animation.setDuration(300)
        self.animation.start()
        
        # Fade in
        self.opacity_anim.stop()
        self.opacity_anim.setStartValue(self.windowOpacity())
        self.opacity_anim.setEndValue(1.0)
        self.opacity_anim.start()
        
        # Avvia il timer per auto-hide dopo il popup_duration_ms
        self.auto_hide_timer.start(self.popup_duration_ms)

    def slide_out(self):
        """Anima la sidebar per nasconderla."""
        if not self.is_visible:
            return
            
        self.is_visible = False
        
        self.animation.stop()
        self.animation.setStartValue(self.pos())
        self.animation.setEndValue(self.hidden_geo.topLeft())
        self.animation.setDuration(300)
        self.animation.start()
        
        # Fade out
        self.opacity_anim.stop()
        self.opacity_anim.setStartValue(self.windowOpacity())
        self.opacity_anim.setEndValue(0.0)
        self.opacity_anim.finished.connect(self._hide_after_fade)
        self.opacity_anim.start()

    def _hide_after_fade(self):
        if not self.is_visible:
            self.hide()
        try:
            self.opacity_anim.finished.disconnect(self._hide_after_fade)
        except Exception:
            pass

    def update_geometry(self, force_hide=False, screen=None):
        """Aggiorna la posizione della sidebar; se floating, aggancia al bordo destro dello schermo."""
        from PyQt6.QtWidgets import QApplication
        if screen is None:
            screen = QApplication.primaryScreen()
            # Se il widget è già visibile, cerca di mantenere lo schermo corrente
            if self.isVisible():
                curr_screen = QApplication.screenAt(self.pos())
                if curr_screen:
                    screen = curr_screen
        
        if not screen:
            return

        geo = screen.availableGeometry()
        screen_x = geo.x()
        screen_y = geo.y()
        screen_w = geo.width()
        screen_h = geo.height()

        # Margini e posizionamento
        margin_top = 50
        margin_bottom = 50
        
        target_x = screen_x + screen_w - self.panel_width - 20 # 20px dal bordo destro
        target_y = screen_y + margin_top
        target_h = screen_h - margin_top - margin_bottom

        # Calcola geometria standard
        standard_visible_geo = QRect(target_x, target_y, self.panel_width, target_h)
        
        # Se non spostato manualmente, usa standard
        if not self.manually_moved:
            self.visible_geo = standard_visible_geo
            
        # Hidden geo: sempre spostato a destra fuori dallo schermo (relativo allo schermo corrente)
        self.hidden_geo = QRect(screen_x + screen_w, target_y, self.panel_width, target_h)
        
        if force_hide:
            self.setGeometry(self.hidden_geo)
            self.setWindowOpacity(0.0)
            self.is_visible = False
        elif self.is_visible:
            self.setGeometry(self.visible_geo)
            self.setWindowOpacity(1.0)
        else:
            self.setGeometry(self.hidden_geo)
            self.setWindowOpacity(0.0)

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
    