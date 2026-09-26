import unittest
from pathlib import Path


class EntryPointTests(unittest.TestCase):
    def test_root_entrypoint_uses_combat_prototype(self):
        source = (Path(__file__).parents[1] / "main.py").read_text(encoding="utf-8")

        self.assertIn("combat_bot.main", source)
        self.assertNotIn("WoWClassicAgent", source)


if __name__ == "__main__":
    unittest.main()
