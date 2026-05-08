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
        if event.type() == QEvent.Type.KeyPress:
            ke = event
            if ke.key() == Qt.Key.Key_F12:
                if not self.isVisible():
                    self._auto_name_widgets()
                    self.raise_()
                    self.resize(self._target.size())
                self.setVisible(not self.isVisible())
                return True
        return super().eventFilter(obj, event)

    def _auto_name_widgets(self) -> None:
        """Auto-assign objectName to all unnamed visible widgets."""
        name_counts: dict[str, int] = {}
        for child in self._target.findChildren(QWidget):
            if child.objectName():
                continue
            if not child.isVisible():
                continue
            if child.size().width() < 15 or child.size().height() < 10:
                continue
            # Generate name from class
            cls = type(child).__name__
            name_counts[cls] = name_counts.get(cls, 0) + 1
            child.setObjectName(f"{cls}_{name_counts[cls]}")

    def paintEvent(self, event) -> None:
        if not self.isVisible():
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        self._paint_widget(painter, self._target, QPoint(0, 0))

    def _paint_widget(self, painter: QPainter, widget: QWidget, offset: QPoint) -> None:
        """Recursively paint outlines and labels for all visible widgets."""
        for child in widget.findChildren(QWidget):
            if not child.isVisible():
                continue
            name = child.objectName()
            if not name:
                continue

            pos = child.mapTo(self._target, QPoint(0, 0))
            rect = QRect(pos, child.size())

            # Skip tiny widgets
            if rect.width() < 18 or rect.height() < 10:
                continue
            if not self.rect().intersects(rect):
                continue

            # Choose color based on widget type
            cls = type(child).__name__
            colors = {
                "QPushButton": QColor(52, 152, 219, 200),
                "QLabel": QColor(155, 89, 182, 200),
                "QComboBox": QColor(46, 204, 113, 200),
                "QLineEdit": QColor(230, 126, 34, 200),
                "QTextEdit": QColor(241, 196, 15, 200),
                "QSlider": QColor(52, 73, 94, 200),
                "QTabWidget": QColor(231, 76, 60, 200),
                "QFrame": QColor(149, 165, 166, 200),
            }
            color = colors.get(cls, QColor(255, 107, 107, 180))

            # Draw outline
            painter.setPen(QPen(color, 1))
            painter.drawRect(rect)

            # Draw label: name + size + type
            label = f"{name} {rect.width()}x{rect.height()} [{cls}]"
            painter.setFont(self._font)
            fm = painter.fontMetrics()
            label_w = fm.horizontalAdvance(label) + 6
            label_h = fm.height() + 4
            label_rect = QRect(pos.x(), pos.y() - label_h, label_w, label_h)

            painter.fillRect(label_rect, color)
            painter.setPen(QPen(QColor(255, 255, 255)))
            painter.drawText(label_rect.adjusted(2, 1, -2, 0),
                             Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                             label)
