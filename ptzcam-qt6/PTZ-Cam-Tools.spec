# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('assets', 'assets'), ('arrow_down.svg', '.'), ('thirdparty/ffmpeg/bin', 'thirdparty/ffmpeg/bin'), ('C:/Users/asuka/AppData/Local/Python/pythoncore-3.14-64/Lib/site-packages/wsdl', 'wsdl')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
# === Trim binaries: remove OpenCV & NumPy, dedup FFmpeg, slim Qt ===
KEEP_QT = {"Core", "Gui", "Widgets", "Multimedia", "MultimediaWidgets",
           "Network", "OpenGL", "OpenGLWidgets", "Svg"}
QT_PREFIX = "PySide6\\Qt6"
REMOVE_PREFIXES = ["cv2\\", "cv2.", "numpy\\", "numpy."]
REMOVE_FILES = {
    "opengl32sw.dll", "PIL\\_avif", "libscipy_openblas",
    "opencv_videoio_ffmpeg", "avfilter-10.dll", "avdevice-61.dll",
    "swresample-5.dll",
}
seen = set()
filtered = []
for b in a.binaries:
    name = b[0]
    # Remove OpenCV/NumPy completely
    if any(name.startswith(p) or p in name for p in REMOVE_PREFIXES):
        continue
    # Remove known-bloat files
    if any(f in name for f in REMOVE_FILES):
        continue
    # Trim Qt
    if name.startswith(QT_PREFIX):
        mod = name[len(QT_PREFIX):].split(".")[0]
        if mod not in KEEP_QT:
            continue
    # Deduplicate FFmpeg DLLs
    if name.endswith('.dll') and any(
        name.endswith(f'{x}.dll') for x in
        ['avcodec-61', 'avformat-61', 'avutil-59', 'swscale-8']
    ):
        if 'thirdparty' not in name:
            continue
    key = name.lower()
    if key in seen:
        continue
    seen.add(key)
    filtered.append(b)
a.binaries = filtered
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
    icon=['assets\\app_square.ico'],
)
