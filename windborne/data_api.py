from .config import API_BASE_URL, make_api_request
from .utils import to_unix_timestamp, save_response_to_file
import time
import os
from math import floor
from datetime import datetime, timezone, timedelta
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

def poll_observations(start_time, end_time=None, interval=60, save_to_file=None, csv_data_key="observations", bucket_hours=6, output_format='csv'):
    """
    Fetches observations between a start time and an optional end time and saves to files in specified format.
    Files are broken up into time buckets, with filenames containing the time at the mid-point of the bucket.
    For example, for 6-hour buckets centered on 00 UTC, the start time should be 21 UTC of the previous day.

    Args:
        start_time (str): The start time in the format 'YYYY-MM-DD_HH:MM'.
        end_time (str): Optional end time in the format 'YYYY-MM-DD_HH:MM'.
        interval (int): Interval in seconds between polls if pagination is required (default: 60).
        save_to_file (str): If provided, saves all data to a single file instead of bucketing.
        csv_data_key (str): Key to extract data for CSV saving (default: "observations").
        bucket_hours (int): Size of time buckets in hours. Defaults to 6 hours.
        output_format (str): Format to save data in ('csv' or 'little_r'). Defaults to 'csv'.
    """

    # We must have a start_time set
    if not start_time:
        print("Please provide a start time in the format 'YYYY-MM-DD_HH:MM'.")
        return

    # Supported formats for saving into a single file:
    #   - .csv (default)
    #   - .little_r
    if output_format not in ['csv', 'little_r']:
        print("Invalid output format. Please use 'csv' or 'little_r'.")
        return

    # Supported formats for saving into a single file:
    # NOTE: for poll_observation we handle .csv saving within poll_observation and not using save_response_to_file
    #   - .csv
    #   - .json
    if save_to_file and not save_to_file.endswith(('.json', '.csv')):
        print("Unsupported file format. Please use either .json or .csv.")
        return

    # Convert start_time to datetime
    start_dt = datetime.strptime(start_time, '%Y-%m-%d_%H:%M').replace(tzinfo=timezone.utc)

    # Calculate first center time that's after start_time
    hours_since_day_start = start_dt.hour + start_dt.minute / 60
    bucket_number = hours_since_day_start // bucket_hours
    first_center = start_dt.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(hours=(bucket_number + 1) * bucket_hours)

    if end_time:
        end_dt = datetime.strptime(end_time, '%Y-%m-%d_%H:%M').replace(tzinfo=timezone.utc)
    else:
        end_dt = datetime.now(timezone.utc)

    # Headers for CSV files
    headers = [
        "timestamp", "time", "latitude", "longitude", "altitude", "humidity",
        "mission_name", "pressure", "specific_humidity", "speed_u", "speed_v", "temperature"
    ]

    if save_to_file:
        all_observations = {}
    else:
        buckets = {}

    # Initialize the polling loop
    current_timestamp = int(start_dt.timestamp())
    has_next_page = True

    while has_next_page:
        try:
            # Fetch observations
            observations_page = get_super_observations(
                since=current_timestamp,
                max_time=int(end_dt.timestamp()),
                include_mission_name=True
            )

            if observations_page is None:
                print("Received null response from API. Retrying in 60 seconds...")
                time.sleep(interval)
                continue

            observations = observations_page.get(csv_data_key, [])
            print(f"Fetched {len(observations)} {'observation' if len(observations) == 1 else 'observations'}")

        except Exception as e:
            print(f"Error occurred: {e}")
            print("Retrying in 60 seconds...")
            time.sleep(interval)
            continue

        for obs in observations:
            timestamp = obs.get('timestamp')
            if not timestamp:
                continue

            try:
                obs_time = datetime.fromtimestamp(timestamp, tz=timezone.utc)
            except (OSError, ValueError, TypeError, OverflowError):
                continue

            mission_name = obs.get('mission_name', 'Unknown')
            obs['time'] = obs_time.strftime('%Y-%m-%d %H:%M:%S')

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
                    bucket_index = floor(hours_diff / bucket_hours)  # Changed from round to floor
                    bucket_center = first_center + timedelta(hours=bucket_index * bucket_hours)
                    bucket_end = bucket_center + timedelta(hours=bucket_hours)  # Full window after center

                    if obs_time < bucket_end:  # Include observations up to the end of the bucket
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

    # Save data
    if save_to_file:
        if save_to_file.endswith('.json'):
            # Save as JSON
            save_response_to_file(save_to_file, {"observations": list(all_observations.values())})
        else:
            # We don't use save_response_to_file as we handled here the headers
            with open(save_to_file, mode='w', newline='') as file:
                writer = csv.DictWriter(file, fieldnames=headers)
                writer.writeheader()
                writer.writerows(all_observations.values())
        print(f"Saved {len(all_observations)} {'observation' if len(all_observations) == 1 else 'observations'} to {save_to_file}")
    else:
        # Track statistics per mission
        mission_stats = {}  # {mission_name: {'files': 0, 'observations': 0}}
        total_observations_written = 0

        # Save bucketed data
        for (bucket_center, mission_name), observations in buckets.items():
            if observations:
                # Format hour to be the actual bucket center
                bucket_hour = int((bucket_center.hour + bucket_hours/2) % 24)

                if output_format == 'csv':
                    output_file = (f"WindBorne_{mission_name}_%04d-%02d-%02d_%02d_%dh.csv" %
                                   (bucket_center.year, bucket_center.month, bucket_center.day,
                                    bucket_hour, bucket_hours))

                    os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)

                    with open(output_file, mode='w', newline='') as file:
                        writer = csv.DictWriter(file, fieldnames=headers)
                        writer.writeheader()
                        writer.writerows(observations.values())
                    total_observations_written += len(observations)
                else:  # little_r format
                    output_file = (f"WindBorne_{mission_name}_%04d-%02d-%02d_%02d:00_%dh.little_r" %
                                   (bucket_center.year, bucket_center.month, bucket_center.day,
                                    bucket_hour, bucket_hours))

                    os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)

                    with open(output_file, 'w') as file:
                        for obs_id, point in observations.items():
                            # Safe conversion functions for numeric values
                            def safe_float(value, default=-888888.0):
                                try:
                                    if value in (None, '', 'None'):
                                        return default
                                    return float(value)
                                except (ValueError, TypeError):
                                    return default

                            # Process numeric values
                            latitude = safe_float(point.get('latitude'))
                            longitude = safe_float(point.get('longitude'))
                            altitude = safe_float(point.get('altitude'))
                            pressure = safe_float(point.get('pressure'))
                            if pressure != -888888.0:
                                pressure *= 100.0  # Convert hPa to Pa
                            temperature = safe_float(point.get('temperature'))
                            if temperature != -888888.0:
                                temperature += 273.15  # Convert C to K
                            humidity = safe_float(point.get('humidity'))
                            speed_u = safe_float(point.get('speed_u'))
                            speed_v = safe_float(point.get('speed_v'))

                            # Format header
                            header_parts = [
                                f"{latitude:20.5f}",
                                f"{longitude:20.5f}",
                                f"{obs_id:<40}",
                                f"{point.get('mission_name', ''):<40}",
                                f"{'FM-35 TEMP':<40}",
                                f"{'WindBorne':<40}",
                                f"{-888888.0:20.5f}",  # elevation
                                f"{-888888:>10d}",
                                f"{0:>10d}",
                                f"{0:>10d}",
                                f"{0:>10d}",
                                f"{0:>10d}",
                                f"{'T':>10}",
                                f"{'F':>10}",
                                f"{'F':>10}",
                                f"{-888888:>10d}",
                                f"{-888888:>10d}",
                                f"{point['time'].replace('-', '').replace(' ', '').replace(':', ''):>20}"
                            ]

                            # Add fixed values for header
                            for _ in range(13):
                                header_parts.extend([f"{-888888.0:13.5f}", f"{0:>7d}"])

                            header = ''.join(header_parts)

                            # Format data record
                            data_parts = [
                                f"{pressure:13.5f}", f"{0:>7d}",
                                f"{altitude:13.5f}", f"{0:>7d}",
                                f"{temperature:13.5f}", f"{0:>7d}",
                                f"{-888888.0:13.5f}", f"{0:>7d}",
                                f"{-888888.0:13.5f}", f"{0:>7d}",
                                f"{-888888.0:13.5f}", f"{0:>7d}",
                                f"{speed_u:13.5f}", f"{0:>7d}",
                                f"{speed_v:13.5f}", f"{0:>7d}",
                                f"{humidity:13.5f}", f"{0:>7d}",
                                f"{-888888.0:13.5f}", f"{0:>7d}"
                            ]

                            data_record = ''.join(data_parts)

                            # End record and tail record are fixed
                            end_record = '-777777.00000      0-777777.00000      0-888888.00000      0-888888.00000      0-888888.00000      0-888888.00000      0-888888.00000      0-888888.00000      0-888888.00000      0-888888.00000      0'
                            tail_record = '     39      0      0'

                            # Write the complete record
                            file.write('\n'.join([header, data_record, end_record, tail_record, '']))
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
