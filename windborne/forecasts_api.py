from .config import FORECASTS_API_BASE_URL, make_api_request
from .utils import to_unix_timestamp, save_response_to_file

from datetime import datetime
import re
import json

TCS_SUPPORTED_FORMATS = ('.csv', '.json', '.geojson', '.gpx', '.kml', 'little_r')

def parse_initialization_time(initialization_time):
    """
    Parse and validate initialization time.

    Args:
        initialization_time (str): Date in either ISO 8601 format (YYYY-MM-DDTHH:00:00)
                                 or compact format (YYYYMMDDHH)
                                 where HH must be 00, 06, 12, or 18

    Returns:
        str: Validated initialization time in ISO format, or None if invalid
    """
    if initialization_time is None:
        return None

    # Regex patterns for both formats
    compact_pattern = r'^\d{10}$'
    iso_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:00:00$'

    is_compact = bool(re.match(compact_pattern, initialization_time))
    is_iso = bool(re.match(iso_pattern, initialization_time))

    if not (is_compact or is_iso):
        print(f"Invalid date format: {initialization_time}")
        print("Please use either:")
        print("  - Compact format: 'YYYYMMDDHH' (e.g., 2024073112)")
        print("  - ISO format: 'YYYY-MM-DDTHH:00:00' (e.g., 2024-07-31T12:00:00)")
        exit(2)

    try:
        if is_compact:
            parsed_date = datetime.strptime(initialization_time, '%Y%m%d%H')
            hour = parsed_date.hour
            initialization_time = parsed_date.strftime('%Y-%m-%dT%H:00:00')
        else:
            parsed_date = datetime.strptime(initialization_time, '%Y-%m-%dT%H:00:00')
            hour = parsed_date.hour

        # Check if someone is coming from the future
        current_time = datetime.now()
        if parsed_date > current_time:
            print("Looks like you are coming from the future!")
            print("\nAs Cavafy might say:\n"
                  "'For some, the future is a beacon of hope,\n"
                  "A path unwritten, yet vast in scope.\n"
                  "Let it come with wisdom and grace,\n"
                  "And find us ready to embrace its face.'\n")
            exit(4444)
        # Check if hour is aligned with our forecasts runs
        if hour not in [0, 6, 12, 18]:
            print(f"Invalid initialization hour: {hour:02d}")
            print("Hour must be one of: 00, 06, 12, 18")
            exit(22)
        return initialization_time

    except ValueError:
        print(f"Invalid date values in: {initialization_time}")
        print("Make sure your date values are valid")
        return None

def get_point_forecasts(coordinates, min_forecast_hour=None, max_forecast_hour=None, initialization_time=None, save_to_file=None):
    url = f"{FORECASTS_API_BASE_URL}/points.json"
    params = {"coordinates": coordinates}

    if not coordinates:
        print("To get points forecasts you must provide coordinates.")
        return
    if min_forecast_hour:
        min_forecast_hour = to_unix_timestamp(min_forecast_hour)
        params["min_forecast_hour"] = min_forecast_hour
    if max_forecast_hour:
        max_forecast_hour = to_unix_timestamp(max_forecast_hour)
        params["max_forecast_hour"] = max_forecast_hour
    if initialization_time:
        initialization_time = to_unix_timestamp(initialization_time)
        params["initialization_time"] = initialization_time

    response = make_api_request(url, params=params)

    save_response_to_file(save_to_file, response, csv_data_key='forecasts')

    return response

def get_tropical_cyclones(initialization_time=None, save_to_file=None):
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
    url = f"{FORECASTS_API_BASE_URL}/tropical_cyclones"
    params = {}

    if initialization_time:
        initialization_time_parsed = parse_initialization_time(initialization_time)
        params["initialization_time"] = initialization_time_parsed
    else:
        # Make this for our displaying message when no active tcs found
        initialization_time = 'latest'

    response = make_api_request(url, params=params)

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
            print(f"There are no active tropical cyclones for initialization time: {initialization_time}")
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
            save_response_to_file(save_to_file, {'prediction': flattened_data}, csv_data_key='prediction')
        elif save_to_file.lower().endswith('.json'):
            # Direct save for JSON
            save_response_to_file(save_to_file, response)
        elif save_to_file.lower().endswith('.geojson'):
            save_as_geojson(save_to_file, response)
        elif save_to_file.lower().endswith('.gpx'):
            save_as_gpx(save_to_file, response)
        elif save_to_file.lower().endswith('.kml'):
            save_as_kml(save_to_file, response)
        elif save_to_file.lower().endswith('.little_r'):
            save_as_little_r(save_to_file, response)
    return response


########################################################################################################################
# HANDLE USEFUL FORMAT
#
# - .geojson
# - GPX
# - KML
# - little_r
########################################################################################################################

def print_tc_supported_formats():
    """Print supported file formats for saving tcs data."""
    print("Supported formats:")
    for format in TCS_SUPPORTED_FORMATS:
        print(f"  - {format}")

def save_as_geojson(filename, cyclone_data):
    """Convert and save cyclone data as GeoJSON."""
    features = []
    for cyclone_id, tracks in cyclone_data.items():
        coordinates = [[float(track['longitude']), float(track['latitude'])] for track in tracks]
        feature = {
            "type": "Feature",
            "properties": {
                "cyclone_id": cyclone_id,
                "start_time": tracks[0]['time'],
                "end_time": tracks[-1]['time']
            },
            "geometry": {
                "type": "LineString",
                "coordinates": coordinates
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
    """Convert and save cyclone data as GPX."""
    gpx = '<?xml version="1.0" encoding="UTF-8"?>\n'
    gpx += '<gpx version="1.1" creator="Windborne">\n'

    for cyclone_id, tracks in cyclone_data.items():
        gpx += f'  <trk>\n    <name>{cyclone_id}</name>\n    <trkseg>\n'
        for track in tracks:
            gpx += f'      <trkpt lat="{track["latitude"]}" lon="{track["longitude"]}">\n'
            gpx += f'        <time>{track["time"]}</time>\n'
            gpx += '      </trkpt>\n'
        gpx += '    </trkseg>\n  </trk>\n'

    gpx += '</gpx>'

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(gpx)
    print("Saved to", filename)

def save_as_kml(filename, cyclone_data):
    """Convert and save cyclone data as KML."""
    kml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    kml += '<kml xmlns="http://www.opengis.net/kml/2.2">\n<Document>\n'

    for cyclone_id, tracks in cyclone_data.items():
        kml += f'  <Placemark>\n    <name>{cyclone_id}</name>\n    <LineString>\n'
        kml += '      <coordinates>\n'
        coordinates = [f'        {track["longitude"]},{track["latitude"]},{0}' for track in tracks]
        kml += '\n'.join(coordinates)
        kml += '\n      </coordinates>\n    </LineString>\n  </Placemark>\n'

    kml += '</Document>\n</kml>'

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(kml)
    print("Saved to", filename)

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