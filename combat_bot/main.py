"""Command-line entry point for the combat prototype."""

from __future__ import annotations

import argparse
import time
from pathlib import Path
from time import monotonic

from PIL import Image

from .capture import WindowCapture
from .shutdown import (
    clear_stop_file,
    install_stop_handlers,
    panic_key_pressed,
    release_all_keys,
    stop_file_path,
    stop_requested,
)
from .config import load_config
from .executor import ActionExecutor
from .layout import UiLayout
from .models import Observation
from .name_matcher import NameMatcher
from .pixel_sensor import PixelSensor
from .response_parser import parse_observation
from .state_machine import CombatStateMachine
from .target_policy import TargetPolicy
from .vision import VisionClient


def build_sensor(config):
    """Pixel sensor with registered name templates when available."""
    root = Path(__file__).resolve().parents[1]
    layout = UiLayout()
    matcher = NameMatcher()
    matcher.register_from_dir(root / "templates")
    return PixelSensor(layout, matcher), matcher



def run(config_path: Path) -> int:
    config = load_config(config_path)
    capture = WindowCapture(
        config.window_title,
        max_size=config.max_image_size,
        quality=config.image_quality,
    )
    executor = ActionExecutor(
        live_input=config.live_input,
        live_targeting=config.rules.live_targeting,
        target_key=config.rules.target_key,
        focus_callback=capture.focus,
    )
    policy = TargetPolicy(config.target_policy)
    machine = CombatStateMachine(policy, config.rules)

    sensor, matcher = build_sensor(config)
    vision = None
    if config.observation_source == "vision":
        vision = VisionClient(
            config.ollama_model,
            config.ollama_base_url,
            config.request_timeout,
        )

    mode = "LIVE INPUT" if config.live_input else "DRY-RUN (targeting enabled)"
    print(f"Mode: {mode}")
    print(f"Looking for window: {config.window_title!r}")
    print(f"Observation source: {config.observation_source}")
    print(f"Name templates: {len(matcher.templates)}")
    if not config.target_policy.allowed_names:
        print("WARNING: no safe targets configured - the bot will not attack.")
        print("         Add one with: python targets.py add \"Young Thistle Boar\"")
    print("Stop: Ctrl+C in this terminal, F12, or `touch bot.stop`.")
    print(f"Panic key: F12 (or create {stop_file_path().name})")

    install_stop_handlers()
    clear_stop_file()

    while True:
        if stop_requested() or panic_key_pressed():
            release_all_keys()
            print("\nStopped (stop file or F12).")
            return 0
        try:
            image = capture.capture_image()
            if image is None:
                print("WAIT: game window not found; no input sent.")
                time.sleep(config.loop_delay)
                continue

            observation: Observation
            if config.observation_source == "vision" and vision is not None:
                encoded = capture.encode(image)
                observation = parse_observation(vision.describe(encoded))
                if observation is None:
                    print("WAIT: unreadable vision response; no input sent.")
                    time.sleep(config.loop_delay)
                    continue
            else:
                observation = sensor.observe(image)

            result = machine.step(observation, now=monotonic())
            execution = executor.execute(result.action)
            target = observation.target
            print(
                f"{result.state:<10} name={target.name!r} "
                f"target_health={target.health_percent} "
                f"player_health={observation.player_health_percent} "
                f"out_of_range={observation.slot_out_of_range} "
                f"action={execution}",
                flush=True,
            )
            time.sleep(config.loop_delay)
        except KeyboardInterrupt:
            release_all_keys()
            print("\nStopped.")
            return 0
        except Exception as exc:
            print(f"ERROR: {type(exc).__name__}: {exc}; no input sent this cycle.")
            time.sleep(config.loop_delay)


def main() -> int:
    parser = argparse.ArgumentParser(description="Radius-combat prototype")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "combat_config.json",
    )
    args = parser.parse_args()
    return run(args.config)


if __name__ == "__main__":
    raise SystemExit(main())
