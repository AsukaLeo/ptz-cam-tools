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
