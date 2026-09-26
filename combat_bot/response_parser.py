"""Extract one complete JSON observation from a vision-model response.

The old bot appended a closing brace to truncated output. That can turn an
incomplete answer into a confidently wrong object, so this parser returns
``None`` and the agent waits instead.
"""

from __future__ import annotations

import json
from typing import Any, Optional

from .models import Observation, TargetInfo


def _balanced_json_candidates(text: str):
    """Yield complete top-level JSON object candidates from noisy text."""
    start = None
    depth = 0
    in_string = False
    escaped = False
    for index, char in enumerate(text):
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
            continue
        if char == "{":
            if depth == 0:
                start = index
            depth += 1
        elif char == "}" and depth:
            depth -= 1
            if depth == 0 and start is not None:
                yield text[start : index + 1]
                start = None


def _first_object(text: str) -> Optional[dict[str, Any]]:
    for candidate in _balanced_json_candidates(text):
        try:
            value = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    return None


def _bool(value: Any, default: Optional[bool] = None) -> Optional[bool]:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        normalized = value.casefold().strip()
        if normalized in {"true", "yes", "1", "present", "visible", "alive"}:
            return True
        if normalized in {"false", "no", "0", "absent", "hidden", "dead", "none"}:
            return False
    return default


def _percent(value: Any) -> Optional[float]:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        number = float(value)
    elif isinstance(value, str):
        try:
            number = float(value.strip().rstrip("%"))
        except ValueError:
            return None
    else:
        return None
    return max(0.0, min(100.0, number))


def _distance(value: Any) -> Optional[str]:
    if not isinstance(value, str):
        return None
    normalized = value.casefold().strip()
    if normalized in {"near", "close", "in_range", "melee", "in melee range"}:
        return "near"
    if normalized in {"far", "distant", "out_of_range", "out of range", "ranged"}:
        return "far"
    return normalized or None


def parse_observation(response_text: str) -> Optional[Observation]:
    payload = _first_object(response_text or "")
    if payload is None:
        return None

    target_payload = payload.get("target")
    if not isinstance(target_payload, dict):
        target_payload = {}

    target_health = _percent(
        target_payload.get("health_percent", target_payload.get("health"))
    )
    target_exists = _bool(
        target_payload.get("exists", target_payload.get("present")),
        default=None,
    )
    if target_exists is None:
        target_exists = bool(target_health is not None and target_health > 0)

    target_name = target_payload.get("name")
    if not isinstance(target_name, str) or not target_name.strip():
        target_name = None

    target_level = target_payload.get("level")
    if isinstance(target_level, str):
        digits = "".join(character for character in target_level if character.isdigit())
        target_level = int(digits) if digits else None
    elif isinstance(target_level, bool):
        target_level = None
    elif isinstance(target_level, (int, float)):
        target_level = int(target_level)
    else:
        target_level = None

    target = TargetInfo(
        name=target_name,
        exists=bool(target_exists),
        is_player=bool(_bool(target_payload.get("is_player", target_payload.get("player")), False)),
        is_elite=bool(_bool(target_payload.get("is_elite", target_payload.get("elite")), False)),
        is_rare=bool(_bool(target_payload.get("is_rare", target_payload.get("rare")), False)),
        health_percent=target_health,
        level=target_level,
        distance=_distance(target_payload.get("distance")),
    )

    pet_health = _percent(payload.get("pet_health_percent", payload.get("pet_health")))
    return Observation(
        target=target,
        player_health_percent=_percent(
            payload.get("player_health_percent", payload.get("health_percent"))
        ),
        player_mana_percent=_percent(
            payload.get("player_mana_percent", payload.get("mana_percent"))
        ),
        pet_health_percent=pet_health,
        pet_alive=_bool(payload.get("pet_alive")),
        target_distance=_distance(payload.get("target_distance", target.distance)),
        facing_target=_bool(payload.get("facing_target", payload.get("facing"))),
        in_combat=_bool(payload.get("in_combat")),
    )
