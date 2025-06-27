"""Constants."""

from enum import IntEnum, StrEnum


class ApiEndpoints(StrEnum):
    """API Endpoints."""

    CONFIG_MANAGER = "/cgi-bin/configManager.cgi"
    ENCODE = "/cgi-bin/encode.cgi"
    EVENT_MANAGER = "/cgi-bin/eventManager.cgi"
    GLOBAL = "/cgi-bin/global.cgi"
    MAGIC_BOX = "/cgi-bin/magicBox.cgi"
    PTZ = "/cgi-bin/ptz.cgi"
    REALTIME_STREAM = "/cam/realmonitor"
    SNAPSHOT = "/cgi-bin/snapshot.cgi"
    STORAGE_DEVICE = "/cgi-bin/storageDevice.cgi"


class StreamType(IntEnum):
    """Stream Types."""

    MAIN = 0
    SUBSTREAM1 = 1
    SUBSTREAM2 = 2


class StreamTypeName(StrEnum):
    """Stream Type Names."""

    MAIN = "Main"
    SUBSTREAM1 = "Sub Stream 1"
    SUBSTREAM2 = "Sub Stream 2"


STREAM_TYPE_DICT = {
    StreamType.MAIN: StreamTypeName.MAIN,
    StreamType.SUBSTREAM1: StreamTypeName.SUBSTREAM1,
    StreamType.SUBSTREAM2: StreamTypeName.SUBSTREAM2,
}
