# PTZ-Cam-Tools 技术交接文档

**版本**: V 0.9.430_2506f44 By Asuka  
**日期**: 2026-04-30  
**状态**: UI 层完成，待接入功能实现

---

## 1. 项目架构

### 1.1 技术栈
- **前端**: PySide6 6.11.0 (Python 3.13+)
- **UI 框架**: Qt6 Widgets
- **设计风格**: 浅色主题，统一 6px 圆角

### 1.2 文件结构（已模块化重构）
```
ptzcam-qt6/
├── main.py                    # 入口（35行）
├── app/                       # 应用主包
│   ├── __init__.py
│   ├── main_window.py         # 主窗口逻辑（~200行）
│   ├── widgets/               # 可复用组件
│   │   ├── __init__.py
│   │   ├── preview.py         # PreviewWidget（视频预览）
│   │   ├── ptz_panel.py       # PTZPanel（PTZ控制）
│   │   └── visca_panel.py     # VISCAPanel（VISCA控制）
│   ├── tabs/                  # Tab 页面
│   │   ├── __init__.py
│   │   ├── usb_tab.py         # USBTab
│   │   ├── rtsp_tab.py        # RTSPTab
│   │   ├── ndi_tab.py         # NDITab
│   │   ├── onvif_tab.py       # ONVIFTab
│   │   └── settings_tab.py    # SettingsTab
│   ├── styles/                # 样式定义
│   │   ├── __init__.py
│   │   └── theme.py           # 全局样式/QSS
│   └── utils/                 # 工具模块
│       ├── __init__.py
│       └── constants.py       # 所有常量/颜色/字符串
├── tests/                     # 测试套件
│   ├── __init__.py
│   ├── test_main_window.py
│   └── test_constants.py
├── mainwindow.h/cpp           # Qt6 C++ 备用实现
├── CMakeLists.txt             # CMake 配置
├── arrow_down.svg             # ComboBox 下拉箭头图标
├── run.bat                    # Windows 启动脚本
├── requirements.txt           # Python 依赖
├── HANDOVER.md                # 项目交接概览
└── TECH_HANDOVER.md           # 本技术文档
```

**重构说明**：2026-04-30 完成模块化重构，将原单文件 main.py（1000+ 行）拆分为 18 个 Python 文件，实现：
- 职责分离：每个模块单一职责
- 样式分离：所有样式抽离到 theme.py
- 常量管理：硬编码提取到 constants.py
- 类型注解：完整的 Python 类型提示
- 测试框架：pytest 测试结构

---

## 2. UI 层实现状态

### 2.1 已完成 ✅

#### 主窗口布局
- 标题栏：PTZ-Cam-Tools（系统原生）
- 窗口尺寸：默认 960x850，最小 800x500
- 支持最大化/最小化/自由缩放

#### Tab 导航（5个）
| Tab | 功能 | 状态 |
|-----|------|------|
| USB | 设备选择、分辨率/格式/帧率配置 | ✅ UI 完成 |
| RTSP | URL、认证、网卡选择 | ✅ UI 完成 |
| NDI | NDI 源选择 | ✅ UI 完成 |
| ONVIF | IP/端口、认证、设备发现 | ✅ UI 完成 |
| 设置 | 语言切换 | ✅ UI 完成 |

#### 视频预览区
- 黑色背景 (#1a1a1a)，圆角边框
- 内部视频层 16:9 比例自适应
- 默认高度 510px，随窗口缩放

#### 控制面板（左右并排）
| 区域 | 功能 |
|------|------|
| PTZ 控制 | 方向键(3x3)、Zoom±/Focus±、Home/Stop |
| VISCA 控制 | 串口配置、网络配置(TCP/UDP) |

### 2.2 样式规范

#### 颜色
```
背景色:    #fff (主) / #f8f8f8 (面板) / #f0f2f5 (卡片)
边框色:    #e0e0e0 (浅色) / #ccc (标准) / #aaa (输入框)
主按钮:    #0078d4
危险按钮:  #c42b1c
文字色:    #333 (主) / #555 (次) / #666 (标签)
```

#### 圆角
- 所有面板/按钮/输入框：6px
- Tab 标签顶部：4px
- 下拉列表：6px

---

## 3. 待实现功能（Next Steps）

### 3.1 视频流接入

#### USB 摄像头
- [ ] 枚举可用 USB 设备
- [ ] 读取支持的格式/分辨率/帧率
- [ ] 调用 PySide6.QtMultimedia 或 OpenCV 捕获
- [ ] 实时显示到预览区

#### RTSP 流
- [ ] 使用 OpenCV (cv2.VideoCapture) 或 FFmpeg
- [ ] 支持 UDP/TCP 传输
- [ ] 支持 Basic/Digest 认证
- [ ] 多网卡绑定选择

#### NDI
- [ ] 集成 NDI SDK (Python bindings)
- [ ] 发现局域网 NDI 源
- [ ] 接收并解码视频帧

#### ONVIF
- [ ] 使用 python-onvif-zeep 库
- [ ] 设备发现 (WS-Discovery)
- [ ] PTZ 控制接口对接
- [ ] 获取 RTSP 地址

### 3.2 PTZ 控制实现

#### VISCA 串口
- [ ] pyserial 库集成
- [ ] 串口参数配置生效
- [ ] VISCA 协议命令封装
- [ ] PTZ 方向/Zoom/Focus/Home 指令发送

#### VISCA over IP
- [ ] TCP/UDP Socket 连接
- [ ] VISCA IP 协议封装
- [ ] 心跳保持/断线重连

### 3.3 视频预览优化

- [ ] 隐藏 "视频预览区" 占位文字
- [ ] 实时帧率显示 (FPS)
- [ ] 分辨率/码率信息叠加
- [ ] 全屏预览功能

### 3.4 设置持久化

- [ ] 使用 QSettings 保存
- [ ] 记录上次使用的设备/配置
- [ ] 语言切换即时生效

---

## 4. 关键代码结构

### 4.1 类结构（模块化后）
```python
MainWindow (QMainWindow)
├── _setup_ui()
│   ├── _create_tab_widget() → 5个 Tab 实例
│   ├── _create_control_panels() → PTZPanel + VISCAPanel
│   └── _create_status_bar()
│
├── _create_preview_for_tab() → PreviewWidget
├── _update_preview_sizes() → 16:9 自适应
│
├── PreviewWidget (QFrame)
│   ├── video_frame: QFrame
│   ├── placeholder_label: QLabel
│   └── update_video_size()
│
├── PTZPanel (QFrame)
│   ├── _create_dpad() → 方向控制
│   ├── _create_zoom_focus_controls()
│   └── _create_home_stop_controls()
│
├── VISCAPanel (QFrame)
│   ├── _create_serial_tab() → 串口配置
│   └── _create_network_tab() → 网络配置
│
└── Tab 页面 (QWidget)
    ├── USBTab / RTSPTab / NDITab / ONVIFTab
    └── SettingsTab
```

### 4.2 重要接口

#### 视频分辨率设置（PreviewWidget）
```python
class PreviewWidget:
    def update_video_size(self, container_width: int, container_height: int) -> None:
        """更新视频帧尺寸，保持 16:9 比例"""
        
    def hide_placeholder(self) -> None:
        """视频播放时隐藏占位文字"""
        
    def show_placeholder(self) -> None:
        """视频停止时显示占位文字"""
```

#### 状态回调设置
```python
# PTZPanel / VISCAPanel / Tab 页面
panel.set_status_callback(callback: Callable[[str], None])
```

#### 主窗口状态更新
```python
main_window.update_status(text: str) -> None
    """更新状态栏文本"""
```

#### 全局样式应用
```python
from app.styles.theme import get_global_stylesheet
app.setStyleSheet(get_global_stylesheet(arrow_svg_path))
```

### 4.3 调试与日志

#### 运行方式

| 脚本 | 用途 | 日志位置 |
|------|------|----------|
| `run.bat` | 正常启动 | `logs/ptzcam_*.log` |
| `run_debug.bat` | 调试模式 | `logs/ptzcam_*.log` + 控制台 |
| `run_debug_console.bat` | 仅控制台调试 | 控制台（不生成文件） |

#### 命令行参数
```bash
python main.py              # 正常模式
python main.py --debug      # 调试模式（详细日志）
python main.py --debug --no-log-file  # 仅控制台日志
```

#### 日志使用
```python
from app.utils.logger import get_logger

logger = get_logger(__name__)
logger.debug("Debug message")    # 仅在 --debug 时显示
logger.info("Info message")      # 始终显示
logger.warning("Warning")
logger.error("Error")
```

日志文件保存在 `logs/ptzcam_YYYYMMDD_HHMMSS.log`

---

## 5. 技术踩坑记录

### 5.1 已解决
1. **QResizeEvent 导入**: 在 `QtGui` 不在 `QtCore`
2. **DPI 策略**: 必须在 `QApplication()` 构造前设置
3. **深色系统**: 强制浅色主题防白字问题
4. **Tab 样式**: pane 用 `margin-top: -1px` 与 tab 融合
5. **窗口比例**: 移除了 16:10 约束，改为自由缩放

### 5.2 待注意
1. **电量/性能**: 视频捕获线程需优化，避免主线程阻塞
2. **资源释放**: 关闭窗口时需停止视频流、关闭串口
3. **错误处理**: 设备断开/网络超时需有友好提示

---

## 6. 推荐实现顺序

### Phase 1: USB 摄像头 (MVP)
- [ ] OpenCV 集成
- [ ] 设备枚举
- [ ] 实时预览
- [ ] 基础 PTZ (VISCA串口)

### Phase 2: 网络流
- [ ] RTSP 播放
- [ ] ONVIF 控制
- [ ] NDI 接收

### Phase 3: 功能完善
- [ ] 录制/截图
- [ ] 预设位管理
- [ ] 多设备同时连接

---

## 7. 依赖安装

```bash
# 基础依赖
pip install PySide6

# 视频处理
pip install opencv-python
pip install numpy

# 串口
pip install pyserial

# ONVIF (可选)
pip install onvif-zeep

# NDI (需手动安装 NDI SDK)
```

---

## 8. 联系方式

**项目负责人**: 飛鳥  
**产品方向**: 会议摄像机、全向麦克风控制工具  
**坐标**: 深圳

---

*本文档由小鸟 AI 助手于 2026-04-30 生成*  
*版本: V 0.9.430_2506f44*
