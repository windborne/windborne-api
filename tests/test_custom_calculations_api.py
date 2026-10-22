"""Current Custom Calculation contracts, checked against backend and live output."""

import copy
import io
import json
import zipfile
from unittest.mock import patch

import jwt
import pytest
import requests

import windborne
from windborne import api_request, custom_calculations_api as calculations


BASE = 'https://api.windbornesystems.com/insights/v1/custom-calculations'
INITIALIZATION = '2026-10-16T18:00:00Z'
EXPRESSION = '[max_temperature_2m_3h] - [min_temperature_2m_3h]'
COORDINATES = '37.7749,-122.4194;34.0522,-118.2437'
BOUNDS = {'min_lat': 37, 'max_lat': 38, 'min_lon': -123, 'max_lon': -122}
THRESHOLD = {'kind': 'percentile', 'percentile': 10, 'direction': 'highest'}


def response(payload=None, *, content=None, status=200):
    result = requests.Response()
    result.status_code = status
    result.url = BASE
    result._content = content if content is not None else json.dumps(payload).encode('utf-8')
    return result


@pytest.fixture(autouse=True)
def fake_credentials(monkeypatch):
    monkeypatch.setattr(api_request, 'get_verified_api_credentials', lambda: ('sdk_test', 'x' * 32))


@pytest.fixture
def archive():
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as output:
        output.writestr('zarr.json', json.dumps({
            'zarr_format': 3, 'node_type': 'group', 'attributes': {
                'model': 'wm-6', 'initialization_time': INITIALIZATION,
                'forecast_zero': '2026-10-16T12:00:00Z', 'forecast_hours': [0, 6, 12],
                'calculation': EXPRESSION,
                'grid_calculations': [EXPRESSION],
                'evaluations': [{'forecast_hour': 6}, {'forecast_hour': 12}],
                'forecast_hour_errors': [{'forecast_hour': 0, 'code': 'MISSING_DATA', 'message': 'Input unavailable'}],
            },
        }))
        output.writestr('result/c/0/0/0/0/0', b'\x00\xff\x80\x00\x01')
    return buffer.getvalue()


def assert_post(request, route, body):
    request.assert_called_once()
    args, kwargs = request.call_args
    assert args == ('POST', BASE + '/' + route)
    assert set(kwargs) == {'auth', 'allow_redirects', 'json'}
    assert kwargs['allow_redirects'] is False
    assert kwargs['json'] == body
    # Real transport serialization must retain JSON numbers, booleans and arrays.
    assert json.loads(json.dumps(kwargs['json'])) == body
    client_id, token = kwargs['auth']
    assert client_id == 'sdk_test'
    assert jwt.decode(token, 'x' * 32, algorithms=['HS256'])['client_id'] == client_id


@pytest.mark.parametrize('helper', [
    'validate_calculation', 'calculate_gridded', 'calculate_points', 'calculate_threshold',
])
def test_helpers_exported_at_package_root(helper):
    assert getattr(windborne, helper) is getattr(calculations, helper)
    assert helper in windborne.__all__


@pytest.mark.parametrize('payload', [
    {'valid': True, 'errors': []},
    {'valid': False, 'errors': [{'code': 'INVALID_CALCULATION', 'message': 'Expected closing bracket at 20'}]},
])
def test_validation_preserves_http_200_result_and_expression(payload, tmp_path, capsys):
    expression = '  [temperature_2m] +\ninvalid syntax  '
    output = tmp_path / 'nested' / 'validation.json'
    with patch.object(api_request.requests, 'request', return_value=response(payload)) as request:
        result = windborne.validate_calculation(expression, output_file=output, print_response=True)
    assert_post(request, 'validate', {'calculation': expression})
    assert result == payload
    assert json.loads(output.read_text()) == payload
    assert json.loads(capsys.readouterr().out) == payload


def test_gridded_binary_preserves_archive_and_all_documented_options(archive, tmp_path, capsys):
    output = tmp_path / 'nested' / 'result.zarr.zip'
    hours, lat_range, lon_range = [0, 6, 12], [24, 50], [170, -170]
    with patch.object(api_request.requests, 'request', return_value=response(content=archive)) as request:
        result = windborne.calculate_gridded(
            EXPRESSION, INITIALIZATION, forecast_hours=hours,
            lat_range=lat_range, lon_range=lon_range, output_file=output,
        )
    assert_post(request, 'gridded', {
        'model': 'wm-6', 'initialization_time': INITIALIZATION, 'calculation': EXPRESSION,
        'forecast_hours': [0, 6, 12], 'lat_range': [24, 50], 'lon_range': [170, -170],
        'as_url': False,
    })
    assert isinstance(result, bytes)
    assert result == output.read_bytes() == archive
    with zipfile.ZipFile(output) as saved:
        assert saved.read('result/c/0/0/0/0/0') == b'\x00\xff\x80\x00\x01'
        metadata = json.loads(saved.read('zarr.json'))['attributes']
        assert metadata['forecast_hour_errors'][0]['forecast_hour'] == 0
        assert metadata['forecast_hours'] == [0, 6, 12]
        assert metadata['grid_calculations'] == [EXPRESSION]
    assert hours == [0, 6, 12]
    assert lat_range == [24, 50]
    assert lon_range == [170, -170]
    assert capsys.readouterr().out == ''


def test_gridded_default_returns_bytes_without_requiring_a_file(archive):
    with patch.object(api_request.requests, 'request', return_value=response(content=archive)) as request:
        result = windborne.calculate_gridded(EXPRESSION, model='wm-6-3km')
    assert result == archive
    assert_post(request, 'gridded', {
        'model': 'wm-6-3km', 'calculation': EXPRESSION, 'as_url': False,
    })


def test_gridded_url_returns_metadata_without_following_signed_url(tmp_path, capsys):
    payload = {
        'url': 'https://example.invalid/result.zarr.zip?signature=synthetic',
        'url_expires_at': '2026-10-22T01:30:00Z',
        'content_type': 'application/zip', 'size_bytes': 12345,
    }
    output = tmp_path / 'download.json'
    with patch.object(api_request.requests, 'request', return_value=response(payload)) as request:
        result = windborne.calculate_gridded(
            EXPRESSION, INITIALIZATION, as_url=True, output_file=output, print_response=True,
        )
    assert_post(request, 'gridded', {
        'model': 'wm-6', 'initialization_time': INITIALIZATION,
        'calculation': EXPRESSION, 'as_url': True,
    })
    assert result == json.loads(output.read_text()) == payload
    assert json.loads(capsys.readouterr().out) == payload


def test_points_omits_initialization_and_hours_for_latest_complete_update():
    payload = {'results': [], 'forecast_hour_errors': []}
    with patch.object(api_request.requests, 'request', return_value=response(payload)) as request:
        result = windborne.calculate_points(EXPRESSION, COORDINATES)
    assert result == payload
    assert_post(request, 'points', {
        'model': 'wm-6', 'calculation': EXPRESSION, 'coordinates': COORDINATES,
    })


def test_points_keeps_nulls_grid_order_and_partial_failures(tmp_path, capsys):
    payload = {
        'model': 'wm-6-3km', 'initialization_time': INITIALIZATION,
        'forecast_zero': '2026-10-16T12:00:00Z', 'forecast_hours': [0, 6],
        'calculation': EXPRESSION, 'grid_calculations': [EXPRESSION, 'another grid'],
        'coordinates': COORDINATES,
        'forecast_hour_errors': [{'forecast_hour': 0, 'code': 'MISSING_DATA', 'message': 'Unavailable input'}],
        'results': [{'forecast_hour': 6, 'grids': [
            {'valid_from': '2026-10-16T18:00:00Z', 'valid_to': '2026-10-16T18:00:00Z', 'values': [1.25, None]},
            {'valid_from': None, 'valid_to': None, 'values': [None, 0]},
        ]}],
    }
    output = tmp_path / 'nested' / 'points.json'
    with patch.object(api_request.requests, 'request', return_value=response(payload)) as request:
        result = windborne.calculate_points(
            EXPRESSION, COORDINATES, model='wm-6-3km', initialization_time=INITIALIZATION,
            forecast_hours=[0, 6], output_file=output, print_response=True,
        )
    assert_post(request, 'points', {
        'model': 'wm-6-3km', 'initialization_time': INITIALIZATION,
        'calculation': EXPRESSION, 'coordinates': COORDINATES, 'forecast_hours': [0, 6],
    })
    assert result == json.loads(output.read_text()) == payload
    assert json.loads(capsys.readouterr().out) == payload


@pytest.mark.parametrize('extension', ['.json', '.geojson'])
@pytest.mark.parametrize('threshold', [
    THRESHOLD, {'kind': 'absolute', 'value': 0, 'comparison': 'at_or_below'},
])
def test_threshold_preserves_geometry_metadata_partial_errors_and_input(threshold, extension, tmp_path, capsys):
    bounds = copy.deepcopy(BOUNDS)
    threshold_before = copy.deepcopy(threshold)
    payload = {
        'model': 'wm-6-3km', 'initialization_time': INITIALIZATION,
        'forecast_zero': '2026-10-16T12:00:00Z', 'forecast_hours': [0, 6],
        'calculation': EXPRESSION, 'grid_calculations': [EXPRESSION],
        'type': 'FeatureCollection', 'features': [{
            'type': 'Feature',
            'geometry': {'type': 'MultiPolygon', 'coordinates': [[[[-123, 37], [-122, 37], [-122, 38], [-123, 37]]]]},
            'properties': {
                'forecast_hour': 0, 'grid_calculation': EXPRESSION,
                'time': {'kind': 'mixed'}, 'level': {'kind': 'reduced'},
                'member': {'kind': 'exact', 'member': 0}, 'threshold': threshold,
                'resolved_threshold': 0, 'comparison': '<=', 'finite_cell_count': 25, 'selected_cell_count': 3,
            },
        }], 'forecast_hour_errors': [{'forecast_hour': 6, 'code': 'MISSING_DATA', 'message': 'Unavailable input'}],
    }
    output = tmp_path / 'nested' / ('threshold' + extension)
    with patch.object(api_request.requests, 'request', return_value=response(payload)) as request:
        result = windborne.calculate_threshold(
            EXPRESSION, bounds, threshold, initialization_time=INITIALIZATION, model='wm-6-3km',
            forecast_hours=[0, 6], output_file=output, print_response=True,
        )
    assert_post(request, 'threshold', {
        'model': 'wm-6-3km', 'calculation': EXPRESSION, 'initialization_time': INITIALIZATION,
        'bounds': BOUNDS, 'threshold': threshold_before, 'forecast_hours': [0, 6],
    })
    assert result == json.loads(output.read_text()) == payload
    assert json.loads(capsys.readouterr().out) == payload
    assert bounds == BOUNDS
    assert threshold == threshold_before


@pytest.mark.parametrize('helper,arguments,route', [
    (windborne.calculate_gridded, {'as_url': True}, 'gridded'),
    (windborne.calculate_points, {'coordinates': COORDINATES}, 'points'),
    (windborne.calculate_threshold, {'bounds': BOUNDS, 'threshold': THRESHOLD}, 'threshold'),
])
@pytest.mark.parametrize('initialization', [{}, {'initialization_time': None}])
def test_all_calculations_omit_unspecified_initialization_for_latest_complete_update(
    helper, arguments, route, initialization,
):
    with patch.object(api_request.requests, 'request', return_value=response({})) as request:
        helper(EXPRESSION, **arguments, **initialization)
    assert_post(request, route, {'model': 'wm-6', 'calculation': EXPRESSION, **arguments})


@pytest.mark.parametrize('helper,arguments', [
    (windborne.calculate_gridded, {'initialization_time': INITIALIZATION, 'as_url': True}),
    (windborne.calculate_points, {'coordinates': COORDINATES}),
    (windborne.calculate_threshold, {'initialization_time': INITIALIZATION, 'bounds': BOUNDS, 'threshold': THRESHOLD}),
])
@pytest.mark.parametrize('hours', [None, 0, [0], [0, 6, 12]])
def test_hour_selection_preserves_omitted_integer_zero_and_list(helper, arguments, hours):
    with patch.object(api_request.requests, 'request', return_value=response({})) as request:
        helper(EXPRESSION, forecast_hours=hours, **arguments)
    body = request.call_args.kwargs['json']
    if hours is None:
        assert 'forecast_hours' not in body
        return
    assert body['forecast_hours'] == hours
    assert type(body['forecast_hours']) is type(hours)


CASES = [
    (windborne.validate_calculation, {}, '.json'),
    (windborne.calculate_gridded, {'initialization_time': INITIALIZATION}, '.zip'),
    (windborne.calculate_gridded, {'initialization_time': INITIALIZATION, 'as_url': True}, '.json'),
    (windborne.calculate_points, {'coordinates': COORDINATES}, '.json'),
    (windborne.calculate_threshold, {'initialization_time': INITIALIZATION, 'bounds': BOUNDS, 'threshold': THRESHOLD}, '.geojson'),
]


@pytest.mark.parametrize('helper,arguments,extension', CASES)
def test_lossy_output_rejected_before_request(helper, arguments, extension, tmp_path):
    output = tmp_path / 'existing.csv'
    output.write_text('keep existing file')
    with patch.object(api_request.requests, 'request') as request:
        with pytest.raises(ValueError, match='output files must use'):
            helper(EXPRESSION, output_file=output, **arguments)
    request.assert_not_called()
    assert output.read_text() == 'keep existing file'


@pytest.mark.parametrize('arguments', [
    {'print_response': True}, {'print_response': True, 'output_file': 'result.zip'},
    {'as_url': False, 'output_file': 'result.json'},
    {'as_url': True, 'output_file': 'result.zip'},
    {'as_url': 'false'}, {'as_url': 'true'}, {'as_url': 1},
])
def test_gridded_invalid_output_mode_prevents_calculation(arguments):
    with patch.object(api_request.requests, 'request') as request:
        with pytest.raises(ValueError):
            windborne.calculate_gridded(EXPRESSION, INITIALIZATION, **arguments)
    request.assert_not_called()


@pytest.mark.parametrize('coordinates', [None, '', '  ', [], [(0, 0)], 42])
def test_points_requires_documented_coordinate_string(coordinates):
    with patch.object(api_request.requests, 'request') as request:
        with pytest.raises(ValueError, match='coordinates'):
            windborne.calculate_points(EXPRESSION, coordinates)
    request.assert_not_called()


@pytest.mark.parametrize('helper,arguments,extension', CASES)
@pytest.mark.parametrize('status', [400, 403, 502])
def test_http_failure_preserves_error_response_and_existing_file_without_retry(
    helper, arguments, extension, status, tmp_path, capsys,
):
    payload = {'error': 'Request failed'}
    if status == 400 and helper is not windborne.validate_calculation:
        payload = {
            'error': 'No selected hour can be calculated',
            'forecast_hour_errors': [
                {'forecast_hour': 0, 'code': 'MISSING_DATA', 'message': 'Unavailable input'},
                {'forecast_hour': 6, 'code': 'MISSING_DATA', 'message': 'Unavailable input'},
            ],
        }
    failed = response(payload, status=status)
    output = tmp_path / ('existing' + extension)
    output.write_bytes(b'keep existing file')
    with patch.object(api_request.requests, 'request', return_value=failed) as request:
        with pytest.raises(requests.HTTPError) as caught:
            helper(EXPRESSION, output_file=output, **arguments)
    assert caught.value.response is failed
    assert caught.value.response.json() == payload
    request.assert_called_once()
    assert output.read_bytes() == b'keep existing file'
    assert capsys.readouterr().out == ''


@pytest.mark.parametrize('helper,arguments,extension', CASES)
@pytest.mark.parametrize('error', [requests.Timeout('timed out'), requests.ConnectionError('disconnected')])
def test_transport_errors_propagate_without_replaying_calculation(helper, arguments, extension, error):
    with patch.object(api_request.requests, 'request', side_effect=error) as request:
        with pytest.raises(type(error)) as caught:
            helper(EXPRESSION, **arguments)
    assert caught.value is error
    request.assert_called_once()


@pytest.mark.parametrize('helper,arguments,extension', [case for case in CASES if case[2] != '.zip'])
def test_malformed_json_raises_without_overwriting_existing_output(helper, arguments, extension, tmp_path):
    output = tmp_path / ('existing' + extension)
    output.write_text('keep existing file')
    with patch.object(api_request.requests, 'request', return_value=response(content=b'not json')) as request:
        with pytest.raises(ValueError):
            helper(EXPRESSION, output_file=output, **arguments)
    request.assert_called_once()
    assert output.read_text() == 'keep existing file'


@pytest.mark.parametrize('helper,arguments,extension', CASES)
def test_file_write_failure_is_not_reported_as_success(helper, arguments, extension, archive, tmp_path):
    blocker = tmp_path / 'not-a-directory'
    blocker.write_text('existing')
    payload = response(content=archive) if extension == '.zip' else response({'ok': True})
    with patch.object(api_request.requests, 'request', return_value=payload) as request:
        with pytest.raises(OSError):
            helper(EXPRESSION, output_file=blocker / ('result' + extension), **arguments)
    request.assert_called_once()
    assert blocker.read_text() == 'existing'


def test_threshold_no_matches_is_a_successful_empty_collection(tmp_path):
    payload = {
        'type': 'FeatureCollection', 'features': [],
        'model': 'wm-6', 'initialization_time': INITIALIZATION,
        'forecast_zero': '2026-10-16T12:00:00Z', 'forecast_hours': [0],
        'calculation': EXPRESSION, 'grid_calculations': [EXPRESSION],
        'forecast_hour_errors': [],
    }
    output = tmp_path / 'no-matches.geojson'
    with patch.object(api_request.requests, 'request', return_value=response(payload)):
        result = windborne.calculate_threshold(EXPRESSION, BOUNDS, THRESHOLD, output_file=output)
    assert result == json.loads(output.read_text()) == payload
