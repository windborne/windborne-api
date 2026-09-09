# WindBorne API

A Python SDK for accessing WindBorne observations, forecasts, insights, and webhooks. The package also includes a CLI for common workflows.

Use it either as a Python package with `import windborne` or as a command-line tool with `windborne`.

## Where to find the right information

The [WindBorne API documentation](https://api.windbornesystems.com/) is the source of truth for HTTP endpoints, supported models, request parameters, and response schemas.

The Python SDK maps documented API operations into Python functions and adds conveniences such as time parsing, pagination, formatted output, and file downloads. The CLI intentionally focuses on common workflows and does not expose every SDK function; use `windborne --help` and `windborne <command> --help` for the exact commands and options installed with your package version.

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

This calls the documented `/forecasts/v1/wm-6/point_forecast/interpolated` endpoint. Use its API documentation to choose variables, time bounds, levels, and distribution options.

### CLI

```bash
windborne points_interpolated "37.7749,-122.4194" --model wm-6 --max-hour 24
```

The Python SDK has broader coverage than the CLI, including webhook management and tropical-cyclone tracker methods. Use the API documentation for service capabilities and the installed CLI help for command availability.

## Support

If you encounter issues or have questions, please ask your WindBorne Systems contact or email data@windbornesystems.com.

## Development

For development of this package, see [README_dev.md](https://github.com/windborne/windborne-api/blob/main/README_dev.md).
