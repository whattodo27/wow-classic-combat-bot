"""Проверка детектора боя на настоящих кадрах и на синтетике."""

import unittest
from pathlib import Path

from PIL import Image, ImageDraw

from combat_bot.combat_badge import in_combat, read_combat_badge

FRAMES = Path("combat_frames")
SIZE = (1040, 807)


def _frames():
    loaded = []
    for path in sorted(FRAMES.glob("frame_*.jpg")):
        try:
            index = int(path.stem.split("_")[-1])
        except ValueError:
            continue
        loaded.append((index, Image.open(path).convert("RGB")))
    return [image for _, image in sorted(loaded)]


def _draw_badge(image: Image.Image, red: bool):
    from combat_bot.combat_badge import badge_box

    left, top, right, bottom = badge_box(image.size)
    draw = ImageDraw.Draw(image)
    color = (200, 40, 40) if red else (40, 40, 40)
    draw.ellipse([left, top, right, bottom], fill=color)
    # Светлый крест внутри - имитация мечей.
    mark = (255, 220, 220) if red else (200, 200, 200)
    mid_x = (left + right) // 2
    mid_y = (top + bottom) // 2
    draw.line([(left + 3, top + 3), (right - 3, bottom - 3)], fill=mark, width=2)
    draw.line([(left + 3, bottom - 3), (right - 3, top + 3)], fill=mark, width=2)
    return image


class BadgeGeometryTests(unittest.TestCase):
    def test_badge_sits_under_the_portrait(self):
        from combat_bot.combat_badge import badge_box

        left, top, right, bottom = badge_box(SIZE)

        self.assertLess(right, 60)
        self.assertGreater(top, 80)
        self.assertLess(bottom, 130)


class SyntheticBadgeTests(unittest.TestCase):
    def test_red_badge_means_combat(self):
        image = _draw_badge(Image.new("RGB", SIZE, (0, 0, 0)), red=True)

        self.assertTrue(in_combat(image))

    def test_dark_badge_means_out_of_combat(self):
        image = _draw_badge(Image.new("RGB", SIZE, (0, 0, 0)), red=False)

        self.assertFalse(in_combat(image))

    def test_empty_frame_is_ambiguous(self):
        badge = read_combat_badge(Image.new("RGB", SIZE, (0, 0, 0)))

        self.assertIsNone(badge.in_combat)


class RealCombatFramesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frames = _frames()

    def test_twenty_frames_present(self):
        self.assertEqual(len(self.frames), 20)

    def test_most_frames_report_combat(self):
        # Кадры сняты в бою, значит мечи должны читаться почти везде.
        combat = sum(1 for image in self.frames if in_combat(image) is True)
        self.assertGreater(combat, len(self.frames) // 2)

    def test_every_frame_gives_a_decision(self):
        for image in self.frames:
            self.assertIn(in_combat(image), (True, False, None))


if __name__ == "__main__":
    unittest.main()
