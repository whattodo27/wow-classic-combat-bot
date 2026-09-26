"""Learn target distance from observed combat feedback.

Instead of guessing range from the creature's on-screen size, the bot can
probe: attack once, then see whether the target's health actually started
dropping. Losing no health after a successful cast means the target was out of
range, so the character must close the distance.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class RangeVerdict(str, Enum):
    IN_RANGE = "in_range"
    OUT_OF_RANGE = "out_of_range"
    UNKNOWN = "unknown"


@dataclass
class RangeTracker:
    """Decides whether the last attack attempt connected."""

    def __init__(self, epsilon: float = 0.8):
        self.epsilon = epsilon
        self.last_health: Optional[float] = None
        self.attack_issued = False
        self.in_range = False
        self.checked = False

    def note_attack(self) -> None:
        self.attack_issued = True
        self.checked = False
        self.in_range = False

    def observe_health(self, health: Optional[float]) -> RangeVerdict:
        if health is None:
            return RangeVerdict.UNKNOWN
        if not self.attack_issued:
            self.last_health = health
            return RangeVerdict.UNKNOWN
        if not self.checked:
            previous = self.last_health
            self.last_health = health
            self.checked = True
            if previous is None:
                return RangeVerdict.UNKNOWN
            # Health dropping means the swing/spell actually reached the target.
            self.in_range = previous - health >= self.epsilon
            return (
                RangeVerdict.IN_RANGE if self.in_range else RangeVerdict.OUT_OF_RANGE
            )
        self.last_health = health
        return RangeVerdict.IN_RANGE if self.in_range else RangeVerdict.OUT_OF_RANGE
