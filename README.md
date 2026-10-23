<p align="center">
<picture>
<source media="(prefers-color-scheme: dark)" srcset="https://api.windbornesystems.com/logo/Logo-Full-White.svg">
<img src="https://api.windbornesystems.com/logo/Logo-Full-Black.svg" alt="WindBorne Systems" width="300">
</picture>
</p>

A Python library for the WindBorne API. Import it in
Python, or run it from the command line as `windborne`.

The [API documentation](https://api.windbornesystems.com/) covers every endpoint's
parameters and responses, with Python and CLI examples.

## Installation

```bash
pip install windborne
```

## Authentication

Set your WindBorne API key as an environment variable:

```bash
export WB_API_KEY="your_api_key"
```

See [Authentication](https://api.windbornesystems.com/technical-guides/authentication/auth/)
for how to get a key.

## Quick Start

Each API key's access is scoped to specific data, such as forecasts or observations, so
some of these examples may not work with your key. See
[Getting Started](https://api.windbornesystems.com/getting-started) for details.

```python
from windborne import get_point_forecasts_interpolated, get_observations, get_events

# WeatherMesh-6 forecast for New York from the latest run
forecast = get_point_forecasts_interpolated(coordinates="40.7,-74.0", model="wm-6")

# Six hours of balloon observations, saved as a CSV
get_observations(
    start_time="2026-01-01T00:00:00Z",
    end_time="2026-01-01T06:00:00Z",
    output_file="observations.csv",
)

# Retrieve detected atmospheric rivers from the latest WeatherMesh-6 run
events = get_events("atmospheric_river")
```

The same requests from the command line:

```bash
windborne points_interpolated "40.7,-74.0" -m wm-6
windborne observations 2026-01-01T00:00:00Z 2026-01-01T06:00:00Z observations.csv
windborne events list atmospheric_river
```

## API Overview

| API Documentation | Functions |
| --- | --- |
| [Observations](https://api.windbornesystems.com/observations/version_1/overview) | `get_observations`, `get_super_observations`, `poll_observations`, `get_soundings`, `get_sounding` |
| [Atlas](https://api.windbornesystems.com/atlas/version_1/overview) | `get_flying_missions`, `get_flight_path`, `get_predicted_path`, `get_current_location`, `get_constellation_status`, `get_mission_launch_site` |
| [Point Forecasts](https://api.windbornesystems.com/forecasts/version_1/point-forecast/interpolated-point-forecast) | `get_point_forecasts_interpolated`, `get_point_forecasts`, `get_point_forecast_conditions`, `get_interpolated_sounding` |
| [Gridded Forecasts](https://api.windbornesystems.com/forecasts/version_1/gridded-forecast/gridded-forecast) | `get_gridded_forecast`, `get_full_gridded_forecast` |
| [Forecast Availability](https://api.windbornesystems.com/forecasts/version_1/forecast-availability/initialization-times) | `get_initialization_times`, `get_archived_initialization_times`, `get_run_information`, `get_variables`, `get_available_stations` |
| [Weather Context](https://api.windbornesystems.com/forecasts/version_1/context/weather-context) | `get_weather_context`, `get_climatology`, `get_climatology_summary`, `get_recent_asos_observations` |
| [Tropical Cyclones](https://api.windbornesystems.com/forecasts/version_1/tropical-cyclones/about) | `get_tropical_cyclones`, `get_tropical_cyclone`, `get_tropical_cyclone_index`, `get_tropical_cyclone_init_times` |
| [Weather Events](https://api.windbornesystems.com/insights/version_1/events/about) | `get_events`, `get_event`, `get_event_index`, `get_event_init_times`, `get_event_context` |
| [Degree Days](https://api.windbornesystems.com/insights/version_1/population-weighted/hdd) | `get_population_weighted_hdds`, `get_population_weighted_cdds` |
| [Webhooks](https://api.windbornesystems.com/technical-guides/webhooks/about-webhooks) | `create_webhook`, `list_webhooks`, `get_webhook`, `update_webhook`, `delete_webhook`, `add_webhook_subscription`, `update_webhook_subscription`, `delete_webhook_subscription`, `ping_webhook_subscription` |

To view a function's arguments, run `help(function)` in Python. To view a command's
options, run `windborne <command> --help`.

## Help

See the [release notes](https://github.com/windborne/windborne-api/blob/main/CHANGELOG.md)
for changes between versions, and [README_dev.md](https://github.com/windborne/windborne-api/blob/main/README_dev.md)
for development of this package.

For further assistance, ask your WindBorne contact or email data@windbornesystems.com.
