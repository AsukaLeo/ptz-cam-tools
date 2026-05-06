"""VISCA camera controller.

Provides a high-level interface for PTZ camera control via the VISCA
protocol. Manages transport connections, command execution, and exposes
a simple API for PTZ operations.

Usage:
    controller = ViscaController()
    controller.connect_serial('COM1', 9600)
    controller.pan_tilt(10, 0)    # pan right
    controller.zoom(5)             # zoom in
    controller.preset_recall(1)   # go to preset 1
    controller.disconnect()
"""

from typing import Optional, Callable

from app.utils.visca_protocol import (
    build_pan_tilt, build_pan_tilt_stop, build_home,
    build_zoom, build_focus,
    build_preset_set, build_preset_recall,
    ViscaResponse,
)
from app.utils.visca_transport import (
    ViscaTransport, SerialTransport, UdpTransport, TcpTransport,
)
from app.utils.logger import get_logger


class ViscaController:
    """High-level VISCA camera controller.

    Attributes:
        on_status_update: Callback for status messages.
        is_connected: Whether the controller has an active transport.
    """

    # Default speeds
    PAN_TILT_SPEED = 12   # medium speed (1~24)
    ZOOM_SPEED = 3        # medium zoom speed (1~7)
    FOCUS_SPEED = 3       # medium focus speed (1~7)

    def __init__(self) -> None:
        """Initialize the controller."""
        self._transport: Optional[ViscaTransport] = None
        self._transport_type: str = ""
        self._logger = get_logger(__name__)
        self.on_status_update: Optional[Callable[[str], None]] = None
        self.is_connected = False

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------

    def connect_serial(self, port: str, baud: int = 9600,
                       data_bits: int = 8, parity: str = 'N',
                       stop_bits: int = 1) -> bool:
        """Connect via serial port.

        Args:
            port: Port name (e.g. 'COM1').
            baud: Baud rate.
            data_bits: Data bits.
            parity: Parity.
            stop_bits: Stop bits.

        Returns:
            True if connected.
        """
        self.disconnect()
        transport = SerialTransport(port, baud, data_bits, parity, stop_bits)
        if not transport.open():
            self._notify(f"串口打开失败: {port}")
            return False

        self._transport = transport
        self._transport_type = "serial"
        self.is_connected = True
        self._notify(f"VISCA 串口已连接: {port} @ {baud}")
        return True

    def connect_udp(self, host: str, port: int = 52381) -> bool:
        """Connect via UDP.

        Args:
            host: Camera IP address.
            port: Camera UDP port.

        Returns:
            True if connected.
        """
        self.disconnect()
        transport = UdpTransport(host, port)
        if not transport.open():
            self._notify(f"UDP 连接失败: {host}:{port}")
            return False

        self._transport = transport
        self._transport_type = "udp"
        self.is_connected = True
        self._notify(f"VISCA UDP 已连接: {host}:{port}")
        return True

    def connect_tcp(self, host: str, port: int = 5678) -> bool:
        """Connect via TCP.

        Args:
            host: Camera IP address.
            port: Camera TCP port.

        Returns:
            True if connected.
        """
        self.disconnect()
        transport = TcpTransport(host, port)
        if not transport.open():
            self._notify(f"TCP 连接失败: {host}:{port}")
            return False

        self._transport = transport
        self._transport_type = "tcp"
        self.is_connected = True
        self._notify(f"VISCA TCP 已连接: {host}:{port}")
        return True

    def disconnect(self) -> None:
        """Disconnect and close transport."""
        if self._transport:
            self._transport.close()
            self._transport = None
        self.is_connected = False
        self._transport_type = ""
        self._notify("VISCA 已断开")

    # ------------------------------------------------------------------
    # PTZ control
    # ------------------------------------------------------------------

    def pan_tilt(self, pan_speed: int = 0, tilt_speed: int = 0,
                 pan_dir: int = 0, tilt_dir: int = 0) -> bool:
        """Pan/tilt control.

        Args:
            pan_speed: Pan speed (1~24). 0 uses default.
            tilt_speed: Tilt speed (1~24). 0 uses default.
            pan_dir: 0=stop, 1=left, 2=right.
            tilt_dir: 0=stop, 1=down, 3=up.

        Returns:
            True if command sent successfully.
        """
        if not self._ensure_connected():
            return False

        cmd = build_pan_tilt(
            pan_speed or self.PAN_TILT_SPEED,
            tilt_speed or self.PAN_TILT_SPEED,
            pan_dir, tilt_dir,
        )
        return self._send(cmd)

    def stop(self) -> bool:
        """Stop all pan/tilt movement.

        Returns:
            True if command sent.
        """
        return self._send(build_pan_tilt_stop())

    def home(self) -> bool:
        """Go to home position.

        Returns:
            True if command sent.
        """
        if not self._ensure_connected():
            return False
        self._notify("PTZ Home")
        return self._send(build_home())

    def zoom(self, speed: int = 0) -> bool:
        """Zoom control.

        Args:
            speed: Positive=tele(in), negative=wide(out), 0=stop.
                   Default: +3 (tele).

        Returns:
            True if command sent.
        """
        if not self._ensure_connected():
            return False
        if speed == 0:
            speed = self.ZOOM_SPEED
        return self._send(build_zoom(speed))

    def focus(self, speed: int = 0) -> bool:
        """Focus control.

        Args:
            speed: Positive=far, negative=near, 0=stop.
                   Default: +3 (far).

        Returns:
            True if command sent.
        """
        if not self._ensure_connected():
            return False
        if speed == 0:
            speed = self.FOCUS_SPEED
        return self._send(build_focus(speed))

    # ------------------------------------------------------------------
    # Presets
    # ------------------------------------------------------------------

    def preset_set(self, preset_id: int) -> bool:
        """Save current position as a preset.

        Args:
            preset_id: Preset number (0~255).

        Returns:
            True if command sent.
        """
        if not self._ensure_connected():
            return False
        self._notify(f"保存预设位 {preset_id}")
        return self._send(build_preset_set(preset_id))

    def preset_recall(self, preset_id: int) -> bool:
        """Recall a preset position.

        Args:
            preset_id: Preset number (0~255).

        Returns:
            True if command sent.
        """
        if not self._ensure_connected():
            return False
        self._notify(f"调用预设位 {preset_id}")
        return self._send(build_preset_recall(preset_id))

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _ensure_connected(self) -> bool:
        """Check if transport is connected and log warning if not.

        Returns:
            True if connected.
        """
        if not self.is_connected or not self._transport:
            self._notify("VISCA 未连接")
            return False
        return True

    def _send(self, cmd: bytes) -> bool:
        """Send a VISCA command and check response.

        Args:
            cmd: Command bytes.

        Returns:
            True if command was sent (response checked non-blocking).
        """
        try:
            self._transport.send(cmd)
            return True
        except Exception as e:
            self._logger.error(f"Command send failed: {e}")
            self._notify(f"命令发送失败: {e}")
            return False

    def _send_with_response(self, cmd: bytes) -> Optional[ViscaResponse]:
        """Send a command and wait for response.

        Args:
            cmd: Command bytes.

        Returns:
            ViscaResponse, or None on failure.
        """
        if not self._transport:
            return None
        resp_bytes = self._transport.send_command(cmd)
        if resp_bytes:
            return ViscaResponse.parse(resp_bytes)
        return None

    def _notify(self, message: str) -> None:
        """Send status message via callback.

        Args:
            message: Status message.
        """
        if self.on_status_update:
            self.on_status_update(message)
