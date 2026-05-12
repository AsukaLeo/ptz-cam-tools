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

"""Reusable control card widget for video tab control panels."""

from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QWidget,
)
from PySide6.QtCore import Qt
from typing import Optional

from app.styles.theme import get_control_card_style


class ControlCard(QFrame):
    """Standard control card with title and labeled row helpers.

    Provides a consistent frame, layout, and fixed height for all
    video tab control panels. Subclasses/tabs add their specific
    controls via add_row() or direct layout access.
    """

    def __init__(self, title: str = "", parent: Optional[QWidget] = None) -> None:
        """Initialize the control card.

        Args:
            title: Optional card title.
            parent: Optional parent widget.
        """
        super().__init__(parent)
        self.setObjectName("controlCard")
        self.setStyleSheet(get_control_card_style())

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(12, 10, 12, 10)
        self._layout.setSpacing(6)

        if title:
            title_label = QLabel(title)
            title_label.setStyleSheet(
                "font-size: 12px; font-weight: 500; color: #555;"
                "background: transparent; padding: 0;"
            )
            self._layout.addWidget(title_label)

        self.setFixedHeight(120)

    def layout(self) -> QVBoxLayout:  # type: ignore[override]
        """Get the card's layout.

        Returns:
            QVBoxLayout of the card.
        """
        return self._layout

    def add_row(self) -> QHBoxLayout:
        """Add a new horizontal row to the card.

        Returns:
            QHBoxLayout to populate with widgets.
        """
        row = QHBoxLayout()
        row.setSpacing(8)
        self._layout.addLayout(row)
        return row

    @staticmethod
    def make_label(text: str, width: int = 80) -> QLabel:
        """Create a standard right-aligned label for a control row.

        Args:
            text: Label text.
            width: Fixed width for alignment.

        Returns:
            Configured QLabel.
        """
        lbl = QLabel(text)
        lbl.setFixedWidth(width)
        lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        return lbl

    @staticmethod
    def make_combo(fixed_width: int = 140, max_visible: int = 12) -> 'QComboBox':
        """Create a standard QComboBox for a control row.

        Args:
            fixed_width: Fixed width for the combo.
            max_visible: Maximum visible items before scroll.

        Returns:
            Configured QComboBox.
        """
        from PySide6.QtWidgets import QComboBox
        combo = QComboBox()
        combo.setMinimumWidth(fixed_width)
        combo.setMaxVisibleItems(max_visible)
        combo.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        return combo

    @staticmethod
    def add_stretch(row: QHBoxLayout) -> None:
        """Add a stretch to push widgets left.

        Args:
            row: Row layout to stretch.
        """
        row.addStretch()
