"""Тесты конуса перед персонажем.

Смысл: бот не должен выбирать цель позади или сбоку, потому что игра
пишет «You are facing the wrong way!» и атака не проходит.
"""

import random
import unittest

from combat_bot.facing import (
    Facing,
    Nameplate,
    angle_between,
    apex_position,
    choose_turn_direction,
    inside_cone,
    pick_target_in_cone,
    random_turn_seconds,
    turn_degrees_for,
)

SIZE = (1040, 807)


def plate(x: int, y: int, width: int = 60) -> Nameplate:
    return Nameplate(x=x, y=y, width=width, name="Young Thistle Boar")


def facing_forward() -> Facing:
    x, y = apex_position(SIZE)
    return Facing(x=x, y=y, angle=0.0)


class ConeGeometryTests(unittest.TestCase):
    def test_apex_sits_where_the_character_stands(self):
        x, y = apex_position(SIZE)

        self.assertAlmostEqual(x / SIZE[0], 0.5, delta=0.01)
        self.assertGreater(y, SIZE[1] * 0.7)

    def test_straight_ahead_is_inside(self):
        facing = facing_forward()

        self.assertTrue(inside_cone((facing.x, facing.y - 200), facing, SIZE))

    def test_directly_behind_is_outside(self):
        facing = facing_forward()

        self.assertFalse(inside_cone((facing.x, facing.y + 100), facing, SIZE))

    def test_target_level_with_character_is_outside(self):
        facing = facing_forward()

        self.assertFalse(inside_cone((facing.x, facing.y), facing, SIZE))

    def test_wide_side_target_is_outside(self):
        facing = facing_forward()

        self.assertFalse(inside_cone((facing.x + 400, facing.y - 200), facing, SIZE))

    def test_target_turned_left_uses_rotated_facing(self):
        base = facing_forward()
        # Смотрим влево на 30 градусов: цель прямо перед нами теперь сбоку.
        left = Facing(base.x, base.y, angle=-30.0)
        forward_point = (base.x, base.y - 200)

        # При взгляде прямо цель спереди, при взгляде влево - почти сбоку.
        self.assertTrue(inside_cone(forward_point, base, SIZE, half_angle=31.0))
        self.assertFalse(inside_cone(forward_point, left, SIZE, half_angle=29.0))

    def test_half_angle_controls_strictness(self):
        facing = facing_forward()
        point = (facing.x + 100, facing.y - 200)

        self.assertFalse(inside_cone(point, facing, SIZE, half_angle=20.0))
        self.assertTrue(inside_cone(point, facing, SIZE, half_angle=30.0))


class TargetPickingTests(unittest.TestCase):
    def test_no_plates_means_no_target(self):
        self.assertIsNone(pick_target_in_cone([], facing_forward(), SIZE))

    def test_only_plates_in_front_are_considered(self):
        facing = facing_forward()
        front = plate(facing.x - 30, facing.y - 250)
        behind = plate(facing.x - 30, facing.y + 60)

        chosen = pick_target_in_cone([behind, front], facing, SIZE)

        self.assertIs(chosen, front)

    def test_closest_plate_wins(self):
        facing = facing_forward()
        near = plate(facing.x, facing.y - 150)
        far = plate(facing.x, facing.y - 400)

        self.assertIs(pick_target_in_cone([far, near], facing, SIZE), near)

    def test_side_plates_are_ignored(self):
        facing = facing_forward()
        side = plate(facing.x + 350, facing.y - 200)
        front = plate(facing.x, facing.y - 200)

        self.assertIs(pick_target_in_cone([side, front], facing, SIZE), front)

    def test_plates_far_apart_are_judged_by_their_own_center(self):
        facing = facing_forward()
        # Левая граница близко к оси, но центр уехал вправо: такая цель
        # вне конуса и выбирать её нельзя.
        shifted = Nameplate(x=facing.x + 200, y=facing.y - 200, width=40)

        self.assertIsNone(pick_target_in_cone([shifted], facing, SIZE))

    def test_normal_width_plate_center_stays_in_cone(self):
        facing = facing_forward()
        normal = Nameplate(x=facing.x - 30, y=facing.y - 200, width=60)

        chosen = pick_target_in_cone([normal], facing, SIZE)

        self.assertIsNotNone(chosen)
        self.assertEqual(chosen.center_x, facing.x)


class TurnDirectionTests(unittest.TestCase):
    def test_first_turn_is_random(self):
        rng = random.Random(7)
        seen = {choose_turn_direction(rng, history=[]) for _ in range(60)}

        self.assertEqual(seen, {1, -1})

    def test_recent_direction_is_not_repeated(self):
        # После поворота влево следующий обязан быть вправо. История
        # пополняется, поэтому проверяем каждый шаг отдельно.
        rng = random.Random(3)
        history = []

        for _ in range(30):
            direction = choose_turn_direction(rng, history=history, avoid_repeats=1)
            if history:
                self.assertNotEqual(direction, history[-1])
            history.append(direction)

    def test_last_two_directions_are_avoided(self):
        # История [1, -1] запрещает оба варианта, но правило берёт
        # последние два - значит остаётся выбор между ними. Проверяем,
        # что выбор не выходит за пределы разрешённого.
        rng = random.Random(11)
        history = [1, -1]

        directions = {
            choose_turn_direction(rng, history=history) for _ in range(40)
        }

        self.assertTrue(directions.issubset({1, -1}))

    def test_two_repeats_in_a_row_force_the_other_way(self):
        rng = random.Random(4)
        history = [1, 1]

        directions = {
            choose_turn_direction(rng, history=history) for _ in range(40)
        }

        self.assertEqual(directions, {-1})

    def test_blocked_direction_unblocks_after_history_moves(self):
        rng = random.Random(5)
        history = [1, 1, 1]

        self.assertEqual(choose_turn_direction(rng, history=history), -1)

    def test_turn_duration_is_randomized(self):
        rng = random.Random(2)
        values = {random_turn_seconds(rng, 0.6, 1.1) for _ in range(40)}

        self.assertGreater(len(values), 5)
        self.assertGreaterEqual(min(values), 0.6)
        self.assertLessEqual(max(values), 1.1)

    def test_turn_duration_respects_equal_bounds(self):
        rng = random.Random(2)

        self.assertEqual(random_turn_seconds(rng, 0.75, 0.75), 0.75)


class FacingMathTests(unittest.TestCase):
    def test_angle_between_wraps_around(self):
        current = Facing(0, 0, angle=350.0)

        self.assertAlmostEqual(turn_degrees_for(current, 10.0), 20.0, delta=0.01)

    def test_angle_between_is_signed(self):
        current = Facing(0, 0, angle=0.0)

        self.assertAlmostEqual(angle_between(current, Facing(0, 0, 90.0)), 90.0)
        self.assertAlmostEqual(angle_between(current, Facing(0, 0, 270.0)), -90.0)


if __name__ == "__main__":
    unittest.main()
