# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('assets', 'assets'), ('arrow_down.svg', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['runtime_hook_utf8.py'],
    excludes=['matplotlib', 'PIL', 'scipy', 'numpy', 'cv2', 'PySide6.Qt3DAnimation', 'PySide6.Qt3DCore', 'PySide6.Qt3DExtras', 'PySide6.Qt3DInput', 'PySide6.Qt3DLogic', 'PySide6.Qt3DRender', 'PySide6.QtBluetooth', 'PySide6.QtCharts', 'PySide6.QtConcurrent', 'PySide6.QtDataVisualization', 'PySide6.QtDesigner', 'PySide6.QtGraphs', 'PySide6.QtGraphsWidgets', 'PySide6.QtHelp', 'PySide6.QtHttpServer', 'PySide6.QtLocation', 'PySide6.QtNfc', 'PySide6.QtOpenGL', 'PySide6.QtOpenGLWidgets', 'PySide6.QtPdf', 'PySide6.QtPdfWidgets', 'PySide6.QtPositioning', 'PySide6.QtPrintSupport', 'PySide6.QtQml', 'PySide6.QtQuick', 'PySide6.QtQuick3D', 'PySide6.QtQuick3DHelpers', 'PySide6.QtQuickControls2', 'PySide6.QtQuickTemplates2', 'PySide6.QtQuickWidgets', 'PySide6.QtRemoteObjects', 'PySide6.QtScxml', 'PySide6.QtSensors', 'PySide6.QtSerialBus', 'PySide6.QtSerialPort', 'PySide6.QtSpatialAudio', 'PySide6.QtSql', 'PySide6.QtStateMachine', 'PySide6.QtSvg', 'PySide6.QtSvgWidgets', 'PySide6.QtTest', 'PySide6.QtTextToSpeech', 'PySide6.QtVirtualKeyboard', 'PySide6.QtWebChannel', 'PySide6.QtWebEngine', 'PySide6.QtWebEngineCore', 'PySide6.QtWebEngineQuick', 'PySide6.QtWebEngineWidgets', 'PySide6.QtWebSockets', 'PySide6.QtXml'],
    noarchive=False,
    optimize=0,
)

# --- Slim binary filter: remove PySide6 Qt DLLs we never use ---
# PyInstaller's PySide6 hook bundles ALL Qt6*.dll files regardless of --exclude-module.
# This filter removes the unnecessary ones at the binary level.

QT_PREFIX = "PySide6\\"
KEEP_QT_DLLS = {
    # Core (always needed)
    "Qt6Core", "Qt6Gui", "Qt6Widgets",
    # Multimedia stack (USB + RTSP)
    "Qt6Multimedia", "Qt6MultimediaWidgets", "Qt6Network",
    # SVG support (arrow_down.svg + icon engine)
    "Qt6Svg",
}
KEEP_PLUGINS = {
    # Must-have platform backends
    "platforms": {"*"},
    # Image formats we actually use
    "imageformats": {"qjpeg", "qpng", "qgif", "qico", "qsvg", "qwebp"},
    # Multimedia backends
    "multimedia": {"*"},
    # SVG icon engine (for arrow_down.svg and other SVGs)
    "iconengines": {"qsvgicon"},
    # Window styling
    "styles": {"qmodernwindowsstyle"},
    # TLS for HTTPS/RTSP
    "tls": {"*"},
    # Network information
    "networkinformation": {"*"},
    # Generic plugins (touch etc.)
    "generic": {"*"},
}

filtered = []
for dest, src, typ in a.binaries:
    if not dest.startswith(QT_PREFIX):
        # Non-PySide6 binary — keep
        filtered.append((dest, src, typ))
        continue

    rel = dest[len(QT_PREFIX):]  # e.g., "Qt6Core.dll" or "plugins\platforms\qwindows.dll"

    # Case 1: Top-level Qt6*.dll
    if rel.startswith("Qt6") and rel.endswith(".dll"):
        dll_name = rel.rsplit(".", 1)[0]  # "Qt6Core"
        if dll_name in KEEP_QT_DLLS:
            filtered.append((dest, src, typ))
        continue

    # Case 2: Plugin DLL (plugins\<category>\<file>)
    if rel.startswith("plugins\\"):
        parts = rel.split("\\")
        if len(parts) >= 3:
            category = parts[1]      # e.g., "platforms"
            fname = parts[-1]        # e.g., "qwindows.dll"
            base = fname.rsplit(".", 1)[0]  # e.g., "qwindows"
            if category in KEEP_PLUGINS:
                allowed = KEEP_PLUGINS[category]
                if "*" in allowed or base in allowed:
                    filtered.append((dest, src, typ))
        continue

    # Case 3: Other PySide6/ files (e.g., shiboken DLLs are separate) — keep
    filtered.append((dest, src, typ))

a.binaries = filtered
# --- End slim binary filter ---

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='PTZ-Cam-Tools',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets\\app_dark.ico'],
)
