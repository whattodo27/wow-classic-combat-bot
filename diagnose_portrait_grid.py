"""Снимок окна с фокусом на игре и сеткой координат (для ручной калибровки)."""

from __future__ import annotations

import sys

from PIL import Image, ImageDraw

from combat_bot.capture import WindowCapture


def main() -> int:
    focus = "--focus" in sys.argv

    capture = WindowCapture("World of Warcraft")
    if focus:
        capture.focus()
    image = capture.capture_image()
    if image is None:
        print("окно не найдено")
        return 1

    image.save("current_window.jpg", quality=92)
    width, height = image.size
    print(f"окно={width}x{height} focus={focus}")

    region = (0, 20, 230, 130)
    crop = image.crop(region)
    scale = 5
    big = crop.resize((crop.width * scale, crop.height * scale), Image.NEAREST)
    draw = ImageDraw.Draw(big)

    for x in range(0, crop.width, 10):
        draw.line([(x * scale, 0), (x * scale, big.height)], fill=(0, 255, 0))
        draw.text((x * scale + 2, 2), str(x + region[0]), fill=(0, 255, 0))
    for y in range(0, crop.height, 10):
        draw.line([(0, y * scale), (big.width, y * scale)], fill=(0, 255, 0))
        draw.text((2, y * scale + 2), str(y + region[1]), fill=(0, 255, 0))

    big.save("diag_portrait_grid.jpg", quality=95)
    print("сохранено diag_portrait_grid.jpg")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
