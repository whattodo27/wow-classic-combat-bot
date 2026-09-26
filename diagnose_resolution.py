"""Compare vision reads at different capture resolutions (diagnostic only)."""
from __future__ import annotations

import base64
from io import BytesIO
from pathlib import Path

import mss
from PIL import Image

from combat_bot.capture import find_window_by_title
from combat_bot.config import load_config
from combat_bot.vision import VisionClient


def capture_at(rect, max_size, quality=60):
    with mss.mss() as sct:
        shot = sct.grab(
            {
                "left": rect.left,
                "top": rect.top,
                "width": rect.width,
                "height": rect.height,
            }
        )
    image = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")
    if max_size:
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=quality)
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def main() -> None:
    config = load_config(Path(__file__).parent / "combat_config.json")
    rect = find_window_by_title(config.window_title)
    if rect is None:
        print("window not found")
        return
    client = VisionClient(
        config.ollama_model,
        config.ollama_base_url,
        config.request_timeout,
    )

    for label, size in (
        ("full-res", None),
        ("800x600", (800, 600)),
        ("1200x900", (1200, 900)),
    ):
        image = capture_at(rect, size, config.image_quality)
        response = client.describe(image)
        print(f"=== {label} ===")
        print(response.strip()[:600])
        print()


if __name__ == "__main__":
    main()
