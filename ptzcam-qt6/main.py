#!/usr/bin/env python3
import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QPushButton, QComboBox, QLineEdit, QTabWidget,
    QFrame, QStatusBar, QListWidget, QSizeGrip
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QResizeEvent


# ── 窗口比例常量 ──────────────────────────────────────────────
ASPECT_W = 16
ASPECT_H = 10
MIN_WIDTH = 800
MIN_HEIGHT = 500


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # 只禁用最大化，不影响最小化和关闭按钮
        self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, False)
        self.setWindowTitle("PTZ-Cam-Tools")

        # 在 setup_ui 之前初始化
        self._preview_frames = []
        self._preview_resolution = None
        self._resizing = False

        # 最小尺寸 & 默认 16:10
        self.setMinimumSize(MIN_WIDTH, MIN_HEIGHT)
        self.resize(960, 600)

        self.setup_ui()

    # ── 窗口比例约束 ────────────────────────────────────────────
    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        if self._resizing:
            return

        w = self.width()
        h = self.height()

        target_h = int(w * ASPECT_H / ASPECT_W)
        target_w = int(h * ASPECT_W / ASPECT_H)

        if abs(w * ASPECT_H - h * ASPECT_W) < abs(h * ASPECT_W - w * ASPECT_H):
            if h != target_h:
                self._resizing = True
                self.resize(w, target_h)
                self._resizing = False
        else:
            if w != target_w:
                self._resizing = True
                self.resize(target_w, h)
                self._resizing = False

        # 延迟更新预览区尺寸（等布局完成后再算）
        from PySide6.QtCore import QTimer
        QTimer.singleShot(0, self._update_preview_size)

    def sizeHint(self):
        return QSize(960, 600)

    # ── 预览区自适应分辨率接口 ─────────────────────────────────
    def set_preview_resolution(self, width: int, height: int):
        """外部调用设置视频预览区分辨率，预览区会自动适配比例"""
        self._preview_resolution = (width, height)
        self._update_preview_size()

    def _update_preview_size(self):
        """动态调整所有预览帧高度，按 16:9 比例"""
        for frame in self._preview_frames:
            if not frame.isVisible():
                continue

            parent = frame.parentWidget()
            if not parent:
                continue

            # 预览区宽度 = tab 页面宽度 - 32（左右 padding）
            content_w = parent.width() - 32
            # 高度按 16:9 比例
            target_h = int(content_w * 9 / 16)
            target_h = max(target_h, 120)

            frame.setFixedHeight(target_h)

    # ── UI 构建 ────────────────────────────────────────────────
    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 12, 0, 0)  # 顶部留 12px 给 Tab
        main_layout.setSpacing(0)

        # Tab widget
        self.create_tab_widget(main_layout)

        # PTZ Panel
        self.create_ptz_panel(main_layout)

        # Status bar
        self.status_label = QLabel("状态: 就绪")
        self.statusBar().addWidget(self.status_label)
        self.statusBar().addPermanentWidget(QSizeGrip(self))

    def create_tab_widget(self, parent_layout):
        self.tab_widget = QTabWidget()

        self.tab_widget.addTab(self.create_usb_tab(), "USB预览")
        self.tab_widget.addTab(self.create_rtsp_tab(), "RTSP")
        self.tab_widget.addTab(self.create_ndi_tab(), "NDI")
        self.tab_widget.addTab(self.create_onvif_tab(), "ONVIF")
        self.tab_widget.addTab(self.create_settings_tab(), "设置")

        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        parent_layout.addWidget(self.tab_widget, 1)  # stretch=1 让 tab 区域占满剩余空间

    def _create_preview(self):
        """创建视频预览区 — 宽度撑满，高度按 16:9 比例计算"""
        preview = QFrame()
        preview.setObjectName("preview")
        preview.setStyleSheet("""
            QFrame#preview {
                background-color: #1a1a1a;
                border: 2px solid #333;
                border-radius: 6px;
            }
        """)
        preview_layout = QVBoxLayout(preview)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        preview_layout.setAlignment(Qt.AlignCenter)
        lbl = QLabel("视频预览区")
        lbl.setStyleSheet("color: #666; font-size: 24px; background: transparent;")
        lbl.setAlignment(Qt.AlignCenter)
        preview_layout.addWidget(lbl)

        self._preview_frames.append(preview)
        return preview

    # ── 按钮工厂 ───────────────────────────────────────────────
    def _make_primary_btn(self, text, callback):
        btn = QPushButton(text)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #0078d4; color: #fff;
                border: 1px solid #0066b8; border-radius: 6px;
                padding: 5px 16px; font-size: 13px;
            }
            QPushButton:hover { background-color: #0066b8; }
            QPushButton:pressed { background-color: #005a9e; }
        """)
        btn.clicked.connect(callback)
        return btn

    def _make_danger_btn(self, text, callback):
        btn = QPushButton(text)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #c42b1c; color: #fff;
                border: 1px solid #a52010; border-radius: 6px;
                padding: 5px 16px; font-size: 13px;
            }
            QPushButton:hover { background-color: #a52010; }
            QPushButton:pressed { background-color: #8a1a0d; }
        """)
        btn.clicked.connect(callback)
        return btn

    def _make_control_card(self):
        """创建控件分组卡片 — 轻量浅灰背景，提供视觉分层"""
        card = QFrame()
        card.setObjectName("controlCard")
        card.setStyleSheet("""
            QFrame#controlCard {
                background-color: #f0f2f5;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
            }
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)
        return card, layout

    def _make_btn(self, text, callback=None):
        btn = QPushButton(text)
        btn.setStyleSheet("""
            QPushButton {
                background: #f5f5f5; border: 1px solid #aaa; border-radius: 6px;
                padding: 5px 16px; font-size: 13px; color: #333;
            }
            QPushButton:hover { background: #e5e5e5; }
            QPushButton:pressed { background: #d5d5d5; }
        """)
        if callback:
            btn.clicked.connect(callback)
        return btn

    def _make_combo(self, items, width=None):
        combo = QComboBox()
        combo.addItems(items)
        if width:
            combo.setFixedWidth(width)
        return combo

    # ── Tab 页面 ───────────────────────────────────────────────
    def create_usb_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(16, 12, 16, 8)
        layout.setSpacing(8)

        # 设备控制卡片
        card1, card1_layout = self._make_control_card()
        device_row = QHBoxLayout()
        device_row.setSpacing(8)
        device_label = QLabel("设备:")
        device_label.setFixedWidth(80)
        device_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        device_row.addWidget(device_label)
        device_row.addWidget(self._make_combo(["USB Camera (1)", "USB Camera (2)"], 200))
        device_row.addWidget(self._make_btn("刷新", lambda: self.update_status("刷新设备列表...")))
        device_row.addWidget(self._make_primary_btn("播放", lambda: self.update_status("播放中")))
        device_row.addStretch()
        card1_layout.addLayout(device_row)
        layout.addWidget(card1)

        # Preview — 不用 stretch，固定高度由 _update_preview_size 管理
        layout.addWidget(self._create_preview())

        # 参数控制卡片
        card2, card2_layout = self._make_control_card()
        control_row = QHBoxLayout()
        control_row.setSpacing(16)

        lbl1 = QLabel("分辨率:")
        lbl1.setFixedWidth(50)
        lbl1.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        c1 = self._make_combo(["1920 x 1080", "1280 x 720", "640 x 480"])

        lbl2 = QLabel("格式:")
        lbl2.setFixedWidth(50)
        lbl2.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        c2 = self._make_combo(["YUY2", "MJPEG", "H264"])

        lbl3 = QLabel("帧率:")
        lbl3.setFixedWidth(50)
        lbl3.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        c3 = self._make_combo(["30 fps", "25 fps", "15 fps"])

        control_row.addWidget(lbl1)
        control_row.addWidget(c1)
        control_row.addWidget(lbl2)
        control_row.addWidget(c2)
        control_row.addWidget(lbl3)
        control_row.addWidget(c3)
        control_row.addStretch()
        card2_layout.addLayout(control_row)
        layout.addWidget(card2)

        return page

    def create_rtsp_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(16, 12, 16, 8)
        layout.setSpacing(8)

        # 连接控制卡片
        card1, card1_layout = self._make_control_card()

        # URL row
        url_row = QHBoxLayout()
        url_row.setSpacing(8)
        url_label = QLabel("RTSP URL:")
        url_label.setFixedWidth(80)
        url_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        url_row.addWidget(url_label)
        url_edit = QLineEdit("rtsp://192.168.2.254/PSIA/Streaming/channels/h264")
        url_edit.setFixedWidth(350)
        url_row.addWidget(url_edit)
        url_row.addWidget(self._make_primary_btn("连接", lambda: self.update_status("连接中...")))
        url_row.addWidget(self._make_danger_btn("断开", lambda: self.update_status("已断开")))
        url_row.addStretch()
        card1_layout.addLayout(url_row)

        # Auth row
        auth_row = QHBoxLayout()
        auth_row.setSpacing(8)
        user_label = QLabel("用户名:")
        user_label.setFixedWidth(80)
        user_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        auth_row.addWidget(user_label)
        user_edit = QLineEdit()
        user_edit.setPlaceholderText("admin")
        user_edit.setFixedWidth(120)
        auth_row.addWidget(user_edit)
        pass_label = QLabel("密码:")
        pass_label.setFixedWidth(50)
        auth_row.addWidget(pass_label)
        pass_edit = QLineEdit()
        pass_edit.setEchoMode(QLineEdit.Password)
        pass_edit.setFixedWidth(120)
        auth_row.addWidget(pass_edit)
        auth_row.addStretch()
        card1_layout.addLayout(auth_row)

        # Network row
        net_row = QHBoxLayout()
        net_row.setSpacing(8)
        net_label = QLabel("网卡:")
        net_label.setFixedWidth(80)
        net_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        net_row.addWidget(net_label)
        net_row.addWidget(self._make_combo(["Realtek PCIe GbE - 192.168.1.100", "Intel Wi-Fi 6 - 192.168.1.101"], 220))
        net_row.addWidget(self._make_combo(["UDP", "TCP"]))
        net_row.addStretch()
        card1_layout.addLayout(net_row)

        layout.addWidget(card1)

        # Preview
        layout.addWidget(self._create_preview())

        return page

    def create_ndi_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(16, 12, 16, 8)
        layout.setSpacing(8)

        card, card_layout = self._make_control_card()
        src_row = QHBoxLayout()
        src_row.setSpacing(8)
        src_label = QLabel("NDI 源:")
        src_label.setFixedWidth(80)
        src_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        src_row.addWidget(src_label)
        src_row.addWidget(self._make_combo(["(未发现 NDI 源)"], 200))
        src_row.addWidget(self._make_btn("刷新", lambda: self.update_status("搜索 NDI 源...")))
        src_row.addWidget(self._make_primary_btn("连接", lambda: self.update_status("连接中...")))
        src_row.addWidget(self._make_danger_btn("断开", lambda: self.update_status("已断开")))
        src_row.addStretch()
        card_layout.addLayout(src_row)
        layout.addWidget(card)

        layout.addWidget(self._create_preview())
        return page

    def create_onvif_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(16, 12, 16, 8)
        layout.setSpacing(8)

        card, card_layout = self._make_control_card()

        ip_row = QHBoxLayout()
        ip_row.setSpacing(8)
        ip_label = QLabel("IP 地址:")
        ip_label.setFixedWidth(80)
        ip_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        ip_row.addWidget(ip_label)
        ip_edit = QLineEdit("192.168.1.64")
        ip_edit.setFixedWidth(120)
        ip_row.addWidget(ip_edit)
        port_label = QLabel("端口:")
        port_label.setFixedWidth(40)
        ip_row.addWidget(port_label)
        port_edit = QLineEdit("80")
        port_edit.setFixedWidth(60)
        ip_row.addWidget(port_edit)
        ip_row.addWidget(self._make_btn("发现", lambda: self.update_status("发现设备...")))
        ip_row.addWidget(self._make_primary_btn("连接", lambda: self.update_status("连接中...")))
        ip_row.addWidget(self._make_danger_btn("断开", lambda: self.update_status("已断开")))
        ip_row.addStretch()
        card_layout.addLayout(ip_row)

        auth_row = QHBoxLayout()
        auth_row.setSpacing(8)
        user_label = QLabel("用户名:")
        user_label.setFixedWidth(80)
        user_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        auth_row.addWidget(user_label)
        user_edit = QLineEdit("admin")
        user_edit.setFixedWidth(100)
        auth_row.addWidget(user_edit)
        pass_label = QLabel("密码:")
        pass_label.setFixedWidth(40)
        auth_row.addWidget(pass_label)
        pass_edit = QLineEdit()
        pass_edit.setEchoMode(QLineEdit.Password)
        pass_edit.setFixedWidth(100)
        auth_row.addWidget(pass_edit)
        auth_row.addStretch()
        card_layout.addLayout(auth_row)

        layout.addWidget(card)
        layout.addWidget(self._create_preview())
        return page

    def create_settings_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(20)

        ui_title = QLabel("界面设置")
        ui_title.setStyleSheet("font-weight: 500; border-bottom: 1px solid #eee; padding-bottom: 4px; background: transparent;")
        layout.addWidget(ui_title)

        lang_row = QHBoxLayout()
        lang_row.setSpacing(12)
        lang_label = QLabel("语言:")
        lang_label.setFixedWidth(100)
        lang_row.addWidget(lang_label)
        lang_row.addWidget(self._make_combo(["中文", "English"]))
        lang_row.addStretch()
        layout.addLayout(lang_row)

        net_title = QLabel("网络设置")
        net_title.setStyleSheet("font-weight: 500; border-bottom: 1px solid #eee; padding-bottom: 4px; background: transparent;")
        layout.addWidget(net_title)

        net_item_row = QHBoxLayout()
        net_item_row.setSpacing(12)
        avail_label = QLabel("可用网卡:")
        avail_label.setFixedWidth(100)
        net_item_row.addWidget(avail_label)

        device_list = QListWidget()
        device_list.setFixedHeight(80)
        device_list.addItem("✓ Realtek PCIe GbE - 192.168.1.100")
        device_list.addItem("  Intel Wi-Fi 6 - 192.168.1.101")
        device_list.addItem("  VirtualBox Host-Only - 192.168.56.1")
        device_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #aaa; border-radius: 6px;
                background: #fafafa; font-size: 12px; color: #555;
            }
        """)
        net_item_row.addWidget(device_list, 1)
        layout.addLayout(net_item_row)
        layout.addStretch()

        return page

    # ── PTZ 控制面板 ───────────────────────────────────────────
    def create_ptz_panel(self, parent_layout):
        ptz_panel = QFrame()
        ptz_panel.setObjectName("ptzPanel")
        ptz_panel.setStyleSheet("""
            QFrame#ptzPanel {
                background-color: #f8f8f8;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                margin-left: 16px;
                margin-right: 16px;
                margin-top: 0px;
                margin-bottom: 0px;
            }
        """)

        layout = QVBoxLayout(ptz_panel)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        title_label = QLabel("PTZ 控制")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 12px; font-weight: 500; color: #555;
                background: transparent;
            }
        """)
        layout.addWidget(title_label)

        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(16)
        controls_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        # Directional pad (3x3)
        dpad = QGridLayout()
        dpad.setSpacing(2)

        def ptz_btn(text, callback=None):
            b = QPushButton(text)
            b.setFixedSize(32, 28)
            b.setStyleSheet("""
                QPushButton {
                    font-size: 12px; padding: 0; border: 1px solid #aaa;
                    border-radius: 6px; background: #f5f5f5; color: #333;
                }
                QPushButton:hover { background: #e5e5e5; }
                QPushButton:pressed { background: #d0d0d0; }
            """)
            if callback:
                b.clicked.connect(callback)
            return b

        dpad.addWidget(ptz_btn("↖"), 0, 0)
        dpad.addWidget(ptz_btn("▲", lambda: self.update_status("PTZ 上")), 0, 1)
        dpad.addWidget(ptz_btn("↗"), 0, 2)
        dpad.addWidget(ptz_btn("◀", lambda: self.update_status("PTZ 左")), 1, 0)

        center = ptz_btn("●", lambda: self.update_status("PTZ 停止"))
        center.setStyleSheet("""
            QPushButton {
                font-size: 10px; padding: 0; border: 1px solid #aaa;
                border-radius: 6px; background: #e0e0e0; color: #888;
            }
            QPushButton:hover { background: #d0d0d0; }
        """)
        dpad.addWidget(center, 1, 1)

        dpad.addWidget(ptz_btn("▶", lambda: self.update_status("PTZ 右")), 1, 2)
        dpad.addWidget(ptz_btn("↙"), 2, 0)
        dpad.addWidget(ptz_btn("▼", lambda: self.update_status("PTZ 下")), 2, 1)
        dpad.addWidget(ptz_btn("↘"), 2, 2)

        controls_layout.addLayout(dpad)

        # Zoom / Focus
        zf_layout = QVBoxLayout()
        zf_layout.setSpacing(8)

        def ctrl_btn(text, callback):
            b = QPushButton(text)
            b.setFixedWidth(60)
            b.setStyleSheet("""
                QPushButton {
                    font-size: 11px; padding: 4px 8px;
                    border: 1px solid #aaa; border-radius: 6px;
                    background: #f5f5f5; color: #333;
                }
                QPushButton:hover { background: #e5e5e5; }
                QPushButton:pressed { background: #d5d5d5; }
            """)
            b.clicked.connect(callback)
            return b

        zr = QHBoxLayout()
        zr.setSpacing(8)
        zr.addWidget(ctrl_btn("Zoom+", lambda: self.update_status("Zoom +")))
        zr.addWidget(ctrl_btn("Zoom-", lambda: self.update_status("Zoom -")))
        zf_layout.addLayout(zr)

        fr = QHBoxLayout()
        fr.setSpacing(8)
        fr.addWidget(ctrl_btn("Focus+", lambda: self.update_status("Focus +")))
        fr.addWidget(ctrl_btn("Focus-", lambda: self.update_status("Focus -")))
        zf_layout.addLayout(fr)

        controls_layout.addLayout(zf_layout)

        # Home / Stop
        hs = QVBoxLayout()
        hs.setSpacing(8)

        def wide_btn(text, callback):
            b = QPushButton(text)
            b.setFixedWidth(100)
            b.setStyleSheet("""
                QPushButton {
                    font-size: 11px; padding: 4px 16px;
                    border: 1px solid #aaa; border-radius: 6px;
                    background: #f5f5f5; color: #333;
                }
                QPushButton:hover { background: #e5e5e5; }
                QPushButton:pressed { background: #d5d5d5; }
            """)
            b.clicked.connect(callback)
            return b

        hs.addWidget(wide_btn("Home", lambda: self.update_status("PTZ Home")))
        hs.addWidget(wide_btn("Stop", lambda: self.update_status("PTZ 停止")))
        controls_layout.addLayout(hs)

        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        parent_layout.addWidget(ptz_panel)

    # ── Tab 切换 / 状态 ────────────────────────────────────────
    def on_tab_changed(self, index):
        statuses = ["就绪", "未连接", "未连接", "未连接", "设置"]
        self.update_status(statuses[index] if index < len(statuses) else "就绪")
        # 切换 tab 后延迟更新预览区尺寸
        from PySide6.QtCore import QTimer
        QTimer.singleShot(0, self._update_preview_size)

    def update_status(self, text):
        self.status_label.setText(f"状态: {text}")


def main():
    import os
    # DPI 策略必须在创建 QApplication 之前设置
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)

    # 下拉箭头图标路径
    _arrow_svg = os.path.join(os.path.dirname(os.path.abspath(__file__)), "arrow_down.svg").replace("\\", "/")

    # 全局强制浅色主题
    app.setStyleSheet(f"""
        QWidget {{ color: #333; background-color: #fff; }}
        QPushButton {{ color: #333; background-color: #f5f5f5; }}
        QLabel {{ color: #333; background-color: transparent; }}
        QLineEdit {{ color: #333; background-color: #fff; }}

        /* ── ComboBox：使用 SVG 标准箭头 ── */
        QComboBox {{
            color: #333; background-color: #fff;
            border: 1px solid #aaa; border-radius: 6px;
            padding: 4px 28px 4px 8px;
        }}
        QComboBox::drop-down {{
            border: none; width: 24px;
            subcontrol-origin: padding;
            subcontrol-position: top right;
        }}
        QComboBox::down-arrow {{
            image: url({_arrow_svg});
            width: 12px; height: 8px;
        }}
        QComboBox QAbstractItemView {{
            color: #333; background-color: #fff; border: 1px solid #aaa; border-radius: 6px;
            selection-background-color: #0078d4; selection-color: #fff;
            outline: none;
        }}
        QComboBox QAbstractItemView::item {{
            padding: 4px 8px; min-height: 24px;
        }}
        QComboBox QAbstractItemView::item:hover {{
            background-color: #e8e8e8;
        }}

        QStatusBar {{ color: #333; background-color: #f0f0f0; }}
        QStatusBar QLabel {{ color: #555; background-color: transparent; }}
        QListWidget {{ color: #555; background-color: #fafafa; }}
        QListWidget::item:selected {{ background-color: #0078d4; color: #fff; }}

        /* ── Tab 样式：选中 Tab 与 Pane 融为一体 ── */
        QTabWidget::pane {{
            border-left: 1px solid #ccc;
            border-right: 1px solid #ccc;
            border-bottom: 1px solid #ccc;
            border-top: none;
            background-color: #fff;
            border-radius: 0 0 6px 6px;
        }}
        QTabBar::tab {{
            background-color: #e8e8e8; color: #777;
            padding: 8px 20px;
            border: 1px solid #ccc;
            border-bottom: 1px solid #ccc;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
            border-bottom-left-radius: 0px;
            border-bottom-right-radius: 0px;
            margin-right: 2px;
            margin-bottom: -1px;
            font-size: 13px;
        }}
        QTabBar::tab:hover {{
            background-color: #f0f0f0; color: #444;
        }}
        QTabBar::tab:selected {{
            background-color: #fff; color: #0078d4;
            font-weight: 600;
            border-bottom-color: #fff;
        }}

        /* ── SizeGrip 样式 ── */
        QSizeGrip {{
            width: 16px; height: 16px;
            background: transparent;
            image: none;
        }}
    """)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
