"""DirectShow video capture module — OpenCV-free using Qt QCamera.

Replaces cv2.VideoCapture + DirectShow backend with native QCamera
+ QMediaCaptureSession + QVideoSink. Zero dependency on OpenCV/NumPy.
"""

import ctypes
import time
from typing import List, Optional, Callable
from dataclasses import dataclass

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QImage
from PySide6.QtMultimedia import (
    QCamera, QCameraDevice, QMediaCaptureSession, QVideoSink,
    QVideoFrame,
)

from app.utils.logger import get_logger

_logger = get_logger(__name__)


# Standard DirectShow FourCC codes (for format detection)
FOURCC_H264 = 0x34363248  # 'H264'
FOURCC_MJPG = 0x47504A4D  # 'MJPG'
FOURCC_YUY2 = 0x32595559  # 'YUY2'
FOURCC_NV12 = 0x3231564E  # 'NV12'


@dataclass
class DShowFormat:
    """DirectShow video format descriptor."""
    width: int = 640
    height: int = 480
    fps: float = 30.0
    format_type: str = "MJPG"
    media_subtype: int = FOURCC_MJPG

    def resolution_str(self) -> str:
        return f"{self.width}x{self.height}"

    def __str__(self) -> str:
        return f"{self.resolution_str()} {self.format_type} {self.fps:.0f}fps"


@dataclass
class DShowDevice:
    """DirectShow device descriptor."""
    name: str
    index: int = 0
    device_path: str = ""
    formats: Optional[List[DShowFormat]] = None

    def get_best_preview_format(self) -> Optional[DShowFormat]:
        """Return the highest resolution format suitable for preview.

        Prefers MJPG > YUY2 > NV12 > H264, then largest resolution.
        """
        if not self.formats:
            return None

        priority = {"MJPG": 0, "YUY2": 1, "H264": 2, "NV12": 3}
        sorted_fmts = sorted(
            self.formats,
            key=lambda f: (
                priority.get(f.format_type, 99),
                -(f.width * f.height),
                -f.fps,
            )
        )
        fmt = sorted_fmts[0]
        _logger.debug(
            f"Best preview format for {self.name}: {fmt.resolution_str()} {fmt.format_type} {fmt.fps:.0f}fps"
        )
        return fmt

    def get_h264_formats(self) -> List[DShowFormat]:
        """Return all H264-capable formats.

        Returns:
            List of DShowFormat with format_type='H264'.
        """
        if not self.formats:
            return []
        return [f for f in self.formats if f.format_type == 'H264']


# ======================================================================
# Device Discovery Helpers
# ======================================================================

def get_dshow_device_name(index: int) -> str:
    """Get device friendly name via DirectShow COM.

    Args:
        index: Camera device index.

    Returns:
        Device friendly name or default string.
    """
    from PySide6.QtMultimedia import QMediaDevices
    devices = QMediaDevices.videoInputs()
    if index < len(devices):
        return devices[index].description()
    return f"USB Camera #{index}"


def enumerate_dshow_devices() -> List[DShowDevice]:
    """Enumerate DirectShow devices using Qt Multimedia.

    Returns:
        List of DShowDevice objects.
    """
    from PySide6.QtMultimedia import QMediaDevices, QCameraDevice
    devices = QMediaDevices.videoInputs()
    result = []

    for i, dev in enumerate(devices):
        formats = []
        for fmt in dev.videoFormats():
            fps = fmt.maxFrameRate() if fmt.maxFrameRate() > 0 else 30.0
            size = fmt.resolution()
            formats.append(DShowFormat(
                width=size.width(),
                height=size.height(),
                fps=fps,
                format_type="MJPG",  # Qt auto-negotiates pixel format
            ))

        result.append(DShowDevice(
            name=dev.description(),
            index=i,
            device_path=dev.id() if hasattr(dev, 'id') else f"video={i}",
            formats=formats if formats else None,
        ))

    return result


def build_dshow_device_from_qt(qt_dev=None, physical_index: int = 0) -> Optional[DShowDevice]:
    """Build a DShowDevice from a QCameraDevice or physical index.

    Args:
        qt_dev: QCameraDevice (optional, used for backward compatibility).
        physical_index: Physical camera index (0-based).

    Returns:
        DShowDevice or None.
    """
    del qt_dev  # unused, kept for backward compatibility
    devices = enumerate_dshow_devices()
    if physical_index < len(devices):
        return devices[physical_index]
    return None


# ======================================================================
# Capture Class (OpenCV-free, uses QCamera natively)
# ======================================================================

class DirectShowCapture(QObject):
    """DirectShow video capture using Qt QCamera (no OpenCV dependency).

    Uses QCamera + QMediaCaptureSession + QVideoSink for native frame delivery.
    Frames are delivered as QImage via frame_ready signal.
    """

    frame_ready = Signal(QImage, float)
    error_occurred = Signal(str)
    state_changed = Signal(str)

    def __init__(self, parent: Optional[QObject] = None) -> None:
        """Initialize capture."""
        super().__init__(parent)
        self._camera: Optional[QCamera] = None
        self._session: Optional[QMediaCaptureSession] = None
        self._sink: Optional[QVideoSink] = None
        self._current_device: Optional[DShowDevice] = None
        self._is_running = False
        self._logger = get_logger(__name__)

    def start_capture(self, device: DShowDevice,
                      format_info: Optional[DShowFormat] = None,
                      callback: Optional[Callable[[QImage], None]] = None) -> bool:
        """Start video capture.

        Args:
            device: Device to capture from.
            format_info: Optional format (for future use with QCameraFormat).
            callback: Optional direct frame callback.

        Returns:
            True if capture started.
        """
        self.stop_capture()

        self._current_device = device

        from PySide6.QtMultimedia import QMediaDevices
        qt_devices = QMediaDevices.videoInputs()
        if device.index >= len(qt_devices):
            self.error_occurred.emit(f"Device index {device.index} out of range")
            return False

        qt_dev = qt_devices[device.index]

        self._camera = QCamera(qt_dev)
        self._session = QMediaCaptureSession()
        self._sink = QVideoSink()

        self._session.setCamera(self._camera)
        self._session.setVideoSink(self._sink)

        self._sink.videoFrameChanged.connect(self._on_frame_changed)
        self._camera.errorOccurred.connect(self._on_error)

        if callback:
            self.frame_ready.connect(callback)

        self._camera.start()
        self._is_running = True
        self.state_changed.emit('playing')
        self._logger.info(f"Capture started: {device.name}")
        return True

    def stop_capture(self) -> None:
        """Stop video capture."""
        if self._camera:
            self._camera.stop()

        if self._sink:
            try:
                self._sink.videoFrameChanged.disconnect(self._on_frame_changed)
            except (TypeError, RuntimeError):
                pass

        if self._camera:
            try:
                self._camera.errorOccurred.disconnect(self._on_error)
            except (TypeError, RuntimeError):
                pass

        self._camera = None
        self._session = None
        self._sink = None
        self._is_running = False
        self.state_changed.emit('stopped')

    def is_running(self) -> bool:
        """Check if capture is active."""
        return self._is_running and self._camera is not None

    def _on_frame_changed(self, frame: QVideoFrame) -> None:
        """Handle new frame from QVideoSink.

        Args:
            frame: New video frame.
        """
        if not self._is_running:
            return
        if not frame.isValid():
            return

        capture_ts = time.perf_counter()
        try:
            image = frame.toImage()
        except Exception:
            return
        if not image.isNull():
            self.frame_ready.emit(image, capture_ts)

    def _on_error(self, error: 'QCamera.Error', error_string: str) -> None:
        """Handle camera errors.

        Args:
            error: Error type.
            error_string: Error description.
        """
        self._logger.error(f"Camera error: {error_string}")
        self.error_occurred.emit(str(error_string))
