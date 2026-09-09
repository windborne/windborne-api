import unittest
import json
import tempfile
from unittest.mock import patch

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
            output_format='zarr',
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

    @patch('windborne.forecasts_api.download_and_save_output')
    @patch('windborne.forecasts_api.make_api_request')
    def test_gridded_explicit_format_controls_default_extension(self, request, download):
        response = object()
        request.return_value = response

        forecasts_api.get_gridded_forecast(
            'temperature_2m',
            time='2026-09-09T00:00:00Z',
            output_file='forecast',
            output_format='netcdf',
            model='wm-6',
            silent=True,
        )

        download.assert_called_once_with('forecast', response, default_extension='.nc')

    @patch('windborne.forecasts_api.make_api_request', return_value={'archived_initialization_times': []})
    def test_archive_returns_response_and_current_pagination(self, request):
        result = forecasts_api.get_archived_initialization_times(
            page=2, page_size=10, order='asc', domain='global'
        )
        self.assertEqual({'archived_initialization_times': []}, result)
        self.assertEqual(
            {'page': 2, 'page_size': 10, 'order': 'asc', 'domain': 'global'},
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

    @patch('windborne.forecasts_api.make_api_request')
    def test_undocumented_analysis_variables_route_is_not_called(self, request):
        with self.assertRaises(NotImplementedError):
            forecasts_api.get_analysis_variables()
        request.assert_not_called()


if __name__ == '__main__':
    unittest.main()
