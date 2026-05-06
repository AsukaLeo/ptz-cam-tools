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

_logger = get_logger(__name__)


# Import OpenCV
try:
    import cv2
    _HAS_CV2 = True
except ImportError:
    cv2 = None
    _HAS_CV2 = False


# Windows API to get device friendly name using DirectShow
def get_device_friendly_name(index: int) -> str:
    """Get DirectShow device friendly name using Windows COM API."""
    try:
        import comtypes.client
        from comtypes import GUID
        CLSID_SystemDeviceEnum = GUID("{62BE5D10-60EB-11d0-BD3B-00A0C911CE86}")
        CLSID_VideoInputDeviceCategory = GUID("{860BB310-5D01-11d0-BD3B-00A0C911CE86}")
        dev_enum = comtypes.client.CreateObject(CLSID_SystemDeviceEnum)
        class_enum = dev_enum.CreateClassEnumerator(CLSID_VideoInputDeviceCategory, 0)
        if class_enum is None:
            return f"Camera {index + 1}"
        device_count = 0
        while True:
            try:
                moniker = class_enum.Next(1)
                if not moniker:
                    break
                if device_count == index:
                    bind_ctx = comtypes.client.CreateObject(comtypes.CLSID_BindCtx)
                    property_bag = moniker[0].BindToStorage(
                        bind_ctx, None,
                        GUID("{55272A00-42CB-11CE-8135-00AA004BB851}")
                    )
                    try:
                        variant = ctypes.c_void_p()
                        property_bag.Read("FriendlyName", ctypes.byref(variant), None)
                        if variant:
                            return ctypes.wstring_at(variant)
                    except Exception:
                        pass
                device_count += 1
            except Exception:
                break
    except ImportError:
        pass
    except Exception as e:
        _logger.warning("Error getting device name: %s", e)
    return f"Camera {index + 1}"


# Standard DirectShow FourCC codes
FOURCC_H264 = 0x34363248  # 'H264'
FOURCC_MJPG = 0x47504A4D  # 'MJPG'
FOURCC_YUY2 = 0x32595559  # 'YUY2'
FOURCC_NV12 = 0x3231564E  # 'NV12'


def fourcc_to_string(fourcc: int) -> str:
    """Convert FourCC code to string."""
    chars = [
        chr((fourcc >> 0) & 0xFF),
        chr((fourcc >> 8) & 0xFF),
        chr((fourcc >> 16) & 0xFF),
        chr((fourcc >> 24) & 0xFF)
    ]
    return ''.join(chars).strip()


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
        if not self.formats:
            return None
        h264_1080 = [f for f in self.formats
                     if f.format_type == 'H264' and f.height >= 1080]
        if h264_1080:
            return max(h264_1080, key=lambda x: x.fps)
        h264 = self.get_h264_formats()
        if h264:
            return max(h264, key=lambda x: (x.width * x.height, x.fps))
        if self.formats:
            return max(self.formats, key=lambda x: (x.width * x.height, x.fps))
        return None


# Common FPS values that are universally supported by DirectShow cameras.
# These are offered to the user; actual negotiation happens at capture time.
STANDARD_FPS = [60, 50, 30, 25, 15, 10, 5]

# Standard compression types offered for every resolution.
# DirectShow cameras commonly support one or more of these.
STANDARD_FORMATS = ['H264', 'MJPG', 'YUY2', 'NV12']

# Common resolutions tested for device availability (no FPS probing).
COMMON_RESOLUTIONS = [
    (2592, 1944), (2560, 1440),
    (1920, 1080), (1600, 1200),
    (1280, 720),  (1024, 768),
    (800, 600),   (640, 480),
    (576, 480),   (320, 240),
]


def enumerate_devices_fast(
    qt_device_names: dict = None,
    qt_formats_by_index: dict = None
) -> List[DShowDevice]:
    """Enumerate DirectShow video capture devices (fast path).
    
    Uses Qt data for resolution detection. Always offers H264, MJPG, YUY2
    formats at standard FPS values. Actual codec capability is tested
    at capture time, not enumeration time.
    
    Args:
        qt_device_names: Dict mapping index to Qt device name.
        qt_formats_by_index: Dict mapping index to list of
            (w, h, fmt_type, fps) tuples from Qt enumeration.
    
    Returns:
        List of available capture devices with formats.
    """
    if not _HAS_CV2 or cv2 is None:
        return []
    
    devices = []
    index = 0
    
    while True:
        cap = None
        try:
            cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
            if not cap.isOpened():
                break
            
            # Get device name
            name = f"Camera {index + 1}"
            if qt_device_names and index in qt_device_names:
                name = qt_device_names[index]
            
            # Determine supported resolutions
            res_list = []
            if qt_formats_by_index and index in qt_formats_by_index:
                seen_res = set()
                for w, h, fmt_type, fps in qt_formats_by_index[index]:
                    if (w, h) not in seen_res:
                        seen_res.add((w, h))
                        res_list.append((w, h))
            
            # Build format entries: per resolution, offer all standard formats
            formats = []
            for w, h in res_list:
                for fmt_name in STANDARD_FORMATS:
                    fourcc = 0
                    if fmt_name == 'H264': fourcc = FOURCC_H264
                    elif fmt_name == 'MJPG': fourcc = FOURCC_MJPG
                    elif fmt_name == 'YUY2': fourcc = FOURCC_YUY2
                    elif fmt_name == 'NV12': fourcc = FOURCC_NV12
                    formats.append(DShowFormat(
                        width=w, height=h, fps=30.0,
                        format_type=fmt_name, media_subtype=fourcc
                    ))
            
            device = DShowDevice(
                index=index, name=name, device_path=f"video={index}",
                formats=formats
            )
            devices.append(device)
            _logger.debug(
                "Device %d (%s): %d resolutions, %d format types",
                index, name, len(res_list), len(formats)
            )
            
        except Exception as e:
            _logger.error("Error detecting device %d: %s", index, e)
            break
        finally:
            if cap:
                cap.release()
        
        index += 1
        if index > 10:
            break
    
    return devices


class DirectShowCapture(QObject):
    """DirectShow video capture using OpenCV backend.
    
    Uses OpenCV's VideoCapture with DirectShow backend for
    broader format support including H264.
    """
    
    frame_ready = Signal(QImage)
    error_occurred = Signal(str)
    state_changed = Signal(str)  # 'stopped', 'playing', 'paused'
    
    def __init__(self, parent: Optional[QObject] = None) -> None:
        """Initialize DirectShow capture."""
        super().__init__(parent)
        self._capture_thread: Optional['CaptureThread'] = None
        self._current_device: Optional[DShowDevice] = None
        self._is_running = False
    
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
            self._capture_thread.wait(3000)
        
        self._is_running = False
        self.state_changed.emit('stopped')
    
    def _on_state_changed(self, state: str) -> None:
        """Handle state changes from capture thread."""
        if state == 'stopped':
            self._is_running = False
        self.state_changed.emit(state)
    
    def is_running(self) -> bool:
        """Check if capture is running."""
        return self._is_running and self._capture_thread and self._capture_thread.isRunning()


class CaptureThread(QThread):
    """Video capture thread."""
    
    frame_ready = Signal(QImage)
    error_occurred = Signal(str)
    state_changed = Signal(str)
    
    def __init__(self, device: DShowDevice, format_info: DShowFormat,
                 parent: Optional[QObject] = None) -> None:
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
        
        logger = get_logger(__name__)
        
        try:
            logger.debug("Opening device %d: %s", self._device.index, self._device.name)
            self._cap = cv2.VideoCapture(self._device.index, cv2.CAP_DSHOW)
            
            if not self._cap.isOpened():
                logger.error("Failed to open device %s", self._device.name)
                self.error_occurred.emit(f"Failed to open device {self._device.name}")
                return
            
            # Set format
            logger.debug("Setting format: %s", self._format)
            self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self._format.width)
            self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self._format.height)
            self._cap.set(cv2.CAP_PROP_FPS, self._format.fps)
            
            # Set codec for H264
            if self._format.format_type == 'H264':
                self._cap.set(cv2.CAP_PROP_FOURCC,
                             cv2.VideoWriter_fourcc('H', '2', '6', '4'))
            
            self.state_changed.emit('playing')
            logger.debug("Capture started, entering loop")
            
            # Capture loop
            frame_count = 0
            fail_count = 0
            
            while not self._stop_flag:
                ret, frame = self._cap.read()
                
                if not ret:
                    fail_count += 1
                    if fail_count == 1:
                        logger.warning("First read failed")
                    elif fail_count % 30 == 0:
                        logger.warning("Read failed %d times", fail_count)
                    continue
                
                fail_count = 0
                frame_count += 1
                
                if frame_count == 1:
                    logger.debug("First frame captured: %s", frame.shape)
                elif frame_count % 30 == 0:
                    logger.debug("Captured %d frames", frame_count)
                
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
        """Convert OpenCV frame to QImage."""
        global cv2
        if frame is None or frame.size == 0 or cv2 is None:
            return None
        
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width = rgb_frame.shape[:2]
        bytes_per_line = 3 * width
        
        image = QImage(rgb_frame.data, width, height,
                      bytes_per_line, QImage.Format_RGB888)
        return image.copy()
