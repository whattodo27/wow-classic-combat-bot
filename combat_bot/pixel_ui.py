"""Read WoW UI state from pixels instead of guessing with a vision model.

Health bars are solid color rectangles, which is far more reliable than asking
a 7B vision model to read small UI text. A target exists when its name plate
is present; a name is only trusted when it matches a registered template.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional, Sequence

from PIL import Image


@dataclass(frozen=True)
class UiRegion:
    """Rectangle inside the game window, in window pixels."""

    left: int
    top: int
    right: int
    bottom: int

    def crop(self, image: Image.Image) -> Image.Image:
        return image.crop((self.left, self.top, self.right, self.bottom))

    @property
    def size(self) -> tuple[int, int]:
        return (self.right - self.left, self.bottom - self.top)


@dataclass(frozen=True)
class BarReading:
    present: bool
    percent: Optional[float]


def _pixels(image: Image.Image):
    """Read pixels without the deprecated getdata() API."""
    rgb = image.convert("RGB")
    if hasattr(rgb, "get_flattened_data"):
        return list(rgb.get_flattened_data())
    return list(rgb.getdata())


def _mean_color(image: Image.Image) -> tuple[int, int, int]:
    samples = _pixels(image)
    if not samples:
        return (0, 0, 0)
    count = len(samples)
    return (
        sum(item[0] for item in samples) // count,
        sum(item[1] for item in samples) // count,
        sum(item[2] for item in samples) // count,
    )


def _color_ratio(image: Image.Image, reference: Sequence[int]) -> float:
    """Fraction of pixels close to a reference color."""
    if not reference:
        return 0.0
    red, green, blue = reference
    total = 0
    matched = 0
    for pixel_r, pixel_g, pixel_b in _pixels(image):
        total += 1
        if (
            abs(pixel_r - red) <= 30
            and abs(pixel_g - green) <= 30
            and abs(pixel_b - blue) <= 30
        ):
            matched += 1
    return matched / total if total else 0.0


def read_bar(image: Image.Image, region: UiRegion, color: Sequence[int]) -> BarReading:
    """Read a solid health/mana bar as a percentage of the full track."""
    crop = region.crop(image)
    if crop.size[0] <= 0 or crop.size[1] <= 0:
        return BarReading(present=False, percent=None)

    filled = _color_ratio(crop, color)
    if filled < 0.05:
        return BarReading(present=False, percent=None)

    # A bar row is fully colored where it is filled and dark where it is empty.
    rows = []
    width, height = crop.size
    pixels = crop.convert("RGB").load()
    reference = tuple(color)
    for y in range(height):
        count = 0
        for x in range(width):
            pixel = pixels[x, y]
            if (
                abs(pixel[0] - reference[0]) <= 30
                and abs(pixel[1] - reference[1]) <= 30
                and abs(pixel[2] - reference[2]) <= 30
            ):
                count += 1
        rows.append(count / width)
    if not rows:
        return BarReading(present=False, percent=None)

    # The bar fill occupies the row with the strongest coverage; the track is
    # as wide as the region, so the ratio is the health percentage.
    best_row = max(rows)
    if best_row <= 0.0:
        return BarReading(present=True, percent=0.0)
    return BarReading(present=True, percent=round(best_row * 100.0, 1))


def is_region_blank(image: Image.Image, region: UiRegion) -> bool:
    """True when a region is empty UI (no target frame drawn)."""
    crop = region.crop(image)
    if crop.size[0] <= 0 or crop.size[1] <= 0:
        return True
    return _mean_color(crop) == (0, 0, 0) and _color_ratio(crop, (255, 255, 255)) < 0.01


def match_template(image: Image.Image, template: Image.Image, tolerance: float = 0.85) -> bool:
    """Compare a target-name template against the name plate region."""
    region = image.convert("RGB")
    left = (region.size[0] - template.size[0]) // 2
    top = (region.size[1] - template.size[1]) // 2
    if left < 0 or top < 0:
        region = region.resize(
            (template.size[0], template.size[1]),
            Image.LANCZOS,
        )
    else:
        region = region.crop(
            (
                left,
                top,
                left + template.size[0],
                top + template.size[1],
            )
        )
    reference = list(template.convert("RGB").getdata())
    candidate = list(region.getdata())
    if len(reference) != len(candidate) or not reference:
        return False
    matched = sum(
        1
        for (ref_r, ref_g, ref_b), (pix_r, pix_g, pix_b) in zip(reference, candidate)
        if abs(ref_r - pix_r) <= 30
        and abs(ref_g - pix_g) <= 30
        and abs(ref_b - pix_b) <= 30
    )
    return (matched / len(reference)) >= tolerance
