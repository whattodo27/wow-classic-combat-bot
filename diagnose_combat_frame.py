"""Проверить красную рамку вокруг портрета как признак боя.

По скриншотам видно: в бою рамка вокруг аватара красная и мигает, вне боя
рамка обычная (серебристая/золотая). Это надёжнее, чем значок с цифрой,
потому что цифра меняется по другим причинам.
"""

from __future__ import annotations

from collections import Counter

from PIL import Image, ImageDraw

from combat_bot.capture import WindowCapture

PORTRAIT_RATIOS = (0.021, 0.062, 0.085, 0.143)


def _pixels(image: Image.Image):
    rgb = image.convert("RGB")
    try:
        return rgb, list(rgb.get_flattened_data())
    except AttributeError:
        return rgb, list(rgb.getdata())


def portrait_box(image: Image.Image, ratios=PORTRAIT_RATIOS):
    width, height = image.size
    return (
        int(width * ratios[0]),
        int(height * ratios[1]),
        int(width * ratios[2]),
        int(height * ratios[3]),
    )


def frame_redness(image: Image.Image, box=None):
    """Доля красных пикселей в кольце вокруг портрета."""
    if box is None:
        box = portrait_box(image)
    left, top, right, bottom = box
    w = right - left
    h = bottom - top

    # Кольцо: внешние 22% с каждой стороны.
    t = max(1, int(min(w, h) * 0.16))
    ring = image.crop((left, top, left + w, top + t))
    ring2 = image.crop((left, bottom - t, left + w, bottom))
    ring3 = image.crop((left, top, left + t, top + h))
    ring4 = image.crop((left + w - t, top, left + w, top + h))

    total = 0
    red = 0
    for part in (ring, ring2, ring3, ring4):
        rgb, data = _pixels(part.convert("RGB"))
        for r, g, b in data:
            total += 1
            if r > 90 and r - g > 45 and r - b > 45:
                red += 1
    return {
        "red": red,
        "total": total,
        "ratio": red / max(1, total),
    }


def main() -> int:
    capture = WindowCapture("World of Warcraft")
    capture.focus()
    image = capture.capture_image()
    if image is None:
        print("окно не найдено")
        return 1

    image.save("current_window.jpg", quality=92)
    width, height = image.size
    print(f"окно={width}x{height}")

    box = portrait_box(image)
    print(f"рамка портрета: {box}")

    for attempt in range(4):
        stats = frame_redness(image, box)
        print(
            f"[{attempt}] красных={stats['red']:>5} из {stats['total']:>5} "
            f"({stats['ratio']:.4f})"
        )
        image.crop(box).resize(
            ((box[2] - box[0]) * 4, (box[3] - box[1]) * 4), Image.NEAREST
        ).save(f"diag_frame_{attempt}.jpg", quality=95)
        import time
        time.sleep(0.7)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
