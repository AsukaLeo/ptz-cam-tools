"""USB Camera device management module.

Provides device enumeration, monitoring, and information retrieval
using PySide6.QtMultimedia.
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

from PySide6.QtCore import QObject, Signal, QTimer
from PySide6.QtMultimedia import (
    QMediaDevices, QCameraDevice, QCameraFormat,
    QCamera
)


class PixelFormat(Enum):
    """Camera pixel format mapping."""
    UNKNOWN = "Unknown"
    YUYV = "YUYV"
    MJPEG = "MJPEG"
    H264 = "H264"
    NV12 = "NV12"
    I420 = "I420"
    RGB24 = "RGB24"
    BGR24 = "BGR24"
    UYVY = "UYVY"


@dataclass
class CameraFormat:
    """Camera format information."""
    resolution: tuple  # (width, height)
    pixel_format: str
    min_fps: float
    max_fps: float
    
    def __str__(self) -> str:
        return f"{self.resolution[0]}x{self.resolution[1]} @ {int(self.max_fps)}fps ({self.pixel_format})"


@dataclass
class CameraDevice:
    """Camera device information."""
    id: str
    name: str
    description: str
    is_default: bool
    position: str  # "Front", "Back", "Unspecified"
    photo_resolutions: List[tuple] = field(default_factory=list)
    video_formats: List[CameraFormat] = field(default_factory=list)
    
    def get_best_preview_format(self) -> Optional[CameraFormat]:
        """Get best format for preview (1080p or highest available)."""
        if not self.video_formats:
            return None
        
        # Prefer 1920x1080 or closest
        target_res = (1920, 1080)
        best_format = None
        best_score = float('inf')
        
        for fmt in self.video_formats:
            # Score based on resolution difference and frame rate
            res_diff = abs(fmt.resolution[0] - target_res[0]) + abs(fmt.resolution[1] - target_res[1])
            score = res_diff - fmt.max_fps * 10  # Prefer higher FPS
            
            if score < best_score:
                best_score = score
                best_format = fmt
        
        return best_format


class DeviceManager(QObject):
    """USB Camera device manager.
    
    Manages camera device enumeration, monitoring, and information retrieval.
    
    Signals:
        device_added: Emitted when a new device is connected
        device_removed: Emitted when a device is disconnected
        device_list_changed: Emitted when device list changes
    """
    
    device_added = Signal(CameraDevice)
    device_removed = Signal(str)  # device_id
    device_list_changed = Signal()
    error_occurred = Signal(str)
    
    def __init__(self, parent: Optional[QObject] = None) -> None:
        """Initialize the device manager.
        
        Args:
            parent: Optional parent QObject.
        """
        super().__init__(parent)
        self._devices: Dict[str, CameraDevice] = {}
        self._media_devices = QMediaDevices()
        self._timer: Optional[QTimer] = None
        self._last_device_ids: set = set()
        
        # Connect to Qt's device monitoring
        self._media_devices.videoInputsChanged.connect(self._on_devices_changed)
    
    def start_monitoring(self, interval_ms: int = 1000) -> None:
        """Start periodic device monitoring.
        
        Args:
            interval_ms: Polling interval in milliseconds.
        """
        if self._timer is None:
            self._timer = QTimer(self)
            self._timer.timeout.connect(self._check_device_changes)
        
        self._timer.start(interval_ms)
    
    def stop_monitoring(self) -> None:
        """Stop device monitoring."""
        if self._timer:
            self._timer.stop()
    
    def enumerate_devices(self) -> List[CameraDevice]:
        """Enumerate all available video capture devices.
        
        Returns:
            List of CameraDevice objects.
        """
        devices = []
        self._devices.clear()
        
        try:
            qdevices = self._media_devices.videoInputs()
            print(f"[DEBUG] enumerate_devices: found {len(qdevices)} raw device(s)")
            
            for i, qdevice in enumerate(qdevices):
                print(f"[DEBUG] Processing device {i+1}: {qdevice.description()}")
                try:
                    device = self._convert_device(qdevice)
                    if device:
                        devices.append(device)
                        self._devices[device.id] = device
                        print(f"[DEBUG] Device {i+1} converted successfully")
                    else:
                        print(f"[DEBUG] Device {i+1} conversion returned None")
                except Exception as e:
                    print(f"[DEBUG] Device {i+1} conversion error: {e}")
                    import traceback
                    traceback.print_exc()
        
        except Exception as e:
            print(f"[DEBUG] enumerate_devices error: {e}")
            import traceback
            traceback.print_exc()
            self.error_occurred.emit(f"Failed to enumerate devices: {e}")
        
        print(f"[DEBUG] enumerate_devices returning {len(devices)} device(s)")
        return devices
    
    def get_device(self, device_id: str) -> Optional[CameraDevice]:
        """Get device information by ID.
        
        Args:
            device_id: Device unique identifier.
            
        Returns:
            CameraDevice if found, None otherwise.
        """
        return self._devices.get(device_id)
    
    def get_default_device(self) -> Optional[CameraDevice]:
        """Get the system default camera device.
        
        Returns:
            Default CameraDevice if available.
        """
        for device in self._devices.values():
            if device.is_default:
                return device
        
        # Return first device if no default marked
        return next(iter(self._devices.values()), None)
    
    def create_camera(self, device_id: str) -> Optional[QCamera]:
        """Create a QCamera instance for the specified device.
        
        Args:
            device_id: Device unique identifier.
            
        Returns:
            Configured QCamera instance.
        """
        device = self.get_device(device_id)
        if not device:
            return None
        
        # Find the QCameraDevice
        qdevices = self._media_devices.videoInputs()
        for qdevice in qdevices:
            if qdevice.id() == device_id:
                return QCamera(qdevice)
        
        return None
    
    def _convert_device(self, qdevice: QCameraDevice) -> Optional[CameraDevice]:
        """Convert QCameraDevice to CameraDevice.
        
        Args:
            qdevice: Qt camera device object.
            
        Returns:
            Converted CameraDevice.
        """
        try:
            # Fix: device ID is QByteArray, convert to string
            device_id_raw = qdevice.id()
            print(f"[DEBUG] Device ID type: {type(device_id_raw)}, value: {repr(device_id_raw)[:80]}")
            
            try:
                # Method 1: QByteArray to bytes then decode
                device_bytes = bytes(device_id_raw)
                device_id = device_bytes.decode('utf-8', errors='ignore')
                print(f"[DEBUG] ID converted via bytes(): {device_id[:50]}...")
            except Exception as e1:
                print(f"[DEBUG] bytes() method failed: {e1}")
                try:
                    # Method 2: Direct str conversion
                    device_id = str(device_id_raw)
                    print(f"[DEBUG] ID converted via str(): {device_id[:50]}...")
                except Exception as e2:
                    print(f"[DEBUG] str() method failed: {e2}")
                    device_id = f"device_{id(qdevice)}"  # Fallback
            
            # Get basic info (always available)
            device_name = qdevice.description()
            is_default = qdevice.isDefault()
            
            # Determine position (handle different Qt versions)
            try:
                position_map = {
                    QCameraDevice.Position.FrontFace: "Front",
                    QCameraDevice.Position.BackFace: "Back",
                }
                position = position_map.get(qdevice.position(), "Unspecified")
            except Exception as e:
                print(f"[DEBUG] Position mapping error: {e}")
                position = "Unspecified"
            
            # Get photo resolutions (may be empty)
            photo_resolutions = []
            try:
                photo_resolutions = [
                    (res.width(), res.height())
                    for res in qdevice.photoResolutions()
                ]
            except Exception:
                pass  # Ignore if not available
            
            # Get video formats (may be empty or fail)
            video_formats = []
            try:
                for fmt in qdevice.videoFormats():
                    try:
                        format_info = CameraFormat(
                            resolution=(fmt.resolution().width(), fmt.resolution().height()),
                            pixel_format=self._convert_pixel_format(fmt.pixelFormat()),
                            min_fps=fmt.minFrameRate(),
                            max_fps=fmt.maxFrameRate()
                        )
                        video_formats.append(format_info)
                    except Exception:
                        continue  # Skip problematic formats
            except Exception:
                pass  # Ignore if not available
            
            return CameraDevice(
                id=device_id,
                name=device_name,
                description=device_name,
                is_default=is_default,
                position=position,
                photo_resolutions=photo_resolutions,
                video_formats=video_formats
            )
        
        except Exception as e:
            self.error_occurred.emit(f"Failed to convert device: {e}")
            return None
    
    def _convert_pixel_format(self, fmt) -> str:
        """Convert Qt pixel format to string.
        
        Args:
            fmt: Qt pixel format enum.
            
        Returns:
            Format name string.
        """
        try:
            # Map by enum value (more reliable across Qt versions)
            format_map = {
                17: "YUYV",      # Format_YUYV
                18: "NV12",      # Format_NV12
                19: "NV21",      # Format_NV21
                20: "I420",      # Format_IMC2/IMC4/I420
                21: "I420",      # Format_YUV420P
                22: "UYVY",      # Format_UYVY
                23: "YVYU",      # Format_YVYU
                24: "RGB24",     # Format_RGB24
                25: "BGR24",     # Format_BGR24
                26: "RGB32",     # Format_RGBX8888
                27: "BGR32",     # Format_BGRX8888
                28: "RGBA",      # Format_RGBA8888
                29: "MJPEG",     # Format_Jpeg
                30: "H264",      # Format_H264 (if available)
            }
            
            # Get the integer value
            fmt_value = fmt.value if hasattr(fmt, 'value') else int(fmt)
            
            return format_map.get(fmt_value, f"Fmt({fmt_value})")
        except Exception as e:
            return f"Unknown"
    
    def _on_devices_changed(self) -> None:
        """Handle device list changes from Qt."""
        self._check_device_changes()
    
    def _check_device_changes(self) -> None:
        """Check for device additions/removals."""
        current_devices = self.enumerate_devices()
        current_ids = {d.id for d in current_devices}
        
        # Check for new devices
        for device in current_devices:
            if device.id not in self._last_device_ids:
                self.device_added.emit(device)
        
        # Check for removed devices
        for device_id in self._last_device_ids:
            if device_id not in current_ids:
                self.device_removed.emit(device_id)
        
        # Update tracking
        if current_ids != self._last_device_ids:
            self._last_device_ids = current_ids
            self.device_list_changed.emit()


def get_device_manager() -> DeviceManager:
    """Get the global device manager instance.
    
    Returns:
        DeviceManager singleton instance.
    """
    if not hasattr(get_device_manager, '_instance'):
        get_device_manager._instance = DeviceManager()
    return get_device_manager._instance
