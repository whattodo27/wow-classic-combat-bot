"""Read the live window and report detected name via templates (diagnostic)."""
from __future__ import annotations

import time
from pathlib import Path

from combat_bot.capture import WindowCapture
from combat_bot.config import load_config
from combat_bot.layout import UiLayout
from combat_bot.name_matcher import NameMatcher
from combat_bot.pixel_sensor import PixelSensor


def main() -> None:
    root = Path(__file__).parent
    config = load_config(root / "combat_config.json")
    matcher = NameMatcher()
    print(f"templates loaded: {matcher.register_from_dir(root / 'templates')}")
    sensor = PixelSensor(UiLayout(), matcher)
    capture = WindowCapture(config.window_title)
    capture.focus()
    time.sleep(1.0)

    for index in range(6):
        image = capture.capture_image()
        if image is None:
            print("window not found")
            return
        observation = sensor.observe(image)
        target = observation.target
        print(
            f"[{index}] exists={target.exists} name={target.name!r} "
            f"target_health={target.health_percent} "
            f"player_health={observation.player_health_percent}"
        )
        time.sleep(1.0)


if __name__ == "__main__":
    main()
