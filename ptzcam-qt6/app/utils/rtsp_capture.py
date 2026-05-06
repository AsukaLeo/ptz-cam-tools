"""RTSP stream capture module.

Provides RTSP video source capture using OpenCV's VideoCapture
with FFmpeg backend. Supports H264 decoding and transport
protocol selection (UDP/TCP).

Design reference: VLC live555.cpp
  - OPTIONS -> DESCRIBE -> SETUP -> PLAY (handled by FFmpeg internally)
  - Transport protocol fallback: UDP default, detect failure -> TCP
  - Frame timeout detection with auto-reconnect
"""

import time
from typing import Optional, Callable

from PySide6.QtCore import QObject, Signal, QThread
from PySide6.QtGui import QImage

from app.utils.logger import get_logger


class RTSPSource(QObject):
    """RTSP video source capture.

    Manages the RTSP capture thread lifecycle. Provides signals
    for frame delivery, error reporting, and state changes.

    Signals:
        frame_ready: Emitted with (QImage, capture_timestamp) for each frame.
        error_occurred: Emitted with error description string.
        state_changed: Emitted with state string: 'connecting', 'connected',
                      'disconnected', 'error'.
    """

    frame_ready = Signal(QImage, float)
    error_occurred = Signal(str)
    state_changed = Signal(str)

    _RECONNECT_DELAY_S = 2.0
    _MAX_RECONNECT_ATTEMPTS = 3

    def __init__(self, parent: Optional[QObject] = None) -> None:
        """Initialize RTSPSource.

        Args:
            parent: Optional parent QObject.
        """
        super().__init__(parent)
        self._logger = get_logger(__name__)
        self._thread: Optional['RTSPCaptureThread'] = None
        self._is_running = False

    def start(self, url: str, transport: str = "udp",
              callback: Optional[Callable[[QImage], None]] = None) -> bool:
        """Start RTSP capture.

        Fully cleans up any previous thread before starting a new one.

        Args:
            url: Full RTSP URL (rtsp://host[:port]/path).
            transport: Transport protocol - 'udp' or 'tcp'.
            callback: Optional frame callback (avoids signal connection overhead).

        Returns:
            True if capture thread was started, False otherwise.
        """
        if self._thread and self._thread.isRunning():
            self._logger.debug("Stopping existing capture before restart")
            self._thread.stop()
            self._thread.wait(3000)
            self._thread = None

        self._logger.info(f"Starting RTSP capture: {url} ({transport})")
        self._thread = RTSPCaptureThread(url, transport, self)

        if callback:
            self._thread.frame_ready.connect(callback)
        self._thread.frame_ready.connect(self.frame_ready)
        self._thread.error_occurred.connect(self.error_occurred)
        self._thread.state_changed.connect(self._on_state_changed)

        self._thread.start()
        self._is_running = True
        return True

    def stop(self) -> None:
        """Stop RTSP capture. Blocks until thread exits."""
        if self._thread and self._thread.isRunning():
            self._logger.debug("Stopping RTSP capture")
            self._thread.stop()
            if not self._thread.wait(5000):
                self._logger.warning("RTSP capture thread did not stop in time")
                self._thread.terminate()
                self._thread.wait(1000)

        self._thread = None
        self._is_running = False
        self.state_changed.emit('disconnected')

    def is_running(self) -> bool:
        """Check if capture is currently active.

        Returns:
            True if a capture thread is running.
        """
        return self._is_running and self._thread is not None and self._thread.isRunning()

    def _on_state_changed(self, state: str) -> None:
        """Forward state changes, tracking running flag.

        Args:
            state: New state from the capture thread.
        """
        if state in ('disconnected', 'error'):
            self._is_running = False
        self.state_changed.emit(state)


class RTSPCaptureThread(QThread):
    """RTSP capture thread using OpenCV + FFmpeg backend.

    Runs a blocking read loop on an RTSP URL. Frames are converted
    to QImage and emitted via frame_ready signal.

    Signals:
        frame_ready: (QImage, capture_timestamp)
        error_occurred: (error_message)
        state_changed: (state_string)
    """

    frame_ready = Signal(QImage, float)
    error_occurred = Signal(str)
    state_changed = Signal(str)

    _FRAME_TIMEOUT_S = 5.0
    _MAX_READ_FAILURES = 100
    _RECONNECT_DELAY_S = 2.0
    _MAX_RECONNECT_ATTEMPTS = 3

    def __init__(self, url: str, transport: str = "udp",
                 parent: Optional[QObject] = None) -> None:
        """Initialize capture thread.

        Args:
            url: Full RTSP URL.
            transport: 'udp' or 'tcp'.
            parent: Optional parent QObject.
        """
        super().__init__(parent)
        self._url = url
        self._transport = transport
        self._stop_flag = False
        self._logger = get_logger(__name__)

    def run(self) -> None:
        """Main thread loop: connect, read frames, handle errors/reconnect."""
        try:
            import cv2
        except ImportError:
            self.error_occurred.emit("OpenCV not available")
            self.state_changed.emit('error')
            return

        # Build URL with transport option following FFmpeg RTSP conventions
        url = self._build_url()
        attempts = 0

        while not self._stop_flag and attempts <= self._MAX_RECONNECT_ATTEMPTS:
            attempts += 1
            self.state_changed.emit('connecting' if attempts == 1 else 'reconnecting')

            cap = None
            try:
                cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)

                if not cap.isOpened():
                    msg = f"无法连接 RTSP 流 (尝试 {attempts}/{self._MAX_RECONNECT_ATTEMPTS})"
                    self._logger.warning(msg)
                    if attempts <= self._MAX_RECONNECT_ATTEMPTS:
                        self._reconnect_delay()
                        continue
                    self.error_occurred.emit("无法连接 RTSP 流")
                    self.state_changed.emit('error')
                    return

                self._logger.info(f"RTSP stream connected (attempt {attempts})")
                self.state_changed.emit('connected')

                # Main frame read loop
                fail_count = 0
                last_frame_time = time.perf_counter()
                frame_count = 0

                while not self._stop_flag:
                    ret, frame = cap.read()

                    if not ret:
                        fail_count += 1
                        if fail_count == 1:
                            self._logger.warning("First RTSP read failed")
                        elif fail_count % 30 == 0:
                            self._logger.warning(
                                f"RTSP read failed {fail_count} times"
                            )

                        # Timeout: no frame for too long
                        elapsed = time.perf_counter() - last_frame_time
                        if elapsed > self._FRAME_TIMEOUT_S:
                            self._logger.error(
                                f"RTSP stream timeout ({elapsed:.0f}s no frame)"
                            )
                            raise TimeoutError(f"无数据 {elapsed:.0f} 秒")

                        if fail_count >= self._MAX_READ_FAILURES:
                            self._logger.error(
                                f"Too many read failures ({fail_count})"
                            )
                            raise ConnectionError("连续读取失败")

                        time.sleep(0.01)  # Prevent busy-loop on fast failures
                        continue

                    # Successful read
                    capture_ts = time.perf_counter()
                    fail_count = 0
                    last_frame_time = capture_ts
                    frame_count += 1

                    image = self._cv_frame_to_qimage(frame)
                    if image:
                        self.frame_ready.emit(image, capture_ts)
                    else:
                        self._logger.warning("Failed to convert RTSP frame to QImage")

            except (TimeoutError, ConnectionError) as e:
                self._logger.warning(f"Stream issue: {e}")
                if attempts <= self._MAX_RECONNECT_ATTEMPTS:
                    self.error_occurred.emit(f"流异常: {e}，正在重连...")
                    self._reconnect_delay()
                    continue
                self.error_occurred.emit(f"流已断开，重连失败")
                break

            except Exception as e:
                self._logger.error(f"RTSP capture error: {e}")
                self.error_occurred.emit(f"RTSP 错误: {e}")
                if attempts <= self._MAX_RECONNECT_ATTEMPTS:
                    self._reconnect_delay()
                    continue
                break

            finally:
                if cap:
                    cap.release()

            # If we reach here, the stream ended cleanly (not by reconnect logic)
            break

        self.state_changed.emit('disconnected')

    def stop(self) -> None:
        """Request thread to stop at the next opportunity."""
        self._stop_flag = True

    def _build_url(self) -> str:
        """Build the full RTSP URL with transport options.

        Appends transport parameter for FFmpeg when TCP is selected.

        Returns:
            Processed RTSP URL string.
        """
        url = self._url
        if self._transport == "tcp":
            # FFmpeg RTSP transport option via URL parameter
            if "?" in url:
                if not url.endswith("?") and not url.endswith("&"):
                    url += "&"
                url += "transport=tcp"
            else:
                url += "?transport=tcp"
        return url

    def _reconnect_delay(self) -> None:
        """Sleep for the configured reconnect delay, checking stop flag."""
        self._logger.debug(
            f"Waiting {self._RECONNECT_DELAY_S}s before reconnection..."
        )
        deadline = time.perf_counter() + self._RECONNECT_DELAY_S
        while time.perf_counter() < deadline and not self._stop_flag:
            time.sleep(0.1)

    @staticmethod
    def _cv_frame_to_qimage(frame) -> Optional[QImage]:
        """Convert an OpenCV BGR frame to a QImage (RGB888).

        Args:
            frame: OpenCV frame (numpy array, BGR format).

        Returns:
            QImage in RGB888 format, or None if conversion fails.
        """
        if frame is None or frame.size == 0:
            return None

        try:
            import cv2
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            height, width = rgb_frame.shape[:2]
            bytes_per_line = 3 * width

            image = QImage(rgb_frame.data, width, height,
                          bytes_per_line, QImage.Format_RGB888)
            return image.copy()
        except Exception:
            return None
