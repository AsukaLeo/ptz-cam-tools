# USB 摄像头功能开发计划

**版本**: V 0.11.430  
**日期**: 2026-04-30  
**状态**: 计划中  

---

## 1. 技术方案选型

### 方案对比

| 方案 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| **PySide6.QtMultimedia** | 与现有框架集成好，跨平台 | 功能相对简单 | **首选方案** - 设备枚举+预览 |
| **OpenCV (cv2)** | 简单易用，文档丰富 | 无法枚举设备信息 | 视频捕获备用 |
| **DirectShow (COM)** | Windows原生，功能完整 | 仅Windows，代码复杂 | 高级功能扩展 |
| **FFmpeg + Python绑定** | 功能强大，格式支持广 | 需要额外依赖 | 视频处理/转码 |

### 推荐架构

```
┌─────────────────────────────────────────────────────────────┐
│                      USBTab (UI Layer)                      │
├─────────────────────────────────────────────────────────────┤
│              CameraController (控制层)                      │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│   │   Device     │  │   Video      │  │   Format     │    │
│   │   Manager    │  │   Capture    │  │   Manager    │    │
│   └──────────────┘  └──────────────┘  └──────────────┘    │
├─────────────────────────────────────────────────────────────┤
│                   Backend (后端层)                          │
│   PySide6.QtMultimedia    OpenCV (备用)    FFmpeg (扩展)   │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. 开发阶段规划

### Phase 1: 设备枚举 (Week 1)

**目标**: 实现 USB 摄像头设备的发现与选择

#### 任务清单

- [ ] **1.1 创建设备管理器模块**
  - 文件: `app/utils/device_manager.py`
  - 功能: 封装设备枚举逻辑
  - 接口:
    ```python
    class DeviceManager:
        def enumerate_devices(self) -> List[CameraDevice]
        def get_device_info(self, device_id: str) -> DeviceInfo
    ```

- [ ] **1.2 QtMultimedia 设备枚举**
  - 使用 `QMediaDevices.videoInputs()`
  - 获取设备名称、ID、默认分辨率
  - 处理设备热插拔事件

- [ ] **1.3 更新 USBTab UI**
  - 设备下拉框绑定枚举结果
  - 实时刷新按钮
  - 设备选择回调

- [ ] **1.4 错误处理**
  - 无设备提示
  - 设备被占用检测
  - 权限不足处理

#### 技术要点

```python
from PySide6.QtMultimedia import QMediaDevices, QCameraDevice

devices = QMediaDevices.videoInputs()
for device in devices:
    print(f"ID: {device.id()}")
    print(f"Name: {device.description()}")
    print(f"Default res: {device.photoResolutions()[0]}")
```

---

### Phase 2: 视频捕获与预览 (Week 2)

**目标**: 实现视频流的捕获与实时预览

#### 任务清单

- [ ] **2.1 创建视频捕获模块**
  - 文件: `app/utils/video_capture.py`
  - 类: `VideoCaptureThread` (QThread)
  - 功能: 后台捕获视频帧

- [ ] **2.2 集成 QCamera + QMediaCaptureSession**
  - 设置视频源
  - 配置视频接收器
  - 帧率控制

- [ ] **2.3 预览显示实现**
  - 修改 `PreviewWidget` 支持实时视频
  - QVideoWidget 集成
  - 保持 16:9 比例自适应

- [ ] **2.4 播放控制**
  - 播放/暂停/停止
  - 状态同步到 UI
  - 错误恢复机制

#### 技术要点

```python
from PySide6.QtMultimedia import QCamera, QMediaCaptureSession
from PySide6.QtMultimediaWidgets import QVideoWidget

# 创建相机实例
camera = QCamera(device)
session = QMediaCaptureSession()
session.setCamera(camera)
session.setVideoOutput(video_widget)
camera.start()
```

---

### Phase 3: 格式与分辨率配置 (Week 3)

**目标**: 实现分辨率、格式、帧率的动态配置

#### 任务清单

- [ ] **3.1 格式枚举**
  - 读取设备支持的所有格式
  - YUY2 / MJPEG / H264 等
  - 分辨率列表

- [ ] **3.2 格式选择 UI**
  - 分辨率下拉框动态更新
  - 格式选择下拉框
  - 帧率选择

- [ ] **3.3 实时切换**
  - 不重启预览切换分辨率
  - 保持播放状态
  - 平滑过渡

- [ ] **3.4 配置持久化**
  - QSettings 保存用户选择
  - 下次启动恢复

#### 技术要点

```python
# 获取支持的格式
formats = camera.cameraFormat()
for fmt in formats:
    print(f"Resolution: {fmt.resolution()}")
    print(f"Pixel Format: {fmt.pixelFormat()}")
    print(f"Frame Rate: {fmt.minFrameRate()}-{fmt.maxFrameRate()}")
```

---

### Phase 4: 高级功能 (Week 4)

**目标**: 添加截图、录制、参数调节等功能

#### 任务清单

- [ ] **4.1 截图功能**
  - 捕获当前帧保存为图片
  - 快捷键支持 (Ctrl+S)
  - 保存路径选择

- [ ] **4.2 视频录制**
  - QMediaRecorder 集成
  - 录制格式选择 (MP4/AVI)
  - 录制状态指示

- [ ] **4.3 摄像头参数调节**
  - 亮度/对比度/饱和度
  - 曝光控制
  - 白平衡

- [ ] **4.4 性能优化**
  - 帧率统计 (FPS 显示)
  - 内存占用监控
  - 延迟优化

---

## 3. 模块设计

### 3.1 设备管理器 (device_manager.py)

```python
from typing import List, Optional
from dataclasses import dataclass
from PySide6.QtMultimedia import QMediaDevices, QCameraDevice

@dataclass
class CameraDevice:
    id: str
    name: str
    description: str
    is_default: bool
    photo_resolutions: List[tuple]
    video_formats: List[CameraFormat]

@dataclass
class CameraFormat:
    resolution: tuple
    pixel_format: str
    min_fps: float
    max_fps: float

class DeviceManager(QObject):
    """USB Camera device manager."""
    
    device_added = Signal(CameraDevice)
    device_removed = Signal(str)  # device_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._devices: Dict[str, CameraDevice] = {}
        self._setup_monitoring()
    
    def enumerate_devices(self) -> List[CameraDevice]:
        """Enumerate all available video capture devices."""
        devices = []
        for qdevice in QMediaDevices.videoInputs():
            device = self._convert_device(qdevice)
            devices.append(device)
            self._devices[device.id] = device
        return devices
    
    def get_device(self, device_id: str) -> Optional[CameraDevice]:
        """Get device info by ID."""
        return self._devices.get(device_id)
```

### 3.2 视频捕获器 (video_capture.py)

```python
from PySide6.QtCore import QThread, Signal
from PySide6.QtMultimedia import QCamera, QMediaCaptureSession
from PySide6.QtMultimediaWidgets import QVideoWidget

class VideoCaptureThread(QThread):
    """Video capture thread for USB camera."""
    
    frame_ready = Signal(QImage)
    error_occurred = Signal(str)
    state_changed = Signal(str)  # "playing", "paused", "stopped"
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._camera: Optional[QCamera] = None
        self._session: Optional[QMediaCaptureSession] = None
        self._video_widget: Optional[QVideoWidget] = None
        self._device_id: Optional[str] = None
    
    def start_capture(self, device_id: str, video_widget: QVideoWidget):
        """Start video capture from device."""
        self._device_id = device_id
        self._video_widget = video_widget
        self.start()
    
    def run(self):
        """Thread main loop."""
        try:
            # Create camera and session
            device = self._find_device(self._device_id)
            self._camera = QCamera(device)
            self._session = QMediaCaptureSession()
            self._session.setCamera(self._camera)
            self._session.setVideoOutput(self._video_widget)
            
            # Start capture
            self._camera.start()
            self.state_changed.emit("playing")
            
            # Run event loop
            self.exec()
            
        except Exception as e:
            self.error_occurred.emit(str(e))
    
    def stop_capture(self):
        """Stop video capture."""
        if self._camera:
            self._camera.stop()
        self.quit()
        self.wait()
        self.state_changed.emit("stopped")
```

### 3.3 USBTab 更新 (usb_tab.py)

```python
class USBTab(QWidget):
    """USB camera tab with full functionality."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._device_manager = DeviceManager(self)
        self._capture_thread: Optional[VideoCaptureThread] = None
        self._current_device: Optional[CameraDevice] = None
        self._is_playing = False
        
        self._setup_ui()
        self._connect_signals()
        self._enumerate_devices()
    
    def _connect_signals(self):
        """Connect device and capture signals."""
        # Device events
        self._device_manager.device_added.connect(self._on_device_added)
        self._device_manager.device_removed.connect(self._on_device_removed)
        
        # UI events
        self.device_combo.currentIndexChanged.connect(self._on_device_changed)
        self.play_btn.clicked.connect(self._toggle_playback)
        self.refresh_btn.clicked.connect(self._enumerate_devices)
        self.resolution_combo.currentIndexChanged.connect(self._on_resolution_changed)
    
    def _enumerate_devices(self):
        """Update device list."""
        self.device_combo.clear()
        devices = self._device_manager.enumerate_devices()
        
        if not devices:
            self.update_status("未检测到 USB 摄像头设备")
            return
        
        for device in devices:
            self.device_combo.addItem(device.name, device.id)
        
        self.update_status(f"检测到 {len(devices)} 个设备")
    
    def _toggle_playback(self):
        """Start or stop video playback."""
        if self._is_playing:
            self._stop_capture()
        else:
            self._start_capture()
    
    def _start_capture(self):
        """Start video capture."""
        device_id = self.device_combo.currentData()
        if not device_id:
            self.update_status("请先选择设备")
            return
        
        # Create capture thread
        self._capture_thread = VideoCaptureThread(self)
        self._capture_thread.state_changed.connect(self._on_state_changed)
        self._capture_thread.error_occurred.connect(self._on_capture_error)
        
        # Start capture
        preview_widget = self.preview_widget.video_frame
        self._capture_thread.start_capture(device_id, preview_widget)
        
        self._is_playing = True
        self.play_btn.setText("停止")
        self.update_status("正在播放...")
```

---

## 4. 依赖安装

### Python 依赖更新

```bash
# requirements.txt 添加
PySide6>=6.11.0
opencv-python>=4.8.0  # 备用方案
numpy>=1.24.0
```

### FFmpeg DLL 配置

项目已包含 FFmpeg DLL，如需使用：
- 将 `thirdparty/ffmpeg/bin/` 添加到 PATH
- 或使用 Python ctypes 直接调用

---

## 5. 测试计划

### 5.1 单元测试

```python
# tests/test_device_manager.py
class TestDeviceManager:
    def test_enumerate_devices(self):
        manager = DeviceManager()
        devices = manager.enumerate_devices()
        assert isinstance(devices, list)
    
    def test_device_info(self):
        manager = DeviceManager()
        devices = manager.enumerate_devices()
        if devices:
            device = devices[0]
            assert device.id
            assert device.name
```

### 5.2 集成测试

- [ ] 设备热插拔测试
- [ ] 多设备切换测试
- [ ] 长时间运行稳定性测试
- [ ] 内存泄漏检测

---

## 6. 风险与对策

| 风险 | 影响 | 对策 |
|------|------|------|
| QtMultimedia 不支持某些摄像头 | 高 | 准备 OpenCV 备用方案 |
| 设备被其他程序占用 | 中 | 友好提示，建议关闭其他程序 |
| 分辨率切换失败 | 中 | 回退到默认分辨率 |
| 性能问题（高分辨率卡顿） | 中 | 自动降帧率，提示用户 |
| Windows 权限问题 | 低 | UAC 提示，管理员权限运行 |

---

## 7. 交付标准

- [ ] 设备枚举成功率 > 95%
- [ ] 预览帧率 >= 25fps @ 1080p
- [ ] CPU 占用 < 15% (i5 处理器)
- [ ] 内存占用 < 200MB
- [ ] 无内存泄漏 (24小时运行)

---

## 8. 时间线

```
Week 1 (5/6-5/9):   Phase 1 - 设备枚举
Week 2 (5/12-5/16): Phase 2 - 视频捕获与预览
Week 3 (5/19-5/23): Phase 3 - 格式与分辨率
Week 4 (5/26-5/30): Phase 4 - 高级功能
```

---

*计划制定: 小鸟 AI 助手  
日期: 2026-04-30  
版本: V 0.11.430*
