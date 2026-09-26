"""Print exact bar geometry for a focused WoW window (diagnostic only)."""
from __future__ import annotations

import time
from pathlib import Path

from combat_bot.capture import WindowCapture
from combat_bot.config import load_config


def scan(image, color, x0, y0, x1, y1, tolerance=40, min_count=15):
    pixels = image.load()
    rows = []
    for y in range(y0, y1):
        xs = [
            x
            for x in range(x0, x1)
            if abs(pixels[x, y][0] - color[0]) <= tolerance
            and abs(pixels[x, y][1] - color[1]) <= tolerance
            and abs(pixels[x, y][2] - color[2]) <= tolerance
        ]
        if len(xs) >= min_count:
            rows.append((y, min(xs), max(xs), len(xs)))
    return rows


def main() -> None:
    root = Path(__file__).parent
    config = load_config(root / "combat_config.json")
    capture = WindowCapture(config.window_title)
    capture.focus()
    time.sleep(1.0)
    image = capture.capture_image()
    if image is None:
        print("window not found")
        return
    image.save(root / "live_frame.png")
    width, height = image.size
    print(f"frame={image.size}")

    print("\n== green rows, top strip (player hp + target hp) ==")
    for row in scan(image, (0, 205, 0), 0, 30, width, 130):
        print(f"  y={row[0]:3d} x={row[1]:3d}..{row[2]:3d} n={row[3]}")

    print("\n== blue rows, top strip (mana) ==")
    for row in scan(image, (0, 0, 110), 0, 30, width, 130):
        print(f"  y={row[0]:3d} x={row[1]:3d}..{row[2]:3d} n={row[3]}")

    pixels = image.load()
    print("\n== samples ==")
    for name, point in (
        ("hp@120,80", (120, 80)),
        ("hp@160,80", (160, 80)),
        ("hp@205,80", (205, 80)),
        ("mana@120,94", (120, 94)),
        ("mana@205,94", (205, 94)),
        ("track_end@210,80", (210, 80)),
    ):
        print(f"  {name} -> {pixels[point[0], point[1]]}")


if __name__ == "__main__":
    main()
