"""Published MetaMesh examples use the model route and preserve the full response."""

import copy
import json
from unittest.mock import patch

import pytest
import requests

from windborne import api_request, cli, get_point_forecast_conditions


@pytest.fixture
def http(monkeypatch):
    monkeypatch.setattr(api_request, 'get_verified_api_credentials',
                        lambda: ('sdk_test', 'x' * 32))
    payload = {
        'model': 'metamesh', 'initialization_time': '2026-10-21T23:00:00Z',
        'forecasts': [{
            'latitude': 37.77, 'longitude': -122.42,
            'hourly': [{'start_time': '2026-10-22T00:00:00Z', 'text': 'Clear',
                        'details': {'probability': None}}],
            'daily': [{'date': '2026-10-22', 'text': 'Windy'}],
            'day_night': [{'period': 'night', 'text': 'Cloudy'}],
        }, {'latitude': 40.7, 'longitude': -74.0, 'hourly': [], 'daily': [], 'day_night': []}],
        'future_metadata': {'values': [False, 0, None]},
    }
    response = requests.Response()
    response.status_code = 200
    response._content = json.dumps(payload).encode()
    with patch.object(api_request.requests, 'get', return_value=response) as request:
        yield request, payload


def assert_request(request):
    request.assert_called_once()
    args, kwargs = request.call_args
    assert args == ('https://api.windbornesystems.com/forecasts/v1/metamesh/point_forecast/conditions',)
    assert kwargs['params'] == {'coordinates': '37.77,-122.42;40.7,-74.0', 'hourly_interval': 6}
    assert kwargs['auth'][0] == 'sdk_test'


def test_metamesh_python_helper_returns_complete_response(http, tmp_path):
    request, payload = http
    original = copy.deepcopy(payload)
    output = tmp_path / 'metamesh.json'
    result = get_point_forecast_conditions(
        '37.77,-122.42;40.7,-74.0', model='metamesh', hourly_interval=6, output_file=output,
    )
    assert_request(request)
    assert result == original
    assert json.loads(output.read_text()) == original


def test_metamesh_documented_cli_order_reaches_http_and_keeps_response(http, tmp_path):
    request, payload = http
    output = tmp_path / 'output.json'
    with patch('sys.argv', ['windborne', 'point_forecast_conditions', '--model', 'metamesh',
                            '37.77,-122.42;40.7,-74.0', '--hourly-interval', '6', str(output)]):
        cli.main()
    assert_request(request)
    assert json.loads(output.read_text()) == payload


def test_conditions_help_lists_both_published_models(capsys):
    with patch('sys.argv', ['windborne', 'point_forecast_conditions', '--help']), \
            pytest.raises(SystemExit) as error:
        cli.main()
    assert error.value.code == 0
    help_text = capsys.readouterr().out
    assert 'wm-6' in help_text
    assert 'metamesh' in help_text
