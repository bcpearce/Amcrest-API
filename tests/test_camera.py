"""Tests the camera"""


async def test_serial_number(camera) -> None:
    """Test serial number."""
    assert await camera.async_serial_number == "AMC00123456789ABCDEF"


async def test_lighting(camera, snapshot) -> None:
    """Test lighting."""
    assert await camera.async_lighting_config == snapshot


async def test_get_privacy_mode_on(camera) -> None:
    """Test Privacy mode, fixture was saved with it 'on'."""
    assert await camera.async_get_privacy_mode_on()


async def test_read_physical_config(camera, snapshot) -> None:
    """Test get physical config parameters unexpected to change."""
    assert await camera.async_read_physical_config() == snapshot


async def test_read_ptz_config(camera, snapshot) -> None:
    """Test get PTZ config."""
    assert await camera.async_ptz_preset_info == snapshot
