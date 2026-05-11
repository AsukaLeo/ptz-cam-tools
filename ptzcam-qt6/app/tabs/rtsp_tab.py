"""RTSP stream tab page with OpenCV FFmpeg capture."""

import time
from typing import Optional, Callable

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame,
    QLabel, QPushButton, QComboBox, QLineEdit
)
from PySide6.QtCore import Qt, QEvent, QTimer
from PySide6.QtGui import QImage

from app.styles.theme import (
    get_primary_button_style, get_danger_button_style
)
from app.utils.network_utils import get_nic_choices
from app.utils.rtsp_capture import RTSPSource
from app.utils.logger import get_logger
from app.utils.i18n import tr
from app.widgets import ControlCard, HelpCard


class RTSPTab(QWidget):
    """RTSP stream configuration tab with real-time video preview.

    Provides RTSP URL input, authentication, network interface selection,
    transport protocol selection, and live video display via OpenCV FFmpeg
    backend.

    Attributes:
        on_status_update: Callback for status bar updates.
        preview_widget: Video preview widget (set externally by main window).
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize the RTSP tab.

        Args:
            parent: Optional parent widget.
        """
        super().__init__(parent)
        self._logger = get_logger(__name__)

        # Callbacks (set externally)
        self.on_status_update: Optional[Callable[[str], None]] = None
        self.on_visca_address: Optional[Callable[[str], None]] = None
        self.preview_widget: Optional[QWidget] = None
        self._on_video_info: Optional[Callable] = None

        # RTSP source
        self._rtsp_source = RTSPSource(self)
        self._rtsp_source.frame_ready.connect(self._on_frame_ready)
        self._rtsp_source.error_occurred.connect(self._on_error)
        self._rtsp_source.state_changed.connect(self._on_state_changed)

        # FPS calculation
        self._frame_times: list[float] = []
        self._is_playing: bool = False
        self._last_video_info = (0, 0, "", 0.0, 0, "", 0.0)

        # UI references (filled by _setup_ui)
        self._url_combo: Optional[QComboBox] = None
        self._user_edit: Optional[QLineEdit] = None
        self._pass_edit: Optional[QLineEdit] = None
        self._net_combo: Optional[QComboBox] = None
        self._proto_combo: Optional[QComboBox] = None
        self._connect_btn: Optional[QPushButton] = None
        self._disconnect_btn: Optional[QPushButton] = None
        self._preview_placeholder: Optional[QWidget] = None

        self._setup_ui()
        self._enumerate_network_interfaces()

    def _setup_ui(self) -> None:
        """Set up the tab UI layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 8)
        layout.setSpacing(8)

        # Connection control card + Help card
        top_row = QHBoxLayout()
        top_row.setSpacing(8)
        card = self._create_control_card()
        top_row.addWidget(card, 1)
        top_row.addWidget(self._create_help_card())
        layout.addLayout(top_row)

        # Preview area placeholder (replaced by set_preview_widget)
        self._preview_placeholder = QWidget()
        layout.addWidget(self._preview_placeholder, 1)

    def _create_help_card(self) -> QWidget:
        """Create help card with usage instructions."""
        return HelpCard(tr("RTSP 使用说明"), [
            tr("1. 输入 RTSP 流媒体地址"),
            tr("2. 如有认证需填写用户名和密码"),
            tr("3. 选择传输协议（UDP/TCP）"),
            tr("4. 点击「连接」开始拉流"),
            tr("5. 点击「断开」停止播放"),
        ])

    def _create_control_card(self) -> QWidget:
        """Create the control card with connection controls.

        Returns:
            Configured control card widget.
        """
        card = ControlCard()

        # Row 1: URL (combo with history) + Connect/Disconnect
        row = card.add_row()
        row.addWidget(ControlCard.make_label("RTSP URL:"))
        self._url_combo = QComboBox()
        self._url_combo.setEditable(True)
        self._url_combo.setMinimumWidth(280)
        self._url_combo.setInsertPolicy(QComboBox.InsertAtTop)
        self._url_combo.setMaxCount(7)  # 5 history + 2 built-in
        # Built-in defaults
        self._url_combo.addItem("rtsp://192.168.2.254/PSIA/Streaming/channels/h264")
        self._url_combo.addItem("rtsp://192.168.1.253:554/live/av0")
        self._url_combo.setCurrentIndex(0)
        # Adjust width to content AFTER items are populated
        self._url_combo.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self._url_combo.adjustSize()
        self._url_combo.lineEdit().returnPressed.connect(self._connect_rtsp)
        row.addWidget(self._url_combo)

        self._connect_btn = QPushButton("连接")
        self._connect_btn.setStyleSheet(get_primary_button_style())
        self._connect_btn.clicked.connect(self._connect_rtsp)
        row.addWidget(self._connect_btn)

        self._disconnect_btn = QPushButton("断开")
        self._disconnect_btn.setStyleSheet(get_danger_button_style())
        self._disconnect_btn.clicked.connect(self._disconnect_rtsp)
        self._disconnect_btn.setEnabled(False)
        row.addWidget(self._disconnect_btn)
        ControlCard.add_stretch(row)

        # Row 2: Authentication
        row = card.add_row()
        row.addWidget(ControlCard.make_label("用户名:"))
        self._user_edit = QLineEdit()
        self._user_edit.setPlaceholderText("admin")
        self._user_edit.setFixedWidth(120)
        self._setup_line_edit(self._user_edit)
        row.addWidget(self._user_edit)

        row.addWidget(ControlCard.make_label("密码:", 50))
        self._pass_edit = QLineEdit()
        self._pass_edit.setEchoMode(QLineEdit.Password)
        self._pass_edit.setFixedWidth(120)
        self._setup_line_edit(self._pass_edit)
        row.addWidget(self._pass_edit)
        ControlCard.add_stretch(row)

        # Row 3: Network interface + Transport protocol
        row = card.add_row()
        row.addWidget(ControlCard.make_label("网卡:"))
        self._net_combo = ControlCard.make_combo(280)
        row.addWidget(self._net_combo)

        self._proto_combo = QComboBox()
        self._proto_combo.addItems(["UDP", "TCP"])
        self._proto_combo.setMinimumWidth(60)
        self._proto_combo.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self._proto_combo.setToolTip("UDP: 低延迟, 可能丢包\nTCP: 更稳定, 延迟稍高")
        row.addWidget(self._proto_combo)
        ControlCard.add_stretch(row)

        return card

    def set_preview_widget(self, widget: QWidget) -> None:
        """Set the video preview widget (called by main window).

        Replaces the internal placeholder with the actual preview widget.

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

    def _enumerate_network_interfaces(self) -> None:
        """Enumerate physical network interfaces using shared utility.

        Populates the network interface combo box with physical adapter
        names and all associated IPv4 addresses.
        """
        if self._net_combo is None:
            return

        self._net_combo.clear()
        choices = get_nic_choices()
        for choice in choices:
            self._net_combo.addItem(choice)

    # ------------------------------------------------------------------
    # Line edit helpers
    # ------------------------------------------------------------------

    def _setup_line_edit(self, edit: QLineEdit) -> None:
        """Configure a line edit with clear button and select-all on focus.

        Args:
            edit: QLineEdit to configure.
        """
        edit.setClearButtonEnabled(True)
        edit.installEventFilter(self)

    def eventFilter(self, obj, event) -> bool:
        """Handle events for line edits: select all on focus in.

        Args:
            obj: Object the event was sent to.
            event: Event object.

        Returns:
            True if the event was handled, False otherwise.
        """
        if event.type() == QEvent.FocusIn:
            if obj in (self._user_edit, self._pass_edit):
                # Defer selectAll to let the event loop finish first
                QTimer.singleShot(0, obj.selectAll)
        return super().eventFilter(obj, event)

    def _connect_rtsp(self) -> None:
        """Establish RTSP connection.

        Builds the full RTSP URL from UI inputs, then starts the
        RTSPSource capture thread.
        """
        if self._url_combo is None:
            return

        raw_url = self._url_combo.currentText().strip()
        if not raw_url:
            self._notify_status("请输入 RTSP URL")
            return

        # Save URL to combo history (dedup, cap at 5 history + 2 built-in)
        idx = self._url_combo.findText(raw_url)
        if idx >= 0:
            self._url_combo.removeItem(idx)
        self._url_combo.insertItem(0, raw_url)
        self._url_combo.setCurrentIndex(0)
        # Keep max 7 (5 history + 2 built-in)
        while self._url_combo.count() > 7:
            self._url_combo.removeItem(self._url_combo.count() - 1)

        # Build URL with authentication if provided
        user = self._user_edit.text().strip() if self._user_edit else ""
        password = self._pass_edit.text().strip() if self._pass_edit else ""

        if user:
            # Insert credentials into URL: rtsp://user:pass@host:port/path
            # Always embed when username is provided (even with empty password)
            if raw_url.startswith("rtsp://"):
                url = f"rtsp://{user}:{password}@{raw_url[7:]}"
            else:
                url = f"rtsp://{user}:{password}@{raw_url}"
        else:
            url = raw_url

        transport = "tcp"
        if self._proto_combo:
            transport = self._proto_combo.currentText().lower()

        self._logger.info(f"Connecting RTSP: {url} ({transport})")

        # Auto-fill VISCA address with RTSP URL's IP
        if self.on_visca_address:
            try:
                from urllib.parse import urlparse
                parsed = urlparse(url)
                if parsed.hostname:
                    self.on_visca_address(parsed.hostname)
            except Exception:
                pass

        # Hide placeholder
        if hasattr(self.preview_widget, 'hide_placeholder'):
            self.preview_widget.hide_placeholder()

        # Disable controls while playing
        self._set_controls_enabled(False)

        # Start capture
        self._rtsp_source.connect_to(url)

    def _disconnect_rtsp(self) -> None:
        """Disconnect RTSP stream."""
        self._logger.info("Disconnecting RTSP stream")
        self._rtsp_source.disconnect()
        self._update_ui_stopped()

    def _on_frame_ready(self, image: QImage, capture_time: float) -> None:
        """Handle incoming video frame from the RTSP source.

        Calculates real-time FPS and latency, displays the frame
        on the preview widget, and updates the status bar.

        Args:
            image: Video frame as QImage.
            capture_time: perf_counter() at frame capture time.
        """
        # Discard stale frames from queued cross-thread signals
        if not self._is_playing:
            return

        import time
        now = time.perf_counter()

        # Calculate latency
        latency_ms = int((now - capture_time) * 1000)

        # Real-time FPS via sliding window
        self._frame_times.append(now)
        if len(self._frame_times) > 30:
            self._frame_times.pop(0)

        real_fps = 0.0
        if len(self._frame_times) >= 2:
            elapsed = self._frame_times[-1] - self._frame_times[0]
            if elapsed > 0:
                real_fps = (len(self._frame_times) - 1) / elapsed

        # Report video info periodically (every 10 frames)
        if self._on_video_info and len(self._frame_times) % 10 == 0:
            w, h = image.width(), image.height()
            self._last_video_info = (w, h, "H264", real_fps, latency_ms, "H264 (FFmpeg)", 0.0)
            self._on_video_info(
                w, h,
                "H264", real_fps, latency_ms,
                "H264 (FFmpeg)", 0.0
            )

        # Display frame on preview widget
        if not self.preview_widget:
            self._logger.warning("No preview widget for RTSP frame")
            return

        if not hasattr(self.preview_widget, 'set_video_frame'):
            self._logger.warning("Preview widget missing set_video_frame")
            return

        try:
            from PySide6.QtGui import QPixmap
            pixmap = QPixmap.fromImage(image)

            if pixmap.isNull():
                self._logger.warning("Null pixmap from RTSP frame")
                return

            target_size = self.preview_widget.video_frame.size()
            scaled = pixmap.scaled(
                target_size,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )

            self.preview_widget.set_video_frame(scaled)

        except Exception as e:
            self._logger.error(f"Error displaying RTSP frame: {e}")

    def _on_error(self, error: str) -> None:
        """Handle RTSP source errors.

        Args:
            error: Error description string.
        """
        self._logger.error(f"RTSP error: {error}")
        self._notify_status(f"错误: {error}")
        # Only stop if not trying to reconnect (reconnecting is handled
        # internally by RTSPSource)

    def _on_state_changed(self, state: str) -> None:
        """Handle RTSP source state changes.

        Args:
            state: New state ('connecting', 'connected', 'disconnected', 'error').
        """
        self._logger.info(f"RTSP state: {state}")

        if state == 'connecting':
            self._notify_status("正在连接 RTSP...")
        elif state == 'reconnecting':
            self._notify_status("RTSP 断线重连中...")
        elif state == 'connected':
            self._is_playing = True
            self._notify_status("RTSP 已连接")
            if self._connect_btn:
                self._connect_btn.setText(tr("已连接"))
                self._connect_btn.setEnabled(False)
            if self._disconnect_btn:
                self._disconnect_btn.setEnabled(True)
        elif state == 'disconnected':
            self._update_ui_stopped()
            self._notify_status("RTSP 已断开")
        elif state == 'error':
            self._update_ui_stopped()

    def _update_ui_stopped(self) -> None:
        """Restore UI to stopped/disconnected state."""
        self._is_playing = False

        # Show placeholder
        if hasattr(self.preview_widget, 'show_placeholder'):
            self.preview_widget.show_placeholder()

        # Restore controls
        self._set_controls_enabled(True)

        if self._connect_btn:
            self._connect_btn.setText(tr("连接"))
            self._connect_btn.setEnabled(True)
        if self._disconnect_btn:
            self._disconnect_btn.setEnabled(False)

        # Clear video info
        self._frame_times.clear()
        self._last_video_info = (0, 0, "", 0.0, 0, "", 0.0)
        if self._on_video_info:
            self._on_video_info(0, 0, "", 0.0, 0, "", 0.0)

    def _set_controls_enabled(self, enabled: bool) -> None:
        """Enable or disable input controls.

        Args:
            enabled: True to enable, False to disable.
        """
        if self._url_combo:
            self._url_combo.setEnabled(enabled)
        if self._user_edit:
            self._user_edit.setEnabled(enabled)
        if self._pass_edit:
            self._pass_edit.setEnabled(enabled)
        if self._net_combo:
            self._net_combo.setEnabled(enabled)
        if self._proto_combo:
            self._proto_combo.setEnabled(enabled)

    def _notify_status(self, message: str) -> None:
        """Send status update to the main window status bar.

        Args:
            message: Status message text.
        """
        if self.on_status_update:
            self.on_status_update(message)

    def refresh_language(self) -> None:
        """Update all UI text for current language."""
        from app.utils.i18n import refresh_widget
        refresh_widget(self)

    def set_status_callback(self, callback: Callable[[str], None]) -> None:
        """Set the status update callback (called by main window).

        Args:
            callback: Function to call when status needs updating.
        """
        self.on_status_update = callback

    def set_video_info_callback(self, callback: Callable) -> None:
        """Set callback for video frame info updates.

        The callback receives (width, height, format_name, fps, latency_ms,
        decode_method, cpu_percent).

        Args:
            callback: Video info callback function.
        """
        self._on_video_info = callback

    def get_last_video_info(self) -> tuple:
        """Get the most recently reported video information.

        Returns:
            Tuple of (width, height, format, fps, latency, decode, cpu).
        """
        return self._last_video_info
