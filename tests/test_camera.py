"""Tests the camera"""

import yarl

from amcrest_api.camera import Camera


async def test_serial_number(camera: Camera) -> None:
    """Test serial number."""
    assert await camera.async_serial_number == "AMC00123456789ABCDEF"


async def test_lighting(camera: Camera, snapshot) -> None:
    """Test lighting."""
    assert await camera.async_lighting_config == snapshot


async def test_get_privacy_mode_on(camera: Camera) -> None:
    """Test Privacy mode, fixture was saved with it 'on'."""
    assert await camera.async_get_privacy_mode_on()


async def test_read_physical_config(camera: Camera, snapshot) -> None:
    """Test get physical config parameters unexpected to change."""
    assert await camera.async_read_physical_config() == snapshot


async def test_read_ptz_config(camera: Camera, snapshot) -> None:
    """Test get PTZ config."""
    assert await camera.async_ptz_preset_info == snapshot


async def test_get_rtsp_url(camera: Camera) -> None:
    """Terst getting the RTSP URL"""
    url = yarl.URL(camera.rtsp_url)
    assert str(url.host) == "localhost"
    assert str(url.scheme) == "rtsp"
    assert url.user
    assert url.password
