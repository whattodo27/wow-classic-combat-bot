import unittest
from pathlib import Path

from combat_bot.config import load_config


class CliConfigTests(unittest.TestCase):
    def test_default_config_can_be_loaded_for_dry_run(self):
        config = load_config(Path(__file__).parents[1] / "combat_config.example.json")

        self.assertFalse(config.live_input)
        self.assertEqual(config.window_title, "")
        self.assertEqual(config.ollama_model, "llava:7b")

    def test_current_profile_contains_young_nightsaber_and_stays_dry_run(self):
        config = load_config(Path(__file__).parents[1] / "combat_config.json")

        self.assertTrue(config.live_input)
        self.assertTrue(config.rules.live_targeting)
        self.assertIn("Young Nightsaber", config.target_policy.allowed_names)
        self.assertEqual(config.attack_slots[1], 1)
        self.assertEqual(config.attack_slots[2], 2)
        self.assertEqual(config.rules.opening_attack_slot, 1)
        self.assertEqual(config.rules.opening_attack_count, 2)
        self.assertEqual(config.rules.melee_attack_slot, 2)
        self.assertEqual(config.rules.melee_attack_interval_min_seconds, 1.0)
        self.assertEqual(config.rules.melee_attack_interval_max_seconds, 1.3)


if __name__ == "__main__":
    unittest.main()
