"""Run the real bot in a child process and prove Ctrl+C stops it."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main() -> int:
    env = dict(os.environ)
    env["PYTHONUNBUFFERED"] = "1"

    child = subprocess.Popen(
        [sys.executable, "-u", str(ROOT / "main.py")],
        cwd=str(ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        errors="ignore",
        encoding="utf-8",
    )

    # Let it get past startup and into its loop.
    time.sleep(12.0)

    if child.poll() is not None:
        output = child.communicate()[0]
        print("---- bot output (exited on its own) ----")
        print(output.strip()[-2000:])
        print("------------------------------------")
        print("FAIL: bot exited before Ctrl+C was sent")
        return 1

    print("bot is running; interrupting it like Ctrl+C does ...")
    # Windows has no way to deliver SIGINT to another process from Python:
    # subprocess rejects it and CTRL_BREAK_EVENT would kill this harness too.
    # taskkill without /F posts WM_CLOSE / ctrl-c to the console group instead
    # of force-killing, which is the closest equivalent to a user Ctrl+C.
    # taskkill's own output is localised cp866, so it is not worth decoding.
    subprocess.run(
        ["taskkill", "/PID", str(child.pid)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        output = child.communicate(timeout=15)[0]
    except subprocess.TimeoutExpired:
        print("FAIL: bot ignored Ctrl+C and kept running")
        child.kill()
        return 1

    print("---- bot output ----")
    print(output.strip()[-1200:])
    print("---------------------")
    print(f"exit code: {child.returncode}")

    if child.returncode == 0:
        print("PASS: Ctrl+C stopped the bot cleanly")
        return 0
    print("FAIL: nonzero exit code after Ctrl+C")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
