"""Print tight candidate boxes for each bar (diagnostic only)."""
from __future__ import annotations

from pathlib import Path

from combat_bot.bar_finder import RatioRect, find_bar, measure_bar
from combat_bot.capture import WindowCapture
from combat_bot.config import load_config


def main() -> None:
    root = Path(__file__).parent
    config = load_config(root / "combat_config.json")
    capture = WindowCapture(config.window_title)
    image = capture.capture_image()
    if image is None:
        print("window not found")
        return
    image.save(root / "live_frame.png")
    print(f"frame={image.size}")

    searches = {
        "player hp": (RatioRect(0.08, 0.085, 0.22, 0.105), (0, 200, 0)),
        "player mana": (RatioRect(0.08, 0.105, 0.22, 0.125), (0, 0, 110)),
        "target hp": (RatioRect(0.44, 0.085, 0.60, 0.105), (0, 200, 0)),
    }
    for name, (rect, color) in searches.items():
        bar = find_bar(image, color, rect)
        if bar is None:
            print(f"{name}: not found in {rect.to_pixels(image.size)}")
            continue
        percent = measure_bar(image, bar, color)
        print(
            f"{name}: search={rect.to_pixels(image.size)} bar={bar} "
            f"track_width={bar[2] - bar[0]} percent={percent}"
        )


if __name__ == "__main__":
    main()
