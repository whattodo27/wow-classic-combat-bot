"""Measure the target frame from a frame that has a selected target."""
from __future__ import annotations

from pathlib import Path

from combat_bot.capture import WindowCapture
from combat_bot.config import load_config


def scan(image, color, x0, y0, x1, y1, tolerance=45, min_count=10):
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
    image = __import__("PIL.Image", fromlist=["Image"]).open(root / "after_tab.png").convert("RGB")
    width, height = image.size
    print(f"frame={image.size}")

    print("\n== GREEN rows, left-top quadrant (target hp) ==")
    for row in scan(image, (0, 205, 0), 200, 30, 520, 120):
        print(f"  y={row[0]:3d} x={row[1]:3d}..{row[2]:3d} n={row[3]}")

    print("\n== GREEN rows, far left (player hp) ==")
    for row in scan(image, (0, 205, 0), 0, 30, 230, 130):
        print(f"  y={row[0]:3d} x={row[1]:3d}..{row[2]:3d} n={row[3]}")

    print("\n== BLUE rows, far left (mana) ==")
    for row in scan(image, (0, 0, 130), 0, 30, 230, 130):
        print(f"  y={row[0]:3d} x={row[1]:3d}..{row[2]:3d} n={row[3]}")

    pixels = image.load()
    print("\n== samples ==")
    for name, point in (
        ("target name px", (300, 66)),
        ("target name px2", (350, 66)),
        ("target hp px", (300, 82)),
        ("target hp px2", (350, 82)),
        ("player hp px", (150, 80)),
        ("mana px", (150, 94)),
    ):
        print(f"  {name} {point} -> {pixels[point[0], point[1]]}")

    width_f, height_f = float(width), float(height)
    print("\nratios for target name (x 265..390, y 58..76):")
    print(f"  {265 / width_f:.4f} {58 / height_f:.4f} {390 / width_f:.4f} {76 / height_f:.4f}")
    print("ratios for target hp (x 265..390, y 78..88):")
    print(f"  {265 / width_f:.4f} {78 / height_f:.4f} {390 / width_f:.4f} {88 / height_f:.4f}")


if __name__ == "__main__":
    main()
