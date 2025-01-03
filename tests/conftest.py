import httpx
import pytest


@pytest.fixture
def mock_json_response():
    with open("tests/fixtures/MockJsonPayload.json") as f:
        yield httpx.Response(200, text=f.read())


@pytest.fixture
def mock_key_value_with_table_response():
    with open("tests/fixtures/MockKeyValuePayloadTable.txt") as f:
        # ensure line endings
        text = "\r\n".join(line.strip() for line in f.readlines())
        yield httpx.Response(200, text=text)


@pytest.fixture
def mock_key_value_with_array_response():
    with open("tests/fixtures/MockKeyValuePayloadWithArray.txt") as f:
        # ensure line endings
        text = "\r\n".join(line.strip() for line in f.readlines())
        yield httpx.Response(200, text=text)


@pytest.fixture
def mock_key_value_response():
    return httpx.Response(200, text="sn=AMC0\r\n")
