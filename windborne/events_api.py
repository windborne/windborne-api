"""Published weather events, including their geometry and point context.

All helpers return the complete API response without flattening geometries,
forecast-hour details, or per-location results. Optional query parameters are
omitted unless supplied, leaving defaults with the API.
"""
import json
from pathlib import Path
from urllib.parse import quote

from .api_request import API_BASE_URL, make_api_request
from .forecasts_api import _format_point_forecast_coordinates
from .utils import parse_time


_TIME_PARAMETERS = {
    'initialization_time', 'min_time', 'max_time',
    'min_forecast_time', 'max_forecast_time',
}


def _event_params(**values):
    params = {}
    for name, value in values.items():
        if value is None:
            continue
        if name in _TIME_PARAMETERS and value != 'latest':
            value = parse_time(value)
        elif isinstance(value, bool):
            # The event API accepts the literal strings true and false.
            value = str(value).lower()
        params[name] = value
    return params


def _get_event_response(model, path, params, output_file, print_response):
    output_path = Path(output_file) if output_file is not None else None
    if output_path is not None:
        if output_path.suffix.lower() not in ('.json', '.geojson'):
            raise ValueError('Event output files must use .json or .geojson.')
        if output_path.suffix.lower() == '.geojson' and params.get('format') != 'geojson':
            raise ValueError("Use format='geojson' to save a native .geojson response.")

    url = f'{API_BASE_URL}/insights/v1/{quote(model, safe="")}/{path}'
    response = make_api_request(url, params=params)
    if response is None:
        return None
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open('w', encoding='utf-8') as file:
            json.dump(response, file, indent=2)
    if print_response:
        print(json.dumps(response, indent=2))
    return response


def get_events(event_type, initialization_time=None, include_details=None, format=None,
               min_latitude=None, max_latitude=None, min_longitude=None, max_longitude=None,
               model='wm-6', output_file=None, print_response=False):
    """Get events of one type from a published model initialization.

    event_type is atmospheric_river, heatwave, coldwave, or front. An omitted
    initialization_time (or 'latest') selects the latest published run for that
    type. Times accept ISO 8601 or YYYYMMDDHH. include_details adds forecast-hour
    geometries; the server defaults to false. format accepts json or geojson and
    defaults to json on the server.

    To filter geographically, provide all four bounding-box edges. Longitude
    bounds can cross the antimeridian. Zero-valued edges are preserved.
    output_file saves the full response to .json; use format='geojson' for a
    native .geojson file. print_response prints that same complete response.
    """
    params = _event_params(
        initialization_time=initialization_time, include_details=include_details, format=format,
        min_latitude=min_latitude, max_latitude=max_latitude,
        min_longitude=min_longitude, max_longitude=max_longitude,
    )
    return _get_event_response(model, quote(event_type, safe=''), params, output_file, print_response)


def get_event_index(event_type, min_time=None, max_time=None,
                    min_latitude=None, max_latitude=None, min_longitude=None, max_longitude=None,
                    page=None, page_size=None, model='wm-6', output_file=None, print_response=False):
    """Get one page of events across published model initializations.

    min_time includes events ending at or after that time; max_time includes
    events starting at or before that time. Each accepts ISO 8601 or YYYYMMDDHH
    and may be used independently. Geographic filters require all four edges.
    page is zero-indexed (server default 0); page_size defaults to 64, maximum
    500. The response retains event IDs, total, page and page_size; this helper
    does not automatically fetch additional pages. output_file supports .json.
    """
    params = _event_params(
        min_time=min_time, max_time=max_time,
        min_latitude=min_latitude, max_latitude=max_latitude,
        min_longitude=min_longitude, max_longitude=max_longitude,
        page=page, page_size=page_size,
    )
    return _get_event_response(model, f'{quote(event_type, safe="")}/index', params, output_file, print_response)


def get_event(event_id, initialization_time=None, format=None, model='wm-6',
              output_file=None, print_response=False):
    """Get one event's summary, geometries and forecast-hour details.

    event_id comes from get_events or get_event_index. initialization_time is
    ISO 8601, YYYYMMDDHH, or 'latest'; omission selects the latest published run
    containing the event. format accepts json or geojson (server default json).
    output_file saves the intact response to .json, or .geojson when format is
    geojson. Forecast-hour detail is included by the API without an extra flag.
    """
    params = _event_params(initialization_time=initialization_time, format=format)
    return _get_event_response(model, quote(event_id, safe=''), params, output_file, print_response)


def get_event_init_times(event_id, model='wm-6', output_file=None, print_response=False):
    """Get published runs containing one event, including available and latest.

    The API's available times are sorted earliest to latest. output_file saves
    the complete response to .json.
    """
    return _get_event_response(model, f'{quote(event_id, safe="")}/init_times', {}, output_file, print_response)


def get_event_context(coordinates, initialization_time=None, min_forecast_time=None,
                      max_forecast_time=None, event_type=None, model='wm-6',
                      output_file=None, print_response=False):
    """Get the events affecting up to ten coordinates at each forecast time.

    coordinates accepts 'lat,lon;lat,lon' or the point-forecast helper's list of
    coordinate pairs, strings or dictionaries. An omitted initialization_time
    (or 'latest') selects the latest run with all four event products complete.
    min_forecast_time and max_forecast_time are inclusive ISO 8601 bounds;
    omission uses forecast_zero through forecast_zero + 360 hours. event_type
    optionally filters atmospheric_river, heatwave, coldwave, or front.

    Returned events[coordinate_index][time_index] arrays retain request order.
    Their summaries describe the entire event, not conditions at the requested
    coordinate. output_file saves the complete response to .json.
    """
    formatted_coordinates = _format_point_forecast_coordinates(coordinates)
    if formatted_coordinates is None:
        raise ValueError('coordinates must contain latitude,longitude pairs.')
    params = _event_params(
        coordinates=formatted_coordinates, initialization_time=initialization_time,
        min_forecast_time=min_forecast_time, max_forecast_time=max_forecast_time,
        event_type=event_type,
    )
    return _get_event_response(model, 'event-context', params, output_file, print_response)
