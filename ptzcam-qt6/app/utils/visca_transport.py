"""VISCA transport layer.

Provides an abstract base class for VISCA communication transports
and concrete implementations for Serial (pyserial), UDP, and TCP.

Design follows the Strategy pattern, allowing the ViscaController to
switch between transports without changing the protocol logic.

Reference: misterhay/VISCA-IP-Controller
"""

from abc import ABC, abstractmethod
from typing import Optional
import socket
import time

from app.utils.logger import get_logger

_logger = get_logger(__name__)


class ViscaTransport(ABC):
    """Abstract base class for VISCA transports.

    Provides a unified interface for sending VISCA commands and
    receiving responses, regardless of the underlying transport.
    """

    @abstractmethod
    def send(self, data: bytes) -> None:
        """Send VISCA command data.

        Args:
            data: Raw command bytes to send.
        """
        ...

    @abstractmethod
    def receive(self, timeout_ms: int = 1000) -> Optional[bytes]:
        """Receive a VISCA response.

        Args:
            timeout_ms: Maximum time to wait for a response (ms).

        Returns:
            Response bytes, or None if timeout/error.
        """
        ...

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if the transport is connected.

        Returns:
            True if connected and ready.
        """
        ...

    @abstractmethod
    def close(self) -> None:
        """Close the transport and release resources."""
        ...

    def send_command(self, data: bytes,
                     response_timeout_ms: int = 2000) -> Optional[bytes]:
        """Send a VISCA command and wait for response.

        Args:
            data: Command bytes to send.
            response_timeout_ms: Timeout for response.

        Returns:
            Response bytes, or None on failure.
        """
        if not self.is_connected():
            _logger.error("Transport not connected")
            return None

        try:
            self.send(data)
            return self.receive(response_timeout_ms)
        except Exception as e:
            _logger.error(f"Send/receive error: {e}")
            return None


class SerialTransport(ViscaTransport):
    """VISCA transport over serial (RS-232/422).

    Uses pyserial for serial port communication.
    Typical configuration: 9600 baud, 8N1.
    """

    def __init__(self, port: str, baud: int = 9600,
                 data_bits: int = 8, parity: str = 'N',
                 stop_bits: int = 1) -> None:
        """Initialize serial transport.

        Args:
            port: Serial port name (e.g. 'COM1').
            baud: Baud rate.
            data_bits: Data bits (5, 6, 7, 8).
            parity: Parity ('N', 'E', 'O', 'M', 'S').
            stop_bits: Stop bits (1, 1.5, 2).
        """
        self._port = port
        self._baud = baud
        self._data_bits = data_bits
        self._parity = parity
        self._stop_bits = stop_bits
        self._serial = None
        self._logger = get_logger(__name__)

    def open(self) -> bool:
        """Open the serial port.

        Returns:
            True if successful.
        """
        try:
            import serial
            parity_map = {
                'N': serial.PARITY_NONE,
                'E': serial.PARITY_EVEN,
                'O': serial.PARITY_ODD,
                'M': serial.PARITY_MARK,
                'S': serial.PARITY_SPACE,
            }
            self._serial = serial.Serial(
                port=self._port,
                baudrate=self._baud,
                bytesize=self._data_bits,
                parity=parity_map.get(self._parity.upper(), serial.PARITY_NONE),
                stopbits=float(self._stop_bits),
                timeout=0.1,
            )
            self._logger.info(f"Serial port opened: {self._port} @ {self._baud}")
            return True
        except ImportError:
            self._logger.error("pyserial not installed")
            return False
        except Exception as e:
            self._logger.error(f"Failed to open serial port: {e}")
            return False

    def send(self, data: bytes) -> None:
        """Send data over serial.

        Args:
            data: Bytes to send.
        """
        if self._serial and self._serial.is_open:
            self._serial.write(data)
            self._serial.flush()

    def receive(self, timeout_ms: int = 1000) -> Optional[bytes]:
        """Read response from serial port.

        Args:
            timeout_ms: Maximum time to wait (ms).

        Returns:
            Response bytes ending with 0xFF, or None.
        """
        if not self._serial or not self._serial.is_open:
            return None

        deadline = time.perf_counter() + (timeout_ms / 1000)
        buf = bytearray()

        while time.perf_counter() < deadline:
            if self._serial.in_waiting:
                byte = self._serial.read(1)
                if byte:
                    buf.extend(byte)
                    if byte[0] == 0xFF:
                        return bytes(buf)
            else:
                time.sleep(0.01)

        return bytes(buf) if buf else None

    def is_connected(self) -> bool:
        return self._serial is not None and self._serial.is_open

    def close(self) -> None:
        if self._serial and self._serial.is_open:
            try:
                self._serial.close()
                self._logger.info("Serial port closed")
            except Exception as e:
                self._logger.error(f"Error closing serial: {e}")
            self._serial = None


class UdpTransport(ViscaTransport):
    """VISCA transport over UDP.

    Default port: 52381
    """

    def __init__(self, host: str, port: int = 52381) -> None:
        """Initialize UDP transport.

        Args:
            host: Camera IP address.
            port: Camera UDP port.
        """
        self._host = host
        self._port = port
        self._sock: Optional[socket.socket] = None
        self._logger = get_logger(__name__)

    def open(self) -> bool:
        """Open UDP socket.

        Returns:
            True if successful.
        """
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._sock.settimeout(0.5)
            self._logger.info(f"UDP transport opened: {self._host}:{self._port}")
            return True
        except Exception as e:
            self._logger.error(f"Failed to create UDP socket: {e}")
            return False

    def send(self, data: bytes) -> None:
        """Send data over UDP.

        Args:
            data: Bytes to send.
        """
        if self._sock:
            self._sock.sendto(data, (self._host, self._port))

    def receive(self, timeout_ms: int = 1000) -> Optional[bytes]:
        """Receive response from UDP socket.

        Args:
            timeout_ms: Maximum time to wait (ms).

        Returns:
            Response bytes, or None.
        """
        if not self._sock:
            return None

        self._sock.settimeout(timeout_ms / 1000)
        try:
            data, _ = self._sock.recvfrom(1024)
            return data
        except socket.timeout:
            return None
        except Exception as e:
            self._logger.error(f"UDP receive error: {e}")
            return None

    def is_connected(self) -> bool:
        return self._sock is not None

    def close(self) -> None:
        if self._sock:
            try:
                self._sock.close()
                self._logger.info("UDP transport closed")
            except Exception:
                pass
            self._sock = None


class TcpTransport(ViscaTransport):
    """VISCA transport over TCP.

    Default port: 5678
    """

    def __init__(self, host: str, port: int = 5678) -> None:
        """Initialize TCP transport.

        Args:
            host: Camera IP address.
            port: Camera TCP port.
        """
        self._host = host
        self._port = port
        self._sock: Optional[socket.socket] = None
        self._logger = get_logger(__name__)

    def open(self) -> bool:
        """Open TCP connection.

        Returns:
            True if successful.
        """
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._sock.settimeout(3.0)
            self._sock.connect((self._host, self._port))
            self._sock.settimeout(0.5)
            self._logger.info(f"TCP connected: {self._host}:{self._port}")
            return True
        except Exception as e:
            self._logger.error(f"Failed to connect TCP: {e}")
            return False

    def send(self, data: bytes) -> None:
        """Send data over TCP.

        Args:
            data: Bytes to send.
        """
        if self._sock:
            try:
                self._sock.sendall(data)
            except Exception as e:
                self._logger.error(f"TCP send error: {e}")

    def receive(self, timeout_ms: int = 1000) -> Optional[bytes]:
        """Receive response from TCP socket.

        Args:
            timeout_ms: Maximum time to wait (ms).

        Returns:
            Response bytes, or None.
        """
        if not self._sock:
            return None

        self._sock.settimeout(timeout_ms / 1000)
        try:
            data = self._sock.recv(1024)
            return data
        except socket.timeout:
            return None
        except Exception as e:
            self._logger.error(f"TCP receive error: {e}")
            return None

    def is_connected(self) -> bool:
        return self._sock is not None

    def close(self) -> None:
        if self._sock:
            try:
                self._sock.close()
                self._logger.info("TCP transport closed")
            except Exception:
                pass
            self._sock = None
