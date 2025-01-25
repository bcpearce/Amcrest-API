"""Tests the camera"""

from typing import TYPE_CHECKING

import pytest
import yarl
from pytest_httpserver import HTTPServer, RequestMatcher

from amcrest_api.camera import Camera
from amcrest_api.const import ApiEndpoints, StreamType
from amcrest_api.error import UnsupportedStreamSubtype

if TYPE_CHECKING:
    from amcrest_api.ptz import PtzCapabilityData, PtzStatusData


async def test_serial_number(camera: Camera) -> None:
    """Test serial number."""
    assert await camera.async_serial_number == "AMC00123456789ABCDEF"


async def test_lighting(camera: Camera, snapshot) -> None:
    """Test lighting."""
    assert await camera.async_lighting_config == snapshot


async def test_get_privacy_mode_on(camera: Camera) -> None:
    """Test Privacy mode, fixture was saved with it 'on'."""
    assert await camera.async_get_privacy_mode_on()


async def test_get_smart_track_on(camera: Camera) -> None:
    """Test Smart track, fixture was saved with it 'off'."""
    assert not await camera.async_get_smart_track_on()


async def test_read_fixed_config(camera: Camera, snapshot) -> None:
    """Test get physical config parameters unexpected to change."""
    assert await camera.async_get_fixed_config() == snapshot


async def test_read_ptz_config(camera: Camera, snapshot) -> None:
    """Test get PTZ config."""
    assert await camera.async_ptz_preset_info == snapshot


async def test_get_rtsp_url(camera: Camera) -> None:
    """Terst getting the RTSP URL"""
    url = yarl.URL(await camera.async_get_rtsp_url())
    assert str(url.host) == "localhost"
    assert str(url.scheme) == "rtsp"
    assert url.user
    assert url.password
    url = yarl.URL(await camera.async_get_rtsp_url(subtype=StreamType.SUBSTREAM1))
    assert str(url.host) == "localhost"
    assert str(url.scheme) == "rtsp"
    assert url.user
    assert url.password
    assert url.query["subtype"] == "1"
    with pytest.raises(UnsupportedStreamSubtype):
        await camera.async_get_rtsp_url(subtype=StreamType.SUBSTREAM2)


async def test_get_ptz_status(camera: Camera) -> None:
    """Test getting PTZ status."""
    status: PtzStatusData = await camera.async_ptz_status
    assert status.position_pan == 242.7
    assert status.position_tilt == 9.6
    assert status.position_zoom == 1.0
    assert status.preset_id is None


async def test_get_ptz_capabilities(
    camera: Camera, mock_camera_server: HTTPServer, snapshot
) -> None:
    """Test getting PTZ capabilities."""
    caps: PtzCapabilityData = await camera.async_ptz_capabilities
    assert set(caps.supported_directions) == {"LEFT", "UP", "DOWN", "RIGHT"}
    assert caps.pan_min == 1
    assert caps.pan_max == 354
    assert caps.tilt_min == -4
    assert caps.tilt_max == 79
    assert caps == snapshot

    # and it's cached
    mock_camera_server.assert_request_made(
        RequestMatcher(uri=ApiEndpoints.PTZ), count=1
    )

    _ = await camera.async_ptz_capabilities

    mock_camera_server.assert_request_made(
        RequestMatcher(uri=ApiEndpoints.PTZ), count=1
    )
