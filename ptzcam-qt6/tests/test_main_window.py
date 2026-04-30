"""Tests for MainWindow."""

import pytest
from PySide6.QtWidgets import QApplication

from app.main_window import MainWindow


@pytest.fixture
def main_window(qtbot):
    """Create a MainWindow instance for testing."""
    window = MainWindow()
    qtbot.addWidget(window)
    return window


def test_window_title(main_window):
    """Test that window has correct title."""
    assert main_window.windowTitle() == "PTZ-Cam-Tools"


def test_window_minimum_size(main_window):
    """Test that window has correct minimum size."""
    from app.utils.constants import MIN_WIDTH, MIN_HEIGHT
    min_size = main_window.minimumSize()
    assert min_size.width() == MIN_WIDTH
    assert min_size.height() == MIN_HEIGHT


def test_status_bar_exists(main_window):
    """Test that status bar is created."""
    assert main_window.statusBar() is not None


def test_tab_widget_exists(main_window):
    """Test that tab widget is created."""
    assert main_window.tab_widget is not None
    assert main_window.tab_widget.count() == 5


def test_preview_frames_created(main_window):
    """Test that preview frames are created."""
    assert len(main_window._preview_frames) == 4  # USB, RTSP, NDI, ONVIF


def test_ptz_panel_exists(main_window):
    """Test that PTZ panel is created."""
    assert main_window._ptz_panel is not None


def test_visca_panel_exists(main_window):
    """Test that VISCA panel is created."""
    assert main_window._visca_panel is not None


def test_update_status(main_window):
    """Test status update functionality."""
    main_window.update_status("Test Status")
    assert "Test Status" in main_window.status_label.text()
