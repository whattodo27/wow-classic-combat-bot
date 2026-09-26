"""Save the current configured WoW window without sending input."""
from __future__ import annotations

import base64
from pathlib import Path

from combat_bot.capture import WindowCapture
from combat_bot.config import load_config


def main() -> None:
    config = load_config(Path(__file__).parent / "combat_config.json")
    capture = WindowCapture(
        config.window_title,
        max_size=config.max_image_size,
        quality=config.image_quality,
    )
    rect = capture.find_window()
    print(f"window={rect}")
    image = capture.capture()
    if image is None:
        print("capture=None")
        return
    Path("current_window.jpg").write_bytes(base64.b64decode(image))
    print("saved=current_window.jpg")


if __name__ == "__main__":
    main()
