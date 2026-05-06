"""Application constants."""

# Window constants
ASPECT_W: int = 16
ASPECT_H: int = 10
MIN_WIDTH: int = 800
MIN_HEIGHT: int = 500
DEFAULT_WIDTH: int = 960
DEFAULT_HEIGHT: int = 850

# Version info
VERSION: str = "0.20.506"
VERSION_STRING: str = f"V {VERSION}_7c94eda By Asuka"

# Colors
COLOR_BG_MAIN: str = "#fff"
COLOR_BG_PANEL: str = "#f8f8f8"
COLOR_BG_CARD: str = "#f0f2f5"
COLOR_BORDER_LIGHT: str = "#e0e0e0"
COLOR_BORDER_STD: str = "#ccc"
COLOR_BORDER_INPUT: str = "#aaa"
COLOR_PRIMARY: str = "#0078d4"
COLOR_PRIMARY_HOVER: str = "#0066b8"
COLOR_PRIMARY_PRESSED: str = "#005a9e"
COLOR_DANGER: str = "#c42b1c"
COLOR_DANGER_HOVER: str = "#a52010"
COLOR_DANGER_PRESSED: str = "#8a1a0d"
COLOR_TEXT_MAIN: str = "#333"
COLOR_TEXT_SECONDARY: str = "#555"
COLOR_TEXT_LABEL: str = "#666"
COLOR_PREVIEW_BG: str = "#1a1a1a"
COLOR_VIDEO_FRAME_BG: str = "#0a0a0a"

# UI strings
STATUS_READY: str = "就绪"
STATUS_CONNECTING: str = "连接中..."
STATUS_DISCONNECTED: str = "已断开"

# Tab names
TAB_USB: str = "USB"
TAB_RTSP: str = "RTSP"
TAB_NDI: str = "NDI"
TAB_ONVIF: str = "ONVIF"
TAB_SETTINGS: str = "设置"

# PTZ directions
PTZ_UP: str = "上"
PTZ_DOWN: str = "下"
PTZ_LEFT: str = "左"
PTZ_RIGHT: str = "右"
PTZ_STOP: str = "停止"
PTZ_HOME: str = "Home"

# VISCA
VISCA_SERIAL_OPENED: str = "VISCA 串口已开启"
VISCA_NETWORK_CONNECTED: str = "VISCA 网络已连接"

# Video preview
PREVIEW_PLACEHOLDER_TEXT: str = "视频预览区"
PREVIEW_MIN_WIDTH: int = 160
PREVIEW_MIN_HEIGHT: int = 90

# ComboBox options
USB_DEVICES: list[str] = ["USB Camera (1)", "USB Camera (2)"]
RESOLUTIONS: list[str] = ["1920 x 1080", "1280 x 720", "640 x 480"]
FORMATS: list[str] = ["YUY2", "MJPEG", "H264"]
FRAME_RATES: list[str] = ["30 fps", "25 fps", "15 fps"]
SERIAL_PORTS: list[str] = ["COM1", "COM2", "COM3", "COM4"]
BAUD_RATES: list[str] = ["9600", "19200", "38400", "57600", "115200"]
DATA_BITS: list[str] = ["8", "7", "6", "5"]
PARITY_BITS: list[str] = ["None", "Odd", "Even", "Mark", "Space"]
STOP_BITS: list[str] = ["1", "1.5", "2"]
NETWORK_PROTOCOLS: list[str] = ["TCP", "UDP"]
LANGUAGES: list[str] = ["中文", "English"]
