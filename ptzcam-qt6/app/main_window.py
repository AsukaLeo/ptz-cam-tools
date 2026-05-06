"""Main application window."""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QStatusBar, QTabWidget
)
from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QResizeEvent
from typing import Optional

from app.utils.constants import (
    MIN_WIDTH, MIN_HEIGHT, DEFAULT_WIDTH, DEFAULT_HEIGHT,
    VERSION_STRING, STATUS_READY,
    TAB_USB, TAB_RTSP, TAB_NDI, TAB_ONVIF, TAB_SETTINGS,
)
from app.styles.theme import get_global_stylesheet
from app.widgets import PreviewWidget, PTZPanel, VISCAPanel
from app.tabs import USBTab, RTSPTab, NDITab, ONVIFTab, SettingsTab
from app.utils.logger import get_logger


class MainWindow(QMainWindow):
    """Main application window for PTZ-Cam-Tools.
    
    Provides a tabbed interface for USB, RTSP, NDI, and ONVIF video sources,
    along with PTZ and VISCA control panels.
    
    Attributes:
        _preview_frames: List of preview widgets for size management.
        _resizing: Flag to prevent recursive resize events.
        _tab_widgets: Dictionary of tab pages.
    """
    
    def __init__(self) -> None:
        """Initialize the main window."""
        super().__init__()
        
        self.setWindowTitle("PTZ-Cam-Tools")
        
        # Initialize logger
        self._logger = get_logger(__name__)
        
        # Initialize instance variables
        self._preview_frames: list[PreviewWidget] = []
        self._resizing: bool = False
        self._tab_widgets: dict[str, QWidget] = {}
        
        # Set window constraints
        self.setMinimumSize(MIN_WIDTH, MIN_HEIGHT)
        self.resize(DEFAULT_WIDTH, DEFAULT_HEIGHT)
        
        self._logger.debug(f"Window size: {DEFAULT_WIDTH}x{DEFAULT_HEIGHT}")
        
        self._setup_ui()
        self._logger.debug("Main window UI setup complete")
    
    def _setup_ui(self) -> None:
        """Set up the main window UI."""
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(16, 6, 16, 6)
        main_layout.setSpacing(6)
        
        # Tab widget
        self._create_tab_widget(main_layout)
        
        # Control panels (PTZ + VISCA)
        self._create_control_panels(main_layout)
        
        # Status bar
        self._create_status_bar()
    
    def _create_tab_widget(self, parent_layout: QVBoxLayout) -> None:
        """Create and configure the tab widget.
        
        Args:
            parent_layout: Layout to add the tab widget to.
        """
        self.tab_widget = QTabWidget()
        
        # Create tab pages
        self._usb_tab = USBTab()
        self._usb_tab.set_video_info_callback(self.update_video_info)
        self._rtsp_tab = RTSPTab()
        self._rtsp_tab.set_video_info_callback(self.update_video_info)
        self._ndi_tab = NDITab()
        self._onvif_tab = ONVIFTab()
        self._settings_tab = SettingsTab()
        
        # Store references
        self._tab_widgets = {
            TAB_USB: self._usb_tab,
            TAB_RTSP: self._rtsp_tab,
            TAB_NDI: self._ndi_tab,
            TAB_ONVIF: self._onvif_tab,
            TAB_SETTINGS: self._settings_tab,
        }
        
        self._logger.debug(f"Created {len(self._tab_widgets)} tabs")
        
        # Set up status callbacks
        for tab in self._tab_widgets.values():
            if hasattr(tab, 'set_status_callback'):
                tab.set_status_callback(self.update_status)
        
        # Create preview widgets for each tab
        self._create_preview_for_tab(self._usb_tab)
        self._create_preview_for_tab(self._rtsp_tab)
        self._create_preview_for_tab(self._ndi_tab)
        self._create_preview_for_tab(self._onvif_tab)
        
        self._logger.debug(f"Created {len(self._preview_frames)} preview widgets")
        
        # Add tabs
        self.tab_widget.addTab(self._usb_tab, TAB_USB)
        self.tab_widget.addTab(self._rtsp_tab, TAB_RTSP)
        self.tab_widget.addTab(self._ndi_tab, TAB_NDI)
        self.tab_widget.addTab(self._onvif_tab, TAB_ONVIF)
        self.tab_widget.addTab(self._settings_tab, TAB_SETTINGS)
        
        # Connect tab change signal
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        
        parent_layout.addWidget(self.tab_widget, 1)
    
    def _create_preview_for_tab(self, tab: QWidget) -> PreviewWidget:
        """Create and attach a preview widget to a tab.
        
        Args:
            tab: Tab page to attach preview to.
            
        Returns:
            Created PreviewWidget.
        """
        preview = PreviewWidget()
        self._preview_frames.append(preview)
        
        if hasattr(tab, 'set_preview_widget'):
            tab.set_preview_widget(preview)
        
        return preview
    
    def _create_control_panels(self, parent_layout: QVBoxLayout) -> None:
        """Create PTZ and VISCA control panels.
        
        Args:
            parent_layout: Layout to add panels to.
        """
        # Create panels
        self._ptz_panel = PTZPanel()
        self._visca_panel = VISCAPanel()
        
        # Set up status callbacks
        self._ptz_panel.set_status_callback(self.update_status)
        self._visca_panel.set_status_callback(self.update_status)
        
        # Layout panels side by side
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(12)
        controls_layout.addWidget(self._ptz_panel, 1)
        controls_layout.addWidget(self._visca_panel, 1)
        
        parent_layout.addLayout(controls_layout)
    
    def _create_status_bar(self) -> None:
        """Create and configure the status bar."""
        # Status label (left)
        self.status_label = QLabel(f"  状态: {STATUS_READY}")
        self.statusBar().addWidget(self.status_label)
        
        # Video info label (center)
        self.video_info_label = QLabel("")
        self.video_info_label.setStyleSheet(
            "color: #666; font-size: 11px; background: transparent;"
        )
        self.statusBar().addWidget(self.video_info_label)
        
        # Version label (right)
        self.version_label = QLabel(f"{VERSION_STRING}  ")
        self.version_label.setStyleSheet(
            "color: #999; font-size: 11px; background: transparent;"
        )
        self.statusBar().addPermanentWidget(self.version_label)
    
    def resizeEvent(self, event: QResizeEvent) -> None:
        """Handle window resize events.
        
        Args:
            event: Resize event.
        """
        super().resizeEvent(event)
        # Delay update to let layout settle first
        QTimer.singleShot(0, self._update_preview_sizes)
    
    def _update_preview_sizes(self) -> None:
        """Update all preview widget sizes to maintain aspect ratio."""
        for preview in self._preview_frames:
            if not preview.isVisible():
                continue
            
            parent = preview.parentWidget()
            if not parent:
                continue
            
            preview.update_video_size(parent.width(), preview.height())
    
    def _on_tab_changed(self, index: int) -> None:
        """Handle tab selection change.
        
        Args:
            index: Index of the newly selected tab.
        """
        tab_names = [TAB_USB, TAB_RTSP, TAB_NDI, TAB_ONVIF, TAB_SETTINGS]
        statuses = [
            STATUS_READY,
            "未连接",
            "未连接",
            "未连接",
            "设置",
        ]
        
        status = statuses[index] if index < len(statuses) else STATUS_READY
        self._logger.debug(f"Tab changed to: {tab_names[index] if index < len(tab_names) else 'Unknown'}")
        self.update_status(status)
        
        # Update preview sizes after tab switch
        QTimer.singleShot(0, self._update_preview_sizes)
    
    def update_status(self, text: str) -> None:
        """Update the status bar text.
        
        Args:
            text: Status text to display.
        """
        self._logger.debug(f"Status updated: {text}")
        self.status_label.setText(f"状态: {text}")
    
    def update_video_info(self, width: int, height: int,
                          format_name: str, fps: float,
                          latency_ms: int = 0,
                          decode_method: str = "",
                          cpu_percent: float = 0.0) -> None:
        """Update video info display in status bar.
        
        Args:
            width: Video frame width.
            height: Video frame height.
            format_name: Pixel format name.
            fps: Current frame rate.
            latency_ms: Capture-to-display latency in ms.
            decode_method: Decoding method description.
            cpu_percent: Current CPU usage percentage.
        """
        cpu_str = f"CPU:{cpu_percent:.0f}%" if cpu_percent > 0 else ""
        parts = [
            f"{width}×{height}",
            f"源:{format_name}",
            f"解码:{decode_method}" if decode_method else "",
            f"{fps:.1f}fps",
            f"{latency_ms}ms",
            cpu_str,
        ]
        display = "  |  ".join(p for p in parts if p)
        self.video_info_label.setText(f"  {display}  ")
    
    def sizeHint(self) -> QSize:
        """Provide recommended window size.
        
        Returns:
            Recommended QSize.
        """
        return QSize(DEFAULT_WIDTH, 600)


def create_application(arrow_svg_path: str) -> None:
    """Configure the application with global stylesheet.
    
    This function should be called after creating QApplication but before
    creating MainWindow.
    
    Args:
        arrow_svg_path: Path to the ComboBox dropdown arrow SVG file.
    """
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import Qt
    
    app = QApplication.instance()
    if app:
        app.setStyleSheet(get_global_stylesheet(arrow_svg_path))
