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


# Standard FPS values that DirectShow cameras commonly support
STANDARD_FPS = [60, 50, 30, 25, 15, 10, 5]


def build_dshow_device_from_qt(qt_dev: 'CameraDevice',
                                physical_index: int) -> Optional[DShowDevice]:
    """Build a DShowDevice from Qt CameraDevice data.
    
    Uses Qt's format list for base resolution/format/FPS data.
    Augments with H264 and MJPG options at standard FPS values for
    each resolution (since Qt doesn't report H264 capabilities).
    
    Args:
        qt_dev: Qt CameraDevice with video_formats.
        physical_index: Physical device index for OpenCV capture.
        
    Returns:
        DShowDevice with formats, or None if no formats.
    """
    if not qt_dev.video_formats:
        return None
    
    # Collect unique resolutions from Qt
    resolutions = []
    seen_res = set()
    for qfmt in qt_dev.video_formats:
        w, h = qfmt.resolution
        if (w, h) not in seen_res:
            seen_res.add((w, h))
            resolutions.append((w, h))
    
    formats = []
    fourcc_map = {
        'H264': FOURCC_H264,
        'MJPG': FOURCC_MJPG,
        'YUYV': FOURCC_YUY2,
        'YUY2': FOURCC_YUY2,
        'MJPEG': FOURCC_MJPG,
        'NV12': FOURCC_NV12,
    }
    
    for (w, h) in resolutions:
        # Step 1: Add Qt-reported format entries (one per unique pixel format)
        seen_qt = set()
        for qfmt in qt_dev.video_formats:
            if qfmt.resolution != (w, h):
                continue
            norm = qfmt.pixel_format.upper()
            if norm not in seen_qt:
                seen_qt.add(norm)
                fc = fourcc_map.get(norm, 0)
                formats.append(DShowFormat(
                    width=w, height=h, fps=float(qfmt.max_fps),
                    format_type=qfmt.pixel_format, media_subtype=fc
                ))
        
        # Step 2: Augment with H264 + MJPG at standard FPS values
        # Qt rarely reports H264, so we always offer it as an option.
        # Users who select it will get actual negotiation at capture time.
        augmented_fmts = []
        for fmt_name, fourcc in [('MJPG', FOURCC_MJPG), ('H264', FOURCC_H264)]:
            if fmt_name.upper() not in seen_qt:
                for fps in STANDARD_FPS:
                    augmented_fmts.append(DShowFormat(
                        width=w, height=h, fps=float(fps),
                        format_type=fmt_name, media_subtype=fourcc
                    ))
        formats.extend(augmented_fmts)
    
    return DShowDevice(
        index=physical_index,
        name=qt_dev.name,
        device_path=f"video={physical_index}",
        formats=formats
    )


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
        
        Ensures any previous thread is fully cleaned up first.
        """
        # Always stop and clean up previous thread first
        if self._capture_thread and self._capture_thread.isRunning():
            self._capture_thread.stop()
            self._capture_thread.wait(3000)
            self._capture_thread = None
        self._is_running = False
        
        self._current_device = device
        fmt = format_info or device.get_best_preview_format()
        
        if not fmt:
            self.error_occurred.emit("No suitable format found")
            return False
        
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
        
        self._capture_thread = None
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
            
            # Try to force H264 codec if user selected H264
            if self._format.format_type == 'H264':
                logger.debug("Setting H264 FourCC")
                self._cap.set(cv2.CAP_PROP_FOURCC,
                             cv2.VideoWriter_fourcc('H', '2', '6', '4'))
            
            self.state_changed.emit('playing')
            logger.debug("Capture started, entering loop")
            
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
                    if fail_count >= 100:
                        logger.error("Too many read failures, stopping")
                        break
                    continue
                
                fail_count = 0
                frame_count += 1
                
                image = self._cv_frame_to_qimage(frame)
                if image:
                    self.frame_ready.emit(image)
                else:
                    logger.warning("Failed to convert frame to QImage")
            
        except Exception as e:
            logger.error("Capture error: %s", e)
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
