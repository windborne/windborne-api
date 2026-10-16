"""Hourly climate normals and calendar summaries for one or more coordinates."""

import json
from datetime import datetime
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


def get_climatology_summary(coordinates, *, date=None, start_date=None, end_date=None,
                            group_by=None, normal=None, elevation_correction=None,
                            water_strategy=None, output_file=None, print_response=False):
    """Get typical daily highs, lows, precipitation, and wind for coordinates.

    Supply date or an inclusive start_date/end_date range of at most 366 dates.
    Dates must be YYYY-MM-DD strings. They refer to each location's calendar
    dates at its fixed standard UTC offset, without daylight saving time; they
    are sent unchanged rather than converted to UTC timestamps. The year picks
    calendar dates, not historical observations from that year.

    group_by defaults to 'day'. Ranges also support 'week' (seven-day groups
    starting at start_date), 'month' (calendar months), or 'period' (one group).
    A single date requires day grouping. The API calculates daily statistics
    for each year in the normal period before averaging them across years.
    Grouped precipitation sums the daily normals; other variables average them.

    Omitted options retain server defaults: normal='1991-2020',
    elevation_correction=False, and land-only interpolation. Set
    water_strategy='allow' to include water grid cells.

    Return the complete response, including metadata, nulls, and summary rows
    grouped by coordinate. output_file accepts .json (the full response) or
    .csv (all summary rows with coordinates and standard UTC offsets).
    print_response prints the full JSON response.
    """
    if isinstance(coordinates, list) and any(
        not isinstance(entry, (str, tuple, list, dict)) for entry in coordinates
    ):
        raise ValueError('Each coordinate must be a string, pair, or coordinate dictionary.')
    formatted_coordinates = _format_point_forecast_coordinates(coordinates)
    if not formatted_coordinates:
        raise ValueError('Climatology summary requires at least one coordinate.')
    if group_by not in (None, 'day', 'week', 'month', 'period'):
        raise ValueError('group_by must be day, week, month, or period.')
    if date is not None:
        if start_date is not None or end_date is not None or group_by not in (None, 'day'):
            raise ValueError('Provide date with day grouping, or both start_date and end_date.')
        dates = {'date': date}
    elif start_date is None or end_date is None:
        raise ValueError('Provide date or both start_date and end_date.')
    else:
        dates = {'start_date': start_date, 'end_date': end_date}

    parsed_dates = {}
    for name, value in dates.items():
        try:
            parsed = datetime.strptime(value, '%Y-%m-%d').date()
            if parsed.isoformat() != value:
                raise ValueError
        except (TypeError, ValueError):
            raise ValueError('{} must be a calendar date in YYYY-MM-DD format.'.format(name))
        parsed_dates[name] = parsed
    if date is None and not 0 <= (parsed_dates['end_date'] - parsed_dates['start_date']).days < 366:
        raise ValueError('The inclusive date range must contain 1 to 366 dates.')

    output_path = Path(output_file) if output_file is not None else None
    if output_path is not None and output_path.suffix.lower() not in ('.json', '.csv'):
        raise ValueError('Climatology summary output files must use .json or .csv.')

    params = {'coordinates': formatted_coordinates}
    params.update(dates)
    for name, value in (
        ('group_by', group_by), ('normal', normal),
        ('elevation_correction', elevation_correction), ('water_strategy', water_strategy),
    ):
        if value is not None:
            params[name] = str(value).lower() if isinstance(value, bool) else value

    response = make_api_request(f'{API_BASE_URL}/forecasts/v1/climatology/summary', params=params)
    if response is None:
        return None
    if output_path is not None:
        save_arbitrary_response(str(output_path), response, csv_data_key='climatology_summaries')
    if print_response:
        print(json.dumps(response, indent=2))
    return response
