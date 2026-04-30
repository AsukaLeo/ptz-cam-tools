"""ONVIF camera tab page."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QLineEdit
)
from PySide6.QtCore import Qt
from typing import Optional, Callable

from app.styles.theme import (
    get_control_card_style,
    get_standard_button_style,
    get_primary_button_style,
    get_danger_button_style,
)
from app.utils.constants import STATUS_CONNECTING, STATUS_DISCONNECTED


class ONVIFTab(QWidget):
    """ONVIF camera configuration tab.
    
    Provides device discovery, connection, and authentication controls.
    """
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize the ONVIF tab.
        
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
        """Create the control card with ONVIF controls.
        
        Returns:
            Configured control card widget.
        """
        from PySide6.QtWidgets import QFrame
        
        card = QFrame()
        card.setObjectName("controlCard")
        card.setStyleSheet(get_control_card_style())
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(12, 10, 12, 10)
        card_layout.setSpacing(6)
        
        # IP/Port row
        ip_row = QHBoxLayout()
        ip_row.setSpacing(8)
        
        ip_label = QLabel("IP 地址:")
        ip_label.setFixedWidth(80)
        ip_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        ip_row.addWidget(ip_label)
        
        ip_edit = QLineEdit("192.168.1.64")
        ip_edit.setFixedWidth(120)
        ip_row.addWidget(ip_edit)
        
        port_label = QLabel("端口:")
        port_label.setFixedWidth(40)
        ip_row.addWidget(port_label)
        
        port_edit = QLineEdit("80")
        port_edit.setFixedWidth(60)
        ip_row.addWidget(port_edit)
        
        discover_btn = QPushButton("发现")
        discover_btn.setStyleSheet(get_standard_button_style())
        discover_btn.clicked.connect(lambda: self._notify_status("发现设备..."))
        ip_row.addWidget(discover_btn)
        
        connect_btn = QPushButton("连接")
        connect_btn.setStyleSheet(get_primary_button_style())
        connect_btn.clicked.connect(lambda: self._notify_status(STATUS_CONNECTING))
        ip_row.addWidget(connect_btn)
        
        disconnect_btn = QPushButton("断开")
        disconnect_btn.setStyleSheet(get_danger_button_style())
        disconnect_btn.clicked.connect(lambda: self._notify_status(STATUS_DISCONNECTED))
        ip_row.addWidget(disconnect_btn)
        
        ip_row.addStretch()
        card_layout.addLayout(ip_row)
        
        # Auth row
        auth_row = QHBoxLayout()
        auth_row.setSpacing(8)
        
        user_label = QLabel("用户名:")
        user_label.setFixedWidth(80)
        user_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        auth_row.addWidget(user_label)
        
        user_edit = QLineEdit("admin")
        user_edit.setFixedWidth(100)
        auth_row.addWidget(user_edit)
        
        pass_label = QLabel("密码:")
        pass_label.setFixedWidth(40)
        auth_row.addWidget(pass_label)
        
        pass_edit = QLineEdit()
        pass_edit.setEchoMode(QLineEdit.Password)
        pass_edit.setFixedWidth(100)
        auth_row.addWidget(pass_edit)
        
        auth_row.addStretch()
        card_layout.addLayout(auth_row)
        
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
