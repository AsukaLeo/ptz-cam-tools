@echo off
chcp 65001 >nul
REM PTZ-Cam-Tools EXE Builder
REM Uses PyInstaller to compile into a single executable

echo ==========================================
echo PTZ-Cam-Tools EXE Builder
echo ==========================================
echo.

cd /d "%~dp0"

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

echo [INFO] Building PTZ-Cam-Tools.exe...
echo [INFO] This may take a few minutes...

python -m PyInstaller --onefile --windowed ^
    --name "PTZ-Cam-Tools" ^
    --add-data "assets;assets" ^
    --add-data "arrow_down.svg;." ^
    --add-data "thirdparty/ffmpeg/bin;thirdparty/ffmpeg/bin" ^
    --hidden-import "PySide6.QtCore" ^
    --hidden-import "PySide6.QtGui" ^
    --hidden-import "PySide6.QtWidgets" ^
    --hidden-import "cv2" ^
    --hidden-import "psutil" ^
    --hidden-import "serial" ^
    --hidden-import "onvif" ^
    --hidden-import "wsdiscovery" ^
    --hidden-import "zeep" ^
    --collect-all "onvif_zeep" ^
    main.py

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed!
    pause
    exit /b 1
)

echo.
echo ==========================================
echo Build successful!
echo Output: dist\PTZ-Cam-Tools.exe
echo ==========================================
echo.

pause
