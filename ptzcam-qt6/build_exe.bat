@echo off
chcp 65001 >nul
REM PTZ-Cam-Tools EXE Builder
REM Uses PyInstaller to compile into a single executable

setlocal
set SCRIPT_DIR=%~dp0
set UPX_DIR=%USERPROFILE%\.workbuddy\tools\upx

echo ==========================================
echo PTZ-Cam-Tools EXE Builder
echo ==========================================
echo.

cd /d "%SCRIPT_DIR%"

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found!
    pause
    exit /b 1
)

REM Check PyInstaller
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing PyInstaller...
    pip install pyinstaller
)

REM Check UPX
set UPX_FLAG=
if exist "%UPX_DIR%\upx.exe" (
    echo [INFO] UPX found, will compress output
    set UPX_FLAG=--upx-dir "%UPX_DIR%"
) else (
    echo [INFO] UPX not found, skipping compression
    echo [INFO] Download from: https://github.com/upx/upx/releases
    echo [INFO] Extract to: %UPX_DIR%
)

REM Resolve ONVIF WSDL directory (onvif-zeep installs WSDL to site-packages/wsdl/)
python -c "import onvif; import os; print(os.path.join(os.path.dirname(os.path.dirname(onvif.__file__)), 'wsdl'))" > "%TEMP%\wsdl_path.txt"
set /p WSDL_DIR=<"%TEMP%\wsdl_path.txt"

REM Prepare minimal FFmpeg DLLs (only core 4 needed for decode)
set FFMPEG_SRC=%SCRIPT_DIR%thirdparty\ffmpeg\bin
set FFMPEG_TMP=%TEMP%\ffmpeg_minimal
if exist "%FFMPEG_TMP%" rmdir /s /q "%FFMPEG_TMP%"
mkdir "%FFMPEG_TMP%"
copy "%FFMPEG_SRC%\avcodec-61.dll" "%FFMPEG_TMP%\" >nul
copy "%FFMPEG_SRC%\avformat-61.dll" "%FFMPEG_TMP%\" >nul
copy "%FFMPEG_SRC%\avutil-59.dll" "%FFMPEG_TMP%\" >nul
copy "%FFMPEG_SRC%\swscale-8.dll" "%FFMPEG_TMP%\" >nul

echo [INFO] Building PTZ-Cam-Tools.exe...
echo [INFO] WSDL dir: %WSDL_DIR%
echo [INFO] FFmpeg: core 4 DLLs only (~87MB vs 119MB full)
echo [INFO] This may take a few minutes...

python -m PyInstaller --onefile --windowed ^
    --name "PTZ-Cam-Tools" ^
    --icon "assets\app_dark.ico" ^
    --runtime-hook "runtime_hook_utf8.py" ^
    %UPX_FLAG% ^
    --add-data "assets;assets" ^
    --add-data "arrow_down.svg;." ^
    --add-data "%FFMPEG_TMP%;thirdparty/ffmpeg/bin" ^
    --add-data "%WSDL_DIR%;wsdl" ^
    --exclude-module "matplotlib" ^
    --exclude-module "PIL" ^
    --exclude-module "scipy" ^
    --exclude-module "IPython" ^
    --exclude-module "notebook" ^
    --exclude-module "jupyter" ^
    --exclude-module "pandas" ^
    --exclude-module "numpy" ^
    --exclude-module "cv2" ^
    --exclude-module "PySide6.Qt3DAnimation" ^
    --exclude-module "PySide6.Qt3DCore" ^
    --exclude-module "PySide6.Qt3DExtras" ^
    --exclude-module "PySide6.Qt3DInput" ^
    --exclude-module "PySide6.Qt3DLogic" ^
    --exclude-module "PySide6.Qt3DRender" ^
    --exclude-module "PySide6.QtBluetooth" ^
    --exclude-module "PySide6.QtCharts" ^
    --exclude-module "PySide6.QtConcurrent" ^
    --exclude-module "PySide6.QtDataVisualization" ^
    --exclude-module "PySide6.QtDesigner" ^
    --exclude-module "PySide6.QtGraphs" ^
    --exclude-module "PySide6.QtGraphsWidgets" ^
    --exclude-module "PySide6.QtHelp" ^
    --exclude-module "PySide6.QtHttpServer" ^
    --exclude-module "PySide6.QtLocation" ^
    --exclude-module "PySide6.QtNfc" ^
    --exclude-module "PySide6.QtOpenGL" ^
    --exclude-module "PySide6.QtOpenGLWidgets" ^
    --exclude-module "PySide6.QtPdf" ^
    --exclude-module "PySide6.QtPdfWidgets" ^
    --exclude-module "PySide6.QtPositioning" ^
    --exclude-module "PySide6.QtPrintSupport" ^
    --exclude-module "PySide6.QtQml" ^
    --exclude-module "PySide6.QtQuick" ^
    --exclude-module "PySide6.QtQuick3D" ^
    --exclude-module "PySide6.QtQuick3DHelpers" ^
    --exclude-module "PySide6.QtQuickControls2" ^
    --exclude-module "PySide6.QtQuickTemplates2" ^
    --exclude-module "PySide6.QtQuickWidgets" ^
    --exclude-module "PySide6.QtRemoteObjects" ^
    --exclude-module "PySide6.QtScxml" ^
    --exclude-module "PySide6.QtSensors" ^
    --exclude-module "PySide6.QtSerialBus" ^
    --exclude-module "PySide6.QtSerialPort" ^
    --exclude-module "PySide6.QtSpatialAudio" ^
    --exclude-module "PySide6.QtSql" ^
    --exclude-module "PySide6.QtStateMachine" ^
    --exclude-module "PySide6.QtSvg" ^
    --exclude-module "PySide6.QtSvgWidgets" ^
    --exclude-module "PySide6.QtTest" ^
    --exclude-module "PySide6.QtTextToSpeech" ^
    --exclude-module "PySide6.QtVirtualKeyboard" ^
    --exclude-module "PySide6.QtWebChannel" ^
    --exclude-module "PySide6.QtWebEngine" ^
    --exclude-module "PySide6.QtWebEngineCore" ^
    --exclude-module "PySide6.QtWebEngineQuick" ^
    --exclude-module "PySide6.QtWebEngineWidgets" ^
    --exclude-module "PySide6.QtWebSockets" ^
    --exclude-module "PySide6.QtXml" ^
    main.py

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed!
    rmdir /s /q "%FFMPEG_TMP%" 2>nul
    pause
    exit /b 1
)

REM Cleanup temp FFmpeg
rmdir /s /q "%FFMPEG_TMP%" 2>nul

REM Get version for renaming
python -c "from app.utils.constants import VERSION_STRING; print(VERSION_STRING.replace(' ',''))" > "%TEMP%\ver.txt"
set /p VER=<"%TEMP%\ver.txt"
move "dist\PTZ-Cam-Tools.exe" "dist\PTZ-Cam-Tools-%VER%.exe" >nul 2>&1

echo.
echo ==========================================
echo Build successful!
for %%f in (dist\PTZ-Cam-Tools-*.exe) do echo Output: dist\%%~nxf
echo ==========================================
echo.

pause
