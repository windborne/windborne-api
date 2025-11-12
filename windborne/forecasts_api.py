import requests

from .utils import (
    parse_time,
    save_arbitrary_response,
    print_table
)

from .api_request import make_api_request, API_BASE_URL
from .track_formatting import save_track

FORECASTS_API_BASE_URL = f"{API_BASE_URL}/forecasts/v1"
TCS_SUPPORTED_FORMATS = ('.csv', '.json', '.geojson', '.gpx', '.kml', '.little_r')


# Run information
def get_run_information(initialization_time=None, ensemble_member=None, print_response=False, model='wm'):
    """
    Get run information for a given model initialization.

    Args:
        initialization_time (str, optional): Initialization time (ISO 8601). If omitted, latest is used.
        ensemble_member (str|int, optional): Ensemble member (e.g., "mean" or member number as string/int)
        print_response (bool, optional): Whether to print a formatted summary
        model (str, optional): Forecast model (e.g., wm, wm4, wm4-intra, ecmwf-det)

    Returns:
        dict: API response containing initialization_time, forecast_zero, in_progress, and available list
    """

    params = {}
    if initialization_time:
        params['initialization_time'] = parse_time(initialization_time, init_time_flag=True)
    if ensemble_member:
        params['ens_member'] = ensemble_member

    response = make_api_request(f"{FORECASTS_API_BASE_URL}/{model}/run_information", params=params)

    if print_response and response is not None:
        print("Initialization time:", response.get('initialization_time'))
        print("Forecast zero:", response.get('forecast_zero'))
        in_progress = response.get('in_progress')
        if in_progress is not None:
            print("In progress:", in_progress)

        print("Available forecast hours:")
        available = response.get('available', [])
        for item in available:
            hour = item.get('forecast_hour')
            created_at = item.get('created_at')
            archived = item.get('archived')

            # eg:
            # - 0 (created at 2025-10-29T00:00:00.000Z, archived)
            # - 0 (created at 2025-10-29T00:00:00.000Z)
            # - 0 (archived)

            if created_at and archived:
                print(f" - {hour} (created at {created_at}, archived)")
            elif created_at and not archived:
                print(f" - {hour} (created at {created_at})")
            elif not created_at and archived:
                print(f" - {hour} (archived)")
            else:
                print(f" - {hour} (archived)")

    return response


# Variables
def get_variables(print_response=False, model='wm'):
    """
    Get available variables and levels for a given model.

    Args:
        print_response (bool, optional): Whether to print a formatted summary
        model (str, optional): Forecast model (e.g., wm, wm4, wm4-intra, ecmwf-det)

    Returns:
        dict: API response containing sfc_variables, upper_variables, and levels
    """

    response = make_api_request(f"{FORECASTS_API_BASE_URL}/{model}/variables")

    if print_response and response is not None:
        sfc = response.get('sfc_variables', [])
        upper = response.get('upper_variables', [])
        levels = response.get('levels', [])

        print("Surface variables:")
        for v in sfc:
            print(f" - {v}")

        if len(upper) > 0:
            print("Upper variables:")
            for v in upper:
                print(f" - {v}")
        else:
            print("No upper variables available")

        if len(levels) > 0:
            print("Levels:")
            for lvl in levels:
                print(f" - {lvl}")
        else:
            print("No levels available")

    return response

# Point forecasts
def get_point_forecasts(coordinates, min_forecast_time=None, max_forecast_time=None, min_forecast_hour=None, max_forecast_hour=None, initialization_time=None, output_file=None, print_response=False, model='wm'):
    """
    Get point forecasts from the API.

    Args:
        coordinates (str, list): Coordinates in the format "latitude,longitude"
                                  or a list of tuples, lists, or dictionaries with keys 'latitude' and 'longitude'
        min_forecast_time (str, optional): Minimum forecast time in ISO 8601 format (YYYY-MM-DDTHH:00:00)
        max_forecast_time (str, optional): Maximum forecast time in ISO 8601 format (YYYY-MM-DDTHH:00:00)
        min_forecast_hour (int, optional): Minimum forecast hour
        max_forecast_hour (int, optional): Maximum forecast hour
        initialization_time (str, optional): Initialization time in ISO 8601 format (YYYY-MM-DDTHH:00:00)
        output_file (str, optional): Path to save the response data
                                      Supported formats: .json, .csv
        print_response (bool, optional): Whether to print the response data
    """

    # coordinates should be formatted as a semi-colon separated list of latitude,longitude tuples, eg 37,-121;40.3,-100
    formatted_coordinates = coordinates

    if isinstance(coordinates, list):
        coordinate_items = []
        for coordinate in coordinates:
            if isinstance(coordinate, tuple) or isinstance(coordinate, list):
                if len(coordinate) != 2:
                    print("Coordinates should be tuples or lists with two elements: latitude and longitude.")
                    return

                coordinate_items.append(f"{coordinate[0]},{coordinate[1]}")
            elif isinstance(coordinate, str):
                coordinate_items.append(coordinate)
            elif isinstance(coordinate, dict):
                if 'latitude' in coordinate and 'longitude' in coordinate:
                    coordinate_items.append(f"{coordinate['latitude']},{coordinate['longitude']}")
                elif 'lat' in coordinate and 'lon' in coordinate:
                    coordinate_items.append(f"{coordinate['lat']},{coordinate['lon']}")
                elif 'lat' in coordinate and 'long' in coordinate:
                    coordinate_items.append(f"{coordinate['lat']},{coordinate['long']}")
                elif 'lat' in coordinate and 'lng' in coordinate:
                    coordinate_items.append(f"{coordinate['lat']},{coordinate['lng']}")
                else:
                    print("Coordinates should be dictionaries with keys 'latitude' and 'longitude'.")
                    return

        formatted_coordinates = ";".join(coordinate_items)

    formatted_coordinates = formatted_coordinates.replace(" ", "")

    if not formatted_coordinates or formatted_coordinates == "":
        print("To get points forecasts you must provide coordinates.")
        return

    params = {
        "coordinates": formatted_coordinates
    }

    if min_forecast_time:
        params["min_forecast_time"] = parse_time(min_forecast_time)
    if max_forecast_time:
        params["max_forecast_time"] = parse_time(max_forecast_time)
    if min_forecast_hour:
        params["min_forecast_hour"] = int(min_forecast_hour)
    if max_forecast_hour:
        params["max_forecast_hour"] = int(max_forecast_hour)
    if initialization_time:
        initialization_time = parse_time(initialization_time,init_time_flag=True)
        params["initialization_time"] = initialization_time

    if print_response:
        print("Generating point forecast...")

    response = make_api_request(f"{FORECASTS_API_BASE_URL}/{model}/point_forecast", params=params)

    if output_file:
        save_arbitrary_response(output_file, response, csv_data_key='forecasts')

    if print_response:
        unformatted_coordinates = formatted_coordinates.split(';')

        keys = ['time', 'temperature_2m', 'dewpoint_2m', 'wind_u_10m', 'wind_v_10m', 'precipitation', 'pressure_msl']
        headers = ['Time', '2m Temperature (°C)', '2m Dewpoint (°C)', 'Wind U (m/s)', 'Wind V (m/s)', 'Precipitation (mm)', 'MSL Pressure (hPa)']

        for i in range(len(response['forecasts'])):
            latitude, longitude = unformatted_coordinates[i].split(',')
            print(f"\nForecast for ({latitude}, {longitude})")
            print_table(response['forecasts'][i], keys=keys, headers=headers)

    return response


def get_gridded_forecast(variable, time=None, initialization_time=None, forecast_hour=None, output_file=None, silent=False, ensemble_member=None, model='wm', level=None):
    """
    Get gridded forecast data from the API.
    Note that this is primarily meant to be used internally by the other functions in this module.

    Args:
        time (str, optional): Date in either ISO 8601 format (YYYY-MM-DDTHH:00:00)
                    or compact format (YYYYMMDDHH). May be used instead of initialization_time and forecast_hour.
        initialization_time (str, optional): Date in either ISO 8601 format (YYYY-MM-DDTHH:00:00)
                    or compact format (YYYYMMDDHH). May be used in conjunction with forecast_hour instead of time.
        forecast_hour (int, optional): The forecast hour to get the forecast for. May be used in conjunction with initialization_time instead of time.
        variable (str): The variable you want the forecast for
        level (int, optional): The level you want the forecast for
        output_file (str, optional): Path to save the response data
                                      Supported formats: .nc
    """

    # backwards compatibility for time and variable order swap
    if time in ['temperature_2m', 'dewpoint_2m', 'wind_u_10m', 'wind_v_10m', '500/wind_u', '500/wind_v', '500/temperature', '850/temperature', 'pressure_msl', '500/geopotential', '850/geopotential', 'FULL']:
        variable, time = time, variable

    # require either time or initialization_time and forecast_hour
    if time is None and (initialization_time is None or forecast_hour is None):
        print("Error: you must provide either time or initialization_time and forecast_hour.")
        return
    elif time is not None and (initialization_time is not None or forecast_hour is not None):
        print("Warning: time, initialization_time, forecast_hour all provided; using initialization_time and forecast_hour.")

    params = {}
    if initialization_time is not None and forecast_hour is not None:
        params["initialization_time"] = parse_time(initialization_time, init_time_flag=True)
        params["forecast_hour"] = forecast_hour
    elif time:
        params["time"] = parse_time(time)

    if ensemble_member:
        params["ens_member"] = ensemble_member

    # Map variable strings like "500/temperature" to query params variable=temperature, level=500
    request_params = dict(params)
    if '/' in variable and variable.split('/')[0].isdigit():
        level_str, var_name = variable.split('/', 1)
        request_params['variable'] = var_name
        request_params['level'] = int(level_str)
    else:
        request_params['variable'] = variable

    if level is not None:
        request_params['level'] = level

    response = make_api_request(f"{FORECASTS_API_BASE_URL}/{model}/gridded", params=request_params, as_json=False)

    if response is None:
        return None

    if output_file:
        if not silent:
            print(f"Output URL found; downloading to {output_file}...")
        download_and_save_output(output_file, response)

    return response

def get_full_gridded_forecast(time=None, initialization_time=None, forecast_hour=None, output_file=None, silent=False, ensemble_member=None, model='wm'):
    """
    Get gridded forecast data for all variables from the API.

    Args:
        time (str, optional): Date in either ISO 8601 format (YYYY-MM-DDTHH:00:00)
                    or compact format (YYYYMMDDHH). May be used instead of initialization_time and forecast_hour.
        initialization_time (str, optional): Date in either ISO 8601 format (YYYY-MM-DDTHH:00:00)
                    or compact format (YYYYMMDDHH). May be used in conjunction with forecast_hour instead of time.
        forecast_hour (int, optional): The forecast hour to get the forecast for. May be used in conjunction with initialization_time instead of time.
        output_file (str, optional): Path to save the response data
                                      Supported formats: .nc
        silent (bool, optional): Whether to print output
        ensemble_member (int, optional): The ensemble member to get the forecast for
        model (str, optional): The model to get the forecast for
    """

    return get_gridded_forecast(variable="all", time=time, initialization_time=initialization_time, forecast_hour=forecast_hour, output_file=output_file, silent=silent, ensemble_member=ensemble_member, model=model)


def get_tropical_cyclones(initialization_time=None, basin=None, output_file=None, print_response=False, model='wm'):
    """
    Get tropical cyclone data from the API.

    Args:
        initialization_time (str): Date in either ISO 8601 format (YYYY-MM-DDTHH:00:00)
                                 or compact format (YYYYMMDDHH)
                                 where HH must be 00, 06, 12, or 18
        basin (str, optional): Basin code (e.g., 'NA', 'EP', 'WP', 'NI', 'SI', 'AU', 'SP')
        output_file (str, optional): Path to save the response data
                                      Supported formats: .json, .csv, .gpx, .geojson, .kml, .little_r
        print_response (bool, optional): Whether to print the response data

    Returns:
        dict: API response data or None if there's an error
    """
    params = {}

    if initialization_time:
        initialization_time_parsed = parse_time(initialization_time, init_time_flag=True)
        params["initialization_time"] = initialization_time_parsed
    else:
        initialization_time = 'latest'

    if basin:
        if basin not in ['NA', 'EP', 'WP', 'NI', 'SI', 'AU', 'SP']:
            print("Basin should be one of the following:")
            print("NA - North Atlantic")
            print("EP - Eastern Pacific")
            print("WP - Western Pacific")
            print("NI - North Indian")
            print("SI - South West Indian")
            print("AU - Australian Region")
            print("SP - South Pacific")
            exit(44)
        params["basin"] = basin

    # Response here is a .json
    # Tropical cyclones endpoint is model-specific
    response = make_api_request(f"{FORECASTS_API_BASE_URL}/{model}/tropical_cyclones", params=params)

    if output_file:
        if not output_file.lower().endswith(TCS_SUPPORTED_FORMATS):
            print("Unsupported file format.")
            print_tc_supported_formats()
            exit(44)
        elif response == {}:
            # This should be prior to any check of specific .filetype format check and post filetype valid check
            # make_api_request covers 403, 404, 502, HTTP, Connections Errors
            # If we pass all of these and we get an empty dictionary ==> there are no active TCs
            print("There are no active tropical cyclones for your request\n")
            # It's pointless to save an empty file
            # save_response_to_file() will throw error on saving {}
        elif response is None:
            print("-------------------------------------------------------")
            print("Tropical cyclones have not yet been generated for this initialization time")
        else:
            save_track(output_file, response, require_ids=True)

    if print_response:
        if not response:
            print("No tropical cyclones for initialization time:", initialization_time)
        elif len(response) == 0:
            print("No tropical cyclones for initialization time:", initialization_time)
        else:
            print("Tropical Cyclones for initialization time:", initialization_time)
            for cyclone_id, tracks in response.items():
                print(f"\nCyclone ID: {cyclone_id}")
                print_table(tracks, keys=['time', 'latitude', 'longitude'], headers=['Time', 'Latitude', 'Longitude'])

    return response


def get_initialization_times(print_response=False, ensemble_member=None, model='wm'):
    """
    Get available WeatherMesh initialization times (also known as cycle times).

    Returns dict with keys "latest", "available", and "in_progress"
    """

    params = {
        'ens_member': ensemble_member,
    }
    response = make_api_request(f"{FORECASTS_API_BASE_URL}/{model}/initialization_times", params=params)

    if print_response:
        print("Latest initialization time:", response['latest'])
        print("Available initialization times:")
        for time in response['available']:
            print(f" - {time}")

        print("In progress initialization times:")
        for time in response['in_progress']:
            print(f" - {time}")

    return response


def get_archived_initialization_times(print_response=False, ensemble_member=None, model='wm', page_end=None):
    """
    Get archived initialization times for forecasts from our archive.
    These may be higher latency to fetch and cannot be used for custom point forecasting.
    """
    params = {
        'ens_member': ensemble_member,
    }
    if page_end:
        params['page_end'] = parse_time(page_end)
    response = make_api_request(f"{FORECASTS_API_BASE_URL}/{model}/initialization_times/archive", params=params)

    if print_response:
        print("Available archived initialization times:")
        times = response.get('archived_initialization_times', response)
        for time in times:
            print(f" - {time}")


# Tropical cyclones
def print_tc_supported_formats():
    """Print supported file formats for saving tcs data."""
    print("Supported formats:")
    for fmt in TCS_SUPPORTED_FORMATS:
        print(f"  - {fmt}")


def download_and_save_output(output_file, response, silent=False):
    """
    Downloads a forecast output from a presigned S3 url contained in a response and saves it as a .nc file.

    Args:
        output_file (str): Path where to save the .nc file
        response (str): Response that contains the S3 url to download the data from

    Returns:
        bool: True if successful, False otherwise
    """

    # Add .nc extension if not present
    if not output_file.endswith('.nc'):
        output_file = output_file + '.nc'

    try:
        # Save the content directly to file
        with open(output_file, 'wb') as f:
            f.write(response.content)

        if not silent:
            print(f"Data Successfully saved to {output_file}")

        return True

    except requests.exceptions.RequestException as e:
        if not silent:
            print(f"Error downloading the file: {e}")
        return False
    except Exception as e:
        if not silent:
            print(f"Error processing the file: {e}")
        return False

def get_population_weighted_hdd(initialization_time, ens_member=None, output_file=None, print_response=False, model='wm'):
    """
    Get population weighted HDD data from the API.
    """
    params = {
        "initialization_time": initialization_time,
        "ens_member": ens_member,
    }
    response = make_api_request(f"{API_BASE_URL}/insights/v1/{model}/hdds", params=params, as_json=True)
    
    if output_file:
        if output_file.endswith('.csv'):
            import csv

            dates = response['dates']
            hdd_map = response.get('hdd', {})

            keys = list(hdd_map.keys())
            is_date_keyed = False
            if len(keys) > 0 and isinstance(keys[0], str):
                import re
                is_date_keyed = re.match(r"^\d{4}-\d{2}-\d{2}", keys[0]) is not None

            if is_date_keyed:
                region_set = set()
                for date in dates:
                    if isinstance(hdd_map.get(date), dict):
                        region_set.update(hdd_map[date].keys())
                regions = sorted(region_set)
                with open(output_file, 'w') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Region'] + dates)
                    for region in regions:
                        row = [region]
                        for date in dates:
                            value = ''
                            if isinstance(hdd_map.get(date), dict):
                                value = hdd_map[date].get(region, '')
                            row.append(value)
                        writer.writerow(row)
            else:
                regions = sorted(hdd_map.keys())
                with open(output_file, 'w') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Region'] + dates)
                    for region in regions:
                        writer.writerow([region] + [hdd_map.get(region, {}).get(date, '') for date in dates])
    
    if print_response:
        dates = response['dates']
        hdd_map = response.get('hdd', {})
        keys = list(hdd_map.keys())
        is_date_keyed = False
        if len(keys) > 0 and isinstance(keys[0], str):
            import re
            is_date_keyed = re.match(r"^\d{4}-\d{2}-\d{2}", keys[0]) is not None

        if is_date_keyed:
            region_set = set()
            for date in dates:
                if isinstance(hdd_map.get(date), dict):
                    region_set.update(hdd_map[date].keys())
            for region in sorted(region_set):
                print(f"{region}:")
                for date in dates:
                    if isinstance(hdd_map.get(date), dict) and region in hdd_map[date]:
                        print(f"  {date}: {hdd_map[date][region]}")
        else:
            for region in sorted(hdd_map.keys()):
                print(f"{region}:")
                for date in dates:
                    if isinstance(hdd_map.get(region), dict) and date in hdd_map[region]:
                        print(f"  {date}: {hdd_map[region][date]}")
    
    return response

def get_population_weighted_cdd(initialization_time, ens_member=None, output_file=None, print_response=False, model='wm'):
    """
    Get population weighted CDD data from the API.
    """
    params = {
        "initialization_time": initialization_time,
        "ens_member": ens_member,
    }
    response = make_api_request(f"{API_BASE_URL}/insights/v1/{model}/cdds", params=params, as_json=True)
    
    if output_file:
        if output_file.endswith('.csv'):
            import csv

            dates = response['dates']
            cdd_map = response.get('cdd', {})

            keys = list(cdd_map.keys())
            is_date_keyed = False
            if len(keys) > 0 and isinstance(keys[0], str):
                import re
                is_date_keyed = re.match(r"^\d{4}-\d{2}-\d{2}", keys[0]) is not None

            if is_date_keyed:
                region_set = set()
                for date in dates:
                    if isinstance(cdd_map.get(date), dict):
                        region_set.update(cdd_map[date].keys())
                regions = sorted(region_set)
                with open(output_file, 'w') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Region'] + dates)
                    for region in regions:
                        row = [region]
                        for date in dates:
                            value = ''
                            if isinstance(cdd_map.get(date), dict):
                                value = cdd_map[date].get(region, '')
                            row.append(value)
                        writer.writerow(row)
            else:
                regions = sorted(cdd_map.keys())
                with open(output_file, 'w') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Region'] + dates)
                    for region in regions:
                        writer.writerow([region] + [cdd_map.get(region, {}).get(date, '') for date in dates])
    
    if print_response:
        dates = response['dates']
        cdd_map = response.get('cdd', {})
        keys = list(cdd_map.keys())
        is_date_keyed = False
        if len(keys) > 0 and isinstance(keys[0], str):
            import re
            is_date_keyed = re.match(r"^\d{4}-\d{2}-\d{2}", keys[0]) is not None

        if is_date_keyed:
            region_set = set()
            for date in dates:
                if isinstance(cdd_map.get(date), dict):
                    region_set.update(cdd_map[date].keys())
            for region in sorted(region_set):
                print(f"{region}:")
                for date in dates:
                    if isinstance(cdd_map.get(date), dict) and region in cdd_map[date]:
                        print(f"  {date}: {cdd_map[date][region]}")
        else:
            for region in sorted(cdd_map.keys()):
                print(f"{region}:")
                for date in dates:
                    if isinstance(cdd_map.get(region), dict) and date in cdd_map[region]:
                        print(f"  {date}: {cdd_map[region][date]}")
    
    return response


def get_point_forecasts_interpolated(coordinates, min_forecast_time=None, max_forecast_time=None, min_forecast_hour=None, max_forecast_hour=None, initialization_time=None, ensemble_member=None, output_file=None, print_response=False, model='wm'):
    """
    Get interpolated point forecasts from the API.

    Args:
        coordinates (str | list): "lat,lon;lat,lon" string or list of tuples/strings/dicts
        min_forecast_time (str, optional): Minimum forecast time (ISO 8601 formats supported)
        max_forecast_time (str, optional): Maximum forecast time (ISO 8601 formats supported)
        min_forecast_hour (int, optional): Minimum forecast hour
        max_forecast_hour (int, optional): Maximum forecast hour
        initialization_time (str, optional): Initialization time (ISO 8601). If omitted, latest is used
        ensemble_member (str | int, optional): Ensemble member (e.g., "mean" or 0-23)
        output_file (str, optional): Save response to .json or .csv (csv_data_key='forecasts')
        print_response (bool, optional): Print response summary to stdout
        model (str, optional): Forecast model (e.g., wm, wm4, wm4-intra, ecmwf-det)
    """

    formatted_coordinates = coordinates

    if isinstance(coordinates, list):
        coordinate_items = []
        for coordinate in coordinates:
            if isinstance(coordinate, (tuple, list)):
                if len(coordinate) != 2:
                    print("Coordinates should be tuples or lists with two elements: latitude and longitude.")
                    return
                coordinate_items.append(f"{coordinate[0]},{coordinate[1]}")
            elif isinstance(coordinate, str):
                coordinate_items.append(coordinate)
            elif isinstance(coordinate, dict):
                if 'latitude' in coordinate and 'longitude' in coordinate:
                    coordinate_items.append(f"{coordinate['latitude']},{coordinate['longitude']}")
                elif 'lat' in coordinate and 'lon' in coordinate:
                    coordinate_items.append(f"{coordinate['lat']},{coordinate['lon']}")
                elif 'lat' in coordinate and 'long' in coordinate:
                    coordinate_items.append(f"{coordinate['lat']},{coordinate['long']}")
                elif 'lat' in coordinate and 'lng' in coordinate:
                    coordinate_items.append(f"{coordinate['lat']},{coordinate['lng']}")
                else:
                    print("Coordinates should be dictionaries with keys 'latitude' and 'longitude'.")
                    return
        formatted_coordinates = ";".join(coordinate_items)

    formatted_coordinates = formatted_coordinates.replace(" ", "")
    if not formatted_coordinates:
        print("To get interpolated points forecasts you must provide coordinates.")
        return

    params = {"coordinates": formatted_coordinates}

    if min_forecast_time:
        params["min_forecast_time"] = parse_time(min_forecast_time)
    if max_forecast_time:
        params["max_forecast_time"] = parse_time(max_forecast_time)
    if min_forecast_hour:
        params["min_forecast_hour"] = int(min_forecast_hour)
    if max_forecast_hour:
        params["max_forecast_hour"] = int(max_forecast_hour)
    if initialization_time:
        params["initialization_time"] = parse_time(initialization_time, init_time_flag=True)
    if ensemble_member is not None:
        params["ens_member"] = ensemble_member

    if print_response:
        print("Generating interpolated point forecast...")

    # Note: interpolated endpoint uses underscore path: point_forecast/interpolated
    response = make_api_request(f"{FORECASTS_API_BASE_URL}/{model}/point_forecast/interpolated", params=params)

    if output_file:
        save_arbitrary_response(output_file, response, csv_data_key='forecasts')

    if print_response and response is not None:
        unformatted_coordinates = formatted_coordinates.split(';')
        # Include latitude/longitude along with standard surface variables
        keys = ['time', 'temperature_2m', 'dewpoint_2m', 'wind_u_10m', 'wind_v_10m', 'precipitation', 'pressure_msl', 'latitude', 'longitude']
        headers = ['Time', '2m Temperature (°C)', '2m Dewpoint (°C)', 'Wind U (m/s)', 'Wind V (m/s)', 'Precipitation (mm)', 'MSL Pressure (hPa)', 'Latitude', 'Longitude']

        forecasts = response.get('forecasts', [])
        for i in range(min(len(forecasts), len(unformatted_coordinates))):
            latitude, longitude = unformatted_coordinates[i].split(',')
            print(f"\nForecast for ({latitude}, {longitude})")
            print_table(forecasts[i], keys=keys, headers=headers)

    return response
