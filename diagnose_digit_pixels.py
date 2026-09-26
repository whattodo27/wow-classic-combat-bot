"""Показать пиксели бокса цифры слота 1 на настоящем боевом кадре."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from combat_bot.slots import digit_box, slot_box


def main() -> int:
    path = sorted(Path("combat_frames").glob("frame_*.jpg"))[5]
    image = Image.open(path).convert("RGB")
    print(f"кадр={path.name} {image.size}")

    sbox = slot_box(1, image.size)
    dbox = digit_box(1, image.size)
    print(f"слот={sbox}")
    print(f"цифра={dbox}")

    crop = image.crop(dbox)
    scale = 12
    crop.resize((crop.width * scale, crop.height * scale), Image.NEAREST).save(
        "diag_digit_real.jpg", quality=95
    )
    print("сохранено diag_digit_real.jpg")

    print("\n--- цвета в боксе цифры (строки) ---")
    left, top, right, bottom = dbox
    for y in range(top, bottom):
        row = []
        for x in range(left, right):
            r, g, b = image.getpixel((x, y))
            if r > 90 and r - g > 45 and r - b > 45:
                row.append("R")
            elif r > 150 and g > 150 and b > 150:
                row.append("W")
            elif r + g + b < 120:
                row.append(".")
            else:
                row.append("o")
        print(f"y {y}: {''.join(row)}")

    print("\n--- весь слот 1, где красное ---")
    left, top, right, bottom = sbox
    for y in range(top, bottom):
        row = []
        for x in range(left, right):
            r, g, b = image.getpixel((x, y))
            if r > 90 and r - g > 45 and r - b > 45:
                row.append("R")
            elif r + g + b < 120:
                row.append(".")
            else:
                row.append("o")
        print(f"y {y}: {''.join(row)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
