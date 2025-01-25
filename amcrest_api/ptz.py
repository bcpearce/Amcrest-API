"""PTZ Helpers."""

from __future__ import annotations

from dataclasses import KW_ONLY, dataclass, field
from enum import StrEnum
from typing import Any


@dataclass(frozen=True)
class PtzPresetData:
    """Data for PTZ preset."""

    index: int
    name: str


class Direction(StrEnum):
    """Directions."""

    UP = "UP"
    DOWN = "DOWN"
    LEFT = "LEFT"
    RIGHT = "RIGHT"
    LEFTUP = "LEFTUP"
    RIGHTUP = "RIGHTUP"
    LEFTDOWN = "LEFTDOWN"
    RIGHTDOWN = "RIGHTDOWN"


ALL_DIRECTIONS = set(Direction)


@dataclass(kw_only=True)
class PtzCapabilityData:
    """Data for PTZ capabilities."""

    pan: bool = False
    tilt: bool = False
    zoom: bool = False
    preset: bool = False
    tour: bool = False

    pan_min: float = 0.0
    pan_max: float = 0.0
    pan_speed_min: int = 1
    pan_speed_max: int = 1

    tilt_min: float = 0.0
    tilt_max: float = 0.0
    tilt_speed_min: int = 1
    tilt_speed_max: int = 1

    zoom_min: float = 1.0
    zoom_max: float = 1.0

    preset_min: int = 0
    preset_max: int = 0

    tour_min: int = 0
    tour_max: int = 0

    supported_directions: list[Direction] = field(default_factory=list[Direction])

    @staticmethod
    def create_from_response(response: dict[str, Any]) -> PtzCapabilityData:
        """Create from a PTZ capabilities response."""
        caps: dict[str, Any] = response["caps"]

        def check_true(key: str) -> bool:
            return str(caps[key]).lower() == "true"

        ret = PtzCapabilityData(
            pan=check_true("Pan"),
            tilt=check_true("Tile"),  # the key is a typo in the API
            zoom=check_true("Zoom"),
            preset=check_true("Preset"),
        )
        if ret.pan:
            ret.pan_min = float(caps["PtzMotionRange"]["HorizontalAngle"][0])
            ret.pan_max = float(caps["PtzMotionRange"]["HorizontalAngle"][1])
            ret.pan_speed_min = int(caps["PanSpeedMin"])
            ret.pan_speed_max = int(caps["PanSpeedMax"])
            if ret.pan_min > ret.pan_max:
                ret.pan_min, ret.pan_max = ret.pan_max, ret.pan_min
        if ret.tilt:
            ret.tilt_min = float(caps["PtzMotionRange"]["VerticalAngle"][0])
            ret.tilt_max = float(caps["PtzMotionRange"]["VerticalAngle"][1])
            ret.pan_speed_min = int(caps["PanSpeedMin"])
            ret.pan_speed_max = int(caps["PanSpeedMax"])
            if ret.tilt_min > ret.tilt_max:
                ret.tilt_min, ret.tilt_max = ret.tilt_max, ret.tilt_min
        if ret.zoom:
            ret.zoom_min = float(caps["ZoomMin"])
            ret.zoom_max = float(caps["ZoomMax"])
        if ret.preset:
            ret.preset_min = int(caps["PresetMin"])
            ret.preset_max = int(caps["PresetMax"])
        if ret.tour:
            ret.tour_min = int(caps["TourMin"])
            ret.tour_max = int(caps["TourMax"])
        ret.supported_directions = sorted(
            list[Direction](
                ALL_DIRECTIONS ^ set[Direction](caps["UnSupportDirections"].values())  # type: ignore
            )
        )
        return ret


@dataclass(kw_only=True)
class PtzStatusData:
    """Data for PTZ status."""

    action: str | None
    move_status: str
    zoom_status: str
    preset_id: int | None = None
    sequence: int | None = None
    position_pan: float
    position_tilt: float
    position_zoom: float
    pts: int | None
    utc: int | None

    @staticmethod
    def create_from_response(response: dict[str, Any]) -> PtzStatusData:
        """Create from a PTZ Status response."""
        ptz_status_dict: dict[str, Any] = response["status"]  # expect nested dict
        if ptz_status_dict.get("PresetID") == "0":
            preset_id = None
        else:
            preset_id = int(ptz_status_dict["PresetID"])
        if ptz_status_dict.get("Sequence") == "0":
            sequence = None
        else:
            sequence = int(ptz_status_dict["Sequence"])
        return PtzStatusData(
            action=ptz_status_dict.get("Action"),
            move_status=ptz_status_dict["MoveStatus"],
            zoom_status=ptz_status_dict["ZoomStatus"],
            preset_id=preset_id,
            sequence=sequence,
            # Typo in API "Postion instead of Position" # codespell:ignore
            position_pan=float(ptz_status_dict["Postion"][0]),  # codespell:ignore
            position_tilt=float(ptz_status_dict["Postion"][1]),  # codespell:ignore
            position_zoom=float(ptz_status_dict["Postion"][2]),  # codespell:ignore
            pts=int(str(ptz_status_dict.get("PTS"))),
            utc=int(str(ptz_status_dict.get("UTC"))),
        )


@dataclass(kw_only=True)
class PtzRelativeMove:
    """Class for a relative move. All values are normalized from [-1,1]."""

    _caps: PtzCapabilityData | None = None
    _horizontal: float | None = None
    _vertical: float | None = None
    _zoom: float | None = None
    _channel: int = 1

    def __init__(
        self,
        *,
        caps: PtzCapabilityData | None = None,
        horizontal: float | None = None,
        vertical: float | None = None,
        zoom: float | None = None,
        channel: int = 1,
    ):
        self.caps = caps
        self.horizontal = horizontal
        self.vertical = vertical
        self.zoom = zoom
        self.channel = channel

    @property
    def caps(self) -> PtzCapabilityData | None:
        """PTZ capabilities."""
        return self._caps

    @caps.setter
    def caps(self, value: PtzCapabilityData):
        self._caps = value

    @property
    def horizontal(self) -> float | None:
        """Relative horizontal movement, [-1,1] inclusive"""
        return self._horizontal

    @horizontal.setter
    def horizontal(self, value: float | None) -> None:
        if value is None or -1.0 <= value <= 1.0:
            self._horizontal = value
        else:
            raise ValueError("Must be between -1.0 and 1.0 inclusive")

    @property
    def vertical(self) -> float | None:
        """Relative vertical movement, [-1,1] inclusive"""
        return self._vertical

    @vertical.setter
    def vertical(self, value: float | None) -> None:
        if value is None or -1.0 <= value <= 1.0:
            self._vertical = value
        else:
            raise ValueError("Must be between -1.0 and 1.0 inclusive")

    @property
    def zoom(self) -> float | None:
        """Relative zoom movement, [-1,1] inclusive"""
        return self._zoom

    @zoom.setter
    def zoom(self, value: float | None) -> None:
        if value is None or -1.0 <= value <= 1.0:
            self._zoom = value
        else:
            raise ValueError("Must be between -1.0 and 1.0 inclusive")

    @property
    def channel(self) -> int:
        """PTZ channel."""
        return self._channel

    @channel.setter
    def channel(self, value: int) -> None:
        self._channel = int(value)

    def get_query_dict(self) -> dict[str, Any]:
        """
        Get a dictionary that can be passed as query parameters to the API Endpoint.

        arg1 is horizontal
        arg2 is vertical
        arg3 is zoom
        """
        ret: dict[str, Any] = {
            "action": "moveRelatively",
            "channel": self.channel,
            "arg1": 0,
            "arg2": 0,
            "arg3": 0,
        }
        if self.horizontal is not None:
            ret["arg1"] = self.horizontal
        if self.vertical is not None:
            ret["arg2"] = self.vertical
        if self.zoom is not None:
            ret["arg3"] = self.zoom
        return ret


@dataclass
class PtzBasicMove:
    """Class for starting PTZ motion."""

    direction: Direction
    _: KW_ONLY
    caps: PtzCapabilityData | None = None
    speed: int = 1
    vertical_speed: int | None = None
    horizontal_speed: int | None = None
    channel: int = 1

    def get_start_query_dict(self) -> dict[str, Any]:
        """
        Get a dictionary that can be passed as query parameters to the API Endpoint.

        arg1 is vertical speed on combo moves
        arg2 is vertical or horizontal speed on single moves
        arg3 is 0
        """
        ret: dict[str, Any] = {
            "action": "start",
            "channel": self.channel,
            "arg1": 0,
            "arg2": 0,
            "arg3": 0,
        }
        if self.direction in [
            Direction.LEFTDOWN,
            Direction.RIGHTDOWN,
            Direction.RIGHTUP,
            Direction.LEFTUP,
        ]:
            ret["arg1"] = self.vertical_speed or self.speed
            ret["arg2"] = self.horizontal_speed or self.speed

        elif self.direction in [
            Direction.LEFT,
            Direction.RIGHT,
            Direction.UP,
            Direction.DOWN,
        ]:
            ret["arg1"] = 0
            ret["arg2"] = self.speed
        ret["code"] = self.direction.title()
        ret["arg3"] = 0
        return ret

    def get_stop_query_dict(self) -> dict[str, Any]:
        """Get the stop query dict."""
        return {
            "action": "stop",
            "channel": self.channel,
            "code": self.direction.title(),
            "arg1": 0,
            "arg2": 0,
            "arg3": 0,
        }


@dataclass(kw_only=True)
class PtzAccuratePosition:
    """Class for Accurate position setting."""

    caps: PtzCapabilityData | None = None
    horizontal_position: float | None = None
    vertical_position: float | None = None
    zoom: float | None = None
    channel: int = 1

    def get_query_dict(self) -> dict[str, Any]:
        """
        Get a dictionary to be passed as query parameters to the Accurate Position API

        arg1 horizonatal position
        arg2 vertical position
        arg3 zoom
        """
        if self.caps is None:
            raise RuntimeError(
                "Cannot get query dict unless PTZ capabilities are assigned."
            )

        ret: dict[str, Any] = {
            "action": "moveAbsolutely",
            "channel": self.channel,
            "arg1": 0,
            "arg2": 0,
            "arg3": 0,
        }
        if self.horizontal_position is not None and self.caps.pan:
            if self.caps.pan_min <= self.horizontal_position <= self.caps.pan_max:
                ret["arg1"] = (self.horizontal_position - 180.0) / 180.0
            else:
                raise ValueError(
                    f"Horizontal move degrees must be in the range [{self.caps.pan_min}, {self.caps.pan_max}, but it was {self.horizontal_position}]"  # noqa: E501
                )
        if self.vertical_position is not None and self.caps.tilt:
            if self.caps.tilt_min <= self.vertical_position <= self.caps.tilt_max:
                ret["arg2"] = self.vertical_position / 180.0
            else:
                raise ValueError(
                    f"Vertical move degrees must be in the range [{self.caps.tilt_min}, {self.caps.tilt_max}, but it was {self.vertical_position}]"  # noqa: E501
                )
        if self.zoom is not None and self.caps.zoom:
            if self.caps.zoom_min <= self.zoom <= self.caps.zoom_max:
                zoom_range = self.caps.zoom_max - self.caps.zoom_min
                zoom_mid = (self.caps.zoom_max + self.caps.zoom_min) / 2.0
                normed = (self.zoom - zoom_mid) / (zoom_range / 2)
                ret["arg3"] = normed
            else:
                raise ValueError(
                    f"Zoom must be in the range [{self.caps.zoom_min}, {self.caps.zoom_max}, but it was {self.zoom}]"  # noqa: E501
                )
        return ret
