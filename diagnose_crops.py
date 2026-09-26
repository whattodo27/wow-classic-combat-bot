"""Crop and upscale regions for visual confirmation (diagnostic only)."""
from __future__ import annotations

from pathlib import Path

from PIL import Image

REGIONS = {
    "crop_player_frame.png": (230, 40, 420, 120),
    "crop_target_frame.png": (200, 20, 640, 120),
    "crop_actionbar.png": (0, 700, 1040, 807),
    "crop_center.png": (300, 250, 740, 560),
}


def main() -> None:
    source = Image.open("calibration_full.png")
    for name, box in REGIONS.items():
        crop = source.crop(box)
        scale = min(4, max(1, 1200 // max(1, crop.size[0])))
        crop = crop.resize((crop.size[0] * scale, crop.size[1] * scale), Image.LANCZOS)
        crop.save(Path(name))
        print(f"{name}: box={box} size={crop.size} scale={scale}")


if __name__ == "__main__":
    main()
