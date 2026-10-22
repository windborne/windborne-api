"""Keep legacy TC routes and unmatched tracker exports working without live calls."""
import copy
import csv
import json
import warnings
from unittest.mock import patch
import xml.etree.ElementTree as ET

import pytest

from windborne import cli, forecasts_api as api


@pytest.mark.parametrize('interface', ['sdk', 'cli'])
@pytest.mark.parametrize('include_details', [False, True])
def test_default_model_uses_current_tracker_and_preserves_response(interface, include_details, tmp_path):
    response = {
        'forecast_zero': 0,
        'initialization_time': '2026-10-22T00:00:00Z',
        'total': 1,
        'tropical_cyclones': {'AL012026': {'storm_name': 'Fixture'}},
    }
    output_path = tmp_path / 'cyclones.json'
    with patch.object(api, 'make_api_request', return_value=response) as request:
        if interface == 'sdk':
            result = api.get_tropical_cyclones(
                basin='NA', include_details=include_details, output_file=str(output_path),
            )
            assert result is response
        else:
            arguments = ['windborne', 'tropical_cyclones', '--basin', 'NA']
            if include_details:
                arguments += ['--include-details', 'true']
            with patch('sys.argv', arguments + [str(output_path)]):
                cli.main()
    request.assert_called_once_with(
        'https://api.windbornesystems.com/forecasts/v1/wm-6/tropical_cyclones',
        params={'basin': 'AL', 'include_details': str(include_details).lower(),
                'include_unofficial_ids': 'false', 'format': 'json'},
    )
    assert json.loads(output_path.read_text()) == response


@pytest.mark.parametrize('model,basin,expected', [
    ('wm-6', 'NA', 'AL'), ('wm-6', 'AL', 'AL'), ('wm-6', 'CP', 'CP'),
    ('gfs', 'NA', 'NA'), ('gfs', 'AL', 'NA'), ('ecmwf-det', 'NA', 'NA'),
    ('wm', 'NA', 'NA'), ('wm6', 'NA', 'NA'),
])
def test_basin_matches_the_gateway_route(model, basin, expected):
    with patch.object(api, 'make_api_request', return_value={}) as request:
        api.get_tropical_cyclones(model=model, basin=basin)
    assert request.call_args.kwargs['params']['basin'] == expected


def test_legacy_route_rejects_unsupported_central_pacific_before_request():
    with patch.object(api, 'make_api_request') as request, pytest.raises(ValueError, match='basin'):
        api.get_tropical_cyclones(model='gfs', basin='CP')
    request.assert_not_called()


@pytest.mark.parametrize('model', ['gfs', 'ecmwf-det', 'wm', 'wm6', 'wm-6'])
@pytest.mark.parametrize('extension', [None, 'json', 'geojson'])
def test_explicit_geojson_uses_legacy_extension_route_or_new_tracker_format(model, extension, tmp_path):
    native_geojson = {
        'type': 'FeatureCollection',
        'features': [{'type': 'Feature', 'properties': {'id': 'storm'},
                      'geometry': {'type': 'LineString', 'coordinates': [[-60, 20], [-61, 21]]}}],
        'initialization_time': '2026-10-12T00:00:00Z',
    }

    def gateway_response(url, params):
        if model == 'wm-6' and params['format'] == 'geojson':
            assert url.endswith('/wm-6/tropical_cyclones')
            return native_geojson
        # The legacy extensionless route proxies to /tcs/{model}.json, whose
        # path format overrides a format=geojson query parameter in Rails.
        if url.endswith('.geojson'):
            return native_geojson
        return {'storm': [{'latitude': 20, 'longitude': -60}]}

    output_path = tmp_path / f'cyclones.{extension}' if extension else None
    with patch.object(api, 'make_api_request', side_effect=gateway_response) as request:
        result = api.get_tropical_cyclones(model=model, format='geojson',
                                          output_file=str(output_path) if output_path else None)
    request.assert_called_once()
    assert request.call_args.kwargs['params']['include_details'] == ('true' if extension == 'geojson' else 'false')
    assert result is native_geojson
    if output_path:
        assert json.loads(output_path.read_text()) == native_geojson


@pytest.mark.parametrize('model', ['gfs', 'ecmwf-det', 'wm', 'wm6', 'wm-6'])
@pytest.mark.parametrize('format_options', [{}, {'format': 'json'}], ids=['default', 'explicit-json'])
def test_geojson_filename_preserves_json_return_and_exports_tracks(model, format_options, tmp_path):
    track = [
        {'time': '2026-10-12T00:00:00Z', 'latitude': 20, 'longitude': -60},
        {'time': '2026-10-12T06:00:00Z', 'latitude': 21, 'longitude': -61},
    ]
    response = {'AL012026': track}
    if model == 'wm-6':
        response = {
            'initialization_time': '2026-10-12T00:00:00Z',
            'tropical_cyclones': {'AL012026': {'path': [
                {'valid_at': point['time'], 'latitude': point['latitude'], 'longitude': point['longitude']}
                for point in track
            ], 'storm_name': 'Fixture'}},
            'total': 1,
        }
    original = copy.deepcopy(response)
    output_path = tmp_path / 'cyclones.GEOJSON'
    with patch.object(api, 'make_api_request', return_value=response) as request:
        result = api.get_tropical_cyclones(model=model, output_file=str(output_path), **format_options)
    request.assert_called_once()
    assert request.call_args.args[0].endswith(f'/{model}/tropical_cyclones')
    assert request.call_args.kwargs['params']['format'] == 'json'
    assert request.call_args.kwargs['params']['include_details'] == 'true'
    assert result is response
    assert response == original
    if model != 'wm-6':
        # Existing callers can continue indexing the returned storm map after export.
        assert result['AL012026'] is track
    saved = json.loads(output_path.read_text())
    assert saved == {
        'type': 'FeatureCollection',
        'features': [{
            'type': 'Feature',
            'properties': {'id': 'AL012026', 'start_time': track[0]['time'], 'end_time': track[-1]['time']},
            'geometry': {'type': 'MultiLineString', 'coordinates': [[[-60, 20], [-61, 21]]]},
        }],
    }


@pytest.mark.parametrize('model,response', [
    ('gfs', {}), ('wm-6', {'tropical_cyclones': {}, 'total': 0}),
])
def test_empty_json_list_exports_empty_geojson_without_changing_return(model, response, tmp_path):
    output_path = tmp_path / 'empty.geojson'
    with patch.object(api, 'make_api_request', return_value=response):
        assert api.get_tropical_cyclones(model=model, output_file=str(output_path)) is response
    assert json.loads(output_path.read_text()) == {'type': 'FeatureCollection', 'features': []}


def cyclone_list_with_empty_paths():
    return {
        'initialization_time': '2026-10-22T21:00:00Z',
        'total': 4,
        'tropical_cyclones': {
            'WP292026': {'storm_name': 'No forecast track', 'path': []},
            'EP222026': {'path': [
                {'valid_at': '2026-10-22T21:00:00Z', 'latitude': 20, 'longitude': -60},
                {'valid_at': '2026-10-23T03:00:00Z', 'latitude': 21, 'longitude': -61},
            ]},
            'SH022027': {'path': [
                {'valid_at': '2026-10-22T21:00:00Z', 'latitude': -15, 'longitude': 150},
                {'valid_at': '2026-10-23T03:00:00Z', 'latitude': -16, 'longitude': 151},
            ]},
            'AL012026': {'storm_name': 'Also empty', 'path': []},
        },
    }


@pytest.mark.parametrize('extension', ['csv', 'geojson', 'gpx', 'kml', 'little_r'])
def test_list_export_warns_for_empty_paths_and_preserves_every_available_point(extension, tmp_path):
    response = cyclone_list_with_empty_paths()
    original = copy.deepcopy(response)
    output_path = tmp_path / f'cyclones.{extension}'
    with patch.object(api, 'make_api_request', return_value=response) as request:
        with pytest.warns(UserWarning, match='empty paths.*WP292026, AL012026') as warning:
            result = api.get_tropical_cyclones(output_file=str(output_path))
    assert len(warning) == 1
    request.assert_called_once()
    assert request.call_args.kwargs['params']['include_details'] == 'true'
    assert result is response
    assert response == original
    expected = [
        (cyclone_id, point['latitude'], point['longitude'])
        for cyclone_id, cyclone in response['tropical_cyclones'].items()
        for point in cyclone['path']
    ]
    if extension == 'csv':
        with output_path.open() as file:
            points = [(row['id'], float(row['latitude']), float(row['longitude']))
                      for row in csv.DictReader(file)]
    elif extension == 'geojson':
        saved = json.loads(output_path.read_text())
        points = [(feature['properties']['id'], latitude, longitude)
                  for feature in saved['features']
                  for segment in feature['geometry']['coordinates']
                  for longitude, latitude in segment]
    elif extension == 'gpx':
        root = ET.fromstring(output_path.read_text())
        points = [(track.find('{*}name').text, float(point.attrib['lat']), float(point.attrib['lon']))
                  for track in root.findall('{*}trk') for point in track.findall('.//{*}trkpt')]
    elif extension == 'kml':
        root = ET.fromstring(output_path.read_text())
        points = [(track.find('{*}name').text, float(point.split(',')[1]), float(point.split(',')[0]))
                  for track in root.findall('.//{*}Placemark')
                  for coordinates in track.findall('.//{*}coordinates')
                  for point in coordinates.text.split()]
    else:
        # Each little_r position record has four lines and fixed-width headers.
        lines = output_path.read_text().splitlines()
        assert len(lines) == 4 * len(expected)
        points = [(header[180:220].strip(), float(header[:20]), float(header[20:40]))
                  for header in lines[::4]]
    assert points == expected


@pytest.mark.parametrize('extension', ['csv', 'geojson', 'gpx', 'kml', 'little_r'])
def test_all_empty_list_paths_raise_without_overwriting_output(extension, tmp_path):
    response = cyclone_list_with_empty_paths()
    for cyclone in response['tropical_cyclones'].values():
        cyclone['path'] = []
    output_path = tmp_path / f'cyclones.{extension}'
    output_path.write_text('existing export')
    with patch.object(api, 'make_api_request', return_value=response):
        with pytest.raises(ValueError, match='all returned cyclones have empty paths'):
            api.get_tropical_cyclones(output_file=str(output_path))
    assert output_path.read_text() == 'existing export'


@pytest.mark.parametrize('missing_path', [{}, {'path': None}])
def test_list_missing_path_is_not_treated_as_an_empty_track(missing_path, tmp_path):
    response = cyclone_list_with_empty_paths()
    response['tropical_cyclones']['WP292026'] = missing_path
    output_path = tmp_path / 'cyclones.csv'
    output_path.write_text('existing export')
    with patch.object(api, 'make_api_request', return_value=response):
        with pytest.raises(ValueError, match='No track points available for WP292026'):
            api.get_tropical_cyclones(output_file=str(output_path))
    assert output_path.read_text() == 'existing export'


@pytest.mark.parametrize('all_empty', [False, True])
def test_json_list_retains_empty_paths_without_warning_or_mutation(all_empty, tmp_path):
    response = cyclone_list_with_empty_paths()
    if all_empty:
        for cyclone in response['tropical_cyclones'].values():
            cyclone['path'] = []
    original = copy.deepcopy(response)
    output_path = tmp_path / 'cyclones.json'
    with patch.object(api, 'make_api_request', return_value=response):
        with warnings.catch_warnings(record=True) as caught:
            result = api.get_tropical_cyclones(output_file=str(output_path))
    assert not caught
    assert result is response
    assert response == original
    assert json.loads(output_path.read_text()) == original


def cyclone_detail(matched=False):
    points = [
        {'valid_at': '2026-10-12T00:00:00Z', 'latitude': 20, 'longitude': -60},
        {'valid_at': '2026-10-12T06:00:00Z', 'latitude': 21, 'longitude': -61},
    ]
    return {
        'tropical_cyclone_id': 'AL012026' if matched else 'unmatched-member-0',
        'mean_path': points if matched else [],
        'members_path': [{'member': 0, 'path': [dict(point, latitude=point['latitude'] + 1) for point in points]}],
    }


@pytest.mark.parametrize('matched', [False, True])
@pytest.mark.parametrize('extension', ['csv', 'gpx', 'kml', 'geojson'])
def test_detail_export_retains_unmatched_track_and_matched_mean(matched, extension, tmp_path):
    response = cyclone_detail(matched)
    original = copy.deepcopy(response)
    expected_points = response['mean_path'] if matched else response['members_path'][0]['path']
    cyclone_id = response['tropical_cyclone_id']
    output_path = tmp_path / f'cyclone.{extension}'
    with patch.object(api, 'make_api_request', return_value=response) as request:
        result = api.get_tropical_cyclone(cyclone_id, output_file=str(output_path))
    assert request.call_args.kwargs['params']['include_members'] == 'true'
    assert request.call_args.kwargs['params']['format'] == 'json'
    request.assert_called_once()
    assert result is response
    assert response == original

    if extension == 'csv':
        with output_path.open() as file:
            rows = list(csv.DictReader(file))
        assert [row['id'] for row in rows] == [cyclone_id, cyclone_id]
        assert [float(row['latitude']) for row in rows] == [point['latitude'] for point in expected_points]
        assert [row['time'] for row in rows] == [point['valid_at'] for point in expected_points]
    elif extension == 'geojson':
        saved = json.loads(output_path.read_text())
        assert saved['type'] == 'FeatureCollection'
        assert len(saved['features']) == 1
        feature = saved['features'][0]
        assert feature['properties'] == {
            'id': cyclone_id,
            'start_time': expected_points[0]['valid_at'],
            'end_time': expected_points[-1]['valid_at'],
        }
        assert feature['geometry'] == {
            'type': 'MultiLineString',
            'coordinates': [[[point['longitude'], point['latitude']] for point in expected_points]],
        }
    else:
        root = ET.fromstring(output_path.read_text())
        assert root.find('.//{*}name').text == cyclone_id
        if extension == 'gpx':
            points = root.findall('.//{*}trkpt')
            assert [float(point.attrib['lat']) for point in points] == [point['latitude'] for point in expected_points]
            assert [point.find('{*}time').text for point in points] == [point['valid_at'] for point in expected_points]
        else:
            coordinates = root.find('.//{*}coordinates').text.split()
            assert [float(point.split(',')[1]) for point in coordinates] == [point['latitude'] for point in expected_points]


def test_fallback_does_not_merge_multiple_member_paths(tmp_path):
    response = cyclone_detail()
    response['members_path'].append({'member': 7, 'path': [
        {'valid_at': '2026-10-12T00:00:00Z', 'latitude': 30, 'longitude': -70},
    ]})
    output_path = tmp_path / 'members.csv'
    with patch.object(api, 'make_api_request', return_value=response):
        api.get_tropical_cyclone(response['tropical_cyclone_id'], output_file=str(output_path))
    with output_path.open() as file:
        rows = list(csv.DictReader(file))
    assert [row['id'] for row in rows] == [
        'unmatched-member-0/member/0', 'unmatched-member-0/member/0', 'unmatched-member-0/member/7',
    ]


@pytest.mark.parametrize('extension', ['csv', 'gpx', 'kml', 'geojson'])
def test_unavailable_track_raises_without_overwriting_output(extension, tmp_path):
    response = cyclone_detail()
    del response['members_path']
    output_path = tmp_path / f'cyclone.{extension}'
    output_path.write_text('existing export')
    with patch.object(api, 'make_api_request', return_value=response), pytest.raises(ValueError, match='No track points'):
        api.get_tropical_cyclone(response['tropical_cyclone_id'], output_file=str(output_path))
    assert output_path.read_text() == 'existing export'


def test_json_detail_does_not_implicitly_request_or_transform_members(tmp_path):
    response = cyclone_detail()
    del response['members_path']
    output_path = tmp_path / 'cyclone.json'
    with patch.object(api, 'make_api_request', return_value=response) as request:
        result = api.get_tropical_cyclone(response['tropical_cyclone_id'], output_file=str(output_path))
    assert request.call_args.kwargs['params']['include_members'] == 'false'
    assert result is response
    assert json.loads(output_path.read_text()) == response


@pytest.mark.parametrize('extension', ['json', 'geojson'])
def test_explicit_native_detail_preserves_features_and_metadata(extension, tmp_path):
    response = {
        'type': 'FeatureCollection',
        'features': [
            {'type': 'Feature', 'properties': {'kind': 'mean_path'},
             'geometry': {'type': 'LineString', 'coordinates': [[-60, 20], [-61, 21]]}},
            {'type': 'Feature', 'properties': {'kind': 'forecast_point', 'valid_at': '2026-10-12T00:00:00Z'},
             'geometry': {'type': 'Point', 'coordinates': [-60, 20]}},
            {'type': 'Feature', 'properties': {'kind': 'cone'},
             'geometry': {'type': 'Polygon', 'coordinates': [[[-60, 20], [-61, 21], [-60, 22], [-60, 20]]]}},
        ],
        'initialization_time': '2026-10-12T00:00:00Z',
    }
    original = copy.deepcopy(response)
    output_path = tmp_path / f'native.{extension}'
    with patch.object(api, 'make_api_request', return_value=response) as request:
        result = api.get_tropical_cyclone('AL012026', format='geojson', include_cones=True,
                                          output_file=str(output_path))
    request.assert_called_once()
    assert request.call_args.kwargs['params']['format'] == 'geojson'
    assert request.call_args.kwargs['params']['include_cones'] == 'true'
    assert request.call_args.kwargs['params']['include_members'] == 'false'
    assert result is response
    assert response == original
    assert json.loads(output_path.read_text()) == response
