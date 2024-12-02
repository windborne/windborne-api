from datetime import datetime
import boto3
import json
import csv


# Supported date formats
# YYYY-MM-DD HH:MM:SS and YYYY-MM-DD_HH:MM
def to_unix_timestamp(date_string):
    if date_string is None:
        return None
    if isinstance(date_string, int):
        return date_string  # If it's already an integer, return as is
    if isinstance(date_string, str):
        formats = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d_%H:%M"]
        current_time = datetime.now()
        for fmt in formats:
            try:
                dt = datetime.strptime(date_string, fmt)
                if dt > current_time:
                    print("Looks like you are coming from the future!")
                    print("\nAs Cavafy might say:\n"
                          "'For some, the future is a beacon of hope,\n"
                          "A path unwritten, yet vast in scope.\n"
                          "Let it come with wisdom and grace,\n"
                          "And find us ready to embrace its face.'\n")
                return int(dt.timestamp())
            except ValueError:
                continue
        print("Invalid date format. Use 'YYYY-MM-DD HH:MM:SS' or 'YYYY-MM-DD_HH:MM'.")
        exit(2)

# Save API response data to a file in either JSON or CSV format
def save_response_to_file(save_to_file, response, csv_data_key=None):
    """
    Save API response data to a file in either JSON or CSV format.

    Args:
        save_to_file (str): The file path where the response will be saved.
        response (dict or list): The response data to save.
        csv_data_key (str, optional): Key to extract data for CSV. Defaults to None.
    """
    if not save_to_file:
        return
    elif not response:
        print("There are no available data to save to file.")
        exit(1)
    elif save_to_file.endswith('.json'):
        with open(save_to_file, 'w', encoding='utf-8') as f:
            json.dump(response, f, indent=4)
        print("Saved to", save_to_file)
    elif save_to_file.endswith('.csv'):
        # Extract data for CSV if a key is provided
        data = response if not csv_data_key else response.get(csv_data_key, [])
        if not data:
            print("No data available to save to CSV.")
            return
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
                writer.writerow(row)
            print("Saved to", save_to_file)
    else:
        print("Unsupported file format. Please use either .json or .csv.")
        exit(4)

def sync_to_s3(data, bucket_name, object_name):
    s3 = boto3.client("s3")
    s3.put_object(Body=str(data), Bucket=bucket_name, Key=object_name)