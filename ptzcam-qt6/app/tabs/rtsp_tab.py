"""RTSP stream tab page."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QLineEdit
)
from PySide6.QtCore import Qt
from typing import Optional, Callable

from app.styles.theme import get_control_card_style, get_primary_button_style, get_danger_button_style
from app.utils.constants import STATUS_CONNECTING, STATUS_DISCONNECTED


class RTSPTab(QWidget):
    """RTSP stream configuration tab.
    
    Provides URL input, authentication, and network interface selection.
    """
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize the RTSP tab.
        
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
        
        # Connection control card
        card = self._create_control_card()
        layout.addWidget(card)
        
        # Preview area placeholder
        self._preview_placeholder = QWidget()
        layout.addWidget(self._preview_placeholder, 1)
    
    def _create_control_card(self) -> QWidget:
        """Create the control card with connection controls.
        
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
        
        # URL row
        url_row = QHBoxLayout()
        url_row.setSpacing(8)
        
        url_label = QLabel("RTSP URL:")
        url_label.setFixedWidth(80)
        url_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        url_row.addWidget(url_label)
        
        url_edit = QLineEdit("rtsp://192.168.2.254/PSIA/Streaming/channels/h264")
        url_edit.setFixedWidth(350)
        url_row.addWidget(url_edit)
        
        connect_btn = QPushButton("连接")
        connect_btn.setStyleSheet(get_primary_button_style())
        connect_btn.clicked.connect(lambda: self._notify_status(STATUS_CONNECTING))
        url_row.addWidget(connect_btn)
        
        disconnect_btn = QPushButton("断开")
        disconnect_btn.setStyleSheet(get_danger_button_style())
        disconnect_btn.clicked.connect(lambda: self._notify_status(STATUS_DISCONNECTED))
        url_row.addWidget(disconnect_btn)
        
        url_row.addStretch()
        card_layout.addLayout(url_row)
        
        # Auth row
        auth_row = QHBoxLayout()
        auth_row.setSpacing(8)
        
        user_label = QLabel("用户名:")
        user_label.setFixedWidth(80)
        user_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        auth_row.addWidget(user_label)
        
        user_edit = QLineEdit()
        user_edit.setPlaceholderText("admin")
        user_edit.setFixedWidth(120)
        auth_row.addWidget(user_edit)
        
        pass_label = QLabel("密码:")
        pass_label.setFixedWidth(50)
        auth_row.addWidget(pass_label)
        
        pass_edit = QLineEdit()
        pass_edit.setEchoMode(QLineEdit.Password)
        pass_edit.setFixedWidth(120)
        auth_row.addWidget(pass_edit)
        
        auth_row.addStretch()
        card_layout.addLayout(auth_row)
        
        # Network row
        net_row = QHBoxLayout()
        net_row.setSpacing(8)
        
        net_label = QLabel("网卡:")
        net_label.setFixedWidth(80)
        net_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        net_row.addWidget(net_label)
        
        net_combo = QComboBox()
        net_combo.addItems(["Realtek PCIe GbE - 192.168.1.100", "Intel Wi-Fi 6 - 192.168.1.101"])
        net_combo.setFixedWidth(220)
        net_row.addWidget(net_combo)
        
        proto_combo = QComboBox()
        proto_combo.addItems(["UDP", "TCP"])
        net_row.addWidget(proto_combo)
        
        net_row.addStretch()
        card_layout.addLayout(net_row)
        
        card.setFixedHeight(120)
        
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
