"""User-facing argument-order regressions, with API dispatch mocked."""

import contextlib
import io
import unittest
from unittest import mock

from windborne import cli, cli_public_api


class CliArgumentOrderTests(unittest.TestCase):
    def invoke(self, arguments, function, module=cli):
        with mock.patch.object(module, function, autospec=True) as called, \
                mock.patch('sys.argv', ['windborne'] + arguments), \
                contextlib.redirect_stdout(io.StringIO()):
            cli.main()
        called.assert_called_once()
        return called.call_args.kwargs

    def test_options_at_every_boundary_preserve_positional_order(self):
        cases = [
            ('tropical_cyclones', ['detail', 'EP072026', 'out.deck'],
             ['--format', 'deck'], 'get_tropical_cyclone',
             {'tropical_cyclone_id': 'EP072026', 'output_file': 'out.deck', 'format': 'deck'}),
            ('tropical_cyclones', ['index', 'out.json'],
             ['--page', '1'], 'get_tropical_cyclone_index',
             {'page': 1, 'output_file': 'out.json'}),
            ('points', ['37.77,-122.42', 'out.csv'],
             ['--model', 'wm-6'], 'get_point_forecasts',
             {'coordinates': '37.77,-122.42', 'model': 'wm-6', 'output_file': 'out.csv'}),
            ('points_interpolated', ['37.77,-122.42', 'out.csv'],
             ['--model', 'wm-6'], 'get_point_forecasts_interpolated',
             {'coordinates': '37.77,-122.42', 'model': 'wm-6', 'output_file': 'out.csv'}),
            ('interpolated_sounding', ['37.77,-122.42', 'out.csv'],
             ['--forecast-hour', '0'], 'get_interpolated_sounding',
             {'coordinates': '37.77,-122.42', 'forecast_hour': 0, 'output_file': 'out.csv'}),
            ('asos_recent', ['KDWH', 'out.csv'],
             ['--include-high-frequency', 'true'], 'get_recent_asos_observations',
             {'station': 'KDWH', 'include_high_frequency': True, 'output_file': 'out.csv'}),
            ('analysis_interpolated', ['37.77,-122.42', '2026-10-12T12:00:00Z', 'out.csv'],
             ['--source', 'era5'], 'get_interpolated_analysis',
             {'coordinates': '37.77,-122.42', 'time': '2026-10-12T12:00:00Z',
              'source': 'era5', 'output_file': 'out.csv'}),
        ]
        for command, positional, options, function, expected in cases:
            for boundary in range(len(positional) + 1):
                arguments = [command] + positional[:boundary] + options + positional[boundary:]
                with self.subTest(arguments=arguments):
                    kwargs = self.invoke(arguments, function)
                    for key, value in expected.items():
                        self.assertEqual(kwargs[key], value)

    def test_multiple_option_groups_and_negative_numeric_values(self):
        kwargs = self.invoke(
            ['points_interpolated', '--model=wm-6', '37.77,-122.42',
             '--min-hour', '0', 'out.csv', '--max-hour', '12', '--variable', 'temperature_2m'],
            'get_point_forecasts_interpolated',
        )
        self.assertEqual(kwargs['coordinates'], '37.77,-122.42')
        self.assertEqual(kwargs['model'], 'wm-6')
        self.assertEqual(kwargs['min_forecast_hour'], 0)
        self.assertEqual(kwargs['max_forecast_hour'], 12)
        self.assertEqual(kwargs['variable'], 'temperature_2m')
        self.assertEqual(kwargs['output_file'], 'out.csv')
        kwargs = self.invoke(
            ['observations_page', '2026-10-12T00:00:00Z', '--min-latitude', '-35',
             'out.json', '--min-longitude', '-120'], 'get_observations_page',
        )
        self.assertEqual(kwargs['min_latitude'], -35)
        self.assertEqual(kwargs['min_longitude'], -120)
        self.assertEqual(kwargs['output_file'], 'out.json')

    def test_separator_preserves_negative_coordinates_and_option_like_filenames(self):
        kwargs = self.invoke(
            ['points', '--model', 'wm-6', '--', '-33.86,151.21', '--model'],
            'get_point_forecasts',
        )
        self.assertEqual(kwargs['coordinates'], '-33.86,151.21')
        self.assertEqual(kwargs['model'], 'wm-6')
        self.assertEqual(kwargs['output_file'], '--model')
        kwargs = self.invoke(
            ['tropical_cyclones', 'detail', '--format', 'deck', '--', 'EP072026', '-out.deck'],
            'get_tropical_cyclone',
        )
        self.assertEqual(kwargs['tropical_cyclone_id'], 'EP072026')
        self.assertEqual(kwargs['output_file'], '-out.deck')

    def test_nested_commands_preserve_options_and_read_request_body_once(self):
        kwargs = self.invoke(
            ['events', 'detail', '--model', 'wm-6', 'heatwave-123', '--output', 'event.json'],
            'get_event', cli_public_api,
        )
        self.assertEqual(kwargs['event_id'], 'heatwave-123')
        self.assertEqual(kwargs['model'], 'wm-6')
        self.assertEqual(kwargs['output_file'], 'event.json')
        body = io.StringIO('{"url": "https://example.test/events"}')
        with mock.patch('sys.stdin', body):
            kwargs = self.invoke(
                ['webhooks', 'update', '--body', '-', '42', '--output', 'webhook.json'],
                'update_webhook', cli_public_api,
            )
        self.assertEqual(kwargs['webhook_id'], '42')
        self.assertEqual(kwargs['url'], 'https://example.test/events')
        self.assertEqual(kwargs['output_file'], 'webhook.json')

    def test_invalid_arguments_never_dispatch(self):
        cases = [
            ['points', '37.77,-122.42', '--unknown', 'out.csv'],
            ['points', '37.77,-122.42', '--model', 'wm-6', 'first.csv', 'extra.csv'],
            ['points', '37.77,-122.42', '--model'],
            ['tropical_cyclones', 'detail', 'EP072026', '--format', 'deck', 'first.deck', 'extra.deck'],
            ['tropical_cyclones', 'index', '--page', '1', 'first.json', 'extra.json'],
            ['tropical_cyclones', 'detail', '--format', 'deck'],
            ['tropical_cyclones', 'detail', 'EP072026', '--page', 'not-an-integer'],
            ['tropical_cyclones', 'detail', 'EP072026', '--format', 'deck', '--unknown', 'out.deck'],
            ['events', 'detail', 'event-123', '--model', 'wm-6', 'extra.json'],
            ['webhooks', 'update', '42'],
        ]
        for arguments in cases:
            with self.subTest(arguments=arguments), contextlib.ExitStack() as stack:
                calls = [stack.enter_context(mock.patch.object(module, name)) for module, name in [
                    (cli, 'get_point_forecasts'), (cli, 'get_tropical_cyclone'),
                    (cli, 'get_tropical_cyclone_index'), (cli_public_api, 'get_event'),
                    (cli_public_api, 'update_webhook'),
                ]]
                stack.enter_context(mock.patch('sys.argv', ['windborne'] + arguments))
                stack.enter_context(contextlib.redirect_stderr(io.StringIO()))
                with self.assertRaises(SystemExit) as error:
                    cli.main()
                self.assertEqual(error.exception.code, 2)
                for called in calls:
                    called.assert_not_called()

    def test_top_level_and_nested_help(self):
        for command in [[], ['points'], ['tropical_cyclones'], ['events', 'detail'], ['webhooks', 'update']]:
            output = io.StringIO()
            with self.subTest(command=command), \
                    mock.patch('sys.argv', ['windborne'] + command + ['--help']), \
                    contextlib.redirect_stdout(output), self.assertRaises(SystemExit) as error:
                cli.main()
            self.assertEqual(error.exception.code, 0)
            self.assertIn('usage:', output.getvalue())


if __name__ == '__main__':
    unittest.main()
