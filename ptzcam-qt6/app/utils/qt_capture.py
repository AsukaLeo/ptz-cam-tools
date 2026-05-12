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

"""Qt Multimedia video capture module.

Uses PySide6.QtMultimedia for cross-platform video capture.
Simpler than DirectShow but with consistent device naming.
"""

from typing import Optional, Callable
from PySide6.QtCore import QObject, Signal, QThread
from PySide6.QtGui import QImage
from PySide6.QtMultimedia import QCamera, QMediaCaptureSession, QVideoFrame
from PySide6.QtMultimediaWidgets import QVideoWidget

from app.utils.logger import get_logger


class QtCaptureThread(QThread):
    """Video capture thread using Qt Multimedia."""
    
    frame_ready = Signal(QImage)
    error_occurred = Signal(str)
    state_changed = Signal(str)  # 'stopped', 'playing'
    
    def __init__(self, camera_device, parent: Optional[QObject] = None) -> None:
        """Initialize capture thread.
        
        Args:
            camera_device: QCameraDevice to capture from.
            parent: Optional parent.
        """
        super().__init__(parent)
        self._camera_device = camera_device
        self._camera: Optional[QCamera] = None
        self._session: Optional[QMediaCaptureSession] = None
        self._stop_flag = False
        self._logger = get_logger(__name__)
    
    def run(self) -> None:
        """Thread main loop."""
        try:
            self._logger.debug(f"Starting Qt capture for: {self._camera_device.description()}")
            
            # Create camera
            self._camera = QCamera(self._camera_device)
            
            # Create session
            self._session = QMediaCaptureSession()
            self._session.setCamera(self._camera)
            
            # Create video sink to receive frames
            from PySide6.QtMultimedia import QVideoSink
            video_sink = QVideoSink()
            video_sink.videoFrameChanged.connect(self._on_video_frame)
            self._session.setVideoSink(video_sink)
            
            # Start camera
            self._camera.start()
            self.state_changed.emit('playing')
            self._logger.debug("Qt camera started")
            
            # Run until stopped
            while not self._stop_flag:
                self.msleep(33)  # ~30fps
            
            self._camera.stop()
            
        except Exception as e:
            self._logger.error(f"Qt capture error: {e}")
            self.error_occurred.emit(str(e))
        
        finally:
            self.state_changed.emit('stopped')
    
    def _on_video_frame(self, frame: QVideoFrame) -> None:
        """Handle new video frame.
        
        Args:
            frame: Video frame from camera.
        """
        if not frame.isValid():
            return
        
        # Convert to QImage
        image = frame.toImage()
        if not image.isNull():
            self.frame_ready.emit(image)
    
    def stop(self) -> None:
        """Request thread stop."""
        self._stop_flag = True


class QtVideoCapture(QObject):
    """Qt Multimedia video capture manager."""
    
    frame_ready = Signal(QImage)
    error_occurred = Signal(str)
    state_changed = Signal(str)
    
    def __init__(self, parent: Optional[QObject] = None) -> None:
        """Initialize Qt video capture.
        
        Args:
            parent: Optional parent.
        """
        super().__init__(parent)
        self._capture_thread: Optional[QtCaptureThread] = None
        self._current_device = None
        self._is_running = False
        self._logger = get_logger(__name__)
    
    def start_capture(self, camera_device) -> bool:
        """Start video capture.
        
        Args:
            camera_device: QCameraDevice to capture from.
            
        Returns:
            True if started successfully.
        """
        if self._is_running:
            self.stop_capture()
        
        self._current_device = camera_device
        self._capture_thread = QtCaptureThread(camera_device, self)
        
        # Connect signals
        self._capture_thread.frame_ready.connect(self.frame_ready)
        self._capture_thread.error_occurred.connect(self.error_occurred)
        self._capture_thread.state_changed.connect(self._on_state_changed)
        
        # Start
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
        """Handle state change."""
        if state == 'stopped':
            self._is_running = False
        self.state_changed.emit(state)
    
    def is_running(self) -> bool:
        """Check if capture is running."""
        return self._is_running and self._capture_thread and self._capture_thread.isRunning()
