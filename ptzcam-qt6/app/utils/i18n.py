"""Internationalization module — simple dict-based translation."""

from typing import Callable, Optional

# Translation map: English -> {中文, English}
_TRANSLATIONS = {
    "USB": {"zh": "USB", "en": "USB"},
    "RTSP": {"zh": "RTSP", "en": "RTSP"},
    "NDI": {"zh": "NDI", "en": "NDI"},
    "ONVIF": {"zh": "ONVIF", "en": "ONVIF"},
    "就绪": {"zh": "就绪", "en": "Ready"},
    "未连接": {"zh": "未连接", "en": "Disconnected"},
    "设置": {"zh": "设置", "en": "Settings"},
    "状态": {"zh": "状态", "en": "Status"},
    "PTZ 控制": {"zh": "PTZ 控制", "en": "PTZ Control"},
    "视频预览区": {"zh": "视频预览区", "en": "Video Preview"},
    "VISCA 控制": {"zh": "VISCA 控制", "en": "VISCA Control"},
    "云台速度": {"zh": "云台速度", "en": "Pan/Tilt Speed"},
    "变焦速度": {"zh": "变焦速度", "en": "Zoom Speed"},
    "预置位": {"zh": "预置位", "en": "Preset"},
    "变焦+": {"zh": "变焦+", "en": "Zoom+"},
    "变焦-": {"zh": "变焦-", "en": "Zoom-"},
    "聚焦+": {"zh": "聚焦+", "en": "Focus+"},
    "聚焦-": {"zh": "聚焦-", "en": "Focus-"},
    "设置": {"zh": "设置", "en": "Set"},
    "清除": {"zh": "清除", "en": "Clear"},
    "调用": {"zh": "调用", "en": "Call"},
    "协议:": {"zh": "协议:", "en": "Proto:"},
    "地址:": {"zh": "地址:", "en": "Addr:"},
    "端口:": {"zh": "端口:", "en": "Port:"},
    "连接": {"zh": "连接", "en": "Connect"},
    "断开": {"zh": "断开", "en": "Disconnect"},
    "连接中...": {"zh": "连接中...", "en": "Connecting..."},
    "连接失败": {"zh": "连接失败", "en": "Failed"},
    "连接超时": {"zh": "连接超时", "en": "Timeout"},
    "已连接": {"zh": "已连接", "en": "Connected"},
    "网络": {"zh": "网络", "en": "Network"},
    "串口": {"zh": "串口", "en": "Serial"},
    "方向反转 \u2714": {"zh": "方向反转 \u2714", "en": "Reverse \u2714"},
    "播放": {"zh": "播放", "en": "Play"},
    "停止": {"zh": "停止", "en": "Stop"},
    "刷新": {"zh": "刷新", "en": "Refresh"},
    "发现": {"zh": "发现", "en": "Discover"},
    "设备:": {"zh": "设备:", "en": "Device:"},
    "分辨率:": {"zh": "分辨率:", "en": "Resolution:"},
    "格式:": {"zh": "格式:", "en": "Format:"},
    "帧率:": {"zh": "帧率:", "en": "FPS:"},
    "用户名:": {"zh": "用户名:", "en": "User:"},
    "密码:": {"zh": "密码:", "en": "Pass:"},
    "网卡:": {"zh": "网卡:", "en": "NIC:"},
    "NDI 源:": {"zh": "NDI 源:", "en": "NDI Src:"},
    "IP 地址:": {"zh": "IP 地址:", "en": "IP:"},
    "用户:": {"zh": "用户:", "en": "User:"},
    "RTSP URL:": {"zh": "RTSP URL:", "en": "RTSP URL:"},
    "请求": {"zh": "请求", "en": "Request"},
    "视频已停止": {"zh": "视频已停止", "en": "Video stopped"},
    "视频播放中": {"zh": "视频播放中", "en": "Playing"},
    "错误：无法找到合适的视频格式": {"zh": "错误：无法找到合适的视频格式", "en": "No suitable video format"},
    "启动视频失败": {"zh": "启动视频失败", "en": "Failed to start video"},
    "请输入 RTSP URL": {"zh": "请输入 RTSP URL", "en": "Enter RTSP URL"},
    "请先选择 NDI 源": {"zh": "请先选择 NDI 源", "en": "Select NDI source first"},
    "请先选择一个预置位编号": {"zh": "请先选择一个预置位编号", "en": "Select preset number first"},
    "USB 使用说明": {"zh": "USB 使用说明", "en": "USB Instructions"},
    "RTSP 使用说明": {"zh": "RTSP 使用说明", "en": "RTSP Instructions"},
    "NDI 使用说明": {"zh": "NDI 使用说明", "en": "NDI Instructions"},
    "ONVIF 使用说明": {"zh": "ONVIF 使用说明", "en": "ONVIF Instructions"},
    "1. 下拉选择 USB 摄像头设备": {"zh": "1. 下拉选择 USB 摄像头设备", "en": "1. Select a USB camera"},
    "2. 点击「播放」开始预览": {"zh": "2. 点击「播放」开始预览", "en": "2. Click Play to preview"},
    "3. 点击「停止」结束预览": {"zh": "3. 点击「停止」结束预览", "en": "3. Click Stop to end"},
    "4. 可切换分辨率、格式和帧率": {"zh": "4. 可切换分辨率、格式和帧率", "en": "4. Adjust resolution, format, FPS"},
    "5. 点「刷新」重新检测设备": {"zh": "5. 点「刷新」重新检测设备", "en": "5. Click Refresh to rescan"},
    "1. 输入 RTSP 流媒体地址": {"zh": "1. 输入 RTSP 流媒体地址", "en": "1. Enter RTSP stream URL"},
    "2. 如有认证需填写用户名和密码": {"zh": "2. 如有认证需填写用户名和密码", "en": "2. Fill user/pass if required"},
    "3. 选择传输协议（UDP/TCP）": {"zh": "3. 选择传输协议（UDP/TCP）", "en": "3. Select protocol (UDP/TCP)"},
    "4. 点击「连接」开始拉流": {"zh": "4. 点击「连接」开始拉流", "en": "4. Click Connect to start"},
    "5. 点击「断开」停止播放": {"zh": "5. 点击「断开」停止播放", "en": "5. Click Disconnect to stop"},
    "1. 点击「刷新」搜索网络 NDI 源": {"zh": "1. 点击「刷新」搜索网络 NDI 源", "en": "1. Click Refresh to search NDI"},
    "2. 下拉选择目标 NDI 设备": {"zh": "2. 下拉选择目标 NDI 设备", "en": "2. Select target NDI device"},
    "3. 点击「连接」开始接收视频": {"zh": "3. 点击「连接」开始接收视频", "en": "3. Click Connect to receive"},
    "4. 非授权设备 15 分钟后可能断流": {"zh": "4. 非授权设备 15 分钟后可能断流", "en": "4. Unlicensed may drop after 15min"},
    "5. 5 秒无帧将提示可能为试用版": {"zh": "5. 5 秒无帧将提示可能为试用版", "en": "5. 5s no-frame = trial notice"},
    "1. 点击「发现」搜索网络设备": {"zh": "1. 点击「发现」搜索网络设备", "en": "1. Click Discover to search"},
    "2. 下拉选择目标 ONVIF 设备": {"zh": "2. 下拉选择目标 ONVIF 设备", "en": "2. Select target ONVIF device"},
    "3. 可输入自定义 IP 和凭据": {"zh": "3. 可输入自定义 IP 和凭据", "en": "3. Or enter custom IP/credentials"},
    "4. 点击「连接」自动探测配置": {"zh": "4. 点击「连接」自动探测配置", "en": "4. Click Connect to auto-probe"},
    "5. 凭据错误将自动尝试常见默认值": {"zh": "5. 凭据错误将自动尝试常见默认值", "en": "5. Auto-try defaults on auth fail"},
}

_current_lang = "zh"
_listeners: list[Callable[[str], None]] = []


def set_language(lang: str) -> None:
    """Switch language and notify all listeners.

    Args:
        lang: 'zh' or 'en'.
    """
    global _current_lang
    _current_lang = lang
    for cb in _listeners:
        cb(lang)


def get_language() -> str:
    """Get current language code."""
    return _current_lang


def on_language_change(callback: Callable[[str], None]) -> None:
    """Register a callback for language changes.

    Args:
        callback: Called with 'zh' or 'en' when language changes.
    """
    _listeners.append(callback)


def tr(text: str) -> str:
    """Translate a text string to the current language.

    Supports both forward lookup (zh key → en) and reverse lookup
    (en value → zh key) for round-trip language switching.

    Args:
        text: Text to translate (can be Chinese or English).

    Returns:
        Translated text.
    """
    # Direct lookup: text is a known key
    entry = _TRANSLATIONS.get(text)
    if entry:
        return entry.get(_current_lang, text)

    # Reverse lookup: text might be a translated value from another language
    for key, langs in _TRANSLATIONS.items():
        for lv in langs.values():
            if lv == text:
                return langs.get(_current_lang, text)

    return text


def refresh_widget(parent) -> None:
    """Recursively refresh all translatable widgets under a parent.

    Handles QLabel, QPushButton, QTabWidget tabs.
    Call this from each module's refresh_language() method.
    """
    from PySide6.QtWidgets import QLabel, QPushButton, QTabWidget, QWidget
    for child in parent.findChildren(QWidget):
        if isinstance(child, QPushButton):
            current = child.text()
            if current:
                translated = tr(current)
                if translated != current:
                    child.setText(translated)
        elif isinstance(child, QLabel):
            current = child.text()
            if current and len(current) > 1:
                translated = tr(current)
                if translated != current:
                    child.setText(translated)

    # QTabWidget tabs
    for tab_widget in parent.findChildren(QTabWidget):
        for i in range(tab_widget.count()):
            current = tab_widget.tabText(i)
            translated = tr(current)
            if translated != current:
                tab_widget.setTabText(i, translated)
