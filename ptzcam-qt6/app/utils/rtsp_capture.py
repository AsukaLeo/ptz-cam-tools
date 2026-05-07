"""RTSP stream capture module — OpenCV-free using Qt QMediaPlayer.

Replaces cv2.VideoCapture + FFmpeg backend with Qt's native QMediaPlayer
+ QVideoSink. Zero dependency on OpenCV or NumPy.

Qt 6.5+ on Windows uses FFmpeg as the multimedia backend,
so RTSP streaming works out of the box.
"""

import time
from typing import Optional

from PySide6.QtCore import QObject, Signal, QUrl, QTimer
from PySide6.QtGui import QImage
from PySide6.QtMultimedia import (
    QMediaPlayer, QVideoSink, QVideoFrame,
)

from app.utils.logger import get_logger


class RTSPSource(QObject):
    """RTSP video source using Qt QMediaPlayer.

    Manages RTSP stream lifecycle with QMediaPlayer + QVideoSink.
    Provides signals for frame delivery, error reporting, and state changes.

    Signals:
        frame_ready: (QImage, capture_timestamp) for each frame.
        error_occurred: Error description string.
        state_changed: State: 'connecting', 'connected', 'error'.
    """

    frame_ready = Signal(QImage, float)
    error_occurred = Signal(str)
    state_changed = Signal(str)

    def __init__(self, parent: Optional[QObject] = None) -> None:
        """Initialize RTSPSource.

        Args:
            parent: Optional parent QObject.
        """
        super().__init__(parent)
        self._logger = get_logger(__name__)
        self._player: Optional[QMediaPlayer] = None
        self._sink: Optional[QVideoSink] = None
        self._url: str = ""
        self._playing = False

    def connect_to(self, url: str) -> bool:
        """Connect to RTSP stream.

        Args:
            url: Full RTSP URL.

        Returns:
            True if connection started.
        """
        self.disconnect()

        self._url = url
        self.state_changed.emit('connecting')

        self._player = QMediaPlayer()
        self._sink = QVideoSink()

        self._player.setVideoSink(self._sink)
        self._sink.videoFrameChanged.connect(self._on_frame_changed)

        self._player.errorOccurred.connect(self._on_player_error)
        self._player.playbackStateChanged.connect(self._on_state_change)

        self._player.setSource(QUrl(url))

        if self._player.error() != QMediaPlayer.Error.NoError:
            self._logger.error(f"RTSP player error: {self._player.errorString()}")
            self.error_occurred.emit(str(self._player.errorString()))
            return False

        self._player.play()
        self._logger.info(f"RTSP connecting: {url}")
        return True

    def disconnect(self) -> None:
        """Stop RTSP stream."""
        if self._player:
            self._player.stop()
        if self._sink:
            try:
                self._sink.videoFrameChanged.disconnect(self._on_frame_changed)
            except (TypeError, RuntimeError):
                pass
        if self._player:
            try:
                self._player.errorOccurred.disconnect(self._on_player_error)
                self._player.playbackStateChanged.disconnect(self._on_state_change)
            except (TypeError, RuntimeError):
                pass
        self._player = None
        self._sink = None
        self._playing = False

    def is_playing(self) -> bool:
        """Check if stream is active.

        Returns:
            True if streaming.
        """
        return self._playing and self._player is not None

    def _on_frame_changed(self, frame: QVideoFrame) -> None:
        """Handle new RTSP frame.

        Args:
            frame: New video frame.
        """
        if not frame.isValid():
            return

        capture_ts = time.perf_counter()
        try:
            image = frame.toImage()
        except Exception:
            return

        if not image.isNull():
            if not self._playing:
                self._playing = True
                self.state_changed.emit('connected')
            self.frame_ready.emit(image, capture_ts)

    def _on_player_error(self, error: 'QMediaPlayer.Error', error_string: str) -> None:
        """Handle player error.

        Args:
            error: Error type.
            error_string: Error description.
        """
        self._logger.error(f"RTSP error: {error_string}")
        self._playing = False
        self.error_occurred.emit(str(error_string))
        self.state_changed.emit('error')

    def _on_state_change(self, state: 'QMediaPlayer.PlaybackState') -> None:
        """Log playback state changes.

        Args:
            state: New playback state.
        """
        state_name = {0: 'stopped', 1: 'playing', 2: 'paused'}.get(int(state), 'unknown')
        self._logger.debug(f"RTSP state: {state_name}")
