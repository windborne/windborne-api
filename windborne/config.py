import os
import requests
import jwt
import time

API_BASE_URL = "https://sensor-data.windbornesystems.com/api/v1"

# If not set make_api_request will print an error message
CLIENT_ID = os.getenv("WB_CLIENT_ID")
API_KEY = os.getenv("WB_API_KEY")

# Authenticate requests using a JWT | no reveal of underlying key
def make_api_request(url, params=None):
    signed_token = jwt.encode({
        'client_id': CLIENT_ID,
        'iat': int(time.time()),
    }, API_KEY, algorithm='HS256')

    try:
        if params:
            response = requests.get(url, auth=(CLIENT_ID, signed_token), params=params)
        else:
            response = requests.get(url, auth=(CLIENT_ID, signed_token))

        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        if http_err.response.status_code == 403:
            print("--------------------------------------")
            print("We couldn't authenticate your request.")
            print("--------------------------------------")
            print("Please make sure you have properly set your WB_CLIENT_ID and WB_API_KEY.")
            print("You can verify this by running echo $WB_CLIENT_ID and echo $WB_API_KEY in your terminal.")
            print("To get an API key, email data@windbornesystems.com.")
        elif http_err.response.status_code == 404:
            print("-------------------------------------------------------")
            print("Our server couldn't find the information you requested.")
            print("-------------------------------------------------------")
            print(f"URL: {url}")
            print("-------------------------------------------------------")
            if params:
                print("Parameters provided:")
                for key, value in params.items():
                    print(f"  {key}: {value}")
            else:
                if 'missions/' in url:
                    mission_id = url.split('/missions/')[1].split('/')[0]
                    print(f"Mission ID provided: {mission_id}")
                    print(f"We couldn't find a mission with id: {mission_id}")
        elif http_err.response.status_code == 502:
            retries = 1
            while response.status_code == 502 and retries < 5:
                print("502 Bad Gateway, sleeping and retrying")
                time.sleep(2**retries)
                response = requests.get(url, auth=(CLIENT_ID, signed_token))
                retries += 1
        else:
            print(f"HTTP error occurred: {http_err}")
    except requests.exceptions.ConnectionError as conn_err:
        print(f"Connection error occurred: {conn_err}")
    except requests.exceptions.Timeout as timeout_err:
        print(f"Timeout error occurred: {timeout_err}")
    except requests.exceptions.RequestException as req_err:
        print(f"An error occurred: {req_err}")