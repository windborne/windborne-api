# WindBorne API
A Python library for WindBorne observations, forecasts, custom calculations, weather events, and webhook management.
This may be imported and used as a python library, or be called directly as a cli.

For CLI usage, run `windborne --help`.

See [https://api.windbornesystems.com/](https://api.windbornesystems.com/) for detailed documentation of all functions and API endpoints.

See the [release notes](https://github.com/windborne/windborne-api/blob/main/CHANGELOG.md)
for new features and behavior changes to review before upgrading.

## Tropical cyclone output

`format` selects the API response and Python return value. `output_file` selects
the saved file format. With the default `format="json"`, a `.geojson` filename
exports tracks locally and keeps the JSON return value:

```python
from windborne import get_tropical_cyclones

# Existing model routes return a dictionary of storm IDs and tracks.
storms = get_tropical_cyclones(model="gfs", output_file="storms.geojson")

# Request the API's native GeoJSON, including its detailed features and metadata.
features = get_tropical_cyclones(
    model="wm-6", include_details=True,
    format="geojson", output_file="storms-native.geojson",
)
```

The same distinction applies to `get_tropical_cyclone` for an individual storm.
Default JSON returns preserve the API's response: an ID-to-track dictionary for
legacy model routes, or the current tracker response for `wm-6`. Local GeoJSON
exports contain tracks; use explicit `format="geojson"` for the native forecast
points, cones, landfalls, and metadata available with the requested detail options.
Track exports use the mean path where available and fall back to member paths
for unmatched cyclones.

## Events and weather context

```python
from windborne import (
    get_events, get_event_context, get_climatology, get_climatology_summary,
    get_weather_context,
)

# Events from the latest published run, including forecast-hour geometries.
events = get_events("atmospheric_river", include_details=True)

# Events affecting these locations, in the same order as the request.
context = get_event_context([(35, -129), (37.77, -122.42)])

normals = get_climatology(
    [(32.90, -97.04)],
    start_time="2026-07-15T12:00:00Z",
    end_time="2026-07-15T13:00:00Z",
    normal="2016-2025",
    rolling_average_days=7,
)

daily_normals = get_climatology_summary(
    [(32.90, -97.04)],
    start_date="2026-07-15",
    end_date="2026-07-21",
    group_by="week",
    normal="2016-2025",
)

weather = get_weather_context(
    stations=["KDFW"],
    include_observations=True,
    include_climatology=True,
    include_climatology_summary=True,
    min_forecast_hour=0,
    max_forecast_hour=24,
)
```

Events also support `get_event_index`, `get_event`, and `get_event_init_times`.
Use an event ID returned by the list or index when requesting detail or initialization times.
The SDK preserves complete responses, including geometry, pagination, units, and arrays for each location.
Pagination helpers return one page and its metadata; they do not fetch every page automatically.

New helpers are quiet by default. Use `print_response=True` to print their JSON response,
or `output_file="response.json"` to save it. Event list and detail also support
`format="geojson", output_file="events.geojson"`. Climatology supports CSV exports;
Weather Context uses JSON to retain its separate forecast, observation, and climatology datasets.

`get_climatology_summary` returns typical daily highs, lows, precipitation, and wind.
Supply `date="YYYY-MM-DD"` for one day, or an inclusive `start_date`/`end_date` range
of up to 366 days. Ranges support `group_by="day"`, `"week"`, `"month"`, or `"period"`.
Dates use each location's fixed standard UTC offset, without daylight saving time.
JSON retains the full response; CSV exports the summary rows with their coordinates
and offsets. Weather Context's `include_climatology_summary=True` adds daily normals
for each location's forecast dates.

Gridded helpers accept `include_deterministic`, `skip_mean`, and `as_url`.
With `as_url=True`, they return the API's download-URL metadata instead of downloading
the archive. `output_file` can save this metadata to a `.json` file, including any
subset byte-range instructions returned by the API.

## Custom calculations

Four Python helpers support the
[Custom Calculations API](https://api.windbornesystems.com/insights/version_1/custom-calculations/about/).
Expressions run on the server. Inputs retain their native units; for example,
subtract `273.15` to convert `temperature_2m` from kelvin to Celsius.

```python
from windborne import (
    validate_calculation, calculate_points, calculate_gridded,
    calculate_threshold,
)

calculation = "[temperature_2m] - 273.15"
validation = validate_calculation(calculation)
# Check validation["valid"]; syntax validation does not check data availability.

points = calculate_points(
    calculation, "37.7749,-122.4194;34.0522,-118.2437", forecast_hours=6,
)
# Each grid's values follow coordinate order. Skipped hours are reported in
# points["forecast_hour_errors"], and unavailable point values are None.

archive = calculate_gridded(
    calculation, forecast_hours=[0, 6, 12],
    lat_range=[37, 38], lon_range=[-123, -122], output_file="temperature.zarr.zip",
)

areas = calculate_threshold(
    calculation,
    bounds={"min_lat": 37, "max_lat": 38, "min_lon": -123, "max_lon": -122},
    threshold={"kind": "absolute", "value": 25, "comparison": "at_or_above"},
    forecast_hours=6, output_file="warm-areas.geojson",
)
# areas["forecast_hour_errors"] reports skipped hours. The Zarr archive records skipped
# hours in its root attributes under "forecast_hour_errors".
```

The calculation endpoints support `wm-6` and `wm-6-3km`. The SDK defaults to
`wm-6`. Omit `initialization_time` to use the latest complete update, or pass an
ISO 8601 initialization time to select a specific run. An omitted
`forecast_hours` selects every available hour; an integer or list selects specific hours.

`calculate_gridded` returns ZIP bytes. With `as_url=True`, it returns temporary
download-URL metadata instead, and `output_file` must use `.json` if supplied.
Validation and point responses can be saved as `.json`; threshold responses as
`.json` or `.geojson`. All JSON responses retain their complete metadata and errors.

The CLI reads the API's JSON request body from a file or stdin:

```bash
windborne custom_calculations points --body - <<'JSON'
{
  "model": "wm-6",
  "calculation": "[temperature_2m] - 273.15",
  "forecast_hours": 6,
  "coordinates": "37.7749,-122.4194;34.0522,-118.2437"
}
JSON
```

The other subcommands are `validate`, `gridded`, and `threshold`. Use
`--body request.json` to read a file. Gridded ZIP output requires
`-o result.zarr.zip`; use `"as_url": true` in the body to print URL metadata instead.

## Webhook management

Use the same `WB_API_KEY` configuration as the existing SDK. Helpers manage the
webhooks owned by your credentials; subscription and forecast permissions still apply.

```python
from windborne import create_webhook, list_webhooks, update_webhook_subscription

webhook = create_webhook(
    "https://example.com/webhook",
    name="Weather events",
    subscriptions={
        "events.available": {"filters": {"model": "wm-6", "event_type": "heatwave"}}
    },
)
# Creation returns a one-time signing_secret; retain it for verifying deliveries.

page = list_webhooks(active=True, page=1, page_size=20)

# Omitted fields stay unchanged. An empty filters object clears filters, and
# response_options=None explicitly removes response enrichment.
update_webhook_subscription(
    webhook["id"], webhook["subscriptions"][0]["id"],
    filters={}, response_options=None,
)
```

The other management helpers are `get_webhook`, `update_webhook`, `delete_webhook`,
`add_webhook_subscription`, `delete_webhook_subscription`, and `ping_webhook_subscription`.
`update_webhook(id, active=False)` pauses delivery. Ping sends a real test delivery
to the registered URL. Successful deletes and pings return `None` (HTTP 204).

Write errors raise exceptions, and writes are sent once without automatic retries.
After a timeout, check the current webhook state before retrying because the server
may already have applied the request. Existing GET retry behavior is retained.
If the API succeeds but saving or printing its response fails, `WebhookOutputError`
retains the successful result in its `.response` attribute, including any one-time
signing secret. Recover that result instead of repeating the write. The CLI emits
this recovery response on stderr and exits with status 1.

## CLI commands

```bash
windborne events list atmospheric_river --include-details --format geojson -o events.geojson
windborne events index heatwave --page 0 --page-size 64
windborne events context "35,-129;37.77,-122.42"
windborne climatology "32.90,-97.04" --time 2026-07-15T12:00:00Z
windborne climatology_summary "32.90,-97.04" --start-date 2026-07-15 --end-date 2026-07-21 --group-by week -o normals.json
windborne weather_context --stations KDFW --include-observations --include-climatology-summary --max-forecast-hour 24
windborne gridded temperature_2m 2026071512 forecast-url.json --model wm-6 --as-url
windborne webhooks list --active true
windborne webhooks update 42 --body changes.json
```

Webhook create, update, and subscription updates accept their documented JSON request
body through `--body FILE` or `--body -` for stdin. For example, `changes.json` can
contain `{"active": false}`. Run `windborne events --help` or `windborne webhooks --help`
for the available operations; each operation also supports `--help`.

## Further information and help request
If you encounter issues or have questions, please ask your WindBorne Systems contact or email data@windbornesystems.com.

For development of this package, see [README_dev.md](README_dev.md).
