# PTZ-Cam-Tools 项目交接文件

## 项目基本信息
- **项目名称**: PTZ-Cam-Tools
- **用途**: 音视频产品控制工具（会议摄像机、全向麦克风）
- **技术栈**: Python + PySide6 6.11.0
- **工作目录**: `C:/Users/asuka/WorkBuddy/20260429153616/ptzcam-qt6/`

## 版本号体系（重要）

**强制格式**: `V {主版本号}.{内测版}.{迭代次数}{日期}_{git版本}`

**当前版本**: `V 0.0.8430_c670e46`

### 字段说明
- **主版本号**: 0 = 开发中
- **内测版**: 0 = 内部测试
- **迭代次数**: 累计迭代次数（8次）
- **日期**: MDD 格式（430 = 4月30日）
- **git版本**: commit hash 前7位

### 更新规则
1. **每次提交 git 后必须更新版本号**
2. 在 `main.py` 第107行的 `version_label` 中更新
3. 同时更新 `C:/Users/asuka/WorkBuddy/20260429153616/.workbuddy/memory/MEMORY.md` 中的版本历史

## 文件结构

```
ptzcam-qt6/
├── main.py              # 主程序（PySide6实现）
├── mainwindow.h         # Qt6 C++ 头文件（备用）
├── mainwindow.cpp       # Qt6 C++ 实现（备用）
├── CMakeLists.txt       # CMake 配置
├── arrow_down.svg       # ComboBox 下拉箭头图标
├── run.bat              # Windows 启动脚本
├── requirements.txt     # Python 依赖
└── HANDOVER.md          # 本文件
```

## 运行方式

### Python 方式（推荐）
```bash
cd "C:/Users/asuka/WorkBuddy/20260429153616/ptzcam-qt6"
"C:/Users/asuka/.workbuddy/binaries/python/envs/ptzcam/Scripts/python.exe" main.py
```

### 启动脚本
双击 `run.bat`

## 近期迭代记录（V 0.0.8430）

- UI 细节调整第6轮
- Tab 标签 "USB预览" → "USB"
- USB Tab 参数行对齐、下拉框自适应
- PTZ 按钮重排（Zoom±/Focus± 交叉）
- 右下角版本署名

## 参考记忆文件

长期技术记录: `C:/Users/asuka/WorkBuddy/20260429153616/.workbuddy/memory/MEMORY.md`
每日工作记录: `C:/Users/asuka/WorkBuddy/20260429153616/.workbuddy/memory/YYYY-MM-DD.md`

## 交接人
飛鳥 @ 深圳
