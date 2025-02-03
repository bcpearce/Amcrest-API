"""Classes for camra imaging."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntFlag
from typing import Any

from .utils import indexed_dict_to_list


class Rotate90Flag(IntFlag):
    NO_ROTATE = 0
    CLOCKWISE_90 = 1
    COUNTERCLOCKWISE_90 = 2


@dataclass(kw_only=True)
class VideoImageControl:
    flip: bool
    freeze: bool
    mirror: bool
    rotate_90: Rotate90Flag
    stable: int

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
