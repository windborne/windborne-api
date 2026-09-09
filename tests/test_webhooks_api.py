import unittest
from unittest.mock import patch

import windborne
from windborne import webhooks_api


class WebhooksApiTest(unittest.TestCase):
    @patch('windborne.webhooks_api.make_api_request', return_value={})
    def test_endpoint_crud(self, request):
        subscriptions = {
            'initialization_time.available': {'filters': {'model': 'wm-6'}}
        }
        webhooks_api.create_webhook(
            'https://receiver.test/hook',
            name='Forecasts',
            active=False,
            subscriptions=subscriptions,
        )
        webhooks_api.list_webhooks(page=1, page_size=20, active=True, subscription_type='forecast_hour.available')
        webhooks_api.get_webhook('wh_1')
        webhooks_api.update_webhook('wh_1', note=None, active=False)
        webhooks_api.delete_webhook('wh_1')

        self.assertEqual(
            {
                'method': 'POST',
                'json': {
                    'url': 'https://receiver.test/hook',
                    'name': 'Forecasts',
                    'subscriptions': subscriptions,
                    'active': False,
                },
            },
            request.call_args_list[0].kwargs,
        )
        self.assertEqual(
            {'page': 1, 'page_size': 20, 'active': True, 'subscription_type': 'forecast_hour.available'},
            request.call_args_list[1].kwargs['params'],
        )
        self.assertEqual({}, request.call_args_list[2].kwargs)
        self.assertEqual({'method': 'PATCH', 'json': {'note': None, 'active': False}}, request.call_args_list[3].kwargs)
        self.assertEqual({'method': 'DELETE'}, request.call_args_list[4].kwargs)

    @patch('windborne.webhooks_api.make_api_request', return_value=None)
    def test_subscription_crud_and_ping(self, request):
        webhooks_api.add_webhook_subscription(
            'wh_1', 'initialization_time.available', filters={'model': 'wm-6'}
        )
        webhooks_api.update_webhook_subscription(
            'wh_1', 'sub_1', response_options=None
        )
        webhooks_api.delete_webhook_subscription('wh_1', 'sub_1')
        webhooks_api.ping_webhook_subscription('wh_1', 'sub_1')

        self.assertEqual(
            {'method': 'PATCH', 'json': {'subscription_type': 'initialization_time.available', 'filters': {'model': 'wm-6'}}},
            request.call_args_list[0].kwargs,
        )
        self.assertEqual({'method': 'PATCH', 'json': {'response_options': None}}, request.call_args_list[1].kwargs)
        self.assertEqual({'method': 'DELETE'}, request.call_args_list[2].kwargs)
        self.assertEqual({'method': 'POST'}, request.call_args_list[3].kwargs)

    def test_documented_functions_are_public(self):
        for name in [
            'create_webhook', 'list_webhooks', 'get_webhook', 'update_webhook', 'delete_webhook',
            'add_webhook_subscription', 'update_webhook_subscription',
            'delete_webhook_subscription', 'ping_webhook_subscription',
            'get_interpolated_point_forecast', 'get_point_forecast_conditions',
            'get_tropical_cyclone', 'get_tropical_cyclone_index',
            'get_tropical_cyclone_init_times',
        ]:
            self.assertTrue(hasattr(windborne, name), name)
            self.assertIn(name, windborne.__all__)


if __name__ == '__main__':
    unittest.main()
