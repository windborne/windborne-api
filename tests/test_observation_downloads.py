import csv
import json
from unittest.mock import call, patch

import pytest
import requests

from windborne import api_request, observations_api


START = 1767225600


def response(payload, status=200):
    result = requests.Response()
    result.status_code = status
    result.url = observations_api.DATA_API_BASE_URL
    result._content = json.dumps(payload).encode()
    return result


def page(rows, cursor, more=False):
    return {"observations": rows, "next_since": cursor, "has_next_page": more}


def row(identifier):
    return {"timestamp": START + identifier, "id": identifier,
            "mission_id": "mission", "mission_name": "W-mission"}


@pytest.fixture(autouse=True)
def fake_credentials(monkeypatch):
    monkeypatch.setattr(api_request, "get_verified_api_credentials",
                        lambda: ("sdk_test", "x" * 32))


@pytest.mark.parametrize("name", ["get_observations", "get_super_observations",
                                  "poll_observations", "poll_super_observations"])
def test_access_denied_stops_public_download_without_retry(name, tmp_path):
    output = tmp_path / "observations.csv"
    responses = [response({}, 403), AssertionError("An access error must not be retried")]
    with patch.object(api_request.requests, "get", side_effect=responses) as get:
        with patch.object(api_request.time, "sleep") as sleep:
            with pytest.raises(requests.HTTPError):
                getattr(observations_api, name)(start_time=START, output_file=str(output))
    get.assert_called_once()
    sleep.assert_not_called()
    assert not output.exists()


@pytest.mark.parametrize("page_number", [0, 1])
def test_failed_sounding_page_raises_instead_of_ending_pagination(page_number, tmp_path):
    output = tmp_path / "soundings.json"
    output.write_text("previous complete download")
    responses = ([response({"soundings": [{"id": "first"}]})] if page_number else [])
    responses.append(response({}, 403))
    with patch.object(api_request.requests, "get", side_effect=responses) as get:
        with patch.object(api_request.time, "sleep") as sleep:
            if page_number:
                assert observations_api.get_soundings(page=0, page_size=1) == [{"id": "first"}]
            with pytest.raises(requests.HTTPError):
                observations_api.get_soundings(page=page_number, output_file=str(output))
    assert get.call_count == page_number + 1
    sleep.assert_not_called()
    assert output.read_text() == "previous complete download"


@pytest.mark.parametrize("name", ["get_observations", "get_super_observations"])
def test_transient_download_failure_exhausts_only_transport_retry_budget(name):
    with patch.object(api_request.requests, "get", return_value=response({}, 502)) as get:
        with patch.object(api_request.time, "sleep") as sleep:
            with pytest.raises(ConnectionError, match="Max retries"):
                getattr(observations_api, name)(START)
    assert get.call_count == 5
    assert sleep.call_args_list == [call(1), call(2), call(4), call(8), call(16)]


@pytest.mark.parametrize("payload", [None, {}, {"soundings": None}])
def test_invalid_sounding_page_is_not_an_empty_result(payload):
    with patch.object(api_request.requests, "get", return_value=response(payload)):
        with pytest.raises(ValueError):
            observations_api.get_soundings()


def test_genuine_empty_sounding_list_is_valid():
    with patch.object(api_request.requests, "get", return_value=response({"soundings": []})):
        assert observations_api.get_soundings() == []


@pytest.mark.parametrize("payload", [None, {}])
def test_invalid_observation_response_is_not_retried(payload, tmp_path):
    responses = [response(payload), AssertionError("An invalid page must not be retried")]
    with patch.object(api_request.requests, "get", side_effect=responses) as get:
        with patch.object(api_request.time, "sleep") as sleep:
            with pytest.raises(ValueError):
                observations_api.get_observations(START, output_file=str(tmp_path / "out.csv"))
    get.assert_called_once()
    sleep.assert_not_called()


@pytest.mark.parametrize("name", ["get_observations", "get_super_observations"])
def test_large_finite_export_writes_once_in_global_timestamp_order(name, tmp_path):
    output = tmp_path / "observations.csv"
    # Pagination follows update time, so a later page can contain older observations.
    responses = [page([row(i) for i in range(2, 10003)], START + 10, True),
                 page([row(1)], START + 20, True), page([], START + 30)]
    with patch.object(api_request.requests, "get", side_effect=[response(p) for p in responses]):
        with patch.object(observations_api, "save_observations_to_file",
                          wraps=observations_api.save_observations_to_file) as save:
            count = getattr(observations_api, name)(START, output_file=str(output), verbose=False)
    assert count == 10002
    save.assert_called_once()
    with output.open() as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
        assert reader.fieldnames[:3] == ["timestamp", "id", "time"]
        assert len(reader.fieldnames) == len(set(reader.fieldnames))
    assert [int(r["id"]) for r in rows] == list(range(1, 10003))
    assert [int(r["timestamp"]) for r in rows] == list(range(START + 1, START + 10003))


def test_failed_later_page_preserves_existing_export_after_large_batch(tmp_path):
    output = tmp_path / "observations.csv"
    output.write_text("previous complete download")
    responses = [response(page([row(i) for i in range(10001)], START + 10, True)),
                 response({}, 403)]
    with patch.object(api_request.requests, "get", side_effect=responses) as get:
        with patch.object(api_request.time, "sleep") as sleep:
            with pytest.raises(requests.HTTPError):
                observations_api.get_observations(START, output_file=str(output), verbose=False)
    assert get.call_count == 2
    sleep.assert_not_called()
    assert output.read_text() == "previous complete download"


def test_custom_save_keeps_threshold_and_final_batches_without_duplicate_final_save():
    responses = [page([row(i) for i in range(10000)], START + 10, True),
                 page([row(10000)], START + 20)]
    batches = []
    with patch.object(api_request.requests, "get", side_effect=[response(p) for p in responses]):
        count = observations_api.get_observations(
            START, output_file="custom-output", verbose=False,
            custom_save=lambda rows, path: batches.append((len(rows), path)))
    assert count == 10001
    assert batches == [(10000, "custom-output"), (10001, "custom-output")]
