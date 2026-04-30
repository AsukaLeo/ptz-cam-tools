#!/usr/bin/env python3
import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QPushButton, QComboBox, QLineEdit, QTabWidget,
    QFrame, QStatusBar, QSizeGrip, QRadioButton
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QResizeEvent, QPainterPath, QRegion


# ── 窗口比例常量 ──────────────────────────────────────────────
ASPECT_W = 16
ASPECT_H = 10
MIN_WIDTH = 800
MIN_HEIGHT = 500


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # 恢复最大化按钮功能
        self.setWindowTitle("PTZ-Cam-Tools")

        # 在 setup_ui 之前初始化
        self._preview_frames = []
        self._preview_resolution = None
        self._resizing = False

        # 最小尺寸 & 默认尺寸（高度适配510px预览区 + 其他控件）
        self.setMinimumSize(MIN_WIDTH, MIN_HEIGHT)
        # 默认窗口高度 = 预览区510 + Tab/卡片约160 + PTZ约120 + 边距
        self.resize(960, 850)

        self.setup_ui()

    # ── 窗口调整 ────────────────────────────────────────────
    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
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
        """设置预览区内部视频层保持 16:9 比例，居中显示"""
        for container in self._preview_frames:
            if not container.isVisible():
                continue

            parent = container.parentWidget()
            if not parent:
                continue

            # 获取外层容器可用空间（宽度 = tab 页宽 - padding，高度 = 容器高度）
            container_w = parent.width() - 32
            container_h = container.height()

            # 计算 16:9 视频层的尺寸，适配容器
            ideal_h = int(container_w * 9 / 16)

            if ideal_h <= container_h:
                # 按宽度算的高度能放下，宽度撑满，高度 16:9
                video_w = container_w
                video_h = ideal_h
            else:
                # 高度超了，按高度算宽度
                video_h = container_h
                video_w = int(video_h * 16 / 9)

            video_w = max(video_w, 160)
            video_h = max(video_h, 90)

            # 找到内层视频层并设置尺寸
            video_frame = container.findChild(QFrame, "videoFrame")
            if video_frame:
                video_frame.setFixedSize(video_w, video_h)

    # ── UI 构建 ────────────────────────────────────────────────
    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(16, 6, 16, 6)  # 统一 16px 左右边距，6px 上下间距
        main_layout.setSpacing(6)  # Tab 与 PTZ 之间 6px 间距

        # Tab widget
        self.create_tab_widget(main_layout)

        # PTZ Panel
        self.create_ptz_panel(main_layout)

        # Status bar
        self.status_label = QLabel("  状态: 就绪")
        self.statusBar().addWidget(self.status_label)

        # 版本署名放到右下角（去掉SizeGrip，避免空白区域）
        self.version_label = QLabel("V 0.9.430_b957676 By Asuka  ")
        self.version_label.setStyleSheet("color: #999; font-size: 11px; background: transparent;")
        self.statusBar().addPermanentWidget(self.version_label)

    def create_tab_widget(self, parent_layout):
        self.tab_widget = QTabWidget()

        self.tab_widget.addTab(self.create_usb_tab(), "USB")
        self.tab_widget.addTab(self.create_rtsp_tab(), "RTSP")
        self.tab_widget.addTab(self.create_ndi_tab(), "NDI")
        self.tab_widget.addTab(self.create_onvif_tab(), "ONVIF")
        self.tab_widget.addTab(self.create_settings_tab(), "设置")

        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        parent_layout.addWidget(self.tab_widget, 1)  # stretch=1 让 tab 区域占满剩余空间

    def _create_preview(self):
        """创建视频预览区 — 黑色背景填充，内部视频层保持 16:9"""
        # 外层容器：黑色背景，默认高度510px，可随窗口缩放
        container = QFrame()
        container.setObjectName("previewContainer")
        container.setMinimumHeight(200)
        container.setStyleSheet("""
            QFrame#previewContainer {
                background-color: #1a1a1a;
                border: 2px solid #333;
                border-radius: 6px;
            }
        """)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setAlignment(Qt.AlignCenter)

        # 内层视频层：保持 16:9 比例
        video_frame = QFrame()
        video_frame.setObjectName("videoFrame")
        video_frame.setStyleSheet("""
            QFrame#videoFrame {
                background-color: #0a0a0a;
                border-radius: 4px;
            }
        """)
        video_layout = QVBoxLayout(video_frame)
        video_layout.setContentsMargins(0, 0, 0, 0)
        video_layout.setAlignment(Qt.AlignCenter)

        lbl = QLabel("视频预览区")
        lbl.setStyleSheet("color: #666; font-size: 24px; background: transparent;")
        lbl.setAlignment(Qt.AlignCenter)
        video_layout.addWidget(lbl)

        container_layout.addWidget(video_frame)

        self._preview_frames.append(container)
        return container

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

        # 设备 & 参数控制卡片（合并为一个卡片，两行）
        card, card_layout = self._make_control_card()

        # 第一行：设备选择
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
        card_layout.addLayout(device_row)

        # 第二行：分辨率 / 格式 / 帧率
        param_row = QHBoxLayout()
        param_row.setSpacing(8)

        lbl1 = QLabel("分辨率:")
        lbl1.setFixedWidth(80)
        lbl1.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        param_row.addWidget(lbl1)
        param_row.addWidget(self._make_combo(["1920 x 1080", "1280 x 720", "640 x 480"]))

        lbl2 = QLabel("格式:")
        lbl2.setFixedWidth(50)
        lbl2.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        param_row.addWidget(lbl2)
        param_row.addWidget(self._make_combo(["YUY2", "MJPEG", "H264"]))

        lbl3 = QLabel("帧率:")
        lbl3.setFixedWidth(50)
        lbl3.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        param_row.addWidget(lbl3)
        param_row.addWidget(self._make_combo(["30 fps", "25 fps", "15 fps"]))

        param_row.addStretch()
        card_layout.addLayout(param_row)

        card.setFixedHeight(120)
        layout.addWidget(card)

        # Preview — 高度由 _update_preview_size 限制为 16:9，不 stretch
        layout.addWidget(self._create_preview())

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

        card1.setFixedHeight(120)
        layout.addWidget(card1)

        # Preview — stretch=1 自动填充
        layout.addWidget(self._create_preview(), 1)

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

        # Preview — stretch=1 自动填充
        layout.addWidget(self._create_preview(), 1)
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
        layout.addWidget(self._create_preview(), 1)
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
                margin-left: 0px;
                margin-right: 0px;
                margin-top: 0px;
                margin-bottom: 6px;
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
        zr.addWidget(ctrl_btn("Focus+", lambda: self.update_status("Focus +")))
        zf_layout.addLayout(zr)

        fr = QHBoxLayout()
        fr.setSpacing(8)
        fr.addWidget(ctrl_btn("Zoom-", lambda: self.update_status("Zoom -")))
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

        # VISCA 控制区域
        visca_widget = self._create_visca_control()
        controls_layout.addWidget(visca_widget)

        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        parent_layout.addWidget(ptz_panel)
        self._ptz_panel = ptz_panel

    def _create_visca_control(self):
        """创建 VISCA 控制区域（串口 + 网络）"""
        visca_frame = QFrame()
        visca_frame.setObjectName("viscaFrame")
        visca_frame.setStyleSheet("""
            QFrame#viscaFrame {
                background-color: #f0f2f5;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
            }
        """)
        visca_layout = QVBoxLayout(visca_frame)
        visca_layout.setContentsMargins(10, 10, 10, 10)
        visca_layout.setSpacing(6)

        # VISCA 标题
        visca_title = QLabel("VISCA 控制")
        visca_title.setStyleSheet("font-size: 12px; font-weight: 500; color: #555; background: transparent;")
        visca_layout.addWidget(visca_title)

        # Tab 切换：串口 / 网络
        visca_tab = QTabWidget()
        visca_tab.setDocumentMode(True)
        visca_tab.setStyleSheet("""
            QTabWidget::pane { border: none; }
            QTabBar::tab {
                background-color: #e0e0e0; color: #666;
                padding: 4px 12px; border: 1px solid #ccc;
                border-top-left-radius: 4px; border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #fff; color: #333;
                border-bottom-color: #fff;
            }
        """)

        # 串口 Tab
        serial_page = QWidget()
        serial_layout = QVBoxLayout(serial_page)
        serial_layout.setContentsMargins(8, 8, 8, 8)
        serial_layout.setSpacing(6)

        # 端口
        port_row = QHBoxLayout()
        port_row.addWidget(QLabel("端口:"))
        port_combo = self._make_combo(["COM1", "COM2", "COM3", "COM4"])
        port_row.addWidget(port_combo)
        serial_layout.addLayout(port_row)

        # 波特率
        baud_row = QHBoxLayout()
        baud_row.addWidget(QLabel("波特率:"))
        baud_combo = self._make_combo(["9600", "19200", "38400", "57600", "115200"])
        baud_row.addWidget(baud_combo)
        serial_layout.addLayout(baud_row)

        # 数据位
        data_row = QHBoxLayout()
        data_row.addWidget(QLabel("数据位:"))
        data_combo = self._make_combo(["8", "7", "6", "5"])
        data_row.addWidget(data_combo)
        serial_layout.addLayout(data_row)

        # 校验位
        parity_row = QHBoxLayout()
        parity_row.addWidget(QLabel("校验位:"))
        parity_combo = self._make_combo(["None", "Odd", "Even", "Mark", "Space"])
        parity_row.addWidget(parity_combo)
        serial_layout.addLayout(parity_row)

        # 停止位
        stop_row = QHBoxLayout()
        stop_row.addWidget(QLabel("停止位:"))
        stop_combo = self._make_combo(["1", "1.5", "2"])
        stop_row.addWidget(stop_combo)
        serial_layout.addLayout(stop_row)

        # 开启按钮
        serial_btn = QPushButton("开启")
        serial_btn.setStyleSheet("""
            QPushButton {
                background: #0078d4; color: #fff; border: none; border-radius: 4px;
                padding: 4px 16px; font-size: 12px;
            }
            QPushButton:hover { background: #0066b8; }
        """)
        serial_btn.clicked.connect(lambda: self.update_status("VISCA 串口已开启"))
        serial_layout.addWidget(serial_btn)
        serial_layout.addStretch()

        visca_tab.addTab(serial_page, "串口")

        # 网络 Tab
        net_page = QWidget()
        net_layout = QVBoxLayout(net_page)
        net_layout.setContentsMargins(8, 8, 8, 8)
        net_layout.setSpacing(6)

        # 协议选择
        proto_row = QHBoxLayout()
        proto_row.addWidget(QLabel("协议:"))
        tcp_rb = QRadioButton("TCP")
        tcp_rb.setChecked(True)
        udp_rb = QRadioButton("UDP")
        proto_row.addWidget(tcp_rb)
        proto_row.addWidget(udp_rb)
        proto_row.addStretch()
        net_layout.addLayout(proto_row)

        # 地址
        addr_row = QHBoxLayout()
        addr_row.addWidget(QLabel("地址:"))
        addr_edit = QLineEdit("192.168.50.254")
        addr_edit.setFixedWidth(120)
        addr_row.addWidget(addr_edit)
        net_layout.addLayout(addr_row)

        # 端口
        port2_row = QHBoxLayout()
        port2_row.addWidget(QLabel("端口:"))
        port2_edit = QLineEdit("5678")
        port2_edit.setFixedWidth(60)
        port2_row.addWidget(port2_edit)
        net_layout.addLayout(port2_row)

        # 连接按钮
        net_btn = QPushButton("连接")
        net_btn.setStyleSheet("""
            QPushButton {
                background: #0078d4; color: #fff; border: none; border-radius: 4px;
                padding: 4px 16px; font-size: 12px;
            }
            QPushButton:hover { background: #0066b8; }
        """)
        net_btn.clicked.connect(lambda: self.update_status("VISCA 网络已连接"))
        net_layout.addWidget(net_btn)
        net_layout.addStretch()

        visca_tab.addTab(net_page, "网络")
        visca_layout.addWidget(visca_tab)

        return visca_frame

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

    # 全局强制浅色主题（QWidget 背景透明，让父容器背景透上来）
    app.setStyleSheet(f"""
        QWidget {{ color: #333; }}
        QMainWindow {{ background-color: #fff; }}
        QPushButton {{ color: #333; background-color: #f5f5f5; }}
        QLabel {{ color: #333; background-color: transparent; }}
        QLineEdit {{
            color: #333; background-color: #fff;
            border: 1px solid #aaa; border-radius: 6px;
            padding: 4px 8px;
        }}

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
        QListWidget {{
            color: #555; background-color: #fafafa;
            border: 1px solid #aaa; border-radius: 6px;
        }}
        QListWidget::item:selected {{ background-color: #0078d4; color: #fff; }}

        /* ── QTabWidget 去掉默认边框 ── */
        QTabWidget {{
            border: none;
        }}

        /* ── Tab 样式：选中 Tab 与 Pane 融为一体 ── */
        QTabWidget::pane {{
            border: 1px solid #ccc;
            background-color: #fff;
            border-top-left-radius: 0px;
            border-top-right-radius: 0px;
            border-bottom-left-radius: 6px;
            border-bottom-right-radius: 6px;
            margin-top: -1px;
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
            margin-right: 0px;
            font-size: 13px;
        }}
        QTabBar::tab:hover {{
            background-color: #f0f0f0; color: #444;
        }}
        QTabBar::tab:selected {{
            background-color: #fff; color: #0078d4;
            font-weight: 600;
            border-bottom-color: #fff;
            margin-bottom: -1px;
            margin-right: 0px;
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
