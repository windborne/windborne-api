"""Track exports for flights that cross the date line, without live calls."""
import json
import xml.etree.ElementTree as ET

import pytest

from windborne.track_formatting import save_track

GPX = '{http://www.topografix.com/GPX/1/1}'

EAST_TO_WEST = [
    {'latitude': 10.0, 'longitude': 179.0, 'transmit_time': '2026-11-01T00:00:00Z'},
    {'latitude': 12.0, 'longitude': -179.0, 'transmit_time': '2026-11-01T01:00:00Z'},
    {'latitude': 13.0, 'longitude': -178.0, 'transmit_time': '2026-11-01T02:00:00Z'},
]
WEST_TO_EAST = list(reversed(EAST_TO_WEST))


@pytest.mark.parametrize('track', [EAST_TO_WEST, WEST_TO_EAST])
def test_gpx_uses_time_key_when_track_crosses_date_line(track, tmp_path):
    output_path = tmp_path / 'flight.gpx'
    save_track(str(output_path), {'W-1234': track}, time_key='transmit_time')

    segments = ET.parse(output_path).getroot().findall(f'{GPX}trk/{GPX}trkseg')
    assert len(segments) == 2
    times = [time.text for segment in segments for time in segment.iter(f'{GPX}time')]
    assert times == [point['transmit_time'] for point in track]


@pytest.mark.parametrize('track,seams', [
    (EAST_TO_WEST, (180, -180)),
    (WEST_TO_EAST, (-180, 180)),
])
def test_geojson_splits_at_interpolated_crossing_latitude(track, seams, tmp_path):
    output_path = tmp_path / 'flight.geojson'
    save_track(str(output_path), {'W-1234': track}, time_key='transmit_time')

    geometry = json.loads(output_path.read_text())['features'][0]['geometry']
    first, second = geometry['coordinates']
    # 179 -> -179 is two degrees of longitude, so the crossing is halfway from 10 to 12
    assert first[-1] == pytest.approx([seams[0], 11.0])
    assert second[0] == pytest.approx([seams[1], 11.0])
    assert len(first) + len(second) == len(track) + 2


def test_geojson_with_empty_track_is_written(tmp_path):
    output_path = tmp_path / 'prediction.geojson'
    save_track(str(output_path), {'W-1234': []})

    feature = json.loads(output_path.read_text())['features'][0]
    assert feature['properties'] == {'id': 'W-1234', 'start_time': None, 'end_time': None}
    assert feature['geometry'] == {'type': 'MultiLineString', 'coordinates': []}
