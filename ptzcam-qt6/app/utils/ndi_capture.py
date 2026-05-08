"""NDI source discovery and video capture module.

Provides high-level wrappers around the NDI SDK for source discovery
and video frame capture with QImage conversion.
"""

import time
import ctypes
from typing import Optional, Callable, List

from PySide6.QtCore import QObject, Signal, QThread
from PySide6.QtGui import QImage

from app.utils.ndi_sdk import (
    initialize as ndi_initialize,
    destroy as ndi_destroy,
    source_t,
    find_create_t,
    find_create_v2,
    find_destroy,
    find_wait_for_sources,
    find_get_current_sources,
    recv_create_v3_t,
    recv_create_v3,
    recv_destroy,
    recv_connect,
    recv_capture_v2,
    recv_free_video_v2,
    video_frame_v2_t,
    metadata_frame_t,
    recv_get_performance,
    recv_performance_t,
    FrameType,
    RecvColorFormat,
    RecvBandwidth,
)
from app.utils.logger import get_logger

_logger = get_logger(__name__)

# Global NDI init/refcount
_ndi_refcount = 0


def _ndi_ensure_init() -> bool:
    """Increment NDI reference count and initialize if needed."""
    global _ndi_refcount
    if _ndi_refcount == 0:
        if not ndi_initialize():
            _logger.error("NDI initialization failed")
            return False
        _logger.info("NDI initialized")
    _ndi_refcount += 1
    return True


def _ndi_release() -> None:
    """Decrement NDI reference count and destroy if zero."""
    global _ndi_refcount
    _ndi_refcount -= 1
    if _ndi_refcount <= 0:
        _ndi_refcount = 0
        ndi_destroy()
        _logger.info("NDI destroyed")


# ---------------------------------------------------------------------------
# Source discovery
# ---------------------------------------------------------------------------

class NDISource:
    """Represents a discovered NDI source.

    Attributes:
        name: Human-readable source name.
        url: Source URL address.
    """

    def __init__(self, name: str, url: str = "") -> None:
        self.name = name
        self.url = url

    def __repr__(self) -> str:
        return self.name


class NDISourceFinder:
    """NDI source discovery via mDNS.

    Usage:
        finder = NDISourceFinder()
        sources = finder.discover(timeout_ms=3000)
        for src in sources:
            print(src.name)
        finder.close()
    """

    def __init__(self) -> None:
        """Initialize source finder."""
        self._finder: Optional[int] = None
        self._initialized = False

    def open(self) -> bool:
        """Open the source finder.

        Returns:
            True if successful.
        """
        if self._finder is not None:
            return True

        if not _ndi_ensure_init():
            return False

        settings = find_create_t(show_local_sources=True)
        self._finder = find_create_v2(settings)
        if not self._finder:
            _logger.error("Failed to create NDI source finder")
            return False

        self._initialized = True
        return True

    def discover(self, timeout_ms: int = 3000) -> List[NDISource]:
        """Discover NDI sources on the network.

        Args:
            timeout_ms: Maximum time to wait for sources (ms).

        Returns:
            List of discovered NDISource objects.
        """
        if not self._finder:
            if not self.open():
                return []

        wait_for_sources = find_wait_for_sources(self._finder, timeout_ms)
        if not wait_for_sources:
            return []

        sources, count = find_get_current_sources(self._finder)
        result = []
        for i in range(count):
            src = sources[i]
            name = src.p_ndi_name.decode("utf-8", errors="replace") if src.p_ndi_name else ""
            url = src.p_url_address.decode("utf-8", errors="replace") if src.p_url_address else ""
            result.append(NDISource(name, url))

        return result

    def close(self) -> None:
        """Close the source finder and release resources."""
        if self._finder:
            find_destroy(self._finder)
            self._finder = None
        if self._initialized:
            _ndi_release()
            self._initialized = False


# ---------------------------------------------------------------------------
# Video capture thread
# ---------------------------------------------------------------------------

class NDICapture(QObject):
    """NDI video capture.

    Manages a receiver thread that captures video frames from a
    specified NDI source and emits them as QImage.

    Signals:
        frame_ready: Emitted with (QImage, capture_timestamp).
        error_occurred: Emitted with error description.
        state_changed: Emitted with state string.
    """

    frame_ready = Signal(QImage, float)
    error_occurred = Signal(str)
    state_changed = Signal(str)

    def __init__(self, parent: Optional[QObject] = None) -> None:
        """Initialize NDI capture."""
        super().__init__(parent)
        self._thread: Optional['NDICaptureThread'] = None
        self._initialized = False
        self._is_running = False

    def start(self, source: NDISource,
              callback: Optional[Callable[[QImage], None]] = None) -> bool:
        """Start capturing from an NDI source.

        Args:
            source: NDI source to capture from.
            callback: Optional frame callback.

        Returns:
            True if capture thread started.
        """
        if self._thread and self._thread.isRunning():
            self.stop()

        if not _ndi_ensure_init():
            self.error_occurred.emit("NDI initialization failed")
            return False
        self._initialized = True

        _logger.info(f"Starting NDI capture: {source.name}")
        self._thread = NDICaptureThread(source, self)

        if callback:
            self._thread.frame_ready.connect(callback)
        self._thread.frame_ready.connect(self.frame_ready)
        self._thread.error_occurred.connect(self.error_occurred)
        self._thread.state_changed.connect(self._on_state_changed)

        self._thread.start()
        self._is_running = True
        return True

    def stop(self) -> None:
        """Stop NDI capture."""
        if self._thread and self._thread.isRunning():
            _logger.debug("Stopping NDI capture")
            self._thread.stop()
            if not self._thread.wait(5000):
                _logger.warning("NDI capture thread did not stop in time")
                self._thread.terminate()
                self._thread.wait(1000)

        self._thread = None
        self._is_running = False
        self.state_changed.emit('disconnected')

        if self._initialized:
            _ndi_release()
            self._initialized = False

    def is_running(self) -> bool:
        """Check if capture is active."""
        return self._is_running and self._thread is not None and self._thread.isRunning()

    def _on_state_changed(self, state: str) -> None:
        if state in ('disconnected', 'error'):
            self._is_running = False
        self.state_changed.emit(state)


class NDICaptureThread(QThread):
    """NDI receiver thread.

    Creates an NDI receiver, connects to a source, and captures
    video frames in a loop.
    """

    frame_ready = Signal(QImage, float)
    error_occurred = Signal(str)
    state_changed = Signal(str)

    def __init__(self, source: NDISource, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._source = source
        self._stop_flag = False
        self._recv: Optional[int] = None
        self._logger = get_logger(__name__)

    def run(self) -> None:
        """Main thread loop."""
        self._logger.info(f"NDI connecting to: {self._source.name}")
        self.state_changed.emit('connecting')

        try:
            # Build source struct
            src = source_t()
            src.p_ndi_name = self._source.name.encode("utf-8")
            if self._source.url:
                src.p_url_address = self._source.url.encode("utf-8")

            # Create receiver settings
            settings = recv_create_v3_t(
                source_to_connect_to=src,
                color_format=RecvColorFormat.BGRX_BGRA,
                bandwidth=RecvBandwidth.HIGHEST,
                allow_video_fields=True,
                p_ndi_recv_name=b"PTZ-Cam-Tools NDI Receiver",
            )

            self._recv = recv_create_v3(settings)
            if not self._recv:
                self.error_occurred.emit("Failed to create NDI receiver")
                self.state_changed.emit('error')
                return

            # Capture loop
            self.state_changed.emit('connected')
            fail_count = 0
            first_frame = True
            last_video_frames = 0
            while not self._stop_flag:
                frame = video_frame_v2_t()
                result = recv_capture_v2(
                    self._recv, frame, None, None, 1000  # 1s timeout
                )

                if result == FrameType.VIDEO:
                    if first_frame:
                        first_frame = False
                    fail_count = 0
                    capture_ts = time.perf_counter()

                    # Convert BGRA frame to QImage
                    image = self._bgra_to_qimage(frame)
                    if image:
                        self.frame_ready.emit(image, capture_ts)

                    recv_free_video_v2(self._recv, frame)

                elif result == FrameType.NONE:
                    if not first_frame:
                        fail_count += 1
                    # Query performance stats when frames stop
                    # to confirm no video data is arriving at all
                    if fail_count == 5:
                        perf = recv_performance_t()
                        recv_get_performance(self._recv, perf)
                        self._logger.warning(
                            f"NDI: 5s no frame — perf: video={perf.video_frames}, "
                            f"audio={perf.audio_frames}, dropped={perf.dropped_frames}, "
                            f"pkt_lost={perf.total_lost_packets}"
                        )
                        if perf.video_frames == last_video_frames:
                            self.error_occurred.emit(
                                "NDI 信号中断 — 源设备可能为非授权/试用版本，已停止输出视频流"
                            )
                    # 30 seconds no frame: disconnect
                    if fail_count >= 30:
                        self._logger.error("NDI: 30s no frame, disconnecting")
                        self.error_occurred.emit("NDI 信号已断开（30秒无数据）")
                        self.state_changed.emit('disconnected')
                        break

                elif result == FrameType.ERROR:
                    self._logger.warning("NDI capture error")
                    self.error_occurred.emit("NDI 接收错误")
                    break

                # Track video frame count for performance comparison
                if fail_count == 0:
                    perf = recv_performance_t()
                    recv_get_performance(self._recv, perf)
                    last_video_frames = perf.video_frames

                # METADATA and STATUS_CHANGE: continue silently

        except Exception as e:
            self._logger.error(f"NDI capture error: {e}")
            self.error_occurred.emit(f"NDI 错误: {e}")

        finally:
            self._cleanup()

    def stop(self) -> None:
        """Request thread to stop."""
        self._stop_flag = True

    def _cleanup(self) -> None:
        """Release NDI receiver resources."""
        if self._recv:
            recv_destroy(self._recv)
            self._recv = None
        self.state_changed.emit('disconnected')

    @staticmethod
    def _bgra_to_qimage(frame: video_frame_v2_t) -> Optional[QImage]:
        """Convert an NDI BGRA video frame to QImage.

        NDI BGRA byte order on little-endian matches QImage.Format_RGB32:
          byte 0 = B, byte 1 = G, byte 2 = R, byte 3 = A (0xFF for BGRX).

        Args:
            frame: NDI video frame.

        Returns:
            QImage in RGB888 format, or None on failure.
        """
        if not frame.p_data or frame.xres <= 0 or frame.yres <= 0:
            return None

        try:
            width = frame.xres
            height = frame.yres
            stride = frame.line_stride_in_bytes

            # Read raw frame data
            buf = (ctypes.c_uint8 * (stride * height)).from_address(
                ctypes.addressof(frame.p_data.contents)
            )

            # Create QImage from BGRA data
            # On little-endian, Format_RGB32 byte order matches NDI BGRA
            image = QImage(
                buf, width, height, stride, QImage.Format_RGB32
            ).copy()

            # Convert to RGB888 for preview widget compatibility
            image = image.convertToFormat(QImage.Format_RGB888)

            return image

        except Exception as e:
            _logger.error(f"NDI frame conversion error: {e}")
            return None
