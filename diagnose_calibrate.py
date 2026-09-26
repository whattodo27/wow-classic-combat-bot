"""Locate player and target bars precisely (diagnostic only)."""
from __future__ import annotations

from pathlib import Path

from combat_bot.capture import WindowCapture
from combat_bot.config import load_config


def bounds(image, color, x0, y0, x1, y1, tolerance=30):
    pixels = image.load()
    found = []
    for y in range(y0, y1):
        xs = [
            x
            for x in range(x0, x1)
            if abs(pixels[x, y][0] - color[0]) <= tolerance
            and abs(pixels[x, y][1] - color[1]) <= tolerance
            and abs(pixels[x, y][2] - color[2]) <= tolerance
        ]
        if len(xs) > 20:
            found.append((y, min(xs), max(xs), len(xs)))
    return found


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

    print("\n== GREEN in top-left (player hp) ==")
    for row in bounds(image, (0, 200, 0), 0, 30, 400, 160):
        print(f"  y={row[0]:3d} x={row[1]:3d}..{row[2]:3d} count={row[3]}")

    print("\n== BLUE in top-left (mana) ==")
    for row in bounds(image, (0, 0, 255), 0, 30, 400, 160):
        print(f"  y={row[0]:3d} x={row[1]:3d}..{row[2]:3d} count={row[3]}")

    print("\n== GREEN top-center (target hp) ==")
    for row in bounds(image, (0, 200, 0), 400, 30, 800, 160):
        print(f"  y={row[0]:3d} x={row[1]:3d}..{row[2]:3d} count={row[3]}")

    print("\n== exact colors sampled ==")
    pixels = image.load()
    for name, point in (
        ("player hp fill", (150, 80)),
        ("player hp fill2", (190, 80)),
        ("player mana fill", (150, 95)),
        ("player mana fill2", (190, 95)),
    ):
        print(f"  {name} {point} -> {pixels[point[0], point[1]]}")


if __name__ == "__main__":
    main()
