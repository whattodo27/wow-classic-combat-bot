"""Bring the game window forward, then capture it (diagnostic only)."""
from __future__ import annotations

import time
from pathlib import Path

from combat_bot.capture import WindowCapture, find_window_by_title
from combat_bot.config import load_config


def main() -> None:
    root = Path(__file__).parent
    config = load_config(root / "combat_config.json")
    capture = WindowCapture(config.window_title)

    print(f"rect before: {find_window_by_title(config.window_title)}")
    print(f"focus ok: {capture.focus()}")
    time.sleep(1.5)
    print(f"rect after:  {find_window_by_title(config.window_title)}")

    image = capture.capture_image()
    if image is None:
        print("capture failed")
        return
    image.save(root / "focused_frame.png")
    print(f"saved focused_frame.png  size={image.size}")


if __name__ == "__main__":
    main()
