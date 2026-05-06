"""USB camera tab page with DirectShow capture."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage
from typing import Optional, Callable

from app.styles.theme import get_control_card_style, get_primary_button_style, get_standard_button_style
from app.utils.device_manager import DeviceManager, CameraDevice
from app.utils.dshow_capture import (
    DirectShowCapture, DShowDevice, DShowFormat,
    build_dshow_device_from_qt, FOURCC_H264
)
from app.utils.logger import get_logger

import psutil


# Import QLabel for frame display
from PySide6.QtWidgets import QLabel


class USBTab(QWidget):
    """USB camera configuration tab with DirectShow support.
    
    Provides device selection, resolution/format/fps controls,
    and real-time video preview with H264 support.
    
    Attributes:
        on_status_update: Callback for status updates.
        preview_widget: Video preview widget (set externally).
        device_manager: Device manager for camera enumeration.
        capture: DirectShow capture instance.
    """
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize the USB tab.
        
        Args:
            parent: Optional parent widget.
        """
        super().__init__(parent)
        self.on_status_update: Optional[Callable[[str], None]] = None
        self.preview_widget: Optional[QWidget] = None
        self._logger = get_logger(__name__)
        
        # Initialize device manager (for Qt enumeration)
        self._device_manager = DeviceManager(self)
        self._device_manager.device_added.connect(self._on_device_added)
        self._device_manager.device_removed.connect(self._on_device_removed)
        self._device_manager.error_occurred.connect(self._on_device_error)
        
        # Initialize DirectShow capture
        self._dshow_capture = DirectShowCapture(self)
        self._dshow_capture.frame_ready.connect(self._on_frame_ready)
        self._dshow_capture.error_occurred.connect(self._on_capture_error)
        self._dshow_capture.state_changed.connect(self._on_capture_state_changed)
        
        self._current_device: Optional[DShowDevice] = None
        self._dshow_devices: list[DShowDevice] = []
        self._on_video_info: Optional[Callable[[int, int, str, float, int, str, float], None]] = None
        self._frame_times: list[float] = []  # For real-time FPS calculation
        self._cpu_percent: float = 0.0
        self._cpu_process = psutil.Process()  # For per-process CPU monitoring
        self._last_cpu_update: float = 0.0    # Throttle CPU check to 1s
        
        self._setup_ui()
        self._enumerate_devices()
    
    def _setup_ui(self) -> None:
        """Set up the tab UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 8)
        layout.setSpacing(8)
        
        # Control card
        card = self._create_control_card()
        layout.addWidget(card)
        
        # Preview area (added externally)
        self._preview_placeholder = QWidget()
        layout.addWidget(self._preview_placeholder, 1)
    
    def _create_control_card(self) -> QWidget:
        """Create the control card with device and parameter controls.
        
        Returns:
            Configured control card widget.
        """
        card = QFrame()
        card.setObjectName("controlCard")
        card.setStyleSheet(get_control_card_style())
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(12, 10, 12, 10)
        card_layout.setSpacing(6)
        
        # Device row
        device_row = QHBoxLayout()
        device_row.setSpacing(8)
        
        device_label = QLabel("设备:")
        device_label.setFixedWidth(80)
        device_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        device_row.addWidget(device_label)
        
        self.device_combo = QComboBox()
        self.device_combo.setFixedWidth(220)
        self.device_combo.setPlaceholderText("正在检测设备...")
        device_row.addWidget(self.device_combo)
        
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.setStyleSheet(get_standard_button_style())
        self.refresh_btn.setToolTip("重新检测 USB 摄像头设备")
        self.refresh_btn.clicked.connect(self._enumerate_devices)
        device_row.addWidget(self.refresh_btn)
        
        self.play_btn = QPushButton("播放")
        self.play_btn.setStyleSheet(get_primary_button_style())
        self.play_btn.setToolTip("开始/停止视频预览")
        self.play_btn.clicked.connect(self._toggle_playback)
        self.play_btn.setEnabled(False)
        device_row.addWidget(self.play_btn)
        
        device_row.addStretch()
        card_layout.addLayout(device_row)
        
        # Parameters row
        param_row = QHBoxLayout()
        param_row.setSpacing(8)
        
        # Resolution
        lbl1 = QLabel("分辨率:")
        lbl1.setFixedWidth(80)
        lbl1.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        param_row.addWidget(lbl1)
        
        self.res_combo = QComboBox()
        self.res_combo.setFixedWidth(140)
        self.res_combo.setMaxVisibleItems(12)
        self.res_combo.setEnabled(False)
        self.res_combo.currentIndexChanged.connect(self._on_resolution_changed)
        param_row.addWidget(self.res_combo)
        
        # Format
        lbl2 = QLabel("格式:")
        lbl2.setFixedWidth(50)
        lbl2.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        param_row.addWidget(lbl2)
        
        self.fmt_combo = QComboBox()
        self.fmt_combo.setFixedWidth(100)
        self.fmt_combo.setMaxVisibleItems(8)
        self.fmt_combo.setEnabled(False)
        param_row.addWidget(self.fmt_combo)
        
        # Frame rate
        lbl3 = QLabel("帧率:")
        lbl3.setFixedWidth(50)
        lbl3.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        param_row.addWidget(lbl3)
        
        self.fps_combo = QComboBox()
        self.fps_combo.setFixedWidth(90)
        self.fps_combo.setMaxVisibleItems(10)
        self.fps_combo.setEnabled(False)
        param_row.addWidget(self.fps_combo)
        
        param_row.addStretch()
        card_layout.addLayout(param_row)
        
        card.setFixedHeight(120)
        
        return card
    
    def set_preview_widget(self, widget: QWidget) -> None:
        """Set the video preview widget.
        
        Args:
            widget: Preview widget to display.
        """
        layout = self.layout()
        # Replace placeholder
        layout.replaceWidget(self._preview_placeholder, widget)
        self._preview_placeholder.hide()
        self.preview_widget = widget
    
    def _enumerate_devices(self) -> None:
        """Enumerate USB camera devices using QtMultimedia (no OpenCV at enum time)."""
        self._logger.debug("Enumerating USB camera devices...")
        self._notify_status("正在检测设备...")
        
        # Clear current list
        self.device_combo.clear()
        self.res_combo.clear()
        self.fmt_combo.clear()
        self.fps_combo.clear()
        self.play_btn.setEnabled(False)
        
        # Qt enumeration only (no OpenCV to avoid DShow driver state corruption)
        qt_devices = self._device_manager.enumerate_devices()
        self._logger.debug(f"Qt found {len(qt_devices)} physical camera(s)")
        
        # Convert Qt devices to DShowDevices using their format data
        self._dshow_devices = []
        for i, qt_dev in enumerate(qt_devices):
            dshow_dev = build_dshow_device_from_qt(qt_dev, physical_index=i)
            if dshow_dev and dshow_dev.formats:
                self._dshow_devices.append(dshow_dev)
                self._logger.debug(
                    f"  Device {i}: {qt_dev.name} ({len(dshow_dev.formats)} format entries)"
                )
        
        if not self._dshow_devices:
            self.device_combo.addItem("未检测到设备", -1)
            self._notify_status("未检测到 USB 摄像头")
            return
        
        # Populate device combo
        for i, device in enumerate(self._dshow_devices):
            self.device_combo.addItem(device.name, i)
        
        # Connect and select first
        self.device_combo.currentIndexChanged.connect(self._on_device_selected)
        self.device_combo.setCurrentIndex(0)
        self._on_device_selected(0)
        
        self._notify_status(f"检测到 {len(self._dshow_devices)} 个设备")
    
    def _on_device_selected(self, index: int) -> None:
        """Handle device selection change.
        
        Args:
            index: Selected device index.
        """
        if index < 0 or index >= len(self._dshow_devices):
            self.play_btn.setEnabled(False)
            return
        
        device = self._dshow_devices[index]
        self._current_device = device
        self._logger.debug(f"Selected device: {device.name}")
        
        # Update format combos
        self._update_format_combos_dshow(device)
        
        # Enable play button
        self.play_btn.setEnabled(True)
    
    def _update_format_combos_dshow(self, device: DShowDevice) -> None:
        """Update resolution/format/fps combos for DShow device.
        
        Args:
            device: Selected DirectShow device.
        """
        self.res_combo.clear()
        self.fmt_combo.clear()
        self.fps_combo.clear()
        
        if not device.formats:
            return
        
        # Group formats by resolution
        from collections import defaultdict
        self._formats_by_resolution: dict = defaultdict(list)
        
        for fmt in device.formats:
            res_key = (fmt.width, fmt.height)
            self._formats_by_resolution[res_key].append(fmt)
        
        # Sort resolutions by area (descending)
        sorted_res = sorted(
            self._formats_by_resolution.keys(),
            key=lambda x: x[0] * x[1],
            reverse=True
        )
        
        # Populate resolution combo
        for res in sorted_res:
            res_str = f"{res[0]} x {res[1]}"
            self.res_combo.addItem(res_str, res)
        
        # Enable and update
        self.res_combo.setEnabled(bool(sorted_res))
        if sorted_res:
            self._update_format_and_fps_for_resolution_dshow(sorted_res[0])
        
        self._logger.debug(
            f"Device {device.name}: {len(sorted_res)} resolutions, "
            f"H264: {len(device.get_h264_formats())}"
        )
    
    def _update_format_and_fps_for_resolution_dshow(self, resolution: tuple) -> None:
        """Update format and fps combos for selected resolution (DShow).
        
        Args:
            resolution: Selected resolution tuple (width, height).
        """
        self.fmt_combo.clear()
        self.fps_combo.clear()
        
        formats = self._formats_by_resolution.get(resolution, [])
        if not formats:
            return
        
        # Collect unique format types and their available FPS values
        format_fps_map = {}  # format_type -> set of fps values
        for fmt in formats:
            if fmt.format_type not in format_fps_map:
                format_fps_map[fmt.format_type] = set()
            format_fps_map[fmt.format_type].add(int(fmt.fps))
        
        # Add formats (MJPG first, H264 last)
        format_priority = {"MJPG": 0, "MJPEG": 0, "YUYV": 1, "YUY2": 1, "NV12": 2, "H264": 3}
        sorted_formats = sorted(
            format_fps_map.keys(),
            key=lambda x: format_priority.get(x.upper(), 99)
        )
        
        for fmt in sorted_formats:
            self.fmt_combo.addItem(fmt)
        
        # Show FPS values for the first (best) format
        if sorted_formats:
            first_fmt = sorted_formats[0]
            fps_values = sorted(format_fps_map[first_fmt], reverse=True)
            for fps in fps_values:
                self.fps_combo.addItem(f"{fps} fps")
        
        # Enable combos
        self.fmt_combo.setEnabled(bool(sorted_formats))
        self.fps_combo.setEnabled(bool(sorted_formats))
    
    def _on_resolution_changed(self, index: int) -> None:
        """Handle resolution selection change.
        
        Args:
            index: Selected resolution index.
        """
        if not self._current_device or index < 0:
            return
        
        resolution = self.res_combo.currentData()
        if resolution:
            self._update_format_and_fps_for_resolution_dshow(resolution)
            self._logger.debug(f"Resolution changed to: {resolution[0]}x{resolution[1]}")
    
    def _toggle_playback(self) -> None:
        """Toggle video playback."""
        if self.play_btn.text() == "播放":
            self._start_playback()
        else:
            self._stop_playback()
    
    def _start_playback(self) -> None:
        """Start video playback using DirectShow."""
        if not self._current_device:
            return
        
        device = self._current_device
        self._logger.info(f"Starting playback for device: {device.name}")
        self._notify_status("正在启动视频...")
        
        # Get selected format from UI
        res = self.res_combo.currentData()
        fmt_name = self.fmt_combo.currentText()
        fps_text = self.fps_combo.currentText()
        fps_value = float(fps_text.replace(" fps", "")) if fps_text else 30.0
        
        # Find matching DShowFormat by resolution + format type, copy with user FPS
        selected_format = None
        for f in device.formats:
            if (f.width, f.height) == res and f.format_type == fmt_name:
                # Clone with user-selected FPS
                selected_format = DShowFormat(
                    width=res[0], height=res[1],
                    fps=fps_value,
                    format_type=fmt_name,
                    media_subtype=f.media_subtype
                )
                break
        
        # Use best format if not found
        if not selected_format:
            best = device.get_best_preview_format()
            if best:
                selected_format = DShowFormat(
                    width=best.width, height=best.height,
                    fps=fps_value,
                    format_type=best.format_type,
                    media_subtype=best.media_subtype
                )
        
        if not selected_format:
            self._notify_status("错误：无法找到合适的视频格式")
            return
        
        self._logger.debug(f"Using format: {selected_format}")
        
        # Hide placeholder
        if hasattr(self.preview_widget, 'hide_placeholder'):
            self.preview_widget.hide_placeholder()
        
        # Disable all controls before starting (Issue #1 fix)
        self.refresh_btn.setEnabled(False)
        self.device_combo.setEnabled(False)
        self.res_combo.setEnabled(False)
        self.fmt_combo.setEnabled(False)
        self.fps_combo.setEnabled(False)
        
        # Start capture
        success = self._dshow_capture.start_capture(device, selected_format)
        
        if success:
            self.play_btn.setText("停止")
            self._notify_status("视频播放中")
        else:
            # Restore controls on failure
            self._update_ui_stopped()
            self._notify_status("启动视频失败")
    
    def _stop_playback(self) -> None:
        """Stop video playback."""
        # Prevent multiple calls
        if self.play_btn.text() == "播放":
            return
        
        self._logger.info("Stopping playback")
        self._notify_status("视频已停止")
        
        # Only stop if running
        if self._dshow_capture.is_running():
            self._dshow_capture.stop_capture()
        
        self._update_ui_stopped()
    
    def _update_ui_stopped(self) -> None:
        """Update UI to stopped state (without calling stop_capture)."""
        # Show placeholder
        if hasattr(self.preview_widget, 'show_placeholder'):
            self.preview_widget.show_placeholder()
        
        # Update UI
        self.play_btn.setText("播放")
        self.device_combo.setEnabled(True)
        self.refresh_btn.setEnabled(True)
        self.res_combo.setEnabled(True)
        self.fmt_combo.setEnabled(True)
        self.fps_combo.setEnabled(True)
    
    def _on_frame_ready(self, image: QImage, capture_time: float) -> None:
        """Handle new video frame.
        
        Args:
            image: Video frame as QImage.
            capture_time: perf_counter() at capture moment (μs precision).
        """
        self._logger.debug(f"Frame received: {image.width()}x{image.height()}")
        
        import time
        now = time.perf_counter()
        
        # Calculate latency in ms
        latency_ms = int((now - capture_time) * 1000)
        
        # Calculate real-time FPS (sliding window of frame timestamps)
        self._frame_times.append(now)
        if len(self._frame_times) > 30:
            self._frame_times.pop(0)
        
        real_fps = 0.0
        if len(self._frame_times) >= 2:
            elapsed = self._frame_times[-1] - self._frame_times[0]
            if elapsed > 0:
                real_fps = (len(self._frame_times) - 1) / elapsed
        
        # Report video info (every 10th frame), CPU refreshed at most once per second
        if self._on_video_info and len(self._frame_times) % 10 == 0:
            fmt_name = self.fmt_combo.currentText() if self.fmt_combo.count() > 0 else ""
            # Refresh CPU at most once per second
            if time.perf_counter() - self._last_cpu_update >= 1.0:
                self._cpu_percent = self._cpu_process.cpu_percent(interval=0)
                self._last_cpu_update = time.perf_counter()
            decode_method = f"{fmt_name} (OpenCV)"
            self._on_video_info(image.width(), image.height(), fmt_name,
                                real_fps, latency_ms, decode_method, self._cpu_percent)
        
        if not self.preview_widget:
            self._logger.warning("No preview widget available")
            return
        
        if not hasattr(self.preview_widget, 'set_video_frame'):
            self._logger.warning("No preview widget available")
            return
        
        if not hasattr(self.preview_widget, 'set_video_frame'):
            self._logger.warning("Preview widget missing set_video_frame method")
            return
        
        try:
            # Convert to pixmap and display
            from PySide6.QtGui import QPixmap
            pixmap = QPixmap.fromImage(image)
            
            if pixmap.isNull():
                self._logger.warning("Failed to convert image to pixmap")
                return
            
            # Scale to fit the video frame
            target_size = self.preview_widget.video_frame.size()
            self._logger.debug(f"Scaling to: {target_size.width()}x{target_size.height()}")
            
            scaled = pixmap.scaled(
                target_size,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            
            self.preview_widget.set_video_frame(scaled)
            self._logger.debug("Frame displayed successfully")
            
        except Exception as e:
            self._logger.error(f"Error displaying frame: {e}")
    
    def _on_capture_error(self, error: str) -> None:
        """Handle capture error.
        
        Args:
            error: Error message.
        """
        self._logger.error(f"Capture error: {error}")
        self._notify_status(f"视频错误: {error}")
        self._stop_playback()
    
    def _on_capture_state_changed(self, state: str) -> None:
        """Handle capture state change.
        
        Args:
            state: New state ('playing', 'stopped').
        """
        self._logger.debug(f"Capture state: {state}")
        # Only update UI if state changed externally
        if state == 'stopped' and self.play_btn.text() == "停止":
            # Playback stopped externally, update UI only
            self._update_ui_stopped()
    
    def _on_device_added(self, device) -> None:
        """Handle device added event (from Qt device manager).
        
        Args:
            device: Newly connected device.
        """
        self._logger.info(f"Qt device connected: {device.name}")
        self._notify_status(f"设备已连接: {device.name}")
        # Re-enumerate with DirectShow
        self._enumerate_devices()
    
    def _on_device_removed(self, device_id: str) -> None:
        """Handle device removed event.
        
        Args:
            device_id: ID of removed device.
        """
        self._logger.info(f"Device disconnected: {device_id}")
        self._notify_status("设备已断开")
        
        # Stop playback if current device was removed
        if self._current_device and self._current_device.id == device_id:
            self._stop_playback()
        
        self._enumerate_devices()
    
    def _on_device_error(self, error: str) -> None:
        """Handle device error.
        
        Args:
            error: Error message.
        """
        self._logger.error(f"Device error: {error}")
        self._notify_status(f"设备错误: {error}")
    
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
    
    def set_video_info_callback(self, callback: Callable[[int, int, str, float, int, str, float], None]) -> None:
        """Set callback for video frame info updates.
        
        Args:
            callback: Function taking (width, height, format_name, fps, latency_ms, decode_method, cpu_percent).
        """
        self._on_video_info = callback
    
    def get_current_device(self) -> Optional[CameraDevice]:
        """Get currently selected device.
        
        Returns:
            Current device or None.
        """
        return self._current_device
