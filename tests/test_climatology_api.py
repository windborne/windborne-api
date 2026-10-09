import copy
import csv
import io
import json
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from windborne import climatology_api


class ClimatologyApiTest(TestCase):
    @patch.object(climatology_api, 'make_api_request')
    def test_single_hour_defaults_and_raw_response(self, request):
        response = {'normal': '1991-2020', 'time': '2026-07-15T00:00:00Z',
                    'rolling_average_days': 0, 'climatologies': [[], []]}
        request.return_value = response
        result = climatology_api.get_climatology('32.9, -97.04; 0, 0', time='2026-07-15')
        request.assert_called_once_with(
            climatology_api.API_BASE_URL + '/forecasts/v1/climatology',
            params={'coordinates': '32.9,-97.04;0,0', 'time': '2026-07-15T00:00:00Z'},
        )
        self.assertIs(response, result)

    @patch.object(climatology_api, 'make_api_request', return_value={})
    def test_range_and_optional_values_preserve_zero_false_and_coordinate_order(self, request):
        climatology_api.get_climatology(
            [(32.9, -97.04), {'lat': 0, 'lon': 0}],
            start_time='2026071500', end_time='2026-07-15T04:00:00-04:00',
            normal='2016-2025', rolling_average_days=0,
            elevation_correction=False, water_strategy='allow',
        )
        self.assertEqual({
            'coordinates': '32.9,-97.04;0,0',
            'start_time': '2026-07-15T00:00:00Z', 'end_time': '2026-07-15T08:00:00Z',
            'normal': '2016-2025', 'rolling_average_days': 0,
            'elevation_correction': 'false', 'water_strategy': 'allow',
        }, request.call_args.kwargs['params'])

    @patch.object(climatology_api, 'make_api_request', return_value={})
    def test_non_hour_aligned_time_is_not_silently_truncated(self, request):
        climatology_api.get_climatology('0,0', time='2026-07-15T01:30:05.123Z')
        self.assertEqual('2026-07-15T01:30:05.123000Z',
                         request.call_args.kwargs['params']['time'])

    @patch.object(climatology_api, 'make_api_request')
    def test_invalid_time_choice_or_empty_coordinates_make_no_request(self, request):
        cases = [
            {'coordinates': '0,0'},
            {'coordinates': '0,0', 'start_time': '2026-07-15'},
            {'coordinates': '0,0', 'end_time': '2026-07-15'},
            {'coordinates': '0,0', 'time': '2026-07-15', 'start_time': '2026-07-15'},
            {'coordinates': '0,0', 'time': '2026-07-15', 'end_time': '2026-07-15'},
            {'coordinates': [], 'time': '2026-07-15'},
            {'coordinates': [(0, 0), 42], 'time': '2026-07-15'},
        ]
        for arguments in cases:
            with self.subTest(arguments=arguments), self.assertRaises(ValueError):
                climatology_api.get_climatology(**arguments)
        request.assert_not_called()

    @patch.object(climatology_api, 'make_api_request')
    def test_exports_keep_all_locations_and_leave_response_unchanged(self, request):
        response = {
            'normal': '2016-2025', 'start_time': '2026-07-15T00:00:00Z',
            'end_time': '2026-07-15T01:00:00Z', 'rolling_average_days': 0,
            'climatologies': [[], [
                {'time': '2026-07-15T00:00:00Z', 'latitude': 1, 'longitude': 2,
                 'temperature_2m': 20, 'pressure_msl': None},
                {'time': '2026-07-15T01:00:00Z', 'latitude': 1, 'longitude': 2,
                 'temperature_2m': 21, 'pressure_msl': None},
            ], [{'time': '2026-07-15T00:00:00Z', 'latitude': 3, 'longitude': 4,
                 'temperature_2m': 22, 'pressure_msl': None}]],
        }
        original = copy.deepcopy(response)
        request.return_value = response
        args = {'coordinates': '0,0;1,2;3,4', 'start_time': '2026-07-15',
                'end_time': '2026-07-15T01'}
        with TemporaryDirectory() as directory, redirect_stdout(io.StringIO()):
            json_path = Path(directory) / 'nested' / 'climatology.json'
            csv_path = Path(directory) / 'climatology.csv'
            self.assertIs(response, climatology_api.get_climatology(**args, output_file=json_path))
            self.assertEqual(response, json.loads(json_path.read_text()))
            climatology_api.get_climatology(**args, output_file=csv_path)
            with csv_path.open() as file:
                rows = list(csv.DictReader(file))
            self.assertEqual(['1', '1', '3'], [row['latitude'] for row in rows])
            self.assertEqual(['20', '21', '22'], [row['temperature_2m'] for row in rows])
        self.assertEqual(original, response)

    @patch.object(climatology_api, 'make_api_request')
    def test_printing_and_failed_requests(self, request):
        response = {'normal': '1991-2020', 'climatologies': [[], []]}
        request.return_value = response
        output = io.StringIO()
        with redirect_stdout(output):
            climatology_api.get_climatology('0,0;1,2', time='2026-07-15', print_response=True)
        self.assertEqual(response, json.loads(output.getvalue()))
        request.return_value = None
        with TemporaryDirectory() as directory, redirect_stdout(io.StringIO()) as output:
            path = Path(directory) / 'error.json'
            result = climatology_api.get_climatology(
                '0,0', time='2026-07-15', output_file=path, print_response=True,
            )
            self.assertIsNone(result)
            self.assertFalse(path.exists())
            self.assertEqual('', output.getvalue())

    @patch.object(climatology_api, 'make_api_request')
    def test_unsupported_output_rejected_before_request(self, request):
        with self.assertRaises(ValueError):
            climatology_api.get_climatology('0,0', time='2026-07-15', output_file='data.nc')
        request.assert_not_called()
