"""Confirm a target's identity by matching a cropped name plate template.

Pixels tell us a target exists; a name template tells us *which* target it is.
Templates are registered from real frames, so no text OCR is required.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

from PIL import Image


@dataclass(frozen=True)
class TemplateMatch:
    name: Optional[str]
    score: float


def _normalized_pixels(image: Image.Image, size=(64, 12)) -> list:
    """Reduce a crop to a small grayscale grid so minor shifts still match."""
    reduced = image.convert("L").resize(size, Image.BILINEAR)
    if hasattr(reduced, "get_flattened_data"):
        data = list(reduced.get_flattened_data())
    else:
        data = list(reduced.getdata())
    if not data:
        return []
    mean = sum(data) / len(data)
    return [(value - mean) / 255.0 for value in data]


def similarity(left: Image.Image, right: Image.Image) -> float:
    """Similarity in [0, 1] between two crops of the same name plate."""
    a = _normalized_pixels(left)
    b = _normalized_pixels(right)
    if not a or len(a) != len(b):
        return 0.0
    total = sum(abs(x - y) for x, y in zip(a, b))
    return max(0.0, 1.0 - total / len(a))


class NameMatcher:
    """Maps cropped name plates to configured target names."""

    def __init__(self, templates: dict[str, Image.Image] | None = None):
        self.templates: dict[str, Image.Image] = dict(templates or {})

    def add(self, name: str, image: Image.Image) -> None:
        self.templates[name] = image

    def register_from_dir(self, directory: str | Path) -> int:
        """Load ``<name>.png`` templates from a folder."""
        path = Path(directory)
        count = 0
        for file in sorted(path.glob("*.png")):
            with Image.open(file) as handle:
                self.templates[file.stem] = handle.convert("RGB").copy()
            count += 1
        return count

    def match(self, crop: Image.Image, threshold: float = 0.86) -> TemplateMatch:
        if not self.templates:
            return TemplateMatch(None, 0.0)
        best_name = None
        best_score = 0.0
        for name, template in self.templates.items():
            score = similarity(crop, template)
            if score > best_score:
                best_score = score
                best_name = name
        if best_score < threshold:
            return TemplateMatch(None, best_score)
        return TemplateMatch(best_name, best_score)
