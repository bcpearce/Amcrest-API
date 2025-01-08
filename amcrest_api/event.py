import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum


class EventMessageType(StrEnum):
    """Event Message Types."""

    Heartbeat = "Heartbeat"
    VideoMotion = "VideoMotion"
    SmartMotionHuman = "SmartMotionHuman"
    SmartMotionVehicle = "SmartMotionVehicle"
    VideoLoss = "VideoLoss"
    VideoBlind = "VideoBlind"
    AlarmLocal = "AlarmLocal"
    StorageNotExist = "StorageNotExist"
    StorageFailure = "StorageFailure"
    StorageLowSpace = "StorageLowSpace"
    AlarmOutput = "AlarmOutput"
    AudioMutation = "AudioMutation"
    AudioAnomaly = "AudioAnomaly"
    CrossLineDetection = "CrossLineDetection"
    CrossRegionDetection = "CrossRegionDetection"
    LeftDetection = "LeftDetection"
    TakenAwayDetection = "TakenAwayDetection"
    SafetyAbnormal = "SafetyAbnormal"
    LoginFailure = "LoginFailure"


class EventAction(StrEnum):
    """Event Action."""

    Start = "Start"
    Stop = "Stop"
    Pulse = "pulse"


@dataclass
class EventMessageData:

    headers: dict[str, str]
    content: str | bytes

    def __init__(self, msg: str):
        lines = msg.splitlines()
        # Expect first line to be a boundary
        assert lines[0] == "--myboundary"
        # The next lines are headers until an empty line
        i = 1
        self.headers = dict[str, str]()
        while lines[i] != "":
            key, value = [x.strip() for x in lines[i].split(":")]
            self.headers[key] = value
            i += 1
        # Next is the content, concatenate the remaining lines
        self.content = "\r\n".join(lines[i + 1 :])


@dataclass
class EventBase:
    """Base class for Amcrest Events."""

    received_at: datetime
    event_type: EventMessageType
    action: EventAction
    raw_data: str | None

    def __init__(
        self,
        event_type: EventMessageType,
        action: EventAction,
        raw_data: str | None = None,
    ):
        self.event_type = event_type
        self.action = action
        self.raw_data = raw_data
        self.received_at = datetime.now(timezone.utc)

    def __repr__(self):
        return f"{self.event_type} {self.action} received at {self.received_at}"


class HeartbeatEvent(EventBase):
    """Heartbeat event."""

    def __init__(self):
        super().__init__(
            event_type=EventMessageType.Heartbeat, action=EventAction.Pulse
        )


class VideoMotionEvent(EventBase):
    """Video motion event."""

    id: list[int]
    region_name: list[str]

    def __init__(self, action: str, raw_data: str):
        super().__init__(EventMessageType.VideoMotion, action, raw_data)
        data = json.loads(raw_data)
        self.id = data.get("Id", [])
        self.region_name = data.get("RegionName", [])


def parse_event_message(content: str) -> EventBase:

    if content.strip() == EventMessageType.Heartbeat:
        return HeartbeatEvent()

    match = re.match(
        r"^Code=(\w+);action=(\w+);index=(\d+);data=(\{.*\})\s*$", content, re.DOTALL
    )
    event_type, action, index, data_raw = match.groups()

    if event_type == EventMessageType.VideoMotion:
        return VideoMotionEvent(action, data_raw)

    return EventBase(event_type, action, data_raw)
