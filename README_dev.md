# Developing this package

To install the local version, run:
```bash
pip install -e .
```

You can then `import windborne` and have it refer to the latest version, or use the `windborne` cli for manual testing.

## Project structure

### windborne Package

The `windborne` package is a Python library and CLI tool for accessing WindBorne's weather balloon data and forecast APIs.

#### Core Modules

- **`__init__.py`** - Public API exports from observations_api and forecasts_api
- **`api_request.py`** - Authentication (JWT), request handling, and retry logic
- **`cli.py`** - Command-line interface implementation using argparse
- **`observations_api.py`** - Balloon observation data access (observations, missions, flight paths)
- **`forecasts_api.py`** - Weather forecast data access (point/gridded forecasts, tropical cyclones)
- **`utils.py`** - Date parsing, file saving, and output formatting utilities
- **`observation_formatting.py`** - Data format conversions (netCDF, little_r)
- **`track_formatting.py`** - Trajectory format conversions (CSV, GeoJSON, GPX, KML)

#### Key Features

- Authenticates via either `WB_CLIENT_ID` + `WB_API_KEY` or a single combined `WB_API_KEY`
- Supports multiple output formats for scientific data
- Provides both Python API and CLI access
- Handles large datasets with bucketing and pagination
- Includes retry logic and comprehensive error messages

## Pushing a new version
1. Make sure you've been added to the pypi organization
2. Increment the version in pyproject.toml
3. Run `bash deploy.sh` which will push the pip package

## Unit testing

Install the package and pytest in a virtual environment, then run:

```bash
python -m pip install -e . pytest
python -m pytest tests -q
```

These tests cover the documented SDK and CLI arguments, request parameters,
response handling, and file exports. API responses are mocked; unexpected HTTP
requests fail the tests, so credentials are not required.

The docs parity tests use the Engine API docs at commit
`b029b91ed9c4c7b7de789f3294d3010fc81caa61`. Existing positional arguments and
`print_result` / `print_results` remain supported alongside the documented
`print_response` keyword. Multi-location forecast CSVs include every location
and a `location_index` column referring to its original request position;
single-location exports retain their existing columns.

## Integration testing
These are end-to-end tests, designed primarily to test that the backend gives expected responses when accessed through the cli.
This is a good way to make sure that new cli methods are interacting with the backends in the way that you expect.
They were implemented in ruby thanks to its eloquent testing framework.

To run for the first time:
1. Install ruby dependencies: `gem install rspec`. It expects ruby 3 or greater.
2. Add a file `credentials.json` to the spec folder. This is a git-ignored JSON file containing API keys; ask on zulip for a copy.

Then, run:
```bash
rspec spec
```
