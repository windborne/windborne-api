import jwt
import time
import requests
import re
import os
import base64

API_BASE_URL = "https://api.windbornesystems.com"
AUTH_DOCS_URL = "https://api.windbornesystems.com/technical-guides/authentication/auth/"


def is_valid_uuid_v4(client_id):
    return re.fullmatch(r"[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}", client_id) is not None


def is_valid_client_id_format(client_id):
    return re.fullmatch(r"[a-z0-9_]+", client_id) is not None


def get_api_credentials():
    client_id = os.getenv('WB_CLIENT_ID')
    api_key = os.getenv('WB_API_KEY')

    if api_key and api_key.startswith('wb_'):
        encoded_credentials = api_key[3:]
        encoded_credentials += '=' * (-len(encoded_credentials) % 4)
        try:
            decoded_credentials = base64.b64decode(encoded_credentials, validate=True).decode('utf-8')
        except Exception:
            pass
        else:
            if ':' in decoded_credentials:
                return None, api_key

    return client_id, api_key


def verify_api_credentials(client_id, api_key):
    if not client_id and not api_key:
        raise ValueError(
            "To access the WindBorne API, set the environment variable WB_API_KEY. "
            f"For instructions, refer to {AUTH_DOCS_URL}"
        )

    if not api_key:
        raise ValueError(
            "To access the WindBorne API, set the environment variable WB_API_KEY. "
            f"For instructions, refer to {AUTH_DOCS_URL}"
        )

    if not client_id and not api_key.startswith("wb_"):
        raise ValueError(
            "Your WB_API_KEY doesn't look valid. "
            "Check that you copied it exactly as provided and try again. "
            f"For instructions, refer to {AUTH_DOCS_URL}"
        )

    # Current API keys use Bearer authentication and do not require a client ID.
    if not client_id:
        return

    if len(client_id) in [32, 35] and len(api_key) not in [32, 35]:
        raise ValueError(
            "Your credentials don't look right. "
            "Check that WB_CLIENT_ID contains your client ID and WB_API_KEY contains your API key, then try again. "
            f"For instructions, refer to {AUTH_DOCS_URL}"
        )

    if not (is_valid_uuid_v4(client_id) or is_valid_client_id_format(client_id)):
        raise ValueError(
            "Your WB_CLIENT_ID doesn't look valid. "
            "Check that you copied it exactly as provided and try again. "
            f"For instructions, refer to {AUTH_DOCS_URL}"
        )

    # Validate legacy client ID + API key credentials.
    if api_key.startswith("wb_"):
        if len(api_key) != 35:
            raise ValueError(
                f"Your API key is misformatted. "
                "Check that you copied it exactly as provided and try again. "
                "For instructions, refer to {AUTH_DOCS_URL}"
            )
    elif len(api_key) != 32:  # For early tokens
        raise ValueError(
            f"Your API key is misformatted. "
            "Check that you copied it exactly as provided and try again. "
            "For instructions, refer to {AUTH_DOCS_URL}"
        )


VERIFIED_WB_CLIENT_ID = None
VERIFIED_WB_API_KEY = None
_CREDENTIALS_VERIFIED = False

def get_verified_api_credentials():
    global VERIFIED_WB_CLIENT_ID, VERIFIED_WB_API_KEY, _CREDENTIALS_VERIFIED

    if not _CREDENTIALS_VERIFIED:
        VERIFIED_WB_CLIENT_ID, VERIFIED_WB_API_KEY = get_api_credentials()
        verify_api_credentials(VERIFIED_WB_CLIENT_ID, VERIFIED_WB_API_KEY)
        _CREDENTIALS_VERIFIED = True

    return VERIFIED_WB_CLIENT_ID, VERIFIED_WB_API_KEY


def make_api_request(url, params=None, as_json=True, retry_counter=0, method='GET', json=None):
    """
    Make an authenticated request to the WindBorne API.

    Current API keys use Bearer authentication. Legacy client ID + API key
    credentials continue to use a short-lived JWT with HTTP Basic auth.

    :param url: The URL to make the request to
    :param params: The parameters to pass to the request
    :param as_json: Whether to return the response as JSON or as a requests.Response object
    :param retry_counter: The number of times the request has been retried
    :param method: HTTP method to use
    :param json: Optional JSON request body
    :return:
    """
    if retry_counter >= 5:
        raise ConnectionError("Max retries to API reached.")

    client_id, api_key = get_verified_api_credentials()

    request_args = {}
    if client_id:
        signed_token = jwt.encode({
            'client_id': client_id,
            'iat': int(time.time()),
        }, api_key, algorithm='HS256')
        request_args['auth'] = (client_id, signed_token)
    else:
        request_args['headers'] = {'Authorization': f'Bearer {api_key}'}

    if params:
        request_args['params'] = params
    if json is not None:
        request_args['json'] = json

    try:
        response = requests.request(method.upper(), url, **request_args)

        response.raise_for_status()

        if response.status_code == 204:
            return None
        elif as_json:
            return response.json()
        else:
            return response

    except requests.exceptions.HTTPError as http_err:
        if http_err.response.status_code in [401, 403]:
            print("--------------------------------------")
            print("We couldn't authenticate your request.")
            print("--------------------------------------")
            print("You likely don't have permission to access this resource.\n")
            print("For questions, email data@windbornesystems.com.")
        elif http_err.response.status_code in [404, 400]:
            print("-------------------------------------------------------")
            print("Our server couldn't find the information you requested.")
            print("-------------------------------------------------------")
            print(f"URL: {url}")
            print(f"Error: {http_err.response.status_code}")
            print("-------------------------------------------------------")
            if params:
                print("\nParameters provided:")
                for key, value in params.items():
                    print(f"  {key}: {value}")
            else:
                if 'missions/' in url:
                    mission_id = url.split('/missions/')[1].split('/')[0]
                    print(f"Mission ID provided: {mission_id}")
                    print(f"No mission found with id: {mission_id}")
            print("-------------------------------------------------------")
            print("Response text:")
            print(http_err.response.text)
            return None
        elif http_err.response.status_code == 502 and method.upper() in ['GET', 'HEAD']:
            print(f"Temporary connection failure; sleeping for {2**retry_counter}s before retrying")
            print(f"Underlying error: 502 Bad Gateway")
            time.sleep(2**retry_counter)
            return make_api_request(url, params, as_json, retry_counter + 1, method=method, json=json)
        else:
            # Re-raise the HTTP error instead of exiting
            raise http_err
    except requests.exceptions.ConnectionError as conn_err:
        if method.upper() not in ['GET', 'HEAD']:
            raise
        print(f"Temporary connection failure; sleeping for {2**retry_counter}s before retrying")
        print(f"Underlying error: \n\n{conn_err}")
        time.sleep(2**retry_counter)
        return make_api_request(url, params, as_json, retry_counter + 1, method=method, json=json)
    except requests.exceptions.Timeout as timeout_err:
        if method.upper() not in ['GET', 'HEAD']:
            raise
        print(f"Temporary connection failure; sleeping for {2**retry_counter}s before retrying")
        print(f"Underlying error: \n\n{timeout_err}")
        time.sleep(2**retry_counter)
        return make_api_request(url, params, as_json, retry_counter + 1, method=method, json=json)
    except requests.exceptions.RequestException as req_err:
        print(f"An error occurred\n\n{req_err}")
