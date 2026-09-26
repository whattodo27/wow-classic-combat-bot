"""Проверить детектор красной рамки на эталонных скриншотах пользователя."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

import diagnose_combat_frame as dcf

SAMPLES = [
    ("in_combat", Path.home() / "AppData/Roaming/Hermes/composer-images/image_7c1dd9.png"),
    ("unknown", Path.home() / "AppData/Roaming/Hermes/composer-images/image_a510a0.png"),
    ("live", Path("current_window.jpg")),
]


def main() -> int:
    for label, path in SAMPLES:
        if not path.exists():
            print(f"{label}: файла нет {path}")
            continue
        image = Image.open(path).convert("RGB")
        width, height = image.size
        box = dcf.portrait_box(image)
        stats = dcf.frame_redness(image, box)
        print(
            f"{label:<10} {width}x{height}  красных={stats['red']:>5} "
            f"из {stats['total']:>5}  ({stats['ratio']:.4f})"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
