import os
import re
from datetime import datetime, timezone
import dateutil.parser
import json
import csv


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
    if isinstance(date_string, int):
        return date_string  # If it's already an integer, return as is
    if isinstance(date_string, str):
        # Supported date formats
        formats = [
            "%Y-%m-%d %H:%M:%S",        # e.g., 2024-12-05 14:48:00
            "%Y-%m-%d_%H:%M",           # e.g., 2024-12-05_14:48
            "%Y-%m-%dT%H:%M:%S.%fZ",    # e.g., 2024-12-05T14:48:00.000Z
            "%Y%m%d%H",                 # e.g., 2024120514
        ]
        for fmt in formats:
            try:
                dt = datetime.strptime(date_string, fmt).replace(tzinfo=timezone.utc)
                return int(dt.timestamp())
            except ValueError:
                continue

        # If no formats match, raise an error
        print("Invalid date format. Please use one of the supported formats:\n"
              "- YYYY-MM-DD HH:MM:SS\n"
              "- YYYY-MM-DD_HH:MM\n"
              "- YYYY-MM-DDTHH:MM:SS.fffZ\n"
              "- YYYYMMDDHH")
        exit(1)

# Supported date format
# Compact format YYYYMMDDHH
def parse_time(time, init_time_flag=None, require_past=False):
    """
    Parse and validate initialization time with support for multiple formats.
    Returns validated initialization time in ISO format, or None if invalid.
    """
    if time is None:
        return None

    try:
        # Try parsing compact format first (YYYYMMDDHH)
        if re.match(r'^\d{10}$', time):
            try:
                parsed_date = datetime.strptime(time, "%Y%m%d%H")
            except (ValueError, OverflowError):
                print(f"Invalid date values in: {time}")
                print("Make sure your date values are valid")
                exit(2)

            if init_time_flag and parsed_date.hour not in [0, 6, 12, 18]:
                print("Initialization time hour must be 00, 06, 12, or 18")
                exit(2)
        else:
            try:
                parsed_date = dateutil.parser.parse(time)
            except (ValueError, OverflowError, TypeError):
                print(f"Invalid date format: {time}\n")
                print("Please use one of these formats:")
                print("  - Compact: 'YYYYMMDDHH' (e.g., 2024073112)")
                print("  - ISO: 'YYYY-MM-DDTHH' or 'YYYY-MM-DDTHH:00:00'")
                print("  - Initialization time hour must be 00, 06, 12, or 18")
                exit(2)

        if require_past and parsed_date > datetime.now():
            print(f"Invalid date: {time} -- cannot be in the future")
            exit(2)

        return parsed_date.strftime('%Y-%m-%dT%H:00:00')

    except Exception:
        print(f"Invalid date format: {time}")
        print("Please check your input format and try again")
        exit(2)


def save_arbitrary_response(output_file, response, csv_data_key=None):
    """
    Save Data API response data to a file in either JSON or CSV format.

    Args:
        output_file (str): The file path where the response will be saved.
        response (dict or list): The response data to save.
        csv_data_key (str, optional): Key to extract data for CSV. Defaults to None.
    """
    # Create directory path if it doesn't exist
    directory = os.path.dirname(output_file)
    if directory and not os.path.isdir(directory):
        os.makedirs(directory, exist_ok=True)

    if '.' not in output_file:
        print("You have to provide a file type for your filename.")
        print("Supported formats:")
        print("  - .csv")
        print("  - .json")
        exit(2)
    elif not response:
        print("There are no available data to save to file.")
        exit(1)
    elif output_file.lower().endswith('.json'):
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(response, f, indent=4)
        print("Saved to", output_file)
    elif output_file.lower().endswith('.csv'):
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
        with open(output_file, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=headers)
            writer.writeheader()
            for row in data:
                # If no value available write 'None'
                row_data = {k: 'None' if v is None or v == '' else v for k, v in row.items()}
                writer.writerow(row_data)
            print("Saved to", output_file)
    else:
        print("Unsupported file format. Please use either .json or .csv.")
        exit(4)


def print_table(data, keys=None, headers=None):
    if len(data) == 0:
        print("No data found")
        return

    if keys is None:
        keys = list(data[0].keys())

    if headers is None:
        headers = keys

    # headers = ["Index", "Mission ID", "Mission Name"]
    rows = [
        [
            str(value.get(key)) if key != 'i' else str(i)
            for key in keys
        ]
        for i, value in enumerate(data, start=1)
    ]

    # Calculate column widths
    col_widths = [max(len(cell) for cell in col) + 2 for col in zip(headers, *rows)]

    # Display table
    print("".join(f"{headers[i]:<{col_widths[i]}}" for i in range(len(headers))))
    print("".join("-" * col_width for col_width in col_widths))
    for row in rows:
        print("".join(f"{row[i]:<{col_widths[i]}}" for i in range(len(row))))
