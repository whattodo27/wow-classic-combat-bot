"""Verify target-frame geometry against a stored frame (diagnostic only)."""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

from combat_bot.bar_finder import measure_bar, region_has_content
from combat_bot.layout import UiLayout


def main() -> None:
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "current_window.jpg")
    if not path.exists():
        print(f"missing {path}")
        return
    image = Image.open(path).convert("RGB")
    size = image.size
    layout = UiLayout()
    print(f"frame={path} size={size}")

    boxes = {
        "player_health": layout.player_health_box(size),
        "player_mana": layout.player_mana_box(size),
        "target_name": layout.target_name_box(size),
        "target_health": layout.target_health_box(size),
    }
    for name, box in boxes.items():
        print(f"  {name}: {box}")

    print(f"  player_health% = {measure_bar(image, boxes['player_health'], layout.player_health_color)}")
    print(f"  player_mana%   = {measure_bar(image, boxes['player_mana'], layout.mana_color)}")
    print(f"  target_name has content = {region_has_content(image, boxes['target_name'])}")
    print(f"  target_health% = {measure_bar(image, boxes['target_health'], layout.target_health_color)}")

    image.crop(boxes["target_name"]).save("crop_name_now.png")
    image.crop(boxes["target_health"]).save("crop_health_now.png")
    image.crop(boxes["player_health"]).save("crop_player_now.png")
    print("saved crop_name_now.png crop_health_now.png crop_player_now.png")


if __name__ == "__main__":
    main()
