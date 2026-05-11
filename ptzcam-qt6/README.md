# PTZ-Cam-Tools

> 会议摄像机 / 全向麦克风 多功能控制工具  
> V 0.34.511 — 布局 V2 分支  
> **35 次迭代 · 23 个 Release**

---

## 功能矩阵

### 📹 视频源接入（4 路全通）

| 视频源 | 实现方式 | 关键特性 |
|--------|----------|----------|
| **USB** | QCamera + QMediaCaptureSession + QVideoSink | 设备枚举、格式/分辨率/帧率选择、H264 硬解 |
| **RTSP** | QMediaPlayer + QVideoSink | TCP/UDP 传输、断线检测+自动重连、认证 URL 拼接 |
| **NDI** | ctypes 直绑 NDI SDK v6 | 源发现列表、视频接收、BGRA→QImage 零拷贝转换 |
| **ONVIF** | WS-Discovery + onvif-zeep + RTSP 复用 | 设备发现、自动填充 IP/端口/凭据、默认凭据轮询（20 组）、回退 RTSP 路径（30+ 种） |

### 🎮 PTZ 控制

- VISCA 协议 — Serial (9600 8N1) / IP (TCP 5678 / UDP 52381)
- Pan / Tilt / Zoom 控制 + 速度滑块
- 预置位管理（6 个存储/调用）
- 串口异步通信 + TX/RX 数据监控

### 🎨 UI 系统

- **Layout V2** — 右侧 PTZ/VISCA 面板 340px，预览区全宽 16:9
- **中英双语国际化** — 100+ 词条，按钮状态不丢失
- **DebugOverlay** — F12 控件标注（名称+宽高+类型，悬停高亮，点击隐藏）
- **状态栏** — 视频信息（分辨率/格式/帧率/延时/解码方式/CPU），跟随 Tab 切换
- **ControlCard 公共组件** — 4 个 Tab 共享，代码量减少 70%
- **网卡统一** — `network_utils.py`，3 个 Tab 共用，IPv4 多 IP 分行

---

## 技术栈

| 层级 | 技术 |
|------|------|
| UI 框架 | PySide6 6.11.0（Qt6） |
| 语言 | Python 3.14 |
| 视频解码 | FFmpeg 7.1 / QtMultimedia |
| 串口通信 | pyserial |
| 网络 | onvif-zeep, WS-Discovery |
| NDI | NDI SDK v6（ctypes） |
| 打包 | PyInstaller（单文件 55MB） |

---

## 版本历史

| 版本 | 日期 | 里程碑 |
|------|------|--------|
| V 0.34.511 | 5/11 | 自适应深色/浅色模式 logo + 图标文件管理 |
| V 0.33.508 | 5/11 | Layout V2 + AF 聚焦 + 3 项 Bug 修复 |
| V 0.33.508 | 5/8 | VISCA 串口数据监控 + DebugOverlay 控件命名 |
| V 0.32.508 | 5/8 | 技术债务清零 + 残留文件清理 |
| V 0.28.507 | 5/7 | Slim Edition（233MB→98MB，Qt 替代 OpenCV） |
| V 0.27.507 | 5/7 | 预置位管理 + 速度滑块 + 串口异步 |
| V 0.25.507 | 5/7 | 6 项 Bug 修复 + ONVIF 默认凭据自动尝试 |
| V 0.23.506 | 5/6 | VISCA 协议 PTZ 控制 |
| V 0.21.506 | 5/6 | ONVIF 设备发现 + 连接 + RTSP 拉流 |
| V 0.20.506 | 5/6 | NDI 视频源接入 |
| V 0.17.506 | 5/6 | RTSP 拉流 |
| V 0.13.506 | 5/6 | USB 预览稳定版 |
| V 0.8.430 | 4/30 | 版本号体系建立 |

完整历史见 [CHANGELOG.md](./CHANGELOG.md)

---

## 目录结构

```
ptzcam-qt6/
├── main.py                 # 入口（--debug 参数）
├── app/
│   ├── main_window.py      # 主窗口
│   ├── widgets/            # 可复用组件
│   │   ├── preview.py      # 视频预览
│   │   ├── ptz_panel.py    # PTZ 控制面板
│   │   ├── visca_panel.py  # VISCA 面板
│   │   ├── control_card.py # 公共控制卡
│   │   └── help_card.py    # 帮助提示卡
│   ├── tabs/               # 功能 Tab
│   │   ├── usb_tab.py      # USB 摄像头
│   │   ├── rtsp_tab.py     # RTSP 拉流
│   │   ├── ndi_tab.py      # NDI 源
│   │   └── onvif_tab.py    # ONVIF 发现
│   ├── styles/
│   │   └── theme.py        # 全局样式
│   └── utils/
│       ├── i18n.py         # 国际化（中英）
│       ├── debug_overlay.py # F12 调试覆盖层
│       ├── network_utils.py # 网卡枚举
│       ├── onvif_device.py  # ONVIF 设备操作
│       └── ...
├── docs/                   # 技术文档
├── logs/                   # 运行日志
├── tests/                  # pytest
├── run.bat                 # 正常启动
└── run_debug.bat           # 调试模式
```

## 编译与发布

```bash
# 编译 EXE（需先清除缓存）
rm -rf build/ dist/ *.spec __pycache__/
python -m PyInstaller --onefile --windowed main.py

# 上传至 Gitea Release（通过 API）
# 详见 MEMORY.md → 远程仓库
```

## 仓库

- **主仓库**：`https://gitea.feiniaoyun.cn/FNY/PTZ-Camara`
- **分支**：main（稳定）| layout-v2（开发中）| slim-opencv（已合入）
