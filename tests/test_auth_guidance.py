import pytest

from windborne.api_request import verify_api_credentials


@pytest.mark.parametrize(
    'client_id, api_key, error_prefix',
    [
        pytest.param(None, None, 'To access the WindBorne API', id='missing-both'),
        pytest.param(None, 'x' * 32, "Your WB_API_KEY doesn't look valid", id='missing-client-id'),
        pytest.param('test_client', None, 'To access the WindBorne API', id='missing-api-key'),
        pytest.param('x' * 32, 'short', "Your credentials don't look right", id='swapped-credentials'),
        pytest.param('invalid client!', 'x' * 32, "Your WB_CLIENT_ID doesn't look valid", id='invalid-client-id'),
        pytest.param('test_client', 'wb_short', 'Your API key is misformatted', id='invalid-prefixed-key'),
        pytest.param('test_client', 'short', 'Your API key is misformatted', id='invalid-legacy-key'),
    ],
)
def test_credential_errors_link_to_current_authentication_guide(client_id, api_key, error_prefix):
    with pytest.raises(ValueError) as error:
        verify_api_credentials(client_id, api_key)

    message = str(error.value)
    assert message.startswith(error_prefix)
    assert 'https://api.windbornesystems.com/technical-guides/authentication/auth/' in message
    assert '{AUTH_DOCS_URL}' not in message
