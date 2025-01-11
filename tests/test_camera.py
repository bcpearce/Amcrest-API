"""Tests the camera"""


async def test_serial_number(camera) -> None:
    """Test serial number."""
    assert await camera.async_serial_number == "AMC0585C9C2FFDD9E2"
