"""Run Custom Calculations commands through the real SDK to mocked HTTP."""

import io
import json
import zipfile
from unittest.mock import patch

import pytest
import requests

from windborne import api_request, cli


BASE_URL = 'https://api.windbornesystems.com/weather/v1/custom-calculations'
CALCULATION = '[temperature_2m] - 273.15'
INITIALIZATION = '2026-10-21T23:00:00Z'
COORDINATES = '37.7749,-122.4194;34.0522,-118.2437'


@pytest.fixture
def http(monkeypatch):
    monkeypatch.setattr(api_request, 'get_verified_api_credentials',
                        lambda: ('sdk_test', 'x' * 32))
    response = requests.Response()
    response.status_code = 200
    response._content = b'{}'
    with patch.object(api_request.requests, 'request', return_value=response) as request:
        yield request, response


def invoke(operation, body, *arguments):
    with patch('sys.argv', ['windborne', 'custom_calculations', operation,
                            '--body', '-'] + list(arguments)), \
            patch('sys.stdin', io.StringIO(json.dumps(body))):
        cli.main()


def assert_request(request, operation, body):
    request.assert_called_once()
    args, kwargs = request.call_args
    assert args == ('POST', BASE_URL + '/' + operation)
    assert kwargs['json'] == body
    assert kwargs['allow_redirects'] is False
    assert kwargs['auth'][0] == 'sdk_test'
    assert set(kwargs) == {'json', 'auth', 'allow_redirects'}


@pytest.mark.parametrize('valid', [True, False])
def test_validation_prints_valid_and_invalid_http_200_results(http, capsys, valid):
    request, response = http
    result = {'valid': valid, 'errors': [] if valid else [
        {'code': 'INVALID_CALCULATION', 'message': 'Expected closing bracket at 16'}]}
    response._content = json.dumps(result).encode()
    body = {'calculation': CALCULATION}
    invoke('validate', body)
    assert_request(request, 'validate', body)
    assert json.loads(capsys.readouterr().out) == result


def test_validation_reads_json_file_and_writes_complete_result(http, tmp_path, capsys):
    request, response = http
    result = {'valid': False, 'errors': [{'code': 'INVALID_TIME_WINDOW', 'message': 'Bad window'}]}
    response._content = json.dumps(result).encode()
    body = {'calculation': '[temperature_2m]'}
    body_file = tmp_path / 'request.json'
    body_file.write_text(json.dumps(body))
    output = tmp_path / 'validation.json'
    with patch('sys.argv', ['windborne', 'custom-calculations', 'validate',
                            '-o', str(output), '--body', str(body_file)]):
        cli.main()
    assert_request(request, 'validate', body)
    assert json.loads(output.read_text()) == result
    assert capsys.readouterr().out == ''


@pytest.mark.parametrize('hours', [None, 0, 6, [0, 6, 12], {'start': 0, 'end': 12}])
def test_points_preserves_forecast_hour_forms_and_partial_results(http, capsys, hours):
    request, response = http
    body = {'calculation': CALCULATION, 'coordinates': COORDINATES}
    if hours is not None:
        body['forecast_hours'] = hours
    result = {
        'model': 'wm-6', 'initialization_time': INITIALIZATION,
        'forecast_zero': '2026-10-21T18:00:00Z', 'forecast_hours': [0, 6, 12],
        'calculation': CALCULATION, 'output_calculations': [CALCULATION],
        'coordinates': COORDINATES,
        'results': [{'forecast_hour': 0, 'outputs': [
            {'valid_from': None, 'valid_to': None, 'values': [0, None]}]}],
        'forecast_hour_errors': [{'forecast_hour': 12, 'code': 'MISSING_INPUT_DATA',
                                 'message': 'Required input is unavailable'}],
    }
    response._content = json.dumps(result).encode()
    invoke('points', body)
    assert_request(request, 'points', dict(body, model='wm-6'))
    assert json.loads(capsys.readouterr().out) == result


def test_points_body_model_and_initialization_are_honored_in_json_output(http, tmp_path):
    request, response = http
    body = {'calculation': CALCULATION, 'coordinates': COORDINATES,
            'model': 'wm-6-3km', 'initialization_time': INITIALIZATION,
            'forecast_hours': [0]}
    result = {'model': 'wm-6-3km', 'results': [], 'forecast_hour_errors': [],
              'future_metadata': [0, False, None]}
    response._content = json.dumps(result).encode()
    output = tmp_path / 'nested' / 'points.json'
    invoke('points', body, '--output', str(output))
    assert_request(request, 'points', body)
    assert json.loads(output.read_text()) == result


@pytest.mark.parametrize('calculation,source,valid_from', [
    ('aggregate_forecast_hours([temperature_2m], min, 0)', 'stdin',
     '2026-10-21T18:00:00Z'),
    ('aggregate_members([temperature_2m(members)], p90)', 'file',
     '2026-10-22T00:00:00Z'),
])
def test_aggregation_expressions_need_no_extra_request_fields(
        http, tmp_path, calculation, source, valid_from):
    request, response = http
    expression = '\n  ' + calculation + '\n'
    body = {'calculation': expression, 'coordinates': COORDINATES,
            'forecast_hours': [12, 6, 12]}
    result = {
        'model': 'wm-6', 'initialization_time': INITIALIZATION,
        'forecast_zero': '2026-10-21T18:00:00Z', 'forecast_hours': [6, 12],
        'calculation': expression, 'output_calculations': [calculation],
        'coordinates': COORDINATES,
        'results': [{'forecast_hour': 6, 'outputs': [{
            'valid_from': valid_from, 'valid_to': '2026-10-22T00:00:00Z',
            'values': [275.25, None],
        }]}],
        'forecast_hour_errors': [{'forecast_hour': 12, 'code': 'MISSING_INPUT_DATA',
                                 'message': 'Required input is unavailable'}],
    }
    response._content = json.dumps(result).encode()
    output = tmp_path / 'aggregation.json'
    if source == 'stdin':
        invoke('points', body, '-o', str(output))
    else:
        body_file = tmp_path / 'request.json'
        body_file.write_text(json.dumps(body))
        with patch('sys.argv', ['windborne', 'custom_calculations', 'points',
                                '--body', str(body_file), '-o', str(output)]):
            cli.main()
    assert_request(request, 'points', dict(body, model='wm-6'))
    assert json.loads(output.read_text()) == result


@pytest.mark.parametrize('initialization_time', [None, INITIALIZATION])
def test_gridded_zip_written_without_printing_or_decoding(http, tmp_path, capsys, initialization_time):
    request, response = http
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, 'w') as zipped:
        zipped.writestr('zarr.json', json.dumps({
            'zarr_format': 3, 'node_type': 'group',
            'attributes': {'forecast_hour_errors': [{'forecast_hour': 12}]},
        }))
        zipped.writestr('result/0', b'\x00\xff\x80\x01')
    response._content = archive.getvalue()
    response.headers['Content-Type'] = 'application/zip'
    body = {'model': 'wm-6', 'calculation': CALCULATION, 'forecast_hours': [0, 6, 12],
            'bounds': {'min_latitude': 0, 'max_latitude': 50,
                       'min_longitude': 170, 'max_longitude': -170}, 'as_url': False}
    if initialization_time is not None:
        body['initialization_time'] = initialization_time
    output = tmp_path / 'result.zarr.zip'
    with patch.object(response, 'json', side_effect=AssertionError('ZIP must not be decoded')):
        invoke('gridded', body, '-o', str(output))
    assert_request(request, 'gridded', body)
    assert output.read_bytes() == archive.getvalue()
    assert capsys.readouterr().out == ''


@pytest.mark.parametrize('save_file', [False, True])
def test_gridded_download_url_preserves_full_envelope(http, tmp_path, capsys, save_file):
    request, response = http
    body = {'calculation': CALCULATION, 'initialization_time': INITIALIZATION, 'as_url': True}
    result = {'url': 'https://downloads.example.test/result.zarr.zip',
              'url_expires_at': '2026-10-22T00:30:00Z',
              'content_type': 'application/zip', 'size_bytes': 42}
    response._content = json.dumps(result).encode()
    output = tmp_path / 'download.json'
    invoke('gridded', body, *(['-o', str(output)] if save_file else []))
    assert_request(request, 'gridded', dict(body, model='wm-6'))
    text = output.read_text() if save_file else capsys.readouterr().out
    assert json.loads(text) == result


@pytest.mark.parametrize('operation,fields', [
    ('gridded', {'bounds': {'min_latitude': 0, 'max_latitude': 38}, 'as_url': True}),
    ('threshold', {
        'bounds': {'min_latitude': 0, 'max_latitude': 38, 'min_longitude': -123, 'max_longitude': 0},
        'threshold': {'kind': 'absolute', 'value': 0, 'comparison': 'at_or_below'},
    }),
])
def test_forecast_hour_range_reaches_calculation_with_nested_fields(http, capsys, operation, fields):
    request, _ = http
    body = dict(fields, calculation=CALCULATION, forecast_hours={'start': 0, 'end': 12})
    invoke(operation, body)
    assert_request(request, operation, dict(body, model='wm-6'))
    assert json.loads(capsys.readouterr().out) == {}


@pytest.mark.parametrize('threshold', [
    {'kind': 'absolute', 'value': 0, 'comparison': 'at_or_below'},
    {'kind': 'percentile', 'percentile': 10, 'direction': 'highest'},
])
@pytest.mark.parametrize('initialization_time', [None, INITIALIZATION])
def test_threshold_preserves_nested_fields_geojson_and_skipped_hours(
        http, tmp_path, threshold, initialization_time):
    request, response = http
    body = {'calculation': CALCULATION, 'forecast_hours': [0, 12],
            'bounds': {'min_latitude': 0, 'max_latitude': 38, 'min_longitude': -123, 'max_longitude': 0},
            'threshold': threshold}
    if initialization_time is not None:
        body['initialization_time'] = initialization_time
    result = {
        'type': 'FeatureCollection', 'model': 'wm-6', 'initialization_time': INITIALIZATION,
        'forecast_zero': '2026-10-21T18:00:00Z', 'forecast_hours': [0, 12],
        'calculation': CALCULATION, 'output_calculations': [CALCULATION],
        'threshold': threshold,
        'features': [{
            'type': 'Feature',
            'geometry': {'type': 'MultiPolygon', 'coordinates': [[[
                [-122.375, 37.875], [-122.125, 37.875], [-122.125, 38],
                [-122.375, 38], [-122.375, 37.875],
            ]]]},
            'properties': {'forecast_hour': 0, 'output_calculation': CALCULATION,
                           'valid_from': '2026-10-21T18:00:00Z',
                           'valid_to': '2026-10-21T18:00:00Z'},
        }],
        'forecast_hour_errors': [{'forecast_hour': 12, 'code': 'MISSING_INPUT_DATA',
                                 'message': 'Missing variable'}],
    }
    response._content = json.dumps(result).encode()
    output = tmp_path / 'result.geojson'
    invoke('threshold', body, '-o', str(output))
    assert_request(request, 'threshold', dict(body, model='wm-6'))
    assert json.loads(output.read_text()) == result


@pytest.mark.parametrize('operation,body,arguments,message', [
    ('validate', {}, [], 'calculation'),
    ('validate', [], [], 'JSON object'),
    ('validate', {'calculation': CALCULATION, 'unknown': 1}, [], 'Unsupported request fields: unknown'),
    ('validate', {'calculation': CALCULATION, 'output_file': 'override.json'}, [], 'output_file'),
    ('validate', {'calculation': CALCULATION, 'print_response': False}, [], 'print_response'),
    ('points', {'calculation': CALCULATION}, [], 'coordinates'),
    ('gridded', {'calculation': CALCULATION, 'initialization_time': INITIALIZATION}, [], '--output'),
    ('gridded', {'calculation': CALCULATION, 'initialization_time': INITIALIZATION, 'as_url': False}, [], '--output'),
    ('gridded', {'calculation': CALCULATION, 'initialization_time': INITIALIZATION, 'as_url': 'false'},
     ['-o', 'unused.zip'], 'as_url'),
    ('gridded', {'calculation': CALCULATION, 'initialization_time': INITIALIZATION}, ['-o', 'unused.json'], '.zip'),
    ('gridded', {'calculation': CALCULATION, 'initialization_time': INITIALIZATION, 'as_url': True},
     ['-o', 'unused.zip'], '.json'),
    ('points', {'calculation': CALCULATION, 'coordinates': COORDINATES}, ['-o', 'unused.csv'], '.json'),
    ('threshold', {'calculation': CALCULATION, 'initialization_time': INITIALIZATION}, [], 'bounds'),
    ('threshold', {'calculation': CALCULATION,
                   'bounds': {'min_latitude': 0, 'max_latitude': 38, 'min_longitude': -123, 'max_longitude': 0}},
     [], 'threshold'),
])
def test_invalid_bodies_and_output_options_fail_before_http(http, capsys, operation, body, arguments, message):
    request, _ = http
    with pytest.raises(SystemExit) as error:
        invoke(operation, body, *arguments)
    assert error.value.code == 2
    request.assert_not_called()
    assert message in capsys.readouterr().err


@pytest.mark.parametrize('contents', ['{', 'null', '1', '"calculation"'])
def test_invalid_json_stdin_fails_before_http(http, capsys, contents):
    request, _ = http
    with patch('sys.argv', ['windborne', 'custom_calculations', 'validate', '--body', '-']), \
            patch('sys.stdin', io.StringIO(contents)), pytest.raises(SystemExit) as error:
        cli.main()
    assert error.value.code == 2
    request.assert_not_called()
    assert 'JSON' in capsys.readouterr().err


def test_missing_json_file_fails_before_http(http, tmp_path, capsys):
    request, _ = http
    with patch('sys.argv', ['windborne', 'custom_calculations', 'validate',
                            '--body', str(tmp_path / 'missing.json')]), \
            pytest.raises(SystemExit) as error:
        cli.main()
    assert error.value.code == 2
    request.assert_not_called()
    assert 'Could not read JSON body' in capsys.readouterr().err


def test_post_error_is_not_retried_and_does_not_create_output(http, tmp_path):
    request, response = http
    response.status_code = 400
    response._content = b'{"error":"No selected forecast hours can be calculated"}'
    output = tmp_path / 'points.json'
    with pytest.raises(requests.HTTPError):
        invoke('points', {'calculation': CALCULATION, 'coordinates': COORDINATES}, '-o', str(output))
    request.assert_called_once()
    assert not output.exists()
