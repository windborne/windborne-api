"""Keep legacy TC routes and unmatched tracker exports working without live calls."""
import copy
import csv
import json
from unittest.mock import patch
import xml.etree.ElementTree as ET

import pytest

from windborne import forecasts_api as api


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
@pytest.mark.parametrize('output', [True, False])
def test_geojson_uses_legacy_extension_route_or_new_tracker_format(model, output, tmp_path):
    native_geojson = {
        'type': 'FeatureCollection',
        'features': [{'type': 'Feature', 'properties': {'id': 'storm'},
                      'geometry': {'type': 'LineString', 'coordinates': [[-60, 20], [-61, 21]]}}],
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

    output_path = tmp_path / 'cyclones.geojson'
    with patch.object(api, 'make_api_request', side_effect=gateway_response):
        result = api.get_tropical_cyclones(model=model, **(
            {'output_file': str(output_path)} if output else {'format': 'geojson'}))
    assert result == native_geojson
    if output:
        assert json.loads(output_path.read_text()) == native_geojson


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
@pytest.mark.parametrize('extension', ['csv', 'gpx', 'kml'])
def test_detail_export_retains_unmatched_track_and_matched_mean(matched, extension, tmp_path):
    response = cyclone_detail(matched)
    original = copy.deepcopy(response)
    expected_points = response['mean_path'] if matched else response['members_path'][0]['path']
    cyclone_id = response['tropical_cyclone_id']
    output_path = tmp_path / f'cyclone.{extension}'
    with patch.object(api, 'make_api_request', return_value=response) as request:
        result = api.get_tropical_cyclone(cyclone_id, output_file=str(output_path))
    assert request.call_args.kwargs['params']['include_members'] == 'true'
    assert result is response
    assert response == original

    if extension == 'csv':
        with output_path.open() as file:
            rows = list(csv.DictReader(file))
        assert [row['id'] for row in rows] == [cyclone_id, cyclone_id]
        assert [float(row['latitude']) for row in rows] == [point['latitude'] for point in expected_points]
        assert [row['time'] for row in rows] == [point['valid_at'] for point in expected_points]
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


@pytest.mark.parametrize('extension', ['csv', 'gpx', 'kml'])
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
