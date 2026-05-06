"""ONVIF device discovery, connection and control module.

Provides ONVIF device discovery via WS-Discovery, device connection
using onvif-zeep, RTSP stream URL retrieval, and basic device info.
"""

from dataclasses import dataclass, field
from typing import Optional, List
import time

from app.utils.logger import get_logger

_logger = get_logger(__name__)


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
        self._logger = get_logger(__name__)

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
        try:
            from onvif import ONVIFCamera

            self._logger.info(f"Connecting to ONVIF device: {ip}:{port}")

            self._cam = ONVIFCamera(ip, port, username, password)
            self._devicemgmt = self._cam.create_devicemgmt_service()

            # Get device info
            info = self.device_info or ONVIFDeviceInfo(ip=ip, port=port)
            try:
                device_info_resp = self._devicemgmt.GetDeviceInformation()
                info.manufacturer = getattr(device_info_resp, 'Manufacturer', '')
                info.model = getattr(device_info_resp, 'Model', '')
                info.firmware = getattr(device_info_resp, 'FirmwareVersion', '')
                info.serial = getattr(device_info_resp, 'SerialNumber', '')
                info.hardware = getattr(device_info_resp, 'HardwareId', '')
            except Exception as e:
                self._logger.warning(f"Could not get device info: {e}")

            # Create media service and get RTSP URL
            try:
                self._media = self._cam.create_media_service()
                profiles = self._media.GetProfiles()
                if profiles:
                    profile_token = profiles[0].token
                    stream_uri = self._media.GetStreamUri({
                        'StreamSetup': {
                            'Stream': 'RTP-Unicast',
                            'Transport': {'Protocol': 'RTSP'}
                        },
                        'ProfileToken': profile_token
                    })
                    info.rtsp_url = stream_uri.Uri
                    self._logger.info(f"RTSP URL: {info.rtsp_url}")
            except Exception as e:
                self._logger.warning(f"Could not get RTSP URL: {e}")

            self.device_info = info
            self.is_connected = True
            return True

        except ImportError:
            self._logger.error("onvif-zeep not installed")
            return False
        except Exception as e:
            self._logger.error(f"ONVIF connection error: {e}")
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
