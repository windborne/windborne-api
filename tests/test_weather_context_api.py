import copy
import io
import json
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from windborne import weather_context_api


class WeatherContextApiTest(TestCase):
    @patch.object(weather_context_api, 'make_api_request', return_value={})
    def test_locations_and_optional_defaults(self, request):
        for arguments, expected in (
            ({'coordinates': '32.9, -97.04'}, {'coordinates': '32.9,-97.04'}),
            ({'stations': ' kdfw, kjfk '}, {'stations': 'KDFW,KJFK'}),
            ({'stations': ['kdfw']}, {'stations': 'KDFW'}),
            ({'coordinates': [(0, 0)]}, {'coordinates': '0,0'}),
        ):
            with self.subTest(arguments=arguments):
                weather_context_api.get_weather_context(**arguments)
                request.assert_called_with(
                    weather_context_api.API_BASE_URL + '/forecasts/v1/weather_context',
                    params=expected,
                )

    @patch.object(weather_context_api, 'make_api_request', return_value={})
    def test_all_options_preserve_false_zero_and_precision(self, request):
        weather_context_api.get_weather_context(
            coordinates=[(0, 0), {'latitude': 32.9, 'longitude': -97.04}],
            stations=['kdfw', 'kjfk'],
            include_conditions=True, include_observations=False,
            include_distribution=False, include_climatology=True,
            initialization_time='2026071500', min_forecast_hour=0, max_forecast_hour=0,
            min_forecast_time='2026-07-15', max_forecast_time='2026-07-15T03:15:05.123-04:00',
            observation_hours=1, climatology_normal='2016-2025',
        )
        self.assertEqual({
            'coordinates': '0,0;32.9,-97.04', 'stations': 'KDFW;KJFK',
            'include_conditions': 'true', 'include_observations': 'false',
            'include_distribution': 'false', 'include_climatology': 'true',
            'initialization_time': '2026-07-15T00:00:00Z',
            'min_forecast_hour': 0, 'max_forecast_hour': 0,
            'min_forecast_time': '2026-07-15T00:00:00Z',
            'max_forecast_time': '2026-07-15T07:15:05.123000Z',
            'observation_hours': 1, 'climatology_normal': '2016-2025',
        }, request.call_args.kwargs['params'])

    @patch.object(weather_context_api, 'make_api_request')
    def test_full_response_and_json_keep_parallel_empty_locations(self, request):
        response = {
            'initialization_time': '2026-07-15T00:00:00Z',
            'forecast_zero': '2026-07-15T01:00:00Z',
            'forecasts': [[{'time': '2026-07-15T01:00:00Z', 'temperature_2m': 20}], []],
            'conditions': [{'temperature_2m': 19}, None],
            'observations': [[{'time': '2026-07-15T00:00:00Z', 'temperature_2m': 18}], []],
            'climatology_normal': '1991-2020',
            'climatologies': [[{'time': '2026-07-15T01:00:00Z', 'temperature_2m': 17}], []],
            'units': {'temperature_2m': 'C'},
        }
        original = copy.deepcopy(response)
        request.return_value = response
        with TemporaryDirectory() as directory, redirect_stdout(io.StringIO()) as output:
            path = Path(directory) / 'nested' / 'weather.json'
            result = weather_context_api.get_weather_context(
                stations=['KDFW', 'KJFK'], include_conditions=True,
                include_observations=True, include_climatology=True,
                output_file=path, print_response=True,
            )
            self.assertIs(response, result)
            self.assertEqual(response, json.loads(path.read_text()))
            self.assertEqual(response, json.loads(output.getvalue()))
        self.assertEqual(original, response)

    @patch.object(weather_context_api, 'make_api_request')
    def test_empty_locations_or_lossy_output_rejected_before_request(self, request):
        for arguments in ({}, {'coordinates': []}, {'stations': '  '},
                          {'coordinates': '', 'stations': []},
                          {'stations': 'KDFW', 'output_file': 'weather.csv'}):
            with self.subTest(arguments=arguments), self.assertRaises(ValueError):
                weather_context_api.get_weather_context(**arguments)
        request.assert_not_called()

    @patch.object(weather_context_api, 'make_api_request')
    def test_invalid_locations_never_make_a_partial_request(self, request):
        for arguments in (
            {'coordinates': 42, 'stations': 'KDFW'},
            {'coordinates': [(0, 0), 42], 'stations': 'KDFW'},
            {'coordinates': [(0, 0), (1, 2, 3)], 'stations': 'KDFW'},
            {'coordinates': '0,0', 'stations': ['KDFW', 42]},
            {'coordinates': [], 'stations': 'KDFW'},
            {'coordinates': '0,0', 'stations': []},
        ):
            with self.subTest(arguments=arguments), self.assertRaises(ValueError):
                weather_context_api.get_weather_context(**arguments)
        request.assert_not_called()

    @patch.object(weather_context_api, 'make_api_request', return_value=None)
    def test_failed_request_does_not_write_or_print(self, request):
        with TemporaryDirectory() as directory, redirect_stdout(io.StringIO()) as output:
            path = Path(directory) / 'error.json'
            result = weather_context_api.get_weather_context(
                stations='KDFW', output_file=path, print_response=True,
            )
            self.assertIsNone(result)
            self.assertFalse(path.exists())
            self.assertEqual('', output.getvalue())
