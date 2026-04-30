@echo off
chcp 65001 >nul
REM PTZ-Cam-Tools Debug Launcher
REM Starts application with verbose logging

echo ==========================================
echo PTZ-Cam-Tools DEBUG MODE
echo ==========================================
echo.
echo Debug logs will be saved to: logs\ptzcam_*.log
echo.

REM Change to script directory
cd /d "%~dp0"

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found! Please install Python 3.13+
    pause
    exit /b 1
)

REM Run application in debug mode
echo Starting PTZ-Cam-Tools in DEBUG mode...
echo.
python main.py --debug

if errorlevel 1 (
    echo.
    echo [ERROR] Application exited with error code %errorlevel%
    pause
)
