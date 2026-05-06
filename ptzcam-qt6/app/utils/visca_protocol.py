"""VISCA protocol command construction and response parsing.

VISCA (Video System Control Architecture) is a byte-oriented protocol
used to control PTZ cameras over serial (RS-232/422) and IP (TCP/UDP).

Command format:
  [Header] [Category] [Command] [Data...] [Terminator: 0xFF]

Response format:
  ACK:      0x41 0x01 ... 0xFF  (command accepted)
  Completion: 0x51 0x01 ... 0xFF  (command completed)
  Error:    0x60 0x01 ... 0xFF  (command rejected)

Reference: misterhay/VISCA-IP-Controller
"""

from typing import Optional, List, Tuple


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Camera address
VISCA_HEADER = 0x80  # base header for camera #1
VISCA_BROADCAST = 0x88  # broadcast to all cameras
VISCA_TERMINATOR = 0xFF

# Response types
VISCA_ACK = 0x41       # command accepted (4x)
VISCA_COMPLETION = 0x51  # command completed (5x)
VISCA_ERROR = 0x60     # command error (6x)

# Packet type: control command
VISCA_COMMAND = 0x01
# Packet type: inquiry
VISCA_INQUIRY = 0x09

# Pan-tilt constants
PAN_TILT_MAX_SPEED = 0x18  # max speed value (24 decimal)
PAN_TILT_MIN_SPEED = 0x01

# Zoom/Focus speed range
ZOOM_MAX_SPEED = 0x07
FOCUS_MAX_SPEED = 0x07


# ---------------------------------------------------------------------------
# Command building
# ---------------------------------------------------------------------------

def _checksum(packet: bytes) -> bytes:
    """Add VISCA checksum to the end of a packet.

    The checksum is the negated sum of bytes between header and terminator,
    masked to a single byte. Replaces the terminator with checksum + terminator.

    Args:
        packet: Packet bytes (should end with 0xFF).

    Returns:
        Packet with checksum byte inserted before terminator.
    """
    if not packet or packet[-1:] != bytes([VISCA_TERMINATOR]):
        return packet

    # Sum all bytes except the terminator
    total = sum(packet[:-1]) & 0xFF
    cs = (-total) & 0xFF
    return packet[:-1] + bytes([cs, VISCA_TERMINATOR])


def build_pan_tilt(pan_speed: int, tilt_speed: int,
                   pan_direction: int, tilt_direction: int) -> bytes:
    """Build a Pan-tilt Drive command.

    Command: 81 01 06 01 VV WW 0Y 0X FF
      VV = pan speed (0x01~0x18)
      WW = tilt speed (0x01~0x18)
      0Y = tilt direction (03=up, 01=down, 00=stop)
      0X = pan direction (02=right, 01=left, 00=stop)

    Args:
        pan_speed: Pan speed 1~24.
        tilt_speed: Tilt speed 1~24.
        pan_direction: 0=stop, 1=left, 2=right.
        tilt_direction: 0=stop, 1=down, 3=up.

    Returns:
        VISCA command packet bytes.
    """
    packet = bytes([
        VISCA_HEADER | 0x01,  # address
        VISCA_COMMAND,         # command type
        0x06, 0x01,           # Pan-tilt Drive
        min(max(pan_speed, 0), PAN_TILT_MAX_SPEED),
        min(max(tilt_speed, 0), PAN_TILT_MAX_SPEED),
        (tilt_direction & 0x03) | 0x00,
        (pan_direction & 0x03) | 0x00,
        VISCA_TERMINATOR,
    ])
    return _checksum(packet)


def build_pan_tilt_stop() -> bytes:
    """Build a Pan-tilt Stop command.

    Command: 81 01 06 01 00 00 03 03 FF

    Returns:
        VISCA command packet bytes.
    """
    return bytes([VISCA_HEADER | 0x01, VISCA_COMMAND,
                  0x06, 0x01, 0x00, 0x00, 0x03, 0x03, VISCA_TERMINATOR])


def build_home() -> bytes:
    """Build a Pan-tilt Home command.

    Command: 81 01 06 04 FF

    Returns:
        VISCA command packet bytes.
    """
    packet = bytes([VISCA_HEADER | 0x01, VISCA_COMMAND,
                    0x06, 0x04, VISCA_TERMINATOR])
    return _checksum(packet)


def build_zoom(speed: int) -> bytes:
    """Build a Zoom command.

    Positive speed = Tele (zoom in), negative = Wide (zoom out).
    Command: 81 01 04 07 2p FF (Tele: p=2-7, Wide: p=2-7)

    Args:
        speed: Zoom speed. Positive=tele, negative=wide, 0=stop.
               Range: -7 to +7.

    Returns:
        VISCA command packet bytes.
    """
    if speed > 0:
        p = min(speed, ZOOM_MAX_SPEED)  # Tele
    elif speed < 0:
        p = 0x20 | min(-speed, ZOOM_MAX_SPEED)  # Wide
    else:
        p = 0x00  # Stop

    packet = bytes([VISCA_HEADER | 0x01, VISCA_COMMAND,
                    0x04, 0x07, p, VISCA_TERMINATOR])
    return _checksum(packet)


def build_focus(speed: int) -> bytes:
    """Build a Focus command.

    Positive speed = Far, negative = Near.
    Command: 81 01 04 08 3p FF (Far: p=2-7, Near: p=2-7)

    Args:
        speed: Focus speed. Positive=far, negative=near, 0=stop.
               Range: -7 to +7.

    Returns:
        VISCA command packet bytes.
    """
    if speed > 0:
        p = 0x20 | min(speed, FOCUS_MAX_SPEED)  # Far
    elif speed < 0:
        p = min(-speed, FOCUS_MAX_SPEED)  # Near
    else:
        p = 0x00  # Stop

    packet = bytes([VISCA_HEADER | 0x01, VISCA_COMMAND,
                    0x04, 0x08, p, VISCA_TERMINATOR])
    return _checksum(packet)


def build_preset_set(preset_id: int) -> bytes:
    """Build a Preset Set command.

    Command: 81 01 04 3F 01 0p FF

    Args:
        preset_id: Preset number (0~255).

    Returns:
        VISCA command packet bytes.
    """
    packet = bytes([VISCA_HEADER | 0x01, VISCA_COMMAND,
                    0x04, 0x3F, 0x01, preset_id & 0xFF, VISCA_TERMINATOR])
    return _checksum(packet)


def build_preset_recall(preset_id: int) -> bytes:
    """Build a Preset Recall command.

    Command: 81 01 04 3F 02 0p FF

    Args:
        preset_id: Preset number (0~255).

    Returns:
        VISCA command packet bytes.
    """
    packet = bytes([VISCA_HEADER | 0x01, VISCA_COMMAND,
                    0x04, 0x3F, 0x02, preset_id & 0xFF, VISCA_TERMINATOR])
    return _checksum(packet)


# ---------------------------------------------------------------------------
# Response parsing
# ---------------------------------------------------------------------------

class ViscaResponse:
    """Parsed VISCA response."""

    def __init__(self, data: bytes):
        self.raw = data
        self._parse(data)

    def _parse(self, data: bytes) -> None:
        """Parse raw response bytes.

        Sets:
            is_ack: True if ACK response.
            is_completion: True if Completion response.
            is_error: True if Error response.
            socket_num: Socket number from response.
            error_code: Error code (if is_error).
        """
        self.is_ack = False
        self.is_completion = False
        self.is_error = False
        self.socket_num = 0
        self.error_code = 0
        self.inquiry_data: Optional[bytes] = None

        if not data or len(data) < 3:
            return

        msg_type = data[0] & 0xF0

        if msg_type == VISCA_ACK:
            self.is_ack = True
            self.socket_num = data[0] & 0x03
        elif msg_type == VISCA_COMPLETION:
            self.is_completion = True
            self.socket_num = data[0] & 0x03
            # Data after socket byte (skip terminator)
            if len(data) > 3:
                self.inquiry_data = data[2:-1]
        elif msg_type == VISCA_ERROR:
            self.is_error = True
            if len(data) >= 3:
                self.error_code = data[2]

    @staticmethod
    def parse(data: bytes) -> 'ViscaResponse':
        """Parse VISCA response bytes.

        Args:
            data: Raw response bytes from camera.

        Returns:
            ViscaResponse object.
        """
        return ViscaResponse(data)


# ---------------------------------------------------------------------------
# Command execution helpers
# ---------------------------------------------------------------------------

def pack_command(cmd_bytes: bytes) -> bytes:
    """Pack a VISCA command for transmission.

    For IP transport, VISCA commands may need additional framing.
    This function adds the terminator if missing.

    Args:
        cmd_bytes: Raw command bytes.

    Returns:
        Properly terminated command bytes.
    """
    if cmd_bytes and cmd_bytes[-1] != VISCA_TERMINATOR:
        return cmd_bytes + bytes([VISCA_TERMINATOR])
    return cmd_bytes
