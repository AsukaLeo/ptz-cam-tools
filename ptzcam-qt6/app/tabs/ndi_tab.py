"""NDI stream tab page."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox
)
from PySide6.QtCore import Qt
from typing import Optional, Callable

from app.styles.theme import get_control_card_style, get_primary_button_style, get_danger_button_style
from app.utils.constants import STATUS_CONNECTING, STATUS_DISCONNECTED


class NDITab(QWidget):
    """NDI stream configuration tab.
    
    Provides NDI source discovery and connection controls.
    """
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize the NDI tab.
        
        Args:
            parent: Optional parent widget.
        """
        super().__init__(parent)
        self.on_status_update: Optional[Callable[[str], None]] = None
        self.preview_widget: Optional[QWidget] = None
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Set up the tab UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 8)
        layout.setSpacing(8)
        
        # Control card
        card = self._create_control_card()
        layout.addWidget(card)
        
        # Preview area placeholder
        self._preview_placeholder = QWidget()
        layout.addWidget(self._preview_placeholder, 1)
    
    def _create_control_card(self) -> QWidget:
        """Create the control card with NDI controls.
        
        Returns:
            Configured control card widget.
        """
        from PySide6.QtWidgets import QFrame
        from app.styles.theme import get_standard_button_style
        
        card = QFrame()
        card.setObjectName("controlCard")
        card.setStyleSheet(get_control_card_style())
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(12, 10, 12, 10)
        card_layout.setSpacing(6)
        
        # Source row
        src_row = QHBoxLayout()
        src_row.setSpacing(8)
        
        src_label = QLabel("NDI 源:")
        src_label.setFixedWidth(80)
        src_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        src_row.addWidget(src_label)
        
        src_combo = QComboBox()
        src_combo.addItems(["(未发现 NDI 源)"])
        src_combo.setFixedWidth(200)
        src_row.addWidget(src_combo)
        
        refresh_btn = QPushButton("刷新")
        refresh_btn.setStyleSheet(get_standard_button_style())
        refresh_btn.clicked.connect(lambda: self._notify_status("搜索 NDI 源..."))
        src_row.addWidget(refresh_btn)
        
        connect_btn = QPushButton("连接")
        connect_btn.setStyleSheet(get_primary_button_style())
        connect_btn.clicked.connect(lambda: self._notify_status(STATUS_CONNECTING))
        src_row.addWidget(connect_btn)
        
        disconnect_btn = QPushButton("断开")
        disconnect_btn.setStyleSheet(get_danger_button_style())
        disconnect_btn.clicked.connect(lambda: self._notify_status(STATUS_DISCONNECTED))
        src_row.addWidget(disconnect_btn)
        
        src_row.addStretch()
        card_layout.addLayout(src_row)
        
        return card
    
    def set_preview_widget(self, widget: QWidget) -> None:
        """Set the video preview widget.
        
        Args:
            widget: Preview widget to display.
        """
        layout = self.layout()
        layout.replaceWidget(self._preview_placeholder, widget)
        self._preview_placeholder.hide()
        self.preview_widget = widget
    
    def _notify_status(self, message: str) -> None:
        """Notify status update via callback."""
        if self.on_status_update:
            self.on_status_update(message)
    
    def set_status_callback(self, callback: Callable[[str], None]) -> None:
        """Set the status update callback."""
        self.on_status_update = callback
