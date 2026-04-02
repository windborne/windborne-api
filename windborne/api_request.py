import jwt
import time
import requests
import re
import os
import base64

API_BASE_URL = "https://api.windbornesystems.com"
AUTH_DOCS_URL = "https://api.windbornesystems.com/technical-guides/authentication/basic-auth/"


def is_valid_uuid_v4(client_id):
    return re.fullmatch(r"[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}", client_id) is not None


def is_valid_client_id_format(client_id):
    return re.fullmatch(r"[a-z0-9_]+", client_id) is not None


def parse_combined_api_key(api_key):
    if not api_key or not api_key.startswith("wb_"):
        return None

    encoded_credentials = api_key[3:]
    padded_encoded_credentials = encoded_credentials + ("=" * (-len(encoded_credentials) % 4))

    try:
        decoded_credentials = base64.b64decode(padded_encoded_credentials, validate=True).decode("utf-8")
    except Exception:
        return None

    if ":" not in decoded_credentials:
        return None

    client_id, password = decoded_credentials.split(":", 1)

    if not client_id or not password:
        return None

    return client_id, password


def get_api_credentials():
    client_id = os.getenv('WB_CLIENT_ID')
    api_key = os.getenv('WB_API_KEY')

    combined_credentials = parse_combined_api_key(api_key)
    if combined_credentials is not None:
        return combined_credentials

    return client_id, api_key


def verify_api_credentials(client_id, api_key):
    if not client_id and not api_key:
        raise ValueError(
            "To access the WindBorne API, set the environment variable WB_API_KEY. "
            f"For instructions, refer to {AUTH_DOCS_URL}"
        )

    if not client_id:
        raise ValueError(
            "Your WB_API_KEY doesn't look valid (or you meant to set WB_CLIENT_ID and WB_API_KEY separately, but didn't). "
            "Check that you copied it exactly as provided and try again. "
            f"For instructions, refer to {AUTH_DOCS_URL}"
        )

    if not api_key:
        raise ValueError(
            "To access the WindBorne API, set the environment variable WB_API_KEY. "
            f"For instructions, refer to {AUTH_DOCS_URL}"
        )

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

    # Validate WB_API_KEY for both newer and older formats
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

def get_verified_api_credentials():
    global VERIFIED_WB_CLIENT_ID, VERIFIED_WB_API_KEY

    if VERIFIED_WB_CLIENT_ID is None or VERIFIED_WB_API_KEY is None:
        VERIFIED_WB_CLIENT_ID, VERIFIED_WB_API_KEY = get_api_credentials()
        verify_api_credentials(VERIFIED_WB_CLIENT_ID, VERIFIED_WB_API_KEY)

    return VERIFIED_WB_CLIENT_ID, VERIFIED_WB_API_KEY


def make_api_request(url, params=None, as_json=True, retry_counter=0):
    """
    Make an authenticated request to the WindBorne API.

    This uses a JWT under the hood
    While basic auth is supported, this method reduces the odds of an improper configuration accidentally leaking the keys

    :param url: The URL to make the request to
    :param params: The parameters to pass to the request
    :param as_json: Whether to return the response as JSON or as a requests.Response object
    :param retry_counter: The number of times the request has been retried
    :return:
    """
    if retry_counter >= 5:
        raise ConnectionError("Max retries to API reached.")

    client_id, api_key = get_verified_api_credentials()

    signed_token = jwt.encode({
        'client_id': client_id,
        'iat': int(time.time()),
    }, api_key, algorithm='HS256')

    try:
        if params:
            response = requests.get(url, auth=(client_id, signed_token), params=params)
        else:
            response = requests.get(url, auth=(client_id, signed_token))

        response.raise_for_status()

        if as_json:
            return response.json()
        else:
            return response

    except requests.exceptions.HTTPError as http_err:
        if http_err.response.status_code == 403:
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
        elif http_err.response.status_code == 502:
            print(f"Temporary connection failure; sleeping for {2**retry_counter}s before retrying")
            print(f"Underlying error: 502 Bad Gateway")
            time.sleep(2**retry_counter)
            return make_api_request(url, params, as_json, retry_counter + 1)
        else:
            # Re-raise the HTTP error instead of exiting
            raise http_err
    except requests.exceptions.ConnectionError as conn_err:
        print(f"Temporary connection failure; sleeping for {2**retry_counter}s before retrying")
        print(f"Underlying error: \n\n{conn_err}")
        time.sleep(2**retry_counter)
        return make_api_request(url, params, as_json, retry_counter + 1)
    except requests.exceptions.Timeout as timeout_err:
        print(f"Temporary connection failure; sleeping for {2**retry_counter}s before retrying")
        print(f"Underlying error: \n\n{timeout_err}")
        time.sleep(2**retry_counter)
        return make_api_request(url, params, as_json, retry_counter + 1)
    except requests.exceptions.RequestException as req_err:
        print(f"An error occurred\n\n{req_err}")
