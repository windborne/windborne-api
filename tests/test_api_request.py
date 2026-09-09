import unittest
from unittest.mock import Mock, patch

import requests

from windborne import api_request


class ApiRequestTest(unittest.TestCase):
    def setUp(self):
        api_request.VERIFIED_WB_CLIENT_ID = None
        api_request.VERIFIED_WB_API_KEY = None
        api_request._CREDENTIALS_VERIFIED = False

    @patch('windborne.api_request.requests.request')
    @patch('windborne.api_request.get_verified_api_credentials', return_value=(None, 'wb_test'))
    def test_bearer_auth_and_json_body(self, credentials, request):
        response = Mock(status_code=200)
        response.json.return_value = {'id': 'webhook'}
        request.return_value = response

        result = api_request.make_api_request(
            'https://example.test/webhooks',
            params={'page': 1},
            method='POST',
            json={'url': 'https://receiver.test'},
        )

        self.assertEqual({'id': 'webhook'}, result)
        request.assert_called_once_with(
            'POST',
            'https://example.test/webhooks',
            headers={'Authorization': 'Bearer wb_test'},
            params={'page': 1},
            json={'url': 'https://receiver.test'},
        )

    @patch('windborne.api_request.requests.request')
    @patch('windborne.api_request.jwt.encode', return_value='signed')
    @patch('windborne.api_request.get_verified_api_credentials', return_value=('client', 'secret'))
    def test_legacy_credentials_use_basic_jwt(self, credentials, encode, request):
        response = Mock(status_code=200)
        response.json.return_value = {}
        request.return_value = response

        api_request.make_api_request('https://example.test/data')

        request.assert_called_once_with(
            'GET', 'https://example.test/data', auth=('client', 'signed')
        )

    @patch('windborne.api_request.requests.request')
    @patch('windborne.api_request.get_verified_api_credentials', return_value=(None, 'wb_test'))
    def test_no_content_returns_none(self, credentials, request):
        request.return_value = Mock(status_code=204)
        self.assertIsNone(api_request.make_api_request('https://example.test/data', method='DELETE'))

    @patch('windborne.api_request.requests.request')
    @patch('windborne.api_request.get_verified_api_credentials', return_value=(None, 'wb_test'))
    def test_mutating_request_is_not_retried_after_connection_failure(self, credentials, request):
        request.side_effect = requests.exceptions.ConnectionError('connection lost')
        with self.assertRaises(requests.exceptions.ConnectionError):
            api_request.make_api_request('https://example.test/webhooks', method='POST', json={})
        self.assertEqual(1, request.call_count)

    def test_current_key_does_not_require_client_id(self):
        api_request.verify_api_credentials(None, 'wb_current-key')

    def test_missing_key_is_rejected(self):
        with self.assertRaises(ValueError):
            api_request.verify_api_credentials('client', None)


if __name__ == '__main__':
    unittest.main()
