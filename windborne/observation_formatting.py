import os
import json
import csv
from datetime import datetime, timezone


def format_little_r_value(value, fortran_format, align=None):
    """
    Format a value according to a given Fortran format for use in little_r
    """
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


def safe_little_r_float(value, default=-888888.0):
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

    for point in observations:
        # Observation time
        observation_time = datetime.fromtimestamp(point['timestamp'], tz=timezone.utc)

        # Convert and validate fields
        pressure_hpa = safe_little_r_float(point.get('pressure'))
        pressure_pa = pressure_hpa * 100.0

        temperature_c = safe_little_r_float(point.get('temperature'))
        temperature_k = temperature_c + 273.15

        altitude = safe_little_r_float(point.get('altitude'))
        humidity = safe_little_r_float(point.get('humidity'))
        speed_u = safe_little_r_float(point.get('speed_u'))
        speed_v = safe_little_r_float(point.get('speed_v'))

        # Header formatting
        header = ''.join([
            # Latitude: F20.5
            format_little_r_value(point.get('latitude'), 'F20.5'),

            # Longitude: F20.5
            format_little_r_value(point.get('longitude'), 'F20.5'),

            # ID: A40
            format_little_r_value(point.get('id'), 'A40'),

            # Name: A40
            format_little_r_value(point.get('mission_name'), 'A40'),

            # Platform (FM‑Code): A40
            format_little_r_value('FM-35 TEMP', 'A40'),

            # Source: A40
            format_little_r_value('WindBorne', 'A40'),

            # Elevation: F20.5
            format_little_r_value('', 'F20.5'),

            # Valid fields: I10
            format_little_r_value(-888888, 'I10'),

            # Num. errors: I10
            format_little_r_value(0, 'I10'),

            # Num. warnings: I10
            format_little_r_value(0, 'I10'),

            # Sequence number: I10
            format_little_r_value(0, 'I10'),

            # Num. duplicates: I10
            format_little_r_value(0, 'I10'),

            # Is sounding?: L
            format_little_r_value('T', 'L10'),

            # Is bogus?: L
            format_little_r_value('F', 'L10'),

            # Discard?: L
            format_little_r_value('F', 'L10'),

            # Unix time: I10
            # format_value(point['timestamp'], 'I10'),
            format_little_r_value(-888888, 'I10'),

            # Julian day: I10
            format_little_r_value(-888888, 'I10'),

            # Date: A20 YYYYMMDDhhmmss
            format_little_r_value(observation_time.strftime('%Y%m%d%H%M%S'), 'A20', align='right'),

            # SLP, QC: F13.5, I7
            format_little_r_value(-888888.0, 'F13.5') + format_little_r_value(0, 'I7'),

            # Ref Pressure, QC: F13.5, I7
            format_little_r_value(-888888.0, 'F13.5') + format_little_r_value(0, 'I7'),

            # Ground Temp, QC: F13.5, I7
            format_little_r_value(-888888.0, 'F13.5') + format_little_r_value(0, 'I7'),

            # SST, QC: F13.5, I7
            format_little_r_value(-888888.0, 'F13.5') + format_little_r_value(0, 'I7'),

            # SFC Pressure, QC: F13.5, I7
            format_little_r_value(-888888.0, 'F13.5') + format_little_r_value(0, 'I7'),

            # Precip, QC: F13.5, I7
            format_little_r_value(-888888.0, 'F13.5') + format_little_r_value(0, 'I7'),

            # Daily Max T, QC: F13.5, I7
            format_little_r_value(-888888.0, 'F13.5') + format_little_r_value(0, 'I7'),

            # Daily Min T, QC: F13.5, I7
            format_little_r_value(-888888.0, 'F13.5') + format_little_r_value(0, 'I7'),

            # Night Min T, QC: F13.5, I7
            format_little_r_value(-888888.0, 'F13.5') + format_little_r_value(0, 'I7'),

            # 3hr Pres Change, QC: F13.5, I7
            format_little_r_value(-888888.0, 'F13.5') + format_little_r_value(0, 'I7'),

            # 24hr Pres Change, QC: F13.5, I7
            format_little_r_value(-888888.0, 'F13.5') + format_little_r_value(0, 'I7'),

            # Cloud cover, QC: F13.5, I7
            format_little_r_value(-888888.0, 'F13.5') + format_little_r_value(0, 'I7'),

            # Ceiling, QC: F13.5, I7
            format_little_r_value(-888888.0, 'F13.5') + format_little_r_value(0, 'I7'),

            # Precipitable water, QC (see note): F13.5, I7
            format_little_r_value(-888888.0, 'F13.5') + format_little_r_value(0, 'I7'),
            ])

        # Data record formatting
        data_record = ''.join([
            # Pressure (Pa): F13.5
            format_little_r_value(pressure_pa, 'F13.5'),

            # QC: I7
            format_little_r_value(0, 'I7'),

            # Height (m): F13.5
            format_little_r_value(altitude, 'F13.5'),

            # QC: I7
            format_little_r_value(0, 'I7'),

            # Temperature (K): F13.5
            format_little_r_value(temperature_k, 'F13.5'),

            # QC: I7
            format_little_r_value(0, 'I7'),

            # Dew point (K): F13.5
            format_little_r_value(-888888.0, 'F13.5'),

            # QC: I7
            format_little_r_value(0, 'I7'),

            # Wind speed (m/s): F13.5
            format_little_r_value(-888888.0, 'F13.5'),

            # QC: I7
            format_little_r_value(0, 'I7'),

            # Wind direction (deg): F13.5
            format_little_r_value(-888888.0, 'F13.5'),

            # QC: I7
            format_little_r_value(0, 'I7'),

            # Wind U (m/s): F13.5
            format_little_r_value(speed_u, 'F13.5'),

            # QC: I7
            format_little_r_value(0, 'I7'),

            # Wind V (m/s): F13.5
            format_little_r_value(speed_v, 'F13.5'),

            # QC: I7
            format_little_r_value(0, 'I7'),

            # Relative humidity (%): F13.5
            format_little_r_value(humidity, 'F13.5'),

            # QC: I7
            format_little_r_value(0, 'I7'),

            # Thickness (m): F13.5
            format_little_r_value(-888888.0, 'F13.5'),

            # QC: I7
            format_little_r_value(0, 'I7')
        ])

        # End record and tail record
        end_record = '-777777.00000      0-777777.00000      0-888888.00000      0-888888.00000      0-888888.00000      0-888888.00000      0-888888.00000      0-888888.00000      0-888888.00000      0-888888.00000      0'
        tail_record = '     39      0      0'

        # Combine into a complete record
        complete_record = '\n'.join([header, data_record, end_record, tail_record, ''])
        little_r_records.append(complete_record)

    return little_r_records

def convert_to_netcdf(data, curtime, output_filename):
    """
    Convert data to netCDF format for WMO ISARRA program.

    The output format is netCDF and the style (variable names, file names, etc.) are described here:
    https://github.com/synoptic/wmo-uasdc/tree/main/raw_uas_to_netCDF
    """

    # Import necessary libraries
    try:
        import xarray as xr
    except ImportError:
        print("Please install the xarray library to save as netCDF, eg 'python3 -m pip install xarray'.")
        return

    try:
        import pandas as pd
    except ImportError:
        print("Please install the pandas library to save as netCDF, eg 'python3 -m pip install pandas'.")
        return

    try:
        import numpy as np
    except ImportError:
        print("Please install the numpy library to save as netCDF, eg 'python3 -m pip install numpy'.")
        return

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
    if isinstance(data, dict):
        # If input is dictionary, convert to list
        for obs_id, obs_data in data.items():
            clean_data = {k: None if v == 'None' else v for k, v in obs_data.items()}
            data_list.append(clean_data)
    else:
        # If input is already a list
        for obs_data in data:
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

    if len(df['mission_name'].unique()) > 1:
        is_multi_mission = True

    output_file = output_filename

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
        'description': 'Which balloon collected the data'
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