import unittest

from PIL import Image, ImageDraw

from combat_bot.layout import UiLayout
from combat_bot.pixel_sensor import PixelSensor


def frame(size, target=True, target_ratio=0.8, player=1.0):
    image = Image.new("RGB", size, (0, 0, 0))
    draw = ImageDraw.Draw(image)
    layout = UiLayout()

    left, top, right, bottom = layout.player_health_box(size)
    draw.rectangle(
        [left, top, left + int((right - left) * player), bottom - 1],
        fill=layout.player_health_color,
    )
    left, top, right, bottom = layout.player_mana_box(size)
    draw.rectangle([left, top, right - 1, bottom - 1], fill=layout.mana_color)

    if target:
        left, top, right, bottom = layout.target_name_box(size)
        draw.rectangle([left, top, right - 1, bottom - 1], fill=layout.target_name_color)
        left, top, right, bottom = layout.target_health_box(size)
        draw.rectangle(
            [left, top, left + int((right - left) * target_ratio), bottom - 1],
            fill=layout.target_health_color,
        )
    return image


SIZES = ((1040, 807), (768, 603), (1280, 900), (1920, 1200))


class PixelSensorLayoutTests(unittest.TestCase):
    def test_reads_player_health_at_every_size(self):
        sensor = PixelSensor()
        for size in SIZES:
            with self.subTest(size=size):
                observation = sensor.observe(frame(size, target=False))
                self.assertAlmostEqual(
                    observation.player_health_percent, 100.0, delta=2.0
                )

    def test_detects_target_at_every_size(self):
        sensor = PixelSensor()
        for size in SIZES:
            with self.subTest(size=size):
                observation = sensor.observe(frame(size, target=True))
                self.assertTrue(observation.target.exists)

    def test_reads_target_health_at_every_size(self):
        sensor = PixelSensor()
        for size in SIZES:
            with self.subTest(size=size):
                observation = sensor.observe(frame(size, target=True, target_ratio=0.5))
                self.assertAlmostEqual(
                    observation.target.health_percent, 50.0, delta=5.0
                )

    def test_no_target_when_frame_absent_at_every_size(self):
        sensor = PixelSensor()
        for size in SIZES:
            with self.subTest(size=size):
                observation = sensor.observe(frame(size, target=False))
                self.assertFalse(observation.target.exists)

    def test_empty_target_bar_is_not_a_target(self):
        sensor = PixelSensor()

        observation = sensor.observe(frame((1040, 807), target=True, target_ratio=0.0))

        self.assertFalse(observation.target.exists)

    def test_black_frame_reports_unknown(self):
        sensor = PixelSensor()

        observation = sensor.observe(Image.new("RGB", (1040, 807), (0, 0, 0)))

        self.assertIsNone(observation.player_health_percent)
        self.assertIsNone(observation.player_mana_percent)
        self.assertFalse(observation.target.exists)
        self.assertIsNone(observation.slot_out_of_range)

    def test_red_digit_marks_target_out_of_range(self):
        # Игра рисует красной именно цифру кнопки, а не рамку слота,
        # поэтому тест рисует цифру в её настоящем месте.
        from combat_bot.slots import digit_box

        image = frame((1040, 807), target=True)
        draw = ImageDraw.Draw(image)
        left, top, right, bottom = digit_box(1, image.size)
        draw.rectangle([left, top, right - 1, bottom - 1], fill=(240, 40, 40))

        observation = PixelSensor().observe(image)

        self.assertTrue(observation.slot_out_of_range)

    def test_white_digit_reports_in_range(self):
        from combat_bot.slots import digit_box

        image = frame((1040, 807), target=True)
        draw = ImageDraw.Draw(image)
        left, top, right, bottom = digit_box(1, image.size)
        draw.rectangle([left, top, right - 1, bottom - 1], fill=(255, 255, 255))

        observation = PixelSensor().observe(image)

        self.assertFalse(observation.slot_out_of_range)

    def test_normal_bar_reports_in_range(self):
        observation = PixelSensor().observe(frame((1040, 807), target=True))

        # Без цифры данных недостаточно: решать дистанцию нельзя.
        self.assertIsNone(observation.slot_out_of_range)


if __name__ == "__main__":
    unittest.main()
