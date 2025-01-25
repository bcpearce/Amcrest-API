"""Constants."""

from enum import IntEnum, StrEnum


class ApiEndpoints(StrEnum):
    """API Endpoints."""

    CONFIG_MANAGER = "/cgi-bin/configManager.cgi"
    ENCODE = "/cgi-bin/encode.cgi"
    EVENT_MANAGER = "/cgi-bin/eventManager.cgi"
    MAGIC_BOX = "/cgi-bin/magicBox.cgi"
    PTZ = "/cgi-bin/ptz.cgi"
    REALTIME_STREAM = "/cam/realmonitor"
    SNAPSHOT = "/cgi-bin/snapshot.cgi"


class StreamType(IntEnum):
    """Stream Types."""

    MAIN = 0
    SUBSTREAM1 = 1
    SUBSTREAM2 = 2
