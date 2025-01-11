"""Configuration for Tests."""

import json
from pathlib import Path

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


@pytest.fixture(name="mock_camera_server")
def mock_camera_server_fixture(httpserver: HTTPServer) -> HTTPServer:
    """Mock camera server."""

    def load_fixture(path: Path | str):
        with open(path, "rb") as f:
            d = json.load(f)
        url = yarl.URL(d["raw_path"])
        httpserver.expect_request(
            url.path, query_string=url.query_string
        ).respond_with_data(d["content"])

    load_fixture("tests/fixtures/mock_responses/get_lelensmask.json")
    load_fixture("tests/fixtures/mock_responses/lighting_config.json")
    load_fixture("tests/fixtures/mock_responses/serial_number.json")
    return httpserver


@pytest.fixture
def camera(mock_camera_server: HTTPServer) -> Camera:
    """Fixture which communicates with mock camera server."""
    return Camera(
        mock_camera_server.host,
        "testuser",
        "testpassword",
        port=mock_camera_server.port,
        verify=False,
    )
