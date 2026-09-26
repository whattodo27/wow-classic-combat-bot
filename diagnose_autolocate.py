"""Auto-locate the target frame by diffing frames before/after Tab (diagnostic)."""
from __future__ import annotations

import time
from pathlib import Path

from PIL import Image, ImageChops

from combat_bot.capture import WindowCapture
from combat_bot.config import load_config


def changed_regions(before: Image.Image, after: Image.Image, threshold=40):
    diff = ImageChops.difference(before.convert("RGB"), after.convert("RGB"))
    gray = diff.convert("L")
    bbox = gray.point(lambda value: 255 if value > threshold else 0).getbbox()
    return bbox


def main() -> None:
    root = Path(__file__).parent
    config = load_config(root / "combat_config.json")
    capture = WindowCapture(config.window_title)
    capture.focus()
    time.sleep(1.0)

    before = capture.capture_image()
    if before is None:
        print("window not found")
        return
    print(f"before size={before.size}")

    pyautogui_press_target()
    time.sleep(1.0)

    after = capture.capture_image()
    if after is None:
        print("capture failed")
        return
    after.save(root / "after_tab.png")
    print(f"after size={after.size}")

    bbox = changed_regions(before, after)
    print(f"changed bbox: {bbox}")
    if bbox is None:
        print("no visible change: Tab probably found no target")
        return

    left, top, right, bottom = bbox
    width, height = after.size
    print("ratios (store in layout):")
    print(f"  left   {left / width:.4f}")
    print(f"  top    {top / height:.4f}")
    print(f"  right  {right / width:.4f}")
    print(f"  bottom {bottom / height:.4f}")

    after.crop(bbox).save(root / "target_frame_crop.png")
    print("saved after_tab.png target_frame_crop.png")


def pyautogui_press_target():
    import pyautogui

    pyautogui.press("tab")


if __name__ == "__main__":
    main()
