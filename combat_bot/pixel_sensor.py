"""Turn a game-window screenshot into a normalized Observation using pixels."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from PIL import Image

from .combat_badge import in_combat
from .bar_finder import color_ratio, measure_bar
from .layout import UiLayout
from .models import Observation, TargetInfo
from .slots import auto_shot_out_of_range


@dataclass(frozen=True)
class CalibratedSensor:
    """Pixel reader driven by size-relative UI geometry."""

    layout: UiLayout = None  # type: ignore[assignment]
    matcher: object = None

    def __post_init__(self):
        if self.layout is None:
            object.__setattr__(self, "layout", UiLayout())

    def observe(self, image: Image.Image) -> Observation:
        size = image.size
        player_health = measure_bar(
            image,
            self.layout.player_health_box(size),
            self.layout.player_health_color,
        )
        mana = measure_bar(
            image,
            self.layout.player_mana_box(size),
            self.layout.mana_color,
        )
        name_box = self.layout.target_name_box(size)
        name_crop = image.crop(name_box)
        name_visible = color_ratio(name_crop, self.layout.target_name_color, 60) >= 0.02
        target_health = measure_bar(
            image,
            self.layout.target_health_box(size),
            self.layout.target_health_color,
        )

        target_name = None
        if name_visible and self.matcher is not None:
            target_name = self.matcher.match(name_crop).name

        # Дистанцию даёт цифра на слоте 1 (Auto Shot, 5-35 ярдов): белая -
        # цель в зоне, красная - вне зоны. Раньше здесь искалась красная
        # рамка слота, но игра рисует красной именно цифру, а иконка мигает,
        # поэтому читать рамку было бесполезно.
        slot_out_of_range = None
        if name_visible and target_health is not None:
            slot_out_of_range = auto_shot_out_of_range(image)

        return Observation(
            target=TargetInfo(
                name=target_name,
                exists=name_visible and target_health is not None,
                health_percent=target_health,
            ),
            player_health_percent=player_health,
            player_mana_percent=mana,
            slot_out_of_range=slot_out_of_range,
            in_combat=in_combat(image),
        )



class PixelSensor:
    """Backwards-compatible alias for the calibrated pixel reader."""

    def __init__(self, layout: Optional[UiLayout] = None, matcher=None):
        self.sensor = CalibratedSensor(layout or UiLayout(), matcher)

    def observe(self, image: Image.Image) -> Observation:
        return self.sensor.observe(image)
