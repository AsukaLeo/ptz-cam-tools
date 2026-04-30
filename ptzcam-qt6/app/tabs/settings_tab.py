"""Settings tab page."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox
)
from PySide6.QtCore import Qt
from typing import Optional, Callable

from app.utils.constants import LANGUAGES


class SettingsTab(QWidget):
    """Application settings tab.
    
    Provides UI configuration options like language selection.
    """
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize the settings tab.
        
        Args:
            parent: Optional parent widget.
        """
        super().__init__(parent)
        self.on_status_update: Optional[Callable[[str], None]] = None
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Set up the tab UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(20)
        
        # UI Settings section
        ui_title = QLabel("界面设置")
        ui_title.setStyleSheet(
            "font-weight: 500; border-bottom: 1px solid #eee; "
            "padding-bottom: 4px; background: transparent;"
        )
        layout.addWidget(ui_title)
        
        # Language selection
        lang_row = QHBoxLayout()
        lang_row.setSpacing(12)
        
        lang_label = QLabel("语言:")
        lang_label.setFixedWidth(100)
        lang_row.addWidget(lang_label)
        
        lang_combo = QComboBox()
        lang_combo.addItems(LANGUAGES)
        lang_row.addWidget(lang_combo)
        lang_row.addStretch()
        
        layout.addLayout(lang_row)
        layout.addStretch()
    
    def _notify_status(self, message: str) -> None:
        """Notify status update via callback."""
        if self.on_status_update:
            self.on_status_update(message)
    
    def set_status_callback(self, callback: Callable[[str], None]) -> None:
        """Set the status update callback."""
        self.on_status_update = callback
