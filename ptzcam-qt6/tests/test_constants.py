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

"""Tests for constants module."""

from app.utils import constants


def test_version_format():
    """Test that version string is properly formatted."""
    assert isinstance(constants.VERSION, str)
    assert len(constants.VERSION.split('.')) == 3


def test_window_constants():
    """Test window dimension constants."""
    assert constants.MIN_WIDTH > 0
    assert constants.MIN_HEIGHT > 0
    assert constants.DEFAULT_WIDTH >= constants.MIN_WIDTH
    assert constants.DEFAULT_HEIGHT >= constants.MIN_HEIGHT


def test_color_constants():
    """Test that color constants are valid hex colors."""
    colors = [
        constants.COLOR_BG_MAIN,
        constants.COLOR_BG_PANEL,
        constants.COLOR_PRIMARY,
        constants.COLOR_DANGER,
    ]
    for color in colors:
        assert color.startswith('#')
        assert len(color) in [4, 7]  # #RGB or #RRGGBB


def test_combo_options():
    """Test that combo box options are lists."""
    options = [
        constants.USB_DEVICES,
        constants.RESOLUTIONS,
        constants.FORMATS,
        constants.FRAME_RATES,
        constants.SERIAL_PORTS,
        constants.BAUD_RATES,
    ]
    for opt in options:
        assert isinstance(opt, list)
        assert len(opt) > 0
