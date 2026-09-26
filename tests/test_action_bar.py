import unittest

from PIL import Image, ImageDraw

from combat_bot.action_bar import BarScanResult, red_frame_rows, scan_action_bar


SIZE = (1040, 807)
STRIP_TOP = int(SIZE[1] * 0.92)


def base_frame(draw):
    draw.rectangle([0, 0, SIZE[0], SIZE[1]], fill=(20, 20, 20))
    # A purple XP bar sits at the top of the strip and must not be read as red.
    draw.rectangle([0, STRIP_TOP, SIZE[0], STRIP_TOP + 6], fill=(150, 40, 160))


def frame(red_slot=False):
    image = Image.new("RGB", SIZE, (20, 20, 20))
    draw = ImageDraw.Draw(image)
    base_frame(draw)
    # Normal slot frames: dark grey.
    for index in range(10):
        left = 80 + index * 48
        draw.rectangle(
            [left, STRIP_TOP + 20, left + 40, STRIP_TOP + 60],
            outline=(70, 65, 55),
            width=2,
        )
    if red_slot:
        # Out-of-range look: the whole slot outline turns red.
        draw.rectangle(
            [80, STRIP_TOP + 20, 120, STRIP_TOP + 60],
            outline=(235, 40, 40),
            width=3,
        )
    return image


def with_glyph():
    """A red '?' icon inside a slot: red pixels but no frame."""
    image = frame(False)
    draw = ImageDraw.Draw(image)
    draw.rectangle(
        [100, STRIP_TOP + 30, 112, STRIP_TOP + 48], fill=(220, 40, 40)
    )
    return image


class RedFrameRowTests(unittest.TestCase):
    def strip(self, image):
        return image.crop((0, STRIP_TOP, image.size[0], image.size[1]))

    def test_normal_bar_has_no_frame_rows(self):
        self.assertEqual(red_frame_rows(self.strip(frame(False))), 0)

    def test_red_frame_creates_frame_rows(self):
        self.assertGreaterEqual(red_frame_rows(self.strip(frame(True))), 2)

    def test_purple_xp_bar_is_not_a_red_frame(self):
        self.assertEqual(red_frame_rows(self.strip(frame(False))), 0)

    def test_red_glyph_alone_is_not_a_frame(self):
        self.assertLess(red_frame_rows(self.strip(with_glyph())), 2)


class ScanActionBarTests(unittest.TestCase):
    def test_normal_bar_reports_in_range(self):
        result = scan_action_bar(frame(False))

        self.assertFalse(result.out_of_range)
        self.assertIsInstance(result, BarScanResult)

    def test_red_frame_reports_out_of_range(self):
        result = scan_action_bar(frame(True))

        self.assertTrue(result.out_of_range)

    def test_red_glyph_does_not_report_out_of_range(self):
        result = scan_action_bar(with_glyph())

        self.assertFalse(result.out_of_range)

    def test_empty_screen_reports_in_range(self):
        result = scan_action_bar(Image.new("RGB", SIZE, (0, 0, 0)))

        self.assertFalse(result.out_of_range)

    def test_scan_works_at_half_size(self):
        small = frame(True).resize((520, 404))

        self.assertTrue(scan_action_bar(small).out_of_range)


if __name__ == "__main__":
    unittest.main()
