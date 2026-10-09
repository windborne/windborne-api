# WindBorne API
A Python library for WindBorne observations, forecasts, weather events, and webhook management.
This may be imported and used as a python library, or be called directly as a cli.

For CLI usage, run `windborne --help`.

See [https://api.windbornesystems.com/](https://api.windbornesystems.com/) for detailed documentation of all functions and API endpoints.

## Events and weather context

```python
from windborne import get_events, get_event_context, get_climatology, get_weather_context

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

weather = get_weather_context(
    stations=["KDFW"],
    include_observations=True,
    include_climatology=True,
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

Gridded helpers accept `include_deterministic`, `skip_mean`, and `as_url`.
With `as_url=True`, they return the API's download-URL metadata instead of downloading
the archive. `output_file` can save this metadata to a `.json` file, including any
subset byte-range instructions returned by the API.

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
windborne weather_context --stations KDFW --include-observations --max-forecast-hour 24
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
