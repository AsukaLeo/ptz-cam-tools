# PTZ-Cam-Tools

会议摄像机多功能控制工具，面向视频会议场景的音视频产品。

## 功能模块

- **USB 摄像头控制** — 设备枚举、格式/分辨率/帧率选择、实时预览
- **RTSP 流媒体** — RTSP 视频流接入
- **NDI 接入** — NDI 源发现与接收（NDI SDK v6）
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

当前版本：**V 0.28.507_6c93be4 By Asuka**

## 更新日志（最新）

**V 0.28.507** — Slim Edition：体积优化（233MB→98MB，-58%）

### 功能
- **USB 摄像头控制** — 设备枚举、格式/分辨率/帧率选择、实时预览
- **RTSP 流媒体** — RTSP 视频流接入、网卡选择、传输协议切换
- **NDI 接入** — NDI 源发现与接收（NDI SDK v6）
- **ONVIF 控制** — ONVIF 设备发现、默认凭据自动探测、RTSP 拉流
- **PTZ 控制** — Sony VISCA 标准协议、八方向压感控制、预置位管理、速度滑块
- 预置位 0-9 设置/清除/调用
- 云台速度 1~24 滑动条（实时调整）
- 变焦速度 1~7 滑动条（实时调整）
- 串口后台异步连接（5 秒超时不卡 UI）
- 视频信息仅跟随激活 Tab
- VISCA 连接/断开按钮变色 + 配置禁用
- 状态栏视频信息跟随 Tab 切换
- 输入框点击全选 + 清空按钮
- 视频预览区 30% 半透明背景
- ONVIF 自动尝试 20 组常用出厂默认凭据
- VISCA 倾斜方向反转，适配不同品牌相机
- 视频源 IP 自动填充 VISCA 地址
- 协议-端口联动（TCP→5678, UDP→52381）

完整历史：参见 [CHANGELOG.md](./CHANGELOG.md)

---

© 2026 Asuka. Shenzhen.
