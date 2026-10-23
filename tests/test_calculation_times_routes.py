"""Exercise public calculation-times routes through SDK and CLI to HTTP.

Contract: Engine's forecast-availability/calculation_times.astro documents
/forecasts/v1/{model}/calculation_times/{calculation_type}; api_infra/nginx.conf
routes that namespace for both degree_days and tropical_cyclones.
"""
import json
from unittest.mock import patch

import pytest
import requests

from windborne import api_request, cli, forecasts_api


@pytest.mark.parametrize('entrypoint', ['sdk', 'cli'])
@pytest.mark.parametrize('product,model,expected_path', [
    ('tropical_cyclones', None, '/forecasts/v1/wm-6/calculation_times/tropical_cyclones'),
    ('degree_days', None, '/forecasts/v1/wm/calculation_times/degree_days'),
    ('degree_days', 'wm-6', '/forecasts/v1/wm-6/calculation_times/degree_days'),
    ('degree_days', 'gfs', '/forecasts/v1/gfs/calculation_times/degree_days'),
])
def test_calculation_times_reaches_public_http_route(entrypoint, product, model, expected_path, capsys):
    payload = {
        'latest': '2026-10-12T00:00:00Z',
        'available': ['2026-10-12T00:00:00Z'],
        'in_progress': [], 'incomplete': [],
    }
    response = requests.Response()
    response.status_code = 200
    response._content = json.dumps(payload).encode('utf-8')
    with patch.object(api_request, 'get_verified_api_credentials', return_value=('sdk_test', 'x' * 32)), \
            patch.object(api_request.requests, 'get', return_value=response) as get:
        if entrypoint == 'sdk':
            function = getattr(forecasts_api, 'get_calculation_times_' + product)
            assert function(**({'model': model} if model is not None else {})) == payload
        else:
            arguments = ['windborne', 'calculation_times', product]
            if model is not None:
                arguments.extend(['--model', model])
            with patch('sys.argv', arguments):
                cli.main()
            assert payload['latest'] in capsys.readouterr().out
    get.assert_called_once()
    assert get.call_args.args[0] == 'https://api.windbornesystems.com' + expected_path
