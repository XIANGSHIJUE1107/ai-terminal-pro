@echo off
cd /d "d:\一看就涨"
set HTTP_PROXY=
set HTTPS_PROXY=
set NO_PROXY=*
echo ==================================================
echo   A股数据代理服务器 V6
echo   http://127.0.0.1:8080/terminal.html
echo ==================================================
python server_v6.py
pause