"""Configuration for Tests."""

import json
from collections.abc import AsyncGenerator  # pylint: disable=no-name-in-module
from pathlib import Path

import httpx
import pytest
import yarl
from pytest_httpserver import HTTPServer
from pytest_httpserver.httpserver import HandlerType

from amcrest_api.camera import Camera


@pytest.fixture
def mock_json_response():
    """Mock json response."""
    with open("tests/fixtures/MockJsonPayload.json", "rb") as f:
        yield httpx.Response(200, json=json.load(f))


@pytest.fixture
def mock_key_value_with_table_response():
    """Key Value response with table."""
    with open("tests/fixtures/MockKeyValuePayloadTable.txt", encoding="utf-8") as f:
        # ensure line endings
        text = "\r\n".join(line.strip() for line in f.readlines())
        yield httpx.Response(200, text=text)


@pytest.fixture
def mock_key_value_with_array_response():
    """Key Value response with array."""
    with open("tests/fixtures/MockKeyValuePayloadWithArray.txt", encoding="utf-8") as f:
        # ensure line endings
        text = "\r\n".join(line.strip() for line in f.readlines())
        yield httpx.Response(200, text=text)


@pytest.fixture
def mock_key_value_response():
    """Key value response."""
    return httpx.Response(200, text="sn=AMC0\r\n")


def _load_fixture(
    path: Path | str, server: HTTPServer, *, handlerType=HandlerType.PERMANENT
):
    with open(path, "rb") as f:
        d = json.load(f)
    url = yarl.URL(d["raw_path"])
    server.expect_request(url.path, query_string=url.query_string).respond_with_data(
        d["content"]
    )


@pytest.fixture(name="mock_camera_server")
def mock_camera_server_fixture(httpserver: HTTPServer) -> HTTPServer:
    """Mock camera server."""

    fixture_path = Path("tests/fixtures/mock_responses")
    for path in fixture_path.iterdir():
        _load_fixture(path, httpserver)

    return httpserver


@pytest.fixture(name="mock_camera_server_no_storage")
def mock_camera_server_no_storage_fixture(httpserver: HTTPServer) -> HTTPServer:
    """Mock camera server with no storage devices."""

    empty_storage_path = Path(
        "tests/fixtures/mock_responses_alt/storage_device_names_empty.json"
    )
    _load_fixture(empty_storage_path, httpserver, handlerType=HandlerType.ORDERED)

    fixture_path = Path("tests/fixtures/mock_responses")
    for path in fixture_path.iterdir():
        _load_fixture(path, httpserver)

    return httpserver


@pytest.fixture(name="mock_camera_server_no_ptz_presets")
def mock_camera_server_no_ptz_presets_fixture(httpserver: HTTPServer) -> HTTPServer:
    """Mock camera server with no storage devices."""

    empty_storage_path = Path(
        "tests/fixtures/mock_responses_alt/ptz_config_presets_empty.json"
    )
    _load_fixture(empty_storage_path, httpserver, handlerType=HandlerType.ORDERED)

    fixture_path = Path("tests/fixtures/mock_responses")
    for path in fixture_path.iterdir():
        _load_fixture(path, httpserver)

    return httpserver


@pytest.fixture(name="mock_camera_server_no_ptz_caps")
def mock_camera_server_no_ptz_caps_fixture(httpserver: HTTPServer) -> HTTPServer:
    """Mock camera server with no PTZ caps."""

    empty_caps_path = Path(
        "tests/fixtures/mock_responses_alt/ptz_capabilities_no_PanTiltZoom.json"
    )
    _load_fixture(empty_caps_path, httpserver, handlerType=HandlerType.ORDERED)

    fixture_path = Path("tests/fixtures/mock_responses")
    for path in fixture_path.iterdir():
        _load_fixture(path, httpserver)

    return httpserver


@pytest.fixture(name="mock_camera_server_no_privacy_mode")
def mock_camera_server_no_privacy_mode_fixture(httpserver: HTTPServer) -> HTTPServer:
    """Mock camera server with no Privacy Mode caps."""

    url = yarl.URL("/cgi-bin/configManager.cgi?action=getConfig&name=LeLensMask")
    httpserver.expect_request(
        url.path, query_string=url.query_string
    ).respond_with_data(
        "Error\nBad Request!\n",
        status=400,
    )

    fixture_path = Path("tests/fixtures/mock_responses")
    for path in fixture_path.iterdir():
        _load_fixture(path, httpserver)

    return httpserver


@pytest.fixture(name="mock_camera_server_no_smart_track")
def mock_camera_server_no_smart_track_fixture(httpserver: HTTPServer) -> HTTPServer:
    """Mock camera server with no Smart Track caps."""

    url = yarl.URL("/cgi-bin/configManager.cgi?action=getConfig&name=LeSmartTrack")
    httpserver.expect_request(
        url.path, query_string=url.query_string
    ).respond_with_data(
        "Error\nBad Request!\n",
        status=400,
    )

    fixture_path = Path("tests/fixtures/mock_responses")
    for path in fixture_path.iterdir():
        _load_fixture(path, httpserver)

    return httpserver


@pytest.fixture
async def camera(mock_camera_server: HTTPServer) -> AsyncGenerator[Camera]:
    """Fixture which communicates with mock camera server."""
    async with Camera(
        mock_camera_server.host,
        "testuser",
        "testpassword",
        port=mock_camera_server.port,
        verify=False,
    ) as cam:
        yield cam


@pytest.fixture
async def camera_no_storage(
    mock_camera_server_no_storage: HTTPServer,
) -> AsyncGenerator[Camera]:
    """Fixture which communicates with mock camera server and has no storage."""
    async with Camera(
        mock_camera_server_no_storage.host,
        "testuser",
        "testpassword",
        port=mock_camera_server_no_storage.port,
        verify=False,
    ) as cam:
        yield cam


@pytest.fixture
async def camera_no_ptz_presets(
    mock_camera_server_no_ptz_presets: HTTPServer,
) -> AsyncGenerator[Camera]:
    """Fixture which communicates with mock camera server and has no PTZ presets."""
    async with Camera(
        mock_camera_server_no_ptz_presets.host,
        "testuser",
        "testpassword",
        port=mock_camera_server_no_ptz_presets.port,
        verify=False,
    ) as cam:
        yield cam


@pytest.fixture
async def camera_no_ptz_caps(
    mock_camera_server_no_ptz_caps: HTTPServer,
) -> AsyncGenerator[Camera]:
    """Fixture which communicates with mock camera server and has no PTZ presets."""
    async with Camera(
        mock_camera_server_no_ptz_caps.host,
        "testuser",
        "testpassword",
        port=mock_camera_server_no_ptz_caps.port,
        verify=False,
    ) as cam:
        yield cam


@pytest.fixture
async def camera_no_privacy_mode(
    mock_camera_server_no_privacy_mode: HTTPServer,
) -> AsyncGenerator[Camera]:
    """Fixture which communicates with mock camera server and has no PTZ presets."""
    async with Camera(
        mock_camera_server_no_privacy_mode.host,
        "testuser",
        "testpassword",
        port=mock_camera_server_no_privacy_mode.port,
        verify=False,
    ) as cam:
        yield cam


@pytest.fixture
async def camera_no_smart_track(
    mock_camera_server_no_smart_track: HTTPServer,
) -> AsyncGenerator[Camera]:
    """Fixture which communicates with mock camera server and has no PTZ presets."""
    async with Camera(
        mock_camera_server_no_smart_track.host,
        "testuser",
        "testpassword",
        port=mock_camera_server_no_smart_track.port,
        verify=False,
    ) as cam:
        yield cam
