# WindBorne API
A Python library for interacting with the WindBorne API to fetch and process observations and forecasts data.

## Installation
```bash
pip install windborne

# Set credentials
export WB_CLIENT_ID='your_client_id'
export WB_API_KEY='your_api_key'
```

## Data API Commands

### poll-observations
**CLI:**
```bash
# Save to multiple files
windborne poll-observations 2024-10-12_00:00 csv
windborne poll-observations 2024-10-12_00:00 json 
windborne poll-observations 2024-10-12_00:00 little_r

# Save to single file
windborne poll-observations 2024-10-12_00:00 output.csv
windborne poll-observations 2024-10-12_00:00 output.json

# Optional args
windborne poll-observations -i 120 -b 12 -xt 2024-11-11_01:00 2024-12-14_00:00 output.csv
```

**Code:**
```python
from windborne import poll_observations

# Multiple files
poll_observations(
    start_time='2024-10-12_00:00',
    output_format='csv'  # or 'json', 'little_r'
)

# Single file
poll_observations(
    start_time='2024-10-12_00:00',
    save_to_file='output.csv'  # or .json
)

# With options
poll_observations(
    start_time='2024-10-12_00:00',
    end_time='2024-10-13_00:00',
    interval=120,
    bucket_hours=12,
    save_to_file='output.csv'
)
```

**Optional Arguments:**
- `-mt/--min`: Minimum time filter
- `-xt/--max`: Maximum time filter
- `-i/--interval`: Polling interval seconds (default: 60)
- `-b/--bucket-hours`: Hours per bucket (default: 6.0)

### observations
For more information about the meaning of available parameters you can refer to [Observations section](https://windbornesystems.com/docs/api/data#observations) on WindBorne Systems API Reference.

**CLI:**
```bash
# Basic with formats
windborne observations 2024-10-12_00:00 output.csv
windborne observations 2024-10-12_00:00 output.json

# With mission id filter
windborne observations -mt 2024-10-12_06:00 -xt 2024-10-12_12:00 -m mission123 2024-10-12_00:00  output.csv

# Geographic filters
windborne observations -ml 45.0 -xl 50.0 -mg -120.0 -xg 110.0 2024-10-12_00:00  output.csv
```

**Code:**
```python
from windborne import get_observations

observations = get_observations(
    since='2024-10-12_00:00',
    min_time='2024-10-12_06:00',
    max_time='2024-10-12_12:00',
    mission_id='mission123',
    min_latitude=45.0,
    max_latitude=50.0,
    min_longitude=-120.0,
    max_longitude=-110.0,
    include_ids=True,
    include_mission_name=True,
    include_updated_at=True,
    save_to_file='output.csv'  # or .json
)
```

### super-observations
For more information about the meaning of available parameters you can refer to [Super observations section](https://windbornesystems.com/docs/api/data#super_observations) on WindBorne Systems API Reference.

**CLI:**
```bash
# Different formats
windborne super-observations 2024-10-12_00:00 output.csv
windborne super-observations 2024-10-12_00:00 output.json

# With filters
windborne super-observations -id -mn -u 2024-10-12_00:00 output.csv
```

**Code:**
```python
from windborne import get_super_observations

super_obs = get_super_observations(
    since='2024-10-12_00:00',
    mission_id='mission123',
    include_ids=True,
    include_mission_name=True,
    include_updated_at=True,
    save_to_file='output.csv'  # or .json
)
```

### flying-missions
**CLI:**
```bash
windborne flying-missions output.json
```

**Code:**
```python
from windborne import get_flying_missions
missions = get_flying_missions(save_to_file='output.json')
```

### launch-site
**CLI:**
```bash
windborne launch-site mission123 output.json
```

**Code:**
```python
from windborne import get_mission_launch_site
site = get_mission_launch_site(mission_id='mission123', save_to_file='output.json')
```

### predict-path
**CLI:**
```bash
windborne predict-path mission123 output.json
```

**Code:**
```python
from windborne import get_predicted_path
path = get_predicted_path(mission_id='mission123', save_to_file='output.json')
```

## Forecast API Commands

### Points
**CLI:**
```bash
windborne points "40.7,-74.0" -i 2024121600 output.csv
windborne points "40.7,-74.0;34.0,-118.2" -i 2024121600 output.csv
windborne points "40.7,-74.0" -mh 0 -xh 24 -i 2024121600 output.csv
windborne points "40.7,-74.0" -mt 2024121606 -xt 2024121612 -i 2024121600 output.csv
```

**Code:**
```python
from windborne import get_point_forecasts

# To save response data in point_forecasts var
point_forecasts = get_point_forecasts(
    coordinates="40.7,-74.0;34.0,-118.2",
    min_forecast_hour=0,
    max_forecast_hour=24,
    initialization_time="2024121600")

# To save data in file
get_point_forecasts(
    coordinates="40.7,-74.0;34.0,-118.2",
    min_forecast_hour=0,
    max_forecast_hour=24,
    initialization_time="2024121600",
    save_to_file="output.csv" # .csv or .json
)
```

### Initialization times
**CLI:**
```bash
windborne init_times
```

**Code:**
```python
from windborne import get_initialization_times

initialization_times = get_initialization_times()
print(initialization_times)
```

### Gridded Forecasts Commands
Time format: YYYY-MM-DD HH:MM:SS, YYYY-MM-DD_HH:MM and ISO strings (HH: 00,06,12,18)

**CLI:**
```bash
windborne grid_temp_2m 2024121600 filename

windborne grid_dewpoint_2m 2024121600 filename ## To be added soon

windborne grid_wind_u_10m 2024121600 filename
windborne grid_wind_v_10m 2024121600 filename

windborne grid_pressure_msl 2024121600 filename

windborne grid_500hpa_geopotential 2024121600 filename
windborne grid_850hpa_geopotential 2024121600 filename

windborne grid_500hpa_wind_u 2024121600 filename
windborne grid_500hpa_wind_v 2024121600 filename

windborne grid_500hpa_temperature 2024121600 filename
windborne grid_850hpa_temperature 2024121600 filename
```

**Code:**
```python
from windborne import get_temperature_2m

# To save response to temp_2m_data var
temp_2m_data = get_temperature_2m(time="2024121600")

# To save data in a file
temp_2m_data = get_temperature_2m(time="2024121600", save_to_file="filename")
```

### Historical Forecast Commands
Time format: YYYYMMDDHH (HH: 00,06,12,18)

**CLI:**
```bash
windborne hist_temp_2m 2024121600 6 output.npy
windborne hist_500hpa_geopotential 2024121600 6 output.npy
windborne hist_500hpa_wind_u 2024121600 6 output.npy
windborne hist_500hpa_wind_v 2024121600 6 output.npy
```

**Code:**
```python
from windborne import get_historical_temperature_2m

# To save response to temp_2m_data var
hist_temp_2m_data = get_historical_temperature_2m(initialization_time="2024121600")

# To save data in a file
get_historical_temperature_2m(initialization_time="2024121600", save_to_file="filename")
```

### cyclones
**CLI:**
```bash
# Latest data
windborne cyclones

# Specific time with different formats
windborne cyclones 2024121600 output.json
windborne cyclones 2024121600 output.csv
windborne cyclones 2024121600 output.gpx
windborne cyclones 2024121600 output.geojson
windborne cyclones 2024121600 output.kml
windborne cyclones 2024121600 output.little_r
```

**Code:**
```python
from windborne import get_tropical_cyclones

# Latest data
cyclones = get_tropical_cyclones()

# With specific time and format
cyclones = get_tropical_cyclones(
    initialization_time="2024121600",
    save_to_file="output.json"  # or .csv, .gpx, .geojson, .kml, .little_r
)
```

## Resources
For more details on the WindBorne Data and Forecasts API, refer to the WindBorne's documentation:

- [Data API](https://windbornesystems.com/docs/api/data)
- [Forecasts API](https://windbornesystems.com/docs/api/forecasts)


If you encounter issues or have questions, please ask your WindBorne Systems contact.
