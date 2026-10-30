"""Published MetaMesh examples use the model route and preserve the full response."""

import copy
import json
from unittest.mock import patch

import pytest
import requests

from windborne import api_request, cli, get_point_forecast_conditions


@pytest.fixture(params=[False, True], ids=['primary-icon', 'sky-state-icon'])
def include_sky_state_icon(request):
    return request.param


@pytest.fixture(params=['wm-6', 'metamesh'])
def model(request):
    return request.param


@pytest.fixture
def http(monkeypatch, include_sky_state_icon, model):
    monkeypatch.setattr(api_request, 'get_verified_api_credentials',
                        lambda: ('sdk_test', 'x' * 32))
    payload = {
        'model': model, 'initialization_time': '2026-10-21T23:00:00Z',
        'forecasts': [{
            'latitude': 37.77, 'longitude': -122.42,
            'hourly': [{'start_time': '2026-10-22T00:00:00Z', 'text': 'Clear',
                        'details': {'probability': None}}],
            'daily': [{'date': '2026-10-22', 'text': 'Windy'}],
            'day_night': [{'period': 'night', 'text': 'Cloudy'}],
        }, {'latitude': 40.7, 'longitude': -74.0, 'hourly': [], 'daily': [], 'day_night': []}],
        'future_metadata': {'values': [False, 0, None]},
    }
    if include_sky_state_icon:
        for block in payload['forecasts'][0]['hourly']:
            block.update(sky_state_icon_url='https://example.test/clear_day.svg', sky_state_condition='Clear')
        for block in payload['forecasts'][0]['daily'] + payload['forecasts'][0]['day_night']:
            block.update(sky_state_icon_url=None, sky_state_condition=None)
    response = requests.Response()
    response.status_code = 200
    response._content = json.dumps(payload).encode()
    with patch.object(api_request.requests, 'get', return_value=response) as request:
        yield request, payload


def assert_request(request, include_sky_state_icon, model):
    request.assert_called_once()
    args, kwargs = request.call_args
    assert args == (f'https://api.windbornesystems.com/forecasts/v1/{model}/point_forecast/conditions',)
    expected = {'coordinates': '37.77,-122.42;40.7,-74.0', 'hourly_interval': 6}
    if include_sky_state_icon:
        expected['include_sky_state_icon'] = 'true'
    assert kwargs['params'] == expected
    assert kwargs['auth'][0] == 'sdk_test'


def test_python_helper_returns_complete_response(http, tmp_path, include_sky_state_icon, model):
    request, payload = http
    original = copy.deepcopy(payload)
    output = tmp_path / 'metamesh.json'
    result = get_point_forecast_conditions(
        '37.77,-122.42;40.7,-74.0', 6, model, output, False,
        include_sky_state_icon=include_sky_state_icon,
    )
    assert_request(request, include_sky_state_icon, model)
    assert result == original
    assert json.loads(output.read_text()) == original


def test_documented_cli_order_reaches_http_and_keeps_response(http, tmp_path, include_sky_state_icon, model):
    request, payload = http
    output = tmp_path / 'output.json'
    options = ['--include-sky-state-icon'] if include_sky_state_icon else []
    with patch('sys.argv', ['windborne', 'point_forecast_conditions', '--model', model,
                            '37.77,-122.42;40.7,-74.0', '--hourly-interval', '6'] + options + [str(output)]):
        cli.main()
    assert_request(request, include_sky_state_icon, model)
    assert json.loads(output.read_text()) == payload


def test_conditions_help_lists_both_published_models(capsys):
    with patch('sys.argv', ['windborne', 'point_forecast_conditions', '--help']), \
            pytest.raises(SystemExit) as error:
        cli.main()
    assert error.value.code == 0
    help_text = capsys.readouterr().out
    assert 'wm-6' in help_text
    assert 'metamesh' in help_text
