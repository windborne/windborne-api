import copy
import csv
import json
from unittest.mock import call, patch

import pytest

from windborne import cli, observations_api


START = 1767225600
CSV_HEADERS = [
    "timestamp", "id", "time", "latitude", "longitude", "altitude", "humidity",
    "pressure", "specific_humidity", "speed_u", "speed_v", "temperature",
    "mission_name", "mission_id",
]


def observation(identifier, include_updated_at=False, mission_id="mission"):
    value = {
        "timestamp": START + identifier,
        "id": identifier,
        "time": "2026-01-01T00:00:{:02d}Z".format(identifier),
        "latitude": 0,
        "longitude": -122.4,
        "altitude": 12000,
        "humidity": None,
        "pressure": 200,
        "specific_humidity": None,
        "speed_u": 0,
        "speed_v": -2.5,
        "temperature": -50.5,
        "mission_name": "W-" + mission_id,
        "mission_id": mission_id,
    }
    if include_updated_at:
        value["updated_at"] = START * 1_000_000_000 + identifier
    return value


def page(observations, next_since, has_next_page=False):
    return {
        "observations": observations,
        "next_since": next_since,
        "has_next_page": has_next_page,
    }


class StopPolling(Exception):
    pass


@pytest.mark.parametrize("name,endpoint", [
    ("poll_observations", "observations.json"),
    ("poll_super_observations", "super_observations.json"),
])
@pytest.mark.parametrize("extension", ["json", "csv"])
def test_public_pollers_advance_at_end_and_after_empty_pages(
    name, endpoint, extension, tmp_path
):
    # Nanosecond cursors must survive the public wrapper without truncation.
    cursors = [START] + [START * 1_000_000_000 + i for i in range(10, 14)]
    pages = {
        cursors[0]: page([observation(1, True)], cursors[1], True),
        cursors[1]: page([observation(2, True)], cursors[2]),
        cursors[2]: page([], cursors[3]),
        cursors[3]: page([observation(3, True)], cursors[4]),
    }
    requested = []
    callbacks = []

    def request(url, params, raise_errors):
        assert url == observations_api.OBSERVATIONS_API_BASE_URL + "/" + endpoint
        assert raise_errors is True
        assert params["include_updated_at"] is True
        requested.append(params["since"])
        if len(requested) == 5:
            raise StopPolling()
        return copy.deepcopy(pages[params["since"]])

    with patch.object(observations_api, "make_api_request", side_effect=request):
        with patch.object(observations_api.time, "sleep") as sleep:
            with pytest.raises(StopPolling):
                getattr(observations_api, name)(
                    start_time=START,
                    include_updated_at=True,
                    output_file=str(tmp_path / ("observations." + extension)),
                    callback=lambda response: callbacks.append(copy.deepcopy(response)),
                    verbose=False,
                )

    assert requested == cursors
    assert [item["id"] for response in callbacks for item in response["observations"]] == [1, 2, 3]
    assert [response["next_since"] for response in callbacks] == cursors[1:]
    assert sleep.call_args_list == [call(60), call(60), call(60)]
    files = sorted(tmp_path.glob("*." + extension))
    assert len(files) == 2  # One caught-up batch and one later batch; no replay.
    exported = []
    for path in files:
        with path.open() as stream:
            exported.extend(json.load(stream) if extension == "json" else csv.DictReader(stream))
    assert sorted(int(item["id"]) for item in exported) == [1, 2, 3]
    assert sorted(int(item["updated_at"]) for item in exported) == [
        START * 1_000_000_000 + i for i in (1, 2, 3)
    ]


@pytest.mark.parametrize("name", ["get_observations", "get_super_observations"])
def test_finite_fetch_still_stops_after_last_page(name, tmp_path):
    values = [observation(1), observation(2)]
    responses = [page(values[:1], START + 10, True), page(values[1:], START + 20)]
    callbacks = []
    output = tmp_path / "observations.json"
    with patch.object(observations_api, "make_api_request", side_effect=responses) as request:
        with patch.object(observations_api.time, "sleep") as sleep:
            result = getattr(observations_api, name)(
                start_time=START,
                end_time=START + 60,
                output_file=str(output),
                callback=lambda response: callbacks.extend(response["observations"]),
                verbose=False,
            )
    assert result == 2
    assert callbacks == values
    assert json.loads(output.read_text()) == values
    assert [args.kwargs["params"]["since"] for args in request.call_args_list] == [START, START + 10]
    sleep.assert_not_called()


@pytest.mark.parametrize("name", ["poll_observations", "poll_super_observations"])
def test_poll_empty_pages_still_advance(name, tmp_path):
    responses = [page([observation(1)], START + 10),
                 {"next_since": START + 20, "has_next_page": False}, StopPolling()]
    callbacks = []
    with patch.object(observations_api, "make_api_request", side_effect=responses) as request:
        with patch.object(observations_api.time, "sleep") as sleep:
            with pytest.raises(StopPolling):
                getattr(observations_api, name)(
                    start_time=START,
                    output_file=str(tmp_path / "observations.json"),
                    callback=lambda response: callbacks.append(copy.deepcopy(response)),
                    verbose=False,
                )
    assert [args.kwargs["params"]["since"] for args in request.call_args_list] == [
        START, START + 10, START + 20,
    ]
    assert len(callbacks) == 2
    assert sleep.call_args_list == [call(60), call(60)]
    files = list(tmp_path.glob("*.json"))
    assert len(files) == 1
    assert json.loads(files[0].read_text()) == [observation(1)]


@pytest.mark.parametrize("include_updated_at", [True, False, None])
@pytest.mark.parametrize("bucketed", [False, True])
def test_observation_csv_retains_requested_update_timestamps_and_existing_columns(
    include_updated_at, bucketed, tmp_path
):
    values = [observation(1, include_updated_at, "a"), observation(2, include_updated_at, "b")]
    responses = [page(values[:1], START + 10, True), page(values[1:], START + 20)]
    options = {"output_format": "csv", "output_dir": str(tmp_path)} if bucketed else {
        "output_file": str(tmp_path / "observations.csv")
    }
    if include_updated_at is not None:
        options["include_updated_at"] = include_updated_at
    with patch.object(observations_api, "make_api_request", side_effect=responses) as request:
        result = observations_api.get_observations(start_time=START, verbose=False, **options)
    assert result == 2
    for args in request.call_args_list:
        assert args.kwargs["params"].get("include_updated_at", False) == bool(include_updated_at)
    files = sorted(tmp_path.glob("*.csv"))
    assert len(files) == (2 if bucketed else 1)
    rows = []
    for path in files:
        with path.open() as stream:
            reader = csv.DictReader(stream)
            assert reader.fieldnames == CSV_HEADERS + (["updated_at"] if include_updated_at else [])
            rows.extend(reader)
    expected = [{key: "" if value is None else str(value) for key, value in row.items()} for row in values]
    assert sorted(rows, key=lambda row: row["id"]) == expected


def constellation_response():
    return {"missions": [
        {"id": "restricted", "name": "W-restricted", "latitude": "restricted",
         "longitude": "restricted", "altitude": 12000, "ascent_rate": 1.25},
        {"id": "numeric", "name": "W-numeric", "latitude": 12.345678,
         "longitude": -98.765432, "altitude": 2000.25, "ascent_rate": -1.236},
        {"id": "zero", "name": "W-zero", "latitude": 0,
         "longitude": 0, "altitude": 0, "ascent_rate": 0},
        {"id": "missing", "name": "W-missing"},
        {"id": "null", "name": "W-null", "latitude": None,
         "longitude": None, "altitude": None, "ascent_rate": None},
    ]}


def assert_constellation_table(output):
    rows = [line.split() for line in output.splitlines() if "W-" in line]
    assert rows == [
        ["1", "W-restricted", "restricted", "restricted", "12000.0", "1.25"],
        ["2", "W-numeric", "12.3457", "-98.7654", "2000.2", "-1.24"],
        ["3", "W-zero", "0.0000", "0.0000", "0.0", "0.00"],
        ["4", "W-missing", "N/A", "N/A", "N/A", "N/A"],
        ["5", "W-null", "N/A", "N/A", "N/A", "N/A"],
    ]


@pytest.mark.parametrize("keyword", ["print_response", "print_results"])
def test_constellation_print_preserves_restricted_markers_and_raw_response(keyword, tmp_path, capsys):
    response = constellation_response()
    original = copy.deepcopy(response)
    output = tmp_path / "constellation.json"
    with patch.object(observations_api, "make_api_request", return_value=response):
        result = observations_api.get_constellation_status(output_file=str(output), **{keyword: True})
    assert result is response["missions"]
    assert response == original
    assert json.loads(output.read_text()) == original
    assert_constellation_table(capsys.readouterr().out)


def test_default_constellation_cli_prints_restricted_coordinates(capsys):
    response = constellation_response()
    original = copy.deepcopy(response)
    with patch.object(observations_api, "make_api_request", return_value=response) as request:
        with patch("sys.argv", ["windborne", "constellation_status"]):
            cli.main()
    request.assert_called_once_with(
        observations_api.POSITIONS_API_BASE_URL + "/constellation_status.json",
        params={"page": 0, "page_size": 64},
    )
    assert response == original
    assert_constellation_table(capsys.readouterr().out)


@pytest.mark.parametrize("options", [{}, {"print_results": True, "print_response": False}])
def test_constellation_stays_quiet_when_printing_disabled(options, capsys):
    response = constellation_response()
    with patch.object(observations_api, "make_api_request", return_value=response):
        assert observations_api.get_constellation_status(**options) is response["missions"]
    assert capsys.readouterr().out == ""
