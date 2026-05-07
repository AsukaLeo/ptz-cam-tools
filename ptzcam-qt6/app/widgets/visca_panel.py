"""VISCA control panel widget."""

from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QComboBox, QLineEdit,
    QTabWidget, QWidget, QCheckBox
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
)


class VISCAPanel(QFrame):
    """VISCA protocol control panel widget.

    Provides serial and network connection configuration for VISCA protocol.
    When a ViscaController is set, the connect buttons issue real connections.
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
        self._controller: Optional['ViscaController'] = None

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the panel UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignTop)

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

    def set_controller(self, controller: 'ViscaController') -> None:
        """Set the VISCA controller for issuing real connections.

        Args:
            controller: ViscaController instance.
        """
        self._controller = controller

    def _create_serial_tab(self) -> QWidget:
        """Create the serial port configuration tab.

        Returns:
            QWidget containing serial configuration controls.
        """
        page = QWidget()
        grid = QGridLayout(page)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setSpacing(6)

        # Port combo
        self._serial_port = QComboBox()
        self._serial_port.addItems(SERIAL_PORTS)
        grid.addWidget(QLabel("端口:"), 0, 0)
        grid.addWidget(self._serial_port, 0, 1)

        # Baud rate
        self._serial_baud = QComboBox()
        self._serial_baud.addItems(BAUD_RATES)
        grid.addWidget(QLabel("波特率:"), 0, 2)
        grid.addWidget(self._serial_baud, 0, 3)

        # Data bits
        self._serial_data = QComboBox()
        self._serial_data.addItems(DATA_BITS)
        grid.addWidget(QLabel("数据位:"), 0, 4)
        grid.addWidget(self._serial_data, 0, 5)

        # Parity
        self._serial_parity = QComboBox()
        self._serial_parity.addItems(PARITY_BITS)
        grid.addWidget(QLabel("校验位:"), 1, 0)
        grid.addWidget(self._serial_parity, 1, 1)

        # Stop bits
        self._serial_stop = QComboBox()
        self._serial_stop.addItems(STOP_BITS)
        grid.addWidget(QLabel("停止位:"), 1, 2)
        grid.addWidget(self._serial_stop, 1, 3)

        # Open button
        self._serial_open_btn = QPushButton("开启")
        self._serial_open_btn.setStyleSheet(get_visca_connect_button_style())
        self._serial_open_btn.clicked.connect(self._connect_serial)
        grid.addWidget(self._serial_open_btn, 1, 4, 1, 2, Qt.AlignCenter)

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
        self._net_proto = QComboBox()
        self._net_proto.addItems(NETWORK_PROTOCOLS)
        self._net_proto.currentIndexChanged.connect(self._on_protocol_changed)
        grid.addWidget(QLabel("协议:"), 0, 0)
        grid.addWidget(self._net_proto, 0, 1)

        # Address
        self._net_addr = QLineEdit("192.168.50.254")
        self._net_addr.setFixedWidth(120)
        grid.addWidget(QLabel("地址:"), 0, 2)
        grid.addWidget(self._net_addr, 0, 3)

        # Port
        self._net_port = QLineEdit("5678")
        self._net_port.setFixedWidth(60)
        grid.addWidget(QLabel("端口:"), 1, 0)
        grid.addWidget(self._net_port, 1, 1)

        # Connect button
        self._net_connect_btn = QPushButton("连接")
        self._net_connect_btn.setStyleSheet(get_visca_connect_button_style())
        self._net_connect_btn.clicked.connect(self._connect_network)
        grid.addWidget(self._net_connect_btn, 1, 2, 1, 2, Qt.AlignCenter)

        # Tilt reverse checkbox (some cameras use swapped up/down values)
        self._tilt_reverse_cb = QCheckBox("倾斜方向反转")
        self._tilt_reverse_cb.setToolTip("部分 VISCA 协议上下方向相反时勾选此项")
        self._tilt_reverse_cb.stateChanged.connect(self._on_tilt_reverse_changed)
        grid.addWidget(self._tilt_reverse_cb, 2, 0, 1, 2)

        grid.setColumnStretch(4, 1)
        return page

    # ------------------------------------------------------------------
    # Protocol-port linkage
    # ------------------------------------------------------------------

    def _on_protocol_changed(self, index: int) -> None:
        """Auto-update port when protocol changes.

        TCP → port 5678, UDP → port 52381.
        """
        proto = self._net_proto.currentText() if hasattr(self, '_net_proto') else "TCP"
        if hasattr(self, '_net_port'):
            if proto == "UDP":
                self._net_port.setText("52381")
            else:
                self._net_port.setText("5678")

    def set_network_address(self, ip: str) -> None:
        """Set the network address field (called from main window / video tabs).

        Args:
            ip: IP address string.
        """
        if hasattr(self, '_net_addr') and ip:
            self._net_addr.setText(ip)

    def set_network_protocol(self, proto: str) -> None:
        """Set the network protocol combo (TCP/UDP).

        Args:
            proto: 'TCP' or 'UDP'.
        """
        if hasattr(self, '_net_proto'):
            idx = self._net_proto.findText(proto)
            if idx >= 0:
                self._net_proto.setCurrentIndex(idx)

    # ------------------------------------------------------------------
    # Connection handlers
    # ------------------------------------------------------------------

    def _connect_serial(self) -> None:
        """Open serial VISCA connection."""
        if not self._controller:
            self._notify_status("控制器未初始化")
            return

        port = self._serial_port.currentText() if hasattr(self, '_serial_port') else "COM1"
        baud = int(self._serial_baud.currentText()) if hasattr(self, '_serial_baud') else 9600
        data = int(self._serial_data.currentText()) if hasattr(self, '_serial_data') else 8
        parity = self._serial_parity.currentText() if hasattr(self, '_serial_parity') else "None"
        stop = int(float(self._serial_stop.currentText())) if hasattr(self, '_serial_stop') else 1

        parity_map = {"None": 'N', "Odd": 'O', "Even": 'E', "Mark": 'M', "Space": 'S'}
        parity_char = parity_map.get(parity, 'N')

        self._controller.connect_serial(port, baud, data, parity_char, stop)

    def _connect_network(self) -> None:
        """Open network VISCA connection."""
        if not self._controller:
            self._notify_status("控制器未初始化")
            return

        proto = self._net_proto.currentText() if hasattr(self, '_net_proto') else "TCP"
        host = self._net_addr.text().strip() if hasattr(self, '_net_addr') else "192.168.50.254"
        port_str = self._net_port.text().strip() if hasattr(self, '_net_port') else "5678"

        try:
            port = int(port_str)
        except ValueError:
            port = 5678

        if proto == "UDP":
            self._controller.connect_udp(host, port)
        else:
            self._controller.connect_tcp(host, port)

    def _on_tilt_reverse_changed(self, state: int) -> None:
        """Update controller tilt reverse flag when checkbox toggles."""
        if self._controller:
            self._controller.tilt_reverse = (state == Qt.CheckState.Checked.value)
            self._notify_status(
                "倾斜方向已反转" if self._controller.tilt_reverse else "倾斜方向恢复正常"
            )

    def _notify_status(self, message: str) -> None:
        """Notify status update via callback."""
        if self.on_status_update:
            self.on_status_update(message)

    def set_status_callback(self, callback: Callable[[str], None]) -> None:
        """Set the status update callback."""
        self.on_status_update = callback
