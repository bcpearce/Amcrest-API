"""Configuration for Tests."""

import json
from collections.abc import AsyncGenerator  # pylint: disable=no-name-in-module
from pathlib import Path
from typing import Callable

import httpx
import pytest
import yarl
from pytest_httpserver import HTTPServer

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


def _load_fixture(path: Path | str, server: HTTPServer):
    with open(path, "rb") as f:
        d = json.load(f)
    url = yarl.URL(d["raw_path"])
    server.expect_request(url.path, query_string=url.query_string).respond_with_data(
        d["content"]
    )


def _make_base_mock_server(server: HTTPServer):
    fixture_path = Path("tests/fixtures/mock_responses")
    for path in fixture_path.iterdir():
        _load_fixture(path, server)

    return server


@pytest.fixture(name="mock_camera_server")
def mock_camera_server_fixture(httpserver: HTTPServer) -> HTTPServer:
    """Mock camera server."""
    return _make_base_mock_server(httpserver)


async def _camera_factory(
    the_server: HTTPServer,
    server_decorator: Callable[[HTTPServer], HTTPServer] = lambda s: s,
) -> AsyncGenerator[Camera]:
    the_server = server_decorator(the_server)
    the_server = _make_base_mock_server(the_server)

    async with Camera(
        the_server.host,
        "testuser",
        "testpassword",
        port=the_server.port,
        verify=False,
    ) as cam:
        yield cam


@pytest.fixture
async def camera(httpserver: HTTPServer) -> AsyncGenerator[Camera]:
    """Fixture which communicates with mock camera server."""
    async for cam in _camera_factory(httpserver):
        yield cam


@pytest.fixture
async def camera_no_storage(httpserver: HTTPServer) -> AsyncGenerator[Camera]:
    """Fixture which communicates with mock camera server and has no storage."""

    def wrapper(httpserver):
        empty_storage_path = Path(
            "tests/fixtures/mock_responses_alt/storage_device_names_empty.json"
        )
        _load_fixture(empty_storage_path, httpserver)
        return httpserver

    async for cam in _camera_factory(httpserver, wrapper):
        yield cam


@pytest.fixture
async def camera_no_ptz_presets(
    httpserver: HTTPServer,
) -> AsyncGenerator[Camera]:
    """Fixture which communicates with mock camera server and has no PTZ presets."""

    def wrapper(httpserver):
        empty_storage_path = Path(
            "tests/fixtures/mock_responses_alt/ptz_config_presets_empty.json"
        )
        _load_fixture(empty_storage_path, httpserver)
        return httpserver

    async for cam in _camera_factory(httpserver, wrapper):
        yield cam


@pytest.fixture
async def camera_no_ptz_caps(
    httpserver: HTTPServer,
) -> AsyncGenerator[Camera]:
    """Fixture which communicates with mock camera server and has no PTZ presets."""

    def wrapper(httpserver):
        empty_caps_path = Path(
            "tests/fixtures/mock_responses_alt/ptz_capabilities_no_PanTiltZoom.json"
        )
        _load_fixture(empty_caps_path, httpserver)
        return httpserver

    async for cam in _camera_factory(httpserver, wrapper):
        yield cam


@pytest.fixture
async def camera_no_privacy_mode(
    httpserver: HTTPServer,
) -> AsyncGenerator[Camera]:
    """Fixture which communicates with mock camera server and has no PTZ presets."""

    def wrapper(httpserver):
        url = yarl.URL("/cgi-bin/configManager.cgi?action=getConfig&name=LeLensMask")
        httpserver.expect_request(
            url.path, query_string=url.query_string
        ).respond_with_data(
            "Error\nBad Request!\n",
            status=400,
        )
        return httpserver

    async for cam in _camera_factory(httpserver, wrapper):
        yield cam


@pytest.fixture
async def camera_no_smart_track(
    httpserver: HTTPServer,
) -> AsyncGenerator[Camera]:
    """Fixture which communicates with mock camera server and has no PTZ presets."""

    def wrapper(httpserver):
        url = yarl.URL("/cgi-bin/configManager.cgi?action=getConfig&name=LeSmartTrack")
        httpserver.expect_request(
            url.path, query_string=url.query_string
        ).respond_with_data(
            "Error\nBad Request!\n",
            status=400,
        )
        return httpserver

    async for cam in _camera_factory(httpserver, wrapper):
        yield cam
