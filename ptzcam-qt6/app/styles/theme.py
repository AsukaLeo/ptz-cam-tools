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

"""Application stylesheet definitions."""

import os

from app.utils.constants import (
    COLOR_BG_MAIN,
    COLOR_BG_PANEL,
    COLOR_BG_CARD,
    COLOR_BORDER_LIGHT,
    COLOR_BORDER_STD,
    COLOR_BORDER_INPUT,
    COLOR_PRIMARY,
    COLOR_PRIMARY_HOVER,
    COLOR_PRIMARY_PRESSED,
    COLOR_DANGER,
    COLOR_DANGER_HOVER,
    COLOR_DANGER_PRESSED,
    COLOR_TEXT_MAIN,
    COLOR_TEXT_SECONDARY,
    COLOR_TEXT_LABEL,
    COLOR_PREVIEW_BG,
    COLOR_VIDEO_FRAME_BG,
)


# ---------------------------------------------------------------------------
# Global stylesheet (assembled from themed sections)
# ---------------------------------------------------------------------------

def get_global_stylesheet(arrow_svg_path: str, bg_image_path: str = "") -> str:
    """Generate the global application stylesheet.

    Args:
        arrow_svg_path: Path to the ComboBox dropdown arrow SVG file.
        bg_image_path: Optional path to background image.

    Returns:
        Complete stylesheet string.
    """
    return "".join([
        _bg_section(bg_image_path),
        _base_widget_section(),
        _combo_box_section(arrow_svg_path),
        _status_bar_section(),
        _tab_section(),
        _size_grip_section(),
    ])


def _bg_section(bg_image_path: str) -> str:
    """Main window background (image fill or solid color)."""
    if bg_image_path and os.path.exists(bg_image_path):
        return f"""
        QMainWindow {{
            border-image: url({bg_image_path}) 0 0 0 0 stretch stretch;
        }}
        """
    return f"""
        QMainWindow {{ background-color: {COLOR_BG_MAIN}; }}
        """
    return f"""
        QMainWindow {{ background-color: {COLOR_BG_MAIN}; }}
        """


def _base_widget_section() -> str:
    """Base widgets: QWidget, QPushButton, QLabel, QLineEdit."""
    return f"""
        QWidget {{ color: {COLOR_TEXT_MAIN}; background: transparent; }}
        QPushButton {{ color: {COLOR_TEXT_MAIN}; background-color: #f5f5f5; }}
        QPushButton:disabled {{ color: #bbb; background-color: #e8e8e8; border: 1px solid #ddd; }}
        QLabel {{ color: {COLOR_TEXT_MAIN}; background-color: transparent; }}
        QLineEdit {{
            color: {COLOR_TEXT_MAIN}; background-color: {COLOR_BG_MAIN};
            border: 1px solid {COLOR_BORDER_INPUT}; border-radius: 6px;
            padding: 4px 8px;
        }}
        QLineEdit:disabled {{
            color: #aaa; background-color: #e8e8e8; border: 1px solid #ddd;
        }}
        QLineEdit:focus {{
            border-color: {COLOR_PRIMARY};
        }}
        """


def _combo_box_section(arrow_svg_path: str) -> str:
    """QComboBox with SVG arrow and scrollable dropdown."""
    return f"""
        QComboBox {{
            color: {COLOR_TEXT_MAIN}; background-color: {COLOR_BG_MAIN};
            border: 1px solid {COLOR_BORDER_INPUT}; border-radius: 6px;
            padding: 4px 28px 4px 8px;
        }}
        QComboBox:disabled {{ color: #bbb; background-color: #f0f0f0; border: 1px solid #ddd; }}
        QComboBox::drop-down {{
            border: none; width: 24px;
            subcontrol-origin: padding;
            subcontrol-position: top right;
        }}
        QComboBox::down-arrow {{
            image: url({arrow_svg_path});
            width: 12px; height: 8px;
        }}
        QComboBox QAbstractItemView {{
            color: {COLOR_TEXT_MAIN}; background-color: {COLOR_BG_MAIN}; 
            border: 1px solid {COLOR_BORDER_INPUT}; border-radius: 6px;
            selection-background-color: {COLOR_PRIMARY}; selection-color: {COLOR_BG_MAIN};
            outline: none;
        }}
        QComboBox QAbstractItemView::item {{
            padding: 4px 8px; min-height: 24px;
        }}
        QComboBox QAbstractItemView::item:hover {{
            background-color: #e8e8e8;
        }}
        QComboBox QAbstractItemView QScrollBar:vertical {{
            width: 8px; background: transparent; margin: 0;
        }}
        QComboBox QAbstractItemView QScrollBar::handle:vertical {{
            background: #ccc; border-radius: 4px; min-height: 30px;
        }}
        QComboBox QAbstractItemView QScrollBar::handle:vertical:hover {{
            background: #aaa;
        }}
        QComboBox QAbstractItemView QScrollBar::add-line:vertical,
        QComboBox QAbstractItemView QScrollBar::sub-line:vertical {{ height: 0px; }}
        QComboBox QAbstractItemView QScrollBar::add-page:vertical,
        QComboBox QAbstractItemView QScrollBar::sub-page:vertical {{ background: none; }}
        """


def _status_bar_section() -> str:
    """QStatusBar and QListWidget styling."""
    return f"""
        QStatusBar {{ color: {COLOR_TEXT_MAIN}; background-color: #f0f0f0; }}
        QStatusBar QLabel {{ color: {COLOR_TEXT_SECONDARY}; background-color: transparent; }}
        QListWidget {{
            color: {COLOR_TEXT_LABEL}; background-color: #fafafa;
            border: 1px solid {COLOR_BORDER_INPUT}; border-radius: 6px;
        }}
        QListWidget::item:selected {{ background-color: {COLOR_PRIMARY}; color: {COLOR_BG_MAIN}; }}
        """


def _tab_section() -> str:
    """QTabWidget semi-transparent tab styling."""
    return f"""
        QTabWidget {{ border: none; }}
        QTabWidget::pane {{
            border: 1px solid rgba(204, 204, 204, 100);
            border-top: none;
            background-color: rgba(255, 255, 255, 200);
            border-top-left-radius: 0px;
            border-top-right-radius: 0px;
            border-bottom-left-radius: 6px;
            border-bottom-right-radius: 6px;
        }}
        QTabBar {{ background: transparent; border: none; }}
        QTabBar::tab {{
            background-color: rgba(232, 232, 232, 130); color: #555;
            padding: 8px 20px;
            border: 1px solid rgba(204, 204, 204, 100);
            border-bottom: 1px solid rgba(204, 204, 204, 100);
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
            border-bottom-left-radius: 0px;
            border-bottom-right-radius: 0px;
            margin-right: 0px;
            font-size: 13px;
        }}
        QTabBar::tab:hover {{ background-color: rgba(240, 240, 240, 180); color: #333; }}
        QTabBar::tab:selected {{
            background-color: rgba(255, 255, 255, 200); color: {COLOR_PRIMARY};
            font-weight: 600;
            border: 1px solid rgba(204, 204, 204, 100);
            border-bottom: none;
        }}
        """


def _size_grip_section() -> str:
    """QSizeGrip (hide the default resize handle)."""
    return """
        QSizeGrip {
            width: 16px; height: 16px;
            background: transparent;
            image: none;
        }
        """


def get_preview_container_style() -> str:
    """Get style for video preview container."""
    return f"""
        QFrame#previewContainer {{
            background-color: {COLOR_PREVIEW_BG};
            border: 2px solid #333;
            border-radius: 6px;
        }}
    """


def get_video_frame_style() -> str:
    """Get style for inner video frame."""
    return f"""
        QFrame#videoFrame {{
            background-color: {COLOR_VIDEO_FRAME_BG};
            border-radius: 4px;
        }}
    """


def get_control_card_style() -> str:
    """Get style for control card panel."""
    return f"""
        QFrame#controlCard {{
            background-color: {COLOR_BG_CARD};
            border: 1px solid {COLOR_BORDER_LIGHT};
            border-radius: 6px;
        }}
    """


def get_ptz_panel_style() -> str:
    """Get style for PTZ control panel."""
    return f"""
        QFrame#ptzPanel {{
            background-color: {COLOR_BG_PANEL};
            border: 1px solid {COLOR_BORDER_LIGHT};
            border-radius: 6px;
            margin-left: 0px;
            margin-right: 0px;
            margin-top: 0px;
            margin-bottom: 6px;
        }}
    """


def get_visca_panel_style() -> str:
    """Get style for VISCA control panel."""
    return f"""
        QFrame#viscaPanel {{
            background-color: {COLOR_BG_PANEL};
            border: 1px solid {COLOR_BORDER_LIGHT};
            border-radius: 6px;
            margin-left: 0px;
            margin-right: 0px;
            margin-top: 0px;
            margin-bottom: 6px;
        }}
    """


def get_primary_button_style() -> str:
    """Get style for primary (blue) buttons."""
    return f"""
        QPushButton {{
            background-color: {COLOR_PRIMARY}; color: #fff;
            border: 1px solid #0066b8; border-radius: 6px;
            padding: 5px 16px; font-size: 13px;
        }}
        QPushButton:hover {{ background-color: {COLOR_PRIMARY_HOVER}; }}
        QPushButton:pressed {{ background-color: {COLOR_PRIMARY_PRESSED}; }}
        QPushButton:disabled {{ background-color: #ccc; color: #eee; border: 1px solid #ccc; }}
    """


def get_danger_button_style() -> str:
    """Get style for danger (red) buttons."""
    return f"""
        QPushButton {{
            background-color: {COLOR_DANGER}; color: #fff;
            border: 1px solid {COLOR_DANGER_HOVER}; border-radius: 6px;
            padding: 5px 16px; font-size: 13px;
        }}
        QPushButton:hover {{ background-color: {COLOR_DANGER_HOVER}; }}
        QPushButton:pressed {{ background-color: {COLOR_DANGER_PRESSED}; }}
    """


def get_standard_button_style() -> str:
    """Get style for standard (gray) buttons."""
    return """
        QPushButton {
            background: #f5f5f5; border: 1px solid #aaa; border-radius: 6px;
            padding: 5px 16px; font-size: 13px; color: #333;
        }
        QPushButton:hover { background: #e5e5e5; }
        QPushButton:pressed { background: #d5d5d5; }
        QPushButton:disabled { background: #e8e8e8; color: #bbb; border: 1px solid #ddd; }
    """


def get_visca_tab_style() -> str:
    """Get style for VISCA inner tab widget."""
    return f"""
        QTabWidget {{
            background: transparent;
        }}
        QTabWidget::pane {{
            border: 1px solid {COLOR_BORDER_STD};
            border-top: none;
            background-color: {COLOR_BG_MAIN};
            border-bottom-left-radius: 6px;
            border-bottom-right-radius: 6px;
            border-top-left-radius: 0px;
            border-top-right-radius: 0px;
        }}
        QTabBar {{
            background: transparent;
            border: none;
        }}
        QTabBar::tab {{
            background-color: {COLOR_BORDER_LIGHT}; color: {COLOR_TEXT_LABEL};
            padding: 4px 16px;
            border: 1px solid {COLOR_BORDER_STD};
            border-bottom: 1px solid {COLOR_BORDER_STD};
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
            border-bottom-left-radius: 0px;
            border-bottom-right-radius: 0px;
            margin-right: 2px;
        }}
        QTabBar::tab:selected {{
            background-color: {COLOR_BG_MAIN}; color: {COLOR_TEXT_MAIN};
            border-bottom: none;
        }}
    """


def get_visca_connect_button_style() -> str:
    """Get style for VISCA connect/open button."""
    return f"""
        QPushButton {{
            background: {COLOR_PRIMARY}; color: #fff; border: none; border-radius: 4px;
            padding: 4px 20px; font-size: 12px;
        }}
        QPushButton:hover {{ background: {COLOR_PRIMARY_HOVER}; }}
    """
