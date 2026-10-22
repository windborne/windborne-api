"""Run server-side calculations over WindBorne forecast data."""

import json
from pathlib import Path

from .api_request import API_BASE_URL, make_api_request


def _write_json_response(response, output_path, print_response):
    """Keep the full response, including validation and partial-result errors."""
    if response is None:
        return
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open('w', encoding='utf-8') as file:
            json.dump(response, file, indent=2)
    if print_response:
        print(json.dumps(response, indent=2))


def validate_calculation(calculation, *, output_file=None, print_response=False):
    """Validate calculation syntax and return the complete JSON response.

    A response with ``valid=False`` is a successful validation request, not an
    HTTP error. Validation does not check availability of a model's input data.
    The expression is sent unchanged. Output files must use .json.
    """
    output_path = Path(output_file) if output_file is not None else None
    if output_path is not None and output_path.suffix.lower() != '.json':
        raise ValueError('Calculation validation output files must use .json.')

    response = make_api_request(
        f'{API_BASE_URL}/insights/v1/custom-calculations/validate',
        method='POST', json={'calculation': calculation},
    )
    _write_json_response(response, output_path, print_response)
    return response


def calculate_gridded(calculation, initialization_time=None, *, model='wm-6',
                      forecast_hours=None, lat_range=None, lon_range=None,
                      as_url=False, output_file=None, print_response=False):
    """Return a calculation's Zarr ZIP bytes, or download metadata with as_url=True.

    Omit the ISO 8601 initialization_time to use the latest complete update.
    forecast_hours accepts one nonnegative integer or a nonempty list; omit it
    to calculate every available hour. lat_range and lon_range are optional
    two-number bounds for wm-6 only.
    A west-to-east lon_range that crosses the dateline is supported.

    The ZIP contains results and metadata, including model, initialization_time,
    forecast_zero, forecast_hours, calculation, grid_calculations and
    forecast_hour_errors for skipped hours. With as_url=True, return the
    complete JSON response containing the temporary URL,
    expiration, content type and size. This helper does not download that URL.
    Output files must use .zip for bytes or .json for URL metadata. Binary data
    cannot be printed with print_response; save it or use the returned bytes.
    """
    if not isinstance(as_url, bool):
        raise ValueError('as_url must be a boolean.')
    if print_response and not as_url:
        raise ValueError('Binary calculation results cannot be printed; use output_file or as_url=True.')
    output_path = Path(output_file) if output_file is not None else None
    extension = '.json' if as_url else '.zip'
    if output_path is not None and output_path.suffix.lower() != extension:
        raise ValueError(f'Gridded calculation output files must use {extension} for this response format.')

    body = {
        'model': model,
        'calculation': calculation,
        'as_url': as_url,
    }
    for name, value in (
        ('initialization_time', initialization_time),
        ('forecast_hours', forecast_hours), ('lat_range', lat_range), ('lon_range', lon_range),
    ):
        if value is not None:
            body[name] = value

    response = make_api_request(
        f'{API_BASE_URL}/insights/v1/custom-calculations/gridded',
        method='POST', json=body, as_json=as_url,
    )
    if as_url:
        _write_json_response(response, output_path, print_response)
        return response

    archive = response.content
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(archive)
    return archive


def calculate_points(calculation, coordinates, *, model='wm-6',
                     initialization_time=None, forecast_hours=None,
                     output_file=None, print_response=False):
    """Return calculated values at semicolon-separated latitude,longitude pairs.

    coordinates is a string such as '37.77,-122.42;34.05,-118.24'. Omit the
    ISO 8601 initialization_time to use the latest complete update. forecast_hours
    accepts an integer or a nonempty list; omit it to calculate every available
    hour. The complete JSON response retains coordinate order, null values,
    grid metadata and forecast_hour_errors for skipped hours. Output files must
    use .json. Calculation syntax and data availability are checked by the API.
    """
    if not isinstance(coordinates, str) or not coordinates.strip():
        raise ValueError('coordinates must be a nonempty string of latitude,longitude pairs.')
    output_path = Path(output_file) if output_file is not None else None
    if output_path is not None and output_path.suffix.lower() != '.json':
        raise ValueError('Point calculation output files must use .json.')

    body = {'model': model, 'calculation': calculation, 'coordinates': coordinates}
    if initialization_time is not None:
        body['initialization_time'] = initialization_time
    if forecast_hours is not None:
        body['forecast_hours'] = forecast_hours

    response = make_api_request(
        f'{API_BASE_URL}/insights/v1/custom-calculations/points',
        method='POST', json=body,
    )
    _write_json_response(response, output_path, print_response)
    return response


def calculate_threshold(calculation, bounds, threshold, *,
                        model='wm-6', initialization_time=None, forecast_hours=None,
                        output_file=None, print_response=False):
    """Return GeoJSON polygons meeting an absolute or percentile threshold.

    Omit the ISO 8601 initialization_time to use the latest complete update.
    bounds contains min_lat, max_lat, min_lon and max_lon; unlike gridded
    subsetting, it cannot cross the dateline.
    threshold is either {'kind': 'absolute', 'value': number, 'comparison':
    'at_or_above' or 'at_or_below'}, or {'kind': 'percentile', 'percentile': number,
    'direction': 'highest' or 'lowest'}.

    forecast_hours accepts an integer or a nonempty list; omission means every
    available hour. Return the full FeatureCollection with calculation metadata,
    each feature's grid_calculation, and forecast_hour_errors for skipped hours.
    Output files may use .json or .geojson. The API validates bounds, thresholds
    and calculation syntax.
    """
    output_path = Path(output_file) if output_file is not None else None
    if output_path is not None and output_path.suffix.lower() not in ('.json', '.geojson'):
        raise ValueError('Threshold calculation output files must use .json or .geojson.')

    body = {
        'model': model,
        'calculation': calculation,
        'bounds': bounds,
        'threshold': threshold,
    }
    if initialization_time is not None:
        body['initialization_time'] = initialization_time
    if forecast_hours is not None:
        body['forecast_hours'] = forecast_hours

    response = make_api_request(
        f'{API_BASE_URL}/insights/v1/custom-calculations/threshold',
        method='POST', json=body,
    )
    _write_json_response(response, output_path, print_response)
    return response
