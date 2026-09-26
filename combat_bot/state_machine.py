"""Finite-state combat controller.

This layer never chooses whom to attack. It receives a normalized observation,
applies the deterministic safety policy, and emits exactly one small action.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from time import monotonic
from typing import Optional

from .models import Action, CombatRules, Observation
from .target_policy import TargetPolicy


@dataclass(frozen=True)
class StateResult:
    state: str
    action: Action


class CombatStateMachine:
    STATES = {
        "IDLE",
        "SEARCHING",
        "APPROACHING",
        "FIGHTING",
        "HEALING",
        "RETREATING",
        "BLOCKED",
    }

    def __init__(
        self,
        policy: TargetPolicy,
        rules: CombatRules | None = None,
        random_interval=None,
    ):
        self.policy = policy
        self.rules = rules or CombatRules()
        self._random_interval = (
            random_interval
            or self.rules.random_interval
            or self._default_random_interval
        )
        self._last_approved_target: Optional[str] = None
        self._next_turn_at: Optional[float] = None
        self._search_started = False
        self._awaiting_scan = False
        self._target_attack_count = 0
        self._last_opening_attack_at: Optional[float] = None
        self._next_melee_attack_at: Optional[float] = None
        self._repeat_attack_started = False
        self._last_attack_at: Optional[float] = None
        self._last_target_health: Optional[float] = None
        self._attack_was_issued = False
        self._missing_hits = 0
        self._out_of_range: Optional[bool] = None

    @staticmethod
    def _default_random_interval(low: float, high: float) -> float:
        return random.uniform(low, high)

    def reset_target(self) -> None:
        self._last_approved_target = None
        self._target_attack_count = 0
        self._last_opening_attack_at = None
        self._next_melee_attack_at = None
        self._repeat_attack_started = False
        self._last_target_health = None
        self._attack_was_issued = False
        self._missing_hits = 0
        self._out_of_range = None

    def step(self, observation: Observation, now: Optional[float] = None) -> StateResult:
        """Apply one observation at a logical time and return one action.

        ``now`` is injectable so timers can be tested without sleeping. The
        continuous runtime passes ``time.monotonic()`` from the main loop.
        """
        if now is None:
            now = monotonic()
        target = observation.target

        if not target.exists:
            self.reset_target()
            return self._search_step(now, "no_target")

        decision = self.policy.check(target)
        if not decision.allowed:
            self.reset_target()
            return self._search_step(
                now,
                f"target_blocked:{decision.reason}",
            )

        if target.name != self._last_approved_target:
            self._begin_target(target.name)

        if (
            observation.player_health_percent is not None
            and observation.player_health_percent <= self.rules.retreat_threshold
        ):
            if self.rules.retreat_key:
                return StateResult(
                    "RETREATING",
                    Action.press(
                        self.rules.retreat_key,
                        "critical_health",
                        hold_seconds=0.3,
                    ),
                )
            return StateResult(
                "RETREATING",
                Action.wait("critical_health_retreat_key_unset"),
            )

        if (
            observation.player_health_percent is not None
            and observation.player_health_percent <= self.rules.heal_threshold
            and self.rules.heal_slot is not None
        ):
            return StateResult(
                "HEALING",
                Action.press(str(self.rules.heal_slot), "health_at_or_below_heal_threshold"),
            )

        # Attacking auto-faces the target, so the bot always attacks first.
        # A red slot digit alone is not a reason to walk: it also appears when
        # the target is too close, and walking would not help.
        if self._last_target_health is not None and observation.target.health_percent is not None:
            damage = self._last_target_health - observation.target.health_percent
            if damage >= 0.5:
                self._missing_hits = 0
            elif self._attack_was_issued and self._attack_settled(now):
                # Health is still untouched, and the last attack had time to
                # land, so the target really is out of reach.
                self._missing_hits += 1
        self._last_target_health = observation.target.health_percent

        # Attacks that land nothing mean the target is out of reach: move in.
        if self._missing_hits >= self.rules.max_attacks_before_closing:
            if self.rules.approach_key:
                return StateResult(
                    "APPROACHING",
                    Action.press(
                        self.rules.approach_key,
                        "attacks_landing_nothing_closing_distance",
                        hold_seconds=0.5,
                    ),
                )
            return StateResult(
                "APPROACHING",
                Action.wait("attacks_missed_approach_key_unset"),
            )

        attack = self._attack_rotation(observation, now)
        if attack.action.kind == "press_key":
            self._attack_was_issued = True
        return attack

    def _begin_target(self, name: Optional[str]) -> None:
        self._last_approved_target = name
        self._target_attack_count = 0
        self._last_opening_attack_at = None
        self._next_melee_attack_at = None
        self._repeat_attack_started = False
        self._last_target_health = None
        self._attack_was_issued = False
        self._missing_hits = 0
        self._out_of_range = None

    def _melee_attack(self, now: float) -> StateResult:
        """Repeat the attack slot at a randomized interval."""
        rules = self.rules
        slot = rules.melee_attack_slot or rules.opening_attack_slot
        if slot is None:
            return StateResult("FIGHTING", Action.wait("no_attack_slot_configured"))
        if not self._repeat_attack_started:
            # The first follow-up attack should land immediately after the
            # opening sequence instead of burning one extra interval.
            self._repeat_attack_started = True
            self._next_melee_attack_at = now
        elif self._next_melee_attack_at is None:
            self._next_melee_attack_at = now + self._random_interval(
                rules.melee_attack_interval_min_seconds,
                rules.melee_attack_interval_max_seconds,
            )
        if now >= self._next_melee_attack_at:
            self._next_melee_attack_at = now + self._random_interval(
                rules.melee_attack_interval_min_seconds,
                rules.melee_attack_interval_max_seconds,
            )
            self._last_attack_at = now
            return StateResult(
                "FIGHTING",
                Action.press(str(slot), "attack"),
            )
        return StateResult("FIGHTING", Action.wait("attack_cooldown"))

    def _attack_settled(self, now: float) -> bool:
        """True once enough time passed for the last attack to have landed."""
        if self._last_attack_at is None:
            return False
        return (now - self._last_attack_at) >= self.rules.attack_settle_seconds

    def _attack_rotation(self, observation: Observation, now: float) -> StateResult:
        rules = self.rules

        # The opening sequence runs once per approved target.
        if (
            rules.opening_attack_slot is not None
            and self._target_attack_count < rules.opening_attack_count
        ):
            opening_ready = (
                self._last_opening_attack_at is None
                or now - self._last_opening_attack_at
                >= rules.opening_attack_interval_seconds
            )
            if not opening_ready:
                return StateResult("FIGHTING", Action.wait("opening_attack_cooldown"))
            self._target_attack_count += 1
            self._last_opening_attack_at = now
            self._last_attack_at = now
            return StateResult(
                "FIGHTING",
                Action.press(str(rules.opening_attack_slot), "opening_attack"),
            )

        return self._melee_attack(now)

    def _search_step(self, now: float, reason: str) -> StateResult:
        """Circle the spawn area, scanning with ``Tab`` after each quarter turn.

        ``Tab`` only selects targets in front of the character, so sweeping the
        camera is what exposes new ones. Holding forward while turning keeps
        the character orbiting its spawn point instead of wandering away, and
        the strict sweep-then-scan alternation guarantees the new facing angle
        is actually checked for targets.
        """
        rules = self.rules
        has_turn_key = bool(rules.turn_left_key or rules.turn_right_key)
        turn_ready = self._next_turn_at is None or now >= self._next_turn_at

        if not has_turn_key:
            return StateResult(
                "SEARCHING",
                Action.press(rules.target_key, reason),
            )

        # A sweep just completed: scan the new angle before turning again.
        if self._awaiting_scan:
            self._awaiting_scan = False
            return StateResult(
                "SEARCHING",
                Action.press(rules.target_key, reason),
            )

        if not turn_ready:
            return StateResult("SEARCHING", Action.wait("sweep_cooldown"))

        # One fixed direction circles the spawn point; alternating left/right
        # would zigzag outward instead.
        key = rules.turn_right_key or rules.turn_left_key
        keys = tuple(item for item in (rules.approach_key, key) if item)

        self._search_started = True
        self._awaiting_scan = True
        self._next_turn_at = now + max(0.0, rules.turn_hold_seconds)

        return StateResult(
            "SEARCHING",
            Action.hold(
                keys,
                "sweep_spawn_area",
                hold_seconds=rules.turn_hold_seconds,
            ),
        )
