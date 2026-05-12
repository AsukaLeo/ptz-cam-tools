# Copyright (C) 2026 Asuka
#
# This file is part of PTZ-Cam-Tools.
#
# PTZ-Cam-Tools is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PTZ-Cam-Tools is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PTZ-Cam-Tools. If not, see <https://www.gnu.org/licenses/>.
# SPDX-License-Identifier: GPL-3.0-only

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

        # Frame throttling: store latest frame, deliver at ~30fps via timer
        self._latest_frame: Optional[QVideoFrame] = None
        self._frame_timer = QTimer()
        self._frame_timer.setInterval(33)  # ~30fps
        self._frame_timer.timeout.connect(self._deliver_frame)

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
        self._frame_timer.start()
        self._logger.info(f"RTSP connecting: {url}")
        return True

    def disconnect(self) -> None:
        """Stop RTSP stream."""
        self._frame_timer.stop()
        self._latest_frame = None
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
        """Store latest frame (no conversion here — avoid blocking main thread).

        Args:
            frame: New video frame.
        """
        if not frame.isValid():
            return
        self._latest_frame = QVideoFrame(frame)  # Copy for later use

    def _deliver_frame(self) -> None:
        """Timer callback: convert latest frame and deliver."""
        if self._latest_frame is None:
            return
        if not self._latest_frame.isValid():
            return

        frame = self._latest_frame
        self._latest_frame = None
        capture_ts = time.perf_counter()

        try:
            image = frame.toImage()
        except Exception:
            return

        if image.isNull():
            return

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
        try:
            state_name = {0: 'stopped', 1: 'playing', 2: 'paused'}.get(int(state), 'unknown')
        except TypeError:
            state_name = str(state).split('.')[-1] if '.' in str(state) else str(state)
        self._logger.debug(f"RTSP state: {state_name}")
