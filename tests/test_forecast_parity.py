"""Regression tests for the documented forecast SDK contract (no API calls)."""
import contextlib
import csv
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from windborne import forecasts_api as api


class ForecastParityTests(unittest.TestCase):
    def setUp(self):
        self.request_patch = patch.object(api, 'make_api_request')
        self.request = self.request_patch.start()
        self.addCleanup(self.request_patch.stop)
        self.request.return_value = {'forecasts': []}

    def params(self):
        return self.request.call_args.kwargs.get('params', {})

    def test_archive_returns_envelope_and_preserves_positional_page_end(self):
        response = {'archived_initialization_times': ['2026-07-24T18:00:00Z'], 'total': 1, 'page': 0, 'page_size': 64}
        self.request.return_value = response
        with contextlib.redirect_stdout(io.StringIO()) as printed:
            result = api.get_archived_initialization_times(True, 0, 'wm-6', '2026072500', page=0, page_size=64, order='oldest', domain='europe')
        self.assertIs(result, response)
        self.assertEqual(self.params(), {'ens_member': 0, 'page_end': '2026-07-25T00:00:00', 'page': 0, 'page_size': 64, 'order': 'oldest', 'domain': 'europe'})
        self.assertIn(response['archived_initialization_times'][0], printed.getvalue())

    def test_zero_bounds_reach_both_point_forecast_endpoints(self):
        for function in (api.get_point_forecasts, api.get_point_forecasts_interpolated):
            with self.subTest(function=function.__name__):
                function('37,-122', min_forecast_hour=0, max_forecast_hour=0)
                self.assertEqual(self.params()['min_forecast_hour'], 0)
                self.assertEqual(self.params()['max_forecast_hour'], 0)

    def test_zero_ensemble_member_reaches_availability_and_gridded(self):
        for function in (api.get_run_information, api.get_initialization_times, api.get_calculation_times_degree_days):
            with self.subTest(function=function.__name__):
                function(ens_member=0)
                self.assertEqual(self.params()['ens_member'], 0)
        api.get_gridded_forecast('temperature_2m', initialization_time='2026072400', forecast_hour=0, ens_member=0)
        self.assertEqual(self.params()['ens_member'], 0)
        self.assertEqual(self.params()['forecast_hour'], 0)

    def test_domains_are_forwarded_for_regional_availability(self):
        for function in (api.get_run_information, api.get_initialization_times, api.get_archived_initialization_times):
            with self.subTest(function=function.__name__):
                function(model='wm-6-3km', domain='europe')
                self.assertEqual(self.params()['domain'], 'europe')

    def test_gridded_explicit_format_controls_download_extension_and_flags(self):
        self.request.return_value = Mock(content=b'forecast bytes')
        with tempfile.TemporaryDirectory() as directory:
            for format, suffix in [('netcdf', '.nc'), ('zarr', '.zarr.zip')]:
                output = str(Path(directory) / format)
                api.get_gridded_forecast('temperature_2m', initialization_time='2026072400', forecast_hour=0,
                                         model='wm-6-3km', format=format, domain='europe', include_distribution=True,
                                         include_members=True, output_file=output, silent=True)
                self.assertEqual(self.params()['format'], format)
                self.assertEqual(self.params()['domain'], 'europe')
                self.assertEqual(self.params()['include_members'], 'true')
                self.assertEqual(self.params()['include_distribution'], 'true')
                self.assertEqual(Path(output + suffix).read_bytes(), b'forecast bytes')

    def test_full_gridded_forwards_new_options(self):
        api.get_full_gridded_forecast(time='2026072400', format='netcdf', domain='conus')
        self.assertEqual(self.params()['variable'], 'all')
        self.assertEqual(self.params()['format'], 'netcdf')
        self.assertEqual(self.params()['domain'], 'conus')

    def test_degree_days_default_to_latest_but_allow_specific_run(self):
        for function in (api.get_population_weighted_hdds, api.get_population_weighted_cdds):
            with self.subTest(function=function.__name__):
                function()
                self.assertNotIn('initialization_time', self.params())
                function(initialization_time='latest')
                self.assertNotIn('initialization_time', self.params())
                function('2026072400', 0)
                self.assertEqual(self.params()['initialization_time'], '2026-07-24T00:00:00')
                self.assertEqual(self.params()['ens_member'], 0)

    def test_degree_days_json_preserves_full_response(self):
        for function, key in [(api.get_population_weighted_hdds, 'hdd'), (api.get_population_weighted_cdds, 'cdd')]:
            with self.subTest(function=function.__name__), tempfile.TemporaryDirectory() as directory:
                response = {'initialization_time': '2026-07-24T00:00:00Z', 'dates': ['2026-07-24'], key: {'2026-07-24': {'United States': 4.5}}}
                self.request.return_value = response
                output = Path(directory) / (key + '.json')
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertIs(function(output_file=str(output)), response)
                self.assertEqual(json.loads(output.read_text()), response)

    def test_degree_days_csv_supports_date_and_region_keyed_data(self):
        dates = ['2026-07-24', '2026-07-25']
        for function, key in [(api.get_population_weighted_hdds, 'hdd'), (api.get_population_weighted_cdds, 'cdd')]:
            for data in [
                {'2026-07-24': {'Canada': 0, 'United States': 4.5}, '2026-07-25': {'United States': 5.5}},
                {'Canada': {'2026-07-24': 0}, 'United States': {'2026-07-24': 4.5, '2026-07-25': 5.5}},
            ]:
                with self.subTest(function=function.__name__, data=data), tempfile.TemporaryDirectory() as directory:
                    response = {'dates': dates, key: data}
                    self.request.return_value = response
                    output = Path(directory) / (key + '.csv')
                    with contextlib.redirect_stdout(io.StringIO()) as printed:
                        self.assertIs(function(output_file=str(output), print_response=True), response)
                    with output.open() as file:
                        self.assertEqual(list(csv.reader(file)), [['Region'] + dates, ['Canada', '0', ''], ['United States', '4.5', '5.5']])
                    self.assertIn('United States:', printed.getvalue())
                    self.assertIn('2026-07-24: 0', printed.getvalue())

    def test_degree_days_missing_response_does_not_write_or_crash(self):
        self.request.return_value = None
        for function in (api.get_population_weighted_hdds, api.get_population_weighted_cdds):
            for extension in ('.csv', '.json'):
                with self.subTest(function=function.__name__, extension=extension), tempfile.TemporaryDirectory() as directory:
                    output = Path(directory) / ('degree-days' + extension)
                    self.assertIsNone(function(output_file=str(output), print_response=True))
                    self.assertFalse(output.exists())

    def test_filtered_coordinate_printing_uses_retained_input_index(self):
        response = {'filtered_coordinates': [0], 'forecasts': [[{'time': '2026-07-24T00:00:00Z', 'temperature_2m': 20}]]}
        self.request.return_value = response
        with contextlib.redirect_stdout(io.StringIO()) as printed:
            result = api.get_point_forecasts_interpolated('1,2;3,4', print_response=True)
        self.assertIs(result, response)
        self.assertIn('Forecast for (3, 4)', printed.getvalue())
        self.assertNotIn('Forecast for (1, 2)', printed.getvalue())

    def test_all_filtered_coordinates_print_no_location(self):
        self.request.return_value = {'filtered_coordinates': [0, 1], 'forecasts': []}
        with contextlib.redirect_stdout(io.StringIO()) as printed:
            api.get_point_forecasts_interpolated('1,2;3,4', print_response=True)
        self.assertNotIn('Forecast for (', printed.getvalue())

    def test_tc_current_basins_and_legacy_alias(self):
        self.request.return_value = {'tropical_cyclones': {}, 'total': 0}
        for basin, expected in [('AL', 'AL'), ('CP', 'CP'), ('NA', 'AL'), ('ep', 'EP')]:
            with self.subTest(basin=basin):
                api.get_tropical_cyclones('latest', basin, model='wm-6', include_details=True, include_unofficial_ids=True)
                self.assertEqual(self.params()['basin'], expected)
                self.assertNotIn('initialization_time', self.params())
                self.assertEqual(self.params()['include_details'], 'true')
                self.assertEqual(self.params()['include_unofficial_ids'], 'true')

    @staticmethod
    def cyclone_response():
        return {
            'initialization_time': '2026-07-24T18:00:00Z', 'forecast_zero': '2026-07-24T18:00:00Z', 'total': 1,
            'tropical_cyclones': {'EP072026': {'tropical_cyclone_id': 'EP072026', 'storm_name': 'GENEVIEVE',
                'path': [{'valid_at': '2026-07-24T18:00:00Z', 'latitude': 9.2, 'longitude': -101.1}]}}
        }

    def test_tc_current_envelope_prints_without_treating_metadata_as_tracks(self):
        response = self.cyclone_response()
        self.request.return_value = response
        with contextlib.redirect_stdout(io.StringIO()) as printed:
            self.assertIs(api.get_tropical_cyclones(model='wm-6', include_details=True, print_response=True), response)
        self.assertIn('GENEVIEVE', printed.getvalue())
        self.assertIn('2026-07-24T18:00:00Z', printed.getvalue())
        self.assertNotIn('Cyclone ID: initialization_time', printed.getvalue())

    def test_tc_compact_summary_and_empty_list_print(self):
        response = self.cyclone_response()
        del response['tropical_cyclones']['EP072026']['path']
        self.request.return_value = response
        with contextlib.redirect_stdout(io.StringIO()) as printed:
            api.get_tropical_cyclones(model='wm-6', print_response=True)
        self.assertIn('GENEVIEVE', printed.getvalue())
        self.request.return_value = {'tropical_cyclones': {}, 'total': 0}
        with contextlib.redirect_stdout(io.StringIO()) as printed:
            api.get_tropical_cyclones(model='wm-6', print_response=True)
        self.assertIn('No tropical cyclones', printed.getvalue())

    def test_tc_json_preserves_envelope_and_track_exports_use_valid_at(self):
        response = self.cyclone_response()
        self.request.return_value = response
        with tempfile.TemporaryDirectory() as directory:
            output_json = str(Path(directory) / 'cyclones.json')
            api.get_tropical_cyclones(output_file=output_json, model='wm-6')
            self.assertEqual(json.loads(Path(output_json).read_text()), response)
            self.assertEqual(self.params()['include_details'], 'false')
            output_csv = str(Path(directory) / 'cyclones.csv')
            api.get_tropical_cyclones(output_file=output_csv, model='wm-6')
            self.assertEqual(self.params()['include_details'], 'true')
            with open(output_csv) as file:
                rows = list(csv.DictReader(file))
            self.assertEqual(rows[0]['id'], 'EP072026')
            self.assertEqual(rows[0]['time'], '2026-07-24T18:00:00Z')
            self.assertNotIn('time', response['tropical_cyclones']['EP072026']['path'][0])
            output_gpx = str(Path(directory) / 'cyclones.gpx')
            api.get_tropical_cyclones(output_file=output_gpx, model='wm-6')
            self.assertIn('<time>2026-07-24T18:00:00Z</time>', Path(output_gpx).read_text())

    def test_tc_geojson_exports_native_features_without_losing_metadata(self):
        response = {
            'type': 'FeatureCollection',
            'features': [{
                'type': 'Feature',
                'properties': {'tropical_cyclone_id': 'EP072026'},
                'geometry': {'type': 'LineString', 'coordinates': [[-101.1, 9.2], [-102, 10]]},
            }],
            'initialization_time': '2026-07-24T18:00:00Z',
        }
        self.request.return_value = response
        with tempfile.TemporaryDirectory() as directory:
            output = str(Path(directory) / 'cyclones.geojson')
            self.assertIs(api.get_tropical_cyclones(model='wm-6', output_file=output), response)
            self.assertEqual(self.params()['format'], 'geojson')
            self.assertEqual(self.params()['include_details'], 'true')
            self.assertEqual(json.loads(Path(output).read_text()), response)

    def test_tc_legacy_tracks_still_print_and_export(self):
        self.request.return_value = {'AL012025': [{'time': '2025-08-01T00:00:00Z', 'latitude': 20, 'longitude': -60}]}
        with tempfile.TemporaryDirectory() as directory, contextlib.redirect_stdout(io.StringIO()) as printed:
            output = str(Path(directory) / 'legacy.csv')
            api.get_tropical_cyclones(None, 'NA', output, True, 'wm')
            self.assertIn('AL012025', printed.getvalue())
            self.assertIn('2025-08-01T00:00:00Z', Path(output).read_text())

    def test_tc_detail_json_and_deck_have_correct_response_modes(self):
        self.request.return_value = {'tropical_cyclone_id': 'EP072026', 'mean_path': []}
        api.get_tropical_cyclone('EP072026', initialization_time='2026072418', include_members=True, include_cones=True)
        self.assertTrue(self.request.call_args.kwargs['as_json'])
        self.assertTrue(self.request.call_args.args[0].endswith('/wm-6/tropical_cyclones/EP072026'))
        self.assertEqual(self.params()['include_members'], 'true')
        self.assertEqual(self.params()['include_cones'], 'true')
        self.request.return_value = Mock(content=b'EP, 07, A-deck\n', text='EP, 07, A-deck\n')
        with tempfile.TemporaryDirectory() as directory:
            output = str(Path(directory) / 'storm.deck')
            response = api.get_tropical_cyclone('EP072026', format='deck', output_file=output)
            self.assertIs(response, self.request.return_value)
            self.assertFalse(self.request.call_args.kwargs['as_json'])
            self.assertEqual(Path(output).read_bytes(), b'EP, 07, A-deck\n')

    def test_tc_index_bounds_pagination_and_availability_routes(self):
        self.request.return_value = {'tropical_cyclones': [], 'available': []}
        api.get_tropical_cyclone_index(basin='CP', min_time='2026072400', page=0, page_size=64)
        self.assertTrue(self.request.call_args.args[0].endswith('/wm-6/tropical_cyclones/index'))
        self.assertEqual(self.params()['min_time'], '2026-07-24T00:00:00')
        self.assertNotIn('max_time', self.params())
        self.assertEqual(self.params()['page'], 0)
        self.assertEqual(self.params()['page_size'], 64)
        api.get_tropical_cyclone_init_times('AL022026')
        self.assertTrue(self.request.call_args.args[0].endswith('/wm-6/tropical_cyclones/AL022026/init_times'))
        api.get_calculation_times_tropical_cyclones()
        self.assertTrue(self.request.call_args.args[0].endswith('/insights/v1/wm-6/calculation_times/tropical_cyclones'))

    def test_conditions_accept_coordinate_list_and_forward_interval(self):
        response = {'forecasts': [{'latitude': 37.77, 'longitude': -122.42, 'hourly': [{'start_time': 'a', 'end_time': 'b', 'text': 'Clear'}]}]}
        self.request.return_value = response
        with contextlib.redirect_stdout(io.StringIO()) as printed:
            result = api.get_point_forecast_conditions([(37.77, -122.42), (40.7, -74.0)], model='wm-6', hourly_interval=6, print_response=True)
        self.assertIs(result, response)
        self.assertEqual(self.params(), {'coordinates': '37.77,-122.42;40.7,-74.0', 'hourly_interval': 6})
        self.assertTrue(self.request.call_args.args[0].endswith('/wm-6/point_forecast/conditions'))
        self.assertIn('Clear', printed.getvalue())

    def test_new_helpers_handle_missing_response(self):
        self.request.return_value = None
        for function, kwargs in [
            (api.get_tropical_cyclones, {}), (api.get_tropical_cyclone, {'tropical_cyclone_id': 'AL022026'}),
            (api.get_tropical_cyclone_index, {}), (api.get_tropical_cyclone_init_times, {'tropical_cyclone_id': 'AL022026'}),
            (api.get_calculation_times_tropical_cyclones, {}), (api.get_point_forecast_conditions, {'coordinates': '1,2'}),
            (api.get_archived_initialization_times, {}),
        ]:
            with self.subTest(function=function.__name__):
                self.assertIsNone(function(print_response=True, **kwargs))


if __name__ == '__main__':
    unittest.main()
