"""Найти слоты по фиолетовым полосам опыта и проверить чтение цифры.

Полоса опыта (фиолетовая) идёт ровно над слотами, поэтому по её сегментам
можно точно восстановить колонки слотов, не гадая с размерами.
"""

from __future__ import annotations

from PIL import Image, ImageDraw

from combat_bot.capture import WindowCapture

BAR_TOP = 0.86


def _pixels(image: Image.Image):
    rgb = image.convert("RGB")
    try:
        return rgb, list(rgb.get_flattened_data())
    except AttributeError:
        return rgb, list(rgb.getdata())


def is_purple(pixel) -> bool:
    """Цвет полосы опыта: (104, 0, 99) и рядом."""
    r, g, b = pixel
    return r > 70 and b > 70 and g < 60 and r - g > 40 and b - g > 40


def find_xp_row(image: Image.Image, strip_top: float = BAR_TOP):
    """Найти строку с наибольшим количеством фиолетовых пикселей."""
    width, height = image.size
    top = int(height * strip_top)
    strip = image.crop((0, top, width, height))
    rgb, data = _pixels(strip)
    sw, sh = rgb.size

    best = None
    for y in range(sh):
        hits = sum(1 for x in range(sw) if is_purple(data[y * sw + x]))
        if best is None or hits > best[1]:
            best = (y, hits)
    if best is None or best[1] < 20:
        return None
    return top + best[0], best[1]


def find_segments(image: Image.Image, y: int, min_width: int = 20, max_gap: int = 8):
    """Сегменты фиолетовой полосы: возвращает список (left, right)."""
    rgb = image.convert("RGB")
    width = rgb.size[0]
    row = [rgb.getpixel((x, y)) for x in range(width)]

    runs = []
    start = None
    gap = 0
    for x, pixel in enumerate(row):
        if is_purple(pixel):
            if start is None:
                start = x
            gap = 0
        else:
            if start is not None:
                gap += 1
                if gap >= max_gap:
                    if x - gap - start >= min_width:
                        runs.append((start, x - gap))
                    start = None
                    gap = 0
    if start is not None and width - start >= min_width:
        runs.append((start, width - 1))
    return runs


def main() -> int:
    capture = WindowCapture("World of Warcraft")
    image = capture.capture_image()
    if image is None:
        print("окно не найдено")
        return 1

    image.save("current_window.jpg", quality=92)
    width, height = image.size
    print(f"окно={width}x{height}")

    row = find_xp_row(image)
    if row is None:
        print("фиолетовая полоса не найдена")
        return 1
    xp_y, hits = row
    print(f"строка опыта: y={xp_y} (фиолетовых={hits})")

    segments = find_segments(image, xp_y)
    print(f"сегментов: {len(segments)}")
    for index, (left, right) in enumerate(segments[:6], start=1):
        print(f"  слот {index}: x {left}..{right}  ширина={right - left + 1}")

    # Слоты идут ниже полосы опыта до низа окна.
    bar_bottom = height - 1
    slot_top = xp_y + 3
    slot_h = bar_bottom - slot_top

    marked = image.convert("RGB")
    draw = ImageDraw.Draw(marked)
    for index, (left, right) in enumerate(segments, start=1):
        box_w = right - left + 1
        # Цифра в правом верхнем углу слота.
        dw = max(6, int(box_w * 0.34))
        dh = max(6, int(slot_h * 0.30))
        dbox = (right - dw + 1, slot_top + 1, right + 1, slot_top + dh + 1)
        draw.rectangle([left, slot_top, right, bar_bottom], outline=(0, 255, 0))
        draw.rectangle(dbox, outline=(255, 255, 0))
        if index <= 2:
            crop = image.crop(dbox)
            crop.resize((crop.width * 8, crop.height * 8), Image.NEAREST).save(
                f"diag_digit_{index}.jpg", quality=95
            )
            print(f"\n  слот {index} кнопка: {dbox}")

    marked.crop((0, slot_top - 12, min(width, 320), bar_bottom + 1)).resize(
        (min(width, 320) * 3, (bar_bottom + 1 - slot_top + 12) * 3), Image.NEAREST
    ).save("diag_marked_slots.jpg", quality=95)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
