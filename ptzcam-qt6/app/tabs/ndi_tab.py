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

"""NDI stream tab page with source discovery and video capture."""

import time
from typing import Optional, Callable

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame,
    QLabel, QPushButton, QComboBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QImage

from app.styles.theme import (
    get_primary_button_style, get_danger_button_style,
    get_standard_button_style,
)
from app.utils.network_utils import get_nic_choices
from app.utils.ndi_capture import NDISourceFinder, NDICapture, NDISource
from app.utils.logger import get_logger
from app.utils.i18n import tr
from app.widgets import ControlCard, HelpCard


class NDITab(QWidget):
    """NDI stream configuration tab with source discovery and video preview.

    Allows discovering NDI sources on the local network, selecting one,
    and receiving real-time video.
    """

    _DISCOVER_TIMEOUT_MS = 2000

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize the NDI tab.

        Args:
            parent: Optional parent widget.
        """
        super().__init__(parent)
        self._logger = get_logger(__name__)

        # Callbacks (set externally)
        self.on_status_update: Optional[Callable[[str], None]] = None
        self.on_visca_address: Optional[Callable[[str], None]] = None
        self.preview_widget: Optional[QWidget] = None
        self._on_video_info: Optional[Callable] = None

        # NDI discovery
        self._finder: Optional[NDISourceFinder] = None
        self._discovered_sources: list[NDISource] = []

        # NDI capture
        self._ndi_capture = NDICapture(self)
        self._ndi_capture.frame_ready.connect(self._on_frame_ready)
        self._ndi_capture.error_occurred.connect(self._on_error)
        self._ndi_capture.state_changed.connect(self._on_state_changed)

        # FPS calculation
        self._frame_times: list[float] = []
        self._is_playing: bool = False
        self._last_video_info = (0, 0, "", 0.0, 0, "", 0.0)

        # UI references
        self._src_combo: Optional[QComboBox] = None
        self._net_combo: Optional[QComboBox] = None
        self._refresh_btn: Optional[QPushButton] = None
        self._connect_btn: Optional[QPushButton] = None
        self._disconnect_btn: Optional[QPushButton] = None
        self._preview_placeholder: Optional[QWidget] = None

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the tab UI layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 8)
        layout.setSpacing(8)

        top_row = QHBoxLayout()
        top_row.setSpacing(8)
        card = self._create_control_card()
        top_row.addWidget(card, 1)
        top_row.addWidget(self._create_help_card())
        layout.addLayout(top_row)

        self._preview_placeholder = QWidget()
        layout.addWidget(self._preview_placeholder, 1)

    def _create_help_card(self) -> QWidget:
        """Create help card with usage instructions."""
        return HelpCard(tr("NDI 使用说明"), [
            tr("1. 点击「刷新」搜索网络 NDI 源"),
            tr("2. 下拉选择目标 NDI 设备"),
            tr("3. 点击「连接」开始接收视频"),
            tr("4. 非授权设备 15 分钟后可能断流"),
            tr("5. 5 秒无帧将提示可能为试用版"),
        ])

    def _create_control_card(self) -> QWidget:
        """Create the control card with NDI controls.

        Returns:
            Configured control card widget.
        """
        card = ControlCard()

        # Source row
        row = card.add_row()
        row.addWidget(ControlCard.make_label("NDI 源:"))

        self._src_combo = ControlCard.make_combo(280)
        self._src_combo.addItem("(点击刷新搜索 NDI 源)")
        row.addWidget(self._src_combo)

        self._refresh_btn = QPushButton("刷新")
        self._refresh_btn.setStyleSheet(get_standard_button_style())
        self._refresh_btn.clicked.connect(self._discover_sources)
        row.addWidget(self._refresh_btn)

        self._connect_btn = QPushButton("连接")
        self._connect_btn.setStyleSheet(get_primary_button_style())
        self._connect_btn.clicked.connect(self._connect_ndi)
        self._connect_btn.setEnabled(False)
        row.addWidget(self._connect_btn)

        self._disconnect_btn = QPushButton("断开")
        self._disconnect_btn.setStyleSheet(get_danger_button_style())
        self._disconnect_btn.clicked.connect(self._disconnect_ndi)
        self._disconnect_btn.setEnabled(False)
        row.addWidget(self._disconnect_btn)
        ControlCard.add_stretch(row)

        # NIC row
        row = card.add_row()
        row.addWidget(ControlCard.make_label("网卡:"))
        self._net_combo = ControlCard.make_combo(280)
        row.addWidget(self._net_combo)
        ControlCard.add_stretch(row)

        # Populate NIC choices
        self._refresh_nic_list()

        return card

    def _refresh_nic_list(self) -> None:
        """Refresh the network interface combo box."""
        if self._net_combo is None:
            return
        self._net_combo.clear()
        for choice in get_nic_choices():
            self._net_combo.addItem(choice)

    def set_preview_widget(self, widget: QWidget) -> None:
        """Set the video preview widget (called by main window).

        Args:
            widget: Preview widget to display.
        """
        layout = self.layout()
        if self._preview_placeholder:
            layout.removeWidget(self._preview_placeholder)
            self._preview_placeholder.deleteLater()
            self._preview_placeholder = None
        layout.addWidget(widget, 1)
        self.preview_widget = widget

    # ------------------------------------------------------------------
    # Source discovery
    # ------------------------------------------------------------------

    def _discover_sources(self) -> None:
        """Discover NDI sources on the network."""
        self._notify_status("搜索 NDI 源...")
        if self._refresh_btn:
            self._refresh_btn.setEnabled(False)
        if self._connect_btn:
            self._connect_btn.setEnabled(False)

        # Run discovery in background via timer to keep UI responsive
        QTimer.singleShot(0, self._do_discover)

    def _do_discover(self) -> None:
        """Perform the actual NDI source discovery."""
        self._logger.info("Starting NDI source discovery")

        # Clean up previous finder
        if self._finder:
            self._finder.close()
            self._finder = None

        self._finder = NDISourceFinder()
        if not self._finder.open():
            self._notify_status("NDI 初始化失败")
            self._refresh_btn.setEnabled(True)
            return

        sources = self._finder.discover(self._DISCOVER_TIMEOUT_MS)
        self._discovered_sources = sources

        # Update combo box
        if self._src_combo:
            self._src_combo.clear()
            if sources:
                for src in sources:
                    display = src.url if src.url else src.name
                    self._src_combo.addItem(f"{src.name}  ({display})")
                self._src_combo.setCurrentIndex(0)
                self._connect_btn.setEnabled(True)
                self._notify_status(f"发现 {len(sources)} 个 NDI 源")
                self._logger.info(f"Discovered {len(sources)} NDI source(s)")
            else:
                self._src_combo.addItem("(未发现 NDI 源)")
                self._notify_status("未发现 NDI 源")

        if self._refresh_btn:
            self._refresh_btn.setEnabled(True)

    # ------------------------------------------------------------------
    # Connection control
    # ------------------------------------------------------------------

    def _connect_ndi(self) -> None:
        """Connect to the selected NDI source."""
        if not self._src_combo or not self._discovered_sources:
            return

        idx = self._src_combo.currentIndex()
        if idx < 0 or idx >= len(self._discovered_sources):
            self._notify_status("请先选择 NDI 源")
            return

        source = self._discovered_sources[idx]
        self._logger.info(f"Connecting to NDI source: {source.name}")

        # Auto-fill VISCA address with NDI source IP
        if self.on_visca_address:
            ip_candidate = source.url.strip() if source.url else ""
            if ip_candidate:
                from urllib.parse import urlparse
                # NDI URL formats: "ip", "ip:port", "tcp://ip:port"
                if "://" in ip_candidate:
                    parsed = urlparse(ip_candidate)
                    ip_candidate = parsed.hostname or ip_candidate
                else:
                    # Strip port if present (e.g. "192.168.1.100:5960")
                    if ":" in ip_candidate:
                        ip_candidate = ip_candidate.split(":")[0]
                self.on_visca_address(ip_candidate)

        # Hide placeholder
        if hasattr(self.preview_widget, 'hide_placeholder'):
            self.preview_widget.hide_placeholder()

        # Disable controls
        self._set_controls_enabled(False)

        # Start capture
        self._ndi_capture.start(source)

    def _disconnect_ndi(self) -> None:
        """Disconnect from the current NDI source."""
        self._logger.info("Disconnecting NDI")
        self._ndi_capture.stop()
        self._update_ui_stopped()

    # ------------------------------------------------------------------
    # Frame handling
    # ------------------------------------------------------------------

    def _on_frame_ready(self, image: QImage, capture_time: float) -> None:
        """Handle incoming NDI video frame.

        Args:
            image: Video frame as QImage.
            capture_time: perf_counter() at frame capture time.
        """
        if not self._is_playing:
            return

        now = time.perf_counter()
        latency_ms = int((now - capture_time) * 1000)

        # Real-time FPS via sliding window
        self._frame_times.append(now)
        if len(self._frame_times) > 30:
            self._frame_times.pop(0)

        real_fps = 0.0
        if len(self._frame_times) >= 2:
            elapsed = self._frame_times[-1] - self._frame_times[0]
            if elapsed > 0:
                real_fps = (len(self._frame_times) - 1) / elapsed

        # Report video info every 10 frames
        if self._on_video_info and len(self._frame_times) % 10 == 0:
            w, h = image.width(), image.height()
            self._last_video_info = (w, h, "BGRA", real_fps, latency_ms, "NDI (SDK v6)", 0.0)
            self._on_video_info(
                w, h,
                "BGRA", real_fps, latency_ms,
                "NDI (SDK v6)", 0.0
            )

        # Display on preview widget
        if not self.preview_widget:
            return
        if not hasattr(self.preview_widget, 'set_video_frame'):
            return

        try:
            from PySide6.QtGui import QPixmap
            pixmap = QPixmap.fromImage(image)
            if pixmap.isNull():
                return

            target_size = self.preview_widget.video_frame.size()
            scaled = pixmap.scaled(
                target_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.preview_widget.set_video_frame(scaled)

        except Exception as e:
            self._logger.error(f"Error displaying NDI frame: {e}")

    def _on_error(self, error: str) -> None:
        """Handle NDI capture errors.

        Args:
            error: Error description.
        """
        self._logger.error(f"NDI error: {error}")
        # License timeout / no-frame errors: show overlay on preview
        if "授权" in error or "试用" in error or "5秒" in error:
            if hasattr(self.preview_widget, 'show_overlay'):
                self.preview_widget.show_overlay(error)
        else:
            self._notify_status(f"错误: {error}")

    def _on_state_changed(self, state: str) -> None:
        """Handle NDI capture state changes.

        Args:
            state: New state string.
        """
        self._logger.info(f"NDI state: {state}")

        if state == 'connecting':
            self._notify_status("正在连接 NDI...")
        elif state == 'connected':
            self._is_playing = True
            self._notify_status("NDI 已连接")
            if self._connect_btn:
                self._connect_btn.setText(tr("已连接"))
                self._connect_btn.setEnabled(False)
            if self._disconnect_btn:
                self._disconnect_btn.setEnabled(True)
        elif state == 'disconnected':
            self._update_ui_stopped()
            self._notify_status("NDI 已断开")
        elif state == 'error':
            self._update_ui_stopped()

    def _update_ui_stopped(self) -> None:
        """Restore UI to stopped/disconnected state."""
        self._is_playing = False

        if hasattr(self.preview_widget, 'show_placeholder'):
            self.preview_widget.show_placeholder()
        if hasattr(self.preview_widget, 'hide_overlay'):
            self.preview_widget.hide_overlay()

        self._set_controls_enabled(True)

        if self._connect_btn:
            self._connect_btn.setText(tr("连接"))
            self._connect_btn.setEnabled(len(self._discovered_sources) > 0)
        if self._disconnect_btn:
            self._disconnect_btn.setEnabled(False)

        self._frame_times.clear()
        self._last_video_info = (0, 0, "", 0.0, 0, "", 0.0)
        if self._on_video_info:
            self._on_video_info(0, 0, "", 0.0, 0, "", 0.0)

    def _set_controls_enabled(self, enabled: bool) -> None:
        """Enable or disable input controls.

        Args:
            enabled: True to enable, False to disable.
        """
        if self._src_combo:
            self._src_combo.setEnabled(enabled)
        if self._refresh_btn:
            self._refresh_btn.setEnabled(enabled)
        if self._net_combo:
            self._net_combo.setEnabled(enabled)

    def _notify_status(self, message: str) -> None:
        """Send status update to the main window status bar.

        Args:
            message: Status message text.
        """
        if self.on_status_update:
            self.on_status_update(message)

    def refresh_language(self) -> None:
        """Update all UI text for current language."""
        from app.utils.i18n import refresh_widget
        refresh_widget(self)

    def set_status_callback(self, callback: Callable[[str], None]) -> None:
        """Set the status update callback.

        Args:
            callback: Function to call when status needs updating.
        """
        self.on_status_update = callback

    def set_video_info_callback(self, callback: Callable) -> None:
        """Set callback for video frame info updates.

        Args:
            callback: Video info callback function.
        """
        self._on_video_info = callback

    def get_last_video_info(self) -> tuple:
        """Get the most recently reported video information.

        Returns:
            Tuple of (width, height, format, fps, latency, decode, cpu).
        """
        return self._last_video_info
