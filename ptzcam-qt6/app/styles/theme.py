"""Application stylesheet definitions."""

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


def get_global_stylesheet(arrow_svg_path: str) -> str:
    """Generate the global application stylesheet.
    
    Args:
        arrow_svg_path: Path to the ComboBox dropdown arrow SVG file.
        
    Returns:
        Complete stylesheet string.
    """
    return f"""
        QWidget {{ color: {COLOR_TEXT_MAIN}; }}
        QMainWindow {{ background-color: {COLOR_BG_MAIN}; }}
        QPushButton {{ color: {COLOR_TEXT_MAIN}; background-color: #f5f5f5; }}
        QPushButton:disabled {{ color: #bbb; background-color: #e8e8e8; border: 1px solid #ddd; }}
        QLabel {{ color: {COLOR_TEXT_MAIN}; background-color: transparent; }}
        QLineEdit {{
            color: {COLOR_TEXT_MAIN}; background-color: {COLOR_BG_MAIN};
            border: 1px solid {COLOR_BORDER_INPUT}; border-radius: 6px;
            padding: 4px 8px;
        }}

        /* ── ComboBox：使用 SVG 标准箭头 ── */
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

        QStatusBar {{ color: {COLOR_TEXT_MAIN}; background-color: #f0f0f0; }}
        QStatusBar QLabel {{ color: {COLOR_TEXT_SECONDARY}; background-color: transparent; }}
        QListWidget {{
            color: {COLOR_TEXT_LABEL}; background-color: #fafafa;
            border: 1px solid {COLOR_BORDER_INPUT}; border-radius: 6px;
        }}
        QListWidget::item:selected {{ background-color: {COLOR_PRIMARY}; color: {COLOR_BG_MAIN}; }}

        /* ── QTabWidget 去掉默认边框 ── */
        QTabWidget {{
            border: none;
        }}

        /* ── Tab 样式：选中 Tab 与 Pane 融为一体 ── */
        QTabWidget::pane {{
            border: 1px solid {COLOR_BORDER_STD};
            background-color: {COLOR_BG_MAIN};
            border-top-left-radius: 0px;
            border-top-right-radius: 0px;
            border-bottom-left-radius: 6px;
            border-bottom-right-radius: 6px;
            margin-top: -1px;
        }}
        QTabBar::tab {{
            background-color: #e8e8e8; color: #777;
            padding: 8px 20px;
            border: 1px solid {COLOR_BORDER_STD};
            border-bottom: 1px solid {COLOR_BORDER_STD};
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
            border-bottom-left-radius: 0px;
            border-bottom-right-radius: 0px;
            margin-right: 0px;
            font-size: 13px;
        }}
        QTabBar::tab:hover {{
            background-color: #f0f0f0; color: #444;
        }}
        QTabBar::tab:selected {{
            background-color: {COLOR_BG_MAIN}; color: {COLOR_PRIMARY};
            font-weight: 600;
            border-bottom-color: {COLOR_BG_MAIN};
            margin-bottom: -1px;
            margin-right: 0px;
        }}

        /* ── SizeGrip 样式 ── */
        QSizeGrip {{
            width: 16px; height: 16px;
            background: transparent;
            image: none;
        }}
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
            background-color: {COLOR_BG_MAIN};
        }}
        QTabWidget::pane {{
            border: 1px solid {COLOR_BORDER_STD};
            background-color: {COLOR_BG_MAIN};
            border-bottom-left-radius: 6px;
            border-bottom-right-radius: 6px;
            border-top-left-radius: 0px;
            border-top-right-radius: 0px;
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
            border-bottom-color: {COLOR_BG_MAIN};
            margin-bottom: -1px;
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
