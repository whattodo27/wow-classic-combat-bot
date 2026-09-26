"""One-shot, guarded live-input probe for a known allowlisted target.

This script is intentionally not the continuous bot. It focuses the named
window, presses the target key once, captures the resulting target frame, and
only presses the configured attack slot when the vision response exactly
matches the configured allowlist. It stops immediately after one decision.
"""
from __future__ import annotations

import time
from pathlib import Path

import pyautogui

from combat_bot.capture import WindowCapture
from combat_bot.config import load_config
from combat_bot.response_parser import parse_observation
from combat_bot.target_policy import TargetPolicy
from combat_bot.vision import VisionClient


def main() -> int:
    config = load_config(Path(__file__).parent / "combat_config.json")
    capture = WindowCapture(
        config.window_title,
        max_size=config.max_image_size,
        quality=config.image_quality,
    )
    rect = capture.find_window()
    if rect is None:
        print("STOP: configured game window not found")
        return 1
    print(f"window={rect}")
    pyautogui.click(rect.left + rect.width // 2, rect.top + rect.height // 2)
    time.sleep(0.5)
    pyautogui.press(config.rules.target_key)
    time.sleep(0.5)
    image = capture.capture()
    if image is None:
        print("STOP: capture failed after target key")
        return 1
    response = VisionClient(
        config.ollama_model,
        config.ollama_base_url,
        config.request_timeout,
    ).describe(image)
    print("raw_response:")
    print(response)
    observation = parse_observation(response)
    if observation is None:
        print("STOP: unreadable response")
        return 1
    target = observation.target
    decision = TargetPolicy(config.target_policy).check(target)
    print(f"target={target.name!r} exists={target.exists} allowed={decision.allowed} reason={decision.reason}")
    if not target.exists or not decision.allowed:
        print("STOP: no confirmed Young Nightsaber; attack slot was not pressed")
        return 1
    if target.name != "Young Nightsaber":
        print("STOP: target name mismatch; attack slot was not pressed")
        return 1
    if not config.rules.attack_slots.get(1):
        print("STOP: attack slot 1 is not configured")
        return 1
    pyautogui.press(str(config.rules.attack_slots[1]))
    print("LIVE: pressed configured attack slot 1 once")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
