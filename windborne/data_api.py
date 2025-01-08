from .config import DATA_API_BASE_URL, LAUNCH_SITES
from .utils import make_api_request, to_unix_timestamp, save_csv_json, format_little_r

import time
import os
from math import floor
from datetime import datetime, timezone, timedelta
import csv
import json

def get_observations(since=None, min_time=None, max_time=None, include_ids=None, include_mission_name=None, include_updated_at=None, mission_id=None, min_latitude=None, max_latitude=None, min_longitude=None, max_longitude=None, save_to_file=None):
    """
    Retrieves observations based on specified filters including geographical bounds.

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

        save_to_file (str): Optional path to save the response data.
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
        params["max_time"] = to_unix_timestamp(min_time)
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
    
    # Remove any keys where the value is None to avoid sending unnecessary parameters
    params = {k: v for k, v in params.items() if v is not None}
    
    response = make_api_request(url, params=params)

    if save_to_file:
        save_csv_json(save_to_file, response, csv_data_key='observations')
    
    return response

def get_super_observations(since=None, min_time=None, max_time=None, include_ids=None, include_mission_name=None, include_updated_at=None, mission_id=None, save_to_file=None):
    """
    Retrieves super observations based on specified filters.

    Args:
        since (str): Filter observations after this timestamp.
        min_time (str): Minimum timestamp for observations.
        max_time (str): Maximum timestamp for observations.
        include_ids (bool): Include observation IDs in response.
        include_mission_name (bool): Include mission names in response.
        include_updated_at (bool): Include update timestamps in response.
        mission_id (str): Filter observations by mission ID.
        save_to_file (str): Optional path to save the response data.
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
    if save_to_file:
        save_csv_json(save_to_file, response, csv_data_key='observations')
    
    return response

def convert_to_netcdf(data, curtime, bucket_hours, output_filename=None):
    # This module outputs data in netcdf format for the WMO ISARRA program.  The output format is netcdf
    #   and the style (variable names, file names, etc.) are described here:
    #  https://github.com/synoptic/wmo-uasdc/tree/main/raw_uas_to_netCDF

    # Import necessary libraries
    import xarray as xr
    import pandas as pd
    import numpy as np

    # Mapping of WindBorne names to ISARRA names
    rename_dict = {
        'latitude': 'lat',
        'longitude': 'lon',
        'altitude': 'altitude',
        'temperature': 'air_temperature',
        'wind_direction': 'wind_direction',
        'wind_speed': 'wind_speed',
        'pressure': 'air_pressure',
        'humidity_mixing_ratio': 'humidity_mixing_ratio',
        'index': 'obs',
    }

    # Convert dictionary to list for DataFrame
    data_list = []
    for obs_id, obs_data in data.items():
        # Convert 'None' strings to None type
        clean_data = {k: None if v == 'None' else v for k, v in obs_data.items()}
        data_list.append(clean_data)

    # Put the data in a panda datafram in order to easily push to xarray then netcdf output
    df = pd.DataFrame(data_list)

    # Convert numeric columns to float
    numeric_columns = ['latitude', 'longitude', 'altitude', 'pressure', 'temperature',
                       'speed_u', 'speed_v', 'specific_humidity', 'timestamp']
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    ds = xr.Dataset.from_dataframe(df)

    # Build the filename and save some variables for use later
    mt = datetime.fromtimestamp(curtime, tz=timezone.utc)
    outdatestring = mt.strftime('%Y%m%d%H%M%S')
    mission_name = df['mission_name'].iloc[0]
    if output_filename:
        output_file = output_filename
    else:
        outdatestring = mt.strftime('%Y%m%d%H%M%S')
        output_file = 'USADC_300_0{}_{}Z.nc'.format(mission_name[2:6], outdatestring)

    # Derived quantities calculated here:

    # convert from specific humidity to humidity_mixing_ratio
    mg_to_kg = 1000000.
    if not all(x is None for x in ds['specific_humidity'].data):
        ds['humidity_mixing_ratio'] = (ds['specific_humidity'] / mg_to_kg) / (1 - (ds['specific_humidity'] / mg_to_kg))
    else:
        ds['humidity_mixing_ratio'] = ds['specific_humidity']

    # Wind speed and direction from components
    ds['wind_speed'] = np.sqrt(ds['speed_u']*ds['speed_u'] + ds['speed_v']*ds['speed_v'])
    ds['wind_direction'] = np.mod(180 + (180 / np.pi) * np.arctan2(ds['speed_u'], ds['speed_v']), 360)

    ds['time'] = ds['timestamp'].astype(float)
    ds = ds.assign_coords(time=("time", ds['time'].data))

    # Now that calculations are done, remove variables not needed in the netcdf output
    variables_to_drop = ['humidity', 'speed_u', 'speed_v', 'speed_x', 'speed_y', 'specific_humidity',
                         'timestamp', 'mission_name']
    existing_vars = [var for var in variables_to_drop if var in ds]
    ds = ds.drop_vars(existing_vars)

    # Rename the variables
    ds = ds.rename(rename_dict)

    # Adding attributes to variables in the xarray dataset
    ds['time'].attrs = {'units': 'seconds since 1970-01-01T00:00:00', 'long_name': 'Time', '_FillValue': float('nan'),
                        'processing_level': ''}
    ds['lat'].attrs = {'units': 'degrees_north', 'long_name': 'Latitude', '_FillValue': float('nan'),
                       'processing_level': ''}
    ds['lon'].attrs = {'units': 'degrees_east', 'long_name': 'Longitude', '_FillValue': float('nan'),
                       'processing_level': ''}
    ds['altitude'].attrs = {'units': 'meters_above_sea_level', 'long_name': 'Altitude', '_FillValue': float('nan'),
                            'processing_level': ''}
    ds['air_temperature'].attrs = {'units': 'Kelvin', 'long_name': 'Air Temperature', '_FillValue': float('nan'),
                                   'processing_level': ''}
    ds['wind_speed'].attrs = {'units': 'm/s', 'long_name': 'Wind Speed', '_FillValue': float('nan'),
                              'processing_level': ''}
    ds['wind_direction'].attrs = {'units': 'degrees', 'long_name': 'Wind Direction', '_FillValue': float('nan'),
                                  'processing_level': ''}
    ds['humidity_mixing_ratio'].attrs = {'units': 'kg/kg', 'long_name': 'Humidity Mixing Ratio',
                                         '_FillValue': float('nan'), 'processing_level': ''}
    ds['air_pressure'].attrs = {'units': 'Pa', 'long_name': 'Atmospheric Pressure', '_FillValue': float('nan'),
                                'processing_level': ''}

    # Add Global Attributes synonymous across all UASDC providers
    ds.attrs['Conventions'] = "CF-1.8, WMO-CF-1.0"
    ds.attrs['wmo__cf_profile'] = "FM 303-2024"
    ds.attrs['featureType'] = "trajectory"

    # Add Global Attributes unique to Provider
    ds.attrs['platform_name'] = "WindBorne Global Sounding Balloon"
    ds.attrs['flight_id'] = mission_name
    ds.attrs['site_terrain_elevation_height'] = 'not applicable'
    ds.attrs['processing_level'] = "b1"
    ds.to_netcdf(output_file)

def poll_super_observations(start_time, end_time=None, interval=60, save_to_file=None, bucket_hours=6.0, output_format=None):
    """
    Fetches observations between a start time and an optional end time and saves to files in specified format.
    Files are broken up into time buckets, with filenames containing the time at the mid-point of the bucket.
    For example, for 6-hour buckets centered on 00 UTC, the start time should be 21 UTC of the previous day.

    Args:
        start_time (str): Start time in the format 'YYYY-MM-DD_HH:MM'.
        end_time (str): Optional end time in the format 'YYYY-MM-DD_HH:MM'.
        interval (int): Interval in seconds between polls if pagination is required (default: 60).
        save_to_file (str): If provided, saves all data to a single file instead of bucketing.
        bucket_hours (int): Size of time buckets in hours. Defaults to 6 hours.
        output_format (str): Format to save data in ('csv' or 'little_r').
    """

    start_time = to_unix_timestamp(start_time)

    if end_time:
        end_time = to_unix_timestamp(end_time)
    else:
        end_time = int(datetime.now().timestamp())

    # Supported formats for saving into separate files:
    #   - csv (default)
    #   - little_r
    #   - json
    #   - netcdf
    if output_format and output_format not in ['json', 'csv', 'little_r', 'netcdf']:
        print("Please use one of the following formats:")
        print("  - json")
        print("  - csv")
        print("  - little_r")
        print("  - netcdf")
        return

    # Supported formats for saving into a single file:
    # NOTE: for poll_super_observations we handle .csv saving within poll_super_observations and not using save_csv_json
    #   - .csv
    #   - .json
    #   - .little_r
    #   - .nc
    if save_to_file and not save_to_file.endswith(('.json', '.csv', '.little_r', '.nc')):
        print("Please use one of the following formats:")
        print("  - .json")
        print("  - .csv")
        print("  - .little_r")
        print("  - .nc")
        return

    # Convert start_time to datetime
    start_dt = datetime.fromtimestamp(start_time, tz=timezone.utc)

    # Calculate first center time that's after start_time
    hours_since_day_start = start_dt.hour + start_dt.minute / 60
    bucket_number = hours_since_day_start // bucket_hours
    first_center = start_dt.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(hours=(bucket_number + 1) * bucket_hours)


    # Headers for CSV files
    headers = [
        "timestamp", "id", "time", "latitude", "longitude", "altitude", "humidity",
        "mission_name", "pressure", "specific_humidity", "speed_u", "speed_v", "temperature"
    ]

    if save_to_file:
        all_observations = {}
    else:
        buckets = {}

    # Initialize the polling loop
    current_timestamp = start_time
    has_next_page = True


    while has_next_page:
        try:
            # Fetch observations
            observations_page = get_super_observations(
                since=current_timestamp,
                min_time=start_time,
                max_time=end_time,
                include_ids=True,
                include_mission_name=True
            )

            if observations_page is None:
                print("\n----------------------------------------------------------------------")
                print(f"Received null response from API. Retrying in {interval} seconds ...")
                print("----------------------------------------------------------------------")
                time.sleep(interval)
                continue

            observations = observations_page.get('observations', [])
            print(f"Fetched {len(observations)} observation(s)")

            for obs in observations:
                if 'mission_name' not in obs:
                    print("Warning: got an observation without a mission name")
                    continue

                timestamp = obs.get('timestamp')
                if not timestamp:
                    continue

                try:
                    obs_time = datetime.fromtimestamp(timestamp, tz=timezone.utc)
                except (OSError, ValueError, TypeError, OverflowError):
                    continue

                mission_name = obs.get('mission_name', 'Unknown')
                obs['time'] = obs_time.replace(tzinfo=timezone.utc).isoformat()

                processed_obs = {}
                for header in headers:
                    value = obs.get(header)
                    if value is None or value == '' or (isinstance(value, str) and not value.strip()):
                        processed_obs[header] = 'None'
                    else:
                        processed_obs[header] = value

                obs_id = f"{timestamp}_{mission_name}"

                if save_to_file:
                    all_observations[obs_id] = processed_obs
                else:
                    if obs_time >= start_dt:  # Only process observations after start time
                        hours_diff = (obs_time - first_center).total_seconds() / 3600
                        bucket_index = floor(hours_diff / bucket_hours)
                        bucket_center = first_center + timedelta(hours=bucket_index * bucket_hours)
                        bucket_end = bucket_center + timedelta(hours=bucket_hours)

                        if obs_time <= bucket_end:  # Include observations up to the end of the bucket
                            bucket_key = (bucket_center, mission_name)
                            if bucket_key not in buckets:
                                buckets[bucket_key] = {}
                            buckets[bucket_key][obs_id] = processed_obs

            # Update pagination
            next_timestamp = observations_page.get('next_since')
            has_next_page = observations_page.get('has_next_page', False)

            if not has_next_page or not next_timestamp or next_timestamp <= current_timestamp:
                print("-----------------------------------------------------\n")
                print("No more pages available or reached end of time range.")
                print("\n-----------------------------------------------------")
                break

            current_timestamp = next_timestamp

        except Exception as e:
            print(f"Error occurred: {e}")
            exit(1001)

    # Save data to a single file
    if save_to_file:
        filtered_observations = {obs_id: obs for obs_id, obs in all_observations.items()
                                 if float(obs['timestamp']) >= start_time}
        # Sort by timestamp
        sorted_observations = dict(sorted(filtered_observations.items(),
                                          key=lambda x: float(x[1]['timestamp'])))

        if save_to_file.endswith('.nc'):
            first_obs_timestamp = float(next(iter(sorted_observations.values()))['timestamp'])
            convert_to_netcdf(sorted_observations, first_obs_timestamp, bucket_hours=None, output_filename=save_to_file)

        elif save_to_file.endswith('.json'):
            with open(save_to_file, 'w', encoding='utf-8') as f:
                json.dump(sorted_observations, f, indent=4)

        elif save_to_file.endswith('.csv'):
            with open(save_to_file, mode='w', newline='') as file:
                writer = csv.DictWriter(file, fieldnames=headers)
                writer.writeheader()
                writer.writerows(sorted_observations.values())

        elif save_to_file.endswith('.little_r'):
            little_r_records = format_little_r(list(sorted_observations.items()))
            with open(save_to_file, 'w') as file:
                file.write('\n'.join(little_r_records))

        print(f"Saved {len(sorted_observations)} {'observation' if len(sorted_observations) == 1 else 'observations'} to {save_to_file}")

    # Save data to multiple file
    elif output_format:
        # Track statistics per mission
        mission_stats = {}  # {mission_name: {'files': 0, 'observations': 0}}
        total_observations_written = 0

        # Save bucketed data
        for (bucket_center, mission_name), observations in buckets.items():
            if observations:
                # Format hour to be the actual bucket center
                bucket_hour = int((bucket_center.hour + bucket_hours/2) % 24)

                if output_format == 'netcdf':
                    convert_to_netcdf(observations, bucket_center.timestamp(), bucket_hours)

                if output_format == 'csv':
                    output_file = (f"WindBorne_{mission_name}_%04d-%02d-%02d_%02d_%dh.csv" %
                                   (bucket_center.year, bucket_center.month, bucket_center.day,
                                    bucket_hour, bucket_hours))

                    os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)

                    # Sort observations by timestamp within each bucket
                    sorted_obs = sorted(observations.values(), key=lambda x: int(x['timestamp']))

                    with open(output_file, mode='w', newline='') as file:
                        writer = csv.DictWriter(file, fieldnames=headers)
                        writer.writeheader()
                        writer.writerows(sorted_obs)

                elif output_format == 'json':
                    output_file = (f"WindBorne_{mission_name}_%04d-%02d-%02d_%02d_%dh.json" %
                                   (bucket_center.year, bucket_center.month, bucket_center.day,
                                    bucket_hour, bucket_hours))

                    os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)

                    # Sort observations by timestamp within each bucket
                    sorted_obs = dict(sorted(observations.items(), key=lambda x: int(x[1]['timestamp'])))

                    with open(output_file, 'w', encoding='utf-8') as file:
                        json.dump(sorted_obs, file, indent=4)

                elif output_format == 'little_r':
                    output_file = (f"WindBorne_{mission_name}_%04d-%02d-%02d_%02d-00_%dh.little_r" %
                                   (bucket_center.year, bucket_center.month, bucket_center.day,
                                    bucket_hour, bucket_hours))

                    os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)

                    sorted_obs = sorted(observations.items(), key=lambda x: int(x[1]['timestamp']))

                    little_r_records = format_little_r(sorted_obs)
                    with open(output_file, 'w') as file:
                        file.write('\n'.join(little_r_records))
                total_observations_written += len(observations)

                # Update statistics
                if mission_name not in mission_stats:
                    mission_stats[mission_name] = {'files': 0, 'observations': 0}
                mission_stats[mission_name]['files'] += 1
                mission_stats[mission_name]['observations'] += len(observations)
        # Print total observations written
        print(f"Total {'observation' if total_observations_written == 1 else 'observations'} written: {total_observations_written}")
        print("-----------------------------------------------------")

        # Print summary for each mission
        for mission_name, stats in mission_stats.items():
            print(f"Mission {mission_name}: Saved {stats['observations']} {'observation' if stats['observations'] == 1 else 'observations'} across {stats['files']} {'file' if stats['files'] == 1 else 'files'}")

    print("-----------------------------------------------------")
    print("All observations have been processed and saved.")

def get_flying_missions(cli=None, save_to_file=None):
    """
    Retrieves a list of currently flying missions.
    In CLI mode, displays missions in a formatted table.

    Args:
        save_to_file (str): Optional path to save the response data.
                           If provided, saves the data in CSV or JSON format.

    Returns:
        dict: The API response containing list of flying missions.
    """

    url = f"{DATA_API_BASE_URL}/missions.json"
    flying_missions_response = make_api_request(url)
    flying_missions = flying_missions_response.get("missions", [])

    # Display currently flying missions only if we are in cli and we don't save info in file
    if flying_missions and cli and not save_to_file:
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

    if save_to_file:
        save_csv_json(save_to_file, flying_missions_response, csv_data_key='missions')
    
    return flying_missions_response

def get_mission_launch_site(mission_id=None, save_to_file=None):
    """
    Retrieves launch site information for a specified mission.
    """
    if not mission_id:
        print("Must provide mission ID")
        return

    url = f"{DATA_API_BASE_URL}/missions/{mission_id}/launch_site.json"
    response = make_api_request(url)

    if response and not save_to_file:
        launch_site = response.get('launch_site')
        if isinstance(launch_site, dict):
            site_name = LAUNCH_SITES.get(launch_site.get('id'), 'N/A')
            print("Mission launch site\n")
            print(f"{'Location':<12} {site_name}")
            print(f"{'Latitude':<12} {launch_site.get('latitude', 'N/A')}")
            print(f"{'Longitude':<12} {launch_site.get('longitude', 'N/A')}")
        else:
            print("Unable to display launch site details - unexpected format")

    if save_to_file:
        save_csv_json(save_to_file, response, csv_data_key='launch_site')

    return response

def get_predicted_path(mission_id=None, save_to_file=None):
    """
        Fetches the predicted flight path for a given mission.
        Displays currently flying missions if the provided mission ID is invalid.

        Args:
            mission_id (str): The ID of the mission to fetch the prediction for.
            save_to_file (str): Optional path to save the response data.
                               If provided, saves the data in CSV format.

        Returns:
            dict: The API response containing the predicted flight path data.
    """
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

    url = f"{DATA_API_BASE_URL}/missions/{mission_id}/prediction.json"
    response = make_api_request(url)

    if save_to_file:
        save_csv_json(save_to_file, response, csv_data_key='prediction')
    
    return response