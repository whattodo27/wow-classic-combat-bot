"""Print exact candidate bar rectangles from a real frame (diagnostic only)."""
from __future__ import annotations

from pathlib import Path

from combat_bot.capture import WindowCapture
from combat_bot.config import load_config
from combat_bot.pixel_ui import UiRegion, _color_ratio


def main() -> None:
    root = Path(__file__).parent
    config = load_config(root / "combat_config.json")
    capture = WindowCapture(config.window_title)
    image = capture.capture_image()
    if image is None:
        print("window not found")
        return
    image.save(root / "live_frame.png")
    print(f"frame={image.size}  saved=live_frame.png")

    def report(label, box, color):
        region = UiRegion(*box)
        crop = region.crop(image)
        ratio = _color_ratio(crop, color)
        print(f"{label}: {box} ratio={ratio:.3f}")

    green = (0, 200, 0)
    report("player hp (y=20..28)", (20, 20, 140, 28), green)
    report("player hp (y=75..90)", (266, 75, 380, 90), green)
    report("target hp (y=76..90)", (265, 76, 385, 90), green)
    report("target name (y=60..74)", (265, 60, 385, 74), (255, 230, 0))
    report("target name (y=55..75)", (260, 55, 390, 75), (255, 230, 0))

    print("\nrow scan for green in y=0..140:")
    pixels = image.load()
    for y in range(0, 140, 2):
        xs = [
            x
            for x in range(0, image.size[0])
            if abs(pixels[x, y][0] - 0) <= 30
            and abs(pixels[x, y][1] - 200) <= 30
            and abs(pixels[x, y][2] - 0) <= 30
        ]
        if len(xs) > 40:
            print(f"  y={y:3d}  x={min(xs)}..{max(xs)}  count={len(xs)}")


if __name__ == "__main__":
    main()
