import unittest

from combat_bot.models import CombatRules, Observation, TargetInfo
from combat_bot.state_machine import CombatStateMachine
from combat_bot.target_policy import TargetPolicy
from combat_bot.models import TargetPolicyConfig


class StateMachineIntegrationTests(unittest.TestCase):
    def test_search_uses_configured_target_key(self):
        machine = CombatStateMachine(
            TargetPolicy(TargetPolicyConfig()),
            CombatRules(target_key="f1"),
        )

        result = machine.step(Observation(target=TargetInfo(exists=False)))

        self.assertEqual(result.action.key, "f1")

    def test_unknown_target_is_blocked_even_when_it_looks_alive(self):
        machine = CombatStateMachine(
            TargetPolicy(TargetPolicyConfig(allowed_names=("Kobold Vermin",))),
            CombatRules(attack_slots={1: 1}),
        )

        result = machine.step(
            Observation(
                target=TargetInfo(
                    name="Kobold Laborer",
                    exists=True,
                    health_percent=80,
                ),
                player_health_percent=90,
                target_distance="near",
            )
        )

        self.assertEqual(result.state, "SEARCHING")
        self.assertEqual(result.action.kind, "press_key")
        self.assertEqual(result.action.key, "tab")
        self.assertIn("target_not_in_allowlist", result.action.reason)


if __name__ == "__main__":
    unittest.main()
