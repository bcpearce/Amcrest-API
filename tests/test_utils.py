"""Test utils.py."""

import pytest

from amcrest_api import utils


def test_parse_json(mock_json_response, snapshot):
    """Test json responses are parsed."""
    res = utils.parse_response(response=mock_json_response)
    assert isinstance(res, dict)
    assert res == snapshot


def test_parse_key_value_table(mock_key_value_with_table_response, snapshot):
    """Test key value responses with tables are parsed."""
    res = utils.parse_response(response=mock_key_value_with_table_response)
    assert isinstance(res, dict)
    # spot check
    assert res["General"]["LockLoginTimes"] == "30"
    # snapshot check
    assert res == snapshot


def test_parse_key_value_with_array(mock_key_value_with_array_response, snapshot):
    """Test key value responses with arrays are parsed."""
    res = utils.parse_response(response=mock_key_value_with_array_response)
    assert isinstance(res, dict)
    # spot  check
    assert res["Snap"][0]["HolidayEnable"] == "false"
    assert res["Snap"][0]["TimeSection"][0][1] == "0 00:00:00-23:59:59"
    # snapshot check
    assert res == snapshot


def test_parse_single_key_value(mock_key_value_response):
    """Test a response with a single key-value"""
    res = utils.parse_response(response=mock_key_value_response)
    assert res["sn"] == "AMC0"


def test_indexed_dict_to_list():
    """Test converting a dict of contiguous indices can be converted to a list."""
    indexed_dict = {
        2: "StorageLowSpace",
        3: "StorageNotExist",
        0: "AudioAnomaly",
        1: "StorageFailure",
        4: "VideoBlind",
        5: "VideoMotion",
    }
    assert utils.indexed_dict_to_list(indexed_dict) == [
        "AudioAnomaly",
        "StorageFailure",
        "StorageLowSpace",
        "StorageNotExist",
        "VideoBlind",
        "VideoMotion",
    ]

    # fails if not all in a sequence
    indexed_dict.pop(3)
    with pytest.raises(KeyError):
        assert utils.indexed_dict_to_list(indexed_dict)
