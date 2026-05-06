@echo off
chcp 65001 >nul
echo ============================================
echo  通过 bundle 方式推送 PTZ-Cam-Tools 到 Gitea
echo ============================================
echo.
echo 步骤1: 先克隆远程仓库（获取 README.md）
echo ============================================
set /p confirm="确认要推送吗？(y/n): "
if not "%confirm%"=="y" exit /b

echo.
echo 创建临时目录...
set TMP_DIR=%TEMP%\ptzcam_gitea_push
if exist %TMP_DIR% rmdir /s /q %TMP_DIR%

echo.
echo 克隆远程仓库...
git clone https://Buddy:David2008@gitea.feiniaoyun.cn/FNY/PTZ-Camara.git %TMP_DIR%
if errorlevel 1 (
    echo.
    echo [错误] 克隆失败，请检查网络连接和代理设置
    goto :end
)

echo.
echo ============================================
echo 步骤2: 从 bundle 恢复完整历史
echo ============================================
cd %TMP_DIR%
git fetch C:\Users\asuka\WorkBuddy\20260429153616\PTZ-Cam-Tools.bundle master
git checkout -b temp-main
git merge --allow-unrelated-histories FETCH_HEAD

echo.
echo ============================================
echo 步骤3: 推送到 Gitea
echo ============================================
git push origin temp-main:main --force

echo.
echo ============================================
cd /d C:\Users\asuka\WorkBuddy\20260429153616
rmdir /s /q %TMP_DIR%
echo 完成！

:end
pause
