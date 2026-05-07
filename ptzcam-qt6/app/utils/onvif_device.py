"""ONVIF device discovery, connection and control module.

Provides ONVIF device discovery via WS-Discovery, device connection
using onvif-zeep, RTSP stream URL retrieval, and basic device info.
"""

from dataclasses import dataclass, field
from typing import Optional, List
import time

from app.utils.logger import get_logger

_logger = get_logger(__name__)

# Common ONVIF default credentials to try when auth fails.
# Format: list of (username, password) tuples.
_COMMON_CREDENTIALS: list[tuple[str, str]] = [
    ("admin", "9999"),   # User's specific camera
    ("admin", ""),
    ("admin", "admin"),
    ("admin", "12345"),
    ("admin", "password"),
    ("admin", "Admin123"),
    ("admin", "Admin@123"),
    ("admin", "123456"),
    ("admin", "111111"),
    ("admin", "888888"),
    ("admin", "1234"),
    ("root", ""),
    ("root", "pass"),
    ("root", "root"),
    ("Administrator", ""),
    ("Administrator", "admin"),
    ("user", "user"),
    ("guest", ""),
    ("guest", "guest"),
    ("", ""),
]


@dataclass
class ONVIFDeviceInfo:
    """Information about a discovered or connected ONVIF device.

    Attributes:
        ip: Device IP address.
        port: Device HTTP port.
        xaddr: Full XAddr (service URL) from WS-Discovery.
        manufacturer: Device manufacturer name.
        model: Device model name.
        firmware: Firmware version.
        serial: Serial number.
        hardware: Hardware ID.
        scopes: WS-Discovery scopes (hardware name, location, etc.).
        rtsp_url: RTSP stream URL (populated after connecting).
    """
    ip: str = ""
    port: int = 80
    xaddr: str = ""
    manufacturer: str = ""
    model: str = ""
    firmware: str = ""
    serial: str = ""
    hardware: str = ""
    scopes: List[str] = field(default_factory=list)
    rtsp_url: str = ""

    def display_name(self) -> str:
        """Get a human-readable display name."""
        if self.manufacturer and self.model:
            return f"{self.manufacturer} {self.model}"
        # Extract from scopes
        for s in self.scopes:
            if "/name/" in s:
                return s.split("/name/")[-1]
        return self.xaddr or f"{self.ip}:{self.port}"


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------

def discover_devices(timeout_ms: int = 3000) -> List[ONVIFDeviceInfo]:
    """Discover ONVIF devices on the local network via WS-Discovery.

    Args:
        timeout_ms: Time to wait for discovery responses (ms).

    Returns:
        List of discovered ONVIFDeviceInfo objects.
    """
    devices = []
    try:
        from wsdiscovery import WSDiscovery

        wsd = WSDiscovery()
        wsd.start()
        services = wsd.searchServices(timeout=max(1, timeout_ms // 1000))
        wsd.stop()

        for svc in services:
            xaddrs = svc.getXAddrs()
            if not xaddrs:
                continue

            xaddr = xaddrs[0]

            # Extract IP and port from URL
            ip, port = _parse_xaddr(xaddr)

            try:
                raw_scopes = svc.getScopes()
                scopes = [str(s) for s in (raw_scopes or [])]
            except Exception:
                scopes = []

            device = ONVIFDeviceInfo(
                ip=ip,
                port=port,
                xaddr=xaddr,
                scopes=scopes,
            )

            # Try to extract hardware name from scopes
            for s in scopes:
                if "/hardware/" in s:
                    device.hardware = s.split("/hardware/")[-1]
                if "/name/" in s:
                    pass  # name captured in display_name

            devices.append(device)
            _logger.info(f"Discovered ONVIF device: {xaddr}")

    except ImportError:
        _logger.error("wsdiscovery not installed")
    except Exception as e:
        _logger.error(f"ONVIF discovery error: {e}")

    return devices


def _parse_xaddr(xaddr: str) -> tuple:
    """Parse IP and port from an XAddr URL.

    Args:
        xaddr: URL like http://192.168.1.100:80/onvif/device_service.

    Returns:
        Tuple of (ip, port).
    """
    ip = ""
    port = 80
    try:
        from urllib.parse import urlparse
        parsed = urlparse(xaddr)
        ip = parsed.hostname or ""
        port = parsed.port or 80
    except Exception:
        pass
    return ip, port


# ---------------------------------------------------------------------------
# Connection
# ---------------------------------------------------------------------------

_RTSP_FALLBACK_PATHS = [
    # Standard ONVIF
    "/onvif/media?profile=Profile_1&transportmode=unicast",
    "/onvif/media?profile=Profile_1",
    "/onvif/profile.1",
    "/onvif/media",
    "/onvif/live",
    # Hikvision
    "/Streaming/Channels/101",
    "/Streaming/Channels/1",
    # Dahua
    "/cam/realmonitor?channel=1&subtype=0",
    "/cam/realmonitor?channel=1&subtype=1",
    "/h264/ch1/main/av_stream",
    "/h264/ch1/sub/av_stream",
    # Common
    "/live/ch0",
    "/live/main",
    "/h264",
    "/h264_1",
    "/video",
    "/video1",
    "/video2",
    "/media",
    "/live",
    "/live/sub",
    "/mpeg4/ch1/main/av_stream",
    "/ch1/main/h264",
    "/11",
    "/media/video",
    "/",
]


def _get_fallback_rtsp_urls(ip: str, onvif_port: int) -> list[str]:
    """Generate common RTSP URL fallback patterns for cameras.

    Args:
        ip: Device IP address.
        onvif_port: ONVIF HTTP port (used to guess RTSP port).

    Returns:
        List of candidate RTSP URLs ordered by likelihood.
    """
    # RTSP 几乎总是用 554 或 8554 端口，不要用 ONVIF HTTP 端口
    rtsp_ports = [554, 8554]

    urls: list[str] = []
    for rport in rtsp_ports:
        for path in _RTSP_FALLBACK_PATHS:
            urls.append(f"rtsp://{ip}:{rport}{path}")

    return urls


def _is_auth_error(exception: Exception) -> bool:
    """Check if an exception is caused by authentication failure.

    Args:
        exception: The exception to check.

    Returns:
        True if the exception indicates an auth/authorization error.
    """
    err = str(exception).lower()
    keywords = [
        "not authorized", "unauthorized", "sender not authorized",
        "auth failure", "authentication failed", "access denied",
        "401", "403",
    ]
    return any(kw in err for kw in keywords)


def _is_auth_error_str(error_message: str) -> bool:
    """Check if an error message string indicates authentication failure.

    Args:
        error_message: The error message to check.

    Returns:
        True if the message indicates an auth/authorization error.
    """
    err = error_message.lower()
    keywords = [
        "not authorized", "unauthorized", "sender not authorized",
        "auth failure", "authentication failed", "access denied",
        "401", "403",
    ]
    return any(kw in err for kw in keywords)


class ONVIFConnection:
    """Manages an ONVIF device connection.

    Wraps onvif-zeep to connect to a device, retrieve device info,
    media profiles, and RTSP stream URLs.

    Attributes:
        device_info: Device information (populated after connect).
        is_connected: Whether the connection is active.
    """

    def __init__(self) -> None:
        """Initialize ONVIF connection."""
        self._cam = None
        self._media = None
        self._devicemgmt = None
        self.device_info: Optional[ONVIFDeviceInfo] = None
        self.is_connected = False
        self._last_error: str = ""
        self._working_username: str = ""
        self._working_password: str = ""
        self._logger = get_logger(__name__)

    def get_last_error(self) -> str:
        """Get the last error message.

        Returns:
            Error description string, or empty string if no error.
        """
        return self._last_error

    def get_working_credentials(self) -> tuple[str, str]:
        """Get the credentials that successfully connected.

        Returns:
            Tuple of (username, password) that worked, or ("","") if not connected.
        """
        return (self._working_username, self._working_password)

    @staticmethod
    def _get_wsdl_dir() -> str:
        """Get the ONVIF WSDL directory path.

        In PyInstaller frozen builds, WSDL files are bundled under
        sys._MEIPASS/wsdl/. In normal Python runs, they are in
        site-packages/wsdl/ (installed by onvif-zeep).

        Returns:
            Absolute path to the WSDL directory.
        """
        import sys as _sys
        import os as _os

        # PyInstaller: bundled at _MEIPASS/wsdl/
        if getattr(_sys, 'frozen', False):
            candidate = _os.path.join(_sys._MEIPASS, 'wsdl')  # type: ignore
            if _os.path.isdir(candidate):
                return candidate

        # Normal Python: site-packages/wsdl/ (relative to onvif module)
        import onvif as _onvif
        candidate = _os.path.join(
            _os.path.dirname(_os.path.dirname(_onvif.__file__)), 'wsdl'
        )
        if _os.path.isdir(candidate):
            return candidate

        # Fallback: let ONVIFCamera use its own default
        return ""

    def connect(self, ip: str, port: int = 80,
                username: str = "", password: str = "",
                device_info: Optional[ONVIFDeviceInfo] = None) -> bool:
        """Connect to an ONVIF device.

        Args:
            ip: Device IP address.
            port: Device HTTP port.
            username: ONVIF username.
            password: ONVIF password.
            device_info: Optional pre-populated device info.

        Returns:
            True if connected successfully.
        """
        # Try user-provided credentials first, then fall back to common defaults
        all_credentials: list[tuple[str, str, str]] = []

        # User credentials (first attempt)
        all_credentials.append(("user", username, password))

        # Common defaults to try if user credentials fail
        if username or password:
            # If user entered something, still try defaults as fallback
            for u, p in _COMMON_CREDENTIALS:
                if (u, p) != (username, password):
                    all_credentials.append(("default", u, p))
        else:
            # User entered nothing, try all defaults
            for u, p in _COMMON_CREDENTIALS:
                all_credentials.append(("default", u, p))

        last_error = ""
        for cred_type, try_user, try_pass in all_credentials:
            try:
                from onvif import ONVIFCamera

                self._logger.info(
                    f"Trying credentials [{cred_type}] {try_user}:***@{ip}:{port}"
                )

                wsdl_dir = self._get_wsdl_dir()
                self._cam = ONVIFCamera(ip, port, try_user, try_pass, wsdl_dir)
                self._devicemgmt = self._cam.create_devicemgmt_service()

                # Try to get device info (fails if auth is wrong)
                info = device_info or ONVIFDeviceInfo(ip=ip, port=port)
                try:
                    device_info_resp = self._devicemgmt.GetDeviceInformation()
                    info.manufacturer = getattr(device_info_resp, 'Manufacturer', '')
                    info.model = getattr(device_info_resp, 'Model', '')
                    info.firmware = getattr(device_info_resp, 'FirmwareVersion', '')
                    info.serial = getattr(device_info_resp, 'SerialNumber', '')
                    info.hardware = getattr(device_info_resp, 'HardwareId', '')
                except Exception:
                    # Device info failed - might still work for media
                    pass

                # Try to create media service and get profiles
                try:
                    self._media = self._cam.create_media_service()
                    profiles = self._media.GetProfiles()
                    profile_count = len(profiles) if profiles else 0
                    self._logger.info(
                        f"Credentials OK: {try_user}:*** ({profile_count} profiles)"
                    )
                except Exception as e:
                    if _is_auth_error(e):
                        last_error = str(e)
                        # Clean up and try next credential
                        self._cam = None
                        self._devicemgmt = None
                        continue
                    # Non-auth error (service not available, etc.) - try next
                    self._cam = None
                    self._devicemgmt = None
                    continue

                # Success! Credentials worked
                self._logger.info(
                    f"ONVIF connected to {ip}:{port} with {try_user}:***"
                )

                # If we used a default credential (not the user's input),
                # inform the caller via last_error
                if cred_type == "default":
                    self._last_error = (
                        f"设备 {ip}:{port} 使用默认凭据连接成功 "
                        f"(用户名: {try_user}, 密码: {try_pass})"
                    )

                # Save the working credentials
                self._working_username = try_user
                self._working_password = try_pass

                # Get RTSP URL from profiles
                if profiles:
                    for profile in profiles:
                        try:
                            stream_uri = self._media.GetStreamUri({
                                'StreamSetup': {
                                    'Stream': 'RTP-Unicast',
                                    'Transport': {'Protocol': 'RTSP'}
                                },
                                'ProfileToken': profile.token
                            })
                            uri = stream_uri.Uri
                            if uri:
                                info.rtsp_url = uri
                                self._logger.info(
                                    f"RTSP URL from profile {profile.token}: {uri}"
                                )
                                break
                        except Exception as e:
                            self._logger.debug(
                                f"Profile {profile.token} failed: {e}"
                            )
                            continue

                # Fallback RTSP URL
                if not info.rtsp_url and ip:
                    self._logger.info("Trying fallback RTSP URL patterns...")
                    fallback_urls = _get_fallback_rtsp_urls(ip, port)
                    for fb_url in fallback_urls:
                        info.rtsp_url = fb_url
                        break

                self.device_info = info
                self.is_connected = True
                return True

            except ImportError:
                self._last_error = "onvif-zeep 库未安装"
                self._logger.error("onvif-zeep not installed")
                return False
            except Exception as e:
                last_error = str(e)
                self._logger.debug(
                    f"Credentials [{cred_type}] failed: {e}"
                )
                self._cam = None
                self._devicemgmt = None
                continue

        # All credentials failed
        self._last_error = (
            f"ONVIF 认证失败：无法连接设备 {ip}:{port}，"
            "已尝试常用默认凭据均未成功。"
            if _is_auth_error_str(last_error)
            else f"ONVIF 连接失败: {last_error}"
        )
        self._logger.error(self._last_error)
        return False

    def disconnect(self) -> None:
        """Disconnect from the device."""
        self._cam = None
        self._media = None
        self._devicemgmt = None
        self.is_connected = False
        self._logger.info("ONVIF disconnected")

    def get_rtsp_url(self) -> str:
        """Get the RTSP stream URL.

        Returns:
            RTSP URL string, or empty string if not available.
        """
        if self.device_info:
            return self.device_info.rtsp_url
        return ""
