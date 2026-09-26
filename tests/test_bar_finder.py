import unittest

from PIL import Image, ImageDraw

from combat_bot.bar_finder import measure_bar, region_has_content


def frame(player_ratio=1.0, target_ratio=0.8, draw_target=True):
    image = Image.new("RGB", (1040, 807), (0, 0, 0))
    draw = ImageDraw.Draw(image)
    # Player health track: x=104..213, y=79..83
    filled = 104 + int(109 * player_ratio)
    draw.rectangle([104, 79, filled, 82], fill=(0, 205, 0))
    if draw_target:
        # Target name plate (text-like white) and green target health.
        draw.rectangle([430, 40, 600, 58], fill=(255, 255, 255))
        t_filled = 430 + int(180 * target_ratio)
        draw.rectangle([430, 62, t_filled, 67], fill=(0, 205, 0))
    return image


class MeasureBarTests(unittest.TestCase):
    def test_full_bar_reads_one_hundred(self):
        percent = measure_bar(
            frame(player_ratio=1.0, draw_target=False),
            (104, 79, 213, 83),
            (0, 205, 0),
        )

        self.assertAlmostEqual(percent, 100.0, delta=1.0)

    def test_half_bar_reads_about_fifty(self):
        percent = measure_bar(
            frame(player_ratio=0.5, draw_target=False),
            (104, 79, 213, 83),
            (0, 205, 0),
        )

        self.assertAlmostEqual(percent, 50.0, delta=4.0)

    def test_empty_bar_region_reads_as_none(self):
        percent = measure_bar(
            frame(player_ratio=0.0, draw_target=False),
            (104, 79, 213, 83),
            (0, 205, 0),
        )

        self.assertIsNone(percent)

    def test_invalid_box_is_none(self):
        self.assertIsNone(measure_bar(frame(), (0, 0, 0, 0), (0, 205, 0)))

    def test_box_outside_frame_is_none(self):
        self.assertIsNone(
            measure_bar(frame(), (5000, 5000, 5100, 5100), (0, 205, 0))
        )


class RegionContentTests(unittest.TestCase):
    def test_name_plate_present_is_content(self):
        image = frame(draw_target=True)

        self.assertTrue(region_has_content(image, (430, 40, 600, 58)))

    def test_name_plate_absent_is_empty(self):
        image = frame(draw_target=False)

        self.assertFalse(region_has_content(image, (430, 40, 600, 58)))


if __name__ == "__main__":
    unittest.main()
