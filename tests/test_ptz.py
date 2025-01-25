"""Tests for PTZ module."""

import pytest

from amcrest_api.ptz import PtzAccuratePosition, PtzCapabilityData


def test_ptz_query_dict_generation_1():
    """Tests generation of a query dict."""

    caps = PtzCapabilityData(
        pan=True, zoom=True, zoom_min=1.0, zoom_max=5.0, pan_min=10, pan_max=350
    )

    pos = PtzAccuratePosition(caps=caps, horizontal_position=130.0, zoom=4.0)

    query_params = pos.get_query_dict()

    assert query_params["channel"] == 1
    assert query_params["arg1"] == pytest.approx(-0.2777777, abs=0.001)
    assert query_params["arg2"] == 0
    assert query_params["arg3"] == pytest.approx(0.5, abs=0.001)


def test_ptz_query_dict_generation_2():
    """Tests generation of a query dict."""

    caps = PtzCapabilityData(
        tilt=True, zoom=True, zoom_min=0.5, zoom_max=2.5, tilt_min=-1, tilt_max=80
    )

    pos = PtzAccuratePosition(caps=caps, vertical_position=10.0, zoom=1.25)

    query_params = pos.get_query_dict()

    assert query_params["channel"] == 1
    assert query_params["arg1"] == 0
    assert query_params["arg2"] == pytest.approx(0.0555555, abs=0.001)
    assert query_params["arg3"] == pytest.approx(-0.25, abs=0.001)


def test_ptz_query_dict_generation_3():
    """Tests generation of a query dict with range error."""

    caps = PtzCapabilityData(tilt=True, tilt_min=-1, tilt_max=80)

    pos = PtzAccuratePosition(caps=caps, vertical_position=-10.0)

    with pytest.raises(ValueError):
        _ = pos.get_query_dict()
