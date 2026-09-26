import unittest

from combat_bot.models import CombatRules, Observation, TargetInfo, TargetPolicyConfig
from combat_bot.state_machine import CombatStateMachine
from combat_bot.target_policy import TargetPolicy


class CombatStateMachineTests(unittest.TestCase):
    def make_machine(self, allowlist=("Kobold Vermin",), rules=None):
        policy = TargetPolicy(
            TargetPolicyConfig(allowed_names=allowlist)
        )
        return CombatStateMachine(policy, rules or CombatRules())

    def test_searches_for_a_target_when_none_exists(self):
        machine = self.make_machine()

        result = machine.step(Observation(target=TargetInfo(exists=False)))

        self.assertEqual(result.action.kind, "press_key")
        self.assertEqual(result.action.key, "tab")
        self.assertEqual(result.state, "SEARCHING")

    def test_blocks_unknown_or_forbidden_target(self):
        machine = self.make_machine()

        result = machine.step(
            Observation(target=TargetInfo(name="Kobold Laborer", exists=True))
        )

        self.assertEqual(result.action.kind, "press_key")
        self.assertEqual(result.action.key, "tab")
        self.assertEqual(result.state, "SEARCHING")

    def test_does_not_reselect_while_approved_target_is_alive(self):
        machine = self.make_machine()

        result = machine.step(
            Observation(
                target=TargetInfo(name="Kobold Vermin", exists=True),
                player_health_percent=90,
                player_mana_percent=70,
                target_distance="near",
                facing_target=True,
            )
        )

        self.assertNotEqual(result.action.kind, "press_key")
        self.assertNotEqual(result.action.key, "tab")
        self.assertEqual(result.state, "FIGHTING")

    def test_empty_attack_slots_never_press_attack_keys(self):
        machine = self.make_machine(
            rules=CombatRules(attack_slots={1: None, 2: None, 3: None})
        )

        result = machine.step(
            Observation(
                target=TargetInfo(name="Kobold Vermin", exists=True),
                player_health_percent=90,
                player_mana_percent=70,
                target_distance="near",
                facing_target=True,
            )
        )

        self.assertEqual(result.action.kind, "wait")
        self.assertIsNone(result.action.key)

    def test_heal_slot_has_priority_over_attack_when_configured(self):
        machine = self.make_machine(
            rules=CombatRules(heal_slot=3, heal_threshold=40, attack_slots={1: None})
        )

        result = machine.step(
            Observation(
                target=TargetInfo(name="Kobold Vermin", exists=True),
                player_health_percent=30,
                player_mana_percent=70,
                target_distance="near",
                facing_target=True,
            )
        )

        self.assertEqual(result.action.kind, "press_key")
        self.assertEqual(result.action.key, "3")
        self.assertEqual(result.state, "HEALING")

    def test_attacking_faces_the_target_so_it_never_just_walks(self):
        machine = self.make_machine()
        result = machine.step(
            Observation(
                target=TargetInfo(
                    name="Kobold Vermin",
                    exists=True,
                    health_percent=80.0,
                ),
                player_health_percent=90.0,
                slot_out_of_range=True,
            ),
            now=0.0,
        )

        self.assertEqual(result.state, "FIGHTING")
        self.assertNotEqual(result.action.kind, "hold_keys")

    def test_dead_target_returns_to_search(self):
        machine = self.make_machine()

        result = machine.step(
            Observation(target=TargetInfo(name="Kobold Vermin", exists=False))
        )

        self.assertEqual(result.state, "SEARCHING")
        self.assertEqual(result.action.key, "tab")


if __name__ == "__main__":
    unittest.main()
