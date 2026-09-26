"""Check which slots look out of range and why (diagnostic only)."""
from __future__ import annotations

import time
from pathlib import Path

from combat_bot.action_bar import red_frame_rows, scan_action_bar
from combat_bot.capture import WindowCapture
from combat_bot.config import load_config


def main() -> None:
    root = Path(__file__).parent
    config = load_config(root / "combat_config.json")
    capture = WindowCapture(config.window_title)
    capture.focus()
    time.sleep(0.5)

    for index in range(4):
        image = capture.capture_image()
        if image is None:
            print("window not found")
            return
        width, height = image.size
        top = int(height * 0.92)
        strip = image.crop((0, top, width, height))
        rows = red_frame_rows(strip)
        result = scan_action_bar(image)
        print(
            f"[{index}] frame_rows={rows} "
            f"out_of_range={result.out_of_range} "
            f"signal={result.red_ratio:.4f} strip={strip.size}"
        )
        time.sleep(0.8)

    # Show the bottom strip enlarged for visual inspection.
    image.crop((0, top, width, height)).save(root / "crop_bar_check.png")
    print("saved crop_bar_check.png")


if __name__ == "__main__":
    main()
