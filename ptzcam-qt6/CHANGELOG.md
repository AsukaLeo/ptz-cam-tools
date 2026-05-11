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

## V 0.34.511_14288d9 — EXE 体积优化 + 浅色模式任务栏图标暗底适配

**Commit**: `14288d9` → `4a5d40c` · **Branch**: `layout-v2` · **日期**: 2026-05-11

### EXE 体积优化（180MB → 56MB，-69%）
- **Spec binary filter**: PyInstaller `.spec` 中过滤 `a.binaries`，移除 Qt6Quick/Qml/OpenGL/Pdf/VirtualKeyboard 等非必要 C++ DLL
- **移除 thirdparty FFmpeg**: QMediaPlayer 已内置 `ffmpegmediaplugin.dll`，独立 FFmpeg DLL 纯重复
- **UPX 压缩集成**: `build_exe.bat` 自动 PATH 注入 UPX，插件 DLL 禁用（CFG 保护）
- **关键教训**: Windows 路径分隔符必须用 `\\`（`PySide6\\`），不能用 `/`，否则 `startswith()` 匹配不到任何文件

### 浅色模式任务栏图标暗底适配
- **问题**: 浅色模式下 `app_light.ico` 在白色任务栏上线条不清晰
- **方案**: Win32 API `SendMessage(hwnd, WM_SETICON, ICON_BIG, hicon)` 单独设任务栏大图标
  - 标题栏（ICON_SMALL）: 保持 `app_light.ico` — `QApplication.setWindowIcon()`
  - 任务栏（ICON_BIG）: 覆盖为 `app_light_with_dark_bg.ico` — Win32 API
- **修改**: `main.py` 新增 `_override_taskbar_icon()` / `_apply_taskbar_icon_for_scheme()`
- **资源**: 新增 `assets/app_light_with_dark_bg.ico` + 源文件 `assets/app_ico_light_with_dark_bg.png`

### 修改文件（6 files, +118/-84）
```
main.py                            | +58  Win32 任务栏图标分离
PTZ-Cam-Tools.spec                 | +35  binary filter 裁减非必要 DLL
build_exe.bat                      | +18  UPX PATH 注入 + spec 模式
assets/app_light_with_dark_bg.ico  | 新增  暗底任务栏图标
assets/app_ico_light_with_dark_bg.png | 新增 图标源文件
app/utils/constants.py             |  +1  版本号更新 → 14288d9
```

### 编译产物
- `PTZ-Cam-Tools-V0.34.511_14288d9-By-Asuka.exe` (56MB)
- Gitea Release #25

---

## V 0.34.511 — 自适应系统深色/浅色模式 Logo

**Commit**: `ac873ce` · **Branch**: `layout-v2` · **日期**: 2026-05-11

### 功能
- **自适应图标**: 使用 `QStyleHints.colorScheme()` 检测系统深色/浅色模式
  - 深色模式 → 加载 `app_dark.ico`（亮色图标，适配深色任务栏）
  - 浅色模式 → 加载 `app_light.ico`（深色图标，适配浅色任务栏）
- **运行时切换**: 注册 `colorSchemeChanged` 信号，系统切换深浅模式时自动跟换图标
- **图标文件管理**: `app_square.ico` 重命名为 `app_dark.ico`，新增 `app_light.ico` 及源文件 `app_ico_light.png`

### 修改文件（3 files, +18/-7）
```
main.py              |  21   图标自适应逻辑（colorScheme检测+信号连接）
build_exe.bat        |   2   PyInstaller打包图标改为app_dark.ico
assets/app_square.ico → app_dark.ico | 重命名
assets/app_light.ico | 新增  浅色模式图标
```

### 踩坑记录
- 无

---

## V 0.33.508 — Layout V2 布局重构 + AF 聚焦 + Bug 修复

**Commit**: `8bc3eb8` · **Branch**: `layout-v2` · **日期**: 2026-05-11

### Layout V2 — UI 布局重构
- **核心改动**: 主窗口从全高 Tab 改为 HBoxLayout（左侧 Tab 预览 + 右侧 PTZ/VISCA 面板 340px）
- 窗口默认 1300x680，最小 900x500
- 右侧面板 PTZ 4/7 高度 + VISCA 3/7 高度
- VISCA/PTZ 自适应高度布局，避免串口 Tab 被挤压消失
- ControlCard 最小 500px，预览区 16:9 自适应
- 全局 QComboBox 改用 AdjustToContents 自适应宽度
- 状态栏新增 i18n 支持（`状态:` 前缀跟随语言切换）

### VISCA 增强
- **自动聚焦 (One Push AF)**: 新增 `auto_focus()` -> `build_auto_focus()`
- **聚焦模式切换**: `set_focus_mode(auto=True/False)` -> `build_focus_mode()`
- **串口方向反转按钮**: 网络/串口共享方向状态
- PTZ 面板布局重排：方向控制 + 变焦/聚焦分离，预置位输入从 QSpinBox 改为 QLineEdit
- IP 模式不走校验和（Dahua 兼容）

### 开发工具
- **DebugOverlay (F12)**: 253 行新文件，自动标注所有控件（名称+宽高+类型，悬停高亮，点击隐藏）
- 版本号自动跟随 git hash 更新

### Bug 修复（3 项）
| Bug | 根因 | 修复 |
|-----|------|------|
| 英文界面下视频无法播放 | `play_btn.text() == "播放"` 硬编码中文比对 | 改用 `_is_playing` 布尔标志（3 处） |
| 所有操作状态更新崩溃 | `main_window.py` 缺少 `from app.utils.i18n import tr` | 模块级导入，删除冗余 inline import |
| 英文下 VISCA 断开连接按钮失效 | `visca_text == "断开连接"` 文本比对 | 改用 `_serial_is_connected` / `_network_is_connected` 布尔标志 |

### 修改文件（13 files, +1145/-122）
```
app/main_window.py          |  85   Layout V2 + tr import + status i18n
app/widgets/visca_panel.py  | 223   串口刷新、方向反转、状态标志、自适应高度
app/widgets/ptz_panel.py    | 210   AF/MF 按钮、布局重排、预置位输入
app/utils/debug_overlay.py  | 253   新增 F12 调试覆盖层
app/utils/visca_protocol.py |  31   build_auto_focus() + build_focus_mode()
app/utils/visca_controller.py| 25   auto_focus() + set_focus_mode()
app/tabs/usb_tab.py         |   6   _is_playing 布尔标志
app/tabs/rtsp_tab.py        |   7   Combo AdjustToContents
app/utils/constants.py      |   8   窗口尺寸 960->1300
app/utils/i18n.py           |   2   AF/MF 翻译
app/widgets/control_card.py |   3   Combo AdjustToContents
docs/layout-v2-prototype.html | 189 交互原型
docs/控件命名参考.html       | 225  控件命名规范
```

### 踩坑记录
1. **PySide6 QResizeEvent 在 QtGui 不在 QtCore** — import 路径诡异
2. **深色主题适配**: 全局 QSS 必须强制 `QWidget { color: #333; background-color: #fff; }`，否则深色系统下文字不可见
3. **QComboBox 下拉列表**必须显式设 QAbstractItemView 的 border/background，否则不可见
4. **i18n 按钮状态**: 绝对不能靠 UI 文本比对判断状态，必须用独立布尔标志
5. **VISCA 串口 Tab 消失**: `QTabWidget` 内层 Tab 在某些高度下被完全隐藏，需设最小高度 220px
6. **Python import 致命性**: 一个缺失的模块级 import 导致所有 Tab 全部崩溃，而非仅影响单一功能

---

## V 0.25.507 — UI/UX 改进 + ONVIF 增强 + Bug 修复

**Tag**: `V0.25.507` · **Commit**: `b290e74` · **日期**: 2026-05-07

### UI/UX 改进
- 状态栏视频信息跟随 Tab 切换（每 Tab 独立缓存，切换时自动刷新）
- RTSP 输入框 disabled 状态变灰（`QLineEdit:disabled` CSS 样式）
- RTSP/NDI/ONVIF 统一网卡选择控件（每行显示一个 IPv4 地址）
- ONVIF 设备选择自动填充 IP/端口/用户信息
- 所有 Tab 控制栏统一 120px 固定高度 + 垂直居中
- 视频预览区背景 30% 不透明度（透出主窗背景图）
- RTSP 输入框支持清空按钮 + 点击全选

### ONVIF 增强
- 遍历所有 Profile 获取 RTSP URL（不再只用 profiles[0]）
- 自动尝试 20 组常见出厂默认凭据（admin:9999 优先）
- 认证失败精确错误提示（状态栏显示具体原因）
- RTSP 回落 URL 覆盖 30+ 种常见路径 + 标准 RTSP 端口 554
- 工作凭据自动传递到 RTSP 拉流（无需手动输入密码）

### Bug 修复
- ONVIF 连接失败后按钮永久变灰锁死（缺 `_update_ui_stopped()`）
- RTSP 回落端口错误（使用了 ONVIF HTTP 端口而非 554）

### 新增文件
- `app/utils/network_utils.py` — 网卡枚举公共函数（多 IP 分行显示）

### 修改文件
- `app/styles/theme.py` — QLineEdit:disabled + :focus 样式
- `app/main_window.py` — Tab 切换视频信息刷新
- `app/tabs/usb_tab.py` — 视频信息缓存
- `app/tabs/rtsp_tab.py` — 共用网卡、清空按钮、全选、disabled 样式
- `app/tabs/ndi_tab.py` — 添加网卡选择、固定高度居中
- `app/tabs/onvif_tab.py` — 网卡选择、居中、自动填充、认证错误提示
- `app/utils/onvif_device.py` — 遍历 Profile、默认凭据、认证检测、回落 URL
- `app/utils/constants.py` — 预览区透明背景

---

## V 0.24.506 — PyInstaller 编译 + 图标 + 全功能修复

**Tag**: `V0.24.506` · **Commit**: `c27b7af` · **日期**: 2026-05-06

### 修复
- PyInstaller 编译版 RTSP/ONVIF 不可用问题
  - FFmpeg DLL 路径修正（_setup_bundled_paths）
  - WSDL 文件打包（onvif-zeep 的 WSDL 在 site-packages/wsdl/）
  - zeep 缓存路径修正（_setup_zeep_cache）
- VISCA 协议 over IP 移除校验和（Dahua 相机不识别）
- RTSP 认证空密码嵌入 + TCP 传参改环境变量

### UI
- 应用图标替换为 app_square.ico（16×16 ~ 256×256）

### 构建
- build_exe.bat: 一键编译，UPX 压缩
- 输出: dist/PTZ-Cam-Tools-V{version}.exe（~178MB）

---

## V 0.23.506 — VISCA 协议 PTZ 控制（Phase 3）

**Tag**: `V0.23.506` · **Commit**: `873f944` · **日期**: 2026-05-06

### 功能
- VISCA 协议命令构造：Pan/Tilt/Zoom/Focus/Home/预设位
- VISCA 三种传输支持：串口(pyserial 9600 8N1)、UDP(52381)、TCP(5678)
- PTZ 面板按钮 → 实际 VISCA 命令发送
- VISCA 面板串口/网络配置 → 实际连接管理
- 响应解析：ACK/Completion/Error

### 新增文件
- `app/utils/visca_protocol.py` — VISCA 命令构造 + 响应解析
- `app/utils/visca_transport.py` — 传输层抽象 + Serial/UDP/TCP 实现
- `app/utils/visca_controller.py` — ViscaController 统一入口

### 修改文件
- `app/widgets/ptz_panel.py` — 按钮对接 controller
- `app/widgets/visca_panel.py` — 配置对接 controller
- `app/main_window.py` — 创建 controller 注入面板

### 依赖变更
- 新增 `pyserial>=3.5`

---

## V 0.22.506 — RTSP/ONVIF 修复：空密码认证 + TCP 传输修正

**Tag**: `V0.22.506` · **Commit**: `77dae89` · **日期**: 2026-05-06

### 修复
- **空密码认证**：用户名不为空时就嵌入 `user:pass@` 到 RTSP URL（即使密码为空），解决 `admin:@` 场景
- **RTSP TCP 传输**：去掉 URL 拼接 `?transport=tcp`（某些相机视其为路径返回 404），改用环境变量 `OPENCV_FFMPEG_CAPTURE_OPTIONS=rtsp_transport;tcp`

### 涉及文件
- `app/utils/rtsp_capture.py` — TCP 传参方式修正
- `app/tabs/rtsp_tab.py` — 认证嵌入逻辑修正
- `app/tabs/onvif_tab.py` — 认证嵌入逻辑修正

---

## V 0.21.506 — ONVIF 设备发现 + 连接 + 视频预览

**Tag**: `V0.21.506` · **Commit**: `7c4db6c` · **日期**: 2026-05-06

### 功能
- ONVIF 设备发现：WS-Discovery 扫描局域网 ONVIF 设备
- ONVIF 连接：onvif-zeep 连接设备，获取设备信息和能力
- RTSP 流获取：通过 ONVIF Media Service 获取 RTSP 流 URL
- 视频预览：复用已有 RTSP 捕获模块（rtsp_capture.py）拉流显示
- 设备选择：下拉列表选择发现设备 + 手动 IP 输入
- 连接/断开状态控制

### 新增文件
- `app/utils/onvif_device.py` — ONVIF 设备模块（发现 + 连接 + RTSP URL 获取）

### 依赖变更
- 新增 `onvif-zeep==0.2.12`（ONVIF SOAP 客户端）
- 新增 `wsdiscovery==2.1.2`（WS-Discovery 设备发现）

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
