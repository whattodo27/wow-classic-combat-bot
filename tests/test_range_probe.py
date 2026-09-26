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
            TargetPolicyConfig(allowed_names=("Young Nightsaber", "Young Thistle Boar"))
        ),
        CombatRules(**settings),
        random_interval=lambda low, high: 1.1,
    )


def observation(health=90.0, out_of_range=None):
    return Observation(
        target=TargetInfo(
            name="Young Nightsaber",
            exists=True,
            health_percent=health,
        ),
        slot_out_of_range=out_of_range,
    )


class RedSlotIsNotAReasonToWalkTests(unittest.TestCase):
    """A red key digit also appears when the target is too close.

    Walking never fixes that, and never attacking is what caused
    "You are facing the wrong way!", so the bot always attacks first.
    """

    def test_red_slot_attacks_instead_of_walking(self):
        result = machine().step(observation(out_of_range=True), now=0.0)

        self.assertEqual(result.state, "FIGHTING")
        self.assertEqual(result.action.key, "1")

    def test_out_of_range_still_keeps_attacking(self):
        machine_under_test = machine()
        machine_under_test.step(observation(out_of_range=True), now=0.0)

        result = machine_under_test.step(
            observation(health=88.0, out_of_range=True),
            now=2.0,
        )

        self.assertEqual(result.state, "FIGHTING")
        self.assertEqual(result.action.key, "2")

    def test_bare_out_of_range_never_forces_approach(self):
        engine = machine()
        for index in range(4):
            result = engine.step(
                observation(
                    health=90.0 if index % 2 else 88.0,
                    out_of_range=True,
                ),
                now=float(index) * 2.0,
            )
            self.assertNotEqual(result.state, "APPROACHING")


class WastedAttackTests(unittest.TestCase):
    def test_missing_damage_eventually_closes_distance(self):
        engine = machine()
        engine.step(observation(health=90.0), now=0.0)
        engine.step(observation(health=90.0), now=2.0)
        engine.step(observation(health=90.0), now=4.0)

        result = engine.step(observation(health=90.0), now=6.0)

        self.assertEqual(result.state, "APPROACHING")
        self.assertEqual(result.action.key, "w")

    def test_damage_stops_the_approach(self):
        engine = machine()
        engine.step(observation(health=90.0), now=0.0)
        engine.step(observation(health=90.0), now=2.0)

        result = engine.step(observation(health=84.0), now=4.0)

        self.assertNotEqual(result.state, "APPROACHING")


if __name__ == "__main__":
    unittest.main()
