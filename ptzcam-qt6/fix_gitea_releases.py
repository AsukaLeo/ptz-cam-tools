# -*- coding: utf-8 -*-
"""Fix garbled Chinese text in Gitea releases for V0.34-V0.36."""
import json
import urllib.request

GITEA_API = "https://gitea.feiniaoyun.cn/api/v1/repos/FNY/PTZ-Camara/releases"
AUTH = "Buddy:David2008"

RELEASES = {
    22: {
        "name": "V 0.34.511 — 自适应深色/浅色模式 Logo",
        "body": """## V 0.34.511_ac873ce — 自适应系统深色/浅色模式 Logo

### 功能
- **自适应图标**: 使用 QStyleHints.colorScheme() 检测系统深色/浅色模式
  - 深色模式 → 加载 app_dark.ico（亮色图标，适配深色任务栏）
  - 浅色模式 → 加载 app_light.ico（深色图标，适配浅色任务栏）
- **运行时切换**: 注册 colorSchemeChanged 信号，系统切换深浅模式时自动跟换图标
- **图标文件管理**: app_square.ico 重命名为 app_dark.ico，新增 app_light.ico 及源文件 app_ico_light.png

### 修改文件（3 files, +18/-7）
```
main.py              |  21   图标自适应逻辑（colorScheme检测+信号连接）
build_exe.bat        |   2   PyInstaller打包图标改为app_dark.ico
assets/app_square.ico → app_dark.ico | 重命名
assets/app_light.ico | 新增  浅色模式图标
```

### 踩坑记录
- 无""",
    },
    23: {
        "name": "V 0.35.511_24f62b0 By Asuka",
        "body": """## V 0.35.511_24f62b0 — 修复中文编码乱码（第一版）

### 修复
- **所有含中文的 .py 文件添加 `# -*- coding: utf-8 -*-` 声明**（15 个文件）
- **新增 .gitattributes** 声明 Python 文件为 UTF-8 编码、CRLF 行尾
- 修复 PyInstaller 编译后 EXE 中文 UI 文本乱码（之前缺少编码声明，Windows 环境下中文被错误解析）

### 修改文件（17 files, +34/-3）
```
.gitattributes          |   16  新增
app/main_window.py      |    1  添加 UTF-8 声明
app/tabs/usb_tab.py     |    1  ↑
app/tabs/rtsp_tab.py    |    1  ↑
app/tabs/ndi_tab.py     |    1  ↑
app/tabs/onvif_tab.py   |    1  ↑
app/utils/constants.py  |    3  UTF-8 声明 + 版本号
app/utils/debug_overlay.py     |    1  UTF-8 声明
app/utils/i18n.py       |    1  ↑
app/utils/ndi_capture.py       |    1  ↑
app/utils/network_utils.py     |    1  ↑
app/utils/onvif_device.py      |    1  ↑
app/utils/visca_controller.py  |    1  ↑
app/widgets/ptz_panel.py       |    1  ↑
app/widgets/visca_panel.py     |    1  ↑
app/widgets/help_card.py       |    1  ↑
PTZ-Cam-Tools.spec             |    2  重新生成
```

### 踩坑记录
- ⚠️ 此版本修复不完整：源码 UTF-8 声明 ≠ 运行时 UTF-8 mode
- 详见 V 0.36.511 的 Runtime Hook 方案""",
    },
    24: {
        "name": "V 0.36.511_34bf09c By Asuka",
        "body": """## V 0.36.511_34bf09c — 修复中文文本编码（Runtime Hook）

### 背景
V 0.35.511 虽然添加了源码 UTF-8 声明和 .gitattributes，字节码验证也通过了，但 **PyInstaller 冻结后在 Windows 系统因 GBK/cp936 locale，运行时 Python 默认使用系统 locale 编码**，导致中文 UI 文本再次乱码。

### 修复
- **新增 runtime_hook_utf8.py** — PyInstaller runtime hook，强制 frozen app 使用 UTF-8 mode
  - sys.stdin/stdout/stderr.reconfigure(encoding='utf-8')
  - 设置 PYTHONUTF8=1 / PYTHONIOENCODING=utf-8
- **构建命令**: PYTHONUTF8=1 python -m PyInstaller --runtime-hook runtime_hook_utf8.py ...
- 清除所有缓存重新编译

### 修改文件
```
runtime_hook_utf8.py     |  20  新增（UTF-8 运行时强制）
main.py                  |   1  添加 UTF-8 声明
app/utils/constants.py   |   2  版本号 V 0.36.511
```

### 踩坑记录
- PyInstaller 的 PYZ 是 ZlibArchive 格式，不是标准 zip（zipfile 打不开）
- ZlibArchiveReader.extract() 返回 code 对象，不是 bytes
- Windows locale cp936 会覆盖源码 UTF-8 声明""",
    },
}


def fix_release(rel_id: int, name: str, body: str):
    """PATCH a Gitea release with proper UTF-8 content."""
    url = f"{GITEA_API}/{rel_id}"

    data = json.dumps({"name": name, "body": body}, ensure_ascii=False).encode("utf-8")

    auth_bytes = AUTH.encode("ascii")
    auth_header = "Basic " + __import__("base64").b64encode(auth_bytes).decode("ascii")

    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": auth_header,
        },
        method="PATCH",
    )

    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            print(f"✅ Release {rel_id} ({result.get('tag_name','?')}) updated: {name}")
            return True
    except urllib.error.HTTPError as e:
        body_text = e.read().decode("utf-8", errors="replace")
        print(f"❌ Release {rel_id} failed: HTTP {e.code} — {body_text[:200]}")
        return False


def main():
    for rel_id in sorted(RELEASES.keys()):
        info = RELEASES[rel_id]
        fix_release(rel_id, info["name"], info["body"])


if __name__ == "__main__":
    main()
