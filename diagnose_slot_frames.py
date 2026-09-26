"""Locate action-bar slot frames by their grey borders and draw them.

The purple bars are the XP bar, which sits over the slots, so they cannot be
used as slot markers. Slot frames are grey rectangles with a dark interior;
detecting vertical border columns finds them.
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


def find_slots(image: Image.Image, strip_top: float = BAR_TOP):
    width, height = image.size
    top = int(height * strip_top)
    strip = image.crop((0, top, width, height))
    rgb, data = _pixels(strip)
    sw, sh = rgb.size

    def is_frame(pixel):
        r, g, b = pixel
        # Grey metal frame: brightish and not colourful.
        return 95 < r < 200 and 90 < g < 200 and 90 < b < 200 and abs(r - g) < 30 and abs(g - b) < 30

    # Vertical border columns: many lit pixels within a narrow band.
    col_hits = []
    for x in range(sw):
        hits = 0
        for y in range(sh):
            r, g, b = data[y * sw + x]
            if 110 < r < 210 and abs(r - g) < 28 and abs(g - b) < 28 and abs(r - b) < 28:
                hits += 1
        col_hits.append(hits)

    runs = []
    start = None
    for x, value in enumerate(col_hits):
        if value >= sh * 0.35:
            if start is None:
                start = x
        else:
            if start is not None and x - start >= 1:
                runs.append((start, x - 1))
            start = None
    if start is not None:
        runs.append((start, sw - 1))

    # Pair borders into boxes: left, right of each slot.
    slots = []
    for i in range(0, len(runs) - 1, 2):
        left, right = runs[i][0], runs[i + 1][1]
        if right - left >= 20:
            slots.append((left, top, right + 1, height))
    return slots


def main() -> int:
    capture = WindowCapture("World of Warcraft")
    image = capture.capture_image()
    if image is None:
        print("window not found")
        return 1
    image.save("current_window.jpg", quality=92)
    width, height = image.size
    print(f"window={width}x{height}")

    slots = find_slots(image)
    print(f"slots: {len(slots)}")

    marked = image.convert("RGB")
    draw = ImageDraw.Draw(marked)
    for index, (left, top, right, bottom) in enumerate(slots, start=1):
        print(f"  slot {index:>2}: x {left}..{right}  y {top}..{bottom}  w={right-left}")
        draw.rectangle([left, top, right - 1, bottom - 1], outline=(0, 255, 0), width=1)
        # Digit corner: top-right.
        w = right - left
        h = bottom - top
        dbox = (right - int(w * 0.42), top + int(h * 0.02), right, top + int(h * 0.34))
        draw.rectangle(list(dbox), outline=(255, 255, 0), width=1)
        if index <= 3:
            marked.crop(dbox).resize(
                (max(1, dbox[2] - dbox[0]) * 6, max(1, dbox[3] - dbox[1]) * 6),
                Image.NEAREST,
            ).save(f"diag_digit_{index}.jpg", quality=95)

    marked.crop((0, int(height * BAR_TOP), width, height)).resize(
        (width * 2, (height - int(height * BAR_TOP)) * 2), Image.NEAREST
    ).save("diag_marked_bar.jpg", quality=95)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
