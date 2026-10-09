import contextlib
import io
import unittest
from unittest import mock

from windborne import cli


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

    def test_gridded_url_and_ensemble_options_in_every_positional_form(self):
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
                        '--model', 'wm-6', '--as-url', '--include-deterministic', 'false', '--skip-mean',
                    ], 'get_gridded_forecast',
                )
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
                self.assertEqual(kwargs['model'], 'wm')

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
                 (['--include-high-frequency', 'true'], True), (['--include-high-frequency', 'false'], False)]
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
