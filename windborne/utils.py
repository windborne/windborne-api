from .config import CLIENT_ID, API_KEY

import os
import requests
import jwt
import time
import re
import uuid
from datetime import datetime, timezone
import dateutil.parser
import boto3
import io
import json
import csv

import numpy as np

# Check if input is uuid v4
def is_valid_uuid_v4(client_id):
    try:
        return str(uuid.UUID(client_id, version=4)) == client_id
    except ValueError:
        return False

# Check if client id input format
def is_valid_client_id_format(client_id):
    return re.fullmatch(r"[a-z0-9_]+", client_id) is not None

# Authenticate requests using a JWT | no reveal of underlying key
def make_api_request(url, params=None, return_type=None):
    # Check if credentials are set
    if not CLIENT_ID and not API_KEY:
        print("To access the WindBorne API, you need to set your Client ID and API key by setting the environment variables WB_CLIENT_ID and WB_API_KEY.")
        print("--------------------------------------")
        print("You may refer to https://windbornesystems.com/docs/api/cli#introduction\n"
              "for instructions on how to set your credentials as environment variables for CLI and Code usage\n\n"
              "and to https://windbornesystems.com/docs/api/pip_data#introduction\n"
              "for instruction on how to set your credentials for code usage.")
        print("--------------------------------------")
        print("To get an API key, email data@windbornesystems.com.")
        exit(80)
    elif not CLIENT_ID:
        print("To access the WindBorne API, you need to set your Client ID by setting the environment variable WB_CLIENT_ID.")
        print("--------------------------------------")
        print("You may refer to https://windbornesystems.com/docs/api/cli#introduction\n"
              "for instructions on how to set your credentials as environment variables for CLI and Code usage\n\n"
              "and to https://windbornesystems.com/docs/api/pip_data#introduction\n"
              "for instruction on how to set your credentials for code usage.")
        print("--------------------------------------")
        print("To get an API key, email data@windbornesystems.com.")
        exit(90)
    elif not API_KEY:
        print("To access the WindBorne API, you need to set your CAPI key by setting the environment variable WB_API_KEY.")
        print("--------------------------------------")
        print("You may refer to https://windbornesystems.com/docs/api/cli#introduction\n"
              "for instructions on how to set your credentials as environment variables for CLI and Code usage\n\n"
              "and to https://windbornesystems.com/docs/api/pip_data#introduction\n"
              "for instruction on how to set your credentials for code usage.")
        print("--------------------------------------")
        print("To get an API key, email data@windbornesystems.com.")
        exit(91)
    # Check if credentials are swapped
    elif len(CLIENT_ID) in [32, 35]:
        print("Your Client ID and API Key are swapped.")
        print("--------------------------------------")
        print("Swap them or modify them accordingly to get access to WindBorne API.")
        print("--------------------------------------")
        print("You may refer to https://windbornesystems.com/docs/api/cli#introduction\n"
              "for instructions on how to set your credentials as environment variables for CLI and Code usage\n\n"
              "and to https://windbornesystems.com/docs/api/pip_data#introduction\n"
              "for instruction on how to set your credentials for code usage.")
        print("--------------------------------------")
        print(f"Current Client ID: {CLIENT_ID}")
        print(f"Current API Key: {API_KEY}")
        exit(95)

    # Validate WB_CLIENT_ID format
    if not (is_valid_uuid_v4(CLIENT_ID) or is_valid_client_id_format(CLIENT_ID)):
        print("Your Client ID is misformatted.")
        print("--------------------------------------")
        print("It should either be a valid UUID v4 or consist of only lowercase letters, digits, and underscores ([a-z0-9_]).")
        print("--------------------------------------")
        print("You may refer to https://windbornesystems.com/docs/api/cli#introduction\n"
              "for instructions on how to set your credentials as environment variables for CLI and Code usage\n\n"
              "and to https://windbornesystems.com/docs/api/pip_data#introduction\n"
              "for instruction on how to set your credentials for code usage.")
        print("--------------------------------------")
        print(f"Current Client ID: {CLIENT_ID}")
        exit(92)

    # Validate WB_API_KEY for both newer and older formats
    if API_KEY.startswith("wb_"):
        if len(API_KEY) != 35:
            print("Your API key is misformatted.")
            print("--------------------------------------")
            print("API keys starting with 'wb_' must be 35 characters long (including the 'wb_' prefix).")
            print("--------------------------------------")
            print("You may refer to https://windbornesystems.com/docs/api/cli#introduction\n"
                  "for instructions on how to set your credentials as environment variables for CLI and Code usage\n\n"
                  "and to https://windbornesystems.com/docs/api/pip_data#introduction\n"
                  "for instruction on how to set your credentials for code usage.")
            print("--------------------------------------")
            print(f"Current API key: {API_KEY}")
            exit(93)
    elif len(API_KEY) != 32:  # For early tokens
        print("Your API key is misformatted.")
        print("--------------------------------------")
        print("API keys created in 2023 or earlier must be exactly 32 characters long.")
        print("--------------------------------------")
        print("You may refer to https://windbornesystems.com/docs/api/cli#introduction\n"
              "for instructions on how to set your credentials as environment variables for CLI and Code usage\n\n"
              "and to https://windbornesystems.com/docs/api/pip_data#introduction\n"
              "for instruction on how to set your credentials for code usage.")
        print("--------------------------------------")
        print(f"Current API key: {API_KEY}")
        exit(94)

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

        if return_type is None:
            # For Data API
            return response.json()
        elif return_type == 'all':
            # For Forecasts API (except tcs) --> return whole response not .json to obtain S3 url
            return response
    except requests.exceptions.HTTPError as http_err:
        if http_err.response.status_code == 403:
            print("--------------------------------------")
            print("We couldn't authenticate your request.")
            print("--------------------------------------")
            print("Please make sure you have properly set your WB_CLIENT_ID and WB_API_KEY.\n")
            print("You can verify this by running\necho $WB_CLIENT_ID and echo $WB_API_KEY in your terminal.\n")
            print("To get an API key, email data@windbornesystems.com.")
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
                    print(f"We couldn't find a mission with id: {mission_id}")
        elif http_err.response.status_code == 502:
            retries = 1
            while response.status_code == 502 and retries < 5:
                print("502 Bad Gateway, sleeping and retrying")
                time.sleep(2**retries)
                response = requests.get(url, auth=(CLIENT_ID, signed_token))
                retries += 1
        else:
            print(f"HTTP error occurred\n\n{http_err}")
            if params:
                print("\nParameters provided:")
                for key, value in params.items():
                    print(f"  {key}: {value}")
        exit(http_err.response.status_code)
    except requests.exceptions.ConnectionError as conn_err:
        print(f"Connection error occurred\n\n{conn_err}")
    except requests.exceptions.Timeout as timeout_err:
        print(f"Timeout error occurred\n\n{timeout_err}")
    except requests.exceptions.RequestException as req_err:
        print(f"An error occurred\n\n{req_err}")

# Supported date formats
# YYYY-MM-DD HH:MM:SS, YYYY-MM-DD_HH:MM and ISO strings
def to_unix_timestamp(date_string):
    """
    Converts a date string or integer to a UNIX timestamp.
    Supports various date formats and handles future dates gracefully.

    Args:
        date_string (str | int | None): The date string to convert or an integer UNIX timestamp.

    Returns:
        int | None: The UNIX timestamp or None if the input is None.
    """
    if date_string is None:
        return None
    if isinstance(date_string, int):
        return date_string  # If it's already an integer, return as is
    if isinstance(date_string, str):
        # Supported date formats
        formats = [
            "%Y-%m-%d %H:%M:%S",        # e.g., 2024-12-05 14:48:00
            "%Y-%m-%d_%H:%M",           # e.g., 2024-12-05_14:48
            "%Y-%m-%dT%H:%M:%S.%fZ",    # e.g., 2024-12-05T14:48:00.000Z
        ]
        current_time = datetime.now(timezone.utc)
        for fmt in formats:
            try:
                dt = datetime.strptime(date_string, fmt).replace(tzinfo=timezone.utc)
                if dt > current_time:
                    print(f"How would it be to live in {dt} ?\n")
                    print("Looks like you are coming from the future!\n")
                    exit(1111)
                return int(dt.timestamp())
            except ValueError:
                continue

        # If no formats match, raise an error
        print("Invalid date format. Please use one of the supported formats:\n"
              "- YYYY-MM-DD HH:MM:SS\n"
              "- YYYY-MM-DD_HH:MM\n"
              "- YYYY-MM-DDTHH:MM:SS.fffZ")
        exit(11)

# Supported date format
# Compact format YYYYMMDDHH
def parse_time(time, init_time_flag=None):
    """
    Parse and validate initialization time with support for multiple formats.
    Returns validated initialization time in ISO format, or None if invalid.
    """
    if time is None:
        return None

    try:
        # Try parsing compact format first (YYYYMMDDHH)
        if re.match(r'^\d{10}$', time):
            try:
                parsed_date = datetime.strptime(time, "%Y%m%d%H")
            except (ValueError, OverflowError):
                print(f"Invalid date values in: {time}")
                print("Make sure your date values are valid")
                exit(2)

            if init_time_flag and parsed_date.hour not in [0, 6, 12, 18]:
                print("Initialization time hour must be 00, 06, 12, or 18")
                exit(2)
        else:
            try:
                parsed_date = dateutil.parser.parse(time)
            except (ValueError, OverflowError, TypeError):
                print(f"Invalid date format: {time}\n")
                print("Please use one of these formats:")
                print("  - Compact: 'YYYYMMDDHH' (e.g., 2024073112)")
                print("  - ISO: 'YYYY-MM-DDTHH' or 'YYYY-MM-DDTHH:00:00'")
                print("  - Initialization time hour must be 00, 06, 12, or 18")
                exit(2)

        if parsed_date > datetime.now():
            print(f"How would it be to live in {parsed_date} ?\n")
            print("Looks like you are coming from the future!\n")
            exit(1111)

        return parsed_date.strftime('%Y-%m-%dT%H:00:00')

    except Exception:
        print(f"Invalid date format: {time}")
        print("Please check your input format and try again")
        exit(2)

# Save API response data to a file in either JSON or CSV format
def save_csv_json(save_to_file, response, csv_data_key=None):
    """
    Save Data API response data to a file in either JSON or CSV format.

    Args:
        save_to_file (str): The file path where the response will be saved.
        response (dict or list): The response data to save.
        csv_data_key (str, optional): Key to extract data for CSV. Defaults to None.
    """
    # Create directory path if it doesn't exist
    directory = os.path.dirname(save_to_file)
    if directory and not os.path.isdir(directory):
        os.makedirs(directory, exist_ok=True)

    if '.' not in save_to_file:
        print("You have to provide a file type for your filename.")
        print("Supported formats:")
        print("  - .csv")
        print("  - .json")
        exit(2)
    elif not response:
        print("There are no available data to save to file.")
        exit(1)
    elif save_to_file.lower().endswith('.json'):
        with open(save_to_file, 'w', encoding='utf-8') as f:
            json.dump(response, f, indent=4)
        print("Saved to", save_to_file)
    elif save_to_file.lower().endswith('.csv'):
        # Extract data for CSV if a key is provided
        data = response if not csv_data_key else response.get(csv_data_key, [])
        if not data:
            print("No data available to save to CSV.")
            return
        # Handle nested list case (for forecasts)
        if isinstance(data, list) and data and isinstance(data[0], list):
            data = data[0]  # Take the first list from nested lists
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
            exit(5)

        # Write data to CSV
        with open(save_to_file, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=headers)
            writer.writeheader()
            for row in data:
                # If no value available write 'None'
                row_data = {k: 'None' if v is None or v == '' else v for k, v in row.items()}
                writer.writerow(row_data)
            print("Saved to", save_to_file)
    else:
        print("Unsupported file format. Please use either .json or .csv.")
        exit(4)

def convert_to_netcdf(data, curtime, output_filename=None):
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

    # Put the data in a panda dataframe in order to easily push to xarray then netcdf output
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
    # Handle dropsondes
    mission_name = str(df['mission_name'].iloc[0]) if (not df.empty and not pd.isna(df['mission_name'].iloc[0])) else ' '

    is_multi_mission = False

    if output_filename:
        output_file = output_filename
        is_multi_mission = True  # we should calculate this directly, rather than relying on the filename
    else:
        output_file = f"WindBorne_{mission_name}_{mt.year:04d}-{mt.month:02d}-{mt.day:02d}_{mt.hour:02d}.nc"

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
    variables_to_drop = ['humidity', 'speed_x', 'speed_y', 'timestamp']
    if 'id' in ds and pd.isna(ds['id']).all():
        variables_to_drop.append('id')

    existing_vars = [var for var in variables_to_drop if var in ds]
    ds = ds.drop_vars(existing_vars)

    # Rename the variables
    ds = ds.rename(rename_dict)

    # Adding attributes to variables in the xarray dataset
    ds['time'].attrs = {
        'units': 'seconds since 1970-01-01T00:00:00',
        'long_name': 'Time', '_FillValue': float('nan'),
        'processing_level': ''
    }

    ds['lat'].attrs = {
        'units': 'degrees_north',
        'long_name': 'Latitude',
        '_FillValue': float('nan'),
        'processing_level': ''
    }
    ds['lon'].attrs = {
        'units': 'degrees_east',
        'long_name': 'Longitude',
        '_FillValue': float('nan'),
        'processing_level': ''
    }
    ds['altitude'].attrs = {
        'units': 'meters_above_sea_level',
        'long_name': 'Altitude',
        '_FillValue': float('nan'),
        'processing_level': ''
    }
    ds['air_temperature'].attrs = {
        'units': 'Kelvin',
        'long_name': 'Air Temperature',
        '_FillValue': float('nan'),
        'processing_level': ''
    }
    ds['wind_speed'].attrs = {
        'units': 'm/s',
        'long_name': 'Wind Speed',
        '_FillValue': float('nan'),
        'processing_level': ''
    }
    ds['wind_direction'].attrs = {
        'units': 'degrees',
        'long_name': 'Wind Direction',
        '_FillValue': float('nan'),
        'processing_level': ''
    }
    ds['humidity_mixing_ratio'].attrs = {
        'units': 'kg/kg',
        'long_name': 'Humidity Mixing Ratio',
        '_FillValue': float('nan'),
        'processing_level': ''
    }
    ds['air_pressure'].attrs = {
        'units': 'Pa',
        'long_name': 'Atmospheric Pressure',
        '_FillValue': float('nan'),
        'processing_level': ''
    }
    ds['speed_u'].attrs = {
        'units': 'm/s',
        'long_name': 'Wind speed in direction of increasing longitude',
        '_FillValue': float('nan'),
        'processing_level': ''
    }
    ds['speed_v'].attrs = {
        'units': 'm/s',
        'long_name': 'Wind speed in direction of increasing latitude',
        '_FillValue': float('nan'),
        'processing_level': ''
    }
    ds['specific_humidity'].attrs = {
        'units': 'mg/kg',
        'long_name': 'Specific Humidity',
        '_FillValue': float('nan'),
        'processing_level': '',
        'Conventions': "CF-1.8, WMO-CF-1.0"
    }
    ds['mission_name'].attrs = {
        'long_name': 'Mission name',
        'description': 'Which balloon collected the data',
        '_FillValue': ''
    }

    # Add Global Attributes synonymous across all UASDC providers
    if not is_multi_mission:
        ds.attrs['wmo__cf_profile'] = "FM 303-2024"
        ds.attrs['featureType'] = "trajectory"

    # Add Global Attributes unique to Provider
    ds.attrs['platform_name'] = "WindBorne Global Sounding Balloon"
    if not is_multi_mission:
        ds.attrs['flight_id'] = mission_name

    ds.attrs['site_terrain_elevation_height'] = 'not applicable'
    ds.attrs['processing_level'] = "b1"
    ds.to_netcdf(output_file)

def format_value(value, fortran_format, align=None):
    if fortran_format[0] == 'F':
        length, decimal_places = fortran_format[1:].split('.')
        if value is None or value == '':
            return ' ' * int(length)

        # turn into a string of length characters, with decimal_places decimal places
        return f"{value:>{length}.{decimal_places}f}"[:int(length)]

    if fortran_format[0] == 'I':
        length = int(fortran_format[1:])
        if value is None or value == '':
            return ' ' * length

        return f"{value:>{length}d}"[:int(length)]

    if fortran_format[0] == 'A':
        length = int(fortran_format[1:])
        if value is None:
            return ' ' * length

        if align == 'right':
            return str(value)[:length].rjust(length, ' ')

        return str(value)[:length].ljust(length, ' ')

    if fortran_format[0] == 'L':
        if value and value in ['T', 't', 'True', 'true', '1', True]:
            value = 'T'
        else:
            value = 'F'

        length = int(fortran_format[1:])

        return value.rjust(length, ' ')

    raise ValueError(f"Unknown format: {fortran_format}")

def safe_float(value, default=-888888.0):
    """
    Convert a value to float. If the value is None, empty, or invalid, return the default.
    """
    try:
        return float(value) if value not in (None, '', 'None') else default
    except (ValueError, TypeError):
        return default

def format_little_r(observations):
    """
    Convert observations to Little_R format.

    Args:
        observations (list): List of observation dictionaries

    Returns:
        list: Formatted Little_R records
    """
    little_r_records = []

    for obs_id, point in observations:
        # Observation time
        observation_time = datetime.fromtimestamp(point['timestamp'], tz=timezone.utc)

        # Convert and validate fields
        pressure_hpa = safe_float(point.get('pressure'))
        pressure_pa = pressure_hpa * 100.0

        temperature_c = safe_float(point.get('temperature'))
        temperature_k = temperature_c + 273.15

        altitude = safe_float(point.get('altitude'))
        humidity = safe_float(point.get('humidity'))
        speed_u = safe_float(point.get('speed_u'))
        speed_v = safe_float(point.get('speed_v'))

        # Header formatting
        header = ''.join([
            # Latitude: F20.5
            format_value(point.get('latitude'), 'F20.5'),

            # Longitude: F20.5
            format_value(point.get('longitude'), 'F20.5'),

            # ID: A40
            format_value(point.get('id'), 'A40'),

            # Name: A40
            format_value(point.get('mission_name'), 'A40'),

            # Platform (FM‑Code): A40
            format_value('FM-35 TEMP', 'A40'),

            # Source: A40
            format_value('WindBorne', 'A40'),

            # Elevation: F20.5
            format_value('', 'F20.5'),

            # Valid fields: I10
            format_value(-888888, 'I10'),

            # Num. errors: I10
            format_value(0, 'I10'),

            # Num. warnings: I10
            format_value(0, 'I10'),

            # Sequence number: I10
            format_value(0, 'I10'),

            # Num. duplicates: I10
            format_value(0, 'I10'),

            # Is sounding?: L
            format_value('T', 'L10'),

            # Is bogus?: L
            format_value('F', 'L10'),

            # Discard?: L
            format_value('F', 'L10'),

            # Unix time: I10
            # format_value(point['timestamp'], 'I10'),
            format_value(-888888, 'I10'),

            # Julian day: I10
            format_value(-888888, 'I10'),

            # Date: A20 YYYYMMDDhhmmss
            format_value(observation_time.strftime('%Y%m%d%H%M%S'), 'A20', align='right'),

            # SLP, QC: F13.5, I7
            format_value(-888888.0, 'F13.5') + format_value(0, 'I7'),

            # Ref Pressure, QC: F13.5, I7
            format_value(-888888.0, 'F13.5') + format_value(0, 'I7'),

            # Ground Temp, QC: F13.5, I7
            format_value(-888888.0, 'F13.5') + format_value(0, 'I7'),

            # SST, QC: F13.5, I7
            format_value(-888888.0, 'F13.5') + format_value(0, 'I7'),

            # SFC Pressure, QC: F13.5, I7
            format_value(-888888.0, 'F13.5') + format_value(0, 'I7'),

            # Precip, QC: F13.5, I7
            format_value(-888888.0, 'F13.5') + format_value(0, 'I7'),

            # Daily Max T, QC: F13.5, I7
            format_value(-888888.0, 'F13.5') + format_value(0, 'I7'),

            # Daily Min T, QC: F13.5, I7
            format_value(-888888.0, 'F13.5') + format_value(0, 'I7'),

            # Night Min T, QC: F13.5, I7
            format_value(-888888.0, 'F13.5') + format_value(0, 'I7'),

            # 3hr Pres Change, QC: F13.5, I7
            format_value(-888888.0, 'F13.5') + format_value(0, 'I7'),

            # 24hr Pres Change, QC: F13.5, I7
            format_value(-888888.0, 'F13.5') + format_value(0, 'I7'),

            # Cloud cover, QC: F13.5, I7
            format_value(-888888.0, 'F13.5') + format_value(0, 'I7'),

            # Ceiling, QC: F13.5, I7
            format_value(-888888.0, 'F13.5') + format_value(0, 'I7'),

            # Precipitable water, QC (see note): F13.5, I7
            format_value(-888888.0, 'F13.5') + format_value(0, 'I7'),
            ])

        # Data record formatting
        data_record = ''.join([
            # Pressure (Pa): F13.5
            format_value(pressure_pa, 'F13.5'),

            # QC: I7
            format_value(0, 'I7'),

            # Height (m): F13.5
            format_value(altitude, 'F13.5'),

            # QC: I7
            format_value(0, 'I7'),

            # Temperature (K): F13.5
            format_value(temperature_k, 'F13.5'),

            # QC: I7
            format_value(0, 'I7'),

            # Dew point (K): F13.5
            format_value(-888888.0, 'F13.5'),

            # QC: I7
            format_value(0, 'I7'),

            # Wind speed (m/s): F13.5
            format_value(-888888.0, 'F13.5'),

            # QC: I7
            format_value(0, 'I7'),

            # Wind direction (deg): F13.5
            format_value(-888888.0, 'F13.5'),

            # QC: I7
            format_value(0, 'I7'),

            # Wind U (m/s): F13.5
            format_value(speed_u, 'F13.5'),

            # QC: I7
            format_value(0, 'I7'),

            # Wind V (m/s): F13.5
            format_value(speed_v, 'F13.5'),

            # QC: I7
            format_value(0, 'I7'),

            # Relative humidity (%): F13.5
            format_value(humidity, 'F13.5'),

            # QC: I7
            format_value(0, 'I7'),

            # Thickness (m): F13.5
            format_value(-888888.0, 'F13.5'),

            # QC: I7
            format_value(0, 'I7')
        ])

        # End record and tail record
        end_record = '-777777.00000      0-777777.00000      0-888888.00000      0-888888.00000      0-888888.00000      0-888888.00000      0-888888.00000      0-888888.00000      0-888888.00000      0-888888.00000      0'
        tail_record = '     39      0      0'

        # Combine into a complete record
        complete_record = '\n'.join([header, data_record, end_record, tail_record, ''])
        little_r_records.append(complete_record)

    return little_r_records

# Download and save a file in .npy upon provided an S3 link
def download_and_save_npy(save_to_file, response):
    """
    Downloads data from a presigned S3 url contained in a response and saves it as a .npy file.

    Args:
        save_to_file (str): Path where to save the .npy file
        response (str): Response that contains the S3 url to download the data from

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Download the file
        print(f"Downloading data")
        # Load the data into memory
        data = np.load(io.BytesIO(response.content))

        # Save the data
        np.save(save_to_file, data)
        print(f"Data Successfully saved to {save_to_file}")
        return True

    except requests.exceptions.RequestException as e:
        print(f"Error downloading the file: {e}")
        return False
    except Exception as e:
        print(f"Error processing the file: {e}")
        return False

# Download and save a file in .nc upon provided an S3 link
def download_and_save_nc(save_to_file, response):
    """
    Downloads data from a presigned S3 url contained in a response and saves it as a .nc file.

    Args:
        save_to_file (str): Path where to save the .nc file
        response (str): Response that contains the S3 url to download the data from

    Returns:
        bool: True if successful, False otherwise
    """

    # Add .nc extension if not present
    if not save_to_file.endswith('.nc'):
        save_to_file = save_to_file + '.nc'

    try:
        # Save the content directly to file
        with open(save_to_file, 'wb') as f:
            f.write(response.content)
        print(f"Data Successfully saved to {save_to_file}")
        return True

    except requests.exceptions.RequestException as e:
        print(f"Error downloading the file: {e}")
        return False
    except Exception as e:
        print(f"Error processing the file: {e}")
        return False

def save_as_geojson(filename, cyclone_data):
    """Convert and save cyclone data as GeoJSON, handling meridian crossing."""
    features = []
    for cyclone_id, tracks in cyclone_data.items():
        # Initialize lists to store line segments
        line_segments = []
        current_segment = []

        for i in range(len(tracks)):
            lon = float(tracks[i]['longitude'])
            lat = float(tracks[i]['latitude'])

            if not current_segment:
                current_segment.append([lon, lat])
                continue

            prev_lon = current_segment[-1][0]

            # Check if we've crossed the meridian (large longitude jump)
            if abs(lon - prev_lon) > 180:
                # If previous longitude was positive and current is negative
                if prev_lon > 0 and lon < 0:
                    # Add point at 180° with same latitude
                    current_segment.append([180, lat])
                    line_segments.append(current_segment)
                    # Start new segment at -180°
                    current_segment = [[-180, lat], [lon, lat]]
                # If previous longitude was negative and current is positive
                elif prev_lon < 0 and lon > 0:
                    # Add point at -180° with same latitude
                    current_segment.append([-180, lat])
                    line_segments.append(current_segment)
                    # Start new segment at 180°
                    current_segment = [[180, lat], [lon, lat]]
            else:
                current_segment.append([lon, lat])

        # Add the last segment if it's not empty
        if current_segment:
            line_segments.append(current_segment)

        # Create a MultiLineString feature with all segments
        feature = {
            "type": "Feature",
            "properties": {
                "cyclone_id": cyclone_id,
                "start_time": tracks[0]['time'],
                "end_time": tracks[-1]['time']
            },
            "geometry": {
                "type": "MultiLineString",
                "coordinates": line_segments
            }
        }
        features.append(feature)

    geojson = {
        "type": "FeatureCollection",
        "features": features
    }

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(geojson, f, indent=4)
    print("Saved to", filename)

def save_as_gpx(filename, cyclone_data):
    """Convert and save cyclone data as GPX, handling meridian crossing."""
    gpx = '<?xml version="1.0" encoding="UTF-8"?>\n'
    gpx += '<gpx version="1.1" creator="Windborne" xmlns="http://www.topografix.com/GPX/1/1">\n'

    for cyclone_id, tracks in cyclone_data.items():
        gpx += f'  <trk>\n    <name>{cyclone_id}</name>\n'

        current_segment = []
        segment_count = 1

        for i in range(len(tracks)):
            lon = float(tracks[i]['longitude'])
            lat = float(tracks[i]['latitude'])

            if not current_segment:
                current_segment.append(tracks[i])
                continue

            prev_lon = float(current_segment[-1]['longitude'])

            # Check if we've crossed the meridian
            if abs(lon - prev_lon) > 180:
                # Write the current segment
                gpx += '    <trkseg>\n'
                for point in current_segment:
                    gpx += f'      <trkpt lat="{point["latitude"]}" lon="{point["longitude"]}">\n'
                    gpx += f'        <time>{point["time"]}</time>\n'
                    gpx += '      </trkpt>\n'
                gpx += '    </trkseg>\n'

                # Start new segment
                current_segment = [tracks[i]]
                segment_count += 1
            else:
                current_segment.append(tracks[i])

        # Write the last segment if it's not empty
        if current_segment:
            gpx += '    <trkseg>\n'
            for point in current_segment:
                gpx += f'      <trkpt lat="{point["latitude"]}" lon="{point["longitude"]}">\n'
                gpx += f'        <time>{point["time"]}</time>\n'
                gpx += '      </trkpt>\n'
            gpx += '    </trkseg>\n'

        gpx += '  </trk>\n'

    gpx += '</gpx>'

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(gpx)
    print(f"Saved to {filename}")

def save_as_kml(filename, cyclone_data):
    """Convert and save cyclone data as KML, handling meridian crossing."""
    kml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    kml += '<kml xmlns="http://www.opengis.net/kml/2.2">\n<Document>\n'

    for cyclone_id, tracks in cyclone_data.items():
        kml += f'  <Placemark>\n    <name>{cyclone_id}</name>\n    <MultiGeometry>\n'

        current_segment = []

        for i in range(len(tracks)):
            lon = float(tracks[i]['longitude'])
            lat = float(tracks[i]['latitude'])

            if not current_segment:
                current_segment.append(tracks[i])
                continue

            prev_lon = float(current_segment[-1]['longitude'])

            # Check if we've crossed the meridian
            if abs(lon - prev_lon) > 180:
                # Write the current segment
                kml += '      <LineString>\n        <coordinates>\n'
                coordinates = [f'          {track["longitude"]},{track["latitude"]},{0}'
                               for track in current_segment]
                kml += '\n'.join(coordinates)
                kml += '\n        </coordinates>\n      </LineString>\n'

                # Start new segment
                current_segment = [tracks[i]]
            else:
                current_segment.append(tracks[i])

        # Write the last segment if it's not empty
        if current_segment:
            kml += '      <LineString>\n        <coordinates>\n'
            coordinates = [f'          {track["longitude"]},{track["latitude"]},{0}'
                           for track in current_segment]
            kml += '\n'.join(coordinates)
            kml += '\n        </coordinates>\n      </LineString>\n'

        kml += '    </MultiGeometry>\n  </Placemark>\n'

    kml += '</Document>\n</kml>'

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(kml)
    print(f"Saved to {filename}")

def save_as_little_r(filename, cyclone_data):
    """Convert and save cyclone data in little_R format."""
    with open(filename, 'w', encoding='utf-8') as f:
        for cyclone_id, tracks in cyclone_data.items():
            for track in tracks:
                # Parse the time
                dt = datetime.fromisoformat(track['time'].replace('Z', '+00:00'))

                # Header line 1
                header1 = f"{float(track['latitude']):20.5f}{float(track['longitude']):20.5f}{'HMS':40}"
                header1 += f"{0:10d}{0:10d}{0:10d}"  # Station ID numbers
                header1 += f"{dt.year:10d}{dt.month:10d}{dt.day:10d}{dt.hour:10d}{0:10d}"
                header1 += f"{0:10d}{0:10.3f}{cyclone_id:40}"
                f.write(header1 + '\n')

                # Header line 2
                header2 = f"{0:20.5f}{1:10d}{0:10.3f}"
                f.write(header2 + '\n')

                # Data line format: p, z, t, d, s, d (pressure, height, temp, dewpoint, speed, direction)
                # We'll only include position data
                data_line = f"{-888888.0:13.5f}{float(track['latitude']):13.5f}{-888888.0:13.5f}"
                data_line += f"{-888888.0:13.5f}{-888888.0:13.5f}{float(track['longitude']):13.5f}"
                data_line += f"{0:7d}"  # End of data line marker
                f.write(data_line + '\n')

                # End of record line
                f.write(f"{-777777.0:13.5f}\n")

    print("Saved to", filename)

def sync_to_s3(data, bucket_name, object_name):
    s3 = boto3.client("s3")
    s3.put_object(Body=str(data), Bucket=bucket_name, Key=object_name)