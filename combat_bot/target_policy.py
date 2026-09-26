"""Deterministic target filtering.

The policy is intentionally deny-by-default. A blank or unknown name never
becomes an attack target merely because it looks hostile on screen.
"""

from __future__ import annotations

from .models import TargetDecision, TargetInfo, TargetPolicyConfig


def _normalize(value: str) -> str:
    return " ".join(value.casefold().split())


class TargetPolicy:
    def __init__(self, config: TargetPolicyConfig | None = None):
        self.config = config or TargetPolicyConfig()
        self.allowed_names = {_normalize(name) for name in self.config.allowed_names}
        self.blocked_names = {_normalize(name) for name in self.config.blocked_names}

    def check(self, target: TargetInfo) -> TargetDecision:
        if target.is_player:
            return TargetDecision(False, "player_target_forbidden")
        if target.is_elite and not self.config.allow_elite:
            return TargetDecision(False, "elite_target_forbidden")
        if target.is_rare and not self.config.allow_rare:
            return TargetDecision(False, "rare_target_forbidden")
        if not target.name or not _normalize(target.name):
            if self.config.allow_unknown:
                return TargetDecision(True, "unknown_target_allowed_by_config")
            return TargetDecision(False, "target_name_unknown")
        if _normalize(target.name) in self.blocked_names:
            return TargetDecision(False, "target_blocked")
        if not self.allowed_names:
            return TargetDecision(False, "target_not_in_allowlist")
        if _normalize(target.name) not in self.allowed_names:
            return TargetDecision(False, "target_not_in_allowlist")
        if self.config.allowed_levels and target.level not in self.config.allowed_levels:
            return TargetDecision(False, "target_level_not_allowed")
        return TargetDecision(True, "allowlisted")
