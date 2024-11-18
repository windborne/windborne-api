import requests
import jwt
import time
from datetime import datetime
from .config import API_BASE_URL, CLIENT_ID, API_KEY
import json
import csv

def to_unix_timestamp(date_string):
    """
    Convert a date string in 'YYYY-MM-DD HH:MM:SS' or 'YYYY-MM-DD_HH:MM' format to a Unix timestamp.
    """
    if date_string is None:
        return None
    if isinstance(date_string, int):
        return date_string  # If it's already an integer, return as is
    if isinstance(date_string, str):
        formats = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d_%H:%M"]
        for fmt in formats:
            try:
                dt = datetime.strptime(date_string, fmt)
                return int(dt.timestamp())
            except ValueError:
                continue
        raise ValueError("Invalid date format. Use 'YYYY-MM-DD HH:MM:SS' or 'YYYY-MM-DD_HH:MM'.")

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
            print("We coudln't authenticate your request.")
            print("--------------------------------------")
            print("Please make sure you have properly set your WB_CLIENT_ID and WB_API_KEY.")
            print("You can verify this by running echo $WB_CLIENT_ID and echo $WB_API_KEY in your ternimal.")
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
                print("No parameters were provided for this request.")
                if 'missions/' in url and '/prediction.json' in url:
                    mission_id = url.split('/missions/')[1].split('/')[0]
                    print(f"Mission ID provided: {mission_id}")
            print("-------------------------------------------------------")
            print("Please make sure the parameters of your request are valid.")
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

def save_to_json(filename, data):
    if not data:
        print("No data to save to JSON.")
        return
    
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)

def save_to_csv(filename, data):
    if not data:
        print("No data to save to CSV.")
        return

    # If data is a list of dictionaries, write each dictionary as a row
    if isinstance(data, list) and all(isinstance(item, dict) for item in data):
        headers = data[0].keys() if data else []
    # If data is a dictionary, determine if it contains a list of dictionaries or is a flat dictionary
    elif isinstance(data, dict):
        # If the dictionary contains a list of dictionaries, use the keys of the first dictionary in the list as headers
        for key, value in data.items():
            if isinstance(value, list) and all(isinstance(item, dict) for item in value):
                headers = value[0].keys() if value else []
                data = value
                break
        else:
            # If no lists of dictionaries are found, use the keys of the dictionary as headers
            headers = data.keys()
            data = [data]
    else:
        print("Unsupported data format for CSV.")
        return

    # Write data to CSV
    with open(filename, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()
        for row in data:
            writer.writerow(row)


def get_observations(since=None, min_time=None, max_time=None, include_ids=None, include_mission_name=None, include_updated_at=None, mission_id=None, min_latitude=None, max_latitude=None, min_longitude=None, max_longitude=None, save_to_file=None):
    url = f"{API_BASE_URL}/observations.json"
    
    # Convert date strings to Unix timestamps
    params = {
        "since": to_unix_timestamp(since),
        "min_time": to_unix_timestamp(min_time),
        "max_time": to_unix_timestamp(max_time),
        "mission_id": mission_id,
        "min_latitude": min_latitude,
        "max_latitude": max_latitude,
        "min_longitude": min_longitude,
        "max_longitude": max_longitude,
    }

    if include_ids:
        params["include_ids"] = True
    if include_mission_name:
        params["include_mission_name"] = True
    if include_updated_at:
        params["include_updated_at"] = True
    
    # Remove any keys where the value is None to avoid sending unnecessary parameters
    params = {k: v for k, v in params.items() if v is not None}
    
    response = make_api_request(url, params=params)

    if save_to_file and response:
        if save_to_file.endswith('.json'):
            save_to_json(save_to_file, response)
        elif save_to_file.endswith('.csv'):
            save_to_csv(save_to_file, response.get('missions', []))
    
    return response

def get_super_observations(since=None, min_time=None, max_time=None, include_ids=None, include_mission_name=None, include_updated_at=None, mission_id=None, save_to_file=None):
    url = f"{API_BASE_URL}/super_observations.json"
    
    params = {
        "since": to_unix_timestamp(since),
        "min_time": to_unix_timestamp(min_time),
        "max_time": to_unix_timestamp(max_time),
        "include_ids": include_ids,
        "include_mission_name": include_mission_name,
        "include_updated_at": include_updated_at,
        "mission_id": mission_id,
    }
    
    if include_ids:
        params["include_ids"] = True
    if include_mission_name:
        params["include_mission_name"] = True
    if include_updated_at:
        params["include_updated_at"] = True
    
    params = {k: v for k, v in params.items() if v is not None}
    
    response = make_api_request(url, params=params)

    if save_to_file and response:
        save_to_json(save_to_file, response)
    
    return response

def get_flying_missions(save_to_file=None):
    url = f"{API_BASE_URL}/missions.json"
    response = make_api_request(url)
    
    if save_to_file and response:
        if save_to_file.endswith('.json'):
            save_to_json(save_to_file, response)
        elif save_to_file.endswith('.csv'):
            save_to_csv(save_to_file, response)
    
    return response

def get_mission_launch_site(mission_id, save_to_file=None):
    if not mission_id:
        raise ValueError("Mission ID is required to retrieve the launch site.")

    url = f"{API_BASE_URL}/missions/{mission_id}/launch_site.json"
    
    response = make_api_request(url)
    
    if save_to_file and response:
        if save_to_file.endswith('.json'):
            save_to_json(save_to_file, response)
        elif save_to_file.endswith('.csv'):
            save_to_csv(save_to_file, response)

    
    return response

def get_predicted_path(mission_id, save_to_file=None):
    if not mission_id:
        raise ValueError("Mission ID is required to retrieve the launch site.")
    url = f"{API_BASE_URL}/missions/{mission_id}/prediction.json"
    response = make_api_request(url)
    
    if save_to_file and response:
        if save_to_file.endswith('.json'):
            save_to_json(save_to_file, response)
        elif save_to_file.endswith('.csv'):
            save_to_csv(save_to_file, response)
    
    return response