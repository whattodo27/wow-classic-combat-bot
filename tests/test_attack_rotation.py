import unittest

from combat_bot.models import CombatRules, Observation, TargetInfo, TargetPolicyConfig
from combat_bot.state_machine import CombatStateMachine
from combat_bot.target_policy import TargetPolicy


class AttackRotationTests(unittest.TestCase):
    def make_machine(self, rng_interval=1.1, **overrides):
        settings = {
            "target_key": "tab",
            "opening_attack_slot": 1,
            "opening_attack_count": 2,
            "opening_attack_interval_seconds": 2.0,
            "melee_attack_slot": 2,
            "melee_attack_interval_min_seconds": 1.0,
            "melee_attack_interval_max_seconds": 1.3,
            "approach_key": "w",
            "max_attacks_before_closing": 2,
        }
        settings.update(overrides)
        return CombatStateMachine(
            TargetPolicy(TargetPolicyConfig(allowed_names=("Young Nightsaber",))),
            CombatRules(**settings),
            random_interval=lambda low, high: rng_interval,
        )

    def observation(self, health=90.0):
        return Observation(
            target=TargetInfo(
                name="Young Nightsaber",
                exists=True,
                health_percent=health,
            ),
        )

    def test_opening_rotation_presses_slot_one_twice_two_seconds_apart(self):
        machine = self.make_machine()

        first = machine.step(self.observation(), now=0.0)
        second = machine.step(self.observation(health=88.0), now=2.0)

        self.assertEqual(first.action.key, "1")
        self.assertEqual(first.action.reason, "opening_attack")
        self.assertEqual(second.action.key, "1")

    def test_opening_rotation_waits_between_slot_one_presses(self):
        machine = self.make_machine()
        machine.step(self.observation(), now=0.0)

        waiting = machine.step(self.observation(health=88.0), now=1.0)

        self.assertEqual(waiting.action.kind, "wait")
        self.assertIsNone(waiting.action.key)

    def test_slot_two_follows_the_opening_burst(self):
        machine = self.make_machine()
        machine.step(self.observation(), now=0.0)
        machine.step(self.observation(health=88.0), now=2.0)

        result = machine.step(self.observation(health=86.0), now=4.0)

        self.assertEqual(result.action.key, "2")

    def test_slot_two_repeats_at_random_interval(self):
        machine = self.make_machine(rng_interval=1.25)
        machine.step(self.observation(), now=0.0)
        machine.step(self.observation(health=88.0), now=2.0)

        first = machine.step(self.observation(health=86.0), now=4.0)
        waiting = machine.step(self.observation(health=84.0), now=4.5)
        repeat = machine.step(self.observation(health=82.0), now=5.35)

        self.assertEqual(first.action.key, "2")
        self.assertEqual(waiting.action.kind, "wait")
        self.assertEqual(repeat.action.key, "2")

    def test_wasted_attacks_trigger_closing_distance(self):
        machine = self.make_machine()
        first = machine.step(self.observation(health=90.0), now=0.0)
        second = machine.step(self.observation(health=90.0), now=2.0)
        closing = machine.step(self.observation(health=90.0), now=4.0)

        self.assertEqual(first.action.key, "1")
        self.assertEqual(second.state, "FIGHTING")
        self.assertEqual(closing.state, "APPROACHING")
        self.assertEqual(closing.action.key, "w")

    def test_damage_resets_the_miss_counter(self):
        machine = self.make_machine()
        machine.step(self.observation(health=90.0), now=0.0)
        machine.step(self.observation(health=90.0), now=1.0)
        machine.step(self.observation(health=88.0), now=2.0)

        result = machine.step(self.observation(health=86.0), now=3.0)

        self.assertNotEqual(result.state, "APPROACHING")


if __name__ == "__main__":
    unittest.main()
