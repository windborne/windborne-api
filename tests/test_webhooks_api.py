import json
from unittest import mock

import pytest
import requests

from windborne import webhooks_api as webhooks


BASE = 'https://api.windbornesystems.com/webhooks/v1'


def test_list_preserves_pagination_envelope_and_false_filter():
    result = {'webhooks': [], 'page': 2, 'page_size': 10, 'total': 0}
    with mock.patch.object(webhooks, 'make_api_request', autospec=True, return_value=result) as request:
        assert webhooks.list_webhooks(page=2, page_size=10, active=False, url='example.com', subscription_type='events.available') is result
        request.assert_called_once_with(BASE, params={
            'page': 2, 'page_size': 10, 'active': 'false', 'url': 'example.com',
            'subscription_type': 'events.available',
        })


def test_list_omits_unset_filters_so_server_defaults_apply():
    with mock.patch.object(webhooks, 'make_api_request', autospec=True, return_value={}) as request:
        webhooks.list_webhooks()
        request.assert_called_once_with(BASE, params={})


def test_get_returns_complete_webhook():
    result = {'id': 42, 'subscriptions': [{'id': 81, 'subscription_type': 'events.available'}]}
    with mock.patch.object(webhooks, 'make_api_request', autospec=True, return_value=result) as request:
        assert webhooks.get_webhook('42') is result
        request.assert_called_once_with(BASE + '/42')


def test_create_retains_nested_options_and_one_time_secret_without_printing(capsys):
    subscriptions = {'initialization_time.available': {
        'filters': {'model': 'wm-6', 'initialization_time_hours': ['0:00', '12:00']},
        'response_options': {'type': 'interpolated_point_forecast', 'options': {
            'coordinates': '37.77,-122.42', 'include_distribution': False,
        }},
    }}
    result = {'id': 42, 'signing_secret': 'synthetic-secret', 'subscriptions': [{'id': 81}]}
    with mock.patch.object(webhooks, 'make_api_request', autospec=True, return_value=result) as request:
        assert webhooks.create_webhook('https://example.com/webhook', active=False, name=None, subscriptions=subscriptions) is result
        request.assert_called_once_with(BASE, method='POST', json={
            'url': 'https://example.com/webhook', 'active': False, 'name': None,
            'subscriptions': subscriptions,
        })
    assert capsys.readouterr().out == ''


def test_create_can_omit_every_optional_field():
    with mock.patch.object(webhooks, 'make_api_request', autospec=True) as request:
        webhooks.create_webhook('https://example.com/webhook')
        request.assert_called_once_with(BASE, method='POST', json={'url': 'https://example.com/webhook'})


def test_update_webhook_preserves_omitted_fields_and_explicit_null_false():
    with mock.patch.object(webhooks, 'make_api_request', autospec=True) as request:
        webhooks.update_webhook(42, active=False, note=None)
        request.assert_called_once_with(BASE + '/42', method='PATCH', json={'active': False, 'note': None})


def test_add_subscription_uses_patch_and_passes_full_configuration():
    options = {'type': 'event_context', 'options': {'coordinates': '35,-129;40.7,-74.0'}}
    with mock.patch.object(webhooks, 'make_api_request', autospec=True) as request:
        webhooks.add_webhook_subscription(42, 'events.available', note='Events', filters={'event_type': ['heatwave']}, response_options=options)
        request.assert_called_once_with(BASE + '/42/subscriptions', method='PATCH', json={
            'subscription_type': 'events.available', 'note': 'Events',
            'filters': {'event_type': ['heatwave']}, 'response_options': options,
        })


def test_subscription_update_distinguishes_omit_clear_and_replace():
    cases = [
        ({}, {}),
        ({'note': None}, {'note': None}),
        ({'filters': {}}, {'filters': {}}),
        ({'response_options': None}, {'response_options': None}),
        ({'filters': {'model': 'wm-6'}, 'response_options': {'type': 'gridded'}},
         {'filters': {'model': 'wm-6'}, 'response_options': {'type': 'gridded'}}),
    ]
    for kwargs, expected in cases:
        with mock.patch.object(webhooks, 'make_api_request', autospec=True) as request:
            webhooks.update_webhook_subscription(42, 81, **kwargs)
            request.assert_called_once_with(BASE + '/42/subscriptions/81', method='PATCH', json=expected)


@pytest.mark.parametrize('helper,args,path,method', [
    (webhooks.delete_webhook, (42,), '/42', 'DELETE'),
    (webhooks.delete_webhook_subscription, (42, 81), '/42/subscriptions/81', 'DELETE'),
    (webhooks.ping_webhook_subscription, (42, 81), '/42/subscriptions/81/ping', 'POST'),
])
def test_no_content_operations_return_none_without_output(helper, args, path, method, tmp_path, capsys):
    output = tmp_path / 'unused.json'
    with mock.patch.object(webhooks, 'make_api_request', autospec=True, return_value=None) as request:
        assert helper(*args, output_file=output, print_response=True) is None
        request.assert_called_once_with(BASE + path, method=method)
    assert not output.exists()
    assert capsys.readouterr().out == ''


def test_explicit_json_output_preserves_full_response(tmp_path, capsys):
    result = {'id': 42, 'subscriptions': [{'id': 81, 'filters': {}, 'response_options': None}]}
    output = tmp_path / 'nested' / 'webhook.json'
    with mock.patch.object(webhooks, 'make_api_request', autospec=True, return_value=result):
        assert webhooks.get_webhook(42, output_file=output, print_response=True) is result
    assert json.loads(output.read_text()) == result
    assert json.loads(capsys.readouterr().out) == result


@pytest.mark.parametrize('identifier', ['all', '../all', '42/subscriptions', '42?secret=value', 0, -1, True, 4.2, None])
def test_invalid_ids_cannot_reach_other_routes(identifier):
    with mock.patch.object(webhooks, 'make_api_request') as request:
        with pytest.raises(ValueError, match='webhook_id'):
            webhooks.get_webhook(identifier)
        with pytest.raises(ValueError, match='subscription_id'):
            webhooks.ping_webhook_subscription(42, identifier)
        request.assert_not_called()


def test_write_error_propagates_without_output_or_retry(tmp_path, capsys):
    error = requests.Timeout('Synthetic timeout')
    output = tmp_path / 'not-created.json'
    with mock.patch.object(webhooks, 'make_api_request', autospec=True, side_effect=error) as request:
        with pytest.raises(requests.Timeout) as caught:
            webhooks.create_webhook('https://example.com/webhook', output_file=output, print_response=True)
        assert caught.value is error
        request.assert_called_once()
    assert not output.exists()
    assert capsys.readouterr().out == ''


BODY_WRITES = [
    (webhooks.create_webhook, ('https://example.com/webhook',)),
    (webhooks.update_webhook, (42,)),
    (webhooks.add_webhook_subscription, (42, 'events.available')),
    (webhooks.update_webhook_subscription, (42, 81)),
]


@pytest.mark.parametrize('helper,args', BODY_WRITES)
@pytest.mark.parametrize('path_kind', ['directory', 'file_parent', 'unwritable'])
def test_output_path_errors_are_checked_before_mutation(helper, args, path_kind, tmp_path):
    if path_kind == 'directory':
        output = tmp_path
        expected = IsADirectoryError
    elif path_kind == 'file_parent':
        parent = tmp_path / 'file-not-directory'
        parent.write_text('preserve me')
        output = parent / 'response.json'
        expected = NotADirectoryError
    else:
        output = tmp_path / 'response.json'
        expected = PermissionError
    with mock.patch.object(webhooks, 'make_api_request') as request:
        with mock.patch.object(webhooks.os, 'access', return_value=(path_kind != 'unwritable')):
            with pytest.raises(expected):
                helper(*args, output_file=output)
        request.assert_not_called()


def test_preflight_neither_truncates_existing_output_nor_creates_directories(tmp_path):
    existing = tmp_path / 'existing.json'
    existing.write_text('preserve me')
    missing = tmp_path / 'not-yet-created' / 'response.json'

    def check_before_request(*args, **kwargs):
        assert existing.read_text() == 'preserve me'
        assert not missing.parent.exists()
        raise requests.Timeout('Synthetic request failure')

    with mock.patch.object(webhooks, 'make_api_request', side_effect=check_before_request):
        for output in [existing, missing]:
            with pytest.raises(requests.Timeout):
                webhooks.create_webhook('https://example.com/webhook', output_file=output)
    assert existing.read_text() == 'preserve me'
    assert not missing.parent.exists()


@pytest.mark.parametrize('helper,args', BODY_WRITES)
def test_output_io_error_retains_successful_response_without_repeating_write(helper, args, tmp_path, capsys):
    response = {'id': 42, 'signing_secret': 'synthetic-secret', 'subscriptions': [{'id': 81}]}
    with mock.patch.object(webhooks, 'make_api_request', autospec=True, return_value=response) as request:
        with mock.patch.object(webhooks.Path, 'open', side_effect=OSError('Synthetic disk failure')):
            with pytest.raises(webhooks.WebhookOutputError) as caught:
                helper(*args, output_file=tmp_path / 'response.json')
        request.assert_called_once()
    assert caught.value.response is response
    assert caught.value.response['signing_secret'] == 'synthetic-secret'
    assert 'synthetic-secret' not in str(caught.value)
    assert 'synthetic-secret' not in repr(caught.value)
    assert capsys.readouterr().out == ''


def test_stdout_failure_also_retains_successful_creation():
    response = {'id': 42, 'signing_secret': 'synthetic-secret'}
    with mock.patch.object(webhooks, 'make_api_request', autospec=True, return_value=response) as request:
        with mock.patch('builtins.print', side_effect=BrokenPipeError('Output closed')):
            with pytest.raises(webhooks.WebhookOutputError) as caught:
                webhooks.create_webhook('https://example.com/webhook', print_response=True)
        request.assert_called_once()
    assert caught.value.response is response
