"""USB camera tab page."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QFrame
)
from PySide6.QtCore import Qt
from typing import Optional, Callable

from app.styles.theme import get_control_card_style, get_primary_button_style, get_standard_button_style
from app.utils.device_manager import DeviceManager, CameraDevice
from app.utils.logger import get_logger


class USBTab(QWidget):
    """USB camera configuration tab.
    
    Provides device selection, resolution, format, and frame rate controls.
    
    Attributes:
        on_status_update: Callback for status updates.
        preview_widget: Video preview widget (set externally).
        device_manager: Device manager for camera enumeration.
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
        
        # Initialize device manager
        self._device_manager = DeviceManager(self)
        self._device_manager.device_added.connect(self._on_device_added)
        self._device_manager.device_removed.connect(self._on_device_removed)
        self._device_manager.error_occurred.connect(self._on_device_error)
        
        self._current_device: Optional[CameraDevice] = None
        
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
        self.fmt_combo.setEnabled(False)
        param_row.addWidget(self.fmt_combo)
        
        # Frame rate
        lbl3 = QLabel("帧率:")
        lbl3.setFixedWidth(50)
        lbl3.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        param_row.addWidget(lbl3)
        
        self.fps_combo = QComboBox()
        self.fps_combo.setFixedWidth(90)
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
        """Enumerate USB camera devices and update UI."""
        self._logger.debug("Enumerating USB devices...")
        self._notify_status("正在检测设备...")
        
        # Clear current list
        self.device_combo.clear()
        self.res_combo.clear()
        self.fmt_combo.clear()
        self.fps_combo.clear()
        self.play_btn.setEnabled(False)
        
        # Enumerate devices
        devices = self._device_manager.enumerate_devices()
        
        if not devices:
            self.device_combo.addItem("未检测到设备", "")
            self._notify_status("未检测到 USB 摄像头")
            self._logger.warning("No USB camera devices detected")
            return
        
        # Populate device combo
        for device in devices:
            display_text = f"{device.name}"
            if device.is_default:
                display_text += " (默认)"
            self.device_combo.addItem(display_text, device.id)
            self._logger.debug(f"Found device: {device.name} ({device.id})")
        
        # Connect device selection
        self.device_combo.currentIndexChanged.connect(self._on_device_selected)
        
        # Select first device
        self.device_combo.setCurrentIndex(0)
        self._on_device_selected(0)
        
        self._notify_status(f"检测到 {len(devices)} 个设备")
        self._logger.info(f"Detected {len(devices)} USB camera(s)")
    
    def _on_device_selected(self, index: int) -> None:
        """Handle device selection change.
        
        Args:
            index: Selected device index.
        """
        device_id = self.device_combo.currentData()
        if not device_id:
            self.play_btn.setEnabled(False)
            return
        
        device = self._device_manager.get_device(device_id)
        if not device:
            return
        
        self._current_device = device
        self._logger.debug(f"Selected device: {device.name}")
        
        # Update format combos
        self._update_format_combos(device)
        
        # Enable play button
        self.play_btn.setEnabled(True)
    
    def _update_format_combos(self, device: CameraDevice) -> None:
        """Update resolution/format/fps combos for selected device.
        
        Args:
            device: Selected camera device.
        """
        self.res_combo.clear()
        self.fmt_combo.clear()
        self.fps_combo.clear()
        
        # Get unique resolutions
        resolutions = set()
        formats = set()
        frame_rates = set()
        
        for fmt in device.video_formats:
            res_str = f"{fmt.resolution[0]} x {fmt.resolution[1]}"
            resolutions.add((fmt.resolution[0], fmt.resolution[1], res_str))
            formats.add(fmt.pixel_format)
            frame_rates.add(f"{int(fmt.max_fps)} fps")
        
        # Sort resolutions by area (descending)
        sorted_res = sorted(resolutions, key=lambda x: x[0]*x[1], reverse=True)
        for _, _, res_str in sorted_res:
            self.res_combo.addItem(res_str)
        
        # Add formats
        for fmt in sorted(formats):
            self.fmt_combo.addItem(fmt)
        
        # Add frame rates
        for fps in sorted(frame_rates, key=lambda x: int(x.split()[0]), reverse=True):
            self.fps_combo.addItem(fps)
        
        # Enable combos
        self.res_combo.setEnabled(bool(resolutions))
        self.fmt_combo.setEnabled(bool(formats))
        self.fps_combo.setEnabled(bool(frame_rates))
        
        self._logger.debug(f"Device supports {len(resolutions)} resolutions, {len(formats)} formats")
    
    def _on_resolution_changed(self, index: int) -> None:
        """Handle resolution selection change.
        
        Args:
            index: Selected resolution index.
        """
        if not self._current_device:
            return
        
        res_text = self.res_combo.currentText()
        self._logger.debug(f"Resolution changed to: {res_text}")
    
    def _toggle_playback(self) -> None:
        """Toggle video playback."""
        if self.play_btn.text() == "播放":
            self._start_playback()
        else:
            self._stop_playback()
    
    def _start_playback(self) -> None:
        """Start video playback."""
        device_id = self.device_combo.currentData()
        if not device_id:
            return
        
        self._logger.info(f"Starting playback for device: {device_id}")
        self._notify_status("正在启动视频...")
        
        # TODO: Start video capture (Phase 2)
        # For now, just update UI
        self.play_btn.setText("停止")
        self.device_combo.setEnabled(False)
        self.refresh_btn.setEnabled(False)
        self._notify_status("视频播放中")
    
    def _stop_playback(self) -> None:
        """Stop video playback."""
        self._logger.info("Stopping playback")
        self._notify_status("视频已停止")
        
        # TODO: Stop video capture (Phase 2)
        # For now, just update UI
        self.play_btn.setText("播放")
        self.device_combo.setEnabled(True)
        self.refresh_btn.setEnabled(True)
    
    def _on_device_added(self, device: CameraDevice) -> None:
        """Handle device added event.
        
        Args:
            device: Newly connected device.
        """
        self._logger.info(f"Device connected: {device.name}")
        self._notify_status(f"设备已连接: {device.name}")
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
    
    def get_current_device(self) -> Optional[CameraDevice]:
        """Get currently selected device.
        
        Returns:
            Current device or None.
        """
        return self._current_device
