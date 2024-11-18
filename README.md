# windborne: a Python Library for interacting with WindBorne Data and Forecasts API

windborne is a Python library designed to interact seamlessly with the WindBorne Data API, facilitating efficient retrieval and management of atmospheric data collected by WindBorne's global constellation of smart weather balloons. We soon intend to integrate Forecasts API to this library as well!

## Installation

Install the library using pip:

```bash
pip install windborne
```

## Configuration

Before using the library, set your WindBorne API credentials as environment variables:

```bash
export WB_CLIENT_ID='your_client_id'
export WB_API_KEY='your_api_key'
```
WindBorne uses API keys to authenticate API requests. If an API request is not properly authenticated, it will fail.

Replace `'your_client_id'` and `'your_api_key'` with the credentials provided. To get an API key, email data@windbornesystems.com.

## Usage Examples

Below are examples demonstrating how to use each endpoint and utility function provided by the windborne library.

### 1. Fetch Observations

Retrieve observations with optional filtering parameters:

```python
import windborne as wb

observations = wb.get_observations(
    since="2024-11-15 00:00:00"
)

print(observations)
```

You can save the observations in a .json file.

```python
import windborne as wb

wb.get_observations(since="2024-11-15 00:00:00", save_to_file="observations.json")
```


**Parameters:**

- `since`: Start fetching data from this timestamp.
- `min_time` and `max_time`: Filter observations within this time range.
- `include_ids`, `include_mission_name`: Include additional information if set to `True`.
- `mission_id`: Filter observations from a specific mission.
- `min_latitude`, `max_latitude`, `min_longitude`, `max_longitude`: Geographic bounds for filtering.

### 2. Fetch Super Observations

Retrieve super observations with optional filtering parameters:

```python
import windborne as wb

super_observations = wb.get_super_observations(
    since="2024-11-15 00:00:00"
)

print(super_observations)
```

You can save the observations in a .json file.

```python
import windborne as wb

wb.get_super_observations(since="2024-11-15 00:00:00", save_to_file="observations.json")

```

**Parameters:**

- `since`: Start fetching data from this timestamp.
- `min_time` and `max_time`: Filter observations within this time range.
- `include_ids`, `include_mission_name`: Include additional information if set to `True`.
- `mission_id`: Filter observations from a specific mission.

### 3. Retrieve Flying Missions

Get a list of currently flying missions:
You may use pprint to display the missions.

```python
import windborne as wb
from pprint import pprint

flying_missions = wb.get_flying_missions()
pprint(flying_missions)
```

### 4. Retrieve Mission Launch Site

Get the launch site information for a specific mission:

```python
import windborne as wb

mission_id = "494f8cb2-5fed-4c81-b3c4-5eacaa2ba4e0"
launch_site_info = wb.get_mission_launch_site(mission_id)
print(launch_site_info)
```

To save mission's launch site in a .json file:

```python
import windborne as wb

wb.get_mission_launch_site(mission_id, save_to_file="mission_launch_site.json")
```
### 5. Retrieve Predicted Path

Get the predicted path for a specific mission:

```python
import windborne as wb

mission_id = "494f8cb2-5fed-4c81-b3c4-5eacaa2ba4e0"
predicted_path = wb.get_predicted_path(mission_id)
print(predicted_path)
```

To save mission's predicted path in a .json file:

```python
import windborne as wb

wb.predicted_path(mission_id, save_to_file="mission_predicted_path.json")
```

### 6. Poll Observations Continuously

Continuously poll the observations endpoint at a specified interval:

```python
import windborne as wb

# Poll every 60 seconds
poll_observations(interval=60, params={"since": "2024-11-01 00:00:00"})
```

**Parameters:**

- `interval`: Time in seconds between each poll.
- `params`: Dictionary of parameters to pass to `get_observations`.

### 7. Sync Data to AWS S3

Upload data to an AWS S3 bucket:

```python
import windborne as wb

data = {"key": "value"}  # Replace with actual data
bucket_name = "your-s3-bucket"
object_name = "data.json"

wb.sync_to_s3(data, bucket_name, object_name)
```

**Parameters:**

- `data`: Data to upload.
- `bucket_name`: Name of the S3 bucket.
- `object_name`: S3 object name (e.g., file name).

## Additional Information

For more details on the WindBorne Data and Forecasts API, refer to the official documentation:

- [WindBorne Systems Data API](https://windbornesystems.com/docs/api/data)

- [WindBorne Systems Forecasts API](https://windbornesystems.com/docs/api/forecasts)

Ensure you have the necessary API credentials and permissions to access the endpoints.

If you encounter issues or have questions, please ask your WindBorne Systems contact.
