"""Compare ways of stopping a console Python process on Windows."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CHILD = r"""
import signal, sys, time
def handler(signum, frame):
    print("child got signal", signum, flush=True)
    raise KeyboardInterrupt
signal.signal(signal.SIGINT, handler)
try:
    signal.signal(signal.SIGTERM, handler)
except Exception:
    pass
print("child ready", flush=True)
try:
    while True:
        time.sleep(0.2)
except KeyboardInterrupt:
    print("child exiting cleanly", flush=True)
    sys.exit(0)
"""


def spawn() -> subprocess.Popen:
    return subprocess.Popen(
        [sys.executable, "-u", "-c", CHILD],
        cwd=str(ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        errors="ignore",
        encoding="utf-8",
    )


def check(label: str, stop) -> bool:
    child = spawn()
    time.sleep(2.0)

    if child.poll() is not None:
        print(f"{label:<24} FAIL (child died on its own)")
        return False

    stop(child)

    try:
        output = child.communicate(timeout=8)[0]
    except subprocess.TimeoutExpired:
        child.kill()
        print(f"{label:<24} FAIL (still running after 8s)")
        return False

    clean = "cleanly" in output
    print(f"{label:<24} {'PASS' if clean else 'partial'}  exit={child.returncode}")
    return clean


def main() -> int:
    results = {}

    results["taskkill"] = check(
        "taskkill (no /F)",
        lambda c: subprocess.run(
            ["taskkill", "/PID", str(c.pid)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ),
    )

    results["taskkill /F"] = check(
        "taskkill /F (force)",
        lambda c: subprocess.run(
            ["taskkill", "/F", "/PID", str(c.pid)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ),
    )

    def generate_console_event(child):
        # Ctrl+C is exactly this: CTRL_C_EVENT to the process group.
        os.kill(child.pid, signal.CTRL_C_EVENT)

    results["CTRL_C_EVENT"] = check("CTRL_C_EVENT", generate_console_event)

    def generate_break(child):
        # Not probed here: CTRL_BREAK_EVENT goes to the whole console group
        # and would kill this harness as well.
        os.kill(child.pid, signal.CTRL_BREAK_EVENT)

    results["CTRL_BREAK_EVENT"] = check("CTRL_BREAK_EVENT (skipped)", lambda c: None)

    print()
    for name, ok in results.items():
        if name == "CTRL_BREAK_EVENT":
            continue
        print(f"{name:<24} {'works' if ok else 'does not deliver SIGINT'}")

    return 0 if results["CTRL_C_EVENT"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
