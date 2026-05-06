# PTZ-Cam-Tools 版本迭代手册

## 版本号格式

```
V {主版本号}.{迭代次数}.{日期}_{git版本} By Asuka
```

| 字段 | 说明 | 示例 |
|------|------|------|
| 主版本号 | 大版本里程碑（0 = 开发中） | 0 |
| 迭代次数 | 累计迭代次数 | 14 |
| 日期 | MDD 格式 | 506 = 5月6日 |
| git版本 | commit hash 前7位 | 75eef0c |

---

## V 0.20.506 — NDI 视频源接入

**Tag**: `V0.20.506` · **Commit**: `7c94eda` · **日期**: 2026-05-06

### 功能
- NDI 源发现：mDNS 搜索局域网 NDI 源（刷新按钮触发）
- NDI 视频接收：选择源后连接，实时预览视频帧
- 源列表显示名称和地址信息
- 连接/断开状态控制，播放中禁用控件
- 状态栏实时信息：分辨率、帧率、延时、解码方式（NDI SDK v6）

### 新增文件
- `app/utils/ndi_sdk.py` — NDI SDK ctypes 封装（加载 DLL、函数签名、数据结构）
- `app/utils/ndi_capture.py` — NDI 源发现 + 视频接收线程 + BGRA→QImage 转换

### 依赖变更
- 运行时依赖：NDI Runtime v6（`Processing.NDI.Lib.x64.dll`）
- 无 Python 包新增（ctypes 直绑）

---

## V 0.19.506 — 网卡过滤完善 + 预览区布局修复

**Tag**: `V0.19.506` · **Commit**: `e1bbb8f` · **日期**: 2026-05-06

### 修复
- 网卡过滤补上中文关键词（蓝牙、虚拟、回环、隧道、本地连接）
- 过滤本地连接*虚拟网卡（Wi-Fi Direct）
- 预览区布局改用 removeWidget + addWidget(widget, 1)，确保占满剩余空间

---

## V 0.18.506 — RTSP 修复：网卡过滤 + 预览区布局

**Tag**: `V0.18.506` · **Commit**: `ace6b55` · **日期**: 2026-05-06

### 修复
- 网卡选择过滤虚拟设备（VMware/Hyper-V/Docker/VPN/蓝牙等不再显示）
- 预览区被压缩问题（replaceWidget 后恢复 stretch=1）

---

## V 0.17.506 — RTSP 拉流（OpenCV FFmpeg 后端）

**Tag**: `V0.17.506` · **Commit**: `01e9c6d` · **日期**: 2026-05-06

### 功能
- RTSP 视频流接入：设备发现、URL + 认证 + 传输协议选择
- 实时视频预览（OpenCV + FFmpeg 后端解码）
- RTSP 传输协议选择（UDP / TCP）
- 网卡自动枚举（基于 psutil）
- 播放/停止状态控制，播放中禁用配置控件
- 状态栏实时信息：分辨率、帧率、延时、解码方式
- 断流自动检测 + 自动重连（最多 3 次）

### 新增文件
- `app/utils/rtsp_capture.py` — RTSP 捕获模块（RTSPSource + RTSPCaptureThread）

### 依赖变更
- 无新增依赖（基于已有 opencv-python + psutil）

---

## V 0.16.506 — UI 视觉优化（背景图 + Tab 半透明 + 按钮修复）

**Tag**: `V0.16.506` · **Commit**: `2a319d9` · **日期**: 2026-05-06

### 功能
- 添加全局背景图（border-image 拉伸铺满）
- 自定义程序图标（标题栏/任务栏）
- Tab 区域 70% 半透明效果，背景图可透出
- 未激活标签文字可读性优化

### 修复
- CPU 占用率归一化到单核（除 cpu_count）
- CPU 刷新率改为每秒一次
- 停止播放时清空状态栏视频信息
- Zoom/Focus 按钮宽度不足导致文字截断（60→80px）
- 激活标签和 Tab 内容区之间的白线/gap
- PTZ/VISCA 控制面板标题水平对齐
- VISCA 内嵌 Tab 白线问题
- 代码仓库推送到 Gitea 私有服务器

### 依赖变更
- 新增 `psutil>=7.0.0`（进程 CPU 监控）

---

## V 0.15.506 — 状态栏扩充（解码方式 + CPU 占用）

**Tag**: `V0.15.506` · **Commit**: `f2809a7` · **日期**: 2026-05-06

### 功能
- 状态栏新增「解码方式」显示（格式 + OpenCV 后端）
- 状态栏新增「CPU 实时占用率」显示（基于 psutil）
- 信息区显示格式改为：`分辨率 | 源:格式 | 解码:方式 | fps | 延时ms | CPU:%`

### 依赖变更
- 新增 `psutil>=7.0.0`（CPU 监控）

---

## V 0.14.506 — USB预览稳定版（当前最新）

**Tag**: `V0.14.506` · **Commit**: `75eef0c` · **日期**: 2026-05-06

### 功能
- USB 摄像头设备枚举（纯 Qt, 秒开, 无虚拟设备）
- 视频实时预览（OpenCV + DirectShow）
- 分辨率/格式/帧率选择（格式排序：MJPG > YUYV > NV12 > H264）
- H264 自动增补（放格式列表最后）
- 状态栏实时视频信息：分辨率、格式、帧率、延时（ms）
- 启动 `--debug` 参数启用详细日志
- `:disabled` CSS 样式（按钮/下拉框禁用视觉反馈）
- QComboBox 滚动条样式（多分辨率时可用）

### 修复
- 设备格式枚举不全（纯 Qt 数据 + H264 标准增补）
- 播放失败后设备被占用（强制线程清理）
- 虚拟摄像机显示（Qt 设备管理器过滤）
- 刷新按钮状态不更新

### 文件结构
```
ptzcam-qt6/
├── main.py                    # 入口
├── .gitignore
├── requirements.txt
├── app/
│   ├── main_window.py         # 主窗口 + 状态栏
│   ├── widgets/
│   │   ├── preview.py         # PreviewWidget
│   │   ├── ptz_panel.py
│   │   └── visca_panel.py
│   ├── tabs/
│   │   ├── usb_tab.py         # USB 摄像头控制
│   │   ├── rtsp_tab.py
│   │   ├── ndi_tab.py
│   │   ├── onvif_tab.py
│   │   └── settings_tab.py
│   ├── styles/
│   │   └── theme.py           # 全局样式
│   └── utils/
│       ├── constants.py       # 版本号、常量
│       ├── device_manager.py  # Qt 设备管理器
│       ├── dshow_capture.py   # DirectShow 捕获
│       ├── qt_capture.py
│       └── logger.py          # 日志系统
├── tests/
├── logs/
└── CHANGELOG.md               # 本文件
```

### 启动方式
```bat
python main.py             # 正常模式
python main.py --debug     # 调试模式
```

---

## V 0.13.506 — USB 枚举架构稳定版

**Tag**: `V0.13.506` · **Commit**: `f90d69a` · **日期**: 2026-05-06

- 枚举架构改为纯 Qt 方案，不碰 OpenCV
- 每个分辨率自动增补 H264（Qt 报告的真实 FPS）
- 去虚拟摄像机
- 修复预览黑屏（避免 OpenCV cap 枚举后 DShow 驱动状态异常）

---

## V 0.12.430 — USB 摄像头预览

**Tag**: `V0.12.430` · **Commit**: `6ddabed` · **日期**: 2026-04-30

- USB 摄像头设备枚举
- OpenCV DirectShow 视频捕获
- 实时预览
- 分辨率/格式/帧率选择
- 模块化重构

---

## V 0.11.430 — 设备枚举 + 格式选择

**日期**: 2026-04-30

- 设备枚举
- 格式选择下拉
- 版本号显示

---

## V 0.10.430 — 模块化重构

**日期**: 2026-04-30

- 代码模块化分层
- 调试日志系统

---

## V 0.9.430 — VISCA 控制

**日期**: 2026-04-30

- 添加 VISCA 串口控制
- 移除设置页网络设置

---

## V 0.8.430 — 版本号体系建立

**日期**: 2026-04-30

- 建立版本号规则
- 界面布局完善

---

## V 0.7.429 — 初始版本

**日期**: 2026-04-29

- 初始 UI 原型
- QTabWidget 5 个 Tab
- PTZ Panel 基础控件

---

## 技术栈

| 组件 | 版本 |
|------|------|
| Python | 3.14 |
| PySide6 | 6.11.0 |
| opencv-python | 4.13.0.92 |
| comtypes | 1.4.16 |

## 回退命令

```bash
git checkout V0.14.506   # 回退到当前稳定版
git checkout V0.13.506   # 回退到上一稳定版
```
