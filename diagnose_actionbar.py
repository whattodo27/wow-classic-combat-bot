"""Locate action-bar key numbers and out-of-range red tint (diagnostic only)."""
from __future__ import annotations

from pathlib import Path

from PIL import Image

from combat_bot.capture import WindowCapture
from combat_bot.config import load_config


def find_red(image, x0, y0, x1, y1, tolerance=60):
    pixels = image.load()
    hits = []
    for y in range(y0, y1):
        xs = [
            x
            for x in range(x0, x1)
            if pixels[x, y][0] > 110
            and pixels[x, y][0] - pixels[x, y][1] > tolerance
            and pixels[x, y][0] - pixels[x, y][2] > tolerance
        ]
        if xs:
            hits.append((y, min(xs), max(xs), len(xs)))
    return hits


def main() -> None:
    root = Path(__file__).parent
    config = load_config(root / "combat_config.json")
    capture = WindowCapture(config.window_title)
    capture.focus()
    image = capture.capture_image()
    if image is None:
        print("window not found")
        return
    image.save(root / "live_frame.png")
    width, height = image.size
    print(f"frame={image.size}")

    # The action bar sits in the bottom strip of the window.
    bar_top = int(height * 0.92)
    print(f"action bar strip: y={bar_top}..{height}")

    image.crop((0, bar_top, width, height)).save(root / "crop_bar_now.png")
    print("saved crop_bar_now.png")

    print("\n== red pixels in bar strip ==")
    for row in find_red(image, 0, bar_top, width, height)[:40]:
        print(f"  y={row[0]:3d} x={row[1]:4d}..{row[2]:4d} n={row[3]}")

    print("\n== red pixels full lower third ==")
    for row in find_red(image, 0, int(height * 0.6), width, height)[:40]:
        print(f"  y={row[0]:3d} x={row[1]:4d}..{row[2]:4d} n={row[3]}")


if __name__ == "__main__":
    main()
