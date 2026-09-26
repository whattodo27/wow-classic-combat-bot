import unittest

from combat_bot.models import Observation, TargetInfo
from combat_bot.response_parser import parse_observation


class ResponseParserTests(unittest.TestCase):
    def test_parses_fenced_json(self):
        text = '''```json
{"player_health_percent": 72, "player_mana_percent": 61, "target": {"name": "Kobold Vermin", "is_player": false, "is_elite": false, "is_rare": false, "health_percent": 84, "distance": "near"}}
```'''

        observation = parse_observation(text)

        self.assertIsNotNone(observation)
        self.assertEqual(observation.target.name, "Kobold Vermin")
        self.assertEqual(observation.player_health_percent, 72)

    def test_parses_json_embedded_in_prose(self):
        text = 'Here is the state: {"player_health_percent": 55, "target": {"name": "Kobold"}} done.'

        observation = parse_observation(text)

        self.assertIsNotNone(observation)
        self.assertEqual(observation.target, TargetInfo(name="Kobold"))

    def test_missing_values_are_safe_defaults(self):
        observation = parse_observation("{}")

        self.assertIsNotNone(observation)
        self.assertIsNone(observation.target.name)
        self.assertFalse(observation.target.exists)
        self.assertIsNone(observation.player_health_percent)

    def test_incomplete_json_is_rejected_instead_of_guessing(self):
        observation = parse_observation('{"target": {"name": "Kobold"')

        self.assertIsNone(observation)


if __name__ == "__main__":
    unittest.main()
