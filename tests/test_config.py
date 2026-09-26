import json
import unittest
from pathlib import Path

from combat_bot.config import load_config


class ConfigTests(unittest.TestCase):
    def test_dry_run_is_the_default_and_slots_are_one_through_nine(self):
        config = load_config(Path(__file__).parents[1] / "combat_config.example.json")

        self.assertFalse(config.live_input)
        self.assertEqual(sorted(config.attack_slots), list(range(1, 10)))
        self.assertTrue(all(config.attack_slots[i] is None for i in range(1, 10)))
        self.assertEqual(config.window_title, "")

    def test_config_rejects_live_input_when_window_title_is_blank(self):
        path = Path(self.enterContext(__import__("tempfile").TemporaryDirectory())) / "bad.json"
        path.write_text(json.dumps({"live_input": True, "window": {"title": ""}}))

        with self.assertRaises(ValueError):
            load_config(path)


if __name__ == "__main__":
    unittest.main()
