"""Manage customer webhooks, subscriptions and saved weather triggers.

Write requests are sent once. If a request fails, inspect the webhook state before
retrying: the server may already have applied it. Webhook creation returns a one-time
``signing_secret``; retain that value securely to verify future deliveries.
If saving or printing a successful response fails, ``WebhookOutputError.response``
retains it, including a newly created signing secret. Recover that response rather
than repeating the API write.
"""

import json
import os
from pathlib import Path
import re
import tempfile

from .api_request import API_BASE_URL, make_api_request


WEBHOOKS_API_BASE_URL = f'{API_BASE_URL}/webhooks/v1'
TRIGGERS_API_BASE_URL = f'{WEBHOOKS_API_BASE_URL}/triggers'
UNSET = object()


class WebhookArgumentError(ValueError):
    """An invalid webhook or trigger argument prevented the request."""


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
    if '\x00' in str(path):
        raise ValueError('output_file must not contain a NUL byte')
    if path.is_symlink():
        raise OSError('output_file must not be a symbolic link')
    if path.exists():
        if path.is_dir():
            raise IsADirectoryError('output_file must be a file, not a directory')
        if not path.is_file():
            raise OSError('output_file must be a regular file')
        if not os.access(path, os.W_OK):
            raise PermissionError('output_file is not writable')
    parent = path.parent
    while not parent.exists():
        parent = parent.parent
    if not parent.is_dir():
        raise NotADirectoryError('An output_file parent is not a directory')
    if not os.access(parent, os.W_OK | os.X_OK):
        raise PermissionError('The output_file parent is not writable')


def _identifier(value, name):
    if not re.fullmatch(r'[0-9]+', str(value)) or int(value) <= 0:
        raise WebhookArgumentError(f'{name} must be a positive integer')
    return str(value)


def _body(**fields):
    # None is a meaningful JSON null, especially for clearing response_options.
    return {key: value for key, value in fields.items() if value is not UNSET}


def _list_params(page, page_size, active, **filters):
    if isinstance(active, bool):
        active = str(active).lower()
    params = dict(page=page, page_size=page_size, active=active, **filters)
    return {key: value for key, value in params.items() if value is not None}


def _save_response(response, output_file):
    """Write privately, then replace the destination with the complete result."""
    path = Path(output_file)
    _preflight_output(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = None
    temporary_path = None
    try:
        # mkstemp creates with 0600, so secrets are never briefly world-readable.
        descriptor, temporary_path = tempfile.mkstemp(
            prefix='.windborne-webhook-', suffix='.json', dir=str(path.parent),
        )
        if hasattr(os, 'fchmod'):
            os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, 'w', encoding='utf-8') as output:
            descriptor = None  # The stream now owns and closes the descriptor.
            json.dump(response, output, indent=2)
            output.write('\n')
        # Check again in case the destination changed while writing the response.
        _preflight_output(path)
        os.replace(temporary_path, str(path))
        temporary_path = None
    finally:
        if descriptor is not None:
            try:
                os.close(descriptor)
            except OSError:
                pass  # Preserve the original output failure for recovery.
        if temporary_path is not None:
            try:
                os.unlink(temporary_path)
            except OSError:
                pass  # Cleanup must not hide the original output failure.


def _result(response, output_file, print_response):
    if response is None:
        return None
    try:
        if output_file is not None:
            _save_response(response, output_file)
        if print_response:
            # A pipe can accept the buffered print and fail only at shutdown.
            # Flush while the response is still available for recovery.
            print(json.dumps(response, indent=2), flush=True)
    except (OSError, ValueError, TypeError) as error:
        raise WebhookOutputError(response) from error
    return response


def list_webhooks(*, page=None, page_size=None, active=None, url=None,
                  subscription_type=None, output_file=None, print_response=False):
    """List your webhooks, optionally filtering by state, URL, or subscription.

    Pagination is one-based; the server defaults to page 1 with 20 results
    (maximum 100). Returns the full ``webhooks/page/page_size/total`` envelope.
    """
    params = _list_params(page, page_size, active, url=url, subscription_type=subscription_type)
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


def list_triggers(*, page=None, page_size=None, active=None, output_file=None, print_response=False):
    """List your saved weather triggers. Pages start at 0 and default to 20 items (maximum 100).

    Returns the full triggers, page, page_size and total envelope.
    """
    response = make_api_request(TRIGGERS_API_BASE_URL, params=_list_params(page, page_size, active),
                                raise_errors=True)
    return _result(response, output_file, print_response)


def get_trigger(trigger_id, *, output_file=None, print_response=False):
    """Get a saved weather trigger by its numeric ID."""
    trigger_id = _identifier(trigger_id, 'trigger_id')
    response = make_api_request(f'{TRIGGERS_API_BASE_URL}/{trigger_id}', raise_errors=True)
    return _result(response, output_file, print_response)


def create_trigger(*, model, trigger, locations, forecast_window, name=UNSET, note=UNSET,
                   active=UNSET, webhook=UNSET, webhook_id=UNSET, output_file=None, print_response=False):
    """Save a weather trigger and optionally subscribe a webhook in the same request.

    Pass webhook={"url": "https://example.com/webhook"} for a new receiver or
    webhook_id for an existing receiver owned by this API key. Either form returns
    webhook_id. Inline creation also returns the new webhook's one-time signing_secret.
    Omit both to save the rule for later subscription.
    """
    if webhook is not UNSET and webhook_id is not UNSET:
        raise WebhookArgumentError('Send either webhook or webhook_id')
    if webhook_id is not UNSET and (type(webhook_id) is not int or webhook_id <= 0):
        raise WebhookArgumentError('webhook_id must be a positive integer')
    _preflight_output(output_file)
    body = _body(model=model, trigger=trigger, locations=locations, forecast_window=forecast_window,
                 name=name, note=note, active=active, webhook=webhook, webhook_id=webhook_id)
    response = make_api_request(TRIGGERS_API_BASE_URL, method='POST', json=body)
    return _result(response, output_file, print_response)


def update_trigger(trigger_id, *, name=UNSET, note=UNSET, active=UNSET, model=UNSET,
                   trigger=UNSET, forecast_window=UNSET, locations=UNSET, add_locations=UNSET,
                   remove_location_ids=UNSET, output_file=None, print_response=False):
    """Update the supplied fields and return the saved trigger. Use None to clear name or note.

    Pass locations to replace every location, or pass add_locations and/or
    remove_location_ids to apply incremental changes in a single request.
    """
    trigger_id = _identifier(trigger_id, 'trigger_id')
    if locations is not UNSET and (add_locations is not UNSET or remove_location_ids is not UNSET):
        raise WebhookArgumentError('locations cannot be combined with add_locations or remove_location_ids')
    _preflight_output(output_file)
    body = _body(name=name, note=note, active=active, model=model, trigger=trigger,
                 forecast_window=forecast_window, locations=locations, add_locations=add_locations,
                 remove_location_ids=remove_location_ids)
    response = make_api_request(f'{TRIGGERS_API_BASE_URL}/{trigger_id}', method='PATCH', json=body)
    return _result(response, output_file, print_response)


def delete_trigger(trigger_id, *, output_file=None, print_response=False):
    """Delete a saved weather trigger. Returns None on successful 204."""
    trigger_id = _identifier(trigger_id, 'trigger_id')
    response = make_api_request(f'{TRIGGERS_API_BASE_URL}/{trigger_id}', method='DELETE')
    return _result(response, output_file, print_response)
