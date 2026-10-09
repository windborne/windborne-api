"""Manage customer webhook endpoints and subscriptions through the public API.

Write requests are sent once. If a request fails, inspect the webhook state before
retrying: the server may already have applied it. Creation returns a one-time
``signing_secret``; retain that value securely to verify future deliveries.
If saving or printing a successful response fails, ``WebhookOutputError.response``
retains it, including a newly created signing secret. Recover that response rather
than repeating the API write.
"""

import json
import os
from pathlib import Path
import re

from .api_request import API_BASE_URL, make_api_request


WEBHOOKS_API_BASE_URL = f'{API_BASE_URL}/webhooks/v1'
UNSET = object()


class WebhookOutputError(OSError):
    """Output failed after API success; ``response`` retains the full result."""

    def __init__(self, response):
        super().__init__(
            'The API request succeeded, but writing its response failed. '
            'Recover the successful result from this exception\'s response attribute; '
            'do not repeat the API write.'
        )
        self.response = response


def _preflight_output(output_file):
    """Check predictable path failures without creating or truncating anything."""
    if output_file is None:
        return
    path = Path(output_file)
    if path.exists():
        if path.is_dir():
            raise IsADirectoryError('output_file must be a file, not a directory')
        if not path.is_file():
            raise OSError('output_file must be a regular file')
        if not os.access(path, os.W_OK):
            raise PermissionError('output_file is not writable')
        return
    parent = path.parent
    while not parent.exists():
        parent = parent.parent
    if not parent.is_dir():
        raise NotADirectoryError('An output_file parent is not a directory')
    if not os.access(parent, os.W_OK | os.X_OK):
        raise PermissionError('The output_file parent is not writable')


def _identifier(value, name):
    if not re.fullmatch(r'[0-9]+', str(value)) or int(value) <= 0:
        raise ValueError(f'{name} must be a positive integer')
    return str(value)


def _body(**fields):
    # None is a meaningful JSON null, especially for clearing response_options.
    return {key: value for key, value in fields.items() if value is not UNSET}


def _result(response, output_file, print_response):
    if response is None:
        return None
    try:
        if output_file is not None:
            path = Path(output_file)
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open('w', encoding='utf-8') as output:
                json.dump(response, output, indent=2)
                output.write('\n')
        if print_response:
            print(json.dumps(response, indent=2))
    except OSError as error:
        raise WebhookOutputError(response) from error
    return response


def list_webhooks(*, page=None, page_size=None, active=None, url=None,
                  subscription_type=None, output_file=None, print_response=False):
    """List your webhooks, optionally filtering by state, URL, or subscription.

    Pagination is one-based; the server defaults to page 1 with 20 results
    (maximum 100). Returns the full ``webhooks/page/page_size/total`` envelope.
    """
    params = {key: value for key, value in {
        'page': page, 'page_size': page_size, 'active': active,
        'url': url, 'subscription_type': subscription_type,
    }.items() if value is not None}
    if isinstance(active, bool):
        params['active'] = str(active).lower()
    response = make_api_request(WEBHOOKS_API_BASE_URL, params=params)
    return _result(response, output_file, print_response)


def get_webhook(webhook_id, *, output_file=None, print_response=False):
    """Get one of your webhook configurations and its subscriptions."""
    webhook_id = _identifier(webhook_id, 'webhook_id')
    response = make_api_request(f'{WEBHOOKS_API_BASE_URL}/{webhook_id}')
    return _result(response, output_file, print_response)


def create_webhook(url, *, name=UNSET, note=UNSET, active=UNSET,
                   subscriptions=UNSET, output_file=None, print_response=False):
    """Register a publicly reachable HTTPS destination and optional subscriptions.

    ``subscriptions`` is a map of subscription type to its note, filters, and
    response_options; nested options are sent unchanged. Returns the created
    configuration, including its one-time signing_secret. Output is silent unless
    explicitly requested with output_file or print_response.
    Predictable output-path errors are checked before creation; later output
    failures raise WebhookOutputError with the successful response attached.
    """
    _preflight_output(output_file)
    body = _body(url=url, name=name, note=note, active=active, subscriptions=subscriptions)
    response = make_api_request(WEBHOOKS_API_BASE_URL, method='POST', json=body)
    return _result(response, output_file, print_response)


def update_webhook(webhook_id, *, url=UNSET, name=UNSET, note=UNSET,
                   active=UNSET, output_file=None, print_response=False):
    """Partially update a webhook; omitted fields retain their existing values.

    Use active=False to pause delivery. Subscriptions are updated through the
    separate subscription helpers. Returns the full updated configuration.
    """
    webhook_id = _identifier(webhook_id, 'webhook_id')
    _preflight_output(output_file)
    response = make_api_request(
        f'{WEBHOOKS_API_BASE_URL}/{webhook_id}', method='PATCH',
        json=_body(url=url, name=name, note=note, active=active),
    )
    return _result(response, output_file, print_response)


def delete_webhook(webhook_id, *, output_file=None, print_response=False):
    """Delete a webhook and its subscriptions. Returns None on successful 204."""
    webhook_id = _identifier(webhook_id, 'webhook_id')
    response = make_api_request(f'{WEBHOOKS_API_BASE_URL}/{webhook_id}', method='DELETE')
    return _result(response, output_file, print_response)


def add_webhook_subscription(webhook_id, subscription_type, *, note=UNSET,
                             filters=UNSET, response_options=UNSET,
                             output_file=None, print_response=False):
    """Add a subscription of a type not already present on this webhook.

    Filters and response_options are passed through unchanged. Returns the full
    updated webhook object, including its new subscription identifier.
    """
    webhook_id = _identifier(webhook_id, 'webhook_id')
    _preflight_output(output_file)
    response = make_api_request(
        f'{WEBHOOKS_API_BASE_URL}/{webhook_id}/subscriptions', method='PATCH',
        json=_body(subscription_type=subscription_type, note=note,
                   filters=filters, response_options=response_options),
    )
    return _result(response, output_file, print_response)


def update_webhook_subscription(webhook_id, subscription_id, *, note=UNSET,
                                filters=UNSET, response_options=UNSET,
                                output_file=None, print_response=False):
    """Update a subscription and return the full updated webhook object.

    Omit filters or response_options to preserve them. filters={} clears filters;
    any other filters object replaces them completely. response_options=None
    removes response enrichment; an object replaces its configuration.
    """
    webhook_id = _identifier(webhook_id, 'webhook_id')
    subscription_id = _identifier(subscription_id, 'subscription_id')
    _preflight_output(output_file)
    response = make_api_request(
        f'{WEBHOOKS_API_BASE_URL}/{webhook_id}/subscriptions/{subscription_id}',
        method='PATCH', json=_body(note=note, filters=filters, response_options=response_options),
    )
    return _result(response, output_file, print_response)


def delete_webhook_subscription(webhook_id, subscription_id, *, output_file=None,
                                print_response=False):
    """Remove one subscription. Returns None on successful 204."""
    webhook_id = _identifier(webhook_id, 'webhook_id')
    subscription_id = _identifier(subscription_id, 'subscription_id')
    response = make_api_request(
        f'{WEBHOOKS_API_BASE_URL}/{webhook_id}/subscriptions/{subscription_id}', method='DELETE',
    )
    return _result(response, output_file, print_response)


def ping_webhook_subscription(webhook_id, subscription_id, *, output_file=None,
                              print_response=False):
    """Request one immediate test delivery. Returns None on successful 204.

    This sends a real HTTP callback to the configured destination. Neither this
    SDK request nor the server's test delivery is automatically retried.
    """
    webhook_id = _identifier(webhook_id, 'webhook_id')
    subscription_id = _identifier(subscription_id, 'subscription_id')
    response = make_api_request(
        f'{WEBHOOKS_API_BASE_URL}/{webhook_id}/subscriptions/{subscription_id}/ping', method='POST',
    )
    return _result(response, output_file, print_response)
