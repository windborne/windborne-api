import unittest
from unittest.mock import patch

from windborne import forecasts_api


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

    @patch('windborne.forecasts_api.print_table')
    @patch('windborne.forecasts_api.make_api_request')
    def test_tropical_cyclone_current_response_shape_prints(self, request, print_table):
        request.return_value = {
            'initialization_time': '2026-09-09T00:00:00Z',
            'tropical_cyclones': {
                'AL022026': {
                    'mean_path': [
                        {'valid_at': '2026-09-09T00:00:00Z', 'latitude': 20, 'longitude': -60}
                    ]
                }
            },
        }
        forecasts_api.get_tropical_cyclones(print_response=True)
        print_table.assert_called_once()

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
