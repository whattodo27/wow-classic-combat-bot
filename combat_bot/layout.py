"""UI geometry expressed as fractions of the window, so resizing works.

Calibration reference (measured on a 1040x807 window with a target selected):

* player health  x 103..213, y 79..83   (green)
* player mana    x  99..213, y 90..97   (blue)
* target name    x 265..390, y 58..76   (yellow name plate)
* target health  x 265..390, y 78..88   (green)

Note: the target frame sits in the top-LEFT next to the player frame, not in
the top-centre, so it must be calibrated from a frame where Tab actually
selected something.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


Box = tuple[int, int, int, int]


def _box(ratios: tuple[float, float, float, float], size: tuple[int, int]) -> Box:
    width, height = size
    left = int(round(ratios[0] * width))
    top = int(round(ratios[1] * height))
    right = int(round(ratios[2] * width))
    bottom = int(round(ratios[3] * height))
    return (
        max(0, min(left, width - 1)),
        max(0, min(top, height - 1)),
        max(left + 1, min(right, width)),
        max(top + 1, min(bottom, height)),
    )


@dataclass(frozen=True)
class UiLayout:
    player_health_ratios: tuple[float, float, float, float] = (0.0990, 0.0979, 0.2048, 0.1029)
    player_mana_ratios: tuple[float, float, float, float] = (0.0952, 0.1115, 0.2048, 0.1202)
    target_name_ratios: tuple[float, float, float, float] = (0.2548, 0.0719, 0.3750, 0.0942)
    target_health_ratios: tuple[float, float, float, float] = (0.2548, 0.0967, 0.3750, 0.1090)
    slot_ratios: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)
    target_name_color: tuple[int, int, int] = (216, 185, 0)
    target_health_color: tuple[int, int, int] = (0, 205, 0)
    player_health_color: tuple[int, int, int] = (0, 205, 0)
    mana_color: tuple[int, int, int] = (0, 0, 130)

    def player_health_box(self, size: tuple[int, int]) -> Box:
        return _box(self.player_health_ratios, size)

    def player_mana_box(self, size: tuple[int, int]) -> Box:
        return _box(self.player_mana_ratios, size)

    def target_name_box(self, size: tuple[int, int]) -> Box:
        return _box(self.target_name_ratios, size)

    def target_health_box(self, size: tuple[int, int]) -> Box:
        return _box(self.target_health_ratios, size)

    def slot_box(self, index: int, size: tuple[int, int]) -> Optional[Box]:
        """Box of action-bar slot ``index`` (1-based), or None if uncalibrated."""
        if self.slot_ratios == (0.0, 0.0, 0.0, 0.0):
            return None
        width, height = size
        left, top, right, bottom = self.slot_ratios
        slot_width = (right - left) * width
        slot_height = (bottom - top) * height
        # Slots are laid out left to right starting at ``left``.
        offset = slot_width * (index - 1)
        return _box(
            (
                left + offset / width,
                top,
                left + (offset + slot_width) / width,
                bottom,
            ),
            size,
        )

    def draw_test_bars(self, draw, size, target=True, target_ratio=0.8):
        """Helper used by tests to draw known bars at the layout positions."""
        left, top, right, bottom = self.player_health_box(size)
        draw.rectangle([left, top, right - 1, bottom - 1], fill=self.player_health_color)
        left, top, right, bottom = self.player_mana_box(size)
        draw.rectangle([left, top, right - 1, bottom - 1], fill=self.mana_color)
        if target:
            left, top, right, bottom = self.target_name_box(size)
            draw.rectangle([left, top, right - 1, bottom - 1], fill=(255, 255, 255))
            left, top, right, bottom = self.target_health_box(size)
            draw.rectangle(
                [left, top, left + int((right - left) * target_ratio), bottom - 1],
                fill=self.target_health_color,
            )
