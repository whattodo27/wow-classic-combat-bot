"""Small immutable data objects shared by the combat pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Literal, Mapping, Optional


@dataclass(frozen=True)
class TargetInfo:
    """Information the vision layer can safely provide about a target."""

    name: Optional[str] = None
    exists: bool = False
    is_player: bool = False
    is_elite: bool = False
    is_rare: bool = False
    health_percent: Optional[float] = None
    level: Optional[int] = None
    distance: Optional[str] = None


@dataclass(frozen=True)
class TargetPolicyConfig:
    """Allow/deny rules. An empty allowlist intentionally denies all targets."""

    allowed_names: tuple[str, ...] = ()
    blocked_names: tuple[str, ...] = ()
    allowed_levels: tuple[int, ...] = ()
    allow_unknown: bool = False
    allow_elite: bool = False
    allow_rare: bool = False


@dataclass(frozen=True)
class TargetDecision:
    allowed: bool
    reason: str


@dataclass(frozen=True)
class Observation:
    """Normalized game observation; None means unreadable, never guessed."""

    target: TargetInfo = field(default_factory=TargetInfo)
    player_health_percent: Optional[float] = None
    player_mana_percent: Optional[float] = None
    pet_health_percent: Optional[float] = None
    pet_alive: Optional[bool] = None
    target_distance: Optional[str] = None
    slot_out_of_range: Optional[bool] = None
    facing_target: Optional[bool] = None
    in_combat: Optional[bool] = None


ActionKind = Literal["wait", "press_key", "hold_keys"]


@dataclass(frozen=True)
class Action:
    """A planned action. Live input is only one possible executor."""

    kind: ActionKind = "wait"
    key: Optional[str] = None
    keys: tuple[str, ...] = ()
    hold_seconds: Optional[float] = None
    reason: str = ""

    @classmethod
    def wait(cls, reason: str) -> "Action":
        return cls(kind="wait", reason=reason)

    @classmethod
    def press(cls, key: str, reason: str, hold_seconds: Optional[float] = None) -> "Action":
        return cls(kind="press_key", key=key, hold_seconds=hold_seconds, reason=reason)

    @classmethod
    def hold(
        cls,
        keys: tuple[str, ...],
        reason: str,
        hold_seconds: float,
    ) -> "Action":
        return cls(
            kind="hold_keys",
            keys=tuple(keys),
            hold_seconds=hold_seconds,
            reason=reason,
        )



@dataclass(frozen=True)
class CombatRules:
    """Configurable combat behavior. Unset abilities are deliberately inert."""

    target_key: str = "tab"
    live_targeting: bool = True
    turn_left_key: Optional[str] = None
    turn_right_key: Optional[str] = None
    turn_hold_seconds: float = 0.75
    approach_key: Optional[str] = "w"
    retreat_key: Optional[str] = "s"
    face_target_key: Optional[str] = None
    heal_slot: Optional[int] = None
    pet_slot: Optional[int] = None
    opening_attack_slot: Optional[int] = None
    opening_attack_count: int = 0
    opening_attack_interval_seconds: float = 2.0
    melee_attack_slot: Optional[int] = None
    melee_attack_interval_min_seconds: float = 1.0
    melee_attack_interval_max_seconds: float = 1.3
    max_attacks_before_closing: int = 2
    attack_settle_seconds: float = 1.5
    random_interval: Optional[Callable[[float, float], float]] = None
    heal_threshold: int = 40
    retreat_threshold: int = 25
    pet_health_threshold: int = 40
    attack_slots: Mapping[int, Optional[int]] = field(
        default_factory=lambda: {index: None for index in range(1, 10)}
    )
    attack_cooldowns: Mapping[int, float] = field(default_factory=dict)

    def normalized_attack_slots(self) -> dict[int, Optional[int]]:
        return {
            int(slot): (None if value is None else int(value))
            for slot, value in self.attack_slots.items()
        }
