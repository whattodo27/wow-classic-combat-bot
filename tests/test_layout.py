import unittest

from PIL import Image, ImageDraw

from combat_bot.layout import UiLayout


def frame(size, target=True, target_ratio=0.8):
    width, height = size
    image = Image.new("RGB", size, (0, 0, 0))
    draw = ImageDraw.Draw(image)
    layout = UiLayout()
    layout.draw_test_bars(draw, size, target=target, target_ratio=target_ratio)
    return image


class LayoutGeometryTests(unittest.TestCase):
    def test_regions_scale_with_window_size(self):
        layout = UiLayout()

        small = layout.player_health_box((1040, 807))
        large = layout.player_health_box((2080, 1614))

        self.assertEqual(small[0] * 2, large[0])
        self.assertEqual(small[1] * 2, large[1])
        self.assertEqual(small[2] * 2, large[2])

    def test_boxes_stay_inside_small_window(self):
        layout = UiLayout()

        for size in ((1040, 807), (768, 603), (1920, 1200)):
            for box in (
                layout.player_health_box(size),
                layout.player_mana_box(size),
                layout.target_name_box(size),
                layout.target_health_box(size),
            ):
                self.assertLess(box[0], size[0])
                self.assertLess(box[1], size[1])
                self.assertGreaterEqual(box[0], 0)
                self.assertGreaterEqual(box[1], 0)


if __name__ == "__main__":
    unittest.main()
