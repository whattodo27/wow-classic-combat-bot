import unittest

from PIL import Image

from combat_bot.pixel_ui import UiRegion, is_region_blank, read_bar


def make_bar_image(width=120, height=8, fill_ratio=0.5, fill=(0, 200, 0)):
    image = Image.new("RGB", (width, height), (20, 20, 20))
    pixels = image.load()
    filled = int(width * fill_ratio)
    for y in range(height):
        for x in range(filled):
            pixels[x, y] = fill
    return image


class BarReadingTests(unittest.TestCase):
    def test_full_bar_reads_near_one_hundred_percent(self):
        image = make_bar_image(fill_ratio=1.0)
        region = UiRegion(0, 0, 120, 8)

        reading = read_bar(image, region, (0, 200, 0))

        self.assertTrue(reading.present)
        self.assertGreater(reading.percent, 95.0)

    def test_half_bar_reads_about_fifty_percent(self):
        image = make_bar_image(fill_ratio=0.5)
        region = UiRegion(0, 0, 120, 8)

        reading = read_bar(image, region, (0, 200, 0))

        self.assertTrue(reading.present)
        self.assertAlmostEqual(reading.percent, 50.0, delta=3.0)

    def test_empty_bar_is_reported_absent(self):
        image = Image.new("RGB", (120, 8), (20, 20, 20))
        region = UiRegion(0, 0, 120, 8)

        reading = read_bar(image, region, (0, 200, 0))

        self.assertFalse(reading.present)
        self.assertIsNone(reading.percent)

    def test_wrong_color_is_not_mistaken_for_a_bar(self):
        image = make_bar_image(fill_ratio=1.0, fill=(200, 0, 0))
        region = UiRegion(0, 0, 120, 8)

        reading = read_bar(image, region, (0, 200, 0))

        self.assertFalse(reading.present)

    def test_invalid_region_is_absent_not_a_crash(self):
        image = make_bar_image()
        region = UiRegion(0, 0, 0, 0)

        reading = read_bar(image, region, (0, 200, 0))

        self.assertFalse(reading.present)


class BlankRegionTests(unittest.TestCase):
    def test_black_region_is_blank(self):
        image = Image.new("RGB", (40, 20), (0, 0, 0))

        self.assertTrue(is_region_blank(image, UiRegion(0, 0, 40, 20)))

    def test_name_plate_with_text_is_not_blank(self):
        image = Image.new("RGB", (40, 20), (0, 0, 0))
        pixels = image.load()
        for x in range(10, 30):
            pixels[x, 10] = (255, 230, 0)

        self.assertFalse(is_region_blank(image, UiRegion(0, 0, 40, 20)))


if __name__ == "__main__":
    unittest.main()
