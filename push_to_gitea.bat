@echo off
chcp 65001 >nul
title 推送 PTZ-Cam-Tools 到 Gitea
echo ============================================
echo  推送 PTZ-Cam-Tools 到 Gitea 私有仓库
echo ============================================
echo.
echo 目标: https://gitea.feiniaoyun.cn/FNY/PTZ-Camara
echo.
echo 注意: Gitea 服务器在国内，需要通过代理连接
echo.
setlocal enabledelayedexpansion

echo [1/2] 先测试 Gitea 连通性...
curl -s -o nul -w "HTTP状态码: %%{http_code}" --connect-timeout 10 "https://gitea.feiniaoyun.cn/"
if errorlevel 1 echo. & echo ⚠  Gitea 暂时无法连接，可能是代理节点问题
echo.

echo [2/2] 开始推送...
git push gitea master
if !errorlevel! equ 0 (
    echo.
    echo ✓ 推送成功！
    goto :done
) else (
    echo.
    echo × 推送失败
    echo.
    echo 可能的原因:
    echo   - Gitea 服务器网络暂时不可用
    echo   - SSL 连接被代理拦截
    echo   - 认证失败
    echo.
    echo 你可以:
    echo   1. 稍后重试: git push gitea master
    echo   2. 使用 bundle 方式: push_to_gitea_fallback.bat
    echo.
    goto :end
)

:done
echo.
echo ✓ 完成! 代码已推送到 Gitea

:end
echo.
pause
