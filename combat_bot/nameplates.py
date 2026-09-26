"""Поиск nameplate'ов существ на экране.

Плашка существа состоит из жёлтого имени и полосы здоровья под ним.
Когда цель выбрана, её плашка остаётся непрозрачной, а у остальных
плашки становятся полупрозрачными - это позволяет отличить выбранную цель.

Так как на плашке есть полоса здоровья, её легко найти по горизонтальному
отрезку насыщенного цвета, а имя находится прямо над ним.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from PIL import Image

from .facing import Nameplate

# Имя существа рисуется жёлтым (невыбранная) или белым (выбранная).
NAME_YELLOW = (216, 185, 0)
NAME_YELLOW_TOLERANCE = 70
NAME_WHITE_TOLERANCE = 40

# Полоса здоровья: насыщенный цвет, заметно длиннее имени.
MIN_PLATE_WIDTH = 26
MAX_PLATE_WIDTH = 190
MIN_PLATE_HEIGHT = 4
MAX_PLATE_HEIGHT = 16

# Имя и полоса разнесены по вертикали.
NAME_GAP_RATIO = 0.0
MAX_NAME_DISTANCE = 34

# Полосы здоровья существ находятся выше середины экрана.
MIN_Y_RATIO = 0.06
MAX_Y_RATIO = 0.92


@dataclass(frozen=True)
class PlateScan:
    """Найденные плашки существ."""

    plates: list[Nameplate]
    selected: Optional[Nameplate] = None


def _is_saturated(pixel, min_channel: int = 70) -> bool:
    """Насыщенный цвет - полоса здоровья, а не тёмный фон."""
    r, g, b = pixel
    return max(r, g, b) >= min_channel and (max(r, g, b) - min(r, g, b)) >= 30


def _is_name_color(pixel) -> bool:
    """Жёлтое или белое имя существа."""
    r, g, b = pixel
    if r > 150 and g > 150 and b > 150:
        return True
    # Жёлтый: много красного и зелёного, почти нет синего.
    return abs(r - g) <= NAME_YELLOW_TOLERANCE and b + 60 < g


def find_health_bars(
    image: Image.Image,
    min_width: int = MIN_PLATE_WIDTH,
    max_width: int = MAX_PLATE_WIDTH,
) -> list[tuple[int, int, int, int]]:
    """Найти горизонтальные полосы здоровья существ.

    Возвращает список боксов (left, top, right, bottom).
    """
    width, height = image.size
    rgb = image.convert("RGB")

    min_y = int(height * MIN_Y_RATIO)
    max_y = int(height * MAX_Y_RATIO)

    # Считаем насыщенные пиксели в каждой строке и ищем горизонтальные
    # отрезки достаточной длины.
    boxes: list[tuple[int, int, int, int]] = []
    row_y = min_y
    while row_y <= max_y:
        runs = []
        start = None
        for x in range(width):
            pixel = rgb.getpixel((x, row_y))
            if _is_saturated(pixel):
                if start is None:
                    start = x
            else:
                if start is not None and x - start >= min_width:
                    runs.append((start, x - 1))
                start = None
        if start is not None and width - start >= min_width:
            runs.append((start, width - 1))

        for left, right in runs:
            span = right - left + 1
            if span > max_width:
                continue
            boxes.append((left, row_y, right, row_y))

        # Пропускаем блок строк, чтобы одна полоса не считалась дважды.
        row_y += 1
    return boxes


def merge_bars(
    boxes: list[tuple[int, int, int, int]],
    max_gap: int = 4,
) -> list[tuple[int, int, int, int]]:
    """Объединить строки одной полосы в один бокс."""
    if not boxes:
        return []
    ordered = sorted(boxes, key=lambda box: (box[1], box[0]))
    merged = [ordered[0]]
    for box in ordered[1:]:
        left, top, right, bottom = merged[-1]
        if (
            abs(box[1] - top) <= max_gap
            and box[0] <= right + 12
            and box[2] >= left - 12
        ):
            merged[-1] = (
                min(left, box[0]),
                min(top, box[1]),
                max(right, box[2]),
                max(bottom, box[3]),
            )
        else:
            merged.append(box)
    return merged


def find_name_above(
    image: Image.Image,
    bar: tuple[int, int, int, int],
    max_distance: int = MAX_NAME_DISTANCE,
) -> Optional[tuple[int, int, int]]:
    """Найти имя существа прямо над полосой здоровья."""
    left, top, right, _ = bar
    width = right - left + 1
    rgb = image.convert("RGB")
    width_px = rgb.size[0]

    # Ищем самую нижнюю строку с именем над полосой.
    for offset in range(1, max_distance + 1):
        y = top - offset
        if y < 0:
            return None
        hits = 0
        first_x = None
        last_x = None
        for x in range(max(0, left - 20), min(width_px, right + 20)):
            if _is_name_color(rgb.getpixel((x, y))):
                hits += 1
                if first_x is None:
                    first_x = x
                last_x = x
        if hits >= 3 and first_x is not None and last_x is not None:
            return (first_x, y, last_x - first_x + 1)
    return None


def find_plates(image: Image.Image) -> list[Nameplate]:
    """Найти все плашки существ с именами."""
    bars = merge_bars(find_health_bars(image))
    plates: list[Nameplate] = []

    for bar in bars:
        left, top, right, bottom = bar
        if bottom - top + 1 > MAX_PLATE_HEIGHT:
            continue
        name = find_name_above(image, bar)
        if name is None:
            continue
        name_x, name_y, name_w = name
        plates.append(
            Nameplate(
                x=min(name_x, left),
                y=min(name_y, top),
                width=max(name_w, right - left + 1),
                name="",
            )
        )
    return plates


def find_selected_plate(image: Image.Image) -> Optional[Nameplate]:
    """Плашка выбранной цели - та, у которой имя непрозрачное.

    Выбранная цель рисуется с рамкой и полной непрозрачностью, остальные
    плашки блёклые. Различаем по насыщенности цвета имени.
    """
    for bar in merge_bars(find_health_bars(image)):
        name = find_name_above(image, bar)
        if name is None:
            continue
        name_x, name_y, name_w = name
        rgb = image.convert("RGB")

        bright = 0
        total = 0
        for y in range(max(0, name_y - 2), name_y + 3):
            for x in range(name_x, name_x + name_w):
                r, g, b = rgb.getpixel((x, y))
                total += 1
                if r + g + b > 420:
                    bright += 1
        if total and bright / total >= 0.5:
            left, top, right, _ = bar
            return Nameplate(
                x=min(name_x, left),
                y=min(name_y, top),
                width=max(name_w, right - left + 1),
                name="",
            )
    return None
