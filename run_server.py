"""Script to start server and verify"""
import subprocess
import sys
import os
import time

os.chdir(r"d:\一看就涨")
os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''
os.environ['NO_PROXY'] = '*'

# Start server_v6.py
proc = subprocess.Popen(
    [sys.executable, '-u', 'server_v6.py'],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    cwd=r"d:\一看就涨",
    text=True,
    bufsize=1
)

# Wait for startup
time.sleep(3)

# Check if running
if proc.poll() is None:
    with open(r'd:\一看就涨\server_status.txt', 'w') as f:
        f.write('SERVER_RUNNING\n')
        f.write(f'PID: {proc.pid}\n')
    # Read any output
    import select
    lines = []
    for _ in range(10):
        ready, _, _ = select.select([proc.stdout], [], [], 0.1)
        if ready:
            line = proc.stdout.readline()
            if line:
                lines.append(line)
    with open(r'd:\一看就涨\server_status.txt', 'a') as f:
        f.write(''.join(lines))
else:
    with open(r'd:\一看就涨\server_status.txt', 'w') as f:
        f.write(f'SERVER_EXITED code={proc.returncode}\n')
        out = proc.stdout.read()
        f.write(out)