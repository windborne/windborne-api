import copy
import csv
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from windborne.utils import parse_time, save_arbitrary_response


class ForecastCSVTests(unittest.TestCase):
    def export(self, response):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'forecast.csv'
            with redirect_stdout(io.StringIO()):
                save_arbitrary_response(str(path), response, csv_data_key='forecasts')
            if not path.exists():
                return []
            with path.open(newline='') as stream:
                return list(csv.DictReader(stream))

    def test_every_location_and_time_is_exported_without_mutating_response(self):
        response = {'forecasts': [
            [{'time': '00:00', 'latitude': 40.7, 'temperature': 10},
             {'time': '01:00', 'latitude': 40.7, 'temperature': 11}],
            [{'time': '00:00', 'latitude': 34.0, 'temperature': 20},
             {'time': '01:00', 'latitude': 34.0, 'temperature': 21}],
        ]}
        original = copy.deepcopy(response)
        rows = self.export(response)
        self.assertEqual([row['temperature'] for row in rows], ['10', '11', '20', '21'])
        self.assertEqual([row['location_index'] for row in rows], ['0', '0', '1', '1'])
        self.assertEqual(response, original)

    def test_empty_first_location_does_not_hide_other_locations(self):
        rows = self.export({'forecasts': [[], [{'temperature': 12}]]})
        self.assertEqual(rows, [{'temperature': '12', 'location_index': '1'}])

    def test_geo_filtered_location_keeps_original_request_index(self):
        rows = self.export({'filtered_coordinates': [0], 'forecasts': [[{'temperature': 20}]]})
        self.assertEqual(rows[0]['location_index'], '1')

    def test_columns_include_fields_present_only_in_later_rows(self):
        rows = self.export({'forecasts': [[{'temperature': 10}], [{'temperature': None, 'precipitation': 0}]]})
        self.assertEqual(rows[0]['precipitation'], '')
        self.assertEqual(rows[1]['precipitation'], '0')
        self.assertEqual(rows[1]['temperature'], 'None')

    def test_single_location_keeps_existing_columns(self):
        self.assertEqual(self.export({'forecasts': [[{'temperature': 10}]]}), [{'temperature': '10'}])

    def test_empty_forecasts_do_not_write_a_misleading_file(self):
        self.assertEqual(self.export({'forecasts': [[], []]}), [])

    def test_json_preserves_full_response(self):
        response = {'forecasts': [[{'temperature': 10}], [{'temperature': 20}]], 'initialization_time': '2026-10-08T07:15:00Z'}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'forecast.json'
            with redirect_stdout(io.StringIO()):
                save_arbitrary_response(str(path), response, csv_data_key='forecasts')
            self.assertEqual(json.loads(path.read_text()), response)


class ForecastTimeTests(unittest.TestCase):
    def test_compact_initialization_accepts_continuous_model_hours(self):
        self.assertEqual(parse_time('2026100807', init_time_flag=True), '2026-10-08T07:00:00')

    def test_iso_initialization_preserves_minutes_seconds_and_fraction(self):
        self.assertEqual(parse_time('2026-10-08T07:15:12.123Z', init_time_flag=True), '2026-10-08T07:15:12.123000Z')

    def test_timezone_is_normalized_without_truncation(self):
        self.assertEqual(parse_time('2026-10-08T07:15:12-07:00'), '2026-10-08T14:15:12Z')

    def test_naive_fractional_timestamp_uses_backend_supported_utc_format(self):
        self.assertEqual(parse_time('2026-10-08T07:15:12.123'), '2026-10-08T07:15:12.123000Z')

    def test_existing_hourly_formats_remain_supported(self):
        self.assertEqual(parse_time('2026100806', init_time_flag=True), '2026-10-08T06:00:00')
        self.assertEqual(parse_time('2026-10-08T06:00:00Z'), '2026-10-08T06:00:00Z')

    def test_past_validation_accepts_timezone_aware_input(self):
        self.assertEqual(parse_time('2000-01-01T00:00:00Z', require_past=True), '2000-01-01T00:00:00Z')

    def test_invalid_time_still_fails_before_an_api_request(self):
        with redirect_stdout(io.StringIO()), self.assertRaises(SystemExit):
            parse_time('not-a-date')


if __name__ == '__main__':
    unittest.main()
