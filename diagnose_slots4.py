"""Найти слоты по тёмным вертикальным швам между иконками.

Полоса опыта непрерывная, поэтому по ней слоты не определить. Зато между
иконками видны тонкие тёмные вертикальные швы, и их положение совпадает с
границами слотов. Слот = промежуток между соседними швами.
"""

from __future__ import annotations

from PIL import Image, ImageDraw

from combat_bot.capture import WindowCapture

# Полоса слотов: между полосой опыта и низом окна.
BAR_TOP = 0.86
# Иконки занимают примерно верхнюю часть полосы, по ним ищем швы.
ICON_BAND = (0.28, 0.62)


def _pixels(image: Image.Image):
    rgb = image.convert("RGB")
    try:
        return rgb, list(rgb.get_flattened_data())
    except AttributeError:
        return rgb, list(rgb.getdata())


def find_xp_row(image: Image.Image, strip_top: float = BAR_TOP):
    """Строка полосы опыта - по ней определяем верх полосы слотов."""
    width, height = image.size
    top = int(height * strip_top)
    strip = image.crop((0, top, width, height))
    rgb, data = _pixels(strip)
    sw, sh = rgb.size

    def is_purple(pixel):
        r, g, b = pixel
        return r > 70 and b > 70 and g < 60 and r - g > 40 and b - g > 40

    best_y, best_hits = 0, 0
    for y in range(sh):
        hits = sum(1 for x in range(sw) if is_purple(data[y * sw + x]))
        if hits > best_hits:
            best_y, best_hits = y, hits
    if best_hits < 20:
        return None
    return top + best_y, best_hits


def find_seams(image: Image.Image, y0: int, y1: int):
    """Столбцы внутри диапазона строк, которые одинаково тёмные."""
    rgb = image.convert("RGB")
    width = rgb.size[0]
    rows = range(y0, y1)

    scores = []
    for x in range(width):
        dark = 0
        total = 0
        for y in rows:
            r, g, b = rgb.getpixel((x, y))
            total += 1
            if r + g + b < 150:
                dark += 1
        scores.append(dark / max(1, total))

    runs = []
    start = None
    for x, value in enumerate(scores):
        if value >= 0.75:
            if start is None:
                start = x
        else:
            if start is not None and x - start >= 1:
                runs.append((start, x - 1))
            start = None
    if start is not None:
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
    print(f"окон={width}x{height}")

    found = find_xp_row(image)
    if found is None:
        print("полоса опыта не найдена")
        return 1
    xp_y, hits = found
    slot_top = xp_y + 4
    print(f"строка опыта y={xp_y}, фиолетовых={hits}, верх слотов={slot_top}")

    bar_h = height - slot_top
    y0 = slot_top + int(bar_h * ICON_BAND[0])
    y1 = slot_top + int(bar_h * ICON_BAND[1])
    print(f"полоса поиска швов: y {y0}..{y1}")

    seams = find_seams(image, y0, y1)
    print(f"швов: {len(seams)}")
    for left, right in seams[:10]:
        print(f"  x {left}..{right} (ширина {right - left + 1})")

    bar_bottom = height - 1
    slots = []
    for index in range(len(seams) - 1):
        left = seams[index][1] + 1
        right = seams[index + 1][0] - 1
        if right - left >= 30:
            slots.append((index + 1, left, right))

    print(f"\nслотов: {len(slots)}")
    marked = image.convert("RGB")
    draw = ImageDraw.Draw(marked)

    for slot_index, left, right in slots[:8]:
        box_w = right - left
        dw = max(6, int(box_w * 0.32))
        dh = max(6, int(bar_h * 0.30))
        dbox = (right - dw + 1, slot_top + 1, right + 1, slot_top + dh + 1)
        draw.rectangle([left, slot_top, right, bar_bottom], outline=(0, 255, 0))
        draw.rectangle(dbox, outline=(255, 255, 0))
        print(f"  слот {slot_index}: x {left}..{right} w={box_w} цифра={dbox}")
        if slot_index <= 3:
            crop = image.crop(dbox)
            crop.resize((crop.width * 8, crop.height * 8), Image.NEAREST).save(
                f"diag_digit_{slot_index}.jpg", quality=95
            )

    marked.crop((0, slot_top - 14, 340, bar_bottom + 1)).resize(
        (340 * 3, (bar_bottom + 1 - slot_top + 14) * 3), Image.NEAREST
    ).save("diag_marked_slots.jpg", quality=95)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
