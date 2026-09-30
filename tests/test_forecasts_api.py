import unittest
import json
import tempfile
from unittest.mock import Mock, patch

import requests

from windborne import forecasts_api
from windborne.track_formatting import save_track_as_gpx


class ForecastsApiTest(unittest.TestCase):
    @patch('windborne.forecasts_api.make_api_request', return_value=[])
    def test_available_stations_uses_unscoped_route(self, request):
        forecasts_api.get_available_stations()
        request.assert_called_once_with(
            'https://api.windbornesystems.com/forecasts/v1/point_forecast/stations'
        )

    @patch('windborne.forecasts_api.make_api_request', return_value={})
    def test_run_and_initialization_times_support_domain(self, request):
        forecasts_api.get_run_information(domain='conus', ens_member=0)
        forecasts_api.get_initialization_times(domain='europe')
        self.assertEqual({'ens_member': 0, 'domain': 'conus'}, request.call_args_list[0].kwargs['params'])
        self.assertEqual({'domain': 'europe'}, request.call_args_list[1].kwargs['params'])

    @patch('windborne.forecasts_api.make_api_request', return_value={'forecasts': []})
    def test_point_forecast_uses_canonical_route(self, request):
        forecasts_api.get_point_forecasts(stations='kjfk')
        request.assert_called_once_with(
            'https://api.windbornesystems.com/forecasts/v1/point_forecast',
            params={'stations': 'KJFK'},
        )

    @patch('windborne.forecasts_api.make_api_request', return_value={'forecasts': []})
    def test_point_forecast_keeps_zero_hour_bounds(self, request):
        forecasts_api.get_point_forecasts(
            coordinates='40,-73',
            min_forecast_hour=0,
            max_forecast_hour=0,
        )
        self.assertEqual(
            {'coordinates': '40,-73', 'min_forecast_hour': 0, 'max_forecast_hour': 0},
            request.call_args.kwargs['params'],
        )

    @patch('windborne.forecasts_api.make_api_request', return_value={'forecasts': []})
    def test_station_forecast_uses_generic_point_forecast(self, request):
        forecasts_api.get_station_forecast('KJFK')
        self.assertEqual(
            'https://api.windbornesystems.com/forecasts/v1/point_forecast',
            request.call_args.args[0],
        )
        self.assertEqual({'stations': 'KJFK'}, request.call_args.kwargs['params'])

    @patch('windborne.forecasts_api.make_api_request', return_value={})
    def test_conditions(self, request):
        forecasts_api.get_point_forecast_conditions([(40, -73)], hourly_interval=3)
        request.assert_called_once_with(
            'https://api.windbornesystems.com/forecasts/v1/wm-6/point_forecast/conditions',
            params={'coordinates': '40,-73', 'hourly_interval': 3},
        )

    @patch('windborne.forecasts_api.make_api_request')
    def test_gridded_supports_current_parameters(self, request):
        forecasts_api.get_gridded_forecast(
            'temperature_2m',
            time='2026-09-09T00:00:00Z',
            include_distribution=True,
            include_deterministic=True,
            include_members=True,
            skip_mean=True,
            format='zarr',
            as_url=True,
            domain='global',
        )
        self.assertEqual(
            'https://api.windbornesystems.com/forecasts/v1/wm-6/gridded',
            request.call_args.args[0],
        )
        self.assertEqual(
            {
                'time': '2026-09-09T00:00:00Z',
                'variable': 'temperature_2m',
                'include_distribution': True,
                'include_members': True,
                'include_deterministic': True,
                'skip_mean': True,
                'format': 'zarr',
                'as_url': True,
                'domain': 'global',
            },
            request.call_args.kwargs['params'],
        )
        self.assertFalse(request.call_args.kwargs['stream'])

    @patch('windborne.forecasts_api.download_and_save_output')
    @patch('windborne.forecasts_api.make_api_request')
    def test_gridded_explicit_format_controls_default_extension(self, request, download):
        response = object()
        request.return_value = response

        forecasts_api.get_gridded_forecast(
            'temperature_2m',
            time='2026-09-09T00:00:00Z',
            output_file='forecast',
            format='netcdf',
            model='wm-6',
            silent=True,
        )

        download.assert_called_once_with(
            'forecast', response, silent=True, default_extension='.nc'
        )
        self.assertTrue(request.call_args.kwargs['stream'])

    @patch('windborne.forecasts_api.make_api_request')
    def test_gridded_as_url_requires_json_output(self, request):
        with self.assertRaisesRegex(ValueError, 'must be saved to a .json file'):
            forecasts_api.get_gridded_forecast(
                'temperature_2m',
                time='2026-09-09T00:00:00Z',
                as_url=True,
                output_file='forecast.nc',
            )
        request.assert_not_called()

    @patch('windborne.forecasts_api.make_api_request')
    def test_gridded_rejects_conflicting_time_modes(self, request):
        with self.assertRaisesRegex(ValueError, 'cannot be combined'):
            forecasts_api.get_gridded_forecast(
                'temperature_2m',
                time='2026-09-09T06:00:00Z',
                initialization_time='2026-09-09T00:00:00Z',
                forecast_hour=6,
            )
        request.assert_not_called()

    def test_gridded_download_streams_chunks(self):
        response = Mock()
        response.iter_content.return_value = [b'first', b'', b'second']

        with tempfile.TemporaryDirectory() as directory:
            output_file = f'{directory}/forecast.nc'
            forecasts_api.download_and_save_output(output_file, response, silent=True)
            with open(output_file, 'rb') as forecast_file:
                self.assertEqual(b'firstsecond', forecast_file.read())

        response.iter_content.assert_called_once_with(chunk_size=1024 * 1024)
        response.close.assert_called_once_with()

    def test_failed_gridded_download_preserves_existing_file(self):
        response = Mock()
        response.iter_content.side_effect = requests.exceptions.ChunkedEncodingError(
            'incomplete response'
        )

        with tempfile.TemporaryDirectory() as directory:
            output_file = f'{directory}/forecast.nc'
            with open(output_file, 'wb') as forecast_file:
                forecast_file.write(b'complete previous download')

            with self.assertRaises(requests.exceptions.ChunkedEncodingError):
                forecasts_api.download_and_save_output(output_file, response, silent=True)

            with open(output_file, 'rb') as forecast_file:
                self.assertEqual(b'complete previous download', forecast_file.read())

        response.close.assert_called_once_with()

    @patch('windborne.forecasts_api.make_api_request', return_value={'archived_initialization_times': []})
    def test_archive_returns_response_and_current_pagination(self, request):
        result = forecasts_api.get_archived_initialization_times(
            page=2, page_size=10, order='oldest', domain='global'
        )
        self.assertEqual({'archived_initialization_times': []}, result)
        self.assertEqual(
            {'page': 2, 'page_size': 10, 'order': 'oldest', 'domain': 'global'},
            request.call_args.kwargs['params'],
        )

    @patch('windborne.forecasts_api.make_api_request', return_value={})
    def test_tropical_cyclone_routes_and_parameters(self, request):
        forecasts_api.get_tropical_cyclones(
            basin='al', include_unofficial_ids=True, include_details=True, format='geojson'
        )
        forecasts_api.get_tropical_cyclone_index(
            basin='EP', min_time='2026090100', max_time='2026090900', page=0, page_size=64
        )
        forecasts_api.get_tropical_cyclone(
            'AL022026', initialization_time='2026090900', include_members=True, include_cones=True,
            format='deck'
        )
        forecasts_api.get_tropical_cyclone_init_times('AL022026')

        self.assertEqual(
            {'basin': 'AL', 'include_unofficial_ids': True, 'include_details': True, 'format': 'geojson'},
            request.call_args_list[0].kwargs['params'],
        )
        self.assertTrue(request.call_args_list[1].args[0].endswith('/tropical_cyclones/index'))
        self.assertEqual(
            {'basin': 'EP', 'min_time': '2026-09-01T00:00:00', 'max_time': '2026-09-09T00:00:00', 'page': 0, 'page_size': 64},
            request.call_args_list[1].kwargs['params'],
        )
        self.assertTrue(request.call_args_list[2].args[0].endswith('/tropical_cyclones/AL022026'))
        self.assertEqual(
            {'initialization_time': '2026-09-09T00:00:00', 'include_members': True, 'include_cones': True, 'format': 'deck'},
            request.call_args_list[2].kwargs['params'],
        )
        self.assertFalse(request.call_args_list[2].kwargs['as_json'])
        self.assertTrue(request.call_args_list[3].args[0].endswith('/tropical_cyclones/AL022026/init_times'))

    @patch('windborne.forecasts_api.make_api_request', return_value={})
    def test_tropical_cyclone_latest_initialization_time_is_supported(self, request):
        forecasts_api.get_tropical_cyclones(initialization_time='latest')
        forecasts_api.get_tropical_cyclone('AL022026', initialization_time='latest')

        self.assertEqual('latest', request.call_args_list[0].kwargs['params']['initialization_time'])
        self.assertEqual('latest', request.call_args_list[1].kwargs['params']['initialization_time'])

    @patch('windborne.forecasts_api.make_api_request')
    def test_tropical_cyclone_invalid_options_raise_value_error(self, request):
        with self.assertRaisesRegex(ValueError, 'Basin must be one of'):
            forecasts_api.get_tropical_cyclones(basin='invalid')
        with self.assertRaisesRegex(ValueError, 'Unsupported file format'):
            forecasts_api.get_tropical_cyclones(output_file='tracks.txt')
        request.assert_not_called()

    @patch('builtins.print')
    @patch('windborne.forecasts_api.make_api_request')
    def test_tropical_cyclone_empty_envelope_is_reported(self, request, print_output):
        response = {
            'initialization_time': '2026-09-09T00:00:00Z',
            'tropical_cyclones': {},
            'total': 0,
        }
        request.return_value = response

        result = forecasts_api.get_tropical_cyclones(print_response=True)

        self.assertEqual(response, result)
        print_output.assert_called_once_with(
            'No tropical cyclones for initialization time:',
            '2026-09-09T00:00:00Z',
        )

    def test_gpx_date_line_crossing_uses_configured_time_key(self):
        tracks = {
            'AL022026': [
                {'valid_at': '2026-09-09T00:00:00Z', 'latitude': 20, 'longitude': 179},
                {'valid_at': '2026-09-09T01:00:00Z', 'latitude': 21, 'longitude': -179},
            ]
        }

        with tempfile.TemporaryDirectory() as directory:
            output_file = f'{directory}/tracks.gpx'
            save_track_as_gpx(output_file, tracks, time_key='valid_at')
            with open(output_file, encoding='utf-8') as exported_file:
                exported = exported_file.read()

        self.assertIn('<time>2026-09-09T00:00:00Z</time>', exported)
        self.assertIn('<time>2026-09-09T01:00:00Z</time>', exported)
        self.assertEqual(2, exported.count('<trkseg>'))

    @patch('windborne.forecasts_api.print_table')
    @patch('windborne.forecasts_api.make_api_request')
    def test_tropical_cyclone_summary_response_prints_without_requesting_details(self, request, print_table):
        request.return_value = {
            'initialization_time': '2026-09-09T00:00:00Z',
            'tropical_cyclones': {
                'AL022026': {
                    'tropical_cyclone_id': 'AL022026',
                    'genesis': {'latitude': 20, 'longitude': -60},
                    'storm_name': 'TEST',
                    'basins': ['AL'],
                    'start_time': '2026-09-09T00:00:00Z',
                    'end_time': '2026-09-16T00:00:00Z',
                    'max_wind_kt': 70.1,
                    'min_mslp_hpa': 982.3,
                }
            },
        }
        forecasts_api.get_tropical_cyclones(print_response=True)

        self.assertNotIn('include_details', request.call_args.kwargs['params'])
        print_table.assert_called_once()
        summary = print_table.call_args.args[0][0]
        self.assertEqual('TEST', summary['storm_name'])
        self.assertEqual('AL', summary['basins'])
        self.assertEqual('20, -60', summary['genesis'])

    @patch('windborne.forecasts_api.print_table')
    @patch('windborne.forecasts_api.make_api_request')
    def test_tropical_cyclone_detailed_response_prints_path(self, request, print_table):
        request.return_value = {
            'tropical_cyclones': {
                'AL022026': {
                    'path': [
                        {'valid_at': '2026-09-09T00:00:00Z', 'latitude': 20, 'longitude': -60}
                    ]
                }
            },
        }

        forecasts_api.get_tropical_cyclones(include_details=True, print_response=True)

        self.assertEqual(2, print_table.call_count)
        self.assertEqual('2026-09-09T00:00:00Z', print_table.call_args_list[1].args[0][0]['valid_at'])

    @patch('builtins.print')
    @patch('windborne.forecasts_api.print_table')
    @patch('windborne.forecasts_api.make_api_request')
    def test_tropical_cyclone_geojson_prints_without_track_formatting(self, request, print_table, print_output):
        response = {'type': 'FeatureCollection', 'features': []}
        request.return_value = response

        result = forecasts_api.get_tropical_cyclones(format='geojson', print_response=True)

        self.assertEqual(response, result)
        print_table.assert_not_called()
        print_output.assert_called_once()

    @patch('windborne.forecasts_api.save_track')
    @patch('windborne.forecasts_api.make_api_request')
    def test_tropical_cyclone_track_export_requests_details(self, request, save_track):
        request.return_value = {
            'tropical_cyclones': {
                'AL022026': {
                    'path': [
                        {'valid_at': '2026-09-09T00:00:00Z', 'latitude': 20, 'longitude': -60}
                    ]
                }
            }
        }

        forecasts_api.get_tropical_cyclones(output_file='tracks.csv')

        self.assertTrue(request.call_args.kwargs['params']['include_details'])
        self.assertTrue(save_track.call_args.args[1]['AL022026'])

    @patch('windborne.forecasts_api.make_api_request')
    def test_tropical_cyclone_geojson_export_is_a_feature_collection(self, request):
        request.return_value = {'type': 'FeatureCollection', 'features': []}

        with tempfile.TemporaryDirectory() as directory:
            output_file = f'{directory}/tracks.geojson'
            forecasts_api.get_tropical_cyclones(output_file=output_file)
            with open(output_file, encoding='utf-8') as exported_file:
                exported = json.load(exported_file)

        self.assertEqual('geojson', request.call_args.kwargs['params']['format'])
        self.assertEqual('FeatureCollection', exported['type'])

    @patch('windborne.forecasts_api.make_api_request')
    def test_tropical_cyclone_json_details_can_be_converted_to_geojson(self, request):
        request.return_value = {
            'tropical_cyclones': {
                'AL022026': {
                    'path': [
                        {'valid_at': '2026-09-09T00:00:00Z', 'latitude': 20, 'longitude': -60},
                        {'valid_at': '2026-09-09T01:00:00Z', 'latitude': 21, 'longitude': -61},
                    ]
                }
            }
        }

        with tempfile.TemporaryDirectory() as directory:
            output_file = f'{directory}/tracks.geojson'
            forecasts_api.get_tropical_cyclones(format='json', output_file=output_file)
            with open(output_file, encoding='utf-8') as exported_file:
                exported = json.load(exported_file)

        self.assertEqual(
            {'include_details': True, 'format': 'json'},
            request.call_args.kwargs['params'],
        )
        self.assertEqual('FeatureCollection', exported['type'])

    @patch('windborne.forecasts_api.make_api_request')
    def test_tropical_cyclone_geojson_response_rejects_track_table_export(self, request):
        with self.assertRaisesRegex(ValueError, 'GeoJSON responses'):
            forecasts_api.get_tropical_cyclones(format='geojson', output_file='tracks.csv')

        request.assert_not_called()

    @patch('windborne.forecasts_api.save_arbitrary_response')
    @patch('windborne.forecasts_api.make_api_request')
    def test_tropical_cyclone_geojson_response_can_be_saved_as_json(self, request, save_response):
        response = {'type': 'FeatureCollection', 'features': []}
        request.return_value = response

        forecasts_api.get_tropical_cyclones(format='geojson', output_file='tracks.json')

        save_response.assert_called_once_with('tracks.json', response)

    @patch('windborne.forecasts_api.get_point_forecasts_interpolated', return_value={})
    def test_documented_interpolated_name_accepts_time(self, interpolated):
        forecasts_api.get_interpolated_point_forecast('40,-73', time='2026-09-09T00:00:00Z')
        interpolated.assert_called_once_with(
            '40,-73',
            min_forecast_time='2026-09-09T00:00:00Z',
            max_forecast_time='2026-09-09T00:00:00Z',
        )

    @patch('windborne.forecasts_api.make_api_request', return_value={})
    def test_degree_days_initialization_time_is_optional(self, request):
        forecasts_api.get_population_weighted_hdds()
        forecasts_api.get_population_weighted_cdds()
        self.assertEqual({}, request.call_args_list[0].kwargs['params'])
        self.assertEqual({}, request.call_args_list[1].kwargs['params'])

    @patch('windborne.forecasts_api.save_arbitrary_response')
    @patch('windborne.forecasts_api.make_api_request')
    def test_degree_days_json_output_is_saved(self, request, save_response):
        request.return_value = {'dates': [], 'hdd': {}, 'cdd': {}}

        forecasts_api.get_population_weighted_hdds(output_file='hdds.json')
        forecasts_api.get_population_weighted_cdds(output_file='cdds.json')

        save_response.assert_any_call('hdds.json', request.return_value)
        save_response.assert_any_call('cdds.json', request.return_value)

    @patch('windborne.forecasts_api.make_api_request', return_value={})
    def test_calculation_times_use_forecast_routes(self, request):
        forecasts_api.get_calculation_times_degree_days(model='wm-6')
        forecasts_api.get_calculation_times_tropical_cyclones(model='wm-6')

        self.assertTrue(
            request.call_args_list[0].args[0].endswith(
                '/forecasts/v1/wm-6/calculation_times/degree_days'
            )
        )
        self.assertTrue(
            request.call_args_list[1].args[0].endswith(
                '/forecasts/v1/wm-6/calculation_times/tropical_cyclones'
            )
        )

    @patch('windborne.forecasts_api.make_api_request', return_value={})
    def test_interpolated_sounding_accepts_documented_coordinate_tuple(self, request):
        forecasts_api.get_interpolated_sounding(
            (40.7, -74.0), time='2026-09-09T00:00:00Z'
        )
        self.assertEqual('40.7,-74.0', request.call_args.kwargs['params']['coordinates'])

    @patch('windborne.forecasts_api.make_api_request')
    def test_invalid_coordinates_raise_value_error(self, request):
        with self.assertRaises(ValueError):
            forecasts_api.get_point_forecasts(coordinates=[(40.7, -74.0), object()])
        request.assert_not_called()

    def test_analysis_variables_is_not_part_of_the_sdk(self):
        self.assertFalse(hasattr(forecasts_api, 'get_analysis_variables'))


if __name__ == '__main__':
    unittest.main()
