# Developing this package

To install the local version, run:
```bash
pip install -e .
```

You can then `import windborne` and have it refer to the latest version, or use the `windborne` cli for manual testing.

## Project structure

### windborne Package

The `windborne` package is a Python library and CLI tool for accessing WindBorne observations, forecasts, insights, and webhooks.

#### Core Modules

- **`__init__.py`** - Package entry point defining the functions available directly from `import windborne`
- **`api_request.py`** - Bearer authentication, legacy JWT authentication, request handling, and retry logic
- **`cli.py`** - Command-line interface implementation using argparse
- **`observations_api.py`** - Observations, missions, flight paths, soundings, and recent ASOS data
- **`forecasts_api.py`** - Forecast availability, point and gridded forecasts, tropical cyclones, analyses, and insights
- **`webhooks_api.py`** - Webhook and subscription management
- **`utils.py`** - Date parsing, file saving, and output formatting utilities
- **`observation_formatting.py`** - Data format conversions (netCDF, little_r)
- **`track_formatting.py`** - Trajectory format conversions (CSV, GeoJSON, GPX, KML)

#### Key Features

- Authenticates with a Bearer `WB_API_KEY`, while retaining support for legacy `WB_CLIENT_ID` + `WB_API_KEY` credentials
- Supports multiple output formats for scientific data
- Provides both Python API and CLI access
- Handles large datasets with bucketing and pagination
- Includes retry logic and comprehensive error messages

## Pushing a new version
1. Make sure you've been added to the pypi organization
2. Increment the version in pyproject.toml
3. Run `bash deploy.sh` which will push the pip package

## Unit testing

Tests are in the `tests/` folder and use Python's standard-library test runner:

```bash
python -m unittest discover -s tests -v
```

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
