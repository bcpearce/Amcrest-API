"""Classes for camra imaging."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum, IntFlag, StrEnum
from typing import Any

from .utils import indexed_dict_to_list


class Rotate90Flag(IntFlag):
    """Rotation flags."""

    NO_ROTATE = 0
    CLOCKWISE_90 = 1
    COUNTERCLOCKWISE_90 = 2


@dataclass(kw_only=True)
class VideoImageControl:
    """Video Image Control (Rotation/Flip)"""

    flip: bool = False
    freeze: bool = False
    mirror: bool = False
    rotate_90: Rotate90Flag = Rotate90Flag.NO_ROTATE
    stable: int = 0

    @staticmethod
    def create_from_response(response: dict[str, Any]) -> list[VideoImageControl]:
        """Create from a Video Image Control response."""
        return [
            VideoImageControl(
                flip=control.get("Flip", "false") == "true",
                freeze=control.get("Freeze", "false") == "true",
                mirror=control.get("Mirror", "false") == "true",
                rotate_90=Rotate90Flag(int(control.get("Rotate90", "0"))),
                stable=int(control.get("Stable", "0")),
            )
            for control in indexed_dict_to_list(response["VideoImageControl"])
        ]


class VideoMode(StrEnum):
    """Selections for video modes."""

    COLOR = "Color"
    BRIGHTNESS = "Brightness"
    BLACK_WHITE = "BlackWhite"
    PHOTORESISTOR = "Photoresistor"
    GAIN = "Gain"


class Sensitivity(IntEnum):
    """Sensitivity settings."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3


class ConfigNo(IntEnum):
    """Video Profile Config Index"""

    DAY = 0
    NIGHT = 1
    NORMAL = 2


CONFIG_NO_DICT = {
    ConfigNo.DAY: "Day",
    ConfigNo.NIGHT: "Night",
    ConfigNo.NORMAL: "Normal/General",
}


class VideoDayNightType(StrEnum):
    """Video Day/Night Types"""

    ELECTRON = "Electron"
    MECHANISM = "Mechanism"
    NIGHT_ICR = "NightICR"
    AUTO = "Auto"


@dataclass(kw_only=True)
class VideoDayNight:
    """Video Day/Night Settings"""

    delay_seconds: int
    mode: VideoMode
    sensitivity: Sensitivity
    type: VideoDayNightType

    @staticmethod
    def create_from_response(
        response: dict[str, Any],
    ) -> list[list[VideoDayNight]]:
        """Create from API response."""
        return [
            [
                VideoDayNight(
                    delay_seconds=int(config["Delay"]),
                    mode=VideoMode(config["Mode"]),
                    sensitivity=Sensitivity(int(config["Sensitivity"])),
                    type=VideoDayNightType(config["Type"]),
                )
                for config in indexed_dict_to_list(video_in_day_night)
            ]
            for video_in_day_night in indexed_dict_to_list(response["VideoInDayNight"])
        ]


class LightingMode(StrEnum):
    """Lighting Modes."""

    MANUAL = "Manual"
    AUTO = "Auto"
    OFF = "Off"


@dataclass(kw_only=True)
class Light:
    """Light."""

    angle: int = 50
    light: int


@dataclass(kw_only=True)
class Lighting:
    """Lighting config."""

    mode: LightingMode
    correction: int | None = None
    # far_light: int
    middle_light: Light | None
    # near_light: int
    light_type: str | None = None
    sensitivity: Sensitivity | None = None

    @staticmethod
    def create_from_response(
        response: dict[str, Any],
    ) -> list[list[list[Lighting]]]:
        """Create from API response."""
        return [
            [
                [
                    Lighting(
                        mode=light["Mode"],
                        correction=light["Correction"],
                        # far_light=int(light["FarLight"][0]["Light"]),
                        middle_light=Light(
                            light=int(light["MiddleLight"][0]["Light"]),
                            angle=int(light["MiddleLight"][0].get("Angle", 50)),
                        ),
                        light_type=light.get("LightType"),
                        # near_light=int(light["NearLight"][0]["Light"]),
                        sensitivity=Sensitivity(int(light["Sensitive"])),
                    )
                    for light in indexed_dict_to_list(config)
                ]
                for config in indexed_dict_to_list(lighting)
            ]
            for lighting in indexed_dict_to_list(response["Lighting_V2"])
        ]
