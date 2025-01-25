"""Tests for amcrest_api.event module."""

from pathlib import Path

from amcrest_api.event import (
    EventAction,
    HeartbeatEvent,
    VideoMotionEvent,
    parse_event_message,
)

FIXTURE_RESOURCE_PATH = Path("tests/fixtures/mock_event_multipart_responses")


def test_parse_video_motion_event():
    """Test parsing video motion event."""
    with open(FIXTURE_RESOURCE_PATH / "video_motion_stop.txt", "rb") as f:
        motion_event_content = f.read().decode(encoding="utf-8")

    event: VideoMotionEvent = parse_event_message(motion_event_content)
    assert isinstance(event, VideoMotionEvent)
    assert event.action == EventAction.Stop


def test_parse_heartbeat_event():
    """Test parsing heartbeat event."""
    with open(FIXTURE_RESOURCE_PATH / "heartbeat.txt", "rb") as f:
        heartbeat_event_content = f.read().decode(encoding="utf-8")

    event: HeartbeatEvent = parse_event_message(heartbeat_event_content)
    assert isinstance(event, HeartbeatEvent)
