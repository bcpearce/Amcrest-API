"""Tests the camera"""

from datetime import datetime
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


async def test_read_ptz_config_empty_presets(camera_no_ptz_presets: Camera) -> None:
    """Test get PTZ config when no presets are set."""
    presets = await camera_no_ptz_presets.async_ptz_preset_info
    assert len(presets) == 0


async def test_read_ptz_config_no_caps(camera_no_ptz_caps: Camera) -> None:
    """Test get PTZ config when no Capabilities."""

    caps = await camera_no_ptz_caps.async_ptz_capabilities
    assert not caps.pan
    assert not caps.tilt
    assert not caps.zoom
    assert not caps.tour


async def test_read_ptz_config_ip4m_1051(camera_ip4m_1051_ptz_caps: Camera) -> None:
    """Test get PTZ config based on IP4M-1051 model"""
    caps = await camera_ip4m_1051_ptz_caps.async_ptz_capabilities
    assert caps.zoom
    assert not caps.zoom_min


async def test_get_rtsp_url(camera: Camera) -> None:
    """Terst getting the RTSP URL"""
    url = await camera.async_get_rtsp_url()
    assert isinstance(url, yarl.URL)
    assert str(url.host) == "localhost"
    assert str(url.scheme) == "rtsp"
    assert url.user
    assert url.password
    url = await camera.async_get_rtsp_url(subtype=StreamType.SUBSTREAM1)
    assert isinstance(url, yarl.URL)
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


async def test_get_storage_info_names(camera: Camera) -> None:
    """Test getting storage info names."""
    storage_info_names = await camera.async_storage_list
    assert len(storage_info_names) == 3
    assert "/dev/sda0" in storage_info_names
    assert "/dev/sda1" in storage_info_names
    assert "/dev/mmc0" in storage_info_names


async def test_get_storage_info_names_no_storage(camera_no_storage: Camera) -> None:
    """Test getting storage info names."""
    storage_info_names = await camera_no_storage.async_storage_list
    assert len(storage_info_names) == 0
    storage_infos = await camera_no_storage.async_storage_info
    assert len(storage_infos) == 0


async def test_get_storage_info(camera: Camera, snapshot) -> None:
    """Test getting storage info."""
    storage_infos = await camera.async_storage_info
    assert len(storage_infos) == 1
    assert not storage_infos[0].cant_hot_plug
    assert storage_infos[0].total_bytes == 997703680
    assert storage_infos == snapshot


async def test_get_video_image_control(camera: Camera, snapshot) -> None:
    """Test getting video image control."""
    video_image_control = await camera.async_video_image_control
    assert video_image_control == snapshot


async def test_get_video_in_day_night(camera: Camera, snapshot) -> None:
    """Test getting video in day night."""
    video_in_day_night = await camera.async_get_video_in_day_night()
    assert video_in_day_night == snapshot


async def test_get_current_time(camera: Camera) -> None:
    """Test getting current time."""
    current_time = await camera.async_get_current_time()
    assert current_time == datetime(2011, 7, 3, 21, 2, 32)


async def test_camera_without_privacy_mode(camera_no_privacy_mode: Camera) -> None:
    """Test camera without privacy mode."""
    config = await camera_no_privacy_mode.async_get_fixed_config()
    assert config.privacy_mode_available is False


async def test_camera_without_smart_track(camera_no_smart_track: Camera) -> None:
    """Test camera without smart tracking."""
    config = await camera_no_smart_track.async_get_fixed_config()
    assert config.smart_track_available is False
