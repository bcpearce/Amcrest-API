from dataclasses import dataclass


@dataclass
class PtzPresetData:
    """Data for PTZ Preset."""

    index: int
    name: str
