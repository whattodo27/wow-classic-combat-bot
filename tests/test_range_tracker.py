import unittest

from combat_bot.range_tracker import RangeTracker, RangeVerdict


class RangeTrackerTests(unittest.TestCase):
    def test_health_drop_after_attack_means_in_range(self):
        tracker = RangeTracker()
        tracker.observe_health(90.0)
        tracker.note_attack()

        verdict = tracker.observe_health(85.0)

        self.assertEqual(verdict, RangeVerdict.IN_RANGE)

    def test_health_unchanged_after_attack_means_out_of_range(self):
        tracker = RangeTracker()
        tracker.observe_health(90.0)
        tracker.note_attack()

        verdict = tracker.observe_health(90.0)

        self.assertEqual(verdict, RangeVerdict.OUT_OF_RANGE)

    def test_health_without_attack_is_unknown(self):
        tracker = RangeTracker()

        self.assertEqual(tracker.observe_health(90.0), RangeVerdict.UNKNOWN)

    def test_missing_health_is_unknown(self):
        tracker = RangeTracker()
        tracker.observe_health(90.0)
        tracker.note_attack()

        self.assertEqual(tracker.observe_health(None), RangeVerdict.UNKNOWN)

    def test_verdict_sticks_until_next_attack(self):
        tracker = RangeTracker()
        tracker.observe_health(90.0)
        tracker.note_attack()
        tracker.observe_health(80.0)

        self.assertEqual(tracker.observe_health(70.0), RangeVerdict.IN_RANGE)

    def test_new_attack_rechecks(self):
        tracker = RangeTracker()
        tracker.observe_health(90.0)
        tracker.note_attack()
        tracker.observe_health(80.0)
        tracker.note_attack()

        self.assertEqual(tracker.observe_health(80.0), RangeVerdict.OUT_OF_RANGE)

    def test_tiny_damage_is_not_counted_as_in_range(self):
        tracker = RangeTracker(epsilon=2.0)
        tracker.observe_health(90.0)
        tracker.note_attack()

        self.assertEqual(tracker.observe_health(89.5), RangeVerdict.OUT_OF_RANGE)

    def test_target_healing_between_probes_means_out_of_range(self):
        tracker = RangeTracker()
        tracker.observe_health(50.0)
        tracker.note_attack()

        self.assertEqual(tracker.observe_health(55.0), RangeVerdict.OUT_OF_RANGE)


if __name__ == "__main__":
    unittest.main()
