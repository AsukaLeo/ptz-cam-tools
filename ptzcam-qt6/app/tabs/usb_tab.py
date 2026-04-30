"""USB camera tab page."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox
)
from PySide6.QtCore import Qt
from typing import Optional, Callable

from app.styles.theme import get_control_card_style
from app.utils.constants import (
    USB_DEVICES, RESOLUTIONS, FORMATS, FRAME_RATES,
)


class USBTab(QWidget):
    """USB camera configuration tab.
    
    Provides device selection, resolution, format, and frame rate controls.
    
    Attributes:
        on_status_update: Callback for status updates.
        preview_widget: Video preview widget (set externally).
    """
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize the USB tab.
        
        Args:
            parent: Optional parent widget.
        """
        super().__init__(parent)
        self.on_status_update: Optional[Callable[[str], None]] = None
        self.preview_widget: Optional[QWidget] = None
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Set up the tab UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 8)
        layout.setSpacing(8)
        
        # Control card
        card = self._create_control_card()
        layout.addWidget(card)
        
        # Preview area (added externally)
        self._preview_placeholder = QWidget()
        layout.addWidget(self._preview_placeholder, 1)
    
    def _create_control_card(self) -> QWidget:
        """Create the control card with device and parameter controls.
        
        Returns:
            Configured control card widget.
        """
        from app.styles.theme import get_control_card_style
        from PySide6.QtWidgets import QFrame
        
        card = QFrame()
        card.setObjectName("controlCard")
        card.setStyleSheet(get_control_card_style())
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(12, 10, 12, 10)
        card_layout.setSpacing(6)
        
        # Device row
        device_row = QHBoxLayout()
        device_row.setSpacing(8)
        
        device_label = QLabel("设备:")
        device_label.setFixedWidth(80)
        device_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        device_row.addWidget(device_label)
        
        device_combo = QComboBox()
        device_combo.addItems(USB_DEVICES)
        device_combo.setFixedWidth(200)
        device_row.addWidget(device_combo)
        
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(lambda: self._notify_status("刷新设备列表..."))
        device_row.addWidget(refresh_btn)
        
        from app.styles.theme import get_primary_button_style
        play_btn = QPushButton("播放")
        play_btn.setStyleSheet(get_primary_button_style())
        play_btn.clicked.connect(lambda: self._notify_status("播放中"))
        device_row.addWidget(play_btn)
        
        device_row.addStretch()
        card_layout.addLayout(device_row)
        
        # Parameters row
        param_row = QHBoxLayout()
        param_row.setSpacing(8)
        
        # Resolution
        lbl1 = QLabel("分辨率:")
        lbl1.setFixedWidth(80)
        lbl1.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        param_row.addWidget(lbl1)
        
        res_combo = QComboBox()
        res_combo.addItems(RESOLUTIONS)
        param_row.addWidget(res_combo)
        
        # Format
        lbl2 = QLabel("格式:")
        lbl2.setFixedWidth(50)
        lbl2.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        param_row.addWidget(lbl2)
        
        fmt_combo = QComboBox()
        fmt_combo.addItems(FORMATS)
        param_row.addWidget(fmt_combo)
        
        # Frame rate
        lbl3 = QLabel("帧率:")
        lbl3.setFixedWidth(50)
        lbl3.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        param_row.addWidget(lbl3)
        
        fps_combo = QComboBox()
        fps_combo.addItems(FRAME_RATES)
        param_row.addWidget(fps_combo)
        
        param_row.addStretch()
        card_layout.addLayout(param_row)
        
        card.setFixedHeight(120)
        
        return card
    
    def set_preview_widget(self, widget: QWidget) -> None:
        """Set the video preview widget.
        
        Args:
            widget: Preview widget to display.
        """
        layout = self.layout()
        # Replace placeholder
        layout.replaceWidget(self._preview_placeholder, widget)
        self._preview_placeholder.hide()
        self.preview_widget = widget
    
    def _notify_status(self, message: str) -> None:
        """Notify status update via callback.
        
        Args:
            message: Status message to send.
        """
        if self.on_status_update:
            self.on_status_update(message)
    
    def set_status_callback(self, callback: Callable[[str], None]) -> None:
        """Set the status update callback.
        
        Args:
            callback: Function to call when status needs updating.
        """
        self.on_status_update = callback
