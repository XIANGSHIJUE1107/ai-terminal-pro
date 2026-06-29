@echo off
chcp 65001 >nul 2>&1
title A股数据代理服务器 - 守护模式
cd /d "%~dp0"

echo ============================================================
echo   A股数据代理服务器 V6
echo   http://127.0.0.1:8080/terminal.html
echo ============================================================

set PORT=8080
set HTTP_PROXY=
set HTTPS_PROXY=
set NO_PROXY=*

for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8080 ^| findstr LISTENING') do (
    echo Stopping existing process on port 8080: PID=%%a
    taskkill /PID %%a /F >nul 2>&1
)
python proxy_server.py
echo Server stopped. Press any key to close.
pause >nul
