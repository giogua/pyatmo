"""Define tests for Camera module."""
from contextlib import nullcontext as does_not_raise
import json

import pytest
from freezegun import freeze_time

import pyatmo

INVALID_NAME = "InvalidName"


def test_CameraData(cameraHomeData):
    assert cameraHomeData.homes is not None


@pytest.mark.parametrize(
    "cid, expected",
    [
        ("12:34:56:00:f1:62", "Hall"),
        ("12:34:56:00:a5:a4", "Garden"),
        ("None", None),
        (None, None),
    ],
)
def test_CameraData_get_camera(cameraHomeData, cid, expected):
    camera = cameraHomeData.get_camera(cid)
    if camera:
        assert camera["name"] == expected
    else:
        assert camera is expected


def test_CameraData_get_module(cameraHomeData):
    assert cameraHomeData.get_module("00:00:00:00:00:00") is None


def test_CameraData_camera_urls(cameraHomeData, requests_mock):
    cid = "12:34:56:00:f1:62"
    vpn_url = (
        "https://prodvpn-eu-2.netatmo.net/restricted/10.255.248.91/"
        "6d278460699e56180d47ab47169efb31/"
        "MpEylTU2MDYzNjRVD-LJxUnIndumKzLboeAwMDqTTg,,"
    )
    local_url = "http://192.168.0.123/678460a0d47e5618699fb31169e2b47d"
    with open("fixtures/camera_ping.json") as f:
        json_fixture = json.load(f)
    requests_mock.post(
        vpn_url + "/command/ping",
        json=json_fixture,
        headers={"content-type": "application/json"},
    )
    with open("fixtures/camera_ping.json") as f:
        json_fixture = json.load(f)
    requests_mock.post(
        local_url + "/command/ping",
        json=json_fixture,
        headers={"content-type": "application/json"},
    )
    cameraHomeData.update_camera_urls(cid)
    assert cameraHomeData.camera_urls(cid) == (vpn_url, local_url)


def test_CameraData_camera_urls_disconnected(auth, requests_mock):
    with open("fixtures/camera_home_data_disconnected.json") as f:
        json_fixture = json.load(f)
    requests_mock.post(
        pyatmo.camera._GETHOMEDATA_REQ,
        json=json_fixture,
        headers={"content-type": "application/json"},
    )
    camera_data = pyatmo.CameraData(auth)

    cid = "12:34:56:00:f1:62"
    vpn_url = (
        "https://prodvpn-eu-2.netatmo.net/restricted/10.255.248.91/"
        "6d278460699e56180d47ab47169efb31/"
        "MpEylTU2MDYzNjRVD-LJxUnIndumKzLboeAwMDqTTg,,"
    )
    local_url = "http://192.168.0.123/678460a0d47e5618699fb31169e2b47d"
    with open("fixtures/camera_ping.json") as f:
        json_fixture = json.load(f)
    requests_mock.post(
        vpn_url + "/command/ping",
        json=json_fixture,
        headers={"content-type": "application/json"},
    )
    with open("fixtures/camera_ping.json") as f:
        json_fixture = json.load(f)
    requests_mock.post(
        local_url + "/command/ping",
        json=json_fixture,
        headers={"content-type": "application/json"},
    )
    camera_data.update_camera_urls(cid)
    assert camera_data.camera_urls(cid) == (None, None)


@pytest.mark.parametrize(
    "home_id, expected", [("91763b24c43d3e344f424e8b", ["Richard Doe"])],
)
def test_CameraData_persons_at_home(cameraHomeData, home_id, expected):
    assert cameraHomeData.persons_at_home(home_id) == expected


@freeze_time("2019-06-16")
@pytest.mark.parametrize(
    "name, cid, exclude, expected",
    [
        ("John Doe", "12:34:56:00:f1:62", None, True),
        ("Richard Doe", "12:34:56:00:f1:62", None, False),
        ("Unknown", "12:34:56:00:f1:62", None, False),
        ("John Doe", "12:34:56:00:f1:62", 1, False),
        ("John Doe", "12:34:56:00:f1:62", 50000, True),
        ("Jack Doe", "12:34:56:00:f1:62", None, False),
    ],
)
def test_CameraData_person_seen_by_camera(cameraHomeData, name, cid, exclude, expected):
    assert cameraHomeData.person_seen_by_camera(name, cid, exclude=exclude) is expected


def test_CameraData__knownPersons(cameraHomeData):
    knownPersons = cameraHomeData._knownPersons()
    assert len(knownPersons) == 3
    assert knownPersons["91827374-7e04-5298-83ad-a0cb8372dff1"]["pseudo"] == "John Doe"


def test_CameraData_knownPersonsNames(cameraHomeData):
    assert sorted(cameraHomeData.knownPersonsNames()) == [
        "Jane Doe",
        "John Doe",
        "Richard Doe",
    ]


@freeze_time("2019-06-16")
@pytest.mark.parametrize(
    "name, expected",
    [
        ("John Doe", "91827374-7e04-5298-83ad-a0cb8372dff1"),
        ("Richard Doe", "91827376-7e04-5298-83af-a0cb8372dff3"),
    ],
)
def test_CameraData_get_person_id(cameraHomeData, name, expected):
    assert cameraHomeData.get_person_id(name) == expected


@pytest.mark.parametrize(
    "hid, pid, json_fixture, expected",
    [
        (
            "91763b24c43d3e344f424e8b",
            "91827374-7e04-5298-83ad-a0cb8372dff1",
            "status_ok.json",
            "ok",
        ),
        (
            "91763b24c43d3e344f424e8b",
            "91827376-7e04-5298-83af-a0cb8372dff3",
            "status_ok.json",
            "ok",
        ),
    ],
)
def test_CameraData_set_persons_away(
    cameraHomeData, requests_mock, hid, pid, json_fixture, expected
):
    with open("fixtures/%s" % json_fixture) as f:
        json_fixture = json.load(f)
    requests_mock.post(
        pyatmo.camera._SETPERSONSAWAY_REQ,
        json=json_fixture,
        headers={"content-type": "application/json"},
    )
    assert cameraHomeData.set_persons_away(pid, hid)["status"] == expected


@pytest.mark.parametrize(
    "hid, pids, json_fixture, expected",
    [
        (
            "91763b24c43d3e344f424e8b",
            [
                "91827374-7e04-5298-83ad-a0cb8372dff1",
                "91827376-7e04-5298-83af-a0cb8372dff3",
            ],
            "status_ok.json",
            "ok",
        ),
        (
            "91763b24c43d3e344f424e8b",
            "91827376-7e04-5298-83af-a0cb8372dff3",
            "status_ok.json",
            "ok",
        ),
    ],
)
def test_CameraData_set_persons_home(
    cameraHomeData, requests_mock, hid, pids, json_fixture, expected
):
    with open("fixtures/%s" % json_fixture) as f:
        json_fixture = json.load(f)
    requests_mock.post(
        pyatmo.camera._SETPERSONSHOME_REQ,
        json=json_fixture,
        headers={"content-type": "application/json"},
    )
    assert cameraHomeData.set_persons_home(pids, hid)["status"] == expected


@freeze_time("2019-06-16")
@pytest.mark.parametrize(
    "camera_id, exclude, expected,expectation",
    [
        ("12:34:56:00:f1:62", None, True, does_not_raise()),
        ("12:34:56:00:f1:62", 5, False, does_not_raise()),
        (None, None, None, pytest.raises(pyatmo.NoDevice)),
    ],
)
def test_CameraData_someone_known_seen(
    cameraHomeData, camera_id, exclude, expected, expectation
):
    with expectation:
        assert cameraHomeData.someone_known_seen(camera_id, exclude) == expected


@freeze_time("2019-06-16")
@pytest.mark.parametrize(
    "camera_id, exclude, expected, expectation",
    [
        ("12:34:56:00:f1:62", None, False, does_not_raise()),
        ("12:34:56:00:f1:62", 100, False, does_not_raise()),
        (None, None, None, pytest.raises(pyatmo.NoDevice)),
    ],
)
def test_CameraData_someone_unknown_seen(
    cameraHomeData, camera_id, exclude, expected, expectation
):
    with expectation:
        assert cameraHomeData.someone_unknown_seen(camera_id, exclude) == expected


@freeze_time("2019-06-16")
@pytest.mark.parametrize(
    "camera_id, exclude, expected, expectation",
    [
        ("12:34:56:00:f1:62", None, False, does_not_raise()),
        ("12:34:56:00:f1:62", 140000, True, does_not_raise()),
        ("12:34:56:00:f1:62", 130000, False, does_not_raise()),
        (None, None, False, pytest.raises(pyatmo.NoDevice)),
    ],
)
def test_CameraData_motion_detected(
    cameraHomeData, camera_id, exclude, expected, expectation
):
    with expectation:
        assert cameraHomeData.motion_detected(camera_id, exclude) == expected


@pytest.mark.parametrize(
    "sid, expected",
    [
        ("12:34:56:00:8b:a2", "Hall"),
        ("12:34:56:00:8b:ac", "Kitchen"),
        ("None", None),
        (None, None),
    ],
)
def test_CameraData_get_smokedetector(cameraHomeData, sid, expected):
    smokedetector = cameraHomeData.get_smokedetector(sid)
    if smokedetector:
        assert smokedetector["name"] == expected
    else:
        assert smokedetector is expected


@pytest.mark.parametrize(
    "home_id, camera_id, floodlight, monitoring, json_fixture, expected",
    [
        (
            "91763b24c43d3e344f424e8b",
            "12:34:56:00:f1:ff",
            "on",
            None,
            "camera_set_state_error.json",
            False,
        ),
        (
            "91763b24c43d3e344f424e8b",
            "12:34:56:00:f1:62",
            None,
            "on",
            "camera_set_state_ok.json",
            True,
        ),
        (None, "12:34:56:00:f1:62", None, "on", "camera_set_state_ok.json", True,),
        (
            "91763b24c43d3e344f424e8b",
            "12:34:56:00:f1:62",
            "auto",
            "on",
            "camera_set_state_ok.json",
            True,
        ),
        (
            "91763b24c43d3e344f424e8b",
            "12:34:56:00:f1:62",
            None,
            "on",
            "camera_set_state_error_already_on.json",
            True,
        ),
        (
            "91763b24c43d3e344f424e8b",
            "12:34:56:00:f1:62",
            "on",
            None,
            "camera_set_state_error_wrong_parameter.json",
            False,
        ),
    ],
)
def test_CameraData_set_state(
    cameraHomeData,
    requests_mock,
    home_id,
    camera_id,
    floodlight,
    monitoring,
    json_fixture,
    expected,
):
    with open("fixtures/%s" % json_fixture) as f:
        json_fixture = json.load(f)
    requests_mock.post(
        pyatmo.camera._SETSTATE_REQ,
        json=json_fixture,
        headers={"content-type": "application/json"},
    )
    assert (
        cameraHomeData.set_state(
            home_id=home_id,
            camera_id=camera_id,
            floodlight=floodlight,
            monitoring=monitoring,
        )
        == expected
    )
