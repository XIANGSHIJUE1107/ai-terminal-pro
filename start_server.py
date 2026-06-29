# -*- coding: utf-8 -*-
"""Start server and write status"""
import subprocess
import sys
import os
os.chdir(r"d:\一看就涨")
proc = subprocess.Popen([sys.executable, "-u", "proxy_server.py"], 
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                        text=True, bufsize=1)
# Wait for startup
import time
time.sleep(2)
# Check if process is still running
if proc.poll() is None:
    print("SERVER_STARTED_OK", flush=True)
    # Read any output
    import select
    while True:
        if select.select([proc.stdout], [], [], 0.5)[0]:
            line = proc.stdout.readline()
            if line:
                print(f"[OUT] {line.rstrip()}", flush=True)
        if proc.poll() is not None:
            break
else:
    print("SERVER_FAILED", flush=True)
    print(proc.stdout.read(), flush=True)