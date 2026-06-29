@echo off
cd /d "d:\一看就涨"
set HTTP_PROXY=
set HTTPS_PROXY=
set NO_PROXY=*
echo Starting server on http://127.0.0.1:8080/terminal.html
python simple_server.py
pause