# -*- coding: utf-8 -*-

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

"""Debug overlay — F12 toggles widget name/geometry display on top of the UI.

Features:
- F12 toggle visibility (top-right hint bar).
- Hover over a widget → its label + outline highlight gold.
- Click a widget's label → hide that widget's annotation (toggle).
- Hidden widgets show as dashed outline + ✕ mark.
- Labels try inside-widget placement first, then outside with overlap avoidance.
- Color-coded outlines by widget type.
"""

from PySide6.QtCore import Qt, QRect, QPoint, QEvent
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QFontMetrics
from PySide6.QtWidgets import QWidget


class DebugOverlay(QWidget):
    """Transparent overlay that draws widget outlines, names, and sizes."""

    # (outline, label_bg) — hex strings per widget type
    TYPE_COLORS: dict[str, tuple[str, str]] = {
        "QPushButton": ("#3498db", "#2980b9"),
        "QLabel":      ("#9b59b6", "#8e44ad"),
        "QComboBox":   ("#2ecc71", "#27ae60"),
        "QLineEdit":   ("#e67e22", "#d35400"),
        "QTextEdit":   ("#f1c40f", "#c0392b"),
        "QSlider":     ("#34495e", "#2c3e50"),
        "QTabWidget":  ("#e74c3c", "#c0392b"),
        "QFrame":      ("#95a5a6", "#7f8c8d"),
    }
    DEFAULT_OUTLINE = "#ff6b6b"
    DEFAULT_BG = "#e05555"
    HOVER_COLOR = QColor("#ffd700")  # gold

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setStyleSheet("background: transparent;")
        self.setMouseTracking(True)
        self.hide()

        self._target = parent
        self._font = QFont("Consolas, monospace", 8)
        self._hovered: QWidget | None = None
        self._hidden_names: set[str] = set()      # objectNames to skip
        self._label_rects: list[tuple[QRect, str]] = []  # (rect, name) from last paint
        self._placed: list[QRect] = []             # already-placed label rects

        parent.installEventFilter(self)

    # ── F12 toggle ──────────────────────────────────────────────

    def eventFilter(self, obj, event) -> bool:
        if event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_F12:
                if not self.isVisible():
                    self._auto_name()
                    self._hidden_names.clear()  # 恢复所有已隐藏的标签
                    self.raise_()
                self.resize(self._target.size())
                self.setVisible(not self.isVisible())
                return True
        return super().eventFilter(obj, event)

    def _auto_name(self) -> None:
        """Auto-assign objectName to unnamed visible widgets."""
        counts: dict[str, int] = {}
        for ch in self._target.findChildren(QWidget):
            if ch.objectName():
                continue
            if not ch.isVisible():
                continue
            if ch.width() < 15 or ch.height() < 10:
                continue
            cls = type(ch).__name__
            counts[cls] = counts.get(cls, 0) + 1
            ch.setObjectName(f"{cls}_{counts[cls]}")

    # ── Hover — find smallest widget containing cursor ───────────

    def _find_widget_at(self, pos: QPoint) -> QWidget | None:
        """Find the deepest (smallest) widget containing cursor.

        Uses same rect-based iteration as paintEvent — reliable
        across all widget types unlike childAt() on QMainWindow.
        """
        best: QWidget | None = None
        best_area = float("inf")
        for ch in self._target.findChildren(QWidget):
            name = ch.objectName()
            if not name or not ch.isVisible():
                continue
            if ch.width() < 18 or ch.height() < 10:
                continue
            r = QRect(ch.mapTo(self._target, QPoint(0, 0)), ch.size())
            if r.contains(pos):
                area = ch.width() * ch.height()
                if area < best_area:
                    best_area = area
                    best = ch
        return best

    def mouseMoveEvent(self, event) -> None:
        old = self._hovered
        self._hovered = self._find_widget_at(event.position().toPoint())
        if old is not self._hovered:
            self.update()

    def leaveEvent(self, event) -> None:
        if self._hovered is not None:
            self._hovered = None
            self.update()

    # ── Click — hide/show individual label ──────────────────────

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position().toPoint()
            for lr, name in self._label_rects:
                if lr.contains(pos):
                    if name in self._hidden_names:
                        self._hidden_names.discard(name)
                    else:
                        self._hidden_names.add(name)
                    self.update()
                    return

    # ── Paint ───────────────────────────────────────────────────

    def paintEvent(self, event) -> None:
        if not self.isVisible():
            return

        self.resize(self._target.size())

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._placed.clear()
        self._label_rects.clear()

        # Collect all annotatable widgets, sorted top→bottom, left→right
        items: list[tuple[int, int, QWidget, QRect]] = []
        for ch in self._target.findChildren(QWidget):
            name = ch.objectName()
            if not name or not ch.isVisible():
                continue
            if ch.width() < 18 or ch.height() < 10:
                continue
            pos = ch.mapTo(self._target, QPoint(0, 0))
            r = QRect(pos, ch.size())
            if not self.rect().intersects(r):
                continue
            items.append((pos.y(), pos.x(), ch, r))

        items.sort(key=lambda x: (x[0], x[1]))  # top→bottom, left→right

        for _, _, ch, rect in items:
            name = ch.objectName()
            cls = type(ch).__name__
            outline_hex, bg_hex = self.TYPE_COLORS.get(
                cls, (self.DEFAULT_OUTLINE, self.DEFAULT_BG))

            is_hidden = name in self._hidden_names
            is_hovered = (ch == self._hovered and not is_hidden)

            if is_hidden:
                # Dashed outline + subtle cross
                pen = QPen(QColor(180, 180, 180, 160), 1)
                pen.setStyle(Qt.PenStyle.DashLine)
                painter.setPen(pen)
                painter.drawRect(rect)
                # Small ✕ in center
                painter.setFont(QFont("Consolas, monospace", 6))
                painter.setPen(QColor(180, 180, 180, 120))
                painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "✕")
                continue

            if is_hovered:
                oc = self.HOVER_COLOR
                bg = QColor("#ffd700")
                pw = 3
            else:
                oc = QColor(outline_hex)
                bg = QColor(bg_hex)
                pw = 1

            # Outline
            painter.setPen(QPen(oc, pw))
            painter.drawRect(rect)

            # Label
            label = f"{name} {rect.width()}x{rect.height()} [{cls}]"
            painter.setFont(self._font)
            fm = painter.fontMetrics()
            lw = fm.horizontalAdvance(label) + 8
            lh = fm.height() + 4

            # Pick best label position
            lr = self._pick_label_pos(rect, lw, lh)

            # Draw label background
            painter.fillRect(lr, bg)
            painter.setPen(QPen(QColor("#fff"), 1 if not is_hovered else 2))
            if is_hovered:
                # Border around hovered label for extra emphasis
                painter.drawRect(lr)
            painter.drawText(
                lr.adjusted(2, 1, -2, 0),
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                label,
            )
            self._placed.append(lr)
            self._label_rects.append((lr, name))

        # Hint bar (top-right)
        hint = "DebugOverlay — F12 隐藏 ｜ 点击标签隐藏"
        painter.setFont(QFont("Consolas", 9))
        fm = painter.fontMetrics()
        hw = fm.horizontalAdvance(hint) + 16
        hh = fm.height() + 10
        hr = QRect(self.width() - hw - 8, 4, hw, hh)
        painter.fillRect(hr, QColor(0, 0, 0, 180))
        painter.setPen(Qt.GlobalColor.white)
        painter.drawText(
            hr.adjusted(6, 4, -6, 0),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            hint,
        )

    # ── Label placement with overlap avoidance ──────────────────

    def _pick_label_pos(self, wr: QRect, lw: int, lh: int) -> QRect:
        """Pick best label position. Prefers inside-widget, then outside.

        Order: inside (if fits) → top → bottom → right → left.
        Each outside candidate checks overlap with already-placed labels.
        """
        inside = QRect(wr.x() + 2, wr.y() + 2, min(lw, wr.width() - 4), lh)
        if inside.width() >= lw * 0.7 and inside.height() >= lh:
            return inside

        candidates = [
            QRect(wr.x(),          wr.y() - lh,          lw, lh),   # top
            QRect(wr.x(),          wr.y() + wr.height(), lw, lh),   # bottom
            QRect(wr.x() + wr.width(), wr.y(),           lw, lh),   # right
            QRect(wr.x() - lw,     wr.y(),               lw, lh),   # left
        ]
        for cr in candidates:
            if (cr.right() <= self.width() and cr.left() >= 0 and
                    cr.bottom() <= self.height() and cr.top() >= 0):
                if not any(cr.intersects(pr) for pr in self._placed):
                    return cr
        return candidates[0]  # fallback: top
