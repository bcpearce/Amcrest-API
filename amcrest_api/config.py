from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Config:
    """A Config containing elements unlikely to change during the API Session."""

    machine_name: str
    network: dict[str, Any]
    serial_number: str
    session_physical_address: str
    supported_events: list[str]
    software_version: str
