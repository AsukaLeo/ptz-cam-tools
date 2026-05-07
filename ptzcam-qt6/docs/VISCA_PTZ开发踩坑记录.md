# VISCA PTZ 控制开发踩坑记录

> 对应产品：动狐PTZ摄像机 · 协议版本 V1.0.3 · Sony FCB-CV7310 机芯
> 编写时间：2026-05-07

---

## 一、协议版本与参考文档

### 1.1 使用的文档

| 文档 | 作用 | 位置 |
|------|------|------|
| `动狐PTZ摄像机 VISCA 通讯协议V1.0.3.docx` | 产品自有协议（变焦/聚焦/白平衡等） | `assets/` |
| `动狐PTZ摄像机 VISCA 通讯协议V1.0.3.pdf` | 同上，PDF 版 | 产品资料库 |
| `Sony FCB-CV7310 Technical Manual (CV7310_TM.pdf)` | Sony 标准 VISCA 命令参考 | 产品资料库 |
| `misterhay/VISCA-IP-Controller` | 开源 VISCA over IP 参考实现 | GitHub |

### 1.2 关键发现

**动狐协议文档只记录了自家扩展指令（变焦/聚焦/ICR/OSD 等），标准 Pan-Tilt 指令在文档中没有列出。** Pan-tilt Drive (`06 01`) 和 Home (`06 04`) 属于标准 Sony VISCA 指令，所有支持 VISCA 的 PTZ 一体机都应支持。

---

## 二、Pan-Tilt Drive 命令格式（核心）

### 2.1 标准 Sony VISCA 格式

```
Byte:   0    1    2    3    4     5     6    7    8
       [Header][Cat.][Sub][Type][PanSpd][TiltSpd][PanDir][TiltDir][FF]
        0x81  0x01 0x06 0x01  0x01~  0x01~  0x01~  0x01~  0xFF
                                0x18   0x18  0x03   0x03
```

### 2.2 方向值（踩坑最多的地方）

```
Pan 方向（Byte 6 = 0Y）:
  0x01 = 左 (Left)
  0x02 = 右 (Right)
  0x03 = 停止/居中 (Stop/Center)

Tilt 方向（Byte 7 = 0X）:
  0x01 = 下 (Down)
  0x02 = 上 (Up)    ← 这是最容易搞错的值！
  0x03 = 停止/居中 (Stop/Center)
```

### 2.3 ❌ 之前错误的实现

```python
# 错：Tilt Up = 0x03
tdir = {0: 0, -1: 3, 1: 1}  # up=3
# 造成的问题：Cardinal方向不工作，对角方向值不对
```

### 2.4 ✅ 正确的实现

```python
# 正确：Tilt Up = 0x02（Sony 标准）
tdir = {0: 3, -1: 2, 1: 1}  # center=3, up=2, down=1
pdir = {0: 3, -1: 1, 1: 2}  # center=3, left=1, right=2
```

### 2.5 Byte 顺序（Byte 6 vs Byte 7）

**标准 Sony VISCA 定义：Byte 6 = Pan 方向, Byte 7 = Tilt 方向**

```
格式: 81 01 06 01 VV WW 0Y 0X FF
      0Y = Pan dir
      0X = Tilt dir
```

**注意**：网络上很多资料对 `0Y 0X` 的解释是反的（说 0Y=Tilt, 0X=Pan），但 Sony 官方文档证实 `0Y=Pan, 0X=Tilt`。以 Sony 官方文档为准。

### 2.6 单轴运动时另一轴的处理

当只运动一个方向（如只上、只左）时，**另一方向必须设为 0x03（居中/停止），不能设为 0x00（无效值）**。

```python
# 上：pan=3(center), tilt=2(up)
build_pan_tilt(5, 5, 3, 2)  →  81 01 06 01 05 05 03 02 FF

# 左：pan=1(left), tilt=3(center)
build_pan_tilt(5, 5, 1, 3)  →  81 01 06 01 05 05 01 03 FF
```

如果设为 0x00，**某些相机会把整个命令当作无效命令忽略**，导致方向键不响应。

---

## 三、命令对照表

### 3.1 Pan-Tilt

| 动作 | 命令 | 说明 |
|------|------|------|
| 上 | `81 01 06 01 05 05 03 02 FF` | pan=3(center), tilt=2(up) |
| 下 | `81 01 06 01 05 05 03 01 FF` | pan=3(center), tilt=1(down) |
| 左 | `81 01 06 01 05 05 01 03 FF` | pan=1(left), tilt=3(center) |
| 右 | `81 01 06 01 05 05 02 03 FF` | pan=2(right), tilt=3(center) |
| 左上 | `81 01 06 01 05 05 01 02 FF` | pan=1(left), tilt=2(up) |
| 右上 | `81 01 06 01 05 05 02 02 FF` | pan=2(right), tilt=2(up) |
| 左下 | `81 01 06 01 05 05 01 01 FF` | pan=1(left), tilt=1(down) |
| 右下 | `81 01 06 01 05 05 02 01 FF` | pan=2(right), tilt=1(down) |
| 停止 | `81 01 06 01 00 00 03 03 FF` | speed=0, 方向=3(stop) |
| Home | `81 01 06 04 FF` | 回到 Home 位 |

### 3.2 Zoom

| 动作 | 命令 | 说明 |
|------|------|------|
| 停止 | `81 01 04 07 00 FF` | |
| Tele(标准) | `81 01 04 07 02 FF` | 固定速度 |
| Wide(标准) | `81 01 04 07 03 FF` | 固定速度 |
| Tele(变速) | `81 01 04 07 2p FF` | p = 0(最慢) ~ 7(最快) |
| Wide(变速) | `81 01 04 07 3p FF` | p = 0(最慢) ~ 7(最快) |

### 3.3 Focus

| 动作 | 命令 | 说明 |
|------|------|------|
| 停止 | `81 01 04 08 00 FF` | |
| 远焦(标准) | `81 01 04 08 02 FF` | |
| 近焦(标准) | `81 01 04 08 03 FF` | |
| 远焦(变速) | `81 01 04 08 2p FF` | p = 0(最慢) ~ 7(最快) |
| 近焦(变速) | `81 01 04 08 3p FF` | p = 0(最慢) ~ 7(最快) |

### 3.4 地址与初始化

| 动作 | 命令 | 说明 |
|------|------|------|
| 地址分配 | `88 30 01 FF` | 设置相机地址为 1（广播） |
| IF_Clear | `81 01 00 01 FF` | 清空命令缓冲区 |

---

## 四、UDP vs TCP 差异

### 4.1 UDP 不可靠性

VISCA over UDP（默认端口 52381）是 fire-and-forget，**UDP 不保证命令送达**。这会导致：

- 方向命令丢了 → 相机不动
- 停止命令丢了 → 相机一直运动不停
- Home 命令丢了 → 相机不回中

**解决方案**：每条命令在 UDP 下发送 3 次（非阻塞）。

```python
retries = self._STOP_RETRY_COUNT if self._transport_type == "udp" else 1
for _ in range(retries):
    self._transport.send(cmd)
```

### 4.2 TCP 可靠性

TCP（默认端口 5678）有重传机制，一条命令发一次即可。

### 4.3 状态检查

VISCA over TCP 可以用 `socket.is_connected()` 检测断线。UDP 没有连接概念，需要应用层心跳。

---

## 五、不同品牌相机的兼容性问题

### 5.1 遇到的差异

| 相机 | 协议 | Tilt Up 值 | Home | 备注 |
|------|------|-----------|------|------|
| Camera 1 (192.168.1.253) | UDP | 标准 **0x02** ✅ | ❌ 不支持 | 可能不支持标准 Home |
| Camera 2 (192.168.2.254) | TCP | 标准 **0x02** ✅ | ✅ | 标准兼容 |

### 5.2 倾斜方向反转开关

部分非标相机（如某些大华/海康）的 Tilt Up/Down 值与 Sony 标准相反。**添加了"倾斜方向反转"复选框**，勾选时互换 up↔down：

```python
if self._controller and self._controller.tilt_reverse:
    tdir = {1: 2, 2: 1}.get(tdir, tdir)  # swap 1↔2
```

**位置**：VISCA 面板 → 网络选项卡 → 底部复选框。

---

## 六、Qt 按钮控制模式

### 6.1 问题：Zoom/Focus/PTZ 松开不停

**根因**：按钮用 `clicked` 信号（点按），只发一次 start 命令，松开不发 stop。

**修复**：所有运动按钮改用 `pressed` / `released` 信号：

```python
# 之前（只发一次，松开不停）
btn.clicked.connect(lambda: self._do_zoom(3))

# 之后（按住持续运动，松开停止）
btn.pressed.connect(lambda: self._do_zoom(3))
btn.released.connect(lambda: self._do_zoom(0))
```

### 6.2 按钮类型分工

| 方法 | 信号 | 用途 |
|------|------|------|
| `_create_dir_btn()` | `pressed`/`released` | 方向键（8方向） |
| `_create_press_btn()` | `pressed`/`released` | Zoom/Focus 键 |
| `_create_ptz_btn()` | `clicked` | 停止/Home 等单次动作 |

---

## 七、其他踩坑记录

### 7.1 zoom(0) / focus(0) 被覆盖

**症状**：Zoom+ 按下能变焦，但松开后继续变焦不停。
**根因**：ViscaController 里 `zoom(0)` 被替换成了默认速度 3。

```python
# ❌ 之前的代码
def zoom(self, speed=0):
    if speed == 0:
        speed = self.ZOOM_SPEED  # 0 被覆盖成 3，停不了！
    ...

# ✅ 修复后
def zoom(self, speed=0):
    # speed=0 透传给 build_zoom(0) → 停止命令
    return self._send(build_zoom(speed))
```

### 7.2 build_zoom 方向字节错误

**症状**：Zoom+ 按了之后画面反而缩小（方向反了）。
**根因**：Tele 应该用 `0x20 | p`，Wide 应该用 `0x30 | p`，但代码把 Tele 写成了 `p`（实际是 Wide 的标准速度 03），Wide 写成了 `0x20 | p`（实际是 Tele 变速）。

```python
# ❌ 之前
if speed > 0: p = min(speed, 7)     # → 03 = Wide(标准)
elif speed < 0: p = 0x20 | min(-speed, 7)  # → 23 = Tele(变速)

# ✅ 修复后
if speed > 0: p = 0x20 | min(speed, 7)  # → 23 = Tele(变速)
elif speed < 0: p = 0x30 | min(-speed, 7)  # → 33 = Wide(变速)
```

### 7.3 缺少地址初始化

**症状**：所有 VISCA 命令无响应。
**根因**：连接后没发 `88 30 01 FF` 分配地址。
**修复**：`connect_udp/tcp/serial` 后立即调用 `_init_address()`。

### 7.4 代码引用问题

**`build_pan_tilt_stop()` 的停止值**：

| 版本 | 值 | 结果 |
|------|----|------|
| 最初 | `03 03` | ✓ 标准 Sony 停止值 |
| 第一次修改 | `00 00` | ✗ 部分相机不识别 |
| 最终修正 | `03 03` | ✓ 回到标准值 |

---

## 八、代码文件结构

### 8.1 相关文件

```
app/utils/
├── visca_protocol.py      # 命令构造 + 响应解析（build_zoom/build_pan_tilt 等）
├── visca_transport.py      # 传输层（Serial/UDP/TCP）
└── visca_controller.py     # 控制器（连接管理 + 命令分发）

app/widgets/
├── ptz_panel.py            # PTZ 控制面板（8方向 + Zoom/Focus/Home）
└── visca_panel.py          # VISCA 配置面板（串口/网络切换 + 倾斜反转）
```

### 8.2 数据流

```
按钮 press/release
    → PTZPanel._do_ptz(pan_dir, tilt_dir)
        → 映射为标准 VISCA 方向值（pan=1/2/3, tilt=1/2/3）
        → ViscaController.pan_tilt(pan_dir, tilt_dir)
            → build_pan_tilt(speed, speed, pan_dir, tilt_dir)
                → bytes([0x81, 0x01, 0x06, 0x01, VV, WW, 0Y, 0X, 0xFF])
            → UdpTransport.send(bytes) 或 TcpTransport.send(bytes)
```

---

## 九、测试验证指引

### 9.1 快速验证命令是否正确

```python
# 验证 Sony 标准命令
from app.utils.visca_protocol import *

print('上:', build_pan_tilt(5,5,3,2).hex())  # → 8101060105050302ff
print('下:', build_pan_tilt(5,5,3,1).hex())  # → 8101060105050301ff
print('左:', build_pan_tilt(5,5,1,3).hex())  # → 8101060105050103ff
print('右:', build_pan_tilt(5,5,2,3).hex())  # → 8101060105050203ff
print('停止:', build_pan_tilt_stop().hex())   # → 8101060100000303ff
print('Zoom+:6', build_zoom(6).hex())         # → 8101040726ff
print('Zoom-:6', build_zoom(-6).hex())        # → 8101040736ff
```

### 9.2 多相机测试矩阵

| 测试项 | Camera 1 (UDP) | Camera 2 (TCP) |
|--------|---------------|---------------|
| 上 | ✅ 标准 Up=0x02 | ✅ |
| 下 | ✅ | ✅ |
| 左 | ✅ | ✅ |
| 右 | ✅ | ✅ |
| 左上/右上/左下/右下 | ✅ | ✅ |
| 停止 | ✅ | ✅ |
| Home | ❌ 不支持 | ✅ |
| Zoom+/- | ✅ | ✅ |
| Focus+/- | ✅ | ✅ |

---

## 十、参考资料

1. Sony FCB-CV7310 Technical Manual (A-EW4-100-01(1)) — VISCA Command List 章节
2. 动狐PTZ摄像机 VISCA 通讯协议 V1.0.3
3. misterhay/VISCA-IP-Controller (https://github.com/misterhay/VISCA-IP-Controller)
4. PySide6 QPushButton pressed/released 信号文档
