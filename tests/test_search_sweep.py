import unittest

from combat_bot.models import CombatRules, Observation, TargetInfo, TargetPolicyConfig
from combat_bot.state_machine import CombatStateMachine
from combat_bot.target_policy import TargetPolicy


def make_machine(**overrides):
    settings = {
        "target_key": "tab",
        "live_targeting": True,
        "turn_left_key": "a",
        "turn_right_key": "d",
        "turn_hold_seconds": 0.75,
        "approach_key": "w",
    }
    settings.update(overrides)
    return CombatStateMachine(
        TargetPolicy(TargetPolicyConfig(allowed_names=("Young Nightsaber",))),
        CombatRules(**settings),
    )


NO_TARGET = Observation(target=TargetInfo(exists=False))


class SearchSweepTests(unittest.TestCase):
    def test_search_sweeps_forward_before_scanning(self):
        machine = make_machine()

        result = machine.step(NO_TARGET, now=0.0)

        self.assertEqual(result.state, "SEARCHING")
        self.assertEqual(result.action.kind, "hold_keys")
        self.assertEqual(set(result.action.keys), {"w", "d"})
        self.assertEqual(result.action.hold_seconds, 0.75)

    def test_search_scans_with_tab_after_a_sweep(self):
        machine = make_machine()
        machine.step(NO_TARGET, now=0.0)

        result = machine.step(NO_TARGET, now=1.0)

        self.assertEqual(result.action.kind, "press_key")
        self.assertEqual(result.action.key, "tab")

    def test_search_alternates_sweep_then_tab(self):
        machine = make_machine()
        machine.step(NO_TARGET, now=0.0)

        second = machine.step(NO_TARGET, now=1.0)
        third = machine.step(NO_TARGET, now=2.0)
        fourth = machine.step(NO_TARGET, now=3.0)

        self.assertEqual(second.action.key, "tab")
        self.assertEqual(third.action.kind, "hold_keys")
        self.assertEqual(fourth.action.key, "tab")

    def test_sweep_keeps_one_direction_so_the_character_circles(self):
        machine = make_machine()
        sweep_keys = []
        for index in range(6):
            sweep = machine.step(NO_TARGET, now=float(index) * 2.0)
            if sweep.action.kind == "hold_keys":
                sweep_keys.append(set(sweep.action.keys))

        self.assertEqual(len(sweep_keys), 3)
        for keys in sweep_keys:
            self.assertEqual(keys, {"w", "d"})

    def test_approved_target_stops_sweeping(self):
        machine = make_machine()
        machine.step(NO_TARGET, now=0.0)

        result = machine.step(
            Observation(
                target=TargetInfo(name="Young Nightsaber", exists=True),
                target_distance="near",
            ),
            now=0.1,
        )

        self.assertNotEqual(result.action.kind, "hold_keys")
        self.assertNotEqual(result.action.key, "tab")

    def test_disabled_turn_keys_scan_with_tab_immediately(self):
        machine = make_machine(turn_left_key=None, turn_right_key=None)

        result = machine.step(NO_TARGET, now=0.0)

        self.assertEqual(result.action.kind, "press_key")
        self.assertEqual(result.action.key, "tab")

    def test_sweep_without_forward_key_only_turns(self):
        machine = make_machine(approach_key=None)

        result = machine.step(NO_TARGET, now=0.0)

        self.assertEqual(result.action.kind, "hold_keys")
        self.assertEqual(set(result.action.keys), {"d"})

    def test_new_target_after_miss_restarts_search_with_sweep(self):
        machine = make_machine()
        machine.step(NO_TARGET, now=0.0)
        machine.step(NO_TARGET, now=1.0)
        machine.step(
            Observation(
                target=TargetInfo(name="Young Nightsaber", exists=True),
                target_distance="near",
            ),
            now=1.5,
        )

        after_target_lost = machine.step(NO_TARGET, now=2.0)

        self.assertEqual(after_target_lost.action.kind, "hold_keys")


if __name__ == "__main__":
    unittest.main()
