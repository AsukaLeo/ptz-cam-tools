"""VISCA control panel widget."""

import time
import threading
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QGridLayout,
    QLabel, QPushButton, QComboBox, QLineEdit,
    QTabWidget, QWidget
)
from PySide6.QtCore import Qt, QTimer
from typing import Optional, Callable
import threading

from app.styles.theme import (
    get_visca_panel_style,
    get_visca_tab_style,
    get_visca_connect_button_style,
)
from app.utils.constants import (
    BAUD_RATES, DATA_BITS, PARITY_BITS, STOP_BITS,
    NETWORK_PROTOCOLS,
)


def _get_disconnect_button_style() -> str:
    """Get style for red disconnect button."""
    return """
        QPushButton {
            background: #d32f2f; color: #fff; border: none; border-radius: 4px;
            padding: 4px 20px; font-size: 12px;
        }
        QPushButton:hover { background: #b71c1c; }
    """


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
        self._on_connection_changed: Optional[Callable[[bool], None]] = None
        self._controller: Optional['ViscaController'] = None

        # Serial connect state
        self._serial_pending = False
        self._serial_timeout_timer: Optional[QTimer] = None

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

        # Default to network tab
        visca_tab.setCurrentIndex(1)

        layout.addWidget(visca_tab)

    def set_controller(self, controller: 'ViscaController') -> None:
        """Set the VISCA controller for issuing real connections.

        Args:
            controller: ViscaController instance.
        """
        self._controller = controller
        # Hook serial data monitor
        self._controller.set_data_callback(self.log_serial_data)
        # Sync default button state to controller
        if hasattr(self, '_tilt_reverse_btn'):
            controller.tilt_reverse = self._tilt_reverse_btn.isChecked()

    def _populate_serial_ports(self) -> None:
        """Populate serial port combo with available ports in ascending order.

        Uses Windows registry (instant, no hang). Falls back to a
        reasonable range if registry read fails.
        """
        self._serial_port.clear()
        ports: list[str] = []

        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"HARDWARE\DEVICEMAP\SERIALCOMM",
            )
            i = 0
            while True:
                try:
                    _, value, _ = winreg.EnumValue(key, i)
                    com = value.upper().strip() if isinstance(value, str) else ""
                    if com.startswith("COM"):
                        ports.append(com)
                    i += 1
                except OSError:
                    break
            winreg.CloseKey(key)
        except Exception:
            pass

        if not ports:
            ports = [f"COM{i}" for i in range(1, 21)]

        ports.sort(key=lambda x: int(x.replace("COM", "")) if x.startswith("COM") else 99)
        for p in ports:
            self._serial_port.addItem(p)

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
        self._populate_serial_ports()
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

        # Connect/Disconnect button
        self._serial_connect_btn = QPushButton("连接")
        self._serial_connect_btn.setStyleSheet(get_visca_connect_button_style())
        self._serial_connect_btn.clicked.connect(self._toggle_serial)
        grid.addWidget(self._serial_connect_btn, 1, 4, 1, 2, Qt.AlignCenter)

        # Serial status label
        self._serial_status = QLabel("")
        self._serial_status.setStyleSheet(
            "color: #888; font-size: 11px; background: transparent; padding: 2px 0;"
        )
        grid.addWidget(self._serial_status, 2, 0, 1, 6)

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

        # Row 0: Protocol + Address + Direction reverse (compact)
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

        # Direction reverse toggle (compact, right of address)
        self._tilt_reverse_btn = QPushButton("方向反转 \u2714")
        self._tilt_reverse_btn.setCheckable(True)
        self._tilt_reverse_btn.setChecked(True)
        self._tilt_reverse_btn.setSizePolicy(
            QPushButton.SizePolicy.Minimum, QPushButton.SizePolicy.Fixed
        )
        self._tilt_reverse_btn.setToolTip("部分 VISCA 协议上下方向相反时取消勾选")
        self._tilt_reverse_btn.setStyleSheet("""
            QPushButton {
                font-size: 10px; background: #fff;
                border: 1px solid #aaa; border-radius: 3px;
                padding: 2px 6px; text-align: left; color: #333;
            }
            QPushButton:checked {
                border-color: #1976d2; color: #1976d2; font-weight: bold;
            }
            QPushButton:!checked {
                color: #888;
            }
            QPushButton:hover {
                background: #f5f5f5;
            }
        """)
        self._tilt_reverse_btn.toggled.connect(self._on_tilt_reverse_changed)
        grid.addWidget(self._tilt_reverse_btn, 0, 4)

        # Row 1: Port + Connect button + Status
        # Port
        self._net_port = QLineEdit("5678")
        self._net_port.setFixedWidth(60)
        grid.addWidget(QLabel("端口:"), 1, 0)
        grid.addWidget(self._net_port, 1, 1)

        # Connect/Disconnect button
        self._net_connect_btn = QPushButton("连接")
        self._net_connect_btn.setStyleSheet(get_visca_connect_button_style())
        self._net_connect_btn.clicked.connect(self._toggle_network)
        grid.addWidget(self._net_connect_btn, 1, 2, 1, 2, Qt.AlignLeft)

        # Connection status (next to connect button)
        self._net_status = QLabel("")
        self._net_status.setStyleSheet(
            "color: #888; font-size: 11px; background: transparent; padding: 2px 0;"
        )
        grid.addWidget(self._net_status, 1, 4)

        # Row 2: Serial data monitor (spans all columns)
        from PySide6.QtWidgets import QTextEdit
        self._serial_monitor = QTextEdit()
        self._serial_monitor.setReadOnly(True)
        self._serial_monitor.setFixedHeight(40)
        self._serial_monitor.setStyleSheet(
            "QTextEdit {"
            "  color: #555; font-size: 10px; font-family: Consolas, monospace;"
            "  background: #fafafa; border: 1px solid #ddd; border-radius: 4px;"
            "  padding: 2px 4px;"
            "}"
        )
        self._serial_monitor.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._serial_monitor.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        grid.addWidget(self._serial_monitor, 2, 0, 1, 5)

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
    # UI state management
    # ------------------------------------------------------------------

    def _set_serial_config_enabled(self, enabled: bool) -> None:
        """Enable or disable serial config widgets.

        Args:
            enabled: True to enable, False to disable.
        """
        for w in [self._serial_port, self._serial_baud,
                  self._serial_data, self._serial_parity, self._serial_stop]:
            w.setEnabled(enabled)

    def _set_serial_connected(self, connected: bool) -> None:
        """Update serial tab UI for connected/disconnected state.

        Args:
            connected: True if connected, False if disconnected.
        """
        btn = self._serial_connect_btn
        if connected:
            btn.setText("断开")
            btn.setStyleSheet(_get_disconnect_button_style())
            self._serial_status.setText("已连接")
            self._serial_status.setStyleSheet(
                "color: #2e7d32; font-size: 11px; background: transparent; padding: 2px 0;"
            )
        else:
            btn.setText("连接")
            btn.setStyleSheet(get_visca_connect_button_style())
            self._serial_status.setText("")
            self._serial_status.setStyleSheet(
                "color: #888; font-size: 11px; background: transparent; padding: 2px 0;"
            )

        self._set_serial_config_enabled(not connected)

        if self._on_connection_changed:
            self._on_connection_changed(connected)

    def _set_network_connected(self, connected: bool) -> None:
        """Update network tab UI for connected/disconnected state.

        Args:
            connected: True if connected, False if disconnected.
        """
        btn = self._net_connect_btn
        if connected:
            btn.setText("断开")
            btn.setStyleSheet(_get_disconnect_button_style())
            self._net_status.setText("已连接")
            self._net_status.setStyleSheet(
                "color: #2e7d32; font-size: 11px; background: transparent; padding: 2px 0;"
            )
        else:
            btn.setText("连接")
            btn.setStyleSheet(get_visca_connect_button_style())
            self._net_status.setText("")
            self._net_status.setStyleSheet(
                "color: #888; font-size: 11px; background: transparent; padding: 2px 0;"
            )

        # Toggle config widgets
        for w in [self._net_proto, self._net_addr, self._net_port]:
            w.setEnabled(not connected)

        if self._on_connection_changed:
            self._on_connection_changed(connected)

    # ------------------------------------------------------------------
    # Connection handlers
    # ------------------------------------------------------------------

    def _toggle_serial(self) -> None:
        """Toggle serial VISCA connection on/off (non-blocking)."""
        if not self._controller:
            self._notify_status("控制器未初始化")
            return

        if self._serial_connect_btn.text() == "断开":
            self._disconnect()
            return

        if self._serial_pending:
            return

        port = self._serial_port.currentText() if hasattr(self, '_serial_port') else "COM1"
        baud = int(self._serial_baud.currentText()) if hasattr(self, '_serial_baud') else 9600
        data = int(self._serial_data.currentText()) if hasattr(self, '_serial_data') else 8
        parity = self._serial_parity.currentText() if hasattr(self, '_serial_parity') else "None"
        stop = int(float(self._serial_stop.currentText())) if hasattr(self, '_serial_stop') else 1

        parity_map = {"None": 'N', "Odd": 'O', "Even": 'E', "Mark": 'M', "Space": 'S'}
        parity_char = parity_map.get(parity, 'N')

        self._enter_connecting_state()
        self._start_async_connect(port, baud, data, parity_char, stop)

    def _enter_connecting_state(self) -> None:
        """Set UI to 'connecting...' state."""
        self._serial_pending = True
        self._serial_connect_btn.setText("连接中...")
        self._serial_connect_btn.setEnabled(False)
        self._set_serial_config_enabled(False)

    def _start_async_connect(
        self, port: str, baud: int, data: int, parity: str, stop: int,
    ) -> None:
        """Run serial connect in background thread with timeout.

        Args:
            port: COM port name.
            baud: Baud rate.
            data: Data bits.
            parity: Parity character.
            stop: Stop bits.
        """
        result: list[bool] = [False]
        done = [False]

        def _do_connect() -> None:
            try:
                result[0] = self._controller.connect_serial(
                    port, baud, data, parity, stop
                )
            except Exception:
                result[0] = False
            done[0] = True

        thread = threading.Thread(target=_do_connect, daemon=True)
        thread.start()

        # Clean up previous timeout timer
        if self._serial_timeout_timer:
            self._serial_timeout_timer.stop()

        def _on_serial_done() -> None:
            if not self._serial_pending:
                return
            self._serial_pending = False
            self._serial_connect_btn.setEnabled(True)
            if result[0]:
                self._set_serial_connected(True)
            else:
                self._show_serial_error("连接失败")
                self._serial_connect_btn.setText("连接")
                self._set_serial_config_enabled(True)

        def _on_serial_timeout() -> None:
            if not self._serial_pending:
                return
            self._serial_pending = False
            done[0] = True
            self._serial_connect_btn.setEnabled(True)
            self._serial_connect_btn.setText("连接")
            self._show_serial_error("连接超时")
            self._set_serial_config_enabled(True)

        # Start timeout timer (stored on self to prevent GC)
        self._serial_timeout_timer = QTimer()
        self._serial_timeout_timer.setSingleShot(True)
        self._serial_timeout_timer.timeout.connect(_on_serial_timeout)
        self._serial_timeout_timer.start(5000)

        # Poll thread completion
        def _poll() -> None:
            if done[0]:
                _on_serial_done()
                return
            if not self._serial_pending:
                return
            QTimer.singleShot(100, _poll)

        QTimer.singleShot(100, _poll)

    def _show_serial_error(self, msg: str) -> None:
        """Show an error message in serial status label.

        Args:
            msg: Error message text.
        """
        self._serial_status.setText(msg)
        self._serial_status.setStyleSheet(
            "color: #c62828; font-size: 11px; background: transparent; padding: 2px 0;"
        )
        self._serial_timeout_timer = None

    def _toggle_network(self) -> None:
        """Toggle network VISCA connection on/off."""
        if not self._controller:
            self._notify_status("控制器未初始化")
            return

        # If currently connected, disconnect
        if self._net_connect_btn.text() == "断开":
            self._disconnect()
            return

        proto = self._net_proto.currentText() if hasattr(self, '_net_proto') else "TCP"
        host = self._net_addr.text().strip() if hasattr(self, '_net_addr') else "192.168.50.254"
        port_str = self._net_port.text().strip() if hasattr(self, '_net_port') else "5678"

        try:
            port = int(port_str)
        except ValueError:
            port = 5678

        if proto == "UDP":
            success = self._controller.connect_udp(host, port)
        else:
            success = self._controller.connect_tcp(host, port)

        if success:
            self._set_network_connected(True)
        else:
            self._net_status.setText("连接失败")
            self._net_status.setStyleSheet(
                "color: #c62828; font-size: 11px; background: transparent; padding: 2px 0;"
            )

    def _disconnect(self) -> None:
        """Disconnect VISCA and reset UI."""
        self._serial_pending = False
        if self._controller:
            self._controller.disconnect()
        self._set_serial_connected(False)
        self._set_network_connected(False)

    def _on_tilt_reverse_changed(self, checked: bool) -> None:
        """Update controller tilt reverse flag when toggle changes.

        Args:
            checked: True if reverse is active.
        """
        self._tilt_reverse_btn.setText("方向反转 \u2714" if checked else "方向反转")
        self._tilt_reverse_btn.setChecked(checked)
        if self._controller:
            self._controller.tilt_reverse = checked
            msg = "方向反转（非标相机使用）" if checked else "方向恢复正常（标准Sony VISCA）"
            self._net_status.setText(msg)
            self._net_status.setStyleSheet(
                "color: #e65100; font-size: 11px; background: transparent; padding: 2px 0;"
            )

    def _notify_status(self, message: str) -> None:
        """Notify status update via callback."""
        if self.on_status_update:
            self.on_status_update(message)

    def set_status_callback(self, callback: Callable[[str], None]) -> None:
        """Set the status update callback."""
        self.on_status_update = callback

    def set_connection_callback(self, callback: Callable[[bool], None]) -> None:
        """Set callback for VISCA connection state changes (True=connected)."""
        self._on_connection_changed = callback

    def log_serial_data(self, direction: str, data: bytes) -> None:
        """Append serial TX/RX data to the monitor.

        Args:
            direction: 'TX' or 'RX'.
            data: Raw bytes sent or received.
        """
        hex_str = ' '.join(f'{b:02X}' for b in data)
        ts = time.strftime('%H:%M:%S')
        line = f"[{ts}] {direction}: {hex_str}"
        self._serial_monitor.append(line)
        # Auto-scroll to bottom
        sb = self._serial_monitor.verticalScrollBar()
        sb.setValue(sb.maximum())
        # Keep only last 200 lines
        if self._serial_monitor.document().blockCount() > 200:
            cursor = self._serial_monitor.textCursor()
            cursor.movePosition(cursor.Start)
            cursor.select(cursor.BlockUnderCursor)
            cursor.removeSelectedText()
            cursor.deleteChar()
