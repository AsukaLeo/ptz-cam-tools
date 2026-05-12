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
if exist "%UPX_DIR%\upx.exe" (
    echo [INFO] UPX found at %UPX_DIR%
) else (
    echo [INFO] UPX not found, get it from: https://github.com/upx/upx/releases
    echo [INFO] Extract win64 zip to: %UPX_DIR%
)

echo [INFO] Building PTZ-Cam-Tools.exe via spec (slim binary filter + UPX)...
echo [INFO] See PTZ-Cam-Tools.spec for filter rules
echo [INFO] This may take a few minutes...

REM Regenerate spec with fresh WSDL path (spec hardcodes datas, WSDL path may drift)
python -c "
import onvif, os
wsdl = os.path.join(os.path.dirname(os.path.dirname(onvif.__file__)), 'wsdl')
spec = open('PTZ-Cam-Tools.spec','r').read()
# The spec already has the WSDL in datas; re-run PyInstaller will find it
"  2>nul

REM Build from spec (spec handles all exclusions + binary filtering)
set "PATH=%UPX_DIR%;%PATH%"
python -m PyInstaller PTZ-Cam-Tools.spec

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed!
    pause
    exit /b 1
)

echo.
echo ==========================================
echo Build successful!
dir dist\PTZ-Cam-Tools-*.exe /b
echo ==========================================
echo.

pause
