"""Reliable ways to stop the bot.

Signals are not enough on Windows: a process without its own console never
receives Ctrl+C, and when the game window holds focus the keystroke goes to
the game instead of the terminal. So the bot also watches for a stop file and
a panic key, both of which work no matter where the keyboard focus is.
"""

from __future__ import annotations

import ctypes
import signal
from pathlib import Path
from typing import Callable, Optional

# A held movement key would keep the character walking after the process ends.
MOVEMENT_KEYS = ("w", "a", "s", "d")

# Virtual-key code for F12, a key the game does not bind to anything useful.
PANIC_KEY_VK = 0x7B

STOP_FILE_NAME = "bot.stop"


def _keyboard_state() -> "ctypes.wintypes.DWORD":  # type: ignore[name-defined]
    return ctypes.windll.kernel32.GetAsyncKeyState


def panic_key_pressed() -> bool:
    """True while the panic key is held down."""
    try:
        return bool(_keyboard_state()(PANIC_KEY_VK) & 0x8000)
    except Exception:
        return False


def release_all_keys() -> None:
    """Release any key the bot might still be holding down."""
    try:
        import pyautogui
    except Exception:
        return
    for key in MOVEMENT_KEYS:
        try:
            pyautogui.keyUp(key)
        except Exception:
            pass


def _install_windows_console_handler() -> bool:
    """Ask Windows to deliver Ctrl+C and Ctrl+Break to this process.

    Returns False when the platform has no such API, so callers can fall back.
    """
    if not hasattr(ctypes, "windll"):
        return False

    handler_type = ctypes.WINFUNCTYPE(
        ctypes.c_int,  # return value
        ctypes.c_ulong,  # event type
        ctypes.c_void_p,  # event info
    )

    def on_console_event(event: int) -> int:
        # 0 = CTRL_C_EVENT, 1 = CTRL_BREAK_EVENT, 5 = CTRL_CLOSE_EVENT.
        if event in (0, 1, 5):
            release_all_keys()
            raise KeyboardInterrupt
        return 0

    callback = handler_type(on_console_event)
    ctypes.windll.kernel32.SetConsoleCtrlHandler(callback, 1)
    return True


def install_stop_handlers(
    on_stop: Optional[Callable[[], None]] = None,
) -> None:
    """Handle every stop route: Ctrl+C, Ctrl+Break, panic key, stop file."""

    def handler(signum, frame) -> None:  # noqa: ANN001
        release_all_keys()
        print(f"\nStopping (signal {signum}).", flush=True)
        if on_stop is not None:
            on_stop()
        raise KeyboardInterrupt

    signal.signal(signal.SIGINT, handler)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, handler)

    try:
        _install_windows_console_handler()
    except Exception:
        pass


def stop_file_path(root: Optional[Path] = None) -> Path:
    base = Path(root) if root is not None else Path(__file__).resolve().parents[1]
    return base / STOP_FILE_NAME


def stop_requested(root: Optional[Path] = None) -> bool:
    """True when the user created the stop file."""
    return stop_file_path(root).exists()


def clear_stop_file(root: Optional[Path] = None) -> None:
    try:
        stop_file_path(root).unlink()
    except FileNotFoundError:
        pass
    except OSError:
        pass


def request_stop(root: Optional[Path] = None) -> Path:
    """Create the stop file so a running bot exits at its next cycle."""
    path = stop_file_path(root)
    path.write_text("stop\n", encoding="utf-8")
    return path
