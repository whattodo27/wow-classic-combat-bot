"""Показать, что сенсор видит на живом окне: цель, дистанцию, бой."""

from __future__ import annotations

from combat_bot.capture import WindowCapture
from combat_bot.combat_badge import in_combat
from combat_bot.name_matcher import NameMatcher
from combat_bot.pixel_sensor import PixelSensor
from combat_bot.slots import read_slot, scan_slots


def main() -> int:
    capture = WindowCapture("World of Warcraft")
    capture.focus()

    try:
        matcher = NameMatcher.load()
    except Exception:
        matcher = None
    print(f"шаблонов имён: {0 if matcher is None else len(matcher.templates)}")

    sensor = PixelSensor(matcher=matcher)

    for index in range(6):
        image = capture.capture_image()
        if image is None:
            print("окно не найдено")
            return 1

        observation = sensor.observe(image)
        slot1 = read_slot(image, 1)
        slot2 = read_slot(image, 2)

        print(
            f"[{index}] цель={observation.target.exists} "
            f"имя={observation.target.name!r} "
            f"hp_цели={observation.target.health_percent} "
            f"hp_игрока={observation.player_health_percent} "
            f"вне_зоны={observation.slot_out_of_range} "
            f"бой={observation.in_combat}"
        )
        print(
            f"      слот1 красных={slot1.red_pixels:>3} "
            f"белых={slot1.white_pixels:>3} -> {slot1.is_red=}, {slot1.is_white=}"
        )
        print(
            f"      слот2 красных={slot2.red_pixels:>3} "
            f"белых={slot2.white_pixels:>3} -> {slot2.is_red=}, {slot2.is_white=}"
        )
        image.save(f"live_{index}.jpg", quality=90)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
