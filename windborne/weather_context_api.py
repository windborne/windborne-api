"""MetaMesh forecasts with optional conditions, observations and climatology."""

import json
from pathlib import Path

from .api_request import API_BASE_URL, make_api_request
from .forecasts_api import _format_point_forecast_coordinates, _format_point_forecast_stations
from .utils import parse_time


def get_weather_context(coordinates=None, stations=None, *, include_conditions=None,
                        include_observations=None, include_distribution=None,
                        include_climatology=None, initialization_time=None,
                        min_forecast_hour=None, max_forecast_hour=None,
                        min_forecast_time=None, max_forecast_time=None,
                        observation_hours=None, climatology_normal=None,
                        output_file=None, print_response=False):
    """Get MetaMesh forecasts and requested context for coordinates or stations.

    Provide coordinates, stations, or both. Coordinates accept a semicolon-
    separated string or a list of coordinate entries, as in get_point_forecasts.
    Stations accept comma/semicolon-separated ICAO IDs or a list of IDs.
    Coordinate results precede station results; empty groups and null entries
    are preserved so all returned arrays retain the same location ordering.

    The API defaults all include_* flags to false. Conditions or observations
    limit the request to 10 total locations. observation_hours defaults to 48
    (range 1-168); climatology_normal defaults to '1991-2020'. These options are
    used only when their corresponding context is requested.

    Forecast-hour bounds default to 0 and 360. Time bounds and the station-only
    initialization_time accept ISO 8601 or YYYYMMDDHH; date-only inputs mean
    midnight UTC. The API always uses MetaMesh, so there is no model argument.

    Return the complete response, including units and any optional datasets.
    output_file supports .json to retain all datasets and location alignment;
    print_response prints the full JSON response.
    """
    if isinstance(coordinates, list) and any(
        not isinstance(entry, (str, tuple, list, dict)) for entry in coordinates
    ):
        raise ValueError('Each coordinate must be a string, pair, or coordinate dictionary.')
    formatted_coordinates = _format_point_forecast_coordinates(coordinates)
    if coordinates is not None and formatted_coordinates is None:
        raise ValueError('Invalid coordinates for weather context.')
    formatted_stations = _format_point_forecast_stations(stations)
    if stations is not None and formatted_stations is None:
        raise ValueError('Invalid stations for weather context.')
    if not formatted_coordinates and not formatted_stations:
        raise ValueError('Weather context requires coordinates or stations.')

    output_path = Path(output_file) if output_file is not None else None
    if output_path is not None and output_path.suffix.lower() != '.json':
        raise ValueError('Weather context output files must use .json to preserve all datasets.')

    params = {}
    if formatted_coordinates:
        params['coordinates'] = formatted_coordinates
    if formatted_stations:
        params['stations'] = formatted_stations
    for name, value in (
        ('include_conditions', include_conditions), ('include_observations', include_observations),
        ('include_distribution', include_distribution), ('include_climatology', include_climatology),
        ('min_forecast_hour', min_forecast_hour), ('max_forecast_hour', max_forecast_hour),
        ('observation_hours', observation_hours), ('climatology_normal', climatology_normal),
    ):
        if value is not None:
            params[name] = str(value).lower() if isinstance(value, bool) else value
    for name, value in (
        ('initialization_time', initialization_time),
        ('min_forecast_time', min_forecast_time), ('max_forecast_time', max_forecast_time),
    ):
        if value is not None:
            normalized = parse_time(value)
            params[name] = normalized if normalized.endswith('Z') else normalized + 'Z'

    response = make_api_request(f'{API_BASE_URL}/forecasts/v1/weather_context', params=params)
    if response is None:
        return None
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open('w', encoding='utf-8') as file:
            json.dump(response, file, indent=2)
    if print_response:
        print(json.dumps(response, indent=2))
    return response
