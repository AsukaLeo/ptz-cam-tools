"""PTZ control panel widget."""

from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QWidget
)
from PySide6.QtCore import Qt
from typing import Optional, Callable

from app.styles.theme import get_ptz_panel_style, get_standard_button_style
from app.utils.constants import PTZ_UP, PTZ_DOWN, PTZ_LEFT, PTZ_RIGHT, PTZ_STOP, PTZ_HOME


class PTZPanel(QFrame):
    """PTZ (Pan-Tilt-Zoom) control panel widget.

    Provides directional pad controls, zoom/focus buttons, and home/stop buttons.
    When a ViscaController is set, buttons issue real VISCA commands.
    """

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

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the panel UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignTop)

        # Title
        title = QLabel("PTZ 控制")
        title.setStyleSheet("""
            QLabel {
                font-size: 12px; font-weight: 500; color: #555;
                background: transparent;
            }
        """)
        layout.addWidget(title)

        # Controls layout
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(16)
        controls_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        # Directional pad (3x3 grid)
        controls_layout.addLayout(self._create_dpad())

        # Zoom / Focus controls
        controls_layout.addLayout(self._create_zoom_focus_controls())

        # Home / Stop buttons
        controls_layout.addLayout(self._create_home_stop_controls())

        controls_layout.addStretch()
        layout.addLayout(controls_layout)

    def set_controller(self, controller: 'ViscaController') -> None:
        """Set the VISCA controller for issuing real commands.

        Args:
            controller: ViscaController instance.
        """
        self._controller = controller

    def _create_dpad(self) -> QGridLayout:
        """Create the 3x3 directional pad layout.

        Returns:
            QGridLayout with directional buttons.
        """
        dpad = QGridLayout()
        dpad.setSpacing(2)

        # Direction buttons - call controller when available
        dpad.addWidget(self._create_ptz_btn("↖"), 0, 0)
        dpad.addWidget(
            self._create_ptz_btn("▲", lambda: self._do_ptz(0, -1)),
            0, 1
        )
        dpad.addWidget(self._create_ptz_btn("↗"), 0, 2)
        dpad.addWidget(
            self._create_ptz_btn("◀", lambda: self._do_ptz(-1, 0)),
            1, 0
        )

        # Center stop button
        center_btn = self._create_ptz_btn("●", lambda: self._do_stop())
        center_btn.setStyleSheet("""
            QPushButton {
                font-size: 10px; padding: 0; border: 1px solid #aaa;
                border-radius: 6px; background: #e0e0e0; color: #888;
            }
            QPushButton:hover { background: #d0d0d0; }
        """)
        dpad.addWidget(center_btn, 1, 1)

        dpad.addWidget(
            self._create_ptz_btn("▶", lambda: self._do_ptz(1, 0)),
            1, 2
        )
        dpad.addWidget(self._create_ptz_btn("↙"), 2, 0)
        dpad.addWidget(
            self._create_ptz_btn("▼", lambda: self._do_ptz(0, 1)),
            2, 1
        )
        dpad.addWidget(self._create_ptz_btn("↘"), 2, 2)

        return dpad

    def _create_zoom_focus_controls(self) -> QVBoxLayout:
        """Create zoom and focus control buttons.

        Returns:
            QVBoxLayout with zoom/focus buttons.
        """
        zf_layout = QVBoxLayout()
        zf_layout.setSpacing(8)

        zr = QHBoxLayout()
        zr.setSpacing(8)
        zr.addWidget(self._create_ctrl_btn("Zoom+", lambda: self._do_zoom(3)))
        zr.addWidget(self._create_ctrl_btn("Focus+", lambda: self._do_focus(3)))
        zf_layout.addLayout(zr)

        fr = QHBoxLayout()
        fr.setSpacing(8)
        fr.addWidget(self._create_ctrl_btn("Zoom-", lambda: self._do_zoom(-3)))
        fr.addWidget(self._create_ctrl_btn("Focus-", lambda: self._do_focus(-3)))
        zf_layout.addLayout(fr)

        return zf_layout

    def _create_home_stop_controls(self) -> QVBoxLayout:
        """Create home and stop buttons.

        Returns:
            QVBoxLayout with home/stop buttons.
        """
        hs = QVBoxLayout()
        hs.setSpacing(8)

        hs.addWidget(self._create_wide_btn(PTZ_HOME, lambda: self._do_home()))
        hs.addWidget(self._create_wide_btn(PTZ_STOP, lambda: self._do_stop()))

        return hs

    def _create_ptz_btn(self, text: str, callback: Optional[Callable] = None) -> QPushButton:
        """Create a PTZ direction button.

        Args:
            text: Button text.
            callback: Optional click callback.

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
        if callback:
            btn.clicked.connect(callback)
        return btn

    def _create_ctrl_btn(self, text: str, callback: Callable) -> QPushButton:
        """Create a control button (Zoom/Focus).

        Args:
            text: Button text.
            callback: Click callback.

        Returns:
            Configured QPushButton.
        """
        btn = QPushButton(text)
        btn.setFixedWidth(80)
        btn.setStyleSheet(get_standard_button_style())
        btn.clicked.connect(callback)
        return btn

    def _create_wide_btn(self, text: str, callback: Callable) -> QPushButton:
        """Create a wide control button (Home/Stop).

        Args:
            text: Button text.
            callback: Click callback.

        Returns:
            Configured QPushButton.
        """
        btn = QPushButton(text)
        btn.setFixedWidth(100)
        btn.setStyleSheet(get_standard_button_style())
        btn.clicked.connect(callback)
        return btn

    # ------------------------------------------------------------------
    # VISCA command dispatch
    # ------------------------------------------------------------------

    def _do_ptz(self, pan_dir: int, tilt_dir: int) -> None:
        """Execute pan/tilt command.

        Args:
            pan_dir: -1=left, 0=center, 1=right.
            tilt_dir: -1=up, 0=center, 1=down.
        """
        pdir = {0: 0, -1: 1, 1: 2}.get(pan_dir, 0)  # stop, left, right
        tdir = {0: 0, -1: 3, 1: 1}.get(tilt_dir, 0)  # stop, up, down

        if self._controller and self._controller.is_connected:
            self._controller.pan_tilt(pan_dir=pdir, tilt_dir=tdir)
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

    def _do_zoom(self, speed: int) -> None:
        """Execute zoom command.

        Args:
            speed: Positive=tele, negative=wide.
        """
        if self._controller and self._controller.is_connected:
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
