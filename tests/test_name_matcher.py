import unittest

from PIL import Image, ImageDraw

from combat_bot.name_matcher import NameMatcher, similarity


def plate(text_width=40, offset=0, color=(255, 255, 255)):
    image = Image.new("RGB", (140, 20), (0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rectangle([0, 2, 139, 17], fill=(60, 50, 10))
    draw.rectangle([10 + offset, 7, 10 + offset + text_width, 12], fill=color)
    return image


class SimilarityTests(unittest.TestCase):
    def test_identical_plates_are_similar(self):
        self.assertGreater(similarity(plate(), plate()), 0.95)

    def test_small_shift_still_matches(self):
        self.assertGreater(similarity(plate(), plate(offset=2)), 0.9)

    def test_different_plates_score_low(self):
        self.assertLess(similarity(plate(text_width=20), plate(text_width=90)), 0.9)


class NameMatcherTests(unittest.TestCase):
    def test_no_templates_never_claims_a_name(self):
        matcher = NameMatcher()

        result = matcher.match(plate())

        self.assertIsNone(result.name)

    def test_registered_template_is_matched(self):
        matcher = NameMatcher()
        matcher.add("Young Nightsaber", plate())

        result = matcher.match(plate())

        self.assertEqual(result.name, "Young Nightsaber")
        self.assertGreater(result.score, 0.86)

    def test_wrong_plate_is_rejected_as_unknown(self):
        matcher = NameMatcher()
        matcher.add("Young Nightsaber", plate(text_width=40))

        result = matcher.match(plate(text_width=110))

        self.assertIsNone(result.name)

    def test_two_templates_pick_the_closer_one(self):
        matcher = NameMatcher()
        matcher.add("Thistle Boar", plate(text_width=20))
        matcher.add("Young Nightsaber", plate(text_width=95))

        result = matcher.match(plate(text_width=95))

        self.assertEqual(result.name, "Young Nightsaber")

    def test_threshold_blocks_weak_matches(self):
        matcher = NameMatcher()
        matcher.add("Young Nightsaber", plate())

        result = matcher.match(plate(), threshold=1.01)

        self.assertIsNone(result.name)


if __name__ == "__main__":
    unittest.main()
