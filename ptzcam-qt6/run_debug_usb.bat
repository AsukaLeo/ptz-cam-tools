@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo === USB Debug Mode ===
python main.py 2>&1 | findstr /i "[USB] Camera WARNING"
echo === Exit ===
pause
