# WindBorne API

A Python library and CLI for accessing WindBorne observations, forecasts, insights, and webhooks.

Use it either as a Python package with `import windborne` or as a command-line tool with `windborne`.

The [WindBorne API documentation](https://api.windbornesystems.com/) is the source of truth for available APIs, parameters, and response schemas.

## Installation

```bash
pip install windborne
```

## Authentication

Set the combined API key provided by WindBorne:

```bash
export WB_API_KEY="your-api-key"
```

See the [authentication guide](https://api.windbornesystems.com/technical-guides/authentication/auth/) for details. Legacy `WB_CLIENT_ID` plus `WB_API_KEY` credentials remain supported.

## Quick start

### Python

```python
from windborne import get_interpolated_point_forecast

forecast = get_interpolated_point_forecast(
    coordinates="37.7749,-122.4194",
    model="wm-6",
    max_forecast_hour=24,
)
```

### CLI

```bash
windborne points_interpolated "37.7749,-122.4194" --model wm-6 --max-hour 24
```

Run `windborne --help` to list the currently installed CLI commands.

## Features

| Category | Capabilities |
| --- | --- |
| Forecasts | Point and gridded forecasts, atmospheric soundings, forecast availability, and tropical cyclone tracking |
| Observations | Raw and aggregated observations, missions, flight paths, soundings, and constellation status |
| Insights | Population-weighted heating and cooling degree days |
| Webhooks | Endpoint and subscription management, including test deliveries |
| Output formats | JSON, CSV, NetCDF, Zarr, little_r, GeoJSON, GPX, and KML |

## Support

If you encounter issues or have questions, please ask your WindBorne Systems contact or email data@windbornesystems.com.

## Development

For development of this package, see [README_dev.md](https://github.com/windborne/windborne-api/blob/main/README_dev.md).
