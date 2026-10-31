"""Exercise the coordinate forms used by the published sounding examples."""
import copy
import json
from unittest.mock import patch

import pytest

from windborne import get_interpolated_sounding
from windborne import forecasts_api


@pytest.fixture
def sounding():
    return {
        'initialization_time': '2026-01-20T00:00:00Z',
        'forecast_zero': '2026-01-20T00:00:00Z',
        'time': '2026-01-20T12:00:00Z',
        'forecast_hour': 12,
        'latitude': 40.7,
        'longitude': -74.0,
        'data': [{'pressure_hpa': 1000, 'altitude_m': 100, 'temperature_c': 12,
                  'dewpoint_c': 8, 'specific_humidity_kg_kg': 0.006,
                  'wind_u_ms': 1, 'wind_v_ms': 2}],
    }


@pytest.mark.parametrize('example', ['valid_time_print', 'initialization_file', 'data_return'])
def test_published_tuple_examples(example, sounding, tmp_path, capsys):
    options = {'time': '2026-01-20T12:00:00Z'}
    if example == 'valid_time_print':
        options['print_response'] = True
    elif example == 'initialization_file':
        options = {'initialization_time': '2026-01-20T00:00:00Z',
                   'forecast_hour': 12, 'output_file': str(tmp_path / 'sounding.json')}
    original = copy.deepcopy(sounding)
    with patch.object(forecasts_api, 'make_api_request', return_value=sounding) as request:
        result = get_interpolated_sounding(coordinates=(40.7, -74.0), model='wm-6', **options)
    expected = {'coordinates': '40.7,-74.0'}
    if example == 'initialization_file':
        expected.update(initialization_time='2026-01-20T00:00:00Z', forecast_hour=12)
        assert json.loads((tmp_path / 'sounding.json').read_text()) == sounding
    else:
        expected['time'] = '2026-01-20T12:00:00Z'
    request.assert_called_once_with(
        forecasts_api.MODELS_API_BASE_URL + '/wm-6/point_forecast/interpolated_sounding',
        params=expected,
    )
    assert result is sounding
    assert sounding == original
    assert result['data'][0]['temperature_c'] == 12
    if example == 'valid_time_print':
        assert '1000' in capsys.readouterr().out


@pytest.mark.parametrize('coordinates,expected', [
    ('40.7,-74.0', '40.7,-74.0'),
    (' 40.7, -74.0 ', '40.7,-74.0'),
    ((0, 0), '0,0'),
])
def test_coordinate_strings_and_zero_tuple(coordinates, expected, sounding):
    with patch.object(forecasts_api, 'make_api_request', return_value=sounding) as request:
        result = get_interpolated_sounding(coordinates, initialization_time='2026012000',
                                          forecast_hour=0, model='wm-6')
    assert request.call_args.kwargs['params']['coordinates'] == expected
    assert request.call_args.kwargs['params']['forecast_hour'] == 0
    assert result is sounding


@pytest.mark.parametrize('coordinates', [(), (40.7,), (40.7, -74.0, 100)])
def test_invalid_tuple_length_is_rejected_before_request(coordinates):
    with patch.object(forecasts_api, 'make_api_request') as request:
        with pytest.raises(ValueError, match='latitude.*longitude'):
            get_interpolated_sounding(coordinates, time='2026-01-20T12:00:00Z', model='wm-6')
    request.assert_not_called()
