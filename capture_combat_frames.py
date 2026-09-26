"""Снять серию кадров окна, чтобы поймать состояние боя.

Нужны кадры и в бою, и вне боя, чтобы откалибровать детектор красной
рамки вокруг портрета. Скрипт просто снимает N кадров подряд.
"""

from __future__ import annotations

import time
from pathlib import Path

from PIL import Image, ImageDraw

from combat_bot.capture import WindowCapture

PORTRAIT = (0.021, 0.062, 0.085, 0.143)
OUT = Path("combat_frames")


def portrait_box(image: Image.Image, ratios=PORTRAIT):
    width, height = image.size
    return (
        int(width * ratios[0]),
        int(height * ratios[1]),
        int(width * ratios[2]),
        int(height * ratios[3]),
    )


def is_red(pixel) -> bool:
    r, g, b = pixel
    return r > 90 and r - g > 45 and r - b > 45


def frame_redness(image: Image.Image, box):
    left, top, right, bottom = box
    w = right - left
    h = bottom - top
    t = max(1, int(min(w, h) * 0.16))

    parts = [
        image.crop((left, top, left + w, top + t)),
        image.crop((left, bottom - t, left + w, bottom)),
        image.crop((left, top, left + t, top + h)),
        image.crop((left + w - t, top, left + w, top + h)),
    ]
    red = 0
    total = 0
    for part in parts:
        for pixel in part.convert("RGB").getdata():
            total += 1
            if is_red(pixel):
                red += 1
    return red, total


def main() -> int:
    count = 20
    OUT.mkdir(exist_ok=True)

    capture = WindowCapture("World of Warcraft")
    capture.focus()
    print(f"Снимаю {count} кадров. Вступай в бой, пока идёт съёмка.")

    for index in range(count):
        image = capture.capture_image()
        if image is None:
            print("окно пропало")
            return 1
        red, total = frame_redness(image, portrait_box(image))
        print(f"[{index:>2}] красная рамка: {red:>5} из {total} ({red / max(1, total):.4f})")
        image.save(OUT / f"frame_{index:>2}.jpg", quality=90)
        time.sleep(0.8)

    # Собираем контактный лист портретов, чтобы осмотреть глазами.
    first = Image.open(OUT / "frame_00.jpg")
    box = portrait_box(first)
    tiles = []
    for index in range(count):
        path = OUT / f"frame_{index:>2}.jpg"
        if not path.exists():
            continue
        img = Image.open(path).convert("RGB")
        tiles.append(img.crop(box).resize((200, 200), Image.NEAREST))

    sheet = Image.new("RGB", (200 * 5, 200 * 4), (0, 0, 0))
    draw = ImageDraw.Draw(sheet)
    for index, tile in enumerate(tiles):
        x = (index % 5) * 200
        y = (index // 5) * 200
        sheet.paste(tile, (x, y))
        draw.text((x + 4, y + 4), str(index), fill=(0, 255, 0))

    sheet.save("diag_portrait_sheet.jpg", quality=92)
    print("сохранено diag_portrait_sheet.jpg")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
