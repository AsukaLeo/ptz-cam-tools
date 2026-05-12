# Copyright (C) 2026 Asuka
#
# This file is part of PTZ-Cam-Tools.
#
# PTZ-Cam-Tools is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PTZ-Cam-Tools is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PTZ-Cam-Tools. If not, see <https://www.gnu.org/licenses/>.
# SPDX-License-Identifier: GPL-3.0-only

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
