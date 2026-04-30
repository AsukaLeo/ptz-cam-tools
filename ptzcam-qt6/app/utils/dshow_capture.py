"""DirectShow video capture module.

Provides Windows DirectShow API access for advanced camera features
including H264 format support.
"""

import sys
import ctypes
from ctypes import wintypes
from typing import List, Optional, Tuple, Callable
from dataclasses import dataclass
from enum import IntEnum

from PySide6.QtCore import QObject, Signal, QThread, QMutex, QWaitCondition
from PySide6.QtGui import QImage

from app.utils.logger import get_logger


# Import OpenCV
try:
    import cv2
    _HAS_CV2 = True
except ImportError:
    cv2 = None
    _HAS_CV2 = False
    print("Warning: OpenCV not available")


# Windows API to get device friendly name
def get_device_friendly_name(index: int) -> str:
    """Get DirectShow device friendly name using Windows SetupAPI.
    
    Args:
        index: Device index.
        
    Returns:
        Device friendly name or default name.
    """
    try:
        import winreg
        # Try to read from registry
        try:
            key_path = r"SYSTEM\CurrentControlSet\Control\Class\{6bdd1fc6-810f-11d0-bec7-08002be2092f}"
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
                # Enumerate subkeys to find camera devices
                sub_index = 0
                camera_count = 0
                while True:
                    try:
                        subkey_name = winreg.EnumKey(key, sub_index)
                        with winreg.OpenKey(key, subkey_name) as subkey:
                            try:
                                friendly_name, _ = winreg.QueryValueEx(subkey, "FriendlyName")
                                if camera_count == index:
                                    return friendly_name
                                camera_count += 1
                            except FileNotFoundError:
                                pass
                        sub_index += 1
                    except OSError:
                        break
        except Exception:
            pass
    except ImportError:
        pass
    
    # Fallback: return default name
    return f"Camera {index + 1}"


class DShowFormatType(IntEnum):
    """DirectShow format types."""
    YUY2 = 0x32595559  # 'YUY2'
    MJPG = 0x47504A4D  # 'MJPG'
    H264 = 0x34363248  # 'H264'
    NV12 = 0x3231564E  # 'NV12'
    I420 = 0x30323449  # 'I420'
    RGB24 = 0x00000000  # BI_RGB
    RGB32 = 0x00000000


@dataclass
class DShowFormat:
    """DirectShow video format."""
    width: int
    height: int
    fps: float
    format_type: str  # 'H264', 'MJPG', 'YUY2', etc.
    media_subtype: int  # FourCC code
    
    def __str__(self) -> str:
        return f"{self.width}x{self.height} @ {self.fps}fps ({self.format_type})"


@dataclass
class DShowDevice:
    """DirectShow capture device."""
    index: int
    name: str
    device_path: str
    formats: List[DShowFormat]
    
    def get_h264_formats(self) -> List[DShowFormat]:
        """Get all H264 formats."""
        return [f for f in self.formats if f.format_type == 'H264']
    
    def get_best_preview_format(self) -> Optional[DShowFormat]:
        """Get best format for preview (1080p H264 or best available)."""
        # Prefer H264 1080p
        h264_1080 = [f for f in self.formats 
                     if f.format_type == 'H264' and f.height >= 1080]
        if h264_1080:
            return max(h264_1080, key=lambda x: x.fps)
        
        # Prefer H264 any resolution
        h264 = self.get_h264_formats()
        if h264:
            return max(h264, key=lambda x: (x.width * x.height, x.fps))
        
        # Fall back to any format, prefer higher resolution
        if self.formats:
            return max(self.formats, key=lambda x: (x.width * x.height, x.fps))
        
        return None


class DirectShowCapture(QObject):
    """DirectShow video capture using OpenCV backend.
    
    Uses OpenCV's VideoCapture with DirectShow backend for
    broader format support including H264.
    """
    
    frame_ready = Signal(QImage)
    error_occurred = Signal(str)
    state_changed = Signal(str)  # 'stopped', 'playing', 'paused'
    
    def __init__(self, parent: Optional[QObject] = None) -> None:
        """Initialize DirectShow capture.
        
        Args:
            parent: Optional parent QObject.
        """
        super().__init__(parent)
        self._capture_thread: Optional['CaptureThread'] = None
        self._current_device: Optional[DShowDevice] = None
        self._is_running = False
    
    @staticmethod
    def enumerate_devices(qt_device_names: dict = None) -> List[DShowDevice]:
        """Enumerate DirectShow video capture devices.
        
        Args:
            qt_device_names: Optional dict mapping index to device name from Qt.
        
        Returns:
            List of available capture devices with formats.
        """
        if not _HAS_CV2 or cv2 is None:
            print("OpenCV not available")
            return []
        
        devices = []
        index = 0
        
        while True:
            cap = None
            try:
                cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
                if not cap.isOpened():
                    break
                
                # Get device name - prefer Qt name, fallback to Windows API
                if qt_device_names and index in qt_device_names:
                    name = qt_device_names[index]
                else:
                    name = get_device_friendly_name(index)
                
                # Enumerate supported formats
                formats = DirectShowCapture._enumerate_formats(cap)
                
                device = DShowDevice(
                    index=index,
                    name=name,
                    device_path=f"video={index}",
                    formats=formats
                )
                devices.append(device)
                
            except Exception as e:
                print(f"Error enumerating device {index}: {e}")
                break
            finally:
                if cap:
                    cap.release()
            
            index += 1
            
            # Safety limit
            if index > 10:
                break
        
        return devices
    
    @staticmethod
    def _enumerate_formats(cap) -> List[DShowFormat]:
        """Enumerate formats from OpenCV capture.
        
        Args:
            cap: OpenCV VideoCapture instance.
            
        Returns:
            List of supported formats.
        """
        formats = []
        
        # Common resolutions to test
        test_resolutions = [
            (1920, 1080),
            (1280, 720),
            (640, 480),
            (320, 240),
        ]
        
        # Test each resolution
        for width, height in test_resolutions:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            
            actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            if actual_width == width and actual_height == height:
                # Try to determine format from FourCC
                fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
                format_type = DirectShowCapture._fourcc_to_string(fourcc)
                
                fmt = DShowFormat(
                    width=actual_width,
                    height=actual_height,
                    fps=fps if fps > 0 else 30.0,
                    format_type=format_type,
                    media_subtype=fourcc
                )
                formats.append(fmt)
        
        # Remove duplicates
        seen = set()
        unique_formats = []
        for fmt in formats:
            key = (fmt.width, fmt.height, fmt.format_type)
            if key not in seen:
                seen.add(key)
                unique_formats.append(fmt)
        
        return unique_formats
    
    @staticmethod
    def _fourcc_to_string(fourcc: int) -> str:
        """Convert FourCC code to string.
        
        Args:
            fourcc: FourCC integer code.
            
        Returns:
            Format string.
        """
        try:
            chars = [
                chr((fourcc >> 0) & 0xFF),
                chr((fourcc >> 8) & 0xFF),
                chr((fourcc >> 16) & 0xFF),
                chr((fourcc >> 24) & 0xFF)
            ]
            return ''.join(chars).strip()
        except:
            return f"FourCC({fourcc:08X})"
    
    def start_capture(self, device: DShowDevice, 
                     format_info: Optional[DShowFormat] = None,
                     callback: Optional[Callable[[QImage], None]] = None) -> bool:
        """Start video capture.
        
        Args:
            device: Device to capture from.
            format_info: Optional format to use (uses best if None).
            callback: Optional frame callback.
            
        Returns:
            True if started successfully.
        """
        if self._is_running:
            self.stop_capture()
        
        self._current_device = device
        fmt = format_info or device.get_best_preview_format()
        
        if not fmt:
            self.error_occurred.emit("No suitable format found")
            return False
        
        # Create and start capture thread
        self._capture_thread = CaptureThread(device, fmt, self)
        
        if callback:
            self._capture_thread.frame_ready.connect(callback)
        self._capture_thread.frame_ready.connect(self.frame_ready)
        self._capture_thread.error_occurred.connect(self.error_occurred)
        self._capture_thread.state_changed.connect(self._on_state_changed)
        
        self._capture_thread.start()
        self._is_running = True
        
        return True
    
    def stop_capture(self) -> None:
        """Stop video capture."""
        if self._capture_thread and self._capture_thread.isRunning():
            self._capture_thread.stop()
            self._capture_thread.wait(3000)  # Wait up to 3 seconds
        
        self._is_running = False
        self.state_changed.emit('stopped')
    
    def _on_state_changed(self, state: str) -> None:
        """Handle state changes from capture thread."""
        if state == 'stopped':
            self._is_running = False
        self.state_changed.emit(state)
    
    def is_running(self) -> bool:
        """Check if capture is running.
        
        Returns:
            True if capturing.
        """
        return self._is_running and self._capture_thread and self._capture_thread.isRunning()


class CaptureThread(QThread):
    """Video capture thread."""
    
    frame_ready = Signal(QImage)
    error_occurred = Signal(str)
    state_changed = Signal(str)
    
    def __init__(self, device: DShowDevice, format_info: DShowFormat,
                 parent: Optional[QObject] = None) -> None:
        """Initialize capture thread.
        
        Args:
            device: Device to capture from.
            format_info: Format to use.
            parent: Optional parent.
        """
        super().__init__(parent)
        self._device = device
        self._format = format_info
        self._stop_flag = False
        self._cap = None
    
    def run(self) -> None:
        """Thread main loop."""
        global cv2
        if cv2 is None:
            self.error_occurred.emit("OpenCV not available")
            return
        
        try:
            # Open capture with DirectShow backend
            self._cap = cv2.VideoCapture(self._device.index, cv2.CAP_DSHOW)
            
            if not self._cap.isOpened():
                self.error_occurred.emit(f"Failed to open device {self._device.name}")
                return
            
            # Set format
            self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self._format.width)
            self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self._format.height)
            self._cap.set(cv2.CAP_PROP_FPS, self._format.fps)
            
            # Set codec for H264
            if self._format.format_type == 'H264':
                # Try to force H264 codec
                self._cap.set(cv2.CAP_PROP_FOURCC, 
                             cv2.VideoWriter_fourcc('H', '2', '6', '4'))
            
            self.state_changed.emit('playing')
            
            # Capture loop
            logger = get_logger(__name__)
            frame_count = 0
            
            while not self._stop_flag:
                ret, frame = self._cap.read()
                
                if not ret:
                    continue
                
                frame_count += 1
                if frame_count == 1:
                    logger.debug(f"First frame captured: {frame.shape}")
                elif frame_count % 30 == 0:
                    logger.debug(f"Captured {frame_count} frames")
                
                # Convert OpenCV frame to QImage
                image = self._cv_frame_to_qimage(frame)
                if image:
                    self.frame_ready.emit(image)
                else:
                    logger.warning("Failed to convert frame to QImage")
            
        except Exception as e:
            self.error_occurred.emit(f"Capture error: {e}")
        
        finally:
            if self._cap:
                self._cap.release()
            self.state_changed.emit('stopped')
    
    def stop(self) -> None:
        """Request thread stop."""
        self._stop_flag = True
    
    @staticmethod
    def _cv_frame_to_qimage(frame) -> Optional[QImage]:
        """Convert OpenCV frame to QImage.
        
        Args:
            frame: OpenCV BGR frame.
            
        Returns:
            QImage or None.
        """
        global cv2
        if frame is None or frame.size == 0 or cv2 is None:
            return None
        
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        height, width = rgb_frame.shape[:2]
        bytes_per_line = 3 * width
        
        image = QImage(rgb_frame.data, width, height, 
                      bytes_per_line, QImage.Format_RGB888)
        
        # Create a copy to ensure data persistence
        return image.copy()
