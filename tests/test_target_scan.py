import unittest

from combat_bot.models import CombatRules, Observation, TargetInfo, TargetPolicyConfig
from combat_bot.state_machine import CombatStateMachine
from combat_bot.target_policy import TargetPolicy


class TargetScanTests(unittest.TestCase):
    def make_machine(self):
        return CombatStateMachine(
            TargetPolicy(TargetPolicyConfig(allowed_names=("Young Nightsaber",))),
            CombatRules(
                target_key="tab",
                turn_left_key=None,
                turn_right_key="d",
                turn_hold_seconds=0.75,
                approach_key="w",
            ),
        )

    def test_no_target_starts_with_a_sweep_not_a_scan(self):
        machine = self.make_machine()

        result = machine.step(Observation(target=TargetInfo(exists=False)), now=0.0)

        self.assertEqual(result.state, "SEARCHING")
        self.assertEqual(result.action.kind, "hold_keys")
        self.assertEqual(set(result.action.keys), {"w", "d"})

    def test_scan_presses_tab_with_no_turn_keys(self):
        machine = CombatStateMachine(
            TargetPolicy(TargetPolicyConfig(allowed_names=("Young Nightsaber",))),
            CombatRules(
                target_key="tab",
                turn_left_key=None,
                turn_right_key=None,
            ),
        )

        first = machine.step(Observation(target=TargetInfo(exists=False)), now=0.0)
        second = machine.step(Observation(target=TargetInfo(exists=False)), now=0.5)

        self.assertEqual(first.action.key, "tab")
        self.assertEqual(second.action.key, "tab")

    def test_unknown_target_is_rescanned_instead_of_being_attacked(self):
        machine = CombatStateMachine(
            TargetPolicy(TargetPolicyConfig(allowed_names=("Young Nightsaber",))),
            CombatRules(
                target_key="tab",
                turn_left_key=None,
                turn_right_key=None,
                attack_slots={1: 1},
            ),
        )

        result = machine.step(
            Observation(target=TargetInfo(name="Kobold Laborer", exists=True)),
            now=0.0,
        )

        self.assertEqual(result.state, "SEARCHING")
        self.assertEqual(result.action.key, "tab")
        self.assertIn("target_not_in_allowlist", result.action.reason)

    def test_approved_target_stops_sweeping_and_scanning(self):
        machine = self.make_machine()
        machine.step(Observation(target=TargetInfo(exists=False)), now=0.0)

        result = machine.step(
            Observation(
                target=TargetInfo(name="Young Nightsaber", exists=True),
                target_distance="near",
            ),
            now=0.1,
        )

        self.assertNotEqual(result.action.kind, "hold_keys")
        self.assertNotEqual(result.action.key, "tab")
        self.assertEqual(result.state, "FIGHTING")


if __name__ == "__main__":
    unittest.main()
