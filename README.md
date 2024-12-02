# WindBorne API python library

A Python lib for interacting with the WindBorne API to fetch and process observations and forecast data.

## Installation

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


## Features

- Poll observations within specified time ranges
- Fetch filtered observations and super-observations
- Get information about currently flying missions
- Retrieve mission launch sites and predicted flight paths
- Save data in CSV, JSON, or Little-R formats
- Command-line interface for all operations

## Command Line Usage
### Poll Observations
```bash
windborne poll-observations start_time [end_time] output [-i INTERVAL] [-b BUCKET_HOURS]

# Example: Poll from 2024-12-01 21:00 UTC, save in 6-hour buckets as CSV
windborne poll-observations 2024-12-01_21:00 csv -b 6

# Example: Poll to single file
windborne poll-observations 2024-12-01_21:00 output.csv
```

### Get Observations
```bash
windborne observations [-s SINCE] [-mt MIN_TIME] [-xt MAX_TIME] [-m MISSION_ID] 
              [-ml MIN_LAT] [-xl MAX_LAT] [-mg MIN_LON] [-xg MAX_LON]
              [-id] [-mn] [-u] [output]

# Example: Get observations with mission name
windborne observations -s 2024-03-01_00:00 -mn output.csv
```

### Get Super Observations
```bash
windborne super-observations [-s SINCE] [-mt MIN_TIME] [-xt MAX_TIME] [-m MISSION_ID]
                [-id] [-mn] [-u] [output]
```

### Get Flying Missions
```bash
windborne flying-missions [output]
```

### Get Mission Launch Site
```bash
windborne launch-site MISSION_ID [output]
```

### Get Predicted Path
```bash
windborne predict-path MISSION_ID [output]
```

## Python API

```python
from windborne import (
    poll_observations,
    get_observations,
    get_super_observations,
    get_flying_missions,
    get_mission_launch_site,
    get_predicted_path
)

# Poll observations with time bucketing
poll_observations(
    start_time='2024-03-01_21:00',
    bucket_hours=6,
    output_format='csv'
)

# Get filtered observations
observations = get_observations(
    since='2024-03-01_00:00',
    min_latitude=45.0,
    max_latitude=50.0,
    include_mission_name=True
)

# Get currently flying missions
missions = get_flying_missions()
```

## Data Formats

### CSV Output Fields
- timestamp
- time
- latitude
- longitude
- altitude
- humidity
- mission_name
- pressure
- specific_humidity
- speed_u
- speed_v
- temperature

### Little-R Format
Supports standard Little-R format with:
- Pressure (Pa)
- Temperature (K)
- Wind components (u, v)
- Humidity
- Location data (lat, lon, alt)

## Error Handling
- Validates input parameters and file formats
- Retries failed API requests with 60-second intervals
- Provides clear error messages for invalid mission IDs
- Handles missing or null data gracefully

## Additional Information

For more details on the WindBorne Data and Forecasts API, refer to the official documentation:

- [WindBorne Systems Data API](https://windbornesystems.com/docs/api/data)

- [WindBorne Systems Forecasts API](https://windbornesystems.com/docs/api/forecasts)

Ensure you have the necessary API credentials and permissions to access the endpoints.

If you encounter issues or have questions, please ask your WindBorne Systems contact.
