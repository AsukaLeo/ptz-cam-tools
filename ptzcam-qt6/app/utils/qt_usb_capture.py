"""USB camera capture using PySide6 QCamera (no OpenCV dependency).

Replaces cv2.VideoCapture + DirectShow backend with native QtMultimedia.
Delivers raw QImage frames via signal, zero format conversion.
"""

import time
from typing import Optional

from PySide6.QtCore import QObject, Signal
from PySide6.QtMultimedia import (
    QCamera, QCameraDevice, QMediaCaptureSession, QVideoSink,
    QVideoFrame, QVideoFrameFormat,
)
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtGui import QImage

from app.utils.logger import get_logger


class QtCameraCapture(QObject):
    """Qt-native USB camera capture.

    Uses QCamera + QVideoSink for continuous frame delivery.
    Frames are delivered as QImage via frame_ready signal.
    Zero dependency on OpenCV or NumPy.

    Signals:
        frame_ready(QImage, float): Emitted when a new frame is available
            with the capture timestamp (perf_counter).
        error_occurred(str): Emitted on capture errors.
    """

    frame_ready = Signal(QImage, float)
    error_occurred = Signal(str)

    def __init__(self, parent: Optional[QObject] = None) -> None:
        """Initialize capture.

        Args:
            parent: Optional parent QObject.
        """
        super().__init__(parent)
        self._camera: Optional[QCamera] = None
        self._session: Optional[QMediaCaptureSession] = None
        self._sink: Optional[QVideoSink] = None
        self._is_running = False
        self._logger = get_logger(__name__)

    def start(self, device: QCameraDevice) -> bool:
        """Start capturing from a USB camera.

        Args:
            device: QCameraDevice to capture from.

        Returns:
            True if capture started.
        """
        self.stop()

        self._camera = QCamera(device)
        self._session = QMediaCaptureSession()
        self._sink = QVideoSink()

        self._session.setCamera(self._camera)
        self._session.setVideoSink(self._sink)

        self._sink.videoFrameChanged.connect(self._on_frame_changed)
        self._camera.errorOccurred.connect(self._on_error)

        self._camera.start()
        self._is_running = True
        self._logger.info(f"Camera started: {device.description()}")
        return True

    def stop(self) -> None:
        """Stop capturing."""
        if self._camera:
            self._camera.stop()
        self._is_running = False
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

    def is_running(self) -> bool:
        """Check if capture is active.

        Returns:
            True if camera is running.
        """
        return self._is_running and self._camera is not None

    def _on_frame_changed(self, frame: QVideoFrame) -> None:
        """Handle new video frame from QVideoSink.

        Args:
            frame: New video frame.
        """
        if not self._is_running:
            return
        if not frame.isValid():
            return

        capture_ts = time.perf_counter()
        image = frame.toImage()
        if not image.isNull():
            self.frame_ready.emit(image, capture_ts)

    def _on_error(self, error: 'QCamera.Error', error_string: str) -> None:
        """Handle camera errors.

        Args:
            error: Error type.
            error_string: Error description.
        """
        self._logger.error(f"Camera error: {error} - {error_string}")
        self.error_occurred.emit(str(error_string))
