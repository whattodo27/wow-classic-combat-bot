"""Find WoW UI bar regions by scanning pixel colors (diagnostic only)."""
from __future__ import annotations

import base64
from collections import Counter
from io import BytesIO
from pathlib import Path

import mss
from PIL import Image

from combat_bot.capture import find_window_by_title
from combat_bot.config import load_config


def capture_full(rect, path: Path) -> Image.Image:
    with mss.mss() as sct:
        shot = sct.grab(
            {
                "left": rect.left,
                "top": rect.top,
                "width": rect.width,
                "height": rect.height,
            }
        )
    image = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")
    image.save(path)
    return image


def is_red(pixel):
    r, g, b = pixel
    return r > 120 and r > g + 50 and r > b + 50


def is_green(pixel):
    r, g, b = pixel
    return g > 110 and g > r + 40 and g > b + 40


def is_blue(pixel):
    r, g, b = pixel
    return b > 110 and b > r + 40 and b > g + 30


def find_runs(image, predicate, min_length=25, max_rows=4):
    width, height = image.size
    pixels = image.load()
    runs = []
    for y in range(height):
        row = [x for x in range(width) if predicate(pixels[x, y])]
        if len(row) < min_length:
            continue
        start = previous = row[0]
        best = (start, previous)
        for x in row[1:] + [None]:
            if x is not None and x == previous + 1:
                previous = x
                continue
            if previous - start + 1 >= min_length:
                if best[1] - best[0] < previous - start:
                    best = (start, previous)
            if x is not None:
                start = previous = x
        runs.append((y, best[0], best[1]))
    if not runs:
        return []
    # Keep only the longest run per contiguous band of rows.
    runs.sort(key=lambda item: item[2] - item[1], reverse=True)
    return runs[:max_rows]


def main() -> None:
    config = load_config(Path(__file__).parent / "combat_config.json")
    rect = find_window_by_title(config.window_title)
    if rect is None:
        print("window not found")
        return
    print(f"window rect: {rect}")
    path = Path("calibration_full.png")
    image = capture_full(rect, path)
    print(f"image size: {image.size}  saved: {path}")

    for label, predicate in (
        ("red(target/mob)", is_red),
        ("green(player hp)", is_green),
        ("blue(mana)", is_blue),
    ):
        print(f"\n== {label} ==")
        for y, x0, x1 in find_runs(image, predicate):
            print(f"  row y={y:4d}  x={x0:4d}..{x1:4d}  width={x1 - x0 + 1:4d}")

    print("\n== top-area common colors ==")
    pixels = image.load()
    counter = Counter()
    for y in range(0, min(140, image.size[1])):
        for x in range(0, image.size[0], 2):
            counter[pixels[x, y]] += 1
    for color, count in counter.most_common(12):
        print(f"  {color}  {count}")


if __name__ == "__main__":
    main()
