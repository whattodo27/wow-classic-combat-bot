"""Find action-bar slot boundaries in the live window (diagnostic only)."""
from __future__ import annotations

from pathlib import Path

from combat_bot.capture import WindowCapture
from combat_bot.config import load_config


def main() -> None:
    root = Path(__file__).parent
    config = load_config(root / "combat_config.json")
    capture = WindowCapture(config.window_title)
    capture.focus()
    image = capture.capture_image()
    if image is None:
        print("window not found")
        return
    image.save(root / "live_frame.png")
    width, height = image.size
    print(f"frame={image.size}")

    # Slot borders are light vertical lines in the bottom strip.
    bar_top = int(height * 0.93)
    row_y = bar_top + int((height - bar_top) * 0.5)
    pixels = image.load()
    print(f"scanning row y={row_y}")

    bright = []
    for x in range(width):
        red, green, blue = pixels[x, row_y]
        if red > 110 and green > 105 and blue > 95:
            bright.append(x)

    # Group consecutive columns into slot separators.
    groups = []
    if bright:
        start = previous = bright[0]
        for x in bright[1:]:
            if x == previous + 1:
                previous = x
                continue
            groups.append((start, previous))
            start = previous = x
        groups.append((start, previous))

    print(f"bright column groups: {len(groups)}")
    for index, (start, end) in enumerate(groups[:30]):
        print(f"  {index:2d}: x={start}..{end}")

    if groups:
        slot_width = (groups[-1][0] - groups[0][0]) / max(1, len(groups) - 1)
        print(f"\nestimated slot width: {slot_width:.1f}")
        print(f"first slot x: {groups[0][0]}..{groups[0][1]}")
        print(f"last slot x: {groups[-1][0]}..{groups[-1][1]}")
        print(f"bar strip y: {bar_top}..{height}")
        print("\nratios for slot 1 (first two separators):")
        first = groups[0][0]
        second = groups[1][0] if len(groups) > 1 else groups[0][0] + int(slot_width)
        print(f"  left   {first / width:.5f}")
        print(f"  right  {second / width:.5f}")
        print(f"  top    {bar_top / height:.5f}")
        print(f"  bottom {height / height:.5f}")

    image.crop((0, bar_top, width, height)).resize(
        (width * 2, (height - bar_top) * 2)
    ).save(root / "crop_bar_zoom.png")
    print("saved crop_bar_zoom.png")


if __name__ == "__main__":
    main()
