"""Contracts from the public weather-event docs, using only local fixtures."""
import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

import requests
from windborne import events_api as api


class EventsApiTests(unittest.TestCase):
    def setUp(self):
        self.patch = patch.object(api, 'make_api_request')
        self.request = self.patch.start()
        self.addCleanup(self.patch.stop)
        self.request.return_value = {'events': {}, 'total': 0}

    def params(self):
        return self.request.call_args.kwargs['params']

    def test_default_routes_do_not_send_unsupported_or_synthetic_params(self):
        cases = [
            (api.get_events, ('atmospheric_river',), '/atmospheric_river', {}),
            (api.get_event_index, ('front',), '/front/index', {}),
            (api.get_event, ('ar_00012026',), '/ar_00012026', {}),
            (api.get_event_init_times, ('ar_00012026',), '/ar_00012026/init_times', {}),
            (api.get_event_context, ('35,-129',), '/event-context', {'coordinates': '35,-129'}),
        ]
        for function, args, path, params in cases:
            with self.subTest(function=function.__name__):
                function(*args)
                self.assertEqual(self.request.call_args.args[0], 'https://api.windbornesystems.com/insights/v1/wm-6' + path)
                self.assertEqual(self.params(), params)

    def test_list_sends_all_documented_filters_with_zero_and_false(self):
        response = {'model': 'wm-6', 'event_type': 'heatwave', 'init_time': '2026-09-14T05:00:00Z', 'events': {}, 'total': 0}
        self.request.return_value = response
        result = api.get_events('heatwave', initialization_time='2026091405', include_details=False, format='json',
                                min_latitude=0, max_latitude=10, min_longitude=0, max_longitude=20)
        self.assertIs(result, response)
        self.assertEqual(self.params(), {
            'initialization_time': '2026-09-14T05:00:00', 'include_details': 'false', 'format': 'json',
            'min_latitude': 0, 'max_latitude': 10, 'min_longitude': 0, 'max_longitude': 20,
        })
        # Exercise requests' actual encoding: the backend rejects "False".
        prepared = requests.Request('GET', self.request.call_args.args[0], params=self.params()).prepare()
        query = parse_qs(urlsplit(prepared.url).query)
        self.assertEqual(query['include_details'], ['false'])
        self.assertEqual(query['min_latitude'], ['0'])
        api.get_events('heatwave', include_details=True)
        self.assertEqual(self.params()['include_details'], 'true')

    def test_index_keeps_one_page_metadata_and_date_line_bounds(self):
        response = {
            'model': 'wm-6', 'events': {'cw_00012026': {'event_id': 'cw_00012026', 'event_type': 'coldwave'}},
            'total': 600, 'page': 0, 'page_size': 500,
        }
        self.request.return_value = response
        result = api.get_event_index('coldwave', min_time='2026091405', max_time='2026-09-15T06:15:12.125+02:00',
                                     min_latitude=-10, max_latitude=10, min_longitude=170, max_longitude=-170,
                                     page=0, page_size=500)
        self.assertIs(result, response)
        self.request.assert_called_once()
        self.assertEqual(self.params(), {
            'min_time': '2026-09-14T05:00:00', 'max_time': '2026-09-15T04:15:12.125000Z',
            'min_latitude': -10, 'max_latitude': 10, 'min_longitude': 170, 'max_longitude': -170,
            'page': 0, 'page_size': 500,
        })

    def test_latest_is_supported_without_losing_omission_semantics(self):
        for function, args in [(api.get_events, ('heatwave',)), (api.get_event, ('hw_00012026',)), (api.get_event_context, ('0,0',))]:
            with self.subTest(function=function.__name__):
                function(*args, initialization_time='latest')
                self.assertEqual(self.params()['initialization_time'], 'latest')
                function(*args, initialization_time=None)
                self.assertNotIn('initialization_time', self.params())

    def test_ids_and_model_are_encoded_as_individual_path_segments(self):
        for function, suffix in [(api.get_event, ''), (api.get_event_init_times, '/init_times')]:
            with self.subTest(function=function.__name__):
                function('event/id?format=geojson#x', model='future/model')
                self.assertEqual(self.request.call_args.args[0],
                                 'https://api.windbornesystems.com/insights/v1/future%2Fmodel/event%2Fid%3Fformat%3Dgeojson%23x' + suffix)

    @staticmethod
    def geojson_response():
        return {
            'type': 'FeatureCollection', 'model': 'wm-6', 'init_time': '2026-09-14T05:00:00Z',
            'forecast_zero': '2026-09-14T00:00:00Z', 'total': 1,
            'lineage': {'parents': ['front_00012026'], 'children': []},
            'features': [{
                'type': 'Feature',
                'geometry': {'type': 'MultiLineString', 'coordinates': [[[179, 35], [180, 36]], [[-180, 36], [-179, 37]]]},
                'properties': {'event_id': 'front_00022026', 'forecast_hour': 0, 'name': 'cold_front',
                               'summary': {'symbol_sides': ['left', 'right'], 'length_km': 245.12}},
            }],
        }

    def test_geojson_geometry_lineage_and_forecast_metadata_survive_return_save_print(self):
        for function, args in [(api.get_events, ('front',)), (api.get_event, ('front_00022026',))]:
            with self.subTest(function=function.__name__), tempfile.TemporaryDirectory() as directory:
                response = self.geojson_response()
                original = copy.deepcopy(response)
                self.request.return_value = response
                output = Path(directory) / 'nested' / 'front.geojson'
                with contextlib.redirect_stdout(io.StringIO()) as printed:
                    result = function(*args, format='geojson', output_file=output, print_response=True)
                self.assertIs(result, response)
                self.assertEqual(response, original)
                self.assertEqual(json.loads(output.read_text()), original)
                self.assertEqual(json.loads(printed.getvalue()), original)
                self.assertEqual(self.params()['format'], 'geojson')

    def test_context_preserves_location_and_time_arrays_and_event_summaries(self):
        response = {
            'model': 'wm-6', 'initialization_time': '2026-09-14T05:00:00Z', 'forecast_zero': '2026-09-14T00:00:00Z',
            'events': [[
                {'latitude': 0, 'longitude': 0, 'time': '2026-09-15T00:00:00Z', 'events': {
                    'hw_00012026': {'event_type': 'heatwave', 'forecast_hour': 24, 'period_end': '2026-09-15T03:00:00Z', 'summary': {'max_temp_c': 38}},
                }},
                {'latitude': 0, 'longitude': 0, 'time': '2026-09-15T03:00:00Z', 'events': {}},
            ], []],
        }
        self.request.return_value = response
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'context.json'
            result = api.get_event_context([(0, 0), {'latitude': 35, 'longitude': -129}],
                                           initialization_time='2026091405', min_forecast_time='2026-09-15T00:00:00Z',
                                           max_forecast_time='2026-09-15T06:00:00Z', event_type='heatwave', output_file=output)
            self.assertIs(result, response)
            self.assertEqual(json.loads(output.read_text()), response)
        self.assertEqual(self.params(), {
            'coordinates': '0,0;35,-129', 'initialization_time': '2026-09-14T05:00:00',
            'min_forecast_time': '2026-09-15T00:00:00Z', 'max_forecast_time': '2026-09-15T06:00:00Z', 'event_type': 'heatwave',
        })

    def test_context_rejects_unsupported_list_entries_without_losing_location_order(self):
        with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(ValueError):
            api.get_event_context([(1, 2), 123, (3, 4)])
        self.request.assert_not_called()

    def test_initialization_times_preserve_order_and_latest(self):
        response = {'event_id': 'ar_00012026', 'available': ['2026-09-14T04:00:00Z', '2026-09-14T05:00:00Z'], 'latest': '2026-09-14T05:00:00Z'}
        self.request.return_value = response
        with contextlib.redirect_stdout(io.StringIO()) as printed:
            self.assertIs(api.get_event_init_times('ar_00012026', print_response=True), response)
        self.assertEqual(json.loads(printed.getvalue()), response)

    def test_unsupported_output_fails_before_request(self):
        for function, args, output in [
            (api.get_events, ('front',), 'events.csv'),
            (api.get_event, ('ar_00012026',), 'event.geojson'),
            (api.get_event_index, ('heatwave',), 'index.geojson'),
            (api.get_event_init_times, ('ar_00012026',), 'runs.geojson'),
            (api.get_event_context, ('0,0',), 'context.csv'),
        ]:
            with self.subTest(function=function.__name__, output=output):
                with self.assertRaises(ValueError):
                    function(*args, output_file=output)
        self.request.assert_not_called()

    def test_none_response_neither_writes_nor_prints(self):
        self.request.return_value = None
        for function, args in [
            (api.get_events, ('front',)), (api.get_event_index, ('heatwave',)),
            (api.get_event, ('ar_00012026',)), (api.get_event_init_times, ('ar_00012026',)),
            (api.get_event_context, ('0,0',)),
        ]:
            with self.subTest(function=function.__name__), tempfile.TemporaryDirectory() as directory:
                output = Path(directory) / 'result.json'
                with contextlib.redirect_stdout(io.StringIO()) as printed:
                    self.assertIsNone(function(*args, output_file=output, print_response=True))
                self.assertFalse(output.exists())
                self.assertEqual(printed.getvalue(), '')

    def test_empty_response_is_saved_without_inventing_fields(self):
        self.request.return_value = {}
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'empty.json'
            self.assertEqual(api.get_events('front', output_file=output), {})
            self.assertEqual(json.loads(output.read_text()), {})


if __name__ == '__main__':
    unittest.main()
