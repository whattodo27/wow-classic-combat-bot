"""Слоты панели действий: геометрия, цифра кнопки, красный индикатор.

Калибровка на боевых кадрах 1040x807 (diagnose_digit_pixels.py показал
реальные пиксели цифры):
* слот 1 (Auto Shot, лук) - x 21..76, y 754..799
* цифра «1» рисуется НЕ в углу слота, а примерно в его середине:
  красные пиксели лежат на y = top+8..top+10, x = left+22..left+24
* цифра белая - способность доступна, красная - недоступна
* цифра очень узкая (3-5 пикселей), поэтому смотрим на верхние строки
  середины слота, а не на угол
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from PIL import Image

# Слоты начинаются сразу под полосой опыта.
SLOT_W_RATIO = 0.0529
SLOT_H_RATIO = 0.0558
SLOT_LEFT_RATIO = 0.0202
SLOT_TOP_RATIO = 0.9343
SLOT_COUNT = 12

# Цифра сидит в верхней части середины слота.
DIGIT_X_RATIO = 0.28
DIGIT_Y_RATIO = 0.14
DIGIT_W_RATIO = 0.16
DIGIT_H_RATIO = 0.13

# Пороги: доля красного в боксе цифры.
DIGIT_RED_THRESHOLD = 0.06
DIGIT_MIN_PIXELS = 3
DIGIT_WHITE_MIN = 3


@dataclass(frozen=True)
class SlotState:
    """Состояние слота по пикселям цифры кнопки."""

    index: int
    red_ratio: float
    red_pixels: int
    white_pixels: int

    @property
    def is_red(self) -> bool:
        """Цифра красная - способность недоступна (вне зоны или кулдаун)."""
        return self.red_pixels >= DIGIT_MIN_PIXELS and self.red_ratio >= DIGIT_RED_THRESHOLD

    @property
    def is_white(self) -> bool:
        return self.white_pixels >= DIGIT_WHITE_MIN and not self.is_red


def _is_red(pixel, tolerance: int = 45) -> bool:
    r, g, b = pixel
    return r > 90 and r - g > tolerance and r - b > tolerance


def _is_white(pixel) -> bool:
    r, g, b = pixel
    return r > 150 and g > 150 and b > 150


def slot_box(index: int, size: tuple[int, int]) -> tuple[int, int, int, int]:
    """Бокс слота (1-based) по размеру окна."""
    width, height = size
    slot_w = max(8, int(width * SLOT_W_RATIO))
    slot_h = max(8, int(height * SLOT_H_RATIO))
    left = int(width * SLOT_LEFT_RATIO) + slot_w * (index - 1)
    top = int(height * SLOT_TOP_RATIO)
    return (left, top, left + slot_w, min(height, top + slot_h))


def digit_box(index: int, size: tuple[int, int]) -> tuple[int, int, int, int]:
    """Бокс, где игра рисует цифру кнопки."""
    left, top, right, bottom = slot_box(index, size)
    box_w = right - left
    box_h = bottom - top
    dx = max(2, int(box_w * DIGIT_X_RATIO))
    dy = max(2, int(box_h * DIGIT_Y_RATIO))
    dw = max(3, int(box_w * DIGIT_W_RATIO))
    dh = max(3, int(box_h * DIGIT_H_RATIO))
    return (left + dx, top + dy, left + dx + dw, top + dy + dh)


def read_slot(image: Image.Image, index: int) -> SlotState:
    """Прочитать цифру слота и определить её цвет."""
    left, top, right, bottom = digit_box(index, image.size)
    crop = image.crop((left, top, right, bottom)).convert("RGB")

    red = 0
    white = 0
    total = 0
    for pixel in crop.getdata():
        total += 1
        if _is_red(pixel):
            red += 1
        elif _is_white(pixel):
            white += 1

    return SlotState(
        index=index,
        red_ratio=red / max(1, total),
        red_pixels=red,
        white_pixels=white,
    )


def scan_slots(image: Image.Image, count: int = SLOT_COUNT) -> dict[int, SlotState]:
    """Прочитать все слоты панели."""
    return {index: read_slot(image, index) for index in range(1, count + 1)}


def auto_shot_out_of_range(image: Image.Image) -> Optional[bool]:
    """Дистанция по слоту 1 (Auto Shot, дальность 5-35 ярдов).

    True - цифра красная, цель вне зоны, надо подходить.
    False - цифра белая, цель в зоне.
    None - данных недостаточно, решение принимать нельзя.
    """
    state = read_slot(image, 1)
    if state.is_red:
        return True
    if state.is_white:
        return False
    return None
