# PTZ-Cam-Tools

会议摄像机多功能控制工具，面向视频会议场景的音视频产品。

## 功能模块

- **USB 摄像头控制** — 设备枚举、格式/分辨率/帧率选择、实时预览
- **RTSP 流媒体** — RTSP 视频流接入
- **NDI 接入** — NDI 源发现与接收
- **ONVIF 控制** — ONVIF 设备发现与配置
- **PTZ 控制** — 云台方向、变焦、聚焦控制（VISCA 串口/网络协议）
- **视频录制与截图**（开发中）

## 技术栈

- **UI 框架**：PySide6 (Qt for Python) 6.11.0
- **视频处理**：OpenCV 4.13.0 (DirectShow 后端) + FFmpeg 7.1
- **PTZ 协议**：VISCA (串口 9600 8N1 / TCP 5678 / UDP 52381)
- **其他**：comtypes (DirectShow COM API)

## 快速开始

```bash
# 安装依赖
pip install -r ptzcam-qt6/requirements.txt

# 启动程序
cd ptzcam-qt6 && python main.py

# 调试模式
cd ptzcam-qt6 && python main.py --debug
```

## 项目结构

```
ptzcam-qt6/
├── app/             # Python 应用主包
│   ├── main_window.py
│   ├── styles/      # UI 样式表
│   ├── tabs/        # 功能 Tab 页面
│   ├── utils/       # 工具模块
│   └── widgets/     # 可复用组件
├── tests/           # 单元测试
├── thirdparty/      # 第三方依赖 (FFmpeg, AMCap)
├── CHANGELOG.md     # 版本迭代记录
├── HANDOVER.md      # 项目交接说明
├── TECH_HANDOVER.md # 技术架构文档
└── main.py          # 入口文件
```

## 版本格式

`V {主版本号}.{迭代次数}.{日期}_{git版本} By Asuka`

- **主版本号**：大版本迭代（0 = 开发中）
- **迭代次数**：累计迭代次数
- **日期**：MDD 格式（如 506 = 5月6日）
- **git版本**：commit hash 前7位

当前版本：**V 0.16.506_2a319d9 By Asuka**

## 更新日志（最新）

**V 0.16.506** — UI 视觉优化（背景图 + Tab 半透明 + 按钮修复）

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

完整历史：参见 [CHANGELOG.md](./CHANGELOG.md)

---

© 2026 Asuka. Shenzhen.
