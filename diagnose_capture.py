"""One-shot diagnostics: capture the configured game window and print raw vision JSON."""
from __future__ import annotations

import base64
from pathlib import Path

from combat_bot.capture import WindowCapture
from combat_bot.config import load_config
from combat_bot.vision import VisionClient


def main() -> None:
    config = load_config(Path(__file__).parent / "combat_config.json")
    capture = WindowCapture(
        config.window_title,
        max_size=config.max_image_size,
        quality=config.image_quality,
    )
    rect = capture.find_window()
    print(f"window={rect}")
    image = capture.capture()
    if image is None:
        print("capture=None")
        return
    Path("diagnostic_window.jpg").write_bytes(base64.b64decode(image))
    print("saved=diagnostic_window.jpg")
    client = VisionClient(
        config.ollama_model,
        config.ollama_base_url,
        config.request_timeout,
    )
    response = client.describe(image)
    print("raw_response:")
    print(response)


if __name__ == "__main__":
    main()
