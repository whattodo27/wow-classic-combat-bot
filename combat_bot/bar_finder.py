"""Measure health and mana bars inside known UI rectangles."""

from __future__ import annotations

from typing import Optional, Sequence

from PIL import Image


def _pixels(image: Image.Image):
    rgb = image.convert("RGB")
    if hasattr(rgb, "get_flattened_data"):
        return list(rgb.get_flattened_data())
    return list(rgb.getdata())


def color_ratio(image: Image.Image, color: Sequence[int], tolerance: int = 40) -> float:
    """Fraction of pixels in a region close to a reference color."""
    if not color:
        return 0.0
    red, green, blue = color
    samples = _pixels(image)
    if not samples:
        return 0.0
    matched = 0
    for pixel in samples:
        if (
            abs(pixel[0] - red) <= tolerance
            and abs(pixel[1] - green) <= tolerance
            and abs(pixel[2] - blue) <= tolerance
        ):
            matched += 1
    return matched / len(samples)


def measure_bar(
    image: Image.Image,
    box: tuple[int, int, int, int],
    color: Sequence[int],
    tolerance: int = 40,
    min_ratio: float = 0.02,
) -> Optional[float]:
    """Return the filled percentage of a bar region, or None if it is empty.

    The region must cover the full bar track, so the colored pixels are the
    fill and the dark remainder is the empty part.
    """
    left, top, right, bottom = box
    width = image.size[0]
    height = image.size[1]
    x0 = max(0, min(left, width - 1))
    y0 = max(0, min(top, height - 1))
    x1 = max(x0 + 1, min(right, width))
    y1 = max(y0 + 1, min(bottom, height))
    if x1 <= x0 or y1 <= y0:
        return None

    crop = image.crop((x0, y0, x1, y1))
    # Use the row with the strongest color coverage: it is the bar body and
    # avoids counting the beveled border rows above and below.
    best = 0.0
    for y in range(crop.size[1]):
        row = crop.crop((0, y, crop.size[0], y + 1))
        best = max(best, color_ratio(row, color, tolerance))
    if best < min_ratio:
        return None
    return round(best * 100.0, 1)


def region_has_content(
    image: Image.Image,
    box: tuple[int, int, int, int],
    tolerance: int = 40,
    min_ratio: float = 0.01,
) -> bool:
    """True when a UI region is not empty (used for the target name plate)."""
    left, top, right, bottom = box
    width, height = image.size
    x0 = max(0, min(left, width - 1))
    y0 = max(0, min(top, height - 1))
    x1 = max(x0 + 1, min(right, width))
    y1 = max(y0 + 1, min(bottom, height))
    if x1 <= x0 or y1 <= y0:
        return False
    crop = image.crop((x0, y0, x1, y1))
    return color_ratio(crop, (255, 255, 255), tolerance) >= min_ratio
