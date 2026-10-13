# Release notes

## 1.8.0 — Unreleased

### Added

- Python helpers and CLI commands for published Events, event detail and indexes,
  event initialization times, and event context for locations.
- Webhook and subscription management, including test deliveries. Writes are not
  automatically retried. If a successful write's output cannot be saved or
  printed, `WebhookOutputError.response` retains the result, including any
  one-time signing secret; the CLI writes that recovery response to stderr.
- Hourly climatology, daily and grouped climatology summaries, and Weather Context
  with optional observations and climatology.
- Point forecast conditions with complete JSON output.
- Current tropical cyclone tracker support: detail, index, initialization times,
  calculation times, native GeoJSON, and A-deck exports. Unmatched cyclone track
  exports use member paths when no mean path exists.
- Documented gridded forecast options for format, regional domain, deterministic
  output, ensemble mean selection, and download-URL metadata. Archive pagination,
  sounding length filters, ASOS high-frequency observations, and documented
  `print_response` aliases are also available.

### Upgrading from 1.7.0

Existing function names and positional argument order are retained. Corrected
behavior can still affect scripts that relied on the previous results:

- Multi-location forecast CSV exports now include every returned location,
  instead of only the first, with a `location_index` column identifying its
  original request position. Single-location exports retain their existing
  columns. CSV headers include fields found in later rows as well as the first.
- Timestamp normalization preserves seconds and fractions instead of truncating
  them. Initialization times are no longer restricted to 00, 06, 12, or 18 UTC;
  the API determines which runs are available for each model.
- Explicit zero-valued forecast-hour bounds and ensemble members are sent to the
  API rather than omitted.
- `get_archived_initialization_times` now returns the API response instead of
  `None`.
- Degree-day helpers normalize initialization times, accept omitted or `latest`
  initialization times, save JSON when requested, and use the documented
  forecast namespace for calculation times.
- Invalid tropical cyclone basins raise `ValueError` rather than exiting the
  process. Atlantic basin aliases are mapped for the selected model route.
- The CLI accepts options between positional arguments, including an output
  filename after an option, consistently on Python 3.11 and 3.14.

For tropical cyclones, `format` selects the response representation and
`output_file` selects the saved file format. A filename ending in `.geojson` with
the default `format="json"` exports tracks locally and preserves the JSON return
value. Existing model routes retain their ID-to-track dictionary; `wm-6` retains
the current tracker response. Explicit `format="geojson"` returns and saves the
native API GeoJSON, including the additional features and metadata available
with the requested detail options. This applies to both `get_tropical_cyclones`
and `get_tropical_cyclone`.
