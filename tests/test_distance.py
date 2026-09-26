import unittest

from combat_bot.distance import estimate_distance


class EstimateDistanceTests(unittest.TestCase):
    def test_full_size_target_is_near(self):
        self.assertEqual(estimate_distance(1000, 1000), "near")

    def test_large_target_is_near(self):
        self.assertEqual(estimate_distance(700, 1000), "near")

    def test_tiny_target_is_far(self):
        self.assertEqual(estimate_distance(100, 1000), "far")

    def test_middle_size_is_unknown_not_guessed(self):
        self.assertIsNone(estimate_distance(400, 1000))

    def test_zero_measurement_is_unknown(self):
        self.assertIsNone(estimate_distance(0, 1000))

    def test_zero_reference_is_unknown(self):
        self.assertIsNone(estimate_distance(500, 0))

    def test_custom_thresholds_are_honored(self):
        self.assertEqual(
            estimate_distance(300, 1000, near_ratio=0.25, far_ratio=0.10),
            "near",
        )


if __name__ == "__main__":
    unittest.main()
