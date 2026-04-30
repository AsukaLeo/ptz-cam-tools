"""Logging configuration for PTZ-Cam-Tools.

Provides both console and file logging with configurable levels.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


# Default log format
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Log directory
LOG_DIR = Path(__file__).parent.parent.parent / "logs"


def setup_logging(
    debug: bool = False,
    log_to_file: bool = True,
    log_dir: Optional[Path] = None
) -> logging.Logger:
    """Setup application logging.
    
    Args:
        debug: Enable debug level logging if True, otherwise INFO.
        log_to_file: Also write logs to file if True.
        log_dir: Custom log directory. Defaults to project/logs.
        
    Returns:
        Root logger instance.
    """
    # Determine log level
    level = logging.DEBUG if debug else logging.INFO
    
    # Create root logger
    root_logger = logging.getLogger("ptzcam")
    root_logger.setLevel(level)
    
    # Clear existing handlers
    root_logger.handlers = []
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler
    if log_to_file:
        log_path = _get_log_file_path(log_dir)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setLevel(level)
        file_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
        
        root_logger.info(f"Logging to file: {log_path}")
    
    root_logger.info(f"Logging level: {'DEBUG' if debug else 'INFO'}")
    
    return root_logger


def _get_log_file_path(log_dir: Optional[Path] = None) -> Path:
    """Generate log file path with timestamp.
    
    Args:
        log_dir: Custom log directory.
        
    Returns:
        Path to log file.
    """
    directory = log_dir or LOG_DIR
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return directory / f"ptzcam_{timestamp}.log"


def get_logger(name: str) -> logging.Logger:
    """Get a named logger under the ptzcam namespace.
    
    Args:
        name: Logger name, typically __name__.
        
    Returns:
        Logger instance.
    """
    return logging.getLogger(f"ptzcam.{name}")
