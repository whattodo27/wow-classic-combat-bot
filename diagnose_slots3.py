"""Найти слоты по серым вертикальным разделителям над полосой опыта.

По цветам видно: фиолетовая полоса опыта прерывается серыми пикселями
на границах между слотами (например (141,130,135)). Эти разделители и есть
границы слотов - надёжнее, чем угадывать по яркости.
"""

from __future__ import annotations

from PIL import Image, ImageDraw

from combat_bot.capture import WindowCapture

BAR_TOP = 0.86


def is_purple(pixel) -> bool:
    r, g, b = pixel
    return r > 70 and b > 70 and g < 60 and r - g > 40 and b - g > 40


def is_divider(pixel) -> bool:
    """Серый металлический разделитель, яркий и не цветной."""
    r, g, b = pixel
    return r > 100 and b > 100 and g > 100 and abs(r - b) < 45 and abs(r - g) < 60


def find_xp_row(image: Image.Image, strip_top: float = BAR_TOP):
    width, height = image.size
    top = int(height * strip_top)
    strip = image.crop((0, top, width, height))
    rgb = strip.convert("RGB")
    sw, sh = rgb.size
    data = list(rgb.getdata())

    best_y, best_hits = None, 0
    for y in range(sh):
        hits = sum(1 for x in range(sw) if is_purple(data[y * sw + x]))
        if hits > best_hits:
            best_y, best_hits = y, hits
    if best_hits < 20:
        return None
    return top + best_y, best_hits


def find_dividers(image: Image.Image, y: int):
    """Колонки-разделители внутри фиолетовой полосы."""
    width = image.size[0]
    columns = []
    for x in range(width):
        pixel = image.getpixel((x, y))
        columns.append(is_divider(pixel) and not is_purple(pixel))

    runs = []
    start = None
    for x, flag in enumerate(columns):
        if flag:
            if start is None:
                start = x
        else:
            if start is not None:
                runs.append((start, x - 1))
                start = None
    if start is not None:
        runs.append((start, len(columns) - 1))
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

    found = find_xp_row(image)
    if found is None:
        print("полоса опыта не найдена")
        return 1
    xp_y, hits = found
    print(f"строка опыта y={xp_y}, фиолетовых={hits}")

    dividers = find_dividers(image, xp_y)
    print(f"разделителей: {len(dividers)}")
    for left, right in dividers[:8]:
        print(f"  x {left}..{right}")

    # Слот = промежуток между соседними разделителями, от полосы до низа.
    slot_top = xp_y + 3
    bar_bottom = height - 1

    slots = []
    for index in range(len(dividers) - 1):
        left = dividers[index][1] + 1
        right = dividers[index + 1][0] - 1
        if right - left >= 25:
            slots.append((index + 1, left, right))

    print(f"\nслотов: {len(slots)}")
    marked = image.convert("RGB")
    draw = ImageDraw.Draw(marked)

    for slot_index, left, right in slots[:6]:
        box_w = right - left
        dw = max(6, int(box_w * 0.30))
        dh = max(6, int((bar_bottom - slot_top) * 0.28))
        dbox = (right - dw + 1, slot_top + 1, right + 1, slot_top + dh + 1)
        draw.rectangle([left, slot_top, right, bar_bottom], outline=(0, 255, 0))
        draw.rectangle(dbox, outline=(255, 255, 0))
        print(f"  слот {slot_index}: x {left}..{right} w={box_w}  цифра={dbox}")
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
