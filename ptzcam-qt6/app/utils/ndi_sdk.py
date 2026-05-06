"""NDI SDK ctypes wrapper.

Provides ctypes bindings for the NDI SDK v5/v6 runtime DLL
(Processing.NDI.Lib.x64.dll). Loads the DLL from the NDI install
path or NDI_REDIST_FOLDER environment variable.

All functions are exported directly by the DLL, so we use simple
ctypes function wrappers rather than the vtable loading pattern.
"""

import ctypes
import os
from ctypes import (
    c_bool, c_int, c_int64, c_float, c_char_p, c_void_p,
    c_uint8, c_uint32, POINTER, Structure, CFUNCTYPE
)
from typing import Optional, List, Tuple

from app.utils.logger import get_logger

_logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# DLL loading
# ---------------------------------------------------------------------------

_ndi_dll: Optional[ctypes.CDLL] = None


def _find_dll() -> Optional[str]:
    """Locate the NDI runtime DLL on disk.

    Search order:
    1. NDI_REDIST_FOLDER environment variable
    2. Standard NDI 6 Runtime install path
    3. Standard NDI 5 Runtime install path
    4. System PATH

    Returns:
        Full path to the DLL, or None if not found.
    """
    candidates = []

    # Env var
    redist = os.environ.get("NDI_REDIST_FOLDER", "")
    if redist:
        candidates.append(os.path.join(redist, "Processing.NDI.Lib.x64.dll"))

    # NDI 6
    candidates.append(
        r"C:\Program Files\NDI\NDI 6 Runtime\v6\Processing.NDI.Lib.x64.dll"
    )
    # NDI 5
    candidates.append(
        r"C:\Program Files\NDI\NDI 5 Runtime\Processing.NDI.Lib.x64.dll"
    )

    for path in candidates:
        if os.path.isfile(path):
            return path

    # Fallback: try bare name (must be on PATH)
    return "Processing.NDI.Lib.x64.dll"


def _ensure_dll() -> None:
    """Load the NDI DLL if not already loaded."""
    global _ndi_dll
    if _ndi_dll is not None:
        return

    dll_path = _find_dll()
    _logger.info(f"Loading NDI DLL: {dll_path}")
    _ndi_dll = ctypes.CDLL(dll_path)


def _fn(name: str, restype: type = None, argtypes: list = None):
    """Get a wrapped function from the NDI DLL.

    Args:
        name: Function name as exported by the DLL.
        restype: Return type (ctypes type or None for void).
        argtypes: List of argument types.

    Returns:
        Callable function with proper type signatures.
    """
    _ensure_dll()
    func = getattr(_ndi_dll, name)
    if restype is not None:
        func.restype = restype
    if argtypes is not None:
        func.argtypes = argtypes
    return func


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class FourCCVideoType:
    """NDIlib_FourCC_video_type_e"""
    UYVY = 0
    UYVA = 1
    P216 = 2
    PA16 = 3
    YV12 = 4
    I420 = 5
    NV12 = 6
    BGRA = 7
    BGRX = 8
    RGBA = 9
    RGBX = 10


class FrameType:
    """NDIlib_frame_type_e"""
    NONE = 0
    VIDEO = 1
    AUDIO = 2
    METADATA = 3
    ERROR = 4
    STATUS_CHANGE = 5


class RecvBandwidth:
    """NDIlib_recv_bandwidth_e"""
    METADATA_ONLY = -10
    AUDIO_ONLY = 10
    LOWEST = 0
    HIGHEST = 100


class RecvColorFormat:
    """NDIlib_recv_color_format_e"""
    BGRX_BGRA = 0       # BGRA bytes, BGRX if no alpha
    UYVY_BGRA = 1        # UYVY -> BGRA conversion
    RGBX_RGBA = 2        # RGBA bytes, RGBX if no alpha
    UYVY_RGBA = 3        # UYVY -> RGBA conversion
    FASTEST = 100         # Let SDK pick fastest
    BEST = 101            # Let SDK pick best quality


# ---------------------------------------------------------------------------
# Structures
# ---------------------------------------------------------------------------

class source_t(Structure):
    """NDIlib_source_t"""
    _fields_ = [
        ("p_ndi_name", c_char_p),
        ("p_url_address", c_char_p),
    ]


class find_create_t(Structure):
    """NDIlib_find_create_t"""
    _fields_ = [
        ("show_local_sources", c_bool),
        ("p_groups", c_char_p),
        ("p_extra_ips", c_char_p),
    ]


class recv_create_v3_t(Structure):
    """NDIlib_recv_create_v3_t"""
    _fields_ = [
        ("source_to_connect_to", source_t),
        ("color_format", c_int),     # RecvColorFormat
        ("bandwidth", c_int),        # RecvBandwidth
        ("allow_video_fields", c_bool),
        ("p_ndi_recv_name", c_char_p),
    ]


class video_frame_v2_t(Structure):
    """NDIlib_video_frame_v2_t"""
    _fields_ = [
        ("xres", c_int),
        ("yres", c_int),
        ("FourCC", c_int),
        ("frame_rate_N", c_int),
        ("frame_rate_D", c_int),
        ("picture_aspect_ratio", c_float),
        ("frame_format_type", c_int),
        ("timecode", c_int64),
        ("p_data", POINTER(c_uint8)),
        ("line_stride_in_bytes", c_int),
        ("p_metadata", c_char_p),
        ("timestamp", c_int64),
    ]


class metadata_frame_t(Structure):
    """NDIlib_metadata_frame_t"""
    _fields_ = [
        ("length", c_int),
        ("timecode", c_int64),
        ("p_data", c_char_p),
    ]


class tally_t(Structure):
    """NDIlib_tally_t"""
    _fields_ = [
        ("on_program", c_bool),
        ("on_preview", c_bool),
    ]


# ---------------------------------------------------------------------------
# Function wrappers
# ---------------------------------------------------------------------------

def initialize() -> bool:
    """Initialize NDI. Must be called once before any other NDI function.

    Returns:
        True if successful.
    """
    return bool(_fn("NDIlib_initialize", c_bool)())


def destroy() -> None:
    """Destroy NDI. Call on shutdown."""
    _fn("NDIlib_destroy", None)()


def find_create_v2(settings: find_create_t) -> Optional[int]:
    """Create a source finder instance.

    Args:
        settings: Find creation settings.

    Returns:
        Opaque finder handle (int), or None on failure.
    """
    ptr = _fn("NDIlib_find_create_v2", c_void_p, [POINTER(find_create_t)])(
        ctypes.byref(settings)
    )
    return ptr if ptr else None


def find_destroy(finder: int) -> None:
    """Destroy a source finder.

    Args:
        finder: Finder handle from find_create_v2.
    """
    _fn("NDIlib_find_destroy", None, [c_void_p])(finder)


def find_wait_for_sources(finder: int, timeout_ms: int = 5000) -> bool:
    """Wait for new sources to be discovered.

    Args:
        finder: Finder handle.
        timeout_ms: Maximum wait time in milliseconds.

    Returns:
        True if new sources are available.
    """
    return bool(
        _fn("NDIlib_find_wait_for_sources", c_bool, [c_void_p, c_uint32])(
            finder, timeout_ms
        )
    )


def find_get_current_sources(finder: int) -> Tuple[List[source_t], int]:
    """Get the list of currently discovered NDI sources.

    Args:
        finder: Finder handle.

    Returns:
        Tuple of (sources_list, count).
    """
    p_count = c_int(0)
    arr = _fn(
        "NDIlib_find_get_current_sources",
        POINTER(source_t),
        [c_void_p, POINTER(c_int)],
    )(finder, ctypes.byref(p_count))

    count = p_count.value
    sources = []
    if arr and count > 0:
        for i in range(count):
            sources.append(arr[i])
    return sources, count


def recv_create_v3(settings: recv_create_v3_t) -> Optional[int]:
    """Create a receiver instance.

    Args:
        settings: Receiver creation settings.

    Returns:
        Receiver handle (int), or None on failure.
    """
    ptr = _fn("NDIlib_recv_create_v3", c_void_p, [POINTER(recv_create_v3_t)])(
        ctypes.byref(settings)
    )
    return ptr if ptr else None


def recv_destroy(recv: int) -> None:
    """Destroy a receiver.

    Args:
        recv: Receiver handle.
    """
    _fn("NDIlib_recv_destroy", None, [c_void_p])(recv)


def recv_connect(recv: int, source: source_t) -> None:
    """Connect a receiver to a specific source.

    Args:
        recv: Receiver handle.
        source: Source to connect to.
    """
    _fn("NDIlib_recv_connect", None, [c_void_p, POINTER(source_t)])(
        recv, ctypes.byref(source)
    )


def recv_capture_v2(
    recv: int,
    video: Optional['video_frame_v2_t'],
    audio: Optional['ctypes.c_void_p'],
    metadata: Optional['metadata_frame_t'],
    timeout_ms: int,
) -> int:
    """Capture a frame from the receiver.

    Args:
        recv: Receiver handle.
        video: Output video frame (or None).
        audio: Output audio frame (or None).
        metadata: Output metadata (or None).
        timeout_ms: Timeout in milliseconds.

    Returns:
        FrameType value indicating what was captured.
    """
    p_video = ctypes.byref(video) if video is not None else None
    p_audio = audio  # keep as void
    p_meta = ctypes.byref(metadata) if metadata is not None else None

    return int(
        _fn(
            "NDIlib_recv_capture_v2",
            c_int,
            [c_void_p, c_void_p, c_void_p, c_void_p, c_uint32],
        )(recv, p_video, p_audio, p_meta, timeout_ms)
    )


def recv_free_video_v2(recv: int, video: video_frame_v2_t) -> None:
    """Free a video frame received from recv_capture_v2.

    Args:
        recv: Receiver handle.
        video: Video frame to free.
    """
    _fn("NDIlib_recv_free_video_v2", None, [c_void_p, POINTER(video_frame_v2_t)])(
        recv, ctypes.byref(video)
    )


def recv_free_metadata(recv: int, metadata: metadata_frame_t) -> None:
    """Free a metadata frame.

    Args:
        recv: Receiver handle.
        metadata: Metadata frame to free.
    """
    _fn("NDIlib_recv_free_metadata", None, [c_void_p, POINTER(metadata_frame_t)])(
        recv, ctypes.byref(metadata)
    )


def recv_free_string(recv: int, string: c_char_p) -> None:
    """Free a string returned by NDI.

    Args:
        recv: Receiver handle.
        string: String pointer to free.
    """
    _fn("NDIlib_recv_free_string", None, [c_void_p, c_char_p])(recv, string)
