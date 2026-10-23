import pytest
import requests


@pytest.fixture(autouse=True)
def block_network_requests(monkeypatch):
    """Contract tests must use fixtures, never credentials or live API data."""
    def unexpected_request(*args, **kwargs):
        raise AssertionError('Unexpected HTTP request: mock the API response in this test')

    monkeypatch.setattr(requests.Session, 'request', unexpected_request)
