"""Constants."""

from enum import IntEnum, StrEnum


class ApiEndpoints(StrEnum):
    """API Endpoints."""

    ConfigManager = "/cgi-bin/configManager.cgi"
    Encode = "/cgi-bin/encode.cgi"
    EventManager = "/cgi-bin/eventManager.cgi"
    MagicBox = "/cgi-bin/magicBox.cgi"
    RealtimeStream = "/cam/realmonitor"
    Snapshot = "/cgi-bin/snapshot.cgi"


class StreamType(IntEnum):
    """Stream Types."""

    Main = 0
    SubStream1 = 1
    SubStream2 = 2
