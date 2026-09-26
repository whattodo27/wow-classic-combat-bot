"""Определить бой по индикатору у портрета: мечи или цифра уровня.

У аватара внизу слева стоит круглый значок. В бою там скрещённые мечи, вне
боя - цифра уровня. Значок всегда на месте, поэтому достаточно отличить
светлые пиксели значка от пустого места под ним.
"""

from __future__ import annotations

from PIL import Image

from combat_bot.capture import WindowCapture

# Значок у портрета: примерно 26-30 пикселей, под кругом аватара.
BADGE_RATIOS = (0.028, 0.058, 0.072, 0.098)


def _pixels(image: Image.Image):
    rgb = image.convert("RGB")
    try:
        return rgb, list(rgb.get_flattened_data())
    except AttributeError:
        return rgb, list(rgb.getdata())


def badge_box(image: Image.Image, ratios=BADGE_RATIOS):
    width, height = image.size
    return (
        int(width * ratios[0]),
        int(height * ratios[1]),
        int(width * ratios[2]),
        int(height * ratios[3]),
    )


def badge_stats(image: Image.Image, box=None):
    """Сколько светлых пикселей в значке."""
    if box is None:
        box = badge_box(image)
    crop = image.crop(box)
    rgb, data = _pixels(crop)
    w, h = rgb.size

    bright = 0
    total = w * h
    for r, g, b in data:
        if r + g + b > 330:
            bright += 1
    return {
        "box": (w, h),
        "bright": bright,
        "total": total,
        "ratio": bright / max(1, total),
    }


def main() -> int:
    capture = WindowCapture("World of Warcraft")
    image = capture.capture_image()
    if image is None:
        print("окно не найдено")
        return 1

    image.save("current_window.jpg", quality=92)
    width, height = image.size
    print(f"окно={width}x{height}")

    box = badge_box(image)
    print(f"значок: {box}  размер={box[2]-box[0]}x{box[3]-box[1]}")

    stats = badge_stats(image)
    print(f"светлых={stats['bright']} из {stats['total']} ({stats['ratio']:.3f})")

    crop = image.crop(box)
    crop.resize((crop.width * 6, crop.height * 6), Image.NEAREST).save(
        "diag_badge.jpg", quality=95
    )

    # Проверим сетку смещений, если текущая точка не попала в значок.
    print("\n--- поиск по сетке смещений ---")
    best = None
    for dy in range(-14, 15, 2):
        for dx in range(-10, 11, 2):
            shifted = (
                box[0] + dx,
                box[1] + dy,
                box[2] + dx,
                box[3] + dy,
            )
            data = badge_stats(image, shifted)
            if best is None or data["bright"] > best[1]["bright"]:
                best = (shifted, data)
    if best is not None:
        print(f"лучшее: {best[0]}  светлых={best[1]['bright']}")
        crop = image.crop(best[0])
        crop.resize((crop.width * 6, crop.height * 6), Image.NEAREST).save(
            "diag_badge_best.jpg", quality=95
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
