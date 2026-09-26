"""Check which rows the player health bar actually uses, over many frames."""
from __future__ import annotations

import time
from collections import Counter
from pathlib import Path

from combat_bot.capture import WindowCapture
from combat_bot.config import load_config
from combat_bot.layout import UiLayout


def main() -> None:
    root = Path(__file__).parent
    config = load_config(root / "combat_config.json")
    capture = WindowCapture(config.window_title)
    layout = UiLayout()
    capture.focus()
    time.sleep(0.5)

    greens = Counter()
    samples = []
    for _ in range(12):
        image = capture.capture_image()
        if image is None:
            print("window not found")
            return
        left, top, right, bottom = layout.player_health_box(image.size)
        crop = image.crop((left - 40, top - 6, right + 120, bottom + 22))
        crop.resize((crop.size[0] * 4, crop.size[1] * 4), Image_LANCZOS).save(
            root / "crop_hp_zoom.png"
        )
        pixels = image.convert("RGB").load()
        for y in range(top - 4, bottom + 12):
            xs = [
                x
                for x in range(max(0, left - 60), min(image.size[0], right + 140))
                if abs(pixels[x, y][0] - 0) <= 40
                and abs(pixels[x, y][1] - 205) <= 45
                and abs(pixels[x, y][2] - 0) <= 40
            ]
            if xs:
                greens[y] += 1
                samples.append((y, min(xs), max(xs), len(xs)))
    print("green rows seen (row: frames):")
    for row, count in sorted(greens.items()):
        print(f"  y={row:3d}  frames={count}")
    print()
    print("layout player_health box:", layout.player_health_box((1040, 807)))
    print("layout player_mana box:  ", layout.player_mana_box((1040, 807)))
    print("saved crop_hp_zoom.png")


try:
    from PIL import Image

    Image_LANCZOS = Image.LANCZOS
except Exception:  # pragma: no cover
    Image_LANCZOS = None


if __name__ == "__main__":
    main()
