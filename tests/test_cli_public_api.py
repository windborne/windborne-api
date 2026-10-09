"""Exercise the new CLI commands through the SDK to mocked HTTP boundaries."""
import json
from unittest.mock import patch

import pytest

import windborne
from windborne import cli, events_api, climatology_api, weather_context_api, webhooks_api


def invoke(arguments, module, response=None):
    with patch('sys.argv', ['windborne'] + arguments), patch.object(
        module, 'make_api_request', return_value=response
    ) as request:
        cli.main()
    request.assert_called_once()
    return request.call_args


def test_public_helpers_are_exported():
    functions = [
        'get_events', 'get_event_index', 'get_event', 'get_event_init_times', 'get_event_context',
        'get_climatology', 'get_weather_context', 'list_webhooks', 'get_webhook',
        'create_webhook', 'update_webhook', 'delete_webhook', 'add_webhook_subscription',
        'update_webhook_subscription', 'delete_webhook_subscription', 'ping_webhook_subscription',
    ]
    for name in functions:
        assert name in windborne.__all__
        assert callable(getattr(windborne, name))


def test_event_list_geojson_preserves_features(tmp_path):
    output = tmp_path / 'events.geojson'
    response = {'type': 'FeatureCollection', 'features': [{'type': 'Feature', 'geometry': None}], 'total': 1}
    call = invoke([
        'events', 'list', 'atmospheric_river', '--initialization-time', 'latest',
        '--format', 'geojson', '--include-details', 'false',
        '--min-latitude', '0', '--max-latitude', '38',
        '--min-longitude=-124', '--max-longitude=-122', '-o', str(output),
    ], events_api, response)
    assert call.args[0].endswith('/insights/v1/wm-6/atmospheric_river')
    assert call.kwargs['params']['min_latitude'] == 0
    assert call.kwargs['params']['include_details'] == 'false'
    assert call.kwargs['params']['format'] == 'geojson'
    assert json.loads(output.read_text()) == response


@pytest.mark.parametrize('arguments,suffix', [
    (['index', 'heatwave', '--page', '0', '--page-size', '20'], '/wm-6/heatwave/index'),
    (['detail', 'heatwave_123', '--format', 'geojson'], '/wm-6/heatwave_123'),
    (['init-times', 'heatwave_123'], '/wm-6/heatwave_123/init_times'),
])
def test_event_commands_reach_documented_routes(arguments, suffix):
    call = invoke(['events'] + arguments, events_api, {})
    assert call.args[0].endswith(suffix)
    if arguments[0] == 'index':
        assert call.kwargs['params']['page'] == 0


def test_event_context_preserves_time_bounds_and_locations(capsys):
    response = {'locations': [{'latitude': 0, 'longitude': 0}, {'latitude': 1, 'longitude': 2}]}
    call = invoke([
        'events', 'context', '0,0;1,2', '--event-type', 'heatwave',
        '--min-forecast-time', '2026-10-08T06:00:00Z',
        '--max-forecast-time', '2026-10-08T12:00:00Z',
    ], events_api, response)
    assert call.kwargs['params']['coordinates'] == '0,0;1,2'
    assert call.kwargs['params']['event_type'] == 'heatwave'
    assert call.kwargs['params']['max_forecast_time'] == '2026-10-08T12:00:00Z'
    assert json.loads(capsys.readouterr().out) == response


def test_climatology_range_flags_preserve_zero_and_false():
    call = invoke([
        'climatology', '32.90,-97.04', '--start-time', '2026-07-15T12:00:00Z',
        '--end-time', '2026-07-15T13:00:00Z', '--normal', '2016-2025',
        '--rolling-average-days', '0', '--elevation-correction', 'false', '--water-strategy', 'allow',
    ], climatology_api, {'climatologies': []})
    assert call.args[0].endswith('/forecasts/v1/climatology')
    assert call.kwargs['params']['rolling_average_days'] == 0
    assert call.kwargs['params']['elevation_correction'] == 'false'
    assert call.kwargs['params']['normal'] == '2016-2025'


def test_weather_context_all_optional_datasets_survive(tmp_path):
    output = tmp_path / 'context.json'
    response = {'forecasts': [[], []], 'conditions': [None, None],
                'observations': [[], []], 'climatologies': [[], []], 'units': {}}
    call = invoke([
        'weather-context', '32.90,-97.04', '--stations', 'KDFW',
        '--include-conditions', '--include-observations', '--include-distribution', 'false',
        '--include-climatology', '--min-forecast-hour', '0', '--max-forecast-hour', '0',
        '--observation-hours', '24', '--climatology-normal', '2016-2025', '-o', str(output),
    ], weather_context_api, response)
    assert call.args[0].endswith('/forecasts/v1/weather_context')
    assert call.kwargs['params']['max_forecast_hour'] == 0
    assert call.kwargs['params']['include_distribution'] == 'false'
    assert call.kwargs['params']['include_conditions'] == 'true'
    assert json.loads(output.read_text()) == response


def test_webhook_list_filters():
    call = invoke([
        'webhooks', 'list', '--page', '1', '--page-size', '20', '--active', 'false',
        '--subscription-type', 'events.available', '--url', 'example.com',
    ], webhooks_api, {'webhooks': [], 'total': 0})
    assert call.kwargs['params'] == {
        'page': 1, 'page_size': 20, 'active': 'false',
        'subscription_type': 'events.available', 'url': 'example.com',
    }


@pytest.mark.parametrize('arguments,body,method,suffix', [
    (['create'], {'url': 'https://example.com/webhook', 'active': False,
                  'subscriptions': {'events.available': {'filters': {'event_type': 'heatwave'}}}},
     'POST', '/webhooks/v1'),
    (['update', '42'], {'active': False, 'note': None}, 'PATCH', '/webhooks/v1/42'),
    (['add-subscription', '42'], {'subscription_type': 'forecast_hour.available', 'filters': {},
                                 'response_options': {'type': 'gridded'}},
     'PATCH', '/webhooks/v1/42/subscriptions'),
    (['update-subscription', '42', '81'], {'filters': {}, 'response_options': None},
     'PATCH', '/webhooks/v1/42/subscriptions/81'),
])
def test_webhook_json_files_reach_write_endpoints(tmp_path, arguments, body, method, suffix):
    body_file = tmp_path / 'body.json'
    body_file.write_text(json.dumps(body))
    call = invoke(['webhooks'] + arguments + ['--body', str(body_file)], webhooks_api, {'id': 42})
    assert call.args[0].endswith(suffix)
    assert call.kwargs['method'] == method
    assert call.kwargs['json'] == body


@pytest.mark.parametrize('arguments,method,suffix', [
    (['get', '42'], 'GET', '/webhooks/v1/42'),
    (['delete', '42'], 'DELETE', '/webhooks/v1/42'),
    (['delete-subscription', '42', '81'], 'DELETE', '/webhooks/v1/42/subscriptions/81'),
    (['ping', '42', '81'], 'POST', '/webhooks/v1/42/subscriptions/81/ping'),
])
def test_webhook_bodyless_commands(arguments, method, suffix):
    call = invoke(['webhooks'] + arguments, webhooks_api)
    assert call.args[0].endswith(suffix)
    assert call.kwargs.get('method', 'GET') == method
    assert call.kwargs.get('json') is None


def test_webhook_body_can_be_read_from_stdin():
    with patch('sys.stdin') as stream:
        stream.read.return_value = '{"active": false, "note": null}'
        call = invoke(['webhooks', 'update', '42', '--body', '-'], webhooks_api, {'id': 42})
    assert call.kwargs['json'] == {'active': False, 'note': None}


@pytest.mark.parametrize('body', [{}, [], {'url': 'https://example.com', 'unknown': True},
                                  {'url': 'https://example.com', 'output_file': 'override.json'}])
def test_invalid_create_body_fails_before_a_request(tmp_path, body):
    body_file = tmp_path / 'body.json'
    body_file.write_text(json.dumps(body))
    with patch('sys.argv', ['windborne', 'webhooks', 'create', '--body', str(body_file)]), \
            patch.object(webhooks_api, 'make_api_request') as request, pytest.raises(SystemExit) as error:
        cli.main()
    assert error.value.code == 2
    request.assert_not_called()


def test_old_command_dispatch_is_unchanged():
    with patch('sys.argv', ['windborne', 'init_times']), patch.object(cli, 'get_initialization_times') as call:
        cli.main()
    call.assert_called_once_with(print_response=True, ens_member=None, model='wm', domain=None)


def test_cli_retains_successful_webhook_result_when_output_fails(tmp_path, capsys):
    body_file = tmp_path / 'body.json'
    body_file.write_text('{"url": "https://example.com/webhook"}')
    response = {'id': 42, 'signing_secret': 'test-only-signing-secret'}
    with patch('sys.argv', ['windborne', 'webhooks', 'create', '--body', str(body_file)]), \
            patch.object(webhooks_api, 'make_api_request', return_value=response) as request, \
            patch.object(webhooks_api, '_result', side_effect=webhooks_api.WebhookOutputError(response)), \
            pytest.raises(SystemExit) as error:
        cli.main()
    assert error.value.code == 1
    request.assert_called_once()
    output = capsys.readouterr()
    assert 'request succeeded' in output.err
    assert json.loads(output.err[output.err.index('{'):]) == response
