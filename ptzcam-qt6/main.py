#!/usr/bin/env python3
"""PTZ-Cam-Tools - Video camera control application.

This is the main entry point for the PTZ-Cam-Tools application.
It provides a GUI for controlling PTZ cameras via USB, RTSP, NDI, and ONVIF protocols.

Usage:
    python main.py           # Normal mode
    python main.py --debug   # Debug mode (verbose logging)
"""

import sys
import os
import argparse

# Add the project root to the path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _setup_bundled_paths() -> None:
    """Add bundled DLL directories to system PATH for PyInstaller frozen builds.

    When running from a PyInstaller single-file EXE, bundled data files
    (FFmpeg DLLs, etc.) are extracted to sys._MEIPASS. They must be on
    the system PATH for OpenCV's FFmpeg backend to load them.
    """
    if not getattr(sys, 'frozen', False):
        return  # Not a PyInstaller build

    meipass = sys._MEIPASS  # type: ignore[attr-defined]

    # FFmpeg DLLs (for OpenCV RTSP decoding)
    ffmpeg_dir = os.path.join(meipass, 'thirdparty', 'ffmpeg', 'bin')
    if os.path.isdir(ffmpeg_dir):
        os.environ['PATH'] = ffmpeg_dir + os.pathsep + os.environ['PATH']

    # Also add the base _MEIPASS dir (for opencv_videoio_ffmpeg*.dll etc.)
    os.environ['PATH'] = meipass + os.pathsep + os.environ['PATH']


def _setup_zeep_cache() -> None:
    """Pre-configure zeep WSDL cache for PyInstaller frozen builds.

    onvif-zeep downloads WSDL files at runtime via the zeep SOAP library.
    Zeep's default SQLite cache may fail in a frozen EXE due to path
    issues. Ensure the cache dir exists in a writable user location.
    """
    if not getattr(sys, 'frozen', False):
        return

    cache_base = os.path.join(
        os.environ.get('LOCALAPPDATA',
                       os.environ.get('APPDATA',
                                      os.path.expanduser('~'))),
        'zeep',
    )
    os.makedirs(os.path.join(cache_base, 'Cache'), exist_ok=True)
    os.environ['ZEEP_CACHE_DIR'] = cache_base


# Run at module load time, before any OpenCV/FFmpeg imports
_setup_bundled_paths()
_setup_zeep_cache()

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from app.main_window import MainWindow
from app.styles.theme import get_global_stylesheet
from app.utils.logger import setup_logging, get_logger


def parse_args() -> argparse.Namespace:
    """Parse command line arguments.
    
    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description="PTZ-Cam-Tools - Video camera control application"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode with verbose logging"
    )
    parser.add_argument(
        "--no-log-file",
        action="store_true",
        help="Disable file logging (console only)"
    )
    return parser.parse_args()


def main() -> int:
    """Main application entry point.
    
    Returns:
        Application exit code.
    """
    # Parse arguments
    args = parse_args()
    
    # Setup logging
    setup_logging(
        debug=args.debug,
        log_to_file=not args.no_log_file
    )
    logger = get_logger("main")
    
    logger.info("=" * 50)
    logger.info("PTZ-Cam-Tools Starting...")
    logger.info(f"Debug mode: {args.debug}")
    logger.info("=" * 50)
    
    # DPI strategy must be set before creating QApplication
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    logger.debug("DPI policy configured")
    
    # Create application
    app = QApplication(sys.argv)
    logger.debug("QApplication created")
    
    # Get asset paths
    arrow_svg = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "arrow_down.svg"
    ).replace("\\", "/")
    bg_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "assets", "Background.png"
    ).replace("\\", "/")
    
    # -- Adaptive app icon: choose dark/light variant based on system color scheme --
    def _get_icon_path(scheme):
        """Return the appropriate icon file path for the given color scheme."""
        asset_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
        icon_name = "app_dark.ico" if scheme == Qt.ColorScheme.Dark else "app_light.ico"
        return os.path.join(asset_dir, icon_name).replace("\\", "/")
    
    _current_scheme = app.styleHints().colorScheme()
    app.setWindowIcon(QIcon(_get_icon_path(_current_scheme)))
    logger.debug(f"App icon set for color scheme: {_current_scheme}")
    
    # React to system theme changes at runtime
    def _on_color_scheme_changed(scheme):
        app.setWindowIcon(QIcon(_get_icon_path(scheme)))
        logger.info(f"App icon switched for color scheme: {scheme}")
    
    app.styleHints().colorSchemeChanged.connect(_on_color_scheme_changed)
    
    # Apply global stylesheet
    app.setStyleSheet(get_global_stylesheet(arrow_svg, bg_path))
    logger.debug("Stylesheet applied")
    
    # Create and show main window
    window = MainWindow()
    window.show()
    logger.info("Main window displayed")
    
    # Run event loop
    logger.info("Entering event loop...")
    return sys.exit(app.exec())


if __name__ == "__main__":
    sys.exit(main())
