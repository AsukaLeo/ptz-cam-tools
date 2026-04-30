"""VISCA control panel widget."""

from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QComboBox, QLineEdit,
    QTabWidget, QWidget
)
from PySide6.QtCore import Qt
from typing import Optional, Callable

from app.styles.theme import (
    get_visca_panel_style,
    get_visca_tab_style,
    get_visca_connect_button_style,
)
from app.utils.constants import (
    SERIAL_PORTS, BAUD_RATES, DATA_BITS, PARITY_BITS, STOP_BITS,
    NETWORK_PROTOCOLS,
    VISCA_SERIAL_OPENED, VISCA_NETWORK_CONNECTED,
)


class VISCAPanel(QFrame):
    """VISCA protocol control panel widget.
    
    Provides serial and network connection configuration for VISCA protocol.
    
    Attributes:
        on_status_update: Callback function for status updates.
    """
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize the VISCA panel.
        
        Args:
            parent: Optional parent widget.
        """
        super().__init__(parent)
        self.setObjectName("viscaPanel")
        self.setStyleSheet(get_visca_panel_style())
        
        self.on_status_update: Optional[Callable[[str], None]] = None
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Set up the panel UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        # Title
        title = QLabel("VISCA 控制")
        title.setStyleSheet("""
            QLabel {
                font-size: 12px; font-weight: 500; color: #555;
                background: transparent;
            }
        """)
        layout.addWidget(title)
        
        # Tab widget for Serial/Network
        visca_tab = QTabWidget()
        visca_tab.setStyleSheet(get_visca_tab_style())
        
        # Serial tab
        visca_tab.addTab(self._create_serial_tab(), "串口")
        
        # Network tab
        visca_tab.addTab(self._create_network_tab(), "网络")
        
        layout.addWidget(visca_tab)
    
    def _create_serial_tab(self) -> QWidget:
        """Create the serial port configuration tab.
        
        Returns:
            QWidget containing serial configuration controls.
        """
        page = QWidget()
        grid = QGridLayout(page)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setSpacing(6)
        
        # Row 0: Port, Baud Rate, Data Bits
        grid.addWidget(QLabel("端口:"), 0, 0)
        grid.addWidget(self._make_combo(SERIAL_PORTS), 0, 1)
        grid.addWidget(QLabel("波特率:"), 0, 2)
        grid.addWidget(self._make_combo(BAUD_RATES), 0, 3)
        grid.addWidget(QLabel("数据位:"), 0, 4)
        grid.addWidget(self._make_combo(DATA_BITS), 0, 5)
        
        # Row 1: Parity, Stop Bits, Open button
        grid.addWidget(QLabel("校验位:"), 1, 0)
        grid.addWidget(self._make_combo(PARITY_BITS), 1, 1)
        grid.addWidget(QLabel("停止位:"), 1, 2)
        grid.addWidget(self._make_combo(STOP_BITS), 1, 3)
        
        open_btn = QPushButton("开启")
        open_btn.setStyleSheet(get_visca_connect_button_style())
        open_btn.clicked.connect(lambda: self._notify_status(VISCA_SERIAL_OPENED))
        grid.addWidget(open_btn, 1, 4, 1, 2, Qt.AlignCenter)
        
        grid.setColumnStretch(6, 1)
        
        return page
    
    def _create_network_tab(self) -> QWidget:
        """Create the network configuration tab.
        
        Returns:
            QWidget containing network configuration controls.
        """
        page = QWidget()
        grid = QGridLayout(page)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setSpacing(6)
        
        # Protocol
        grid.addWidget(QLabel("协议:"), 0, 0)
        grid.addWidget(self._make_combo(NETWORK_PROTOCOLS), 0, 1)
        
        # Address
        grid.addWidget(QLabel("地址:"), 0, 2)
        addr_edit = QLineEdit("192.168.50.254")
        addr_edit.setFixedWidth(120)
        grid.addWidget(addr_edit, 0, 3)
        
        # Port
        grid.addWidget(QLabel("端口:"), 1, 0)
        port_edit = QLineEdit("5678")
        port_edit.setFixedWidth(60)
        grid.addWidget(port_edit, 1, 1)
        
        # Connect button
        connect_btn = QPushButton("连接")
        connect_btn.setStyleSheet(get_visca_connect_button_style())
        connect_btn.clicked.connect(lambda: self._notify_status(VISCA_NETWORK_CONNECTED))
        grid.addWidget(connect_btn, 1, 2, 1, 2, Qt.AlignCenter)
        
        grid.setColumnStretch(4, 1)
        
        return page
    
    def _make_combo(self, items: list[str]) -> QComboBox:
        """Create a combo box with the given items.
        
        Args:
            items: List of items to add.
            
        Returns:
            Configured QComboBox.
        """
        combo = QComboBox()
        combo.addItems(items)
        return combo
    
    def _notify_status(self, message: str) -> None:
        """Notify status update via callback.
        
        Args:
            message: Status message to send.
        """
        if self.on_status_update:
            self.on_status_update(message)
    
    def set_status_callback(self, callback: Callable[[str], None]) -> None:
        """Set the status update callback.
        
        Args:
            callback: Function to call when status needs updating.
        """
        self.on_status_update = callback
