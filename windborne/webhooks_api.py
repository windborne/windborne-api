from .api_request import API_BASE_URL, make_api_request


WEBHOOKS_API_BASE_URL = f"{API_BASE_URL}/webhooks/v1"
_UNSET = object()


def _provided_fields(**values):
    return {key: value for key, value in values.items() if value is not _UNSET}


def create_webhook(url, name=None, note=None, subscriptions=None, active=None):
    """Create a webhook endpoint and return its one-time signing secret."""
    body = {'url': url}
    if name is not None:
        body['name'] = name
    if note is not None:
        body['note'] = note
    if subscriptions is not None:
        body['subscriptions'] = subscriptions
    if active is not None:
        body['active'] = active
    return make_api_request(WEBHOOKS_API_BASE_URL, method='POST', json=body)


def list_webhooks(page=None, page_size=None, active=None, subscription_type=None, url=None):
    """List webhook endpoints visible to the current API key."""
    params = {}
    if page is not None:
        params['page'] = page
    if page_size is not None:
        params['page_size'] = page_size
    if active is not None:
        params['active'] = active
    if subscription_type is not None:
        params['subscription_type'] = subscription_type
    if url is not None:
        params['url'] = url
    return make_api_request(WEBHOOKS_API_BASE_URL, params=params)


def get_webhook(webhook_id):
    """Get a webhook endpoint by ID."""
    return make_api_request(f"{WEBHOOKS_API_BASE_URL}/{webhook_id}")


def update_webhook(webhook_id, url=_UNSET, name=_UNSET, note=_UNSET, active=_UNSET):
    """Update the supplied fields on a webhook endpoint."""
    body = _provided_fields(url=url, name=name, note=note, active=active)
    return make_api_request(
        f"{WEBHOOKS_API_BASE_URL}/{webhook_id}",
        method='PATCH',
        json=body,
    )


def delete_webhook(webhook_id):
    """Delete a webhook endpoint."""
    return make_api_request(f"{WEBHOOKS_API_BASE_URL}/{webhook_id}", method='DELETE')


def add_webhook_subscription(webhook_id, subscription_type, note=None, filters=None, response_options=None):
    """Add a subscription to an existing webhook endpoint."""
    body = {'subscription_type': subscription_type}
    if note is not None:
        body['note'] = note
    if filters is not None:
        body['filters'] = filters
    if response_options is not None:
        body['response_options'] = response_options
    return make_api_request(
        f"{WEBHOOKS_API_BASE_URL}/{webhook_id}/subscriptions",
        method='PATCH',
        json=body,
    )


def update_webhook_subscription(webhook_id, subscription_id, note=_UNSET, filters=_UNSET, response_options=_UNSET):
    """Update a webhook subscription; explicit null values clear nullable fields."""
    body = _provided_fields(note=note, filters=filters, response_options=response_options)
    return make_api_request(
        f"{WEBHOOKS_API_BASE_URL}/{webhook_id}/subscriptions/{subscription_id}",
        method='PATCH',
        json=body,
    )


def delete_webhook_subscription(webhook_id, subscription_id):
    """Delete one subscription from a webhook endpoint."""
    return make_api_request(
        f"{WEBHOOKS_API_BASE_URL}/{webhook_id}/subscriptions/{subscription_id}",
        method='DELETE',
    )


def ping_webhook_subscription(webhook_id, subscription_id):
    """Send a test delivery for a webhook subscription."""
    return make_api_request(
        f"{WEBHOOKS_API_BASE_URL}/{webhook_id}/subscriptions/{subscription_id}/ping",
        method='POST',
    )
