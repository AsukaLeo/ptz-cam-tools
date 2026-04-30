"""Video preview widget component."""

from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QLabel, QWidget
)
from PySide6.QtCore import Qt
from typing import Optional

from app.styles.theme import (
    get_preview_container_style,
    get_video_frame_style,
)
from app.utils.constants import PREVIEW_PLACEHOLDER_TEXT


class PreviewWidget(QFrame):
    """Video preview area widget with 16:9 aspect ratio support.
    
    This widget creates a black background container with an inner video
    frame that maintains 16:9 aspect ratio when resized.
    
    Attributes:
        video_frame: The inner QFrame that holds the actual video content.
        placeholder_label: Label shown when no video is playing.
    """
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize the preview widget.
        
        Args:
            parent: Optional parent widget.
        """
        super().__init__(parent)
        self.setObjectName("previewContainer")
        self.setMinimumHeight(200)
        self.setStyleSheet(get_preview_container_style())
        
        # Container layout
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setAlignment(Qt.AlignCenter)
        
        # Inner video frame - maintains 16:9 ratio
        self.video_frame = QFrame()
        self.video_frame.setObjectName("videoFrame")
        self.video_frame.setStyleSheet(get_video_frame_style())
        
        self._video_layout = QVBoxLayout(self.video_frame)
        self._video_layout.setContentsMargins(0, 0, 0, 0)
        self._video_layout.setAlignment(Qt.AlignCenter)
        
        # Placeholder text
        self.placeholder_label = QLabel(PREVIEW_PLACEHOLDER_TEXT)
        self.placeholder_label.setStyleSheet(
            "color: #666; font-size: 24px; background: transparent;"
        )
        self.placeholder_label.setAlignment(Qt.AlignCenter)
        self._video_layout.addWidget(self.placeholder_label)
        
        # Video display label (for showing frames)
        self.video_label = QLabel()
        self.video_label.setStyleSheet("background: transparent;")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setScaledContents(True)
        self.video_label.hide()  # Hidden by default
        self._video_layout.addWidget(self.video_label)
        
        self._layout.addWidget(self.video_frame)
    
    def set_video_frame(self, pixmap) -> None:
        """Display video frame.
        
        Args:
            pixmap: QPixmap to display.
        """
        if pixmap and not pixmap.isNull():
            self.video_label.setPixmap(pixmap)
            if not self.video_label.isVisible():
                self.video_label.show()
            if self.placeholder_label.isVisible():
                self.placeholder_label.hide()
    
    def update_video_size(self, container_width: int, container_height: int) -> None:
        """Update video frame size to maintain 16:9 aspect ratio.
        
        Args:
            container_width: Available width for the video.
            container_height: Available height for the video.
        """
        # Account for padding
        available_width = container_width - 32
        available_height = container_height
        
        # Calculate 16:9 video dimensions
        ideal_height = int(available_width * 9 / 16)
        
        if ideal_height <= available_height:
            # Width constrained
            video_width = available_width
            video_height = ideal_height
        else:
            # Height constrained
            video_height = available_height
            video_width = int(video_height * 16 / 9)
        
        # Enforce minimum size
        from app.utils.constants import PREVIEW_MIN_WIDTH, PREVIEW_MIN_HEIGHT
        video_width = max(video_width, PREVIEW_MIN_WIDTH)
        video_height = max(video_height, PREVIEW_MIN_HEIGHT)
        
        self.video_frame.setFixedSize(video_width, video_height)
    
    def hide_placeholder(self) -> None:
        """Hide the placeholder text (call when video starts playing)."""
        self.placeholder_label.hide()
    
    def show_placeholder(self) -> None:
        """Show the placeholder text (call when video stops)."""
        self.placeholder_label.show()
