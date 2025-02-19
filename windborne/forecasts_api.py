import requests

from .utils import (
    parse_time,
    save_arbitrary_response,
    print_table
)

from .api_request import make_api_request
from .track_formatting import save_track

FORECASTS_API_BASE_URL = "https://forecasts.windbornesystems.com/api/v1"
FORECASTS_GRIDDED_URL = f"{FORECASTS_API_BASE_URL}/gridded"
FORECASTS_HISTORICAL_URL = f"{FORECASTS_API_BASE_URL}/gridded/historical"
FORECASTS_TCS_URL = f"{FORECASTS_API_BASE_URL}/tropical_cyclones"
TCS_SUPPORTED_FORMATS = ('.csv', '.json', '.geojson', '.gpx', '.kml', '.little_r')


# Point forecasts
def get_point_forecasts(coordinates, min_forecast_time=None, max_forecast_time=None, min_forecast_hour=None, max_forecast_hour=None, initialization_time=None, output_file=None, print_response=False):
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

    response = make_api_request(f"{FORECASTS_API_BASE_URL}/points", params=params)

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


def get_gridded_forecast(time, variable, output_file=None):
    """
    Get gridded forecast data from the API.
    Note that this is primarily meant to be used internally by the other functions in this module.

    Args:
        time (str): Date in either ISO 8601 format (YYYY-MM-DDTHH:00:00)
                    or compact format (YYYYMMDDHH)
                    where HH must be 00, 06, 12, or 18
        variable (str): The variable you want the forecast for
        output_file (str, optional): Path to save the response data
                                      Supported formats: .nc
    """

    params = {}

    if not time:
        print("Error: the time you want the forecast for is required.")
        return
    else:
        time_parsed = parse_time(time)
        params["time"] = time_parsed

    response = make_api_request(f"{FORECASTS_GRIDDED_URL}/{variable}", params=params, as_json=False)

    if response is None:
        return None

    if output_file:
        print(f"Output URL found; downloading to {output_file}...")
        download_and_save_output(output_file, response)

    return response

def get_full_gridded_forecast(time, output_file=None):
    return get_gridded_forecast(time, "FULL", output_file)

def get_temperature_2m(time, output_file=None):
    return get_gridded_forecast(time, "temperature_2m", output_file)

# Not yet implemented
# def get_dewpoint_2m(time, output_file=None):
#     return get_gridded_forecast(time, "dewpoint_2m", output_file)

def get_wind_u_10m(time, output_file=None):
    return get_gridded_forecast(time, "wind_u_10m", output_file)

def get_wind_v_10m(time, output_file=None):
    return get_gridded_forecast(time, "wind_v_10m", output_file)

def get_500hpa_wind_u(time, output_file=None):
    return get_gridded_forecast(time, "500/wind_u", output_file)

def get_500hpa_wind_v(time, output_file=None):
    return get_gridded_forecast(time, "500/wind_v", output_file)

def get_500hpa_temperature(time, output_file=None):
    return get_gridded_forecast(time, "500/temperature", output_file)

def get_850hpa_temperature(time, output_file=None):
    return get_gridded_forecast(time, "850/temperature", output_file)

def get_pressure_msl(time, output_file=None):
    return get_gridded_forecast(time, "pressure_msl", output_file)

def get_500hpa_geopotential(time, output_file=None):
    return get_gridded_forecast(time, "500/geopotential", output_file)

def get_850hpa_geopotential(time, output_file=None):
    return get_gridded_forecast(time, "850/geopotential", output_file)


def get_historical_output(initialization_time, forecast_hour, variable, output_file=None):
    params = {}

    if not initialization_time or not forecast_hour:
        print("To get the historical output of global temperature forecasts you need to provide:\n"
              "- the initialization time of the forecast\n"
              "- how many hours after the run time the forecast is valid at.\n")
        return
    else:
        params["initialization_time"] = parse_time(initialization_time, init_time_flag=True)
        params["forecast_hour"] = forecast_hour

    response = make_api_request(f"{FORECASTS_HISTORICAL_URL}/{variable}", params=params, as_json=False)

    if response is None:
        return None

    if output_file:
        print(f"Output URL found; downloading to {output_file}...")
        download_and_save_output(output_file, response)

    return response


def get_historical_temperature_2m(initialization_time, forecast_hour, output_file=None):
    return get_historical_output(initialization_time, forecast_hour, "temperature_2m", output_file)

def get_historical_500hpa_geopotential(initialization_time, forecast_hour, output_file=None):
    return get_historical_output(initialization_time, forecast_hour, "500/geopotential", output_file)

def get_historical_500hpa_wind_u(initialization_time, forecast_hour, output_file=None):
    return get_historical_output(initialization_time, forecast_hour, "500/wind_u", output_file)

def get_historical_500hpa_wind_v(initialization_time, forecast_hour, output_file=None):
    return get_historical_output(initialization_time, forecast_hour, "500/wind_v", output_file)


def get_tropical_cyclones(initialization_time=None, basin=None, output_file=None, print_response=False):
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
    response = make_api_request(FORECASTS_TCS_URL, params=params)

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
            print("You are too quick!\nThe tropical cyclone data for initialization time are not uploaded yet.")
            print('You may check again in a few hour.')
        else:
            save_track(output_file, response, require_ids=True)

    if print_response:
        if len(response) == 0:
            print("No tropical cyclones for initialization time:", initialization_time)
        else:
            print("Tropical Cyclones for initialization time:", initialization_time)
            for cyclone_id, tracks in response.items():
                print(f"\nCyclone ID: {cyclone_id}")
                print_table(tracks, keys=['time', 'latitude', 'longitude'], headers=['Time', 'Latitude', 'Longitude'])

    return response


def get_initialization_times(print_response=False):
    """
    Get available WeatherMesh initialization times (also known as cycle times).

    Returns dict with keys "latest" and "available" (a list)
    """

    response = make_api_request(f"{FORECASTS_API_BASE_URL}/initialization_times.json")

    if print_response:
        print("Latest initialization time:", response['latest'])
        print("Available initialization times:")
        for time in response['available']:
            print(f" - {time}")

    return response


# Tropical cyclones
def print_tc_supported_formats():
    """Print supported file formats for saving tcs data."""
    print("Supported formats:")
    for fmt in TCS_SUPPORTED_FORMATS:
        print(f"  - {fmt}")


def download_and_save_output(output_file, response):
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
        print(f"Data Successfully saved to {output_file}")
        return True

    except requests.exceptions.RequestException as e:
        print(f"Error downloading the file: {e}")
        return False
    except Exception as e:
        print(f"Error processing the file: {e}")
        return False