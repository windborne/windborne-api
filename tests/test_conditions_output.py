"""Conditions exports preserve the documented JSON response, without flattening."""

import copy
import json
from unittest.mock import patch

import pytest

from windborne import cli, forecasts_api


@pytest.mark.parametrize('filename', ['conditions.csv', 'conditions.txt', 'conditions', ''])
def test_unsupported_output_rejected_before_request(filename, tmp_path):
    output = str(tmp_path / filename) if filename else ''
    response = {'forecasts': [{'latitude': 37.77, 'longitude': -122.42,
                              'hourly': [{'text': 'Clear'}], 'daily': [], 'day_night': []}]}
    with patch.object(forecasts_api, 'make_api_request', return_value=response) as request:
        with pytest.raises(ValueError, match=r'\.json'):
            forecasts_api.get_point_forecast_conditions('37.77,-122.42', output_file=output)
        request.assert_not_called()
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize('path_kind', ['string', 'path', 'uppercase'])
def test_json_export_preserves_all_locations_periods_and_metadata(path_kind, tmp_path):
    response = {
        'initialization_time': '2026-10-12T00:00:00Z',
        'forecasts': [{
            'latitude': 37.77, 'longitude': -122.42,
            'hourly': [{'start_time': '2026-10-12T06:00:00Z',
                        'text': 'Clear', 'details': {'probability': None}}],
            'daily': [{'date': '2026-10-12', 'text': 'Windy'}],
            'day_night': [{'period': 'night', 'text': 'Clear'}],
        }, {
            'latitude': 40.7, 'longitude': -74.0,
            'hourly': [], 'daily': [], 'day_night': [],
        }],
        'metadata': {'future_field': [None, False, 0]},
    }
    original = copy.deepcopy(response)
    path = tmp_path / 'nested' / ('conditions.JSON' if path_kind == 'uppercase' else 'conditions.json')
    output = str(path) if path_kind == 'string' else path
    with patch.object(forecasts_api, 'make_api_request', return_value=response) as request:
        result = forecasts_api.get_point_forecast_conditions(
            '37.77,-122.42;40.7,-74.0', hourly_interval=6, output_file=output,
        )
        request.assert_called_once()
    assert result is response
    assert json.loads(path.read_text()) == original
    assert response == original


def test_failed_request_does_not_create_output(tmp_path):
    output = tmp_path / 'nested' / 'conditions.json'
    with patch.object(forecasts_api, 'make_api_request', return_value=None):
        assert forecasts_api.get_point_forecast_conditions('37.77,-122.42', output_file=output) is None
    assert not output.parent.exists()


def test_cli_csv_rejected_before_request(tmp_path):
    output = tmp_path / 'conditions.csv'
    response = {'forecasts': [{'latitude': 37.77, 'longitude': -122.42,
                              'hourly': [{'text': 'Clear'}], 'daily': [], 'day_night': []}]}
    with patch('sys.argv', ['windborne', 'point_forecast_conditions', '37.77,-122.42',
                            '--hourly-interval', '6', str(output)]), \
            patch.object(forecasts_api, 'make_api_request', return_value=response) as request:
        with pytest.raises(ValueError, match=r'\.json'):
            cli.main()
        request.assert_not_called()
    assert not output.exists()
