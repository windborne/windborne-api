import time
import os
from datetime import datetime, timezone, timedelta
import csv
import json

from .api_request import make_api_request
from .observation_formatting import format_little_r, convert_to_netcdf
from .utils import to_unix_timestamp, save_arbitrary_response, print_table
from .track_formatting import save_track

DATA_API_BASE_URL = "https://sensor-data.windbornesystems.com/api/v1"

# ------------
# CORE RESOURCES
# ------------

def get_observations_page(since=None, min_time=None, max_time=None, include_ids=None, include_mission_name=True, include_updated_at=None, mission_id=None, min_latitude=None, max_latitude=None, min_longitude=None, max_longitude=None, output_file=None):
    """
    Retrieves observations page based on specified filters including geographical bounds.

    Args:
        since (str): Filter observations after this timestamp.

        min_time (str): Minimum timestamp for observations.
        max_time (str): Maximum timestamp for observations.
        include_ids (bool): Include observation IDs in response.
        include_mission_name (bool): Include mission names in response.
        include_updated_at (bool): Include update timestamps in response.
        mission_id (str): Filter observations by mission ID.
        min_latitude (float): Minimum latitude boundary.
        max_latitude (float): Maximum latitude boundary.
        min_longitude (float): Minimum longitude boundary.
        max_longitude (float): Maximum longitude boundary.

        output_file (str): Optional path to save the response data.
                           If provided, saves the data in CSV format.

    Returns:
        dict: The API response containing filtered observations.
    """

    url = f"{DATA_API_BASE_URL}/observations.json"
    
    # Convert date strings to Unix timestamps
    params = {}
    if since:
        params["since"] = to_unix_timestamp(since)
    if min_time:
        params["min_time"] = to_unix_timestamp(min_time)
    if max_time:
        params["max_time"] = to_unix_timestamp(max_time)
    if mission_id:
        params["mission_id"] = mission_id
    if min_latitude:
        params["min_latitude"] = min_latitude
    if max_latitude:
        params["max_latitude"] = max_latitude
    if min_longitude:
        params["min_longitude"] = min_longitude
    if max_longitude:
        params["max_longitude"] = max_longitude
    if include_ids:
        params["include_ids"] = True
    if include_mission_name:
        params["include_mission_name"] = True
    if include_updated_at:
        params["include_updated_at"] = True
    
    params = {k: v for k, v in params.items() if v is not None}
    
    response = make_api_request(url, params=params)

    if output_file:
        save_arbitrary_response(output_file, response, csv_data_key='observations')
    
    return response


def get_super_observations_page(since=None, min_time=None, max_time=None, include_ids=None, include_mission_name=None, include_updated_at=None, mission_id=None, output_file=None):
    """
    Retrieves super observations page based on specified filters.

    Args:
        since (str): Filter observations after this timestamp.
        min_time (str): Minimum timestamp for observations.
        max_time (str): Maximum timestamp for observations.
        include_ids (bool): Include observation IDs in response.
        include_mission_name (bool): Include mission names in response.
        include_updated_at (bool): Include update timestamps in response.
        mission_id (str): Filter observations by mission ID.
        output_file (str): Optional path to save the response data.
                           If provided, saves the data in CSV format.

    Returns:
        dict: The API response containing filtered super observations.
    """

    url = f"{DATA_API_BASE_URL}/super_observations.json"

    params = {}
    if since:
        params["since"] = to_unix_timestamp(since)
    if min_time:
        params["min_time"] = to_unix_timestamp(min_time)
    if max_time:
        params["max_time"] = to_unix_timestamp(max_time)
    if mission_id:
        params["mission_id"] = mission_id
    if include_ids:
        params["include_ids"] = True
    if include_mission_name:
        params["include_mission_name"] = True
    if include_updated_at:
        params["include_updated_at"] = True

    params = {k: v for k, v in params.items() if v is not None}

    response = make_api_request(url, params=params)
    if output_file:
        save_arbitrary_response(output_file, response, csv_data_key='observations')

    return response


def save_observations_batch(observations, output_file, output_format, output_dir, start_time=None, end_time=None, bucket_hours=6.0, csv_headers=None, custom_save=None, prevent_overwrites=False):
    filtered_observations = observations
    if start_time is not None:
        filtered_observations = [obs for obs in observations if float(obs['timestamp']) >= start_time]

    if end_time is not None:
        filtered_observations = [obs for obs in observations if float(obs['timestamp']) <= end_time]

    # Sort by timestamp
    sorted_observations = sorted(filtered_observations, key=lambda x: float(x['timestamp']))

    if output_file:
        if custom_save is not None:
            custom_save(sorted_observations, output_file)
        else:
            save_observations_to_file(sorted_observations, output_file, csv_headers=csv_headers, prevent_overwrites=prevent_overwrites)
    else:
        save_observations_batch_in_buckets(sorted_observations, output_format, output_dir, bucket_hours=bucket_hours, csv_headers=csv_headers, custom_save=custom_save, prevent_overwrites=prevent_overwrites)


def save_observations_to_file(sorted_observations, output_file, csv_headers=None, prevent_overwrites=False):
    if len(sorted_observations) == 0:
        print(f"Skipping empty file {output_file}")
        return

    directory = os.path.dirname(output_file)
    if directory and not os.path.isdir(directory):
        os.makedirs(directory, exist_ok=True)

    if prevent_overwrites and os.path.exists(output_file):
        # save to outputfile.0.ext, outputfile.1.ext, etc.
        base, ext = os.path.splitext(output_file)
        if ext[0] == '.':
            ext = ext[1:]

        # if ext is already a .0.ext, we need to split it again
        i = 1
        if '.' in ext and ext.split('.')[0].isdigit():
            i = int(ext.split('.')[0]) + 1
            ext = '.'.join(ext.split('.')[1:])

        while os.path.exists(f"{base}.{i}.{ext}"):
            i += 1

        output_file = f"{base}.{i}.{ext}"

    print(f"Saving {len(sorted_observations)} {'observation' if len(sorted_observations) == 1 else 'observations'} to {output_file}")
    if len(sorted_observations) > 10_000:
        print("This may take a while...")
    print("-----------------------------------------------------\n")

    if output_file.endswith('.nc'):
        first_obs_timestamp = float(sorted_observations[0]['timestamp'])
        convert_to_netcdf(sorted_observations, first_obs_timestamp, output_file)

    elif output_file.endswith('.json'):
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(sorted_observations, f, indent=4)

    elif output_file.endswith('.csv'):
        with open(output_file, mode='w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=csv_headers)
            writer.writeheader()
            writer.writerows(sorted_observations)

    elif output_file.endswith('.little_r'):
        little_r_records = format_little_r(sorted_observations)
        with open(output_file, 'w') as file:
            file.write('\n'.join(little_r_records))

    print(f"Saved {len(sorted_observations)} {'observation' if len(sorted_observations) == 1 else 'observations'} to {output_file}")


def save_observations_batch_in_buckets(sorted_observations, output_format, output_dir, bucket_hours=6.0, csv_headers=None, custom_save=None, prevent_overwrites=False):
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        print(f"Files will be saved to {output_dir}")
    else:
        print(f"Files will be saved to {os.getcwd()}")


    by_mission = {}
    mission_names = {}
    for observation in sorted_observations:
        mission_id = observation['mission_id']
        if mission_id not in by_mission:
            by_mission[mission_id] = []
            mission_names[mission_id] = observation.get('mission_name', mission_id)

        by_mission[mission_id].append(observation)

    for mission_id, accumulated_observations in by_mission.items():
        mission_name = mission_names[mission_id]
        start_index = 0
        earliest_time = accumulated_observations[0]['timestamp']
        curtime = earliest_time - earliest_time % (bucket_hours * 60 * 60)

        for i in range(len(accumulated_observations)):
            segment = None
            if accumulated_observations[i]['timestamp'] - curtime > bucket_hours * 60 * 60:
                segment = accumulated_observations[start_index:i]

            if i == len(accumulated_observations) - 1:
                segment = accumulated_observations[start_index:]

            if segment is None:
                continue

            bucket_start = datetime.fromtimestamp(curtime, tz=timezone.utc)

            file_name = f"WindBorne_{mission_name}_%04d-%02d-%02d_%02d_%dh" % (
                bucket_start.year, bucket_start.month, bucket_start.day,
                bucket_start.hour, bucket_hours)

            extension = f".{output_format}"
            if output_format == 'netcdf':
                extension = '.nc'

            output_file = os.path.join(output_dir or '.', file_name + extension)
            if custom_save is not None:
                custom_save(segment, output_file)
            else:
                save_observations_to_file(segment, output_file, csv_headers=csv_headers, prevent_overwrites=prevent_overwrites)

            start_index = i
            curtime += timedelta(hours=bucket_hours).seconds


def get_observations_core(api_args, csv_headers, get_page, start_time=None, end_time=None, output_file=None, bucket_hours=6.0, output_format=None, output_dir=None, callback=None, custom_save=None, exit_at_end=True):
    """
    Fetches observations or superobservations between a start time and an optional end time and saves to files in specified format.
    Files are broken up into time buckets, with filenames containing the time at the mid-point of the bucket.
    For example, for 6-hour buckets centered on 00 UTC, the start time should be 21 UTC of the previous day.

    Args:
        api_args (dict): Arguments to pass to the API endpoint.
        csv_headers (list): Headers for CSV files.
        get_page (callable): Function to fetch a page of observations.
        start_time (str): A date string, supporting formats YYYY-MM-DD HH:MM:SS, YYYY-MM-DD_HH:MM and ISO strings,
                          representing the starting time of fetching data.
        end_time (str): Optional. A date string, supporting formats YYYY-MM-DD HH:MM:SS, YYYY-MM-DD_HH:MM and ISO strings,
                        representing the end time of fetching data. If not provided, current time is used as end time.



        output_file (str): Saves all data to a single file instead of bucketing.
                            Supported formats are '.csv', '.json', '.little_r' and '.nc'
        bucket_hours (int): Optional. Size of time buckets in hours. Defaults to 6 hours.
        output_format (str): Optional. Format to save data in separate files. Supported formats are 'json, 'csv', 'little_r' and 'netcdf'.
        output_dir (str): Optional. Directory path where the separate files should be saved. If not provided, files will be saved in current directory.
        callback (callable): Optional callback function that receives (super observations, metadata) before saving.
                             This allows custom processing or saving in custom formats.
        custom_save (callable): Optional function to save observations in a custom format.
        exit_at_end (bool): Whether to exit after fetching all observations or keep polling.
    """
    if output_format and not custom_save:
        verify_observations_output_format(output_format)

    if output_file and not custom_save:
        verify_observations_output_format(output_file.split('.')[-1])

    # When we don't clear batches, we can safely overwrite the output files; this is nice
    # However, it also holds everything in memory, so we should only do this when we're not going to run indefinitely
    clear_batches = not exit_at_end
    batch_size = 10_000
    if not batch_size: # save less frequently
        batch_size = 100_000

    if start_time is not None:
        start_time = to_unix_timestamp(start_time)

    if end_time is not None:
        end_time = to_unix_timestamp(end_time)

    def save_with_context(observations_batch):
        save_observations_batch(
            observations_batch,
            output_file=output_file,
            output_format=output_format,
            output_dir=output_dir,
            start_time=start_time,
            end_time=end_time,
            bucket_hours=bucket_hours,
            csv_headers=csv_headers,
            custom_save=custom_save,
            prevent_overwrites=clear_batches
        )

    result = iterate_through_observations(get_page, api_args, callback=callback, batch_callback=save_with_context, exit_at_end=exit_at_end, clear_batches=clear_batches, batch_size=batch_size)
    if isinstance(result, int):
        print(f"Processed {result} observations")

    return result


def iterate_through_observations(get_page, args, callback=None, batch_callback=None, exit_at_end=True, batch_size=10_000, clear_batches=True):
    """
    Repeatedly calls `get_page` with `args`
    For each page fetched, it calls `callback` with the full response
    Every `batch_size` observations fetched, it calls `batch_callback` with the batched observations (if provided)
    Returns an array of all observations fetched if no batch_callback is provided

    Args:
        get_page (callable): Function to fetch a page of observations
        args (dict): Arguments to pass to `get_page`
        callback (callable): Function to call with each page of observations
        batch_callback (callable): Function to call with a batch of observations
        exit_at_end (bool): Whether to exit after fetching all observations or keep polling
        batch_size (int): Number of observations to accumulate before calling `batch_callback`
        clear_batches (bool): Whether to clear the batched observations after calling `batch_callback`
    """

    batched_observations = []
    since = args.get('since', 0)
    processed_count = 0

    if args.get('min_time') is not None:
        args['min_time'] = to_unix_timestamp(args['min_time'])
        if since == 0:
            since = args['min_time']

    if args.get('max_time') is not None:
        args['max_time'] = to_unix_timestamp(args['max_time'])

    while True:
        args = {**args, 'since': since}
        response = get_page(**args)
        if not response:
            print("Received null response from API. Retrying in 10 seconds...")
            time.sleep(10)
            continue

        observations = response.get('observations', [])

        if callback:
            callback(response)
        else:
            since_timestamp = since
            if since_timestamp > 4_000_000_000: # in nanoseconds rather than seconds
                since_timestamp /= 1_000_000_000
            since_dt = datetime.fromtimestamp(since_timestamp, timezone.utc)
            print(f"Fetched page with {len(observations)} observation(s) updated {since_dt} or later")

        batched_observations.extend(observations)

        processed_count += len(observations)

        if batch_callback and (len(batched_observations) >= batch_size or not response['has_next_page']):
            batch_callback(batched_observations)
            if clear_batches:
                batched_observations = []

        if not response['has_next_page']:
            print("No more data available.")
            if exit_at_end:
                break

            time.sleep(60)
            continue

        since = response['next_since']

    if batch_callback and len(batched_observations) > 0:
        batch_callback(batched_observations)
        if clear_batches:
            batched_observations = []

    if batch_callback:
        return processed_count
    else:
        return batched_observations


def verify_observations_output_format(output_format):
    valid_formats = ['json', 'csv', 'little_r', 'netcdf', 'nc']
    if output_format  in valid_formats:
        return True

    print("Please use one of the following formats:")
    for fmt in valid_formats:
        print(f"  - {fmt}")

    exit(1)

def get_observations(start_time, end_time=None, include_updated_at=None, mission_id=None, min_latitude=None, max_latitude=None, min_longitude=None, max_longitude=None, output_file=None, bucket_hours=6.0, output_format=None, output_dir=None, callback=None, custom_save=None, exit_at_end=True):
    """
    Fetches observations between a start time and an optional end time and saves to files in specified format.
    Files are broken up into time buckets, with filenames containing the time at the mid-point of the bucket.
    For example, for 6-hour buckets centered on 00 UTC, the start time should be 21 UTC of the previous day.

    Args:
        start_time (str): A date string, supporting formats YYYY-MM-DD HH:MM:SS, YYYY-MM-DD_HH:MM and ISO strings,
                          representing the starting time of fetching data.
        end_time (str): Optional. A date string, supporting formats YYYY-MM-DD HH:MM:SS, YYYY-MM-DD_HH:MM and ISO strings,
                        representing the end time of fetching data. If not provided, current time is used as end time.

        include_updated_at (bool): Include update timestamps in response.
        mission_id (str): Filter observations by mission ID.
        min_latitude (float): Minimum latitude boundary.
        max_latitude (float): Maximum latitude boundary.
        min_longitude (float): Minimum longitude boundary.
        max_longitude (float): Maximum longitude boundary.

        output_file (str): Saves all data to a single file instead of bucketing.
                            Supported formats are '.csv', '.json', '.little_r' and '.nc'
        bucket_hours (int): Optional. Size of time buckets in hours. Defaults to 6 hours.
        output_format (str): Optional. Format to save data in separate files. Supported formats are 'json, 'csv', 'little_r' and 'netcdf'.
        output_dir (str): Optional. Directory path where the separate files should be saved. If not provided, files will be saved in current directory.
        callback (callable): Optional callback function that receives (super observations, metadata) before saving.
                             This allows custom processing or saving in custom formats.
        custom_save (callable): Optional function to save observations in a custom format.
        exit_at_end (bool): Whether to exit after fetching all observations or keep polling.
    """

    # Headers for CSV files
    csv_headers = [
        "timestamp", "id", "time", "latitude", "longitude", "altitude", "humidity",
        "pressure", "specific_humidity", "speed_u", "speed_v", "temperature", "mission_name", "mission_id"
    ]

    api_args = {
        'min_time': start_time,
        'max_time': end_time,
        'min_latitude': min_latitude,
        'max_latitude': max_latitude,
        'min_longitude': min_longitude,
        'max_longitude': max_longitude,
        'include_updated_at': include_updated_at,
        'mission_id': mission_id,
        'include_ids': True,
        'include_mission_name': True
    }

    return get_observations_core(api_args, csv_headers, get_page=get_observations_page, start_time=start_time, end_time=end_time, output_file=output_file, bucket_hours=bucket_hours, output_format=output_format, output_dir=output_dir, callback=callback, custom_save=custom_save, exit_at_end=exit_at_end)

def poll_observations(**kwargs):
    """
    Continuously polls for observations and saves to files in specified format.
    Will run indefinitely until interrupted.
    Same as get_observations, but runs in an infinite loop.
    """

    # Print warning about infinite loop
    print(" ___________________________________________________________________")
    print("|                          WARNING  \U000026A0\U0000FE0F                               |")
    print("|                 You are entering an endless loop.                 |")
    print("|                                                                   |")
    print("|                 Press Ctrl + C anytime to exit.                   |")
    print("|___________________________________________________________________|\n\n")

    get_observations(**kwargs, exit_at_end=False)

def get_super_observations(start_time, end_time=None, mission_id=None, include_updated_at=True, output_file=None, bucket_hours=6.0, output_format=None, output_dir=None, callback=None, custom_save=None, exit_at_end=True):
    """
    Fetches super observations between a start time and an optional end time and saves to files in specified format.
    Files are broken up into time buckets, with filenames containing the time at the mid-point of the bucket.
    For example, for 6-hour buckets centered on 00 UTC, the start time should be 21 UTC of the previous day.

    Args:
        start_time (str): A date string, supporting formats YYYY-MM-DD HH:MM:SS, YYYY-MM-DD_HH:MM and ISO strings,
                          representing the starting time of fetching data.
        end_time (str): Optional. A date string, supporting formats YYYY-MM-DD HH:MM:SS, YYYY-MM-DD_HH:MM and ISO strings,
                        representing the end time of fetching data. If not provided, current time is used as end time.
        mission_id (str): Filter observations by mission ID.
        include_updated_at (bool): Include update timestamps in response.
        output_file (str): Saves all data to a single file instead of bucketing.
                            Supported formats are '.csv', '.json', '.little_r' and '.nc'
        bucket_hours (int): Optional. Size of time buckets in hours. Defaults to 6 hours.
        output_format (str): Optional. Format to save data in separate files. Supported formats are 'json, 'csv', 'little_r' and 'netcdf'.
        output_dir (str): Optional. Directory path where the separate files should be saved. If not provided, files will be saved in current directory.
        callback (callable): Optional callback function that receives (super observations, metadata) before saving.
                             This allows custom processing or saving in custom formats.
        custom_save (callable): Optional function to save observations in a custom format.
        exit_at_end (bool): Whether to exit after fetching all observations or keep polling.
    """
    csv_headers = [
        "timestamp", "id", "time", "latitude", "longitude", "altitude", "humidity",
        "mission_name", "pressure", "specific_humidity", "speed_u", "speed_v", "temperature"
    ]

    api_args = {
        'min_time': start_time,
        'max_time': end_time,
        'mission_id': mission_id,
        'include_updated_at': include_updated_at,
        'include_ids': True,
        'include_mission_name': True
    }

    return get_observations_core(api_args, csv_headers, get_page=get_super_observations_page, start_time=start_time, end_time=end_time, output_file=output_file, bucket_hours=bucket_hours, output_format=output_format, output_dir=output_dir, callback=callback, custom_save=custom_save, exit_at_end=exit_at_end)

def poll_super_observations(**kwargs):
    """
    Continuously polls for super observations and saves to files in specified format.
    Will run indefinitely until interrupted.
    Same as get_super_observations, but runs in an infinite loop.
    """

    # Print warning about infinite loop
    print(" ___________________________________________________________________")
    print("|                          WARNING  \U000026A0\U0000FE0F                               |")
    print("|                 You are entering an endless loop.                 |")
    print("|                                                                   |")
    print("|                 Press Ctrl + C anytime to exit.                   |")
    print("|___________________________________________________________________|\n\n")

    get_super_observations(**kwargs, exit_at_end=False)


# ------------
# METADATA
# ------------
def get_flying_missions(output_file=None, print_results=False):
    """
    Retrieves a list of currently flying missions.
    In CLI mode, displays missions in a formatted table.

    Args:
        output_file (str): Optional path to save the response data.
                           If provided, saves the data in CSV or JSON format.
        print_results (bool): Whether to print the results in the CLI.

    Returns:
        dict: The API response containing list of flying missions.
    """
    page_size = 64

    # Initial query to get total flying
    query_params = {
        'page': 0,
        'page_size': page_size 
    }

    url = f"{DATA_API_BASE_URL}/missions.json"
    flying_missions_response = make_api_request(url, params=query_params)

    flying_missions = flying_missions_response.get("missions", [])
    num_fetched_missions = len(flying_missions) 
    
    while num_fetched_missions == page_size:
        query_params['page'] += 1

        new_missions = make_api_request(url, params=query_params).get('missions', [])
        num_fetched_missions = len(new_missions)
        
        flying_missions += new_missions
    
    for mission in flying_missions:
        if mission.get('number'):
            mission['name'] = f"W-{mission['number']}"

    # Display currently flying missions only if we are in cli and we don't save info in file
    if print_results:
        if flying_missions:
            print("Currently flying missions:\n")

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

    if output_file:
        save_arbitrary_response(output_file, flying_missions_response, csv_data_key='missions')
    
    return flying_missions


def get_mission_launch_site(mission_id=None, output_file=None, print_result=False):
    """
    Retrieves launch site information for a specified mission.

    Args:
        mission_id (str): The ID of the mission to fetch the launch site for.
        output_file (str): Optional path to save the response data.
                           If provided, saves the data in CSV format.
        print_result (bool): Whether to print the results in the CLI.

    Returns:
        dict: The API response containing the launch site information.
    """
    if not mission_id:
        print("Must provide mission ID")
        return

    url = f"{DATA_API_BASE_URL}/missions/{mission_id}/launch_site.json"
    response = make_api_request(url)

    if response and print_result:
        launch_site = response.get('launch_site')
        if isinstance(launch_site, dict):
            print("Mission launch site\n")
            print(f"{'ID':<12} {launch_site.get('id')}")
            print(f"{'Latitude':<12} {launch_site.get('latitude', 'N/A')}")
            print(f"{'Longitude':<12} {launch_site.get('longitude', 'N/A')}")
        else:
            print("Unable to display launch site details - unexpected format")

    if output_file:
        save_arbitrary_response(output_file, response, csv_data_key='launch_site')

    return response.get('launch_site')


def get_flying_mission(mission_id, verify_flying=True):
    """
    Fetches a flying mission by ID.
    If the mission is not flying, displays a list of currently flying missions.

    Args:
        mission_id (str): The ID of the mission to fetch.
        verify_flying (bool): Whether to always check if the mission is flying.

    Returns:
        dict: The API response containing the mission data, or None if the mission is not flying.
    """
    if not verify_flying and not mission_id.startswith('W-'):
        return {
            'id': mission_id,
        }

    # Check if provided mission ID belong to a flying mission
    flying_missions = get_flying_missions()

    mission = None
    for candidate in flying_missions:
        if candidate.get('id') == mission_id or candidate.get('name') == mission_id:
            mission = candidate
            break

    if mission is None:
        print(f"Provided mission ID '{mission_id}' does not belong to a mission that is currently flying.")

        # Display currently flying missions
        if flying_missions:
            print("\nCurrently flying missions:\n")

            print_table(flying_missions, keys=['id', 'name'], headers=['Mission ID', 'Mission Name'])
        else:
            print("No missions are currently flying.")
        return None

    return mission


def get_predicted_path(mission_id=None, output_file=None, print_result=False):
    """
        Fetches the predicted flight path for a given mission.
        Displays currently flying missions if the provided mission ID is invalid.

        Args:
            mission_id (str): The ID of the mission to fetch the prediction for.
            output_file (str): Optional path to save the response data.
            print_result (bool): Whether to print the results in the CLI.

        Returns:
            list: The API response containing the predicted flight path data.
    """
    if not mission_id:
        print("To get the predicted flight path for a given mission you must provide a mission ID.")
        return

    mission = get_flying_mission(mission_id)

    url = f"{DATA_API_BASE_URL}/missions/{mission.get('id')}/prediction.json"
    response = make_api_request(url)

    if response is None:
        return

    if output_file:
        name = mission.get('name', mission_id)
        save_track(output_file, {name: response['prediction']}, time_key='time')

    if print_result:
        print("Predicted flight path\n")
        print_table(response['prediction'], keys=['time', 'latitude', 'longitude', 'altitude'], headers=['Time', 'Latitude', 'Longitude', 'Altitude'])

    return response.get('prediction')


def get_current_location(mission_id=None, output_file=None, print_result=False, verify_flying=True):
    """
    Fetches the current location for a given mission.

    Args:
        mission_id (str): The ID of the mission to fetch the current location for.
        output_file (str): Optional path to save the response data.
        print_result (bool): Whether to print the results in the CLI.
        verify_flying (bool): Whether to verify the mission is flying before trying to fetch the current location

    Returns:
        dict: Current location with latitude, longitude, and altitude, or None if not found
    """
    if not mission_id:
        print("To get the current location for a given mission you must provide a mission ID.")
        return

    mission = get_flying_mission(mission_id, verify_flying=verify_flying)

    url = f"{DATA_API_BASE_URL}/missions/{mission.get('id')}/current_location.json"
    response = make_api_request(url)

    if response is None:
        return

    if output_file:
        save_arbitrary_response(output_file, response, csv_data_key=None)

    if print_result:
        print("Current location\n")
        print_table([response], keys=['latitude', 'longitude', 'altitude'],
                    headers=['Latitude', 'Longitude', 'Altitude'])

    return response


def get_flight_path(mission_id=None, output_file=None, print_result=False):
    """
        Fetches the flight path for a given mission.

        Args:
            mission_id (str): The ID of the mission to fetch the flight path for.
            output_file (str): Optional path to save the response data.
            print_result (bool): Whether to print the results in the CLI.

        Returns:
            list: The API response containing the flight path.
    """
    if not mission_id:
        print("A mission id is required to get a flight path")
        return

    url = f"{DATA_API_BASE_URL}/missions/{mission_id}/flight_data.json"
    response = make_api_request(url)

    if response is None:
        return

    if output_file:
        save_track(output_file, {mission_id: response['flight_data']}, time_key='transmit_time')

    if print_result:
        print("Flight path\n")
        print_table(response['flight_data'], keys=['transmit_time', 'latitude', 'longitude', 'altitude'], headers=['Time', 'Latitude', 'Longitude', 'Altitude'])

    return response.get('flight_data')
