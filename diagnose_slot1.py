"""Locate action-bar slot 1 and the combat indicator next to the portrait."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from combat_bot.capture import WindowCapture

STRIP_TOP = 0.90


def column_profile(image: Image.Image, strip_top: float = STRIP_TOP):
    """Count non-dark pixels per column inside the bottom strip."""
    width, height = image.size
    top = int(height * strip_top)
    strip = image.crop((0, top, width, height))
    rgb = strip.convert("RGB")
    data = list(rgb.getdata())
    strip_w, strip_h = rgb.size

    profile = []
    for x in range(strip_w):
        count = 0
        for y in range(strip_h):
            r, g, b = data[y * strip_w + x]
            if r + g + b > 90:
                count += 1
        profile.append(count)
    return strip, profile


def row_profile(image: Image.Image, strip_top: float = STRIP_TOP):
    width, height = image.size
    top = int(height * strip_top)
    strip = image.crop((0, top, width, height))
    rgb = strip.convert("RGB")
    data = list(rgb.getdata())
    strip_w, strip_h = rgb.size

    profile = []
    for y in range(strip_h):
        count = 0
        for x in range(strip_w):
            r, g, b = data[y * strip_w + x]
            if r + g + b > 90:
                count += 1
        profile.append(count)
    return profile


def find_runs(values, threshold, min_len):
    runs = []
    start = None
    for index, value in enumerate(values):
        if value >= threshold:
            if start is None:
                start = index
        else:
            if start is not None and index - start >= min_len:
                runs.append((start, index - 1))
            start = None
    if start is not None and len(values) - start >= min_len:
        runs.append((start, len(values) - 1))
    return runs


def main() -> int:
    capture = WindowCapture("World of Warcraft")
    image = capture.capture_image()
    if image is None:
        print("window not found")
        return 1

    image.save("diag_bar.jpg", quality=92)
    width, height = image.size
    print(f"window={width}x{height}")

    strip, cols = column_profile(image)
    strip_w, strip_h = strip.size
    print(f"strip={strip_w}x{strip_h} top={int(height * STRIP_TOP)}")

    rows = row_profile(image)
    print("\n--- row profile (y : lit pixels) ---")
    for index, value in enumerate(rows):
        bar = "#" * min(60, value // 4)
        print(f"{index:>3} : {value:>4} {bar}")

    print("\n--- column runs (lit >= 25) ---")
    for start, end in find_runs(cols, 25, 3):
        print(f"  x {start:>4}..{end:>4}  width={end - start + 1}")

    strip.resize((strip_w * 2, strip_h * 2), Image.NEAREST).save("diag_strip.jpg", quality=95)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
