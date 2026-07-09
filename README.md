# WindBorne API

A Python library and CLI for accessing WindBorne weather balloon observations and AI-powered forecasts.

## Installation

```bash
pip install windborne
```

## Authentication

Sign up at [windbornesystems.com](https://windbornesystems.com) to get API credentials, then set them as environment variables:

```bash
export WB_CLIENT_ID="your-client-id"
export WB_API_KEY="your-api-key"
```

## Quick Start

### Python

```python
import windborne

# Get an interpolated point forecast for San Francisco
forecast = windborne.get_point_forecasts_interpolated(
    coordinates="37.7749,-122.4194",
    model="wm-6",
    max_forecast_hour=24
)
print(forecast)

# Filter to a single variable with ensemble distribution
forecast = windborne.get_point_forecasts_interpolated(
    coordinates="37.7749,-122.4194",
    model="wm-6",
    variable="temperature_2m",
    include_distribution=True,
    max_forecast_hour=24
)
print(forecast)

# Get recent balloon observations
observations = windborne.get_observations()
```

### CLI

```bash
# Interpolated point forecast
windborne points_interpolated 37.7749,-122.4194 --model wm-6 --max-forecast-hour 24

# With variable filter and distribution
windborne points_interpolated 37.7749,-122.4194 --model wm-6 -v temperature_2m --include-distribution

# Upper-air forecast at 500 hPa
windborne points_interpolated 37.7749,-122.4194 --model wm-6 -v temperature -l 500

# List flying missions
windborne flying

# Full CLI help
windborne --help
```

## Features

| Category | Capabilities |
|---|---|
| **Forecasts** | Point forecasts, interpolated point forecasts, gridded forecasts, station forecasts, tropical cyclones, degree days |
| **Observations** | Balloon observations, super observations, soundings, ASOS stations, constellation status |
| **WM-6 Params** | `variable` filter, `include_distribution` (ensemble stats), `level` (pressure level), `ens_member` (individual member) |
| **Output Formats** | JSON, CSV, netCDF, little_r, GeoJSON, GPX, KML |
| **Interfaces** | Python library (`import windborne`) and CLI (`windborne --help`) |

## Documentation

See [api.windbornesystems.com](https://api.windbornesystems.com/) for full API documentation, endpoint reference, and response schemas.

## Support

If you encounter issues or have questions, please ask your WindBorne Systems contact or email data@windbornesystems.com.

## Development

For development of this package, see [README_dev.md](https://github.com/windborne/windborne-api/blob/main/README_dev.md).
