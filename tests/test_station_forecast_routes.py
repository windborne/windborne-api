"""Keep the single-station SDK contract while using current MetaMesh data."""

import copy
import csv
import json
from unittest.mock import patch

import pytest

from windborne import cli, forecasts_api


@pytest.fixture
def station_response():
    row = {
        'time': '2026-10-22T05:00:00Z',
        'station_id': 'KJFK', 'latitude': 40.65, 'longitude': -73.78,
        'temperature_2m': 9.6, 'dewpoint_2m': 2.59,
        'wind_u_10m': 0, 'wind_v_10m': -4.3,
        'precipitation': 0, 'pressure_msl': 1015.95,
        'apparent_temperature': 6.7,
        'temperature_2m_distribution': {'p10': 8.91, 'p90': 10.29},
        'precipitation_distribution': {'mean': 0, 'gt_25mm': 0},
        'future_field': {'enabled': False, 'value': None},
    }
    later = dict(row, time='2026-10-22T06:00:00Z', precipitation=None,
                 temperature_2m_distribution=None)
    return {
        'initialization_time': '2026-10-22T05:00:00Z',
        'forecast_zero': '2026-10-22T05:00:00Z',
        'forecasts': [[row, later]],
        'metadata': {'source': 'fixture', 'future_field': [None, False, 0]},
    }


def expected_single_station(response):
    return {
        'initialization_time': response['initialization_time'],
        'forecast_zero': response['forecast_zero'],
        'metadata': response['metadata'],
        'station_id': 'KJFK', 'latitude': 40.65, 'longitude': -73.78,
        'model': 'metamesh', 'forecast': response['forecasts'][0],
    }


@pytest.mark.parametrize('model', [None, 'mm', 'metamesh'])
def test_metamesh_aliases_use_station_query_and_preserve_response(model, station_response, capsys):
    original = copy.deepcopy(station_response)
    options = {} if model is None else {'model': model}
    station = ' kjfk '
    with patch.object(forecasts_api, 'make_api_request', return_value=station_response) as request:
        result = forecasts_api.get_station_forecast(station, **options)
    request.assert_called_once_with(
        forecasts_api.FORECASTS_API_BASE_URL + '/' + (model or 'wm') + '/point_forecast',
        params={'stations': 'KJFK'},
    )
    assert result == expected_single_station(original)
    assert result is not station_response
    assert station_response == original
    assert station == ' kjfk '
    assert capsys.readouterr().out == ''


@pytest.mark.parametrize('model', ['gfs', 'wm4', 'wm-6'])
def test_explicit_non_metamesh_models_keep_legacy_route_and_response(model, station_response):
    response = expected_single_station(station_response)
    response['model'] = model
    original = copy.deepcopy(response)
    with patch.object(forecasts_api, 'make_api_request', return_value=response) as request:
        result = forecasts_api.get_station_forecast(
            'KJFK', initialization_time='2026102205', model=model,
        )
    request.assert_called_once_with(
        forecasts_api.FORECASTS_API_BASE_URL + '/' + model + '/point_forecast/stations/KJFK',
        params={'initialization_time': '2026-10-22T05:00:00'},
    )
    assert result is response
    assert response == original


def test_existing_positional_call_normalizes_init_and_prints_current_fields(
    station_response, tmp_path, capsys
):
    output = tmp_path / 'station.json'
    with patch.object(forecasts_api, 'make_api_request', return_value=station_response) as request:
        result = forecasts_api.get_station_forecast('KJFK', '2026102205', str(output), True, 'mm')
    assert request.call_args.kwargs['params'] == {
        'stations': 'KJFK', 'initialization_time': '2026-10-22T05:00:00',
    }
    assert json.loads(output.read_text()) == result
    printed = capsys.readouterr().out
    assert 'Station: KJFK' in printed
    assert 'Location: (40.65, -73.78)' in printed
    assert 'Model: metamesh' in printed
    assert '2026-10-22T06:00:00Z' in printed
    assert '9.6' in printed and '1015.95' in printed


def test_json_preserves_top_level_metadata_and_every_forecast_field(station_response, tmp_path):
    original = copy.deepcopy(station_response)
    output = tmp_path / 'nested' / 'station.json'
    with patch.object(forecasts_api, 'make_api_request', return_value=station_response):
        result = forecasts_api.get_station_forecast('KJFK', output_file=str(output))
    assert result == expected_single_station(original)
    assert json.loads(output.read_text()) == result
    assert station_response == original


def test_csv_contains_every_time_and_field_from_station_series(station_response, tmp_path):
    original = copy.deepcopy(station_response)
    output = tmp_path / 'station.csv'
    with patch.object(forecasts_api, 'make_api_request', return_value=station_response):
        result = forecasts_api.get_station_forecast('KJFK', output_file=str(output))
    with output.open(newline='') as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 2
    for actual, expected in zip(rows, original['forecasts'][0]):
        assert set(actual) == set(expected)
        for field, value in expected.items():
            assert actual[field] == ('None' if value is None else str(value))
    assert result == expected_single_station(original)
    assert station_response == original


@pytest.mark.parametrize('model', [None, 'mm', 'metamesh'])
def test_cli_parser_reaches_station_query_with_filename_after_options(
    model, station_response, tmp_path
):
    output = tmp_path / 'cli-station.json'
    arguments = ['windborne', 'station_forecast', 'kjfk', '--init-time', '2026102205']
    if model is not None:
        arguments.extend(['--model', model])
    arguments.append(str(output))
    with patch('sys.argv', arguments), \
            patch.object(forecasts_api, 'make_api_request', return_value=station_response) as request:
        cli.main()
    request.assert_called_once_with(
        forecasts_api.FORECASTS_API_BASE_URL + '/' + (model or 'wm') + '/point_forecast',
        params={'stations': 'KJFK', 'initialization_time': '2026-10-22T05:00:00'},
    )
    assert json.loads(output.read_text()) == expected_single_station(station_response)


@pytest.mark.parametrize('model', ['wm', 'gfs'])
def test_failed_request_preserves_existing_output_and_returns_none(model, tmp_path):
    output = tmp_path / 'station.json'
    output.write_text('existing output')
    with patch.object(forecasts_api, 'make_api_request', return_value=None):
        assert forecasts_api.get_station_forecast('KJFK', output_file=str(output), model=model) is None
    assert output.read_text() == 'existing output'


@pytest.mark.parametrize('forecasts', [[], [[]]])
def test_empty_station_results_return_normally_without_overwriting(forecasts, tmp_path, capsys):
    response = {'initialization_time': '2026-10-22T05:00:00Z', 'forecasts': forecasts}
    output = tmp_path / 'station.csv'
    output.write_text('existing output')
    with patch.object(forecasts_api, 'make_api_request', return_value=response):
        assert forecasts_api.get_station_forecast('KJFK', output_file=str(output)) is None
    assert output.read_text() == 'existing output'
    assert 'No point forecasts found for station KJFK' in capsys.readouterr().out


@pytest.mark.parametrize('station', ['KJFK;PANC', 'KJFK,PANC', '   '])
def test_multiple_or_blank_station_ids_rejected_before_request(station):
    with patch.object(forecasts_api, 'make_api_request') as request:
        with pytest.raises(ValueError, match='one station ID'):
            forecasts_api.get_station_forecast(station)
    request.assert_not_called()


@pytest.mark.parametrize('empty_first_group', [False, True])
def test_extra_forecast_groups_cannot_be_silently_discarded(
    empty_first_group, station_response, tmp_path
):
    response = copy.deepcopy(station_response)
    response['forecasts'] = [
        [] if empty_first_group else response['forecasts'][0],
        [{'time': '2026-10-22T05:00:00Z', 'station_id': 'PANC', 'latitude': 61.17, 'longitude': -150}],
    ]
    original = copy.deepcopy(response)
    output = tmp_path / 'station.json'
    output.write_text('existing output')
    with patch.object(forecasts_api, 'make_api_request', return_value=response):
        with pytest.raises(ValueError, match='exactly one station'):
            forecasts_api.get_station_forecast('KJFK', output_file=str(output))
    assert response == original
    assert output.read_text() == 'existing output'


@pytest.mark.parametrize('station', [None, ''])
def test_missing_station_id_still_returns_before_request(station, capsys):
    with patch.object(forecasts_api, 'make_api_request') as request:
        assert forecasts_api.get_station_forecast(station) is None
    request.assert_not_called()
    assert 'provide a station_id' in capsys.readouterr().out
