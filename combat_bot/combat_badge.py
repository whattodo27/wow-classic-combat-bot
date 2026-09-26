"""Определить бой по скрещённым мечам под портретом.

По боевым кадрам: в бою под портретом красный круг с мечами, вне боя там
номер уровня (цифра в круге). Отличие - круг красный в бою и тёмный вне боя,
плюс в бою мечи рисуются крестом, а цифра вертикальной чертой.

Калибровка на 1040x807: круг значка в районе x 22..48, y 88..114.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from PIL import Image

BADGE_LEFT = 0.0212
BADGE_TOP = 0.1091
BADGE_W = 0.0250
BADGE_H = 0.0322

# Порог доли красного в круге: в бою круг красный, вне боя тёмный.
COMBAT_RED_THRESHOLD = 0.10
# Ниже этого значения точно не бой.
NOT_COMBAT_RED_THRESHOLD = 0.04


@dataclass(frozen=True)
class CombatBadge:
    """Состояние индикатора боя у портрета."""

    red_ratio: float
    lit_pixels: int

    @property
    def in_combat(self) -> Optional[bool]:
        # Пустой кадр - это не «вне боя», а «нечего читать»: окно могло
        # быть перекрыто или ещё не отрисовалось. Решение не принимаем.
        if self.lit_pixels < 3:
            return None
        if self.red_ratio >= COMBAT_RED_THRESHOLD:
            return True
        if self.red_ratio < NOT_COMBAT_RED_THRESHOLD:
            return False
        return None


def badge_box(size: tuple[int, int]) -> tuple[int, int, int, int]:
    width, height = size
    left = int(width * BADGE_LEFT)
    top = int(height * BADGE_TOP)
    return (
        left,
        top,
        left + max(4, int(width * BADGE_W)),
        top + max(4, int(height * BADGE_H)),
    )


def read_combat_badge(image: Image.Image) -> CombatBadge:
    """Прочитать индикатор боя: красный круг с мечами или тёмный с цифрой."""
    left, top, right, bottom = badge_box(image.size)
    crop = image.crop((left, top, right, bottom)).convert("RGB")

    red = 0
    lit = 0
    total = 0
    for r, g, b in crop.getdata():
        total += 1
        if r > 90 and r - g > 45 and r - b > 45:
            red += 1
        if r + g + b > 300:
            lit += 1

    return CombatBadge(
        red_ratio=red / max(1, total),
        lit_pixels=lit,
    )


def in_combat(image: Image.Image) -> Optional[bool]:
    """True - персонаж в бою, False - нет, None - неясно."""
    return read_combat_badge(image).in_combat
