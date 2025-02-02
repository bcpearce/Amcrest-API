"""Config for information unlikely to change during a session."""

from dataclasses import dataclass
from typing import Any

from amcrest_api.const import StreamType, StreamTypeName

from .event import EventMessageType
from .ptz import PtzCapabilityData


@dataclass(frozen=True)
class Config:
    """A Config containing elements unlikely to change during the API Session."""

    device_type: str
    hardware_version: str
    machine_name: str
    max_extra_stream: StreamType
    network: dict[str, Any]
    ptz_capabilities: PtzCapabilityData
    serial_number: str
    session_physical_address: str
    supported_events: list[EventMessageType]
    supported_streams: dict[StreamType, StreamTypeName]
    software_version: str
