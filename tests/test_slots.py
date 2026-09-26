"""Чтение слота Auto Shot на настоящих боевых кадрах.

Кадры сняты в момент боя, где цель была вне зоны: цифра «1» красная.
Проверяем, что детектор это видит, и не ловит ложных срабатываний.
"""

import unittest
from pathlib import Path

from PIL import Image, ImageDraw

from combat_bot.slots import (
    auto_shot_out_of_range,
    read_slot,
    scan_slots,
    slot_box,
)

FRAMES = Path("combat_frames")
SIZE = (1040, 807)


def _frame(index: int):
    for path in sorted(FRAMES.glob("frame_*.jpg")):
        if path.name == f"frame_{index}.jpg":
            return Image.open(path).convert("RGB")
    return None


def _draw_digit(image: Image.Image, index: int, color, thickness: int = 6):
    """Нарисовать цифру в боксе слота, как это делает игра."""
    from combat_bot.slots import digit_box

    left, top, right, bottom = digit_box(index, image.size)
    draw = ImageDraw.Draw(image)
    # Диагональные штрихи имитируют начертание цифры.
    draw.line([(left, bottom), (right, top)], fill=color, width=thickness)
    draw.line([(left, top), (right, bottom)], fill=color, width=thickness)
    return image


class SlotGeometryTests(unittest.TestCase):
    def test_first_slot_matches_calibration(self):
        left, top, right, bottom = slot_box(1, SIZE)

        self.assertLessEqual(left, 25)
        self.assertGreaterEqual(right, 70)
        self.assertLessEqual(top, 760)
        self.assertGreaterEqual(bottom, 795)

    def test_slots_do_not_overlap(self):
        one = slot_box(1, SIZE)
        two = slot_box(2, SIZE)

        self.assertLessEqual(one[2], two[0])

    def test_geometry_scales_with_window(self):
        small = slot_box(1, (520, 404))
        full = slot_box(1, SIZE)

        self.assertLess(small[2] - small[0], full[2] - full[0])


class DigitColorTests(unittest.TestCase):
    def test_red_digit_reads_as_out_of_range(self):
        image = Image.new("RGB", SIZE, (0, 0, 0))
        _draw_digit(image, 1, (255, 40, 40))

        self.assertTrue(read_slot(image, 1).is_red)
        self.assertTrue(auto_shot_out_of_range(image))

    def test_white_digit_reads_as_in_range(self):
        image = Image.new("RGB", SIZE, (0, 0, 0))
        _draw_digit(image, 1, (255, 255, 255))

        state = read_slot(image, 1)
        self.assertFalse(state.is_red)
        self.assertFalse(auto_shot_out_of_range(image))

    def test_empty_digit_is_ambiguous(self):
        image = Image.new("RGB", SIZE, (0, 0, 0))

        self.assertIsNone(auto_shot_out_of_range(image))

    def test_only_slot_one_is_read_for_range(self):
        image = Image.new("RGB", SIZE, (0, 0, 0))
        _draw_digit(image, 2, (255, 40, 40))

        self.assertFalse(read_slot(image, 1).is_red)
        self.assertTrue(read_slot(image, 2).is_red)


class RealFrameTests(unittest.TestCase):
    """Проверка на кадрах, снятых в настоящем бою."""

    @classmethod
    def setUpClass(cls):
        loaded = []
        for path in sorted(FRAMES.glob("frame_*.jpg")):
            # Имена файлов вроде "frame_ 5.jpg" содержат пробел из-за
            # форматирования, поэтому индекс берём из самого числа.
            try:
                index = int(path.stem.split("_")[-1])
            except ValueError:
                continue
            loaded.append((index, Image.open(path).convert("RGB")))
        cls.frames = [image for _, image in sorted(loaded)]

    def test_all_twenty_frames_were_captured(self):
        self.assertEqual(len(self.frames), 20)

    def test_every_frame_reports_a_decision(self):
        for image in self.frames:
            self.assertIsNotNone(auto_shot_out_of_range(image))

    def test_out_of_range_is_detected_on_most_frames(self):
        # Цель была далеко весь бой, поэтому цифра «1» красная почти всегда.
        red = sum(1 for image in self.frames if auto_shot_out_of_range(image))
        self.assertGreater(red, len(self.frames) // 2)

    def test_all_twelve_slots_are_readable(self):
        states = scan_slots(self.frames[0])

        self.assertEqual(len(states), 12)
        self.assertIn(1, states)


if __name__ == "__main__":
    unittest.main()
