@echo off
chcp 65001 >nul
REM PTZ-Cam-Tools Debug Console Mode
REM Debug output to console only (no log files)

echo ==========================================
echo PTZ-Cam-Tools DEBUG CONSOLE MODE
echo ==========================================
echo.
echo Debug output will only show in this console
echo No log files will be created
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

REM Run application in debug mode without file logging
echo Starting PTZ-Cam-Tools...
echo.
python main.py --debug --no-log-file

if errorlevel 1 (
    echo.
    echo [ERROR] Application exited with error code %errorlevel%
    pause
)
