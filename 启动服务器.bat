@echo off
chcp 65001 >nul
cd /d "d:\一看就涨"

set HTTP_PROXY=
set HTTPS_PROXY=
set NO_PROXY=*

echo ==================================================
echo   A股数据代理服务器 V6
echo   页面地址: http://127.0.0.1:8080/terminal.html
echo   数据来源: 新浪实时 / TDX快照
echo   按 Ctrl+C 停止服务器
echo ==================================================
echo.

python server_v6.py
pause