from .config import API_BASE_URL, make_api_request
from .utils import to_unix_timestamp, save_response_to_file

import os
import time
from datetime import datetime, timezone
import csv


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

    save_response_to_file(save_to_file, response, csv_data_key='observations')
    
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

    save_response_to_file(save_to_file, response, csv_data_key='observations')
    
    return response

def poll_observations(start_time, end_time=None, interval=60, save_to_file=None, csv_data_key="observations"):
    """
    Fetches observations between a start time and an optional end time and saves to a CSV file.

    Args:
        start_time (str): The start time in the format 'YYYY-MM-DD_HH:MM'.
        end_time (str): The optional end time in the format 'YYYY-MM-DD_HH:MM'. Defaults to None.
        interval (int): The interval in seconds between polls if pagination is required (default: 60).
        save_to_file (str): The file path where observations will be saved. Defaults to generated filename.
        csv_data_key (str): Key to extract data for CSV saving (default: "observations").
    """
    if not start_time:
        print("Please provide a start time in the format 'YYYY-MM-DD_HH:MM'.")
        return

    # Convert start_time and end_time to timestamps
    start_timestamp = to_unix_timestamp(start_time)
    if end_time:
        end_timestamp = to_unix_timestamp(end_time),
        end_label = end_time
    else:
        end_timestamp = None
        end_label = 'latest'

    # Generate default filename if not provided
    if save_to_file is None:
        save_to_file = f"observations_{start_time}_{end_label}.csv"

    # Check if the file already exists
    file_exists = os.path.exists(save_to_file)
    if file_exists:
        print(f"File '{save_to_file}' already exists. Delete it or choose a different filename.")
    else:
        print(f"Creating new file: '{save_to_file}'")

    # Rearranged headers for CSV
    rearranged_headers = [
        "timestamp", "time", "latitude", "longitude", "altitude", "humidity",
        "mission_name", "pressure", "specific_humidity", "speed_u", "speed_v", "temperature"
    ]

    # Initialize the polling loop
    has_next_page = True

    while has_next_page and (end_timestamp is None or start_timestamp <= end_timestamp):
        # Fetch a page of observations
        observations_page = get_observations(since=start_timestamp, include_mission_name=True)
        print(f"Fetched {len(observations_page.get(csv_data_key, []))} observations")

        # Process and save data to CSV
        data = observations_page.get(csv_data_key, [])
        processed_data = []
        for item in data:
            # Compute the time field from timestamp
            computed_time = datetime.fromtimestamp(item['timestamp'], tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
            item['time'] = computed_time
            processed_data.append({header: item.get(header, '') for header in rearranged_headers})

        # Write data to CSV
        write_mode = 'a' if file_exists else 'w'
        with open(save_to_file, mode=write_mode, newline='') as file:
            writer = csv.DictWriter(file, fieldnames=rearranged_headers)
            # Write headers only if the file is being created
            if not file_exists:
                writer.writeheader()
                file_exists = True  # Ensure headers are only written once
            writer.writerows(processed_data)

        # Check for next page
        has_next_page = observations_page.get('has_next_page', False)
        start_timestamp = observations_page.get('next_since', start_timestamp)

        if not has_next_page:
            print("---------------------------------------------------")
            print("Your latest observations don't have a next page.")
            print("---------------------------------------------------")
            print(f"Sleeping for {interval} seconds")
            time.sleep(interval)

    print(f"Observations saved to {save_to_file}")

def get_flying_missions(save_to_file=None):
    url = f"{API_BASE_URL}/missions.json"
    response = make_api_request(url)

    save_response_to_file(save_to_file, response, csv_data_key='missions')
    
    return response

def get_mission_launch_site(mission_id=None, save_to_file=None):
    if not mission_id:
        print("To get a mission's launch site you must provide the mission's ID.")
        return
    url = f"{API_BASE_URL}/missions/{mission_id}/launch_site.json"
    
    response = make_api_request(url)

    save_response_to_file(save_to_file, response, csv_data_key='launch_site')
    
    return response

def get_predicted_path(mission_id=None, save_to_file=None):
    if not mission_id:
        print("To get the predicted flight path for a given mission you must provide a mission ID.")
        return

    # Check if provided mission ID belong to a flying mission
    flying_missions_response = get_flying_missions()
    flying_missions = flying_missions_response.get("missions", [])

    if mission_id not in [mission.get("id") for mission in flying_missions]:
        print(f"Provided mission ID '{mission_id}' does not belong to a mission that is currently flying.")

        # Display currently flying missions
        if flying_missions:
            print("\nCurrently flying missions:\n")

            # Define headers and data
            headers = ["Index", "Mission ID", "Mission Name"]
            rows = [
                [str(i), mission.get("id", "N/A"), mission.get("name", "Unnamed Mission")]
                for i, mission in enumerate(flying_missions, start=1)
            ]

            # Kinda overkill | but it's a good practice if we ever change missions naming convention
            # Calculate column widths
            col_widths = [max(len(cell) for cell in col) + 2 for col in zip(headers, *rows)]

            # Display table
            print("".join(f"{headers[i]:<{col_widths[i]}}" for i in range(len(headers))))
            print("".join("-" * col_width for col_width in col_widths))
            for row in rows:
                print("".join(f"{row[i]:<{col_widths[i]}}" for i in range(len(row))))
        else:
            print("No missions are currently flying.")
        return

    url = f"{API_BASE_URL}/missions/{mission_id}/prediction.json"
    response = make_api_request(url)

    save_response_to_file(save_to_file, response, csv_data_key='prediction')
    
    return response