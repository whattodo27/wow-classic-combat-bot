import unittest

from combat_bot.models import CombatRules, Observation, TargetInfo, TargetPolicyConfig
from combat_bot.state_machine import CombatStateMachine
from combat_bot.target_policy import TargetPolicy


def engine(**overrides):
    settings = {
        "target_key": "tab",
        "turn_right_key": "d",
        "approach_key": "w",
        "retreat_key": "s",
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


def obs(health=None, out_of_range=None):
    return Observation(
        target=TargetInfo(name="Young Nightsaber", exists=True, health_percent=health),
        slot_out_of_range=out_of_range,
    )


class AlwaysAttackTests(unittest.TestCase):
    """Attacking auto-faces the target, so the bot must always try first."""

    def test_attacks_even_when_slot_reports_out_of_range(self):
        result = engine().step(obs(health=90.0, out_of_range=True), now=0.0)

        self.assertEqual(result.action.key, "1")
        self.assertNotEqual(result.action.kind, "hold_keys")

    def test_attack_is_the_very_first_thing_after_target(self):
        machine = engine()
        machine.step(obs(health=90.0), now=0.0)

        result = machine.step(obs(health=88.0), now=2.0)

        self.assertEqual(result.action.key, "2")


class MoveOnlyWhenAttackMissesTests(unittest.TestCase):
    def test_two_wasted_attacks_make_the_bot_approach(self):
        machine = engine()
        machine.step(obs(health=90.0), now=0.0)
        machine.step(obs(health=90.0), now=2.0)
        machine.step(obs(health=90.0), now=4.0)

        result = machine.step(obs(health=90.0), now=6.0)

        self.assertEqual(result.state, "APPROACHING")
        self.assertEqual(result.action.key, "w")

    def test_damage_after_attack_means_keep_attacking(self):
        machine = engine()
        machine.step(obs(health=90.0), now=0.0)

        result = machine.step(obs(health=86.0), now=2.0)

        self.assertEqual(result.state, "FIGHTING")

    def test_never_holds_keys_while_a_target_is_selected(self):
        machine = engine()
        for index in range(8):
            health = 90.0 if index % 2 else 88.0
            result = machine.step(obs(health=health), now=float(index) * 2.0)
            self.assertNotEqual(result.action.kind, "hold_keys")


class AttackSettleGateTests(unittest.TestCase):
    """Cooldown gaps must not be mistaken for attacks that missed."""

    def make_machine(self):
        return CombatStateMachine(
            TargetPolicy(TargetPolicyConfig(allowed_names=("Young Nightsaber",))),
            CombatRules(
                target_key="tab",
                opening_attack_slot=1,
                opening_attack_count=2,
                opening_attack_interval_seconds=2.0,
                melee_attack_slot=2,
                approach_key="w",
                max_attacks_before_closing=2,
                attack_settle_seconds=1.5,
            ),
            random_interval=lambda low, high: 1.1,
        )

    def observation(self, health=90.0):
        return Observation(
            target=TargetInfo(
                name="Young Nightsaber",
                exists=True,
                health_percent=health,
            ),
        )

    def test_cooldown_does_not_count_as_a_missed_attack(self):
        machine = self.make_machine()
        machine.step(self.observation(health=90.0), now=0.0)

        # 0.5s later the opening attack is still on cooldown: no damage yet,
        # but the attack has not had time to land either.
        result = machine.step(self.observation(health=90.0), now=0.5)

        self.assertNotEqual(result.state, "APPROACHING")

    def test_real_miss_after_settle_time_still_approaches(self):
        machine = self.make_machine()
        machine.step(self.observation(health=90.0), now=0.0)
        machine.step(self.observation(health=90.0), now=2.0)

        result = machine.step(self.observation(health=90.0), now=4.0)

        self.assertEqual(result.state, "APPROACHING")

    def test_damage_keeps_the_bot_attacking_through_cooldowns(self):
        machine = self.make_machine()
        machine.step(self.observation(health=90.0), now=0.0)

        states = []
        for index in range(8):
            result = machine.step(
                self.observation(health=max(60.0, 90.0 - index * 4.0)),
                now=float(index) * 1.7,
            )
            states.append(result.state)

        self.assertNotIn("APPROACHING", states)


if __name__ == "__main__":
    unittest.main()
