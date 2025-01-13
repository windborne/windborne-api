from .config import (FORECASTS_API_BASE_URL,
                     FORECASTS_GRIDDED_URL,
                     FORECASTS_HISTORICAL_URL,
                     FORECASTS_TCS_URL,
                     TCS_SUPPORTED_FORMATS)

from .utils import (make_api_request,
                    parse_time,
                    download_and_save_nc,
                    save_csv_json,
                    save_as_geojson,
                    save_as_gpx,
                    save_as_kml,
                    save_as_little_r)

# Point forecasts
def get_point_forecasts(coordinates, min_forecast_time=None, max_forecast_time=None, min_forecast_hour=None, max_forecast_hour=None, initialization_time=None, save_to_file=None):
    # Sanitize coordinates by removing whitespace
    coordinates = coordinates.replace(" ", "")

    params = {"coordinates": coordinates}

    if not coordinates:
        print("To get points forecasts you must provide coordinates.")
        return
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

    print("We are initiating handshake procedure with our S3 server.\n")

    response = make_api_request(f"{FORECASTS_API_BASE_URL}/points", params=params)

    if save_to_file:
        # Save as .json
        save_csv_json(save_to_file, response, csv_data_key='forecasts')

    return response

# Gridded forecasts
# We return the whole response, not just the url

# 500hPa geopotential
# 850hPa geopotential
# 500hPa wind u
# 500hPa wind v
# 500hPa temperature
# 850hPa temperature
# wind_u_10m
# wind_v_10m
# pressure_msl
# temperature_2m

def get_temperature_2m(time, save_to_file=None):
    params = {}

    if not time:
        print("To get the gridded output of global 2m temperature forecast you need to provide the time for which to get the forecast.")
        return
    else:
        time_parsed = parse_time(time)
        params["time"] = time_parsed

    print("We are initiating handshake procedure with our S3 server.\n")

    response = make_api_request(f"{FORECASTS_GRIDDED_URL}/temperature_2m", params=params, return_type='all')

    if save_to_file:
        download_and_save_nc(save_to_file, response)

    return response

# not implemented yet
def get_dewpoint_2m(time, save_to_file=None):
    params = {}

    if not time:
        print("To get the gridded output of global 2m dewpoint forecast you need to provide the time for which to get the forecast.")
        return
    else:
        time_parsed = parse_time(time)
        params["time"] = time_parsed

    print("We are initiating handshake procedure with our S3 server.\n")
    response = make_api_request(f"{FORECASTS_GRIDDED_URL}/dewpoint_2m", params=params, return_type='all')

    if save_to_file:
        download_and_save_nc(save_to_file, response)

    return response

def get_wind_u_10m(time, save_to_file=None):
    params = {}

    if not time:
        print("To get the gridded output of global 10m u-component of wind forecasts you need to provide the time for which to get the forecast.")
        return
    else:
        time_parsed = parse_time(time)
        params["time"] = time_parsed

    print("We are initiating handshake procedure with our S3 server.\n")
    response = make_api_request(f"{FORECASTS_GRIDDED_URL}/wind_u_10m", params=params, return_type='all')

    if save_to_file:
        download_and_save_nc(save_to_file, response)

    return response

def get_wind_v_10m(time, save_to_file=None):
    params = {}

    if not time:
        print("To get the gridded output of global 10m v-component of wind forecasts you need to provide the time for which to get the forecast.")
        return
    else:
        time_parsed = parse_time(time)
        params["time"] = time_parsed

    print("We are initiating handshake procedure with our S3 server.\n")
    response = make_api_request(f"{FORECASTS_GRIDDED_URL}/wind_v_10m", params=params, return_type='all')

    if save_to_file:
        download_and_save_nc(save_to_file, response)

    return response

def get_500hpa_wind_u(time, save_to_file=None):
    params = {}

    if not time:
        print("To get the gridded output of global 500hPa wind u-component of wind forecasts you need to provide the time for which to get the forecast.")
        return
    else:
        time_parsed = parse_time(time)
        params["time"] = time_parsed

    print("We are initiating handshake procedure with our S3 server.\n")
    response = make_api_request(f"{FORECASTS_GRIDDED_URL}/500/wind_u", params=params, return_type='all')

    if save_to_file:
        download_and_save_nc(save_to_file, response)

    return response

def get_500hpa_wind_v(time, save_to_file=None):
    params = {}

    if not time:
        print("To get the gridded output of global 500hPa wind v-component of wind forecasts you need to provide the time for which to get the forecast.")
        return
    else:
        time_parsed = parse_time(time)
        params["time"] = time_parsed

    print("We are initiating handshake procedure with our S3 server.\n")
    response = make_api_request(f"{FORECASTS_GRIDDED_URL}/500/wind_v", params=params, return_type='all')

    if save_to_file:
        download_and_save_nc(save_to_file, response)

    return response

def get_500hpa_temperature(time, save_to_file=None):
    params = {}

    if not time:
        print("To get the gridded output of global 500hPa temperature forecasts you need to provide the time for which to get the forecast.")
        return
    else:
        time_parsed = parse_time(time)
        params["time"] = time_parsed

    print("We are initiating handshake procedure with our S3 server.\n")
    response = make_api_request(f"{FORECASTS_GRIDDED_URL}/500/temperature", params=params, return_type='all')

    if save_to_file:
        download_and_save_nc(save_to_file, response)

    return response

def get_850hpa_temperature(time, save_to_file=None):
    params = {}

    if not time:
        print("To get the gridded output of global 850hPa temperature forecasts you need to provide the time for which to get the forecast.")
        return
    else:
        time_parsed = parse_time(time)
        params["time"] = time_parsed

    print("We are initiating handshake procedure with our S3 server.\n")
    response = make_api_request(f"{FORECASTS_GRIDDED_URL}/850/temperature", params=params, return_type='all')

    if save_to_file:
        download_and_save_nc(save_to_file, response)

    return response

def get_pressure_msl(time, save_to_file=None):
    params = {}

    if not time:
        print("To get the gridded output of global mean sea level pressure forecasts you need to provide the time for which to get the forecast.")
        return
    else:
        time_parsed = parse_time(time)
        params["time"] = time_parsed

    print("We are initiating handshake procedure with our S3 server.\n")
    response = make_api_request(f"{FORECASTS_GRIDDED_URL}/pressure_msl", params=params, return_type='all')

    if save_to_file:
        download_and_save_nc(save_to_file, response)

    return response

def get_500hpa_geopotential(time, save_to_file=None):
    params = {}

    if not time:
        print("To get the gridded output of global 500hPa geopotential forecasts you need to provide the time for which to get the forecast.")
        return
    else:
        time_parsed = parse_time(time)
        params["time"] = time_parsed

    print("We are initiating handshake procedure with our S3 server.\n")
    response = make_api_request(f"{FORECASTS_GRIDDED_URL}/500/geopotential", params=params, return_type='all')

    if save_to_file:
        download_and_save_nc(save_to_file, response)

    return response

def get_850hpa_geopotential(time, save_to_file=None):
    params = {}

    if not time:
        print("To get the gridded output of global 850hPa geopotential forecasts you need to provide the time for which to get the forecast.")
        return
    else:
        time_parsed = parse_time(time)
        params["time"] = time_parsed

    print("We are initiating handshake procedure with our S3 server.\n")
    response = make_api_request(f"{FORECASTS_GRIDDED_URL}/850/geopotential", params=params, return_type='all')

    if save_to_file:
        download_and_save_nc(save_to_file, response)

    return response

# Historical forecasts
# We return the whole response, not just the url

def get_historical_temperature_2m(initialization_time, forecast_hour, save_to_file=None):
    params = {}

    if not initialization_time or not forecast_hour:
        print("To get the historical output of global temperature forecasts you need to provide:\n"
              "- the initialization time of the forecast\n"
              "- how many hours after the run time the forecast is valid at.\n")
        return
    else:
        time_parsed = parse_time(initialization_time, init_time_flag=True)
        params["initialization_time"] = time_parsed
        params["forecast_hour"] = forecast_hour

    print("We are initiating handshake procedure with our S3 server.\n")

    response = make_api_request(f"{FORECASTS_HISTORICAL_URL}/temperature_2m", params=params, return_type='all')

    if save_to_file:
        download_and_save_nc(save_to_file, response)

    return response

def get_historical_500hpa_geopotential(initialization_time, forecast_hour, save_to_file=None):
    params = {}

    if not initialization_time or not forecast_hour:
        print("To get the historical output of global 500hPa geopotential forecasts you need to provide:\n"
              "- the initialization time of the forecast\n"
              "- how many hours after the run time the forecast is valid at.\n")
        return
    else:
        time_parsed = parse_time(initialization_time,init_time_flag=True)
        params["initialization_time"] = time_parsed
        params["forecast_hour"] = forecast_hour

    print("We are initiating handshake procedure with our S3 server.\n")

    response = make_api_request(f"{FORECASTS_HISTORICAL_URL}/500/geopotential", params=params, return_type='all')

    if save_to_file:
        download_and_save_nc(save_to_file, response)

    return response

def get_historical_500hpa_wind_u(initialization_time, forecast_hour, save_to_file=None):
    params = {}

    if not initialization_time or not forecast_hour:
        print("To get the historical output of global 500hPa wind u forecasts you need to provide:\n"
              "- the initialization time of the forecast\n"
              "- how many hours after the run time the forecast is valid at.\n")
        return
    else:
        time_parsed = parse_time(initialization_time,init_time_flag=True)
        params["initialization_time"] = time_parsed
        params["forecast_hour"] = forecast_hour

    print("We are initiating handshake procedure with our S3 server.\n")

    response = make_api_request(f"{FORECASTS_HISTORICAL_URL}/500/wind_u", params=params, return_type='all')

    if save_to_file:
        download_and_save_nc(save_to_file, response)

    return response

def get_historical_500hpa_wind_v(initialization_time, forecast_hour, save_to_file=None):
    params = {}

    if not initialization_time or not forecast_hour:
        print("To get the historical output of global 500hPa wind v forecasts you need to provide:\n"
              "- the initialization time of the forecast\n"
              "- how many hours after the run time the forecast is valid at.\n")
        return
    else:
        time_parsed = parse_time(initialization_time, init_time_flag=True)
        params["initialization_time"] = time_parsed
        params["forecast_hour"] = forecast_hour

    print("We are initiating handshake procedure with our S3 server.\n")

    response = make_api_request(f"{FORECASTS_HISTORICAL_URL}/500/wind_v", params=params, return_type='all')

    if save_to_file:
        download_and_save_nc(save_to_file, response)

    return response

# Other
# TCs
def get_tropical_cyclones(initialization_time=None, basin=None, save_to_file=None):
    """
    Get tropical cyclone data from the API.

    Args:
        initialization_time (str): Date in either ISO 8601 format (YYYY-MM-DDTHH:00:00)
                                 or compact format (YYYYMMDDHH)
                                 where HH must be 00, 06, 12, or 18
        save_to_file (str, optional): Path to save the response data
                                      Supported formats: .json, .csv, .gpx, .geojson, .kml, .little_r

    Returns:
        dict: API response data or None if there's an error
    """
    params = {}

    if initialization_time:
        initialization_time_parsed = parse_time(initialization_time, init_time_flag=True)
        params["initialization_time"] = initialization_time_parsed
    else:
        # Madee this for our displaying message when no active tcs found
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

    if save_to_file:
        if '.' not in save_to_file:
            print("You have to provide a filetype for your output file.")
            print_tc_supported_formats()
            exit (4)
        elif not save_to_file.lower().endswith(TCS_SUPPORTED_FORMATS):
            print("Unsupported file format.")
            print_tc_supported_formats()
            exit(44)
        elif response == {}:
            # This should be prior to any check of specific .filetype format check and post filetype valid check
            # make_api_request covers 403, 404, 502, HTTP, Connections Errors
            # If we pass all of these and we get an empty dictionary ==> there are no active TCs
            print("There are no active tropical cyclones for your request\n")
            print("We didn't save any file on your machine.")
            # It's pointless to save an empty file
            # save_response_to_file() will throw error on saving {}
        elif response is None:
            print("-------------------------------------------------------")
            print("You are too quick!\nThe tropical cyclone data for initialization time are not uploaded yet.")
            print('You may check again in a few hours again.')
        elif save_to_file.lower().endswith('.csv'):
            # Flatten for CSV
            flattened_data = []
            for cyclone_id, tracks in response.items():
                for track in tracks:
                    track_data = {
                        'cyclone_id': cyclone_id,
                        'latitude': track['latitude'],
                        'longitude': track['longitude'],
                        'time': track['time']
                    }
                    flattened_data.append(track_data)
            save_csv_json(save_to_file, {'prediction': flattened_data}, csv_data_key='prediction')
        elif save_to_file.lower().endswith('.json'):
            # Direct save for JSON
            save_csv_json(save_to_file, response)
        elif save_to_file.lower().endswith('.geojson'):
            save_as_geojson(save_to_file, response)
        elif save_to_file.lower().endswith('.gpx'):
            save_as_gpx(save_to_file, response)
        elif save_to_file.lower().endswith('.kml'):
            save_as_kml(save_to_file, response)
        elif save_to_file.lower().endswith('.little_r'):
            save_as_little_r(save_to_file, response)

    return response

def get_initialization_times():
    """
    Get available initialization times for pointy.
    Returns:
        dict: API response data or None if there's an error
    """

    # Response here is a .json
    response = make_api_request(f"{FORECASTS_API_BASE_URL}/initialization_times.json")

    return response

# Tropical cyclones
def print_tc_supported_formats():
    """Print supported file formats for saving tcs data."""
    print("Supported formats:")
    for fmt in TCS_SUPPORTED_FORMATS:
        print(f"  - {fmt}")