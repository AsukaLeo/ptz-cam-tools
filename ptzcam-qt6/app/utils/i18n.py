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

    Handles QLabel, QPushButton, QTabWidget tabs, and QComboBox items.
    Call this from each module's refresh_language() method.
    """
    from PySide6.QtWidgets import QLabel, QPushButton, QTabWidget, QComboBox
    for child in parent.findChildren((QLabel, QPushButton)):
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
