"""Load the prototype's JSON configuration with safe defaults."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional


@dataclass(frozen=True)
class BotConfig:
    window_title: str
    live_input: bool
    loop_delay: float
    request_timeout: int
    ollama_model: str
    ollama_base_url: str
    observation_source: str
    max_image_size: tuple[int, int]
    image_quality: int
    target_policy: Any
    rules: Any

    @property
    def attack_slots(self) -> dict[int, Optional[int]]:
        return self.rules.normalized_attack_slots()


def _tuple_strings(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(item.strip() for item in value if isinstance(item, str) and item.strip())


def _tuple_ints(value: Any) -> tuple[int, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(int(item) for item in value if isinstance(item, (int, float)) and not isinstance(item, bool))


def _int(value: Any, default: int) -> int:
    return int(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else default


def load_config(path: str | Path) -> BotConfig:
    path = Path(path)
    with path.open("r", encoding="utf-8") as stream:
        raw: Mapping[str, Any] = json.load(stream)

    window = raw.get("window", {})
    if not isinstance(window, Mapping):
        raise ValueError("window must be an object")
    title = window.get("title", "")
    if not isinstance(title, str):
        raise ValueError("window.title must be a string")
    live_input = bool(raw.get("live_input", False))
    if live_input and not title.strip():
        raise ValueError("live_input requires a non-empty window.title")

    target = raw.get("target_policy", {})
    rules = raw.get("combat_rules", {})
    if not isinstance(target, Mapping) or not isinstance(rules, Mapping):
        raise ValueError("target_policy and combat_rules must be objects")

    from .models import CombatRules, TargetPolicyConfig

    target_config = TargetPolicyConfig(
        allowed_names=_tuple_strings(target.get("allowed_names")),
        blocked_names=_tuple_strings(target.get("blocked_names")),
        allowed_levels=_tuple_ints(target.get("allowed_levels")),
        allow_unknown=bool(target.get("allow_unknown", False)),
        allow_elite=bool(target.get("allow_elite", False)),
        allow_rare=bool(target.get("allow_rare", False)),
    )

    attack_slots_raw = rules.get("attack_slots", {})
    attack_slots: dict[int, Optional[int]] = {}
    if isinstance(attack_slots_raw, Mapping):
        for slot, value in attack_slots_raw.items():
            number = int(slot)
            attack_slots[number] = None if value is None else int(value)
    for slot in range(1, 10):
        attack_slots.setdefault(slot, None)

    combat_rules = CombatRules(
        target_key=str(rules.get("target_key", "tab")),
        live_targeting=bool(rules.get("live_targeting", True)),
        turn_left_key=None if rules.get("turn_left_key") is None else str(rules["turn_left_key"]),
        turn_right_key=None if rules.get("turn_right_key") is None else str(rules["turn_right_key"]),
        turn_hold_seconds=float(rules.get("turn_hold_seconds", 0.75)),
        approach_key=None if rules.get("approach_key") is None else str(rules["approach_key"]),
        retreat_key=None if rules.get("retreat_key") is None else str(rules["retreat_key"]),
        face_target_key=None if rules.get("face_target_key") is None else str(rules["face_target_key"]),
        heal_slot=None if rules.get("heal_slot") is None else int(rules["heal_slot"]),
        pet_slot=None if rules.get("pet_slot") is None else int(rules["pet_slot"]),
        opening_attack_slot=None if rules.get("opening_attack_slot") is None else int(rules["opening_attack_slot"]),
        opening_attack_count=_int(rules.get("opening_attack_count"), 0),
        opening_attack_interval_seconds=float(rules.get("opening_attack_interval_seconds", 2.0)),
        melee_attack_slot=None if rules.get("melee_attack_slot") is None else int(rules["melee_attack_slot"]),
        melee_attack_interval_min_seconds=float(rules.get("melee_attack_interval_min_seconds", 1.0)),
        melee_attack_interval_max_seconds=float(rules.get("melee_attack_interval_max_seconds", 1.3)),
        max_attacks_before_closing=_int(rules.get("max_attacks_before_closing"), 2),
        attack_settle_seconds=float(rules.get("attack_settle_seconds", 1.5)),
        heal_threshold=_int(rules.get("heal_threshold"), 40),
        retreat_threshold=_int(rules.get("retreat_threshold"), 25),
        pet_health_threshold=_int(rules.get("pet_health_threshold"), 40),
        attack_slots=attack_slots,
    )

    capture = raw.get("capture", {})
    if not isinstance(capture, Mapping):
        raise ValueError("capture must be an object")
    ollama_model = str(raw.get("ollama_model", "llava:7b"))
    ollama_base_url = str(raw.get("ollama_base_url", "http://localhost:11434"))
    source = str(raw.get("observation_source", "pixels")).strip().casefold()
    if source not in {"pixels", "vision", "both"}:
        raise ValueError("observation_source must be pixels, vision, or both")
    size = capture.get("max_image_size", [400, 300])
    if not isinstance(size, list) or len(size) != 2:
        raise ValueError("capture.max_image_size must contain width and height")
    width = _int(size[0], 400)
    height = _int(size[1], 300)
    if width <= 0 or height <= 0:
        raise ValueError("capture.max_image_size values must be positive")

    return BotConfig(
        window_title=title,
        live_input=live_input,
        loop_delay=float(raw.get("loop_delay", 5.0)),
        request_timeout=_int(raw.get("request_timeout"), 60),
        ollama_model=ollama_model,
        ollama_base_url=ollama_base_url,
        observation_source=source,
        max_image_size=(width, height),
        image_quality=_int(capture.get("image_quality"), 60),
        target_policy=target_config,
        rules=combat_rules,
    )
