"""Показать реальные цвета рамки слота, чтобы понять порог детектора."""

from __future__ import annotations

from collections import Counter

from PIL import Image

from combat_bot.capture import WindowCapture

BAR_TOP = 0.86


def main() -> int:
    capture = WindowCapture("World of Warcraft")
    image = capture.capture_image()
    if image is None:
        print("окно не найдено")
        return 1

    image.save("current_window.jpg", quality=92)
    width, height = image.size
    print(f"окно={width}x{height}")

    top = int(height * BAR_TOP)
    strip = image.crop((0, top, width, height))
    rgb = strip.convert("RGB")
    data = list(rgb.getdata())
    sw, sh = rgb.size
    print(f"полоса={sw}x{sh}, верх={top}")

    # Считаем цвета по строкам, чтобы найти границы иконок.
    print("\n--- строки: сколько пикселей не тёмные ---")
    for y in range(sh):
        lit = sum(1 for x in range(sw) if sum(data[y * sw + x]) > 150)
        if lit > 0:
            print(f"  y {y:>3} (abs {top + y:>4}) : {lit:>4}")

    # Горизонтальный срез через середину иконок - ищем вертикальные рамки.
    mid = sh // 2
    print(f"\n--- срез y={mid} (abs {top + mid}), цвета слева направо ---")
    row = []
    for x in range(min(120, sw)):
        row.append(data[mid * sw + x])
    for x in range(0, len(row), 1):
        r, g, b = row[x]
        if x % 10 == 0:
            print(f"\n  x {x:>4}: ", end="")
        print(f"({r:>3},{g:>3},{b:>3})", end=" ")

    print()

    # Собираем самые частые цвета в полосе.
    counter = Counter(data)
    print("\n--- 20 самых частых цветов в полосе ---")
    for color, count in counter.most_common(20):
        print(f"  {color}  x{count}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
