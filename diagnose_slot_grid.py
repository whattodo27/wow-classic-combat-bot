"""Auto-calibrate the action-bar slot grid by finding vertical borders."""
from __future__ import annotations

from collections import Counter
from pathlib import Path

from PIL import Image

from combat_bot.capture import WindowCapture
from combat_bot.config import load_config


def border_columns(image: Image.Image, top: int, bottom: int, threshold=105):
    """Columns that look like a slot border: bright over most of the row height."""
    pixels = image.load()
    width = image.size[0]
    height = max(1, bottom - top)
    scores = []
    for x in range(width):
        bright = 0
        for y in range(top, bottom):
            red, green, blue = pixels[x, y]
            if red > threshold and green > threshold and blue > threshold * 0.9:
                bright += 1
        scores.append(bright / height)
    return scores


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

    # Try several candidate strips; the bar row is near the bottom.
    for top_ratio in (0.90, 0.92, 0.94, 0.955):
        top = int(height * top_ratio)
        bottom = height
        scores = border_columns(image, top, bottom)
        candidates = [x for x, score in enumerate(scores) if score > 0.5]
        groups = []
        if candidates:
            start = previous = candidates[0]
            for x in candidates[1:]:
                if x == previous + 1:
                    previous = x
                    continue
                groups.append((start, previous))
                start = previous = x
            groups.append((start, previous))
        centers = [(a + b) // 2 for a, b in groups]
        spacings = [b - a for a, b in zip(centers, centers[1:]) if b - a > 5]
        modal = Counter(spacings).most_common(3)
        print(
            f"top_ratio={top_ratio} groups={len(groups)} "
            f"modal_spacing={modal}"
        )
        if len(groups) >= 4 and modal:
            step = modal[0][0]
            first = centers[0]
            print(
                f"  -> first_border_x={first} step={step} "
                f"left={first - step / 2:.0f} right={first + step / 2:.0f}"
            )
            print(
                f"  ratios: left={(first - step / 2) / width:.5f} "
                f"right={(first + step / 2) / width:.5f} "
                f"top={top / height:.5f} bottom=1.0"
            )
            break


if __name__ == "__main__":
    main()
