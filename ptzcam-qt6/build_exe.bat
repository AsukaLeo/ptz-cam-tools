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

echo [INFO] Building PTZ-Cam-Tools.exe...
echo [INFO] WSDL dir: %WSDL_DIR%
echo [INFO] This may take a few minutes...

python -m PyInstaller --onefile --windowed ^
    --name "PTZ-Cam-Tools" ^
    --icon "assets\app_dark.ico" ^
    %UPX_FLAG% ^
    --add-data "assets;assets" ^
    --add-data "arrow_down.svg;." ^
    --add-data "thirdparty/ffmpeg/bin;thirdparty/ffmpeg/bin" ^
    --add-data "%WSDL_DIR%;wsdl" ^
    --exclude-module "matplotlib" ^
    --exclude-module "PIL" ^
    --exclude-module "scipy" ^
    --exclude-module "IPython" ^
    --exclude-module "notebook" ^
    --exclude-module "jupyter" ^
    --exclude-module "pandas" ^
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
