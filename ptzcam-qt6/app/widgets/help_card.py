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

"""Help card widget for tab usage instructions."""

from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QWidget
from PySide6.QtCore import Qt
from typing import Optional


class HelpCard(QFrame):
    """Semi-transparent help card showing usage instructions for a tab.

    Placed to the right of the control card in each video tab.
    Uses border styling that matches the control card.
    """

    def __init__(self, title: str, tips: list[str],
                 parent: Optional[QWidget] = None) -> None:
        """Initialize the help card.

        Args:
            title: Card title (e.g. "USB 使用说明").
            tips: List of instruction tips to display.
            parent: Optional parent widget.
        """
        super().__init__(parent)
        self.setObjectName("helpCard")
        self.setStyleSheet("""
            QFrame#helpCard {
                background-color: rgba(255, 255, 255, 180);
                border: 1px solid rgba(204, 204, 204, 100);
                border-radius: 6px;
            }
        """)
        self.setMinimumWidth(200)
        self.setFixedHeight(120)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet(
            "font-size: 11px; font-weight: 600; color: #555;"
            "background: transparent;"
        )
        layout.addWidget(title_label)

        # Tips
        for tip in tips:
            tip_label = QLabel(tip)
            tip_label.setWordWrap(True)
            tip_label.setStyleSheet(
                "font-size: 10px; color: #777; background: transparent;"
                "padding-left: 4px;"
            )
            layout.addWidget(tip_label)

        layout.addStretch()
