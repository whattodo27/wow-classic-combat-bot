"""Action execution with an explicit dry-run boundary."""

from __future__ import annotations

import time
from typing import Callable, Optional

from .models import Action


class ActionExecutor:
    """Send keyboard input to the game.

    Focusing the window on every keystroke forces a repaint, and a screenshot
    taken mid-repaint shows a half-drawn UI, which corrupts pixel readings. The
    window is therefore focused once and then left alone unless the caller
    explicitly requests a refocus.
    """

    def __init__(
        self,
        live_input: bool = False,
        live_targeting: bool = False,
        target_key: str = "tab",
        pause: float = 0.1,
        keyboard=None,
        focus_callback: Optional[Callable[[], None]] = None,
    ):
        self.live_input = live_input
        self.live_targeting = live_targeting
        self.target_key = target_key.casefold()
        self.focus_callback = focus_callback
        self._focused = False

        if keyboard is not None:
            self._keyboard = keyboard
        elif live_input or live_targeting:
            import pyautogui

            self._keyboard = pyautogui
        else:
            self._keyboard = None

        if self._keyboard is not None:
            self._keyboard.PAUSE = pause
            self._keyboard.FAILSAFE = True

    def focus_now(self) -> None:
        """Force a window focus, e.g. after the user clicked elsewhere."""
        if self.focus_callback is not None:
            self.focus_callback()
        self._focused = True

    def _ensure_focus(self) -> None:
        if self._focused:
            return
        self.focus_now()

    def _should_send_live(self, action: Action) -> bool:
        if self.live_input:
            return True
        if not self.live_targeting:
            return False
        if action.kind == "hold_keys":
            return True
        return action.key is not None and action.key.casefold() == self.target_key

    def execute(self, action: Action) -> str:
        if action.kind == "wait":
            return f"WAIT [{action.reason}]"

        if action.kind == "hold_keys":
            return self._execute_hold(action)

        if not action.key:
            return "BLOCKED empty_key"

        if not self._should_send_live(action):
            return f"DRY-RUN press {action.key!r} [{action.reason}]"

        if self._keyboard is None:
            return "BLOCKED keyboard_unavailable"

        self._ensure_focus()
        self._keyboard.press(action.key, presses=1, interval=0.05)
        if action.hold_seconds:
            time.sleep(action.hold_seconds)

        prefix = "LIVE" if self.live_input else "LIVE TARGET"
        return f"{prefix} press {action.key!r} [{action.reason}]"

    def _execute_hold(self, action: Action) -> str:
        keys = tuple(action.keys)
        if not keys:
            return "BLOCKED empty_keys"

        if not self._should_send_live(action):
            return f"DRY-RUN hold {keys} [{action.reason}]"

        if self._keyboard is None:
            return "BLOCKED keyboard_unavailable"

        self._ensure_focus()

        hold = max(0.0, float(action.hold_seconds or 0.0))
        pressed: list[str] = []
        try:
            for key in keys:
                self._keyboard.keyDown(key)
                pressed.append(key)
            if hold:
                time.sleep(hold)
        finally:
            # Always release, even if the game rejects a key mid-sweep.
            for key in reversed(pressed):
                try:
                    self._keyboard.keyUp(key)
                except Exception:
                    pass

        prefix = "LIVE" if self.live_input else "LIVE SWEEP"
        return f"{prefix} hold {keys} for {hold:.2f}s [{action.reason}]"
