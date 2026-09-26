"""Точно найти слоты и снять их с боевых кадров.

Полоса слотов ниже, чем считалось: на кадрах иконки начинаются примерно с
y=770. Рисуем разметку, чтобы подтвердить глазами, и меряем красный слот 1.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

FRAMES = Path("combat_frames")


def is_red(pixel) -> bool:
    r, g, b = pixel
    return r > 90 and r - g > 45 and r - b > 45


def main() -> int:
    paths = sorted(FRAMES.glob("frame_*.jpg"))
    if not paths:
        print("нет кадров")
        return 1

    image = Image.open(paths[0]).convert("RGB")
    width, height = image.size
    print(f"кадр={width}x{height}, кадров={len(paths)}")

    # Нижняя часть окна с координатной сеткой.
    region = (0, 740, 300, 807)
    crop = image.crop(region)
    scale = 4
    big = crop.resize((crop.width * scale, crop.height * scale), Image.NEAREST)
    draw = ImageDraw.Draw(big)
    for x in range(0, crop.width, 20):
        draw.line([(x * scale, 0), (x * scale, big.height)], fill=(0, 255, 0))
        draw.text((x * scale + 2, 2), str(x), fill=(0, 255, 0))
    for y in range(0, crop.height, 10):
        draw.line([(0, y * scale), (big.width, y * scale)], fill=(0, 255, 0))
        draw.text((2, y * scale + 2), str(y + 740), fill=(0, 255, 0))
    big.save("diag_bar_grid.jpg", quality=95)
    print("сохранено diag_bar_grid.jpg")

    # Ищем вертикальные швы: тёмные колонки в диапазоне строк иконок.
    y0, y1 = 775, 800
    scores = []
    for x in range(width):
        dark = 0
        count = 0
        for y in range(y0, y1):
            r, g, b = image.getpixel((x, y))
            count += 1
            if r + g + b < 160:
                dark += 1
        scores.append(dark / max(1, count))

    seams = []
    start = None
    for x, value in enumerate(scores):
        if value >= 0.6:
            if start is None:
                start = x
        else:
            if start is not None:
                seams.append((start, x - 1))
                start = None
    if start is not None:
        seams.append((start, width - 1))

    print(f"швов: {len(seams)}")
    for left, right in seams[:12]:
        print(f"  x {left}..{right}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
