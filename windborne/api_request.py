import jwt
import time
import requests
import re
import os

def is_valid_uuid_v4(client_id):
    return re.fullmatch(r"[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}", client_id) is not None


def is_valid_client_id_format(client_id):
    return re.fullmatch(r"[a-z0-9_]+", client_id) is not None


def get_api_credentials():
    client_id = os.getenv('WB_CLIENT_ID')
    api_key = os.getenv('WB_API_KEY')
    
    return client_id, api_key


def verify_api_credentials(client_id, api_key):
    if not client_id and not api_key:
        print("To access the WindBorne API, set your Client ID and API key by setting the environment variables WB_CLIENT_ID and WB_API_KEY.")
        print("--------------------------------------")
        print("You may refer to https://windbornesystems.com/docs/api/cli#introduction\n"
              "for instructions on how to set your credentials as environment variables for CLI and Code usage\n\n"
              "and to https://windbornesystems.com/docs/api/pip_data#introduction\n"
              "for instruction on how to set your credentials for code usage.")
        print("--------------------------------------")
        print("To get an API key, email data@windbornesystems.com.")
        exit(80)

    if not client_id:
        print("To access the WindBorne API, you need to set your Client ID by setting the environment variable WB_CLIENT_ID.")
        print("--------------------------------------")
        print("You may refer to https://windbornesystems.com/docs/api/cli#introduction\n"
              "for instructions on how to set your credentials as environment variables for CLI and Code usage\n\n"
              "and to https://windbornesystems.com/docs/api/pip_data#introduction\n"
              "for instruction on how to set your credentials for code usage.")
        print("--------------------------------------")
        print("To get an API key, email data@windbornesystems.com.")
        exit(90)

    if not api_key:
        print("To access the WindBorne API, you need to set your API key by setting the environment variable WB_API_KEY.")
        print("--------------------------------------")
        print("You may refer to https://windbornesystems.com/docs/api/cli#introduction\n"
              "for instructions on how to set your credentials as environment variables for CLI and Code usage\n\n"
              "and to https://windbornesystems.com/docs/api/pip_data#introduction\n"
              "for instruction on how to set your credentials for code usage.")
        print("--------------------------------------")
        print("To get an API key, email data@windbornesystems.com.")
        exit(91)

    if len(client_id) in [32, 35] and len(api_key) not in [32, 35]:
        print("Your Client ID and API Key are likely swapped.")
        print("--------------------------------------")
        print("Swap them or modify them accordingly to get access to WindBorne API.")
        print("--------------------------------------")
        print("You may refer to https://windbornesystems.com/docs/api/cli#introduction\n"
              "for instructions on how to set your credentials as environment variables for CLI and Code usage\n\n"
              "and to https://windbornesystems.com/docs/api/pip_data#introduction\n"
              "for instruction on how to set your credentials for code usage.")
        print("--------------------------------------")
        print(f"Current Client ID: {client_id}")
        print(f"Current API Key: {api_key}")
        exit(95)

    # Validate WB_CLIENT_ID format
    if is_valid_uuid_v4(client_id):
        print("Personal API tokens are not yet supported.")
        print("--------------------------------------")
        print("You will need to get a globally-authorizing API key.")
        print("For questions, email data@windbornesystems.com.")
        exit(1)

    if not (is_valid_uuid_v4(client_id) or is_valid_client_id_format(client_id)):
        print("Your Client ID is misformatted.")
        print("--------------------------------------")
        print("It should either be a valid UUID v4 or consist of only lowercase letters, digits, and underscores ([a-z0-9_]).")
        print("--------------------------------------")
        print("You may refer to https://windbornesystems.com/docs/api/cli#introduction\n"
              "for instructions on how to set your credentials as environment variables for CLI and Code usage\n\n"
              "and to https://windbornesystems.com/docs/api/pip_data#introduction\n"
              "for instruction on how to set your credentials for code usage.")
        print("--------------------------------------")
        print(f"Current Client ID: {client_id}")
        exit(92)

    # Validate WB_API_KEY for both newer and older formats
    if api_key.startswith("wb_"):
        if len(api_key) != 35:
            print("Your API key is misformatted.")
            print("--------------------------------------")
            print("API keys starting with 'wb_' must be 35 characters long (including the 'wb_' prefix).")
            print("--------------------------------------")
            print("You may refer to https://windbornesystems.com/docs/api/cli#introduction\n"
                  "for instructions on how to set your credentials as environment variables for CLI and Code usage\n\n"
                  "and to https://windbornesystems.com/docs/api/pip_data#introduction\n"
                  "for instruction on how to set your credentials for code usage.")
            print("--------------------------------------")
            print(f"Current API key: {api_key}")
            exit(93)
    elif len(api_key) != 32:  # For early tokens
        print("Your API key is misformatted.")
        print("--------------------------------------")
        print("API keys created in 2023 or earlier must be exactly 32 characters long.")
        print("--------------------------------------")
        print("You may refer to https://windbornesystems.com/docs/api/cli#introduction\n"
              "for instructions on how to set your credentials as environment variables for CLI and Code usage\n\n"
              "and to https://windbornesystems.com/docs/api/pip_data#introduction\n"
              "for instruction on how to set your credentials for code usage.")
        print("--------------------------------------")
        print(f"Current API key: {api_key}")
        exit(94)


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
        print("Max retries to API reached. Exiting.")
        exit(1)

    client_id, api_key = get_verified_api_credentials()

    if is_valid_uuid_v4(client_id):
        token_id = client_id
        client_id = 'api_token'

        signed_token = jwt.encode({
            'client_id': client_id,
            'iat': int(time.time()),
            'token_id': token_id
        }, api_key, algorithm='HS256')
    else:
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
            print(f"Unrecoverable HTTP error occurred \n\n{http_err}")
            if params:
                print("\nParameters provided:")
                for key, value in params.items():
                    print(f"  {key}: {value}")
            exit(1)
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
