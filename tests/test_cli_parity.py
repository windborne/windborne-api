import contextlib
import copy
import io
import json
import os
import tempfile
import unittest
from unittest import mock

from windborne import api_request, cli


class CliParityTests(unittest.TestCase):
    def invoke(self, arguments, function):
        with mock.patch.object(cli, function, autospec=True) as called:
            with mock.patch('sys.argv', ['windborne'] + arguments):
                with contextlib.redirect_stdout(io.StringIO()):
                    cli.main()
            called.assert_called_once()
            return called.call_args.kwargs

    def test_archive_pagination_and_legacy_page_end(self):
        kwargs = self.invoke(
            ['archived_init_times', '--model', 'wm-6', '--page', '0',
             '--page-size', '64', '--order', 'oldest'],
            'get_archived_initialization_times',
        )
        self.assertEqual(kwargs['page'], 0)
        self.assertEqual(kwargs['page_size'], 64)
        self.assertEqual(kwargs['order'], 'oldest')
        self.assertIsNone(kwargs['page_end'])
        kwargs = self.invoke(
            ['archived_init_times', '-p', '2026-10-01T00:00:00Z'],
            'get_archived_initialization_times',
        )
        self.assertEqual(kwargs['page_end'], '2026-10-01T00:00:00Z')
        self.assertIsNone(kwargs['page'])

    def test_documented_command_aliases_preserve_existing_names(self):
        for command in ['point_forecast', 'points']:
            with self.subTest(command=command):
                kwargs = self.invoke([command, '37.77,-122.42', 'output.csv'], 'get_point_forecasts')
                self.assertEqual(kwargs['coordinates'], '37.77,-122.42')
                self.assertEqual(kwargs['output_file'], 'output.csv')
        for command in ['predicted_path', 'predict_path']:
            with self.subTest(command=command):
                kwargs = self.invoke([command, '494f8cb2-5fed-4c81-b3c4-5eacaa2ba4e0', 'output.json'], 'get_predicted_path')
                self.assertEqual(kwargs['mission_id'], '494f8cb2-5fed-4c81-b3c4-5eacaa2ba4e0')
                self.assertEqual(kwargs['output_file'], 'output.json')

    def test_run_information_defaults_to_latest(self):
        kwargs = self.invoke(['run_information', '--model', 'wm-6'], 'get_run_information')
        self.assertIsNone(kwargs['initialization_time'])
        self.assertEqual(kwargs['model'], 'wm-6')

    def test_gridded_format_in_every_supported_positional_form(self):
        cases = [
            (['temperature', '2026100100', 'forecast.nc'],
             {'variable': 'temperature', 'time': '2026100100'}),
            (['temperature', '2026100100', '0', 'forecast.nc'],
             {'variable': 'temperature', 'initialization_time': '2026100100', 'forecast_hour': '0'}),
            (['temperature', '500', '2026100100', 'forecast.nc'],
             {'variable': '500/temperature', 'time': '2026100100'}),
            (['temperature', '500', '2026100100', '0', 'forecast.nc'],
             {'variable': '500/temperature', 'initialization_time': '2026100100', 'forecast_hour': '0'}),
        ]
        for positional, expected in cases:
            with self.subTest(positional=positional):
                kwargs = self.invoke(
                    ['gridded'] + positional + ['-m', 'wm-6', '-f', 'netcdf'],
                    'get_gridded_forecast',
                )
                self.assertEqual(kwargs['format'], 'netcdf')
                self.assertEqual(kwargs['output_file'], 'forecast.nc')
                for key, value in expected.items():
                    self.assertEqual(kwargs[key], value)
        kwargs = self.invoke(
            ['gridded', 'temperature', '2026100100', 'forecast.zarr'],
            'get_gridded_forecast',
        )
        self.assertIsNone(kwargs['format'])

    def test_regional_domain_options(self):
        cases = [
            (['init_times'], 'get_initialization_times'),
            (['archived_init_times'], 'get_archived_initialization_times'),
            (['run_information', '2026100100'], 'get_run_information'),
            (['gridded', 'temperature_2m', '2026100100', 'forecast.zarr'], 'get_gridded_forecast'),
        ]
        for arguments, function in cases:
            with self.subTest(command=arguments[0]):
                kwargs = self.invoke(arguments + ['--model', 'wm-6-3km', '--domain', 'europe'], function)
                self.assertEqual(kwargs['domain'], 'europe')
                self.assertEqual(kwargs['model'], 'wm-6-3km')

    def test_gridded_shared_options_in_every_positional_form(self):
        cases = [
            ['temperature_2m', '2026100100', 'url.json'],
            ['temperature_2m', '2026100100', '0', 'url.json'],
            ['temperature', '500', '2026100100', 'url.json'],
            ['temperature', '500', '2026100100', '0', 'url.json'],
        ]
        for positional in cases:
            with self.subTest(positional=positional):
                kwargs = self.invoke(
                    ['gridded'] + positional + [
                        '--model', 'wm-6-3km', '--ens-member', '3', '--domain', 'europe',
                        '--format', 'netcdf', '--include-distribution', '--include-members',
                        '--as-url', '--include-deterministic', 'false', '--skip-mean',
                    ], 'get_gridded_forecast',
                )
                self.assertEqual(kwargs['model'], 'wm-6-3km')
                self.assertEqual(kwargs['ens_member'], '3')
                self.assertEqual(kwargs['domain'], 'europe')
                self.assertEqual(kwargs['format'], 'netcdf')
                self.assertTrue(kwargs['include_distribution'])
                self.assertTrue(kwargs['include_members'])
                self.assertTrue(kwargs['as_url'])
                self.assertFalse(kwargs['include_deterministic'])
                self.assertTrue(kwargs['skip_mean'])
                self.assertEqual(kwargs['output_file'], 'url.json')

    def test_gridded_level_request_error_is_not_retried_as_surface_variable(self):
        with mock.patch.object(cli, 'get_gridded_forecast', autospec=True, side_effect=ValueError('Unsupported format')) as called:
            with mock.patch('sys.argv', ['windborne', 'gridded', 'temperature', '500', '2026100100', '0', 'out.nc', '-f', 'netcdf']):
                with self.assertRaisesRegex(ValueError, 'Unsupported format'):
                    cli.main()
            called.assert_called_once()
            self.assertEqual(called.call_args.kwargs['variable'], '500/temperature')

    def test_tropical_cyclones_documented_list(self):
        kwargs = self.invoke(
            ['tropical_cyclones', '-m', 'wm-6', '--initialization-time', '2026072418',
             '--basin', 'EP', '--include-details', 'true', '--include-unofficial-ids', 'false',
             '--format', 'geojson'],
            'get_tropical_cyclones',
        )
        self.assertEqual(kwargs['initialization_time'], '2026072418')
        self.assertEqual(kwargs['basin'], 'EP')
        self.assertTrue(kwargs['include_details'])
        self.assertFalse(kwargs['include_unofficial_ids'])
        self.assertEqual(kwargs['format'], 'geojson')
        self.assertTrue(kwargs['print_response'])

    def test_tropical_cyclones_preserves_legacy_positionals(self):
        cases = [
            ([], None, None),
            (['2026100100'], '2026100100', None),
            (['cyclones.json'], None, 'cyclones.json'),
            (['2026100100', 'cyclones.json'], '2026100100', 'cyclones.json'),
            (['2026-10-01T00:00:00.000Z'], '2026-10-01T00:00:00.000Z', None),
        ]
        for suffix in ['.json', '.geojson', '.csv', '.gpx', '.kml', '.little_r']:
            cases.append(([f'TC_tracks{suffix}'], None, f'TC_tracks{suffix}'))
            cases.append(([f'TC_tracks{suffix.upper()}'], None, f'TC_tracks{suffix.upper()}'))
        for positional, initialization_time, output_file in cases:
            with self.subTest(positional=positional):
                kwargs = self.invoke(['tropical_cyclones'] + positional, 'get_tropical_cyclones')
                self.assertEqual(kwargs['initialization_time'], initialization_time)
                self.assertEqual(kwargs['output_file'], output_file)
                self.assertEqual(kwargs['print_response'], not output_file)
                self.assertEqual(kwargs['model'], 'wm-6')

    def test_tropical_cyclone_filename_only_exports_tracks_from_json(self):
        track = [
            {'valid_at': '2026-07-24T18:00:00Z', 'latitude': 20.5, 'longitude': -110.0},
            {'valid_at': '2026-07-25T00:00:00Z', 'latitude': 21.0, 'longitude': -111.0},
        ]
        cases = [
            ('legacy list', [], ['--model', 'gfs'], '/forecasts/v1/gfs/tropical_cyclones',
             {'EP072026': [dict(time=point['valid_at'], latitude=point['latitude'],
                               longitude=point['longitude']) for point in track]},
             'EP072026', 'include_details'),
            ('current list', [], ['--model', 'wm-6'], '/weather/v1/events/tropical_cyclones',
             {'initialization_time': '2026-07-24T18:00:00Z',
              'tropical_cyclones': {'EP072026': {'path': track}}},
             'EP072026', 'include_details'),
            ('unmatched detail', ['detail', 'generated-unmatched-id'], ['--model', 'wm-6'],
             '/weather/v1/events/tropical_cyclones/generated-unmatched-id',
             {'tropical_cyclone_id': 'generated-unmatched-id', 'mean_path': [],
              'members_path': [{'member': 1, 'path': track}]},
             'generated-unmatched-id', 'include_members'),
        ]
        for name, operation, options, route, payload, cyclone_id, needed_paths in cases:
            for options_first in (True, False):
                with self.subTest(case=name, options_first=options_first), tempfile.TemporaryDirectory() as tmp:
                    output = os.path.join(tmp, 'storm.geojson')
                    original_payload = copy.deepcopy(payload)
                    response = mock.Mock(status_code=200)
                    response.json.return_value = payload
                    arguments = operation + (options + [output] if options_first else [output] + options)
                    with mock.patch('sys.argv', ['windborne', 'tropical_cyclones'] + arguments), \
                            mock.patch.object(api_request, 'get_verified_api_credentials', return_value=('test_client', 's' * 32)), \
                            mock.patch.object(api_request.requests, 'get', return_value=response) as get, \
                            contextlib.redirect_stdout(io.StringIO()):
                        cli.main()
                    get.assert_called_once()
                    self.assertEqual(get.call_args.args[0], 'https://api.windbornesystems.com' + route)
                    self.assertEqual(get.call_args.kwargs['params']['format'], 'json')
                    self.assertEqual(get.call_args.kwargs['params'][needed_paths], 'true')
                    with open(output, encoding='utf-8') as stream:
                        exported = json.load(stream)
                    self.assertEqual(exported['type'], 'FeatureCollection')
                    self.assertEqual(len(exported['features']), 1)
                    feature = exported['features'][0]
                    self.assertEqual(feature['properties']['id'], cyclone_id)
                    self.assertEqual(feature['geometry'], {
                        'type': 'MultiLineString',
                        'coordinates': [[[-110.0, 20.5], [-111.0, 21.0]]],
                    })
                    self.assertEqual(payload, original_payload)

    def test_tropical_cyclone_explicit_geojson_preserves_native_response(self):
        payload = {
            'type': 'FeatureCollection',
            'initialization_time': '2026-07-24T18:00:00Z',
            'features': [
                {'type': 'Feature', 'geometry': {'type': 'Point', 'coordinates': [-110.0, 20.5]},
                 'properties': {'tropical_cyclone_id': 'EP072026', 'max_wind_kt': 65,
                                'landfall': {'country': 'Mexico'}}},
                {'type': 'Feature', 'geometry': {'type': 'Polygon', 'coordinates': [
                    [[-111.0, 20.0], [-110.0, 21.0], [-109.0, 20.0], [-111.0, 20.0]]]},
                 'properties': {'kind': 'cone', 'probability': 0.67}},
            ],
        }
        cases = [
            ('legacy list', [], ['--model', 'gfs'], '/forecasts/v1/gfs/tropical_cyclones.geojson'),
            ('current list', [], ['--model', 'wm-6'], '/weather/v1/events/tropical_cyclones'),
            ('detail', ['detail', 'EP072026'], ['--model', 'wm-6', '--include-cones'],
             '/weather/v1/events/tropical_cyclones/EP072026'),
        ]
        for name, operation, options, route in cases:
            options = options + ['--format', 'geojson']
            for options_first in (True, False):
                with self.subTest(case=name, options_first=options_first), tempfile.TemporaryDirectory() as tmp:
                    output = os.path.join(tmp, 'storm.geojson')
                    response = mock.Mock(status_code=200)
                    response.json.return_value = copy.deepcopy(payload)
                    arguments = operation + (options + [output] if options_first else [output] + options)
                    with mock.patch('sys.argv', ['windborne', 'tropical_cyclones'] + arguments), \
                            mock.patch.object(api_request, 'get_verified_api_credentials', return_value=('test_client', 's' * 32)), \
                            mock.patch.object(api_request.requests, 'get', return_value=response) as get, \
                            contextlib.redirect_stdout(io.StringIO()):
                        cli.main()
                    get.assert_called_once()
                    self.assertEqual(get.call_args.args[0], 'https://api.windbornesystems.com' + route)
                    self.assertEqual(get.call_args.kwargs['params']['format'], 'geojson')
                    with open(output, encoding='utf-8') as stream:
                        self.assertEqual(json.load(stream), payload)

    def test_tropical_cyclone_index(self):
        kwargs = self.invoke(
            ['tropical_cyclones', 'index', '-m', 'wm-6', '--basin', 'EP',
             '--min-time', '2026072400', '--max-time', '2026100100', '--page', '0',
             '--page-size', '64', '--include-unofficial-ids', 'true'],
            'get_tropical_cyclone_index',
        )
        self.assertEqual(kwargs['min_time'], '2026072400')
        self.assertEqual(kwargs['max_time'], '2026100100')
        self.assertEqual(kwargs['page'], 0)
        self.assertEqual(kwargs['page_size'], 64)
        self.assertTrue(kwargs['include_unofficial_ids'])

    def test_tropical_cyclone_detail(self):
        kwargs = self.invoke(
            ['tropical_cyclones', 'detail', 'EP072026', '-m', 'wm-6',
             '--initialization-time', '2026072418', '--include-cones', 'true',
             '--include-members', 'false', '--format', 'geojson'],
            'get_tropical_cyclone',
        )
        self.assertEqual(kwargs['tropical_cyclone_id'], 'EP072026')
        self.assertEqual(kwargs['initialization_time'], '2026072418')
        self.assertTrue(kwargs['include_cones'])
        self.assertFalse(kwargs['include_members'])
        self.assertEqual(kwargs['format'], 'geojson')
        kwargs = self.invoke(
            ['tropical_cyclones', 'detail', 'EP072026', 'cyclone.atcf', '--format', 'deck'],
            'get_tropical_cyclone',
        )
        self.assertEqual(kwargs['output_file'], 'cyclone.atcf')
        self.assertFalse(kwargs['print_response'])

    def test_tropical_cyclone_initialization_and_calculation_times(self):
        kwargs = self.invoke(
            ['tropical_cyclones', 'init_times', 'AL022026', '-m', 'wm-6'],
            'get_tropical_cyclone_init_times',
        )
        self.assertEqual(kwargs['tropical_cyclone_id'], 'AL022026')
        self.assertTrue(kwargs['print_response'])
        kwargs = self.invoke(
            ['calculation_times', 'tropical_cyclones', '-m', 'wm-6'],
            'get_calculation_times_tropical_cyclones',
        )
        self.assertEqual(kwargs['model'], 'wm-6')
        self.assertTrue(kwargs['print_response'])

    def test_conditions_documented_command(self):
        kwargs = self.invoke(
            ['point_forecast_conditions', '--model', 'wm-6', '37.77,-122.42;40.7,-74.0',
             '--hourly-interval', '6', 'output.json'],
            'get_point_forecast_conditions',
        )
        self.assertEqual(kwargs['coordinates'], '37.77,-122.42;40.7,-74.0')
        self.assertEqual(kwargs['hourly_interval'], 6)
        self.assertEqual(kwargs['output_file'], 'output.json')
        self.assertFalse(kwargs['print_response'])

    def test_conditions_output_before_after_or_without_options(self):
        cases = [
            (['37.77,-122.42', 'output.json', '--hourly-interval', '6'], 'output.json'),
            (['37.77,-122.42', '--hourly-interval', '6', 'output.json'], 'output.json'),
            (['--hourly-interval', '6', '37.77,-122.42', 'output.json'], 'output.json'),
            (['37.77,-122.42', '--hourly-interval', '6'], None),
        ]
        for arguments, output_file in cases:
            with self.subTest(arguments=arguments):
                kwargs = self.invoke(
                    ['point-forecast-conditions'] + arguments,
                    'get_point_forecast_conditions',
                )
                self.assertEqual(kwargs['coordinates'], '37.77,-122.42')
                self.assertEqual(kwargs['hourly_interval'], 6)
                self.assertEqual(kwargs['output_file'], output_file)
                self.assertEqual(kwargs['print_response'], output_file is None)

    def test_conditions_rejects_unknown_options_and_extra_outputs(self):
        cases = [
            ['37.77,-122.42', '--unknown'],
            ['37.77,-122.42', '--unknown', 'output.json'],
            ['37.77,-122.42', '--hourly-interval', '6', '--unknown', 'output.json'],
            ['37.77,-122.42', 'first.json', '--hourly-interval', '6', 'second.json'],
            ['37.77,-122.42', '--hourly-interval', '6', 'first.json', 'second.json'],
        ]
        for arguments in cases:
            with self.subTest(arguments=arguments):
                with mock.patch('sys.argv', ['windborne', 'point_forecast_conditions'] + arguments), \
                        mock.patch.object(cli, 'get_point_forecast_conditions') as called, \
                        contextlib.redirect_stderr(io.StringIO()), \
                        self.assertRaises(SystemExit) as error:
                    cli.main()
                self.assertEqual(error.exception.code, 2)
                called.assert_not_called()

    def test_degree_days_allow_latest_and_explicit_run(self):
        for command, function in [('hdds', 'get_population_weighted_hdds'), ('cdds', 'get_population_weighted_cdds')]:
            with self.subTest(command=command):
                kwargs = self.invoke([command, '-m', 'wm-6', '-o', 'forecast.csv'], function)
                self.assertIsNone(kwargs['initialization_time'])
                self.assertEqual(kwargs['output_file'], 'forecast.csv')
                kwargs = self.invoke([command, '2026100100', '-m', 'wm-6'], function)
                self.assertEqual(kwargs['initialization_time'], '2026100100')
                self.assertTrue(kwargs['print_response'])

    def test_soundings_minimum_length(self):
        kwargs = self.invoke(['soundings', '--min-length', '2000', 'soundings.json'], 'get_soundings')
        self.assertEqual(kwargs['min_length'], 2000.0)
        self.assertEqual(kwargs['output_file'], 'soundings.json')

    def test_asos_high_frequency_can_be_omitted_true_or_false(self):
        cases = [([], None), (['--include-high-frequency'], True),
                 (['--include-high-frequency', 'true'], True), (['--include-high-frequency', 'false'], False),
                 (['--include-high-frequency', 'TRUE'], True), (['--include-high-frequency', 'False'], False)]
        for flags, expected in cases:
            with self.subTest(flags=flags):
                kwargs = self.invoke(['asos_recent', 'KDFW'] + flags, 'get_recent_asos_observations')
                self.assertIs(kwargs['include_high_frequency'], expected)

    def test_zero_forecast_hour_limits_survive_cli(self):
        for command, function in [('points', 'get_point_forecasts'), ('points-interpolated', 'get_point_forecasts_interpolated')]:
            with self.subTest(command=command):
                kwargs = self.invoke([command, '37.77,-122.42', '--min-hour', '0', '--max-hour', '0'], function)
                self.assertEqual(kwargs['min_forecast_hour'], 0)
                self.assertEqual(kwargs['max_forecast_hour'], 0)

    def test_invalid_tropical_cyclone_arguments_fail_before_dispatch(self):
        cases = [
            ['tropical_cyclones', 'detail'],
            ['tropical_cyclones', 'init_times'],
            ['tropical_cyclones', '--include-details', 'maybe'],
            ['tropical_cyclones', '--format', 'deck'],
            ['tropical_cyclones', '2026100100', 'out.json', '--initialization-time', '2026100200'],
        ]
        for arguments in cases:
            with self.subTest(arguments=arguments):
                with mock.patch('sys.argv', ['windborne'] + arguments):
                    with contextlib.redirect_stderr(io.StringIO()):
                        with self.assertRaises(SystemExit) as error:
                            cli.main()
                self.assertEqual(error.exception.code, 2)


if __name__ == '__main__':
    unittest.main()
