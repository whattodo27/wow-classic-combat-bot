import unittest

from combat_bot.models import CombatRules, Observation, TargetInfo, TargetPolicyConfig
from combat_bot.state_machine import CombatStateMachine
from combat_bot.target_policy import TargetPolicy


def machine(**overrides):
    settings = {
        "target_key": "tab",
        "turn_right_key": "d",
        "approach_key": "w",
        "opening_attack_slot": 1,
        "opening_attack_count": 1,
        "opening_attack_interval_seconds": 2.0,
        "melee_attack_slot": 2,
        "max_attacks_before_closing": 2,
    }
    settings.update(overrides)
    return CombatStateMachine(
        TargetPolicy(
            TargetPolicyConfig(
                allowed_names=("Young Nightsaber", "Young Thistle Boar")
            )
        ),
        CombatRules(**settings),
        random_interval=lambda low, high: 1.1,
    )


def observation(out_of_range=None, health=90.0):
    return Observation(
        target=TargetInfo(name="Young Nightsaber", exists=True, health_percent=health),
        slot_out_of_range=out_of_range,
    )


class AttackFirstTests(unittest.TestCase):
    def test_red_slot_still_attacks_instead_of_walking(self):
        result = machine().step(observation(out_of_range=True), now=0.0)

        self.assertEqual(result.state, "FIGHTING")
        self.assertEqual(result.action.key, "1")

    def test_no_signal_attacks(self):
        result = machine().step(observation(), now=0.0)

        self.assertEqual(result.state, "FIGHTING")
        self.assertEqual(result.action.key, "1")

    def test_never_holds_keys_with_a_target_selected(self):
        engine = machine()
        for index in range(6):
            result = engine.step(
                observation(health=90.0 if index % 2 else 88.0),
                now=float(index) * 2.0,
            )
            self.assertNotEqual(result.action.kind, "hold_keys")

    def test_never_presses_tab_with_a_target_selected(self):
        engine = machine()
        for index in range(4):
            result = engine.step(observation(), now=float(index) * 2.0)
            self.assertNotEqual(result.action.key, "tab")

    def test_missing_slot_signal_does_not_block_attacks(self):
        result = machine().step(observation(out_of_range=None), now=0.0)

        self.assertEqual(result.state, "FIGHTING")

    def test_approach_without_approach_key_waits(self):
        engine = machine(approach_key=None)
        engine.step(observation(), now=0.0)
        engine.step(observation(), now=2.0)

        result = engine.step(observation(), now=4.0)

        self.assertEqual(result.state, "APPROACHING")
        self.assertEqual(result.action.kind, "wait")


class RecoveryAfterTargetLostTests(unittest.TestCase):
    def test_sweep_resumes_when_target_disappears(self):
        engine = machine()
        engine.step(observation(), now=0.0)

        result = engine.step(Observation(target=TargetInfo(exists=False)), now=1.0)

        self.assertEqual(result.state, "SEARCHING")
        self.assertEqual(result.action.kind, "hold_keys")

    def test_new_target_forgets_previous_misses(self):
        engine = machine()
        engine.step(observation(), now=0.0)
        engine.step(observation(), now=1.0)
        engine.step(
            Observation(target=TargetInfo(name="Young Thistle Boar", exists=True)),
            now=2.0,
        )

        result = engine.step(
            Observation(
                target=TargetInfo(
                    name="Young Thistle Boar",
                    exists=True,
                    health_percent=70.0,
                )
            ),
            now=3.0,
        )

        self.assertNotEqual(result.state, "APPROACHING")


if __name__ == "__main__":
    unittest.main()
