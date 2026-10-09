"""Hourly climatology for one or more coordinates."""

import json
from pathlib import Path

from .api_request import API_BASE_URL, make_api_request
from .forecasts_api import _format_point_forecast_coordinates
from .utils import parse_time, save_arbitrary_response


def get_climatology(coordinates, *, time=None, start_time=None, end_time=None,
                    normal=None, rolling_average_days=None, elevation_correction=None,
                    water_strategy=None, output_file=None, print_response=False):
    """Get hourly climate normals for coordinates in their requested order.

    coordinates accepts "latitude,longitude;latitude,longitude" or a list of
    coordinate entries, as in get_point_forecasts. Supply either time or both
    start_time and end_time. The range includes both endpoints, up to 8,784
    hours. Times must be hour-aligned; ISO 8601 and YYYYMMDDHH are accepted,
    and date-only inputs mean midnight UTC. Minutes and seconds are preserved
    so the API can reject times that are not hour-aligned.

    Omitted options retain server defaults: normal='1991-2020',
    rolling_average_days=0, elevation_correction=False, and land-only points.
    Set water_strategy='allow' to include water points. rolling_average_days
    is a radius from 0 to 182 days around the requested calendar day.

    Return the complete response, including metadata and the climatologies
    array grouped by location. output_file supports .json (the full response)
    or .csv (all climatology rows, including their coordinates).
    print_response prints the full JSON response.
    """
    if isinstance(coordinates, list) and any(
        not isinstance(entry, (str, tuple, list, dict)) for entry in coordinates
    ):
        raise ValueError('Each coordinate must be a string, pair, or coordinate dictionary.')
    formatted_coordinates = _format_point_forecast_coordinates(coordinates)
    if not formatted_coordinates:
        raise ValueError('Climatology requires at least one coordinate.')
    if time is not None:
        if start_time is not None or end_time is not None:
            raise ValueError('Provide either time or start_time and end_time, not both.')
    elif start_time is None or end_time is None:
        raise ValueError('Provide either time or both start_time and end_time.')

    output_path = Path(output_file) if output_file is not None else None
    if output_path is not None and output_path.suffix.lower() not in ('.json', '.csv'):
        raise ValueError('Climatology output files must use .json or .csv.')

    params = {'coordinates': formatted_coordinates}
    for name, value in (('time', time), ('start_time', start_time), ('end_time', end_time)):
        if value is not None:
            normalized = parse_time(value)
            params[name] = normalized if normalized.endswith('Z') else normalized + 'Z'
    for name, value in (
        ('normal', normal), ('rolling_average_days', rolling_average_days),
        ('elevation_correction', elevation_correction), ('water_strategy', water_strategy),
    ):
        if value is not None:
            params[name] = str(value).lower() if isinstance(value, bool) else value

    response = make_api_request(f'{API_BASE_URL}/forecasts/v1/climatology', params=params)
    if response is None:
        return None
    if output_path is not None:
        save_arbitrary_response(str(output_path), response, csv_data_key='climatologies')
    if print_response:
        print(json.dumps(response, indent=2))
    return response
