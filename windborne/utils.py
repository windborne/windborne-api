from .config import CLIENT_ID, API_KEY

import requests
import jwt
import time
import re
from datetime import datetime
import boto3
import io
import json
import csv

import numpy as np

# Authenticate requests using a JWT | no reveal of underlying key
def make_api_request(url, params=None, return_type=None):
    signed_token = jwt.encode({
        'client_id': CLIENT_ID,
        'iat': int(time.time()),
    }, API_KEY, algorithm='HS256')

    try:
        if params:
            response = requests.get(url, auth=(CLIENT_ID, signed_token), params=params)
        else:
            response = requests.get(url, auth=(CLIENT_ID, signed_token))

        response.raise_for_status()

        if return_type is None:
            # For Data API
            return response.json()
        elif return_type == 'npy':
            # For Forecasts API (except tcs) --> return whole response not .json to obtain S3 url
            return response
    except requests.exceptions.HTTPError as http_err:
        if http_err.response.status_code == 403:
            print("--------------------------------------")
            print("We couldn't authenticate your request.")
            print("--------------------------------------")
            print("Please make sure you have properly set your WB_CLIENT_ID and WB_API_KEY.\n")
            print("You can verify this by running\necho $WB_CLIENT_ID and echo $WB_API_KEY in your terminal.\n")
            print("To get an API key, email data@windbornesystems.com.")
        elif http_err.response.status_code in [404, 400]:
            print("-------------------------------------------------------")
            print("Our server couldn't find the information you requested.")
            print("-------------------------------------------------------")
            print(f"URL: {url}")
            print(f"Error: {http_err.response.status_code}")
            print("-------------------------------------------------------")
            if params:
                print("Parameters provided:")
                for key, value in params.items():
                    print(f"  {key}: {value}")
            else:
                if 'missions/' in url:
                    mission_id = url.split('/missions/')[1].split('/')[0]
                    print(f"Mission ID provided: {mission_id}")
                    print(f"We couldn't find a mission with id: {mission_id}")
        elif http_err.response.status_code == 502:
            retries = 1
            while response.status_code == 502 and retries < 5:
                print("502 Bad Gateway, sleeping and retrying")
                time.sleep(2**retries)
                response = requests.get(url, auth=(CLIENT_ID, signed_token))
                retries += 1
        else:
            print(f"HTTP error occurred\n\n{http_err}")
            if params:
                print("Parameters provided:")
                for key, value in params.items():
                    print(f"  {key}: {value}")
        exit(http_err.response.status_code)
    except requests.exceptions.ConnectionError as conn_err:
        print(f"Connection error occurred\n\n{conn_err}")
    except requests.exceptions.Timeout as timeout_err:
        print(f"Timeout error occurred\n\n{timeout_err}")
    except requests.exceptions.RequestException as req_err:
        print(f"An error occurred\n\n{req_err}")

# Supported date formats
# YYYY-MM-DD HH:MM:SS, YYYY-MM-DD_HH:MM and ISO strings
def to_unix_timestamp(date_string):
    """
    Converts a date string or integer to a UNIX timestamp.
    Supports various date formats and handles future dates gracefully.

    Args:
        date_string (str | int | None): The date string to convert or an integer UNIX timestamp.

    Returns:
        int | None: The UNIX timestamp or None if the input is None.
    """
    if date_string is None:
        return None

    # Supported date formats
    formats = [
        "%Y-%m-%d %H:%M:%S",        # e.g., 2024-12-05 14:48:00
        "%Y-%m-%d_%H:%M",           # e.g., 2024-12-05_14:48
        "%Y-%m-%dT%H:%M:%S.%fZ",    # e.g., 2024-12-05T14:48:00.000Z
    ]
    current_time = datetime.now()

    for fmt in formats:
        try:
            dt = datetime.strptime(date_string, fmt)
            if dt > current_time:
                print(
                    "Looks like you are coming from the future!\n\n"
                    "As Cavafy might say:\n"
                    "'For some, the future is a beacon of hope,\n"
                    " A path unwritten, yet vast in scope.\n"
                    " Let it come with wisdom and grace,\n"
                    " And find us ready to embrace its face.'\n"
                )
            return int(dt.timestamp())
        except ValueError:
            # Try the next format
            continue

    # If no formats match, raise an error
    print("Invalid date format. Please use one of the supported formats:\n"
            "- YYYY-MM-DD HH:MM:SS\n"
            "- YYYY-MM-DD_HH:MM\n"
            "- YYYY-MM-DDTHH:MM:SS.fffZ")
    exit(11)

# Supported date format
# Compact format YYYYMMDDHH
def parse_initialization_time(initialization_time):
    """
    Parse and validate initialization time using regex.

    Args:
        initialization_time (str): Date in compact format (YYYYMMDDHH)
                                 where HH must be 00, 06, 12, or 18

    Returns:
        str: Validated initialization time in ISO format, or None if invalid
    """
    if initialization_time is None:
        return None

    # Regex for compact format (YYYYMMDDHH)
    # Year --> XYZW
    # Month --> 0[1-9] or 1[0-2]
    # Day -->  0[1-9] or 1[0-2]
    # Hour --> 00 | 06 | 12 | 18
    compact_pattern = r'^([0-9][0-9][0-9][0-9])(0[1-9]|1[0-2])(0[1-9]|1[1-9]|2[1-9]|3[01])(00|06|12|18)$'

    compact_match = re.match(compact_pattern, initialization_time)

    if not compact_match:
        print(f"Invalid date format: {initialization_time}\n")
        print("Please use:")
        print("  - Compact format: 'YYYYMMDDHH' (e.g., 2024073112)")
        print("  - Hour must be one of: 00, 06, 12, 18")
        exit(2)

    try:
        year, month, day, hour = compact_match.groups()
        parsed_date = datetime(int(year), int(month), int(day), int(hour))
        initialization_time = parsed_date.strftime('%Y-%m-%dT%H:00:00')

        # Check if someone is coming from the future
        current_time = datetime.now()
        if parsed_date > current_time:
            print("Looks like you are coming from the future!")
            print("\nAs Cavafy might say:\n"
                  "'For some, the future is a beacon of hope,\n"
                  " A path unwritten, yet vast in scope.\n"
                  " Let it come with wisdom and grace,\n"
                  " And find us ready to embrace its face.'\n")
            exit(4444)
        return initialization_time

    except ValueError:
        print(f"Invalid date values in: {initialization_time}")
        print("Make sure your date values are valid")
        exit(2)

# Save API response data to a file in either JSON or CSV format
def save_csv_json(save_to_file, response, csv_data_key=None):
    """
    Save Data API response data to a file in either JSON or CSV format.

    Args:
        save_to_file (str): The file path where the response will be saved.
        response (dict or list): The response data to save.
        csv_data_key (str, optional): Key to extract data for CSV. Defaults to None.
    """
    if '.' not in save_to_file:
        print("You have to provide a file type for your filename.")
        print("Supported formats:")
        print("  - .csv")
        print("  - .json")
        exit(2)
    elif not response:
        print("There are no available data to save to file.")
        exit(1)
    elif save_to_file.lower().endswith('.json'):
        with open(save_to_file, 'w', encoding='utf-8') as f:
            json.dump(response, f, indent=4)
        print("Saved to", save_to_file)
    elif save_to_file.lower().endswith('.csv'):
    # Extract data for CSV if a key is provided
        data = response if not csv_data_key else response.get(csv_data_key, [])
        if not data:
            print("No data available to save to CSV.")
            return
        # Handle nested list case (for forecasts)
        if isinstance(data, list) and data and isinstance(data[0], list):
            data = data[0]  # Take the first list from nested lists
        # If data is a list of dictionaries, write each dictionary as a row
        if isinstance(data, list) and all(isinstance(item, dict) for item in data):
            headers = data[0].keys() if data else []
        # If data is a dictionary, determine if it contains a list of dictionaries or is a flat dictionary
        elif isinstance(data, dict):
            # If the dictionary contains a list of dictionaries, use the keys of the first dictionary in the list as headers
            for key, value in data.items():
                if isinstance(value, list) and all(isinstance(item, dict) for item in value):
                    headers = value[0].keys() if value else []
                    data = value
                    break
            else:
                # If no lists of dictionaries are found, use the keys of the dictionary as headers
                headers = data.keys()
                data = [data]
        else:
            print("Unsupported data format for CSV.")
            exit(5)

        # Write data to CSV
        with open(save_to_file, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=headers)
            writer.writeheader()
            for row in data:
                # If no value available write 'None'
                row_data = {k: 'None' if v is None or v == '' else v for k, v in row.items()}
                writer.writerow(row_data)
            print("Saved to", save_to_file)
    else:
        print("Unsupported file format. Please use either .json or .csv.")
        exit(4)

# Download and save a file in .npy upon provided an S3 link
def download_and_save_npy(save_to_file, response):
    """
    Downloads data from a presigned S3 url contained in a response and saves it as a .npy file.

    Args:
        save_to_file (str): Path where to save the .npy file
        response (str): Response that contains the S3 url to download the data from

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Download the file
        print(f"Downloading data")
        # Load the data into memory
        data = np.load(io.BytesIO(response.content))

        # Save the data
        np.save(save_to_file, data)
        print(f"Data Successfully saved to {save_to_file}")
        return True

    except requests.exceptions.RequestException as e:
        print(f"Error downloading the file: {e}")
        return False
    except Exception as e:
        print(f"Error processing the file: {e}")
        return False

def save_as_geojson(filename, cyclone_data):
    """Convert and save cyclone data as GeoJSON, handling meridian crossing."""
    features = []
    for cyclone_id, tracks in cyclone_data.items():
        # Initialize lists to store line segments
        line_segments = []
        current_segment = []

        for i in range(len(tracks)):
            lon = float(tracks[i]['longitude'])
            lat = float(tracks[i]['latitude'])

            if not current_segment:
                current_segment.append([lon, lat])
                continue

            prev_lon = current_segment[-1][0]

            # Check if we've crossed the meridian (large longitude jump)
            if abs(lon - prev_lon) > 180:
                # If previous longitude was positive and current is negative
                if prev_lon > 0 and lon < 0:
                    # Add point at 180° with same latitude
                    current_segment.append([180, lat])
                    line_segments.append(current_segment)
                    # Start new segment at -180°
                    current_segment = [[-180, lat], [lon, lat]]
                # If previous longitude was negative and current is positive
                elif prev_lon < 0 and lon > 0:
                    # Add point at -180° with same latitude
                    current_segment.append([-180, lat])
                    line_segments.append(current_segment)
                    # Start new segment at 180°
                    current_segment = [[180, lat], [lon, lat]]
            else:
                current_segment.append([lon, lat])

        # Add the last segment if it's not empty
        if current_segment:
            line_segments.append(current_segment)

        # Create a MultiLineString feature with all segments
        feature = {
            "type": "Feature",
            "properties": {
                "cyclone_id": cyclone_id,
                "start_time": tracks[0]['time'],
                "end_time": tracks[-1]['time']
            },
            "geometry": {
                "type": "MultiLineString",
                "coordinates": line_segments
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
    """Convert and save cyclone data as GPX, handling meridian crossing."""
    gpx = '<?xml version="1.0" encoding="UTF-8"?>\n'
    gpx += '<gpx version="1.1" creator="Windborne" xmlns="http://www.topografix.com/GPX/1/1">\n'

    for cyclone_id, tracks in cyclone_data.items():
        gpx += f'  <trk>\n    <name>{cyclone_id}</name>\n'

        current_segment = []
        segment_count = 1

        for i in range(len(tracks)):
            lon = float(tracks[i]['longitude'])
            lat = float(tracks[i]['latitude'])

            if not current_segment:
                current_segment.append(tracks[i])
                continue

            prev_lon = float(current_segment[-1]['longitude'])

            # Check if we've crossed the meridian
            if abs(lon - prev_lon) > 180:
                # Write the current segment
                gpx += '    <trkseg>\n'
                for point in current_segment:
                    gpx += f'      <trkpt lat="{point["latitude"]}" lon="{point["longitude"]}">\n'
                    gpx += f'        <time>{point["time"]}</time>\n'
                    gpx += '      </trkpt>\n'
                gpx += '    </trkseg>\n'

                # Start new segment
                current_segment = [tracks[i]]
                segment_count += 1
            else:
                current_segment.append(tracks[i])

        # Write the last segment if it's not empty
        if current_segment:
            gpx += '    <trkseg>\n'
            for point in current_segment:
                gpx += f'      <trkpt lat="{point["latitude"]}" lon="{point["longitude"]}">\n'
                gpx += f'        <time>{point["time"]}</time>\n'
                gpx += '      </trkpt>\n'
            gpx += '    </trkseg>\n'

        gpx += '  </trk>\n'

    gpx += '</gpx>'

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(gpx)
    print(f"Saved to {filename}")

def save_as_kml(filename, cyclone_data):
    """Convert and save cyclone data as KML, handling meridian crossing."""
    kml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    kml += '<kml xmlns="http://www.opengis.net/kml/2.2">\n<Document>\n'

    for cyclone_id, tracks in cyclone_data.items():
        kml += f'  <Placemark>\n    <name>{cyclone_id}</name>\n    <MultiGeometry>\n'

        current_segment = []

        for i in range(len(tracks)):
            lon = float(tracks[i]['longitude'])
            lat = float(tracks[i]['latitude'])

            if not current_segment:
                current_segment.append(tracks[i])
                continue

            prev_lon = float(current_segment[-1]['longitude'])

            # Check if we've crossed the meridian
            if abs(lon - prev_lon) > 180:
                # Write the current segment
                kml += '      <LineString>\n        <coordinates>\n'
                coordinates = [f'          {track["longitude"]},{track["latitude"]},{0}'
                               for track in current_segment]
                kml += '\n'.join(coordinates)
                kml += '\n        </coordinates>\n      </LineString>\n'

                # Start new segment
                current_segment = [tracks[i]]
            else:
                current_segment.append(tracks[i])

        # Write the last segment if it's not empty
        if current_segment:
            kml += '      <LineString>\n        <coordinates>\n'
            coordinates = [f'          {track["longitude"]},{track["latitude"]},{0}'
                           for track in current_segment]
            kml += '\n'.join(coordinates)
            kml += '\n        </coordinates>\n      </LineString>\n'

        kml += '    </MultiGeometry>\n  </Placemark>\n'

    kml += '</Document>\n</kml>'

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(kml)
    print(f"Saved to {filename}")

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

def sync_to_s3(data, bucket_name, object_name):
    s3 = boto3.client("s3")
    s3.put_object(Body=str(data), Bucket=bucket_name, Key=object_name)