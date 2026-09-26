"""Поиск цели только в конусе перед персонажем.

Задача: бот не должен выбирать цель позади или сбоку, иначе игра пишет
«You are facing the wrong way!» и атака не проходит. Поэтому цели ищутся
только внутри конуса, выходящего из позиции персонажа.

Геометрия конуса взята с рисунка пользователя: угол раствора около 30
градусов в каждую сторону от вертикали, то есть 60 градусов всего.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Optional

# Угол раствора конуса в каждую сторону от направления взгляда.
DEFAULT_HALF_ANGLE = 30.0

# Точка, из которой выходит конус: позиция персонажа на экране.
DEFAULT_APEX_RATIO = (0.5, 0.78)

# Смещение вершины конуса вперёд, чтобы точка самого персонажа не попадала
# в зону проверки.
APEX_FORWARD_OFFSET = 0.045


@dataclass(frozen=True)
class Nameplate:
    """Имя и полоса здоровья существа над ним."""

    x: int
    y: int
    width: int
    name: str = ""

    @property
    def center_x(self) -> int:
        return self.x + self.width // 2


@dataclass(frozen=True)
class Facing:
    """Направление взгляда персонажа на экране."""

    x: int
    y: int
    angle: float  # в градусах, 0 = вверх по экрану, по часовой стрелке


def apex_position(size: tuple[int, int], ratio=DEFAULT_APEX_RATIO) -> tuple[int, int]:
    """Вершина конуса - точка, от которой смотрит персонаж."""
    width, height = size
    return (int(width * ratio[0]), int(height * ratio[1]))


def inside_cone(
    point: tuple[int, int],
    facing: Facing,
    size: tuple[int, int],
    half_angle: float = DEFAULT_HALF_ANGLE,
) -> bool:
    """Попадает ли точка в конус перед персонажем.

    Направление конуса задаётся ``facing.angle``: 0 - прямо вверх по
    экрану, положительные значения - вправо по часовой стрелке.
    """
    # Переводим точку в систему координат персонажа: ось Y направлена
    # вперёд по взгляду, поэтому угол смещения считается от неё.
    dx = point[0] - facing.x
    dy = facing.y - point[1]  # вверх по экрану - положительное значение

    if dy <= 0:
        return False  # цель ниже или на уровне персонажа

    # Поворот камеры смещает конус: компенсируем угол взгляда.
    angle = math.degrees(math.atan2(dx, dy)) - facing.angle
    angle = (angle + 180.0) % 360.0 - 180.0
    return abs(angle) <= half_angle


def distance_to_apex(point: tuple[int, int], facing: Facing) -> float:
    """Расстояние от вершины конуса до точки."""
    return math.hypot(point[0] - facing.x, facing.y - point[1])


def angle_between(first: Facing, second: Facing) -> float:
    """Разница направлений в градусах, сведённая к диапазону -180..180."""
    delta = (second.angle - first.angle) % 360.0
    if delta > 180.0:
        delta -= 360.0
    return delta


def pick_target_in_cone(
    plates: list[Nameplate],
    facing: Facing,
    size: tuple[int, int],
    half_angle: float = DEFAULT_HALF_ANGLE,
) -> Optional[Nameplate]:
    """Самая близкая к персонажу цель внутри конуса."""
    candidates = [
        plate
        for plate in plates
        if inside_cone((plate.center_x, plate.y), facing, size, half_angle)
    ]
    if not candidates:
        return None
    return min(
        candidates,
        key=lambda plate: distance_to_apex((plate.center_x, plate.y), facing),
    )


def turn_degrees_for(current: Facing, desired: float) -> float:
    """Сколько градусов довернуть до нужного направления."""
    return angle_between(current, Facing(current.x, current.y, desired))


def choose_turn_direction(
    rng: random.Random,
    last_direction: Optional[int] = None,
    avoid_repeats: int = 2,
    history: Optional[list[int]] = None,
) -> int:
    """Выбрать направление поворота с защитой от метаний.

    Идея пользователя: если только что повернули влево, следующие два
    поворота не должны быть влево, иначе бот дёргается туда-сюда.

    ``history`` хранит последние направления, чтобы правило работало и
    при нескольких шагах подряд.
    """
    recent = list(history or [])
    banned = set(recent[-avoid_repeats:]) if avoid_repeats else set()

    options = [direction for direction in (1, -1) if direction not in banned]
    if not options:
        options = [1, -1]
    return rng.choice(options)


def random_turn_seconds(
    rng: random.Random,
    min_seconds: float,
    max_seconds: float,
) -> float:
    """Рандомная длительность поворота, чтобы движение не было ровным."""
    if max_seconds <= min_seconds:
        return max(0.0, min_seconds)
    return rng.uniform(min_seconds, max_seconds)
