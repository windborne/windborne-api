"""Analysis source names must resolve to the matching model catalog."""
from unittest.mock import patch

import pytest

from windborne import cli, forecasts_api as api


CATALOG = {
    'sfc_variables': ['temperature_2m', 'pressure_msl'],
    'upper_variables': ['temperature', 'geopotential'],
    'levels': [500, 850],
    'derived_sfc_variables': ['winds_10m'],
    'derived_upper_variables': ['winds'],
    'distribution_details': {},
}


@pytest.mark.parametrize('source,model', [
    ('ecmwf_det_anl', 'ifs_anl'),
    ('ecmwf_ens_anl', 'ens_anl'),
    ('era5', 'era5'),
    ('ifs_anl', 'ifs_anl'),
    ('ens_anl', 'ens_anl'),
    ('custom_analysis', 'custom_analysis'),
])
def test_analysis_source_uses_model_catalog_and_preserves_response(source, model, capsys):
    with patch.object(api, 'make_api_request', return_value=CATALOG) as request:
        result = api.get_analysis_variables(source)
    request.assert_called_once_with(api.FORECASTS_API_BASE_URL + '/' + model + '/variables')
    assert result is CATALOG
    assert capsys.readouterr().out == ''


def test_default_analysis_source_uses_deterministic_analysis_catalog():
    with patch.object(api, 'make_api_request', return_value=CATALOG) as request:
        assert api.get_analysis_variables() is CATALOG
    request.assert_called_once_with(api.FORECASTS_API_BASE_URL + '/ifs_anl/variables')


@pytest.mark.parametrize('response', [CATALOG, {'analysis': CATALOG}])
def test_positional_print_option_supports_both_existing_response_shapes(response, capsys):
    with patch.object(api, 'make_api_request', return_value=response) as request:
        assert api.get_analysis_variables('ecmwf_ens_anl', True) is response
    request.assert_called_once_with(api.FORECASTS_API_BASE_URL + '/ens_anl/variables')
    assert capsys.readouterr().out == (
        'Surface variables:\n - temperature_2m\n - pressure_msl\n'
        'Upper variables:\n - temperature\n - geopotential\n'
        'Levels:\n - 500\n - 850\n'
    )


def test_failed_request_keeps_none_return_and_does_not_print(capsys):
    with patch.object(api, 'make_api_request', return_value=None):
        assert api.get_analysis_variables(print_response=True) is None
    assert capsys.readouterr().out == ''


@pytest.mark.parametrize('arguments,model', [
    ([], 'ifs_anl'),
    (['--source', 'ecmwf_det_anl'], 'ifs_anl'),
    (['--source', 'ecmwf_ens_anl'], 'ens_anl'),
    (['--source', 'era5'], 'era5'),
    (['--source', 'ifs_anl'], 'ifs_anl'),
    (['--source', 'ens_anl'], 'ens_anl'),
])
def test_cli_dispatch_reaches_catalog_and_prints_values(arguments, model, capsys):
    # Exercise the parser and real SDK helper together, replacing only HTTP.
    with patch.object(api, 'make_api_request', return_value=CATALOG) as request:
        with patch('sys.argv', ['windborne', 'analysis_variables'] + arguments):
            cli.main()
    request.assert_called_once_with(api.FORECASTS_API_BASE_URL + '/' + model + '/variables')
    output = capsys.readouterr().out
    assert 'Surface variables:\n - temperature_2m\n - pressure_msl' in output
    assert 'Upper variables:\n - temperature\n - geopotential' in output
    assert 'Levels:\n - 500\n - 850' in output
