"""Constants."""

from enum import StrEnum


class EventMessageTypes(StrEnum):
    """Event Message Types."""

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


class ApiEndpoints(StrEnum):
    """API Endpoints."""

    ConfigManager = "/cgi-bin/configManager.cgi"
    Encode = "/cgi-bin/encode.cgi"
    EventManager = "/cgi-bin/eventManager.cgi"
    MagicBox = "/cgi-bin/magicBox.cgi"
