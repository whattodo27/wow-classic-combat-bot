"""Найти плашки существ на боевых кадрах и проверить детектор."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

from combat_bot.capture import WindowCapture
from combat_bot.facing import (
    Facing,
    apex_position,
    pick_target_in_cone,
)
from combat_bot.nameplates import find_plates, find_selected_plate

FRAMES = Path("combat_frames")


def main() -> int:
    capture = WindowCapture("World of Warcraft")
    capture.focus()
    image = capture.capture_image()
    if image is None:
        print("окно не найдено")
        return 1

    image.save("current_window.jpg", quality=92)
    size = image.size
    print(f"окно={size}")

    paths = sorted(FRAMES.glob("frame_*.jpg"))
    total = 0
    found_any = 0

    for path in paths[:5]:
        try:
            index = int(path.stem.split("_")[-1])
        except ValueError:
            continue
        frame = Image.open(path).convert("RGB")
        plates = find_plates(frame)
        selected = find_selected_plate(frame)
        total += 1
        if plates:
            found_any += 1
        print(
            f"кадр {index}: плашек={len(plates)} "
            f"выбрана={'да' if selected else 'нет'} "
            f"{[(p.x, p.y, p.width) for p in plates[:5]]}"
        )

    if total:
        print(f"\nкадров с плашками: {found_any} из {total}")

    # Живое окно.
    plates = find_plates(image)
    selected = find_selected_plate(image)
    facing = Facing(*apex_position(size), angle=0.0)
    best = pick_target_in_cone(plates, facing, size)
    print(f"\nживое окно: плашек={len(plates)} выбрана={'да' if selected else 'нет'}")
    print(f"плашки: {[(p.x, p.y, p.width) for p in plates[:8]]}")
    print(f"в конусе: {best}")

    marked = image.convert("RGB")
    draw = ImageDraw.Draw(marked)
    for plate in plates:
        draw.rectangle(
            [plate.x, plate.y, plate.x + plate.width, plate.y + 18],
            outline=(0, 255, 0),
        )
    x, y = apex_position(size)
    draw.line([(x, y), (x, y - 260)], fill=(255, 0, 255), width=2)
    marked.save("diag_plates.jpg", quality=92)
    print("сохранено diag_plates.jpg")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
