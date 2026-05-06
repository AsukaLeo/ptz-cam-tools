"""ONVIF camera tab page with device discovery and video preview."""

import time
from typing import Optional, Callable

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame,
    QLabel, QPushButton, QComboBox, QLineEdit
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QImage

from app.styles.theme import (
    get_control_card_style, get_primary_button_style,
    get_danger_button_style, get_standard_button_style,
)
from app.utils.onvif_device import (
    discover_devices, ONVIFConnection, ONVIFDeviceInfo
)
from app.utils.rtsp_capture import RTSPSource
from app.utils.logger import get_logger


class ONVIFTab(QWidget):
    """ONVIF camera tab with WS-Discovery, connection, and video preview.

    Discovers ONVIF devices on the network, connects to a selected device,
    retrieves the RTSP stream URL via ONVIF media service, and displays
    the video using the shared RTSP capture module.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize the ONVIF tab.

        Args:
            parent: Optional parent widget.
        """
        super().__init__(parent)
        self._logger = get_logger(__name__)

        # Callbacks (set externally)
        self.on_status_update: Optional[Callable[[str], None]] = None
        self.preview_widget: Optional[QWidget] = None
        self._on_video_info: Optional[Callable] = None

        # ONVIF state
        self._discovered_devices: list[ONVIFDeviceInfo] = []
        self._onvif_conn: Optional[ONVIFConnection] = None

        # RTSP capture (reuses existing module)
        self._rtsp_source = RTSPSource(self)
        self._rtsp_source.frame_ready.connect(self._on_frame_ready)
        self._rtsp_source.error_occurred.connect(self._on_rtsp_error)
        self._rtsp_source.state_changed.connect(self._on_rtsp_state)

        # RTSP URL cache (for reconnection)
        self._last_rtsp_url: str = ""

        # FPS
        self._frame_times: list[float] = []
        self._is_playing: bool = False

        # UI references
        self._ip_edit: Optional[QLineEdit] = None
        self._port_edit: Optional[QLineEdit] = None
        self._user_edit: Optional[QLineEdit] = None
        self._pass_edit: Optional[QLineEdit] = None
        self._discover_btn: Optional[QPushButton] = None
        self._connect_btn: Optional[QPushButton] = None
        self._disconnect_btn: Optional[QPushButton] = None
        self._device_combo: Optional[QComboBox] = None
        self._preview_placeholder: Optional[QWidget] = None

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the tab UI layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 8)
        layout.setSpacing(8)

        card = self._create_control_card()
        layout.addWidget(card)

        self._preview_placeholder = QWidget()
        layout.addWidget(self._preview_placeholder, 1)

    def _create_control_card(self) -> QWidget:
        """Create the control card with ONVIF controls.

        Returns:
            Configured control card widget.
        """
        card = QFrame()
        card.setObjectName("controlCard")
        card.setStyleSheet(get_control_card_style())
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(12, 10, 12, 10)
        card_layout.setSpacing(6)

        # --- Row 1: Device discovery ---
        dev_row = QHBoxLayout()
        dev_row.setSpacing(8)

        dev_label = QLabel("设备:")
        dev_label.setFixedWidth(80)
        dev_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        dev_row.addWidget(dev_label)

        self._device_combo = QComboBox()
        self._device_combo.setFixedWidth(320)
        self._device_combo.addItem("(点击发现搜索 ONVIF 设备)")
        dev_row.addWidget(self._device_combo)

        self._discover_btn = QPushButton("发现")
        self._discover_btn.setStyleSheet(get_standard_button_style())
        self._discover_btn.clicked.connect(self._discover_devices)
        dev_row.addWidget(self._discover_btn)

        self._connect_btn = QPushButton("连接")
        self._connect_btn.setStyleSheet(get_primary_button_style())
        self._connect_btn.clicked.connect(self._connect_device)
        self._connect_btn.setEnabled(False)
        dev_row.addWidget(self._connect_btn)

        self._disconnect_btn = QPushButton("断开")
        self._disconnect_btn.setStyleSheet(get_danger_button_style())
        self._disconnect_btn.clicked.connect(self._disconnect_device)
        self._disconnect_btn.setEnabled(False)
        dev_row.addWidget(self._disconnect_btn)

        dev_row.addStretch()
        card_layout.addLayout(dev_row)

        # --- Row 2: Connection details ---
        detail_row = QHBoxLayout()
        detail_row.setSpacing(8)

        ip_label = QLabel("IP 地址:")
        ip_label.setFixedWidth(80)
        ip_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        detail_row.addWidget(ip_label)

        self._ip_edit = QLineEdit("192.168.2.254")
        self._ip_edit.setFixedWidth(120)
        detail_row.addWidget(self._ip_edit)

        port_label = QLabel("端口:")
        port_label.setFixedWidth(40)
        detail_row.addWidget(port_label)

        self._port_edit = QLineEdit("8000")
        self._port_edit.setFixedWidth(60)
        detail_row.addWidget(self._port_edit)

        user_label = QLabel("用户:")
        user_label.setFixedWidth(40)
        detail_row.addWidget(user_label)

        self._user_edit = QLineEdit("admin")
        self._user_edit.setFixedWidth(100)
        detail_row.addWidget(self._user_edit)

        pass_label = QLabel("密码:")
        pass_label.setFixedWidth(40)
        detail_row.addWidget(pass_label)

        self._pass_edit = QLineEdit()
        self._pass_edit.setEchoMode(QLineEdit.Password)
        self._pass_edit.setFixedWidth(100)
        detail_row.addWidget(self._pass_edit)

        detail_row.addStretch()
        card_layout.addLayout(detail_row)

        return card

    def set_preview_widget(self, widget: QWidget) -> None:
        """Set the video preview widget (called by main window).

        Args:
            widget: Preview widget to display.
        """
        layout = self.layout()
        if self._preview_placeholder:
            layout.removeWidget(self._preview_placeholder)
            self._preview_placeholder.deleteLater()
            self._preview_placeholder = None
        layout.addWidget(widget, 1)
        self.preview_widget = widget

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    def _discover_devices(self) -> None:
        """Discover ONVIF devices on the network."""
        self._notify_status("搜索 ONVIF 设备...")
        if self._discover_btn:
            self._discover_btn.setEnabled(False)
        if self._connect_btn:
            self._connect_btn.setEnabled(False)

        QTimer.singleShot(0, self._do_discover)

    def _do_discover(self) -> None:
        """Perform actual WS-Discovery scan."""
        self._logger.info("Starting ONVIF discovery")
        self._discovered_devices = discover_devices(3000)

        # Filter to only ONVIF video devices
        onvif_devices = [
            d for d in self._discovered_devices
            if "onvif" in d.xaddr.lower() and d.ip
        ]

        if self._device_combo:
            self._device_combo.clear()
            if onvif_devices:
                for d in onvif_devices:
                    label = f"{d.display_name()}  ({d.ip}:{d.port})"
                    self._device_combo.addItem(label)
                self._connect_btn.setEnabled(True)
                self._notify_status(f"发现 {len(onvif_devices)} 个 ONVIF 设备")
            else:
                self._device_combo.addItem("(未发现 ONVIF 设备)")
                self._notify_status("未发现 ONVIF 设备")

        if self._discover_btn:
            self._discover_btn.setEnabled(True)

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------

    def _connect_device(self) -> None:
        """Connect to the selected ONVIF device."""
        ip = self._ip_edit.text().strip() if self._ip_edit else ""
        port_str = self._port_edit.text().strip() if self._port_edit else "80"
        username = self._user_edit.text().strip() if self._user_edit else ""
        password = self._pass_edit.text().strip() if self._pass_edit else ""

        try:
            port = int(port_str)
        except ValueError:
            port = 80

        if not ip:
            self._notify_status("请输入 IP 地址")
            return

        self._logger.info(f"Connecting ONVIF: {ip}:{port}")
        self._notify_status("正在连接 ONVIF 设备...")
        self._set_controls_enabled(False)

        # Try to find matching discovered device for pre-populated info
        pre_info = None
        for d in self._discovered_devices:
            if d.ip == ip:
                pre_info = d
                break

        # Connect via ONVIF
        self._onvif_conn = ONVIFConnection()
        success = self._onvif_conn.connect(
            ip, port, username, password, pre_info
        )

        if not success:
            self._notify_status("ONVIF 连接失败")
            self._update_ui_stopped()
            return

        # Get RTSP URL
        rtsp_url = self._onvif_conn.get_rtsp_url()
        if not rtsp_url:
            self._notify_status("ONVIF 已连接，但无法获取 RTSP 流")
            return

        self._last_rtsp_url = rtsp_url
        self._logger.info(f"ONVIF connected, RTSP: {rtsp_url}")

        # Hide preview placeholder
        if hasattr(self.preview_widget, 'hide_placeholder'):
            self.preview_widget.hide_placeholder()

        # Start RTSP capture
        self._rtsp_source.start(rtsp_url, transport="tcp")

    def _disconnect_device(self) -> None:
        """Disconnect from the ONVIF device."""
        self._logger.info("Disconnecting ONVIF")
        self._rtsp_source.stop()

        if self._onvif_conn:
            self._onvif_conn.disconnect()
            self._onvif_conn = None

        self._update_ui_stopped()

    # ------------------------------------------------------------------
    # RTSP frame handling
    # ------------------------------------------------------------------

    def _on_frame_ready(self, image: QImage, capture_time: float) -> None:
        """Handle incoming RTSP video frame (from ONVIF stream).

        Args:
            image: Video frame as QImage.
            capture_time: perf_counter() at frame capture time.
        """
        if not self._is_playing:
            return

        now = time.perf_counter()
        latency_ms = int((now - capture_time) * 1000)

        self._frame_times.append(now)
        if len(self._frame_times) > 30:
            self._frame_times.pop(0)

        real_fps = 0.0
        if len(self._frame_times) >= 2:
            elapsed = self._frame_times[-1] - self._frame_times[0]
            if elapsed > 0:
                real_fps = (len(self._frame_times) - 1) / elapsed

        if self._on_video_info and len(self._frame_times) % 10 == 0:
            self._on_video_info(
                image.width(), image.height(),
                "H264", real_fps, latency_ms,
                "ONVIF (RTSP)", 0.0
            )

        if not self.preview_widget:
            return
        if not hasattr(self.preview_widget, 'set_video_frame'):
            return

        try:
            from PySide6.QtGui import QPixmap
            pixmap = QPixmap.fromImage(image)
            if pixmap.isNull():
                return
            target_size = self.preview_widget.video_frame.size()
            scaled = pixmap.scaled(
                target_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.preview_widget.set_video_frame(scaled)
        except Exception as e:
            self._logger.error(f"Error displaying ONVIF frame: {e}")

    def _on_rtsp_error(self, error: str) -> None:
        """Handle RTSP capture errors.

        Args:
            error: Error description.
        """
        self._logger.error(f"ONVIF RTSP error: {error}")
        self._notify_status(f"RTSP 错误: {error}")

    def _on_rtsp_state(self, state: str) -> None:
        """Handle RTSP capture state changes.

        Args:
            state: New state string.
        """
        self._logger.info(f"ONVIF RTSP state: {state}")

        if state == 'connected':
            self._is_playing = True
            self._notify_status("ONVIF 已连接")
            if self._connect_btn:
                self._connect_btn.setText("已连接")
                self._connect_btn.setEnabled(False)
            if self._disconnect_btn:
                self._disconnect_btn.setEnabled(True)
        elif state == 'disconnected':
            self._update_ui_stopped()
            self._notify_status("ONVIF 已断开")
        elif state == 'error':
            self._update_ui_stopped()

    def _update_ui_stopped(self) -> None:
        """Restore UI to disconnected state."""
        self._is_playing = False

        if hasattr(self.preview_widget, 'show_placeholder'):
            self.preview_widget.show_placeholder()

        self._set_controls_enabled(True)

        if self._connect_btn:
            self._connect_btn.setText("连接")
            self._connect_btn.setEnabled(len(self._discovered_devices) > 0)
        if self._disconnect_btn:
            self._disconnect_btn.setEnabled(False)

        self._frame_times.clear()
        if self._on_video_info:
            self._on_video_info(0, 0, "", 0.0, 0, "", 0.0)

    def _set_controls_enabled(self, enabled: bool) -> None:
        """Enable or disable input controls.

        Args:
            enabled: True to enable, False to disable.
        """
        for w in [self._ip_edit, self._port_edit, self._user_edit,
                  self._pass_edit, self._device_combo, self._discover_btn]:
            if w:
                w.setEnabled(enabled)

    def _notify_status(self, message: str) -> None:
        """Send status update to the main window status bar.

        Args:
            message: Status message text.
        """
        if self.on_status_update:
            self.on_status_update(message)

    def set_status_callback(self, callback: Callable[[str], None]) -> None:
        """Set the status update callback.

        Args:
            callback: Function to call when status needs updating.
        """
        self.on_status_update = callback

    def set_video_info_callback(self, callback: Callable) -> None:
        """Set callback for video frame info updates.

        Args:
            callback: Video info callback function.
        """
        self._on_video_info = callback
