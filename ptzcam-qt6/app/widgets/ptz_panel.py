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

"""PTZ control panel widget."""

from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QSlider, QSpinBox, QWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIntValidator
from typing import Optional, Callable

from app.styles.theme import get_ptz_panel_style
from app.utils.i18n import tr, on_language_change

class PTZPanel(QFrame):
    """PTZ (Pan-Tilt-Zoom) control panel widget.

    Provides directional pad, zoom/focus buttons, preset management,
    and speed sliders.
    When a ViscaController is set, buttons issue real VISCA commands.
    """

    # Sony VISCA standard speed ranges
    PTZ_SPEED_MIN = 1
    PTZ_SPEED_MAX = 24
    PTZ_SPEED_DEFAULT = 12
    ZOOM_SPEED_MIN = 1
    ZOOM_SPEED_MAX = 7
    ZOOM_SPEED_DEFAULT = 4

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize the PTZ panel.

        Args:
            parent: Optional parent widget.
        """
        super().__init__(parent)
        self.setObjectName("ptzPanel")
        self.setStyleSheet(get_ptz_panel_style())

        self.on_status_update: Optional[Callable[[str], None]] = None
        self._controller: Optional['ViscaController'] = None

        # Current speed values (updated by sliders)
        self._ptz_speed = self.PTZ_SPEED_DEFAULT
        self._zoom_speed = self.ZOOM_SPEED_DEFAULT

        # Preset selection
        self._selected_preset_id = -1

        self._setup_ui()
        self.set_connected(False)  # Start disabled until VISCA connects

    def refresh_language(self) -> None:
        """Update all UI text for current language."""
        from app.utils.i18n import refresh_widget
        refresh_widget(self)

    def _setup_ui(self) -> None:
        """Set up the panel UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignTop)

        # Title
        self._title_label = QLabel(tr("PTZ 控制"))
        self._title_label.setStyleSheet("""
            QLabel {
                font-size: 12px; font-weight: 500; color: #555;
                background: transparent;
            }
        """)
        layout.addWidget(self._title_label)

        # Top row: direction group (left) | zoom/focus (right)
        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        dpad = self._create_dpad()
        dpad.setAlignment(Qt.AlignCenter)
        top_row.addLayout(dpad)

        top_row.addLayout(self._create_zoom_focus_controls())

        layout.addLayout(top_row)

        # Preset controls
        layout.addLayout(self._create_preset_controls())

        # Speed sliders
        layout.addLayout(self._create_speed_sliders())

    def set_controller(self, controller: 'ViscaController') -> None:
        """Set the VISCA controller for issuing real commands.

        Args:
            controller: ViscaController instance.
        """
        self._controller = controller

    def set_connected(self, connected: bool) -> None:
        """Enable/disable all PTZ controls based on VISCA connection state.

        Args:
            connected: True if connected, False if disconnected.
        """
        for child in self.findChildren(QPushButton):
            child.setEnabled(connected)
        for child in self.findChildren(QSlider):
            child.setEnabled(connected)
        for child in self.findChildren(QSpinBox):
            child.setEnabled(connected)
        for child in self.findChildren(QLineEdit):
            child.setEnabled(connected)

    # ------------------------------------------------------------------
    # D-pad
    # ------------------------------------------------------------------

    def _create_dpad(self) -> QGridLayout:
        """Create the 3x3 directional pad layout with press/release control.

        Center button = Home (click to go home).

        Returns:
            QGridLayout with directional buttons.
        """
        dpad = QGridLayout()
        dpad.setSpacing(2)

        dpad.addWidget(
            self._create_dir_btn("↖", lambda: self._do_ptz(-1, -1),
                                 lambda: self._do_stop()), 0, 0)
        dpad.addWidget(
            self._create_dir_btn("▲", lambda: self._do_ptz(0, -1),
                                 lambda: self._do_stop()), 0, 1)
        dpad.addWidget(
            self._create_dir_btn("↗", lambda: self._do_ptz(1, -1),
                                 lambda: self._do_stop()), 0, 2)
        dpad.addWidget(
            self._create_dir_btn("◀", lambda: self._do_ptz(-1, 0),
                                 lambda: self._do_stop()), 1, 0)

        # Center Home button
        center_btn = QPushButton("Home")
        center_btn.setFixedSize(32, 28)
        center_btn.setStyleSheet("""
            QPushButton {
                font-size: 9px; padding: 0; border: 1px solid #888;
                border-radius: 6px; background: #e0e0e0; color: #444;
                font-weight: 600;
            }
            QPushButton:hover { background: #d0d0d0; }
        """)
        center_btn.clicked.connect(self._do_home)
        dpad.addWidget(center_btn, 1, 1)

        dpad.addWidget(
            self._create_dir_btn("▶", lambda: self._do_ptz(1, 0),
                                 lambda: self._do_stop()), 1, 2)
        dpad.addWidget(
            self._create_dir_btn("↙", lambda: self._do_ptz(-1, 1),
                                 lambda: self._do_stop()), 2, 0)
        dpad.addWidget(
            self._create_dir_btn("▼", lambda: self._do_ptz(0, 1),
                                 lambda: self._do_stop()), 2, 1)
        dpad.addWidget(
            self._create_dir_btn("↘", lambda: self._do_ptz(1, 1),
                                 lambda: self._do_stop()), 2, 2)

        return dpad

    # ------------------------------------------------------------------
    # Zoom / Focus
    # ------------------------------------------------------------------

    def _create_zoom_focus_controls(self) -> QVBoxLayout:
        """Create zoom and focus control buttons.

        Returns:
            QVBoxLayout with zoom/focus buttons.
        """
        zf = QVBoxLayout()
        zf.setSpacing(4)

        zr = QHBoxLayout()
        zr.setSpacing(4)
        zr.addWidget(self._create_press_btn(tr("变焦+"), lambda: self._do_zoom(1),
                                            lambda: self._do_zoom(0)))
        zr.addWidget(self._create_press_btn(tr("聚焦+"), lambda: self._do_focus(3),
                                            lambda: self._do_focus(0)))
        zf.addLayout(zr)

        fr = QHBoxLayout()
        fr.setSpacing(4)
        fr.addWidget(self._create_press_btn(tr("变焦-"), lambda: self._do_zoom(-1),
                                            lambda: self._do_zoom(0)))
        fr.addWidget(self._create_press_btn(tr("聚焦-"), lambda: self._do_focus(-3),
                                            lambda: self._do_focus(0)))
        zf.addLayout(fr)

        # Auto / Manual focus mode buttons  
        af_row = QHBoxLayout()
        af_row.setSpacing(4)
        af_row.addWidget(self._create_click_btn(tr("自动聚焦"), self._do_auto_focus))
        af_row.addWidget(self._create_click_btn(tr("手动聚焦"), self._do_manual_focus_mode))
        zf.addLayout(af_row)

        return zf

    # ------------------------------------------------------------------
    # Preset controls
    # ------------------------------------------------------------------

    def _create_preset_controls(self) -> QVBoxLayout:
        """Create preset management (0-9 numbers + manual address input).

        Numbers are compact and right-aligned. To the right of the
        number grid is a manual address input (0-254) with range label
        above. Manual address and 0-9 grid are mutually exclusive.

        Returns:
            QVBoxLayout with preset buttons and address input.
        """
        outer = QVBoxLayout()
        outer.setSpacing(6)

        label = QLabel(tr("预置位"))
        label.setStyleSheet(
            "font-size: 11px; color: #666; background: transparent;"
        )
        outer.addWidget(label)

        # Row: compact number grid + manual address input
        preset_row = QHBoxLayout()
        preset_row.setSpacing(8)

        # 0-9 number grid (2 rows × 5 cols, tight)
        grid = QGridLayout()
        grid.setSpacing(1)
        self._preset_btns: list[QPushButton] = []
        for i in range(10):
            btn = self._create_preset_num_btn(str(i))
            btn.clicked.connect(lambda checked, p=i: self._select_preset(p))
            self._preset_btns.append(btn)
            grid.addWidget(btn, i // 5, i % 5)
        preset_row.addLayout(grid)
        preset_row.addStretch()

        # Manual address input (empty by default, range 0-254)
        addr_group = QVBoxLayout()
        addr_group.setSpacing(2)

        range_label = QLabel("0 ~ 254")
        range_label.setStyleSheet(
            "font-size: 9px; color: #999; background: transparent;"
        )
        addr_group.addWidget(range_label)

        self._addr_input = QLineEdit()
        self._addr_input.setFixedWidth(54)
        self._addr_input.setPlaceholderText("")
        self._addr_input.setValidator(QIntValidator(0, 254))
        self._addr_input.setStyleSheet("""
            QLineEdit {
                font-size: 11px; padding: 1px 4px;
                border: 1px solid #aaa; border-radius: 3px;
                background: #fff; color: #333;
            }
        """)
        self._addr_input.textChanged.connect(self._on_manual_addr_changed)
        addr_group.addWidget(self._addr_input)

        preset_row.addLayout(addr_group)
        outer.addLayout(preset_row)

        # Action buttons row
        action_row = QHBoxLayout()
        action_row.setSpacing(4)

        set_btn = self._create_preset_action_btn(tr("设置"))
        set_btn.clicked.connect(self._on_set_preset)
        action_row.addWidget(set_btn)

        clear_btn = self._create_preset_action_btn(tr("清除"))
        clear_btn.clicked.connect(self._on_clear_preset)
        action_row.addWidget(clear_btn)

        recall_btn = self._create_preset_action_btn(tr("调用"))
        recall_btn.clicked.connect(self._on_recall_preset)
        action_row.addWidget(recall_btn)

        outer.addLayout(action_row)
        return outer

    def _create_preset_num_btn(self, text: str) -> QPushButton:
        """Create a preset number button (0-9).

        Args:
            text: Button text.

        Returns:
            Configured QPushButton.
        """
        btn = QPushButton(text)
        btn.setFixedSize(28, 24)
        btn.setStyleSheet("""
            QPushButton {
                font-size: 10px; padding: 0; border: 1px solid #aaa;
                border-radius: 4px; background: #f5f5f5; color: #333;
            }
            QPushButton:hover { background: #e5e5e5; }
            QPushButton:checked { background: #c8e6c9; border-color: #4caf50; }
        """)
        btn.setCheckable(True)
        return btn

    def _create_preset_action_btn(self, text: str) -> QPushButton:
        """Create a preset action button (设置/清除/调用).

        Args:
            text: Button text.

        Returns:
            Configured QPushButton.
        """
        btn = QPushButton(text)
        btn.setFixedSize(44, 24)
        btn.setStyleSheet("""
            QPushButton {
                font-size: 10px; padding: 0 2px; border: 1px solid #aaa;
                border-radius: 4px; background: #f5f5f5; color: #333;
            }
            QPushButton:hover { background: #e5e5e5; }
            QPushButton:pressed { background: #d5d5d5; }
        """)
        return btn

    def _selected_preset(self) -> int:
        """Get the currently selected preset number (0-9).

        Returns:
            Selected preset number, or -1 if none selected.
        """
        return self._selected_preset_id

    def _select_preset(self, preset_id: int) -> None:
        """Select a preset number and update button highlight.

        Also clears the manual address input (mutual exclusion).

        Args:
            preset_id: Preset number (0-9).
        """
        self._selected_preset_id = preset_id
        for i, btn in enumerate(self._preset_btns):
            btn.setChecked(i == preset_id)
        # Clear manual address (block signals to avoid triggering
        # _on_manual_addr_changed which would re-clear the grid)
        self._addr_input.blockSignals(True)
        self._addr_input.clear()
        self._addr_input.blockSignals(False)

    def _manual_addr_value(self) -> int:
        """Get the manual address input value.

        Returns:
            Address value (0-254), or -1 if empty/invalid.
        """
        text = self._addr_input.text().strip()
        if not text:
            return -1
        try:
            val = int(text)
            if 0 <= val <= 254:
                return val
        except ValueError:
            pass
        return -1

    def _on_manual_addr_changed(self, text: str) -> None:
        """Clear 0-9 preset selection when manual address is entered.

        Ensures mutual exclusion: typing a manual address deselects
        the number grid.

        Args:
            text: Current text in the address input.
        """
        text = text.strip()
        if text:
            try:
                val = int(text)
                if 0 <= val <= 254:
                    self._selected_preset_id = -1
                    for btn in self._preset_btns:
                        btn.setChecked(False)
            except ValueError:
                pass

    def _get_preset_target(self) -> int:
        """Get the target preset number.

        Prefers manual address input over 0-9 grid selection.

        Returns:
            Preset number (0-255), or -1 if nothing selected.
        """
        manual = self._manual_addr_value()
        if manual >= 0:
            return manual
        return self._selected_preset_id

    def _on_set_preset(self) -> None:
        """Save current position to selected preset or manual address."""
        preset = self._get_preset_target()
        if preset < 0:
            self._notify_status("请先选择一个预置位编号或输入地址")
            return
        self._set_preset(preset)

    def _on_clear_preset(self) -> None:
        """Clear selected preset or manual address."""
        preset = self._get_preset_target()
        if preset < 0:
            self._notify_status("请先选择一个预置位编号或输入地址")
            return
        self._clear_preset(preset)

    def _on_recall_preset(self) -> None:
        """Recall selected preset or manual address."""
        preset = self._get_preset_target()
        if preset < 0:
            self._notify_status("请先选择一个预置位编号或输入地址")
            return
        self._recall_preset(preset)

    def _set_preset(self, preset_id: int) -> None:
        """Save preset.

        Args:
            preset_id: Preset number (0-9).
        """
        if self._controller and self._controller.is_connected:
            self._controller.preset_set(preset_id)
        else:
            self._notify_status("VISCA 未连接")

    def _clear_preset(self, preset_id: int) -> None:
        """Clear preset.

        Args:
            preset_id: Preset number (0-9).
        """
        if self._controller and self._controller.is_connected:
            self._controller.preset_clear(preset_id)
        else:
            self._notify_status("VISCA 未连接")

    def _recall_preset(self, preset_id: int) -> None:
        """Recall preset and optionally update selection.

        Args:
            preset_id: Preset number (0-255).
        """
        # Only update grid selection for 0-9 presets
        if 0 <= preset_id <= 9:
            self._select_preset(preset_id)
        if self._controller and self._controller.is_connected:
            self._controller.preset_recall(preset_id)
        else:
            self._notify_status("VISCA 未连接")

    # ------------------------------------------------------------------
    # Speed sliders
    # ------------------------------------------------------------------

    def _create_speed_sliders(self) -> QHBoxLayout:
        """Create speed slider controls for PTZ and zoom.

        PTZ speed: 1~24 (Sony VISCA standard)
        Zoom speed: 1~7 (Sony VISCA standard)

        Returns:
            QHBoxLayout with slider widgets.
        """
        row = QHBoxLayout()
        row.setSpacing(16)

        # Pan/Tilt speed slider
        ptz_group = QVBoxLayout()
        ptz_group.setSpacing(2)
        ptz_label = QLabel(tr("云台速度"))
        ptz_label.setStyleSheet(
            "font-size: 11px; color: #666; background: transparent;"
        )
        ptz_group.addWidget(ptz_label)

        slider_row = QHBoxLayout()
        slider_row.setSpacing(4)

        self._ptz_slider = QSlider(Qt.Horizontal)
        self._ptz_slider.setRange(self.PTZ_SPEED_MIN, self.PTZ_SPEED_MAX)
        self._ptz_slider.setValue(self.PTZ_SPEED_DEFAULT)
        self._ptz_slider.setFixedWidth(120)
        self._ptz_slider.valueChanged.connect(self._on_ptz_speed_changed)
        slider_row.addWidget(self._ptz_slider)

        self._ptz_speed_label = QLabel(str(self.PTZ_SPEED_DEFAULT))
        self._ptz_speed_label.setFixedWidth(20)
        self._ptz_speed_label.setStyleSheet(
            "font-size: 11px; color: #333; background: transparent;"
        )
        slider_row.addWidget(self._ptz_speed_label)

        ptz_group.addLayout(slider_row)
        row.addLayout(ptz_group)

        # Zoom speed slider
        zoom_group = QVBoxLayout()
        zoom_group.setSpacing(2)
        zoom_label = QLabel(tr("变焦速度"))
        zoom_label.setStyleSheet(
            "font-size: 11px; color: #666; background: transparent;"
        )
        zoom_group.addWidget(zoom_label)

        zslider_row = QHBoxLayout()
        zslider_row.setSpacing(4)

        self._zoom_slider = QSlider(Qt.Horizontal)
        self._zoom_slider.setRange(self.ZOOM_SPEED_MIN, self.ZOOM_SPEED_MAX)
        self._zoom_slider.setValue(self.ZOOM_SPEED_DEFAULT)
        self._zoom_slider.setFixedWidth(120)
        self._zoom_slider.valueChanged.connect(self._on_zoom_speed_changed)
        zslider_row.addWidget(self._zoom_slider)

        self._zoom_speed_label = QLabel(str(self.ZOOM_SPEED_DEFAULT))
        self._zoom_speed_label.setFixedWidth(20)
        self._zoom_speed_label.setStyleSheet(
            "font-size: 11px; color: #333; background: transparent;"
        )
        zslider_row.addWidget(self._zoom_speed_label)

        zoom_group.addLayout(zslider_row)
        row.addLayout(zoom_group)

        row.addStretch()
        return row

    def _on_ptz_speed_changed(self, value: int) -> None:
        """Update PTZ speed from slider."""
        self._ptz_speed = value
        self._ptz_speed_label.setText(str(value))

    def _on_zoom_speed_changed(self, value: int) -> None:
        """Update zoom speed from slider."""
        self._zoom_speed = value
        self._zoom_speed_label.setText(str(value))

    # ------------------------------------------------------------------
    # Button creation helpers
    # ------------------------------------------------------------------

    def _create_dir_btn(self, text: str,
                        on_press: Callable, on_release: Callable) -> QPushButton:
        """Create a direction button with press/release actions.

        Args:
            text: Button text.
            on_press: Start movement callback.
            on_release: Stop movement callback.

        Returns:
            Configured QPushButton.
        """
        btn = QPushButton(text)
        btn.setFixedSize(32, 28)
        btn.setStyleSheet("""
            QPushButton {
                font-size: 12px; padding: 0; border: 1px solid #aaa;
                border-radius: 6px; background: #f5f5f5; color: #333;
            }
            QPushButton:hover { background: #e5e5e5; }
            QPushButton:pressed { background: #d0d0d0; }
        """)
        btn.pressed.connect(on_press)
        btn.released.connect(on_release)
        return btn

    def _create_press_btn(self, text: str,
                          on_press: Callable, on_release: Callable) -> QPushButton:
        """Create a button with press/release for zoom/focus.

        Args:
            text: Button text.
            on_press: Start action callback.
            on_release: Stop action callback.

        Returns:
            Configured QPushButton.
        """
        btn = QPushButton(text)
        btn.setFixedWidth(64)
        btn.setStyleSheet("""
            QPushButton {
                font-size: 11px; padding: 2px 4px; border: 1px solid #aaa;
                border-radius: 6px; background: #f5f5f5; color: #333;
            }
            QPushButton:hover { background: #e5e5e5; }
            QPushButton:pressed { background: #d0d0d0; }
        """)
        btn.pressed.connect(on_press)
        btn.released.connect(on_release)
        return btn

    def _create_click_btn(self, text: str,
                          on_click: Callable) -> QPushButton:
        """Create a simple click button (for one-shot actions).

        Args:
            text: Button text.
            on_click: Click callback.

        Returns:
            Configured QPushButton.
        """
        btn = QPushButton(text)
        btn.setFixedWidth(64)
        btn.setStyleSheet("""
            QPushButton {
                font-size: 11px; padding: 2px 4px; border: 1px solid #aaa;
                border-radius: 6px; background: #f5f5f5; color: #333;
            }
            QPushButton:hover { background: #e5e5e5; }
            QPushButton:pressed { background: #d0d0d0; }
        """)
        btn.clicked.connect(on_click)
        return btn

    # ------------------------------------------------------------------
    # VISCA command dispatch
    # ------------------------------------------------------------------

    def _do_ptz(self, pan_dir: int, tilt_dir: int) -> None:
        """Execute pan/tilt using slider speed and standard Sony VISCA directions.

        Args:
            pan_dir: -1=left, 0=center, 1=right.
            tilt_dir: -1=up, 0=center, 1=down.
        """
        pdir = {0: 3, -1: 1, 1: 2}.get(pan_dir, 3)
        tdir = {0: 3, -1: 2, 1: 1}.get(tilt_dir, 3)

        if self._controller and self._controller.tilt_reverse:
            tdir = {1: 2, 2: 1}.get(tdir, tdir)

        if self._controller and self._controller.is_connected:
            self._controller.pan_tilt(
                pan_speed=self._ptz_speed,
                tilt_speed=self._ptz_speed,
                pan_dir=pdir, tilt_dir=tdir,
            )
        else:
            self._notify_status("VISCA 未连接")

    def _do_stop(self) -> None:
        """Stop pan/tilt movement."""
        if self._controller and self._controller.is_connected:
            self._controller.stop()
        else:
            self._notify_status("VISCA 未连接")

    def _do_home(self) -> None:
        """Go to home position."""
        if self._controller and self._controller.is_connected:
            self._controller.home()
        else:
            self._notify_status("VISCA 未连接")

    def _do_zoom(self, direction: int) -> None:
        """Execute zoom command using slider speed.

        Args:
            direction: 1=tele(in), -1=wide(out), 0=stop.
        """
        if self._controller and self._controller.is_connected:
            if direction == 0:
                self._controller.zoom(0)
            else:
                speed = self._zoom_speed if direction > 0 else -self._zoom_speed
                self._controller.zoom(speed)
        else:
            self._notify_status("VISCA 未连接")

    def _do_focus(self, speed: int) -> None:
        """Execute focus command.

        Args:
            speed: Positive=far, negative=near.
        """
        if self._controller and self._controller.is_connected:
            self._controller.focus(speed)
        else:
            self._notify_status("VISCA 未连接")

    def _do_auto_focus(self) -> None:
        """Enable continuous Auto Focus mode."""
        if self._controller and self._controller.is_connected:
            self._controller.set_focus_mode(auto=True)
            self._notify_status("自动聚焦已开启")
        else:
            self._notify_status("VISCA 未连接")

    def _do_manual_focus_mode(self) -> None:
        """Switch to manual focus mode."""
        if self._controller and self._controller.is_connected:
            self._controller.set_focus_mode(auto=False)
        else:
            self._notify_status("VISCA 未连接")

    def _notify_status(self, message: str) -> None:
        """Notify status update via callback."""
        if self.on_status_update:
            self.on_status_update(message)

    def set_status_callback(self, callback: Callable[[str], None]) -> None:
        """Set the status update callback."""
        self.on_status_update = callback
