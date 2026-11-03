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
            climatology_api.API_BASE_URL + '/weather/v1/climatology/point',
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
            'min_time': '2026-07-15T00:00:00Z', 'max_time': '2026-07-15T08:00:00Z',
            'normal': '2016-2025', 'rolling_average_days': 0,
            'elevation_correction': 'false', 'water_strategy': 'allow',
        }, request.call_args.kwargs['params'])

    @patch.object(climatology_api, 'make_api_request', return_value={})
    def test_non_hour_aligned_time_is_not_silently_truncated(self, request):
        climatology_api.get_climatology('0,0', time='2026-07-15T01:30:05.123Z')
        self.assertEqual('2026-07-15T01:30:05.123000Z',
                         request.call_args.kwargs['params']['time'])

    @patch.object(climatology_api, 'make_api_request')
    def test_new_and_legacy_bound_names_make_identical_requests(self, request):
        response = {'start_time': '2026-07-15T00:00:00Z',
                    'end_time': '2026-07-15T01:00:00Z', 'climatologies': [[]]}
        request.return_value = response
        for lower in ('min_time', 'start_time'):
            for upper in ('max_time', 'end_time'):
                with self.subTest(lower=lower, upper=upper):
                    result = climatology_api.get_climatology(
                        '0,0', **{lower: '2026071500', upper: '2026-07-15T01:00:00Z'},
                    )
                    self.assertIs(response, result)
                    self.assertEqual({
                        'coordinates': '0,0', 'min_time': '2026-07-15T00:00:00Z',
                        'max_time': '2026-07-15T01:00:00Z',
                    }, request.call_args.kwargs['params'])

    @patch.object(climatology_api, 'make_api_request')
    def test_duplicate_bound_names_fail_before_request(self, request):
        for canonical, legacy in (('min_time', 'start_time'), ('max_time', 'end_time')):
            with self.subTest(bound=canonical), self.assertRaisesRegex(ValueError, 'not both'):
                climatology_api.get_climatology(
                    '0,0', **{canonical: '2026-07-15', legacy: '2026-07-16'},
                )
        request.assert_not_called()

    @patch.object(climatology_api, 'make_api_request')
    def test_invalid_time_choice_or_empty_coordinates_make_no_request(self, request):
        cases = [
            {'coordinates': '0,0'},
            {'coordinates': '0,0', 'min_time': '2026-07-15'},
            {'coordinates': '0,0', 'max_time': '2026-07-15'},
            {'coordinates': '0,0', 'time': '2026-07-15', 'min_time': '2026-07-15'},
            {'coordinates': '0,0', 'time': '2026-07-15', 'max_time': '2026-07-15'},
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


class ClimatologySummaryApiTest(TestCase):
    @patch.object(climatology_api, 'make_api_request')
    def test_single_calendar_date_defaults_and_raw_response(self, request):
        response = {'normal': '1991-2020', 'group_by': 'day', 'start_date': '2027-09-28',
                    'end_date': '2027-09-28', 'climatology_summaries': [[], []]}
        request.return_value = response
        result = climatology_api.get_climatology_summary('32.9, -97.04; 0, 0', date='2027-09-28')
        request.assert_called_once_with(
            climatology_api.API_BASE_URL + '/weather/v1/climatology/summary',
            params={'coordinates': '32.9,-97.04;0,0', 'date': '2027-09-28'},
        )
        self.assertIs(response, result)

    @patch.object(climatology_api, 'make_api_request', return_value={})
    def test_inclusive_range_groupings_and_explicit_options(self, request):
        for grouping in ('day', 'week', 'month', 'period'):
            with self.subTest(grouping=grouping):
                climatology_api.get_climatology_summary(
                    [(32.9, -97.04), {'lat': 0, 'lon': 0}],
                    start_date='2028-01-01', end_date='2028-12-31', group_by=grouping,
                    normal='2016-2025', elevation_correction=False, water_strategy='allow',
                )
                self.assertEqual({
                    'coordinates': '32.9,-97.04;0,0', 'start_date': '2028-01-01',
                    'end_date': '2028-12-31', 'group_by': grouping, 'normal': '2016-2025',
                    'elevation_correction': 'false', 'water_strategy': 'allow',
                }, request.call_args.kwargs['params'])

    @patch.object(climatology_api, 'make_api_request')
    def test_invalid_dates_combinations_or_coordinates_make_no_request(self, request):
        cases = [
            {}, {'start_date': '2027-09-28'}, {'end_date': '2027-09-28'},
            {'date': '2027-09-28', 'start_date': '2027-09-28'},
            {'date': '2027-09-28', 'end_date': '2027-09-28'},
            {'date': '2027-09-28', 'group_by': 'period'},
            {'date': '2027-09-28', 'group_by': 'year'},
            {'date': '2027-09-28T00:00:00Z'}, {'date': '2027-9-28'},
            {'date': '2027-02-29'}, {'date': 20270928},
            {'start_date': '2028-01-01', 'end_date': '2029-01-01'},
            {'start_date': '2027-09-29', 'end_date': '2027-09-28'},
            {'coordinates': [], 'date': '2027-09-28'},
            {'coordinates': [(0, 0), 42], 'date': '2027-09-28'},
            {'date': '2027-09-28', 'output_file': 'data.nc'},
        ]
        for arguments in cases:
            with self.subTest(arguments=arguments), self.assertRaises(ValueError):
                climatology_api.get_climatology_summary(**dict({'coordinates': '0,0'}, **arguments))
        request.assert_not_called()

    @patch.object(climatology_api, 'make_api_request')
    def test_exports_and_printing_preserve_all_locations_dates_nulls_and_metadata(self, request):
        response = {
            'normal': '2016-2025', 'group_by': 'period', 'start_date': '2027-09-28',
            'end_date': '2027-09-29', 'filtered_coordinates': [1],
            'climatology_summaries': [[{
                'start_date': '2027-09-28', 'end_date': '2027-09-29',
                'latitude': 32.9, 'longitude': -97.04, 'standard_utc_offset_minutes': -360,
                'temperature_2m_min': 20.15, 'temperature_2m_max': 29.42,
                'dewpoint_2m_min': 15.21, 'dewpoint_2m_max': 19.08,
                'precipitation': None, 'avg_daily_precipitation': None,
                'wind_speed_10m_mean': 3.12, 'wind_speed_10m_max': 6.48,
            }], [], [{
                'start_date': '2027-09-28', 'end_date': '2027-09-29',
                'latitude': 27.72, 'longitude': 85.32, 'standard_utc_offset_minutes': 345,
                'temperature_2m_min': None, 'temperature_2m_max': None,
                'precipitation': 3.14, 'avg_daily_precipitation': 1.57,
            }]],
        }
        original = copy.deepcopy(response)
        request.return_value = response
        arguments = {'start_date': '2027-09-28', 'end_date': '2027-09-29', 'group_by': 'period'}
        with TemporaryDirectory() as directory:
            json_path = Path(directory) / 'nested' / 'summary.json'
            with redirect_stdout(io.StringIO()):
                result = climatology_api.get_climatology_summary(
                    '32.9,-97.04;90,0;0,0;27.72,85.32', output_file=json_path, **arguments,
                )
            self.assertIs(response, result)
            self.assertEqual(response, json.loads(json_path.read_text()))
            csv_path = Path(directory) / 'summary.csv'
            with redirect_stdout(io.StringIO()):
                climatology_api.get_climatology_summary('0,0', output_file=csv_path, **arguments)
            with csv_path.open() as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(['32.9', '27.72'], [row['latitude'] for row in rows])
            self.assertEqual(['-360', '345'], [row['standard_utc_offset_minutes'] for row in rows])
            self.assertEqual(['None', '3.14'], [row['precipitation'] for row in rows])
            self.assertEqual(['2027-09-28'] * 2, [row['start_date'] for row in rows])
            with redirect_stdout(io.StringIO()) as output:
                climatology_api.get_climatology_summary('0,0', print_response=True, **arguments)
            self.assertEqual(response, json.loads(output.getvalue()))
        self.assertEqual(original, response)

    @patch.object(climatology_api, 'make_api_request', return_value=None)
    def test_failed_request_does_not_write_or_print(self, request):
        with TemporaryDirectory() as directory, redirect_stdout(io.StringIO()) as output:
            path = Path(directory) / 'error.json'
            result = climatology_api.get_climatology_summary(
                '0,0', date='2027-09-28', output_file=path, print_response=True,
            )
            self.assertIsNone(result)
            self.assertFalse(path.exists())
            self.assertEqual('', output.getvalue())
