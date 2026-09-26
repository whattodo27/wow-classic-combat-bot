"""Собрать контактный лист из кадров боя: портреты и панель слотов."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

FRAMES = Path("combat_frames")
OUT = Path("diag_sheet.jpg")

PORTRAIT = (21, 50, 88, 115)
BAR = (0, 745, 340, 807)


def is_red(pixel) -> bool:
    r, g, b = pixel
    return r > 90 and r - g > 45 and r - b > 45


def frame_redness(image: Image.Image, box):
    left, top, right, bottom = box
    w, h = right - left, bottom - top
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
    return red / max(1, total)


def slot_one_red(image: Image.Image):
    """Красная ли доля в первом слоте (лук, Auto Shot)."""
    crop = image.crop((14, 755, 63, 807))
    red = 0
    total = 0
    for pixel in crop.convert("RGB").getdata():
        total += 1
        if is_red(pixel):
            red += 1
    return red / max(1, total)


def main() -> int:
    paths = sorted(FRAMES.glob("frame_*.jpg"))
    if not paths:
        print("нет кадров")
        return 1
    print(f"кадров: {len(paths)}")

    tile = 150
    cols = 5
    rows = (len(paths) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tile * 2, rows * (tile + 34)), (0, 0, 0))
    draw = ImageDraw.Draw(sheet)

    for index, path in enumerate(paths):
        image = Image.open(path).convert("RGB")
        redness = frame_redness(image, PORTRAIT)
        slot_red = slot_one_red(image)

        x = (index % cols) * tile * 2
        y = (index // cols) * (tile + 34)

        portrait = image.crop(PORTRAIT).resize((tile, tile), Image.NEAREST)
        bar = image.crop(BAR).resize((tile * 2, tile * 2 // 3), Image.NEAREST)
        sheet.paste(portrait, (x, y))
        sheet.paste(bar, (x, y + tile))
        draw.text((x + 3, y + 3), f"{index}", fill=(0, 255, 0))
        draw.text(
            (x + 3, y + tile + 3),
            f"frame {redness:.2f} slot {slot_red:.2f}",
            fill=(255, 210, 0),
        )

    sheet.save(OUT, quality=92)
    print(f"сохранено {OUT}  ({sheet.size[0]}x{sheet.size[1]})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
