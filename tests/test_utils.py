from amcrest_api import utils


def test_parse_json(mock_json_response, snapshot):
    res = utils.parse_response(response=mock_json_response)
    assert isinstance(res, dict)
    assert res == snapshot


def test_parse_key_value_table(mock_key_value_with_table_response, snapshot):
    res = utils.parse_response(response=mock_key_value_with_table_response)
    assert isinstance(res, dict)
    # spot check
    assert res["General"]["LockLoginTimes"] == "30"
    # snapshot check
    assert res == snapshot


def test_parse_key_value_with_array(
    mock_key_value_with_array_response, snapshot
):
    res = utils.parse_response(response=mock_key_value_with_array_response)
    assert isinstance(res, dict)
    # spot  check
    assert res["Snap"][0]["HolidayEnable"] == "false"
    assert res["Snap"][0]["TimeSection"][0][1] == "0 00:00:00-23:59:59"
    # snapshot check
    assert res == snapshot


def test_parse_single_key_value(mock_key_value_response):
    res = utils.parse_response(response=mock_key_value_response)
    assert res["sn"] == "AMC0"
