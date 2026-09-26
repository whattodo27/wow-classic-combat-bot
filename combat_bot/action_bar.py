"""Detect out-of-range ability slots from the action bar.

WoW Classic draws a red rectangle around a slot whose ability cannot be used
against the current target. The distinguishing feature is that the red forms
*long horizontal lines* (the top and bottom edges of the frame), while unrelated
red elements - the XP bar, a red "?" icon inside a slot, damage text - do not.

Counting long horizontal red runs is therefore much more specific than counting
red pixels, and it is independent of window size and UI scale.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from PIL import Image


@dataclass(frozen=True)
class BarScanResult:
    out_of_range: Optional[bool]
    red_ratio: float


def _rgb(image: Image.Image):
    rgb = image.convert("RGB")
    if hasattr(rgb, "get_flattened_data"):
        return rgb, list(rgb.get_flattened_data())
    return rgb, list(rgb.getdata())


def _is_red(pixel, tolerance: int) -> bool:
    red, green, blue = pixel
    return red > 80 and red - green > tolerance and red - blue > tolerance


def red_frame_rows(
    image: Image.Image,
    tolerance: int = 55,
    min_run: int | None = None,
) -> int:
    """Count rows that look like a horizontal edge of a red slot frame.

    The run length is required relative to the strip width, so the same
    threshold works for any window size: a full slot frame is a small fraction
    of the bar, and that fraction is what identifies it.
    """
    rgb, flat = _rgb(image)
    width, height = rgb.size
    if width <= 0 or height <= 0:
        return 0
    if min_run is None:
        min_run = max(8, int(width * 0.02))
    rows = 0
    for y in range(height):
        run = 0
        best = 0
        for x in range(width):
            if _is_red(flat[y * width + x], tolerance):
                run += 1
                best = max(best, run)
            else:
                run = 0
        if best >= min_run:
            rows += 1
    return rows



def scan_action_bar(
    image: Image.Image,
    strip_top: float = 0.92,
    min_rows: int = 2,
) -> BarScanResult:
    """Report whether any action slot is unusable against the current target.

    ``None`` means the frame is too ambiguous, so callers keep their previous
    belief instead of guessing in either direction.
    """
    width, height = image.size
    top = max(0, min(int(height * strip_top), height - 1))
    strip = image.crop((0, top, width, height))
    rows = red_frame_rows(strip)
    ratio = rows / max(1, strip.size[1])
    if rows < min_rows:
        return BarScanResult(False, ratio)
    if rows < min_rows * 2:
        return BarScanResult(None, ratio)
    return BarScanResult(True, ratio)
