"""Find action-bar slots from the purple XP segments, then locate each digit.

WoW draws one purple XP segment above every action-bar slot, so the segments
give the exact slot columns without guessing. The keybind digit lives in the
top-right corner of a slot: white when the ability is usable, red when it is
not. The digit is a stable signal, unlike the icon, which blinks.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from combat_bot.capture import WindowCapture

# Digits sit in the top-right corner of a slot.
DIGIT_W = 0.55   # fraction of slot width taken by the digit corner
DIGIT_H = 0.42   # fraction of slot height


def _pixels(image: Image.Image):
    rgb = image.convert("RGB")
    return rgb, list(rgb.getdata())


def find_xp_segments(image: Image.Image, strip_top: float = 0.88):
    """Return (y_top, y_bottom, columns) of the purple XP segments."""
    width, height = image.size
    top = int(height * strip_top)
    strip = image.crop((0, top, width, height))
    rgb, data = _pixels(strip)
    sw, sh = rgb.size

    def is_purple(pixel):
        r, g, b = pixel
        return r > 90 and b > 110 and g < r - 20 and b > g + 40

    # Rows that contain a decent amount of purple.
    row_hits = []
    for y in range(sh):
        hits = sum(1 for x in range(sw) if is_purple(data[y * sw + x]))
        row_hits.append(hits)

    if not row_hits:
        return None
    best_row = max(range(sh), key=lambda y: row_hits[y])
    if row_hits[best_row] < 10:
        return None

    # The XP band is a couple of rows tall; take the rows close to the peak.
    band = [best_row]
    for y in (best_row - 1, best_row + 1):
        if 0 <= y < sh and row_hits[y] >= row_hits[best_row] * 0.6:
            band.append(y)

    columns = []
    for x in range(sw):
        hits = sum(1 for y in band if is_purple(data[y * sw + x]))
        columns.append(hits)

    return top + min(band), top + max(band), columns


def group_columns(columns, threshold, min_gap=2):
    """Group lit columns into runs, merging runs separated by < min_gap."""
    runs = []
    start = None
    gap = 0
    for x, value in enumerate(columns):
        if value >= threshold:
            if start is None:
                start = x
            gap = 0
        else:
            if start is not None:
                gap += 1
                if gap >= min_gap:
                    runs.append((start, x - gap))
                    start = None
                    gap = 0
    if start is not None:
        runs.append((start, len(columns) - 1))
    return runs


def slot_boxes(image: Image.Image):
    """Return [(index, box)] for every action-bar slot, left to right."""
    found = find_xp_segments(image)
    if found is None:
        return []
    xp_top, xp_bottom, columns = found

    total_lit = sum(1 for value in columns if value >= 1)
    if total_lit == 0:
        return []
    runs = group_columns(columns, threshold=1, min_gap=3)

    width, height = image.size
    # The slot body starts just under the XP band and runs to the bar bottom.
    slot_top = xp_bottom + 1
    slot_bottom = height - 1

    boxes = []
    for index, (left, right) in enumerate(runs, start=1):
        boxes.append((index, (left, slot_top, right + 1, slot_bottom)))
    return boxes


def digit_box(slot_box):
    """Top-right corner of a slot, where the keybind digit is drawn."""
    left, top, right, bottom = slot_box
    box_w = right - left
    box_h = bottom - top
    dx = int(box_w * (1.0 - DIGIT_W))
    dy = int(box_h * DIGIT_H)
    return (right - dx, top, right, top + dy)


def corner_color_stats(image: Image.Image, box):
    """Redness / whiteness inside a small box."""
    left, top, right, bottom = box
    crop = image.crop(box)
    rgb, data = _pixels(crop)
    w, h = rgb.size

    red = 0
    white = 0
    bright = 0
    for pixel in data:
        r, g, b = pixel
        if r + g + b < 200:
            continue
        bright += 1
        if r > 90 and r - g > 55 and r - b > 55:
            red += 1
        elif r > 150 and g > 150 and b > 150:
            white += 1
    return {
        "bright": bright,
        "red": red,
        "white": white,
        "size": w * h,
    }


def main() -> int:
    capture = WindowCapture("World of Warcraft")
    image = capture.capture_image()
    if image is None:
        print("window not found")
        return 1

    image.save("current_window.jpg", quality=92)
    width, height = image.size
    print(f"window={width}x{height}")

    found = find_xp_segments(image)
    if found is None:
        print("NO purple XP segments found")
        return 1
    xp_top, xp_bottom, columns = found
    print(f"xp band: y {xp_top}..{xp_bottom}")
    lit = sum(1 for value in columns if value >= 1)
    print(f"xp lit columns: {lit}")

    boxes = slot_boxes(image)
    print(f"\nslots found: {len(boxes)}")
    for index, box in boxes[:14]:
        stats = corner_color_stats(image, digit_box(box))
        print(
            f"  slot {index:>2}  x {box[0]:>4}..{box[2]:>4}  "
            f"digit bright={stats['bright']:>4} red={stats['red']:>4} white={stats['white']:>4}"
        )
        if index <= 3:
            dbox = digit_box(box)
            image.crop(dbox).resize(
                (max(1, (dbox[2] - dbox[0])) * 8, max(1, (dbox[3] - dbox[1])) * 8),
                Image.NEAREST,
            ).save(f"diag_digit_{index}.jpg", quality=95)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
