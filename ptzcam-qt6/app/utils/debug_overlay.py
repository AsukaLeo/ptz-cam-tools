"""Debug overlay — F12 toggles widget name/geometry display on top of the UI."""

from PySide6.QtCore import Qt, QRect, QPoint
from PySide6.QtGui import QPainter, QColor, QPen, QFont
from PySide6.QtWidgets import QWidget


class DebugOverlay(QWidget):
    """Transparent overlay that draws widget outlines, names, and sizes.

    Press F12 to toggle visibility. Only widgets with a non-empty
    objectName() are annotated.
    """

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setStyleSheet("background: transparent;")
        self.hide()

        self._target = parent
        self._font = QFont("Consolas, monospace", 8)
        self._pen_outline = QPen(QColor(255, 107, 107, 200), 1)
        self._pen_label = QPen(QColor(255, 255, 255))
        self._bg_label = QColor(255, 107, 107, 180)

        # Install event filter on parent to catch F12
        parent.installEventFilter(self)

    def eventFilter(self, obj, event):
        from PySide6.QtCore import QEvent
        from PySide6.QtGui import QKeyEvent
        if event.type() == QEvent.Type.KeyPress:
            ke = event
            if ke.key() == Qt.Key.Key_F12:
                self.setVisible(not self.isVisible())
                if self.isVisible():
                    self.raise_()
                    self.resize(self._target.size())
                return True
        return super().eventFilter(obj, event)

    def paintEvent(self, event) -> None:
        if not self.isVisible():
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        self._paint_widget(painter, self._target, QPoint(0, 0))

    def _paint_widget(self, painter: QPainter, widget: QWidget, offset: QPoint) -> None:
        """Recursively paint outlines and labels for widgets with objectName."""
        for child in widget.findChildren(QWidget):
            if not child.isVisible():
                continue
            name = child.objectName()
            if not name:
                continue

            # Convert child's pos to overlay coordinates
            pos = child.mapTo(self._target, QPoint(0, 0))
            rect = QRect(pos, child.size())

            # Skip if too small or off-screen
            if rect.width() < 20 or rect.height() < 10:
                continue
            if not self.rect().intersects(rect):
                continue

            # Draw outline
            painter.setPen(self._pen_outline)
            painter.drawRect(rect)

            # Draw label
            label = f"{name}  {rect.width()}x{rect.height()}"
            painter.setFont(self._font)
            fm = painter.fontMetrics()
            label_w = fm.horizontalAdvance(label) + 8
            label_h = fm.height() + 4
            label_rect = QRect(pos.x(), pos.y() - label_h, label_w, label_h)

            painter.fillRect(label_rect, self._bg_label)
            painter.setPen(self._pen_label)
            painter.drawText(label_rect.adjusted(2, 1, 0, 0),
                             Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                             label)
