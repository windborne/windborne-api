"""The printed catalog must expose the derived and distribution selections."""
import copy
import json
from unittest.mock import patch

import pytest
import requests

from windborne import api_request, cli, get_variables


@pytest.mark.parametrize('entrypoint', ['sdk', 'cli'])
def test_complete_catalog_is_visible_without_changing_the_response(entrypoint, capsys):
    payload = {
        'sfc_variables': ['temperature_2m'],
        'upper_variables': ['temperature'],
        'derived_sfc_variables': ['wind_speed_10m'],
        'derived_upper_variables': ['wind_speed'],
        'levels': [500, 850],
        'distribution_details': {
            'sfc_variables': {'temperature_2m': ['mean', 'p90', 'members']},
            'derived_upper_variables': {'wind_speed': ['mean', 'det']},
        },
    }
    original = copy.deepcopy(payload)
    response = requests.Response()
    response.status_code = 200
    response._content = json.dumps(payload).encode('utf-8')
    with patch.object(api_request, 'get_verified_api_credentials', return_value=('sdk_test', 'x' * 32)), \
            patch.object(api_request.requests, 'get', return_value=response) as get:
        if entrypoint == 'sdk':
            assert get_variables(model='wm-6', print_response=True) == original
        else:
            with patch('sys.argv', ['windborne', 'variables', '--model', 'wm-6']):
                cli.main()

    get.assert_called_once()
    assert get.call_args.args[0] == 'https://api.windbornesystems.com/forecasts/v1/wm-6/variables'
    output = capsys.readouterr().out
    assert 'Derived surface variables:\n - wind_speed_10m' in output
    assert 'Derived upper variables:\n - wind_speed' in output
    assert json.loads(output.split('Distribution details:\n', 1)[1]) == payload['distribution_details']
    assert payload == original


@pytest.mark.parametrize('extra', [{}, {'derived_sfc_variables': [], 'derived_upper_variables': [], 'distribution_details': []}])
def test_legacy_catalog_printing_is_unchanged(extra, capsys):
    payload = dict(sfc_variables=['temperature_2m'], upper_variables=[], levels=[], **extra)
    with patch('windborne.forecasts_api.make_api_request', return_value=payload):
        assert get_variables(print_response=True) is payload
    assert capsys.readouterr().out == 'Surface variables:\n - temperature_2m\nNo upper variables available\nNo levels available\n'


def test_catalog_default_is_quiet_and_retains_extra_fields(capsys):
    payload = {'derived_sfc_variables': ['wind_speed_10m'], 'new_metadata': {'version': 1}}
    with patch('windborne.forecasts_api.make_api_request', return_value=payload):
        assert get_variables() is payload
    assert capsys.readouterr().out == ''
