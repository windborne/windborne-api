import json
from unittest import mock

import jwt
import pytest
import requests

from windborne import api_request


URL = 'https://api.windbornesystems.com/webhooks/v1'


def response(status, payload=None):
    result = requests.Response()
    result.status_code = status
    result.url = URL
    result._content = b'' if payload is None else json.dumps(payload).encode()
    return result


@pytest.fixture(autouse=True)
def fake_credentials(monkeypatch):
    monkeypatch.setattr(api_request, 'get_verified_api_credentials', lambda: ('sdk_test', 'x' * 32))


def test_get_preserves_existing_positional_signature_and_transport():
    result = response(200, {'webhooks': []})
    with mock.patch.object(api_request.requests, 'get', return_value=result) as get:
        assert api_request.make_api_request(URL, {'page': 1}, True, 0) == {'webhooks': []}
    args, kwargs = get.call_args
    assert args == (URL,)
    assert kwargs['params'] == {'page': 1}
    assert set(kwargs) == {'auth', 'params'}


@pytest.mark.parametrize('method', ['POST', 'PATCH', 'PUT', 'DELETE'])
def test_writes_preserve_signed_token_authentication_and_json_body(method):
    payload = {'active': False, 'response_options': None, 'filters': {}}
    result = response(200, {'id': 42})
    with mock.patch.object(api_request.requests, 'request', return_value=result) as request:
        assert api_request.make_api_request(URL, method=method.lower(), json=payload) == {'id': 42}
    args, kwargs = request.call_args
    assert args == (method, URL)
    assert kwargs['json'] is payload
    assert kwargs['allow_redirects'] is False
    client_id, token = kwargs['auth']
    assert client_id == 'sdk_test'
    decoded = jwt.decode(token, 'x' * 32, algorithms=['HS256'])
    assert decoded['client_id'] == client_id
    assert isinstance(decoded['iat'], int)


@pytest.mark.parametrize('method', ['POST', 'PATCH', 'PUT', 'DELETE'])
@pytest.mark.parametrize('status', [400, 401, 403, 404, 422, 500, 502])
def test_write_http_errors_raise_without_retry_or_logging(method, status, capsys):
    failed = response(status, {'signing_secret': 'synthetic-secret-must-not-be-logged'})
    with mock.patch.object(api_request.requests, 'request', return_value=failed) as request:
        with mock.patch.object(api_request.time, 'sleep') as sleep:
            with pytest.raises(requests.HTTPError) as caught:
                api_request.make_api_request(URL, method=method, json={'active': False})
            assert caught.value.response is failed
            request.assert_called_once()
            sleep.assert_not_called()
    assert capsys.readouterr().out == ''


@pytest.mark.parametrize('method', ['POST', 'PATCH', 'PUT', 'DELETE'])
@pytest.mark.parametrize('error_type', [requests.Timeout, requests.ConnectionError, requests.RequestException])
def test_ambiguous_write_failures_are_never_automatically_retried(method, error_type, capsys):
    error = error_type('Synthetic transport failure')
    with mock.patch.object(api_request.requests, 'request', side_effect=error) as request:
        with mock.patch.object(api_request.time, 'sleep') as sleep:
            with pytest.raises(error_type) as caught:
                api_request.make_api_request(URL, method=method)
            assert caught.value is error
            request.assert_called_once()
            sleep.assert_not_called()
    assert capsys.readouterr().out == ''


@pytest.mark.parametrize('method', ['POST', 'PATCH', 'DELETE'])
def test_empty_204_does_not_attempt_json_decoding(method):
    result = response(204)
    with mock.patch.object(api_request.requests, 'request', return_value=result):
        with mock.patch.object(result, 'json') as decode:
            assert api_request.make_api_request(URL, method=method) is None
            decode.assert_not_called()


def test_write_redirect_is_not_followed_or_reported_as_success():
    result = response(307)
    result.headers['Location'] = URL + '/elsewhere'
    with mock.patch.object(api_request.requests, 'request', return_value=result) as request:
        with pytest.raises(requests.HTTPError, match='Redirect refused'):
            api_request.make_api_request(URL, method='POST', json={})
        request.assert_called_once()
        assert request.call_args.kwargs['allow_redirects'] is False


def test_invalid_write_json_raises_without_retry():
    result = response(200)
    result._content = b'not JSON'
    with mock.patch.object(api_request.requests, 'request', return_value=result) as request:
        with pytest.raises(ValueError):
            api_request.make_api_request(URL, method='PATCH', json={})
        request.assert_called_once()


@pytest.mark.parametrize('failure', [response(502), requests.Timeout('timeout'), requests.ConnectionError('connection')])
def test_get_keeps_existing_retry_behavior(failure):
    successful = response(200, {'ok': True})
    with mock.patch.object(api_request.requests, 'get', side_effect=[failure, successful]) as get:
        with mock.patch.object(api_request.time, 'sleep') as sleep:
            assert api_request.make_api_request(URL) == {'ok': True}
            assert get.call_count == 2
            sleep.assert_called_once_with(1)


def test_get_retry_limit_still_applies():
    with mock.patch.object(api_request.requests, 'get', side_effect=requests.Timeout('timeout')) as get:
        with mock.patch.object(api_request.time, 'sleep'):
            with pytest.raises(ConnectionError, match='Max retries'):
                api_request.make_api_request(URL)
    assert get.call_count == 5


@pytest.mark.parametrize('status', [400, 403, 404])
def test_legacy_get_error_return_remains_none(status):
    with mock.patch.object(api_request.requests, 'get', return_value=response(status, {'error': 'unavailable'})):
        assert api_request.make_api_request(URL) is None


def test_as_json_false_keeps_raw_response_contract():
    result = response(204)
    with mock.patch.object(api_request.requests, 'request', return_value=result):
        assert api_request.make_api_request(URL, as_json=False, method='DELETE') is result
