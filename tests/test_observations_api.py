import unittest
from unittest.mock import patch

from windborne import observations_api


class ObservationsApiTest(unittest.TestCase):
    @patch('windborne.observations_api.make_api_request')
    def test_soundings_use_iso_times_and_min_length(self, request):
        request.return_value = {'soundings': []}
        observations_api.get_soundings(
            min_time='2026-09-01T00:00:00Z',
            max_time='2026-09-02T00:00:00Z',
            min_length=20,
        )
        self.assertEqual(
            {
                'min_time': '2026-09-01T00:00:00Z',
                'max_time': '2026-09-02T00:00:00Z',
                'min_length': 20,
            },
            request.call_args.kwargs['params'],
        )

    @patch('windborne.observations_api.make_api_request')
    def test_flying_missions_can_request_one_documented_page(self, request):
        request.return_value = {'missions': [{'id': 'mission'}]}
        result = observations_api.get_flying_missions(page=3, page_size=25)
        self.assertEqual([{'id': 'mission'}], result)
        request.assert_called_once_with(
            'https://api.windbornesystems.com/observations/v1/flying_missions.json',
            params={'page': 3, 'page_size': 25},
        )

    @patch('windborne.observations_api.make_api_request')
    def test_predicted_path_calls_mission_route_directly(self, request):
        request.return_value = {'prediction': []}
        self.assertEqual([], observations_api.get_predicted_path('mission-id'))
        request.assert_called_once_with(
            'https://api.windbornesystems.com/observations/v1/missions/mission-id/predicted_path.json'
        )


if __name__ == '__main__':
    unittest.main()
