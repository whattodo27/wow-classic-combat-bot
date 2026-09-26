"""Win32 window discovery, focusing, and screenshot capture.

The bot never treats the primary monitor as a valid fallback. If the named
window cannot be found, it waits instead of sending input elsewhere.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass
from io import BytesIO
from typing import Optional

import mss
from PIL import Image


@dataclass(frozen=True)
class WindowRect:
    left: int
    top: int
    width: int
    height: int


def _is_hidden(window) -> bool:
    """Windows reports minimized windows at -32000 with a 160x28 titlebar rect."""
    try:
        if getattr(window, "isMinimized", False):
            return True
    except Exception:
        pass
    return (
        int(window.left) <= -30000
        or int(window.top) <= -30000
        or int(window.width) < 240
        or int(window.height) < 160
    )


def _to_rect(window) -> Optional[WindowRect]:
    if _is_hidden(window):
        return None
    return WindowRect(
        int(window.left),
        int(window.top),
        int(window.width),
        int(window.height),
    )


def find_window_by_title(title: str) -> Optional[WindowRect]:
    if not title.strip():
        return None
    try:
        import pygetwindow as gw
    except ImportError:
        return None

    def matches(predicate) -> list[WindowRect]:
        found = []
        for window in gw.getAllWindows():
            if not window.title or not predicate(window.title):
                continue
            rect = _to_rect(window)
            if rect is not None:
                found.append(rect)
        return found

    try:
        exact = [
            _to_rect(window)
            for window in gw.getWindowsWithTitle(title)
            if window.title
        ]
    except Exception:
        exact = []
    exact = [rect for rect in exact if rect is not None]
    if exact:
        return exact[0]

    # A minimized window must never win over a visible one with the same name.
    partial = matches(
        lambda window_title: window_title.casefold() == title.casefold()
        or title.casefold() in window_title.casefold()
    )
    if not partial:
        return None
    return partial[0]


class WindowCapture:
    def __init__(self, title: str, max_size: tuple[int, int] = (400, 300), quality: int = 60):
        self.title = title
        self.max_size = max_size
        self.quality = quality
        self.sct = mss.mss()

    def find_window(self) -> Optional[WindowRect]:
        return find_window_by_title(self.title)

    def focus(self) -> bool:
        """Focus the named window, restoring it if it was minimized."""
        window = self._find_window()
        if window is None:
            return False
        try:
            if getattr(window, "isMinimized", False):
                window.restore()
            try:
                window.activate()
            except Exception:
                # Some Windows builds reject pygetwindow activation. The title
                # lookup still provides a safe, deterministic target rectangle.
                pass
            return True
        except Exception:
            return False

    def _find_window(self):
        try:
            import pygetwindow as gw
        except ImportError:
            return None
        title = self.title
        candidates = []
        try:
            candidates = [
                window
                for window in gw.getWindowsWithTitle(title)
                if window.title
            ]
        except Exception:
            candidates = []
        if not candidates:
            candidates = [
                window
                for window in gw.getAllWindows()
                if window.title and title.casefold() in window.title.casefold()
            ]
        if not candidates:
            return None
        visible = [window for window in candidates if not _is_hidden(window)]
        if visible:
            return visible[0]
        # Nothing visible: the first match is minimized and can be restored.
        return candidates[0]

    def capture_image(self) -> Optional[Image.Image]:
        """Grab the named window at full resolution, without downscaling."""
        rect = self.find_window()
        if rect is None:
            return None
        shot = self.sct.grab(
            {
                "left": rect.left,
                "top": rect.top,
                "width": rect.width,
                "height": rect.height,
            }
        )
        return Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")

    def encode(self, image: Image.Image) -> str:
        """Encode a full-resolution frame for the vision model."""
        if image.size[0] > self.max_size[0] or image.size[1] > self.max_size[1]:
            image = image.copy()
            image.thumbnail(self.max_size, Image.Resampling.LANCZOS)
        buffer = BytesIO()
        image.save(buffer, format="JPEG", quality=self.quality)
        return base64.b64encode(buffer.getvalue()).decode("ascii")

    def capture(self) -> Optional[str]:
        image = self.capture_image()
        if image is None:
            return None
        return self.encode(image)

