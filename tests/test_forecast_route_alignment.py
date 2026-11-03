"""Product routes must preserve explicit legacy model choices and response shapes."""
import json
from unittest.mock import patch

import pytest

from windborne import forecasts_api as api


@pytest.mark.parametrize('model,path,response', [
    ('mm', '/models/v1/mm/point_forecast/stations', [{'station_id': 'KJFK'}]),
    ('metamesh', '/forecasts/v1/metamesh/point_forecast/stations',
     {'stations': [{'station_id': 'KJFK'}], 'metadata': {'source': 'fixture'}}),
    ('wm', '/forecasts/v1/wm/point_forecast/stations', [{'station_id': 'KJFK'}]),
])
def test_station_lists_keep_model_specific_shapes(model, path, response, tmp_path):
    # Engine deliberately keeps metamesh wrapped and mm unwrapped.
    output = str(tmp_path / 'stations.json')
    with patch.object(api, 'make_api_request', return_value=response) as request:
        result = api.get_available_stations(output, False, model)
    request.assert_called_once_with(api.API_BASE_URL + path)
    assert result is response
    assert json.loads((tmp_path / 'stations.json').read_text()) == response


@pytest.mark.parametrize('model,path', [
    ('wm', '/weather/v1/point'),
    ('mm', '/weather/v1/point'),
    ('metamesh', '/weather/v1/point'),
    ('gfs', '/forecasts/v1/gfs/point_forecast'),
])
def test_point_model_aliases_do_not_replace_an_explicit_other_model(model, path):
    response = {'forecasts': [], 'metadata': {'future': [None, False, 0]}}
    with patch.object(api, 'make_api_request', return_value=response) as request:
        result = api.get_point_forecasts('37,-122', model=model, min_forecast_hour=0)
    request.assert_called_once_with(
        api.API_BASE_URL + path, params={'coordinates': '37,-122', 'min_forecast_hour': 0},
    )
    assert result is response


@pytest.mark.parametrize('model', ['gfs', 'ecmwf-det', 'wm6'])
@pytest.mark.parametrize('function,arguments,suffix', [
    (api.get_tropical_cyclone, ('AL012026',), '/AL012026'),
    (api.get_tropical_cyclone_index, (), '/index'),
    (api.get_tropical_cyclone_init_times, ('AL012026',), '/AL012026/init_times'),
])
def test_explicit_other_tc_models_keep_their_route(function, arguments, suffix, model):
    response = {'tropical_cyclones': {}, 'available': [], 'metadata': {'future': None}}
    with patch.object(api, 'make_api_request', return_value=response) as request:
        assert function(*arguments, model=model) is response
    assert request.call_args.args[0] == api.FORECASTS_API_BASE_URL + '/' + model + '/tropical_cyclones' + suffix


def test_conditions_other_model_is_not_silently_changed():
    response = {'forecasts': []}
    with patch.object(api, 'make_api_request', return_value=response) as request:
        assert api.get_point_forecast_conditions('37,-122', model='gfs') is response
    request.assert_called_once_with(
        api.FORECASTS_API_BASE_URL + '/gfs/point_forecast/conditions',
        params={'coordinates': '37,-122'},
    )
