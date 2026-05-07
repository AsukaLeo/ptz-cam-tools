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
# === Trim Qt DLLs to only needed modules ===
KEEP_QT = {"Core", "Gui", "Widgets", "Multimedia", "MultimediaWidgets",
           "Network", "OpenGL", "OpenGLWidgets"}
all_dlls = [(b[0], os.path.getsize(b[1])/1024/1024) for b in a.binaries if b[0].endswith(".dll") or b[0].endswith(".pyd")]
all_dlls.sort(key=lambda x: -x[1])
for name, size in all_dlls: print(f"  {name}: {size:.1f}MB")
import os
a.binaries = [
    b for b in a.binaries
    if not b[0].startswith("Qt6") or any(b[0].startswith(f"Qt6{m}") for m in KEEP_QT)
]
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
