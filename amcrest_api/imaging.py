"""Classes for camra imaging."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum, IntFlag, StrEnum
from typing import Any

from .utils import indexed_dict_to_list


class Rotate90Flag(IntFlag):
    NO_ROTATE = 0
    CLOCKWISE_90 = 1
    COUNTERCLOCKWISE_90 = 2


@dataclass(kw_only=True)
class VideoImageControl:
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


class VideoSensitivity(IntEnum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3


class ConfigNo(IntEnum):
    DAY = 0
    NIGHT = 1
    NORMAL = 2


CONFIG_NO_DICT = {
    ConfigNo.DAY: "Day",
    ConfigNo.NIGHT: "Night",
    ConfigNo.NORMAL: "Normal/General",
}


class VideoDayNightType(StrEnum):
    ELECTRON = "Electron"
    MECHANISM = "Mechanism"
    NIGHT_ICR = "NightICR"
    AUTO = "Auto"


@dataclass(kw_only=True)
class VideoDayNight:
    delay_seconds: int
    mode: VideoMode
    sensitivity: VideoSensitivity
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
                    sensitivity=VideoSensitivity(int(config["Sensitivity"])),
                    type=VideoDayNightType(config["Type"]),
                )
                for config in indexed_dict_to_list(video_in_day_night)
            ]
            for video_in_day_night in indexed_dict_to_list(response["VideoInDayNight"])
        ]
