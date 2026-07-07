# -*- coding: utf-8 -*-
"""Start proxy server with auto-restart and logging."""
import subprocess
import sys
import os
import time
import threading
from pathlib import Path

os.chdir(r"d:\一看就涨")
LOG_FILE = Path("server.log")


def log(line: str):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    msg = f"[{ts}] {line}"
    print(msg, flush=True)
    try:
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except Exception:
        pass


def stream_reader(proc: subprocess.Popen):
    try:
        for line in proc.stdout:
            log(f"[OUT] {line.rstrip()}")
    except Exception as exc:
        log(f"[READER] error: {exc}")


def start_once() -> subprocess.Popen:
    proc = subprocess.Popen(
        [sys.executable, "-u", "proxy_server.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        encoding="utf-8",
        errors="replace",
    )
    # start reader thread
    threading.Thread(target=stream_reader, args=(proc,), daemon=True).start()
    return proc


def main():
    log("=" * 50)
    log("Server manager starting")
    while True:
        proc = start_once()
        # wait for startup
        time.sleep(3)
        if proc.poll() is None:
            log("SERVER_STARTED_OK")
        else:
            log(f"SERVER_FAILED immediately, code={proc.returncode}")
            time.sleep(5)
            continue

        # wait until it exits
        try:
            proc.wait()
        except KeyboardInterrupt:
            log("Stopping on Ctrl+C")
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
            break

        log(f"SERVER_EXITED code={proc.returncode}, restarting in 5s")
        time.sleep(5)


if __name__ == "__main__":
    main()
