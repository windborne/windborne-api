# Release notes

## 2.1.0

- Custom Calculation validation, gridded Zarr downloads or temporary download
  URLs, point values, and threshold GeoJSON, through Python helpers and the
  `custom_calculations` CLI commands. Complete responses retain partial errors
  and metadata. These helpers use the existing authentication configuration.
  Expressions, including ensemble-member and forecast-hour aggregations, are
  passed unchanged to the API for evaluation.

## 2.0.1

- Observation and super-observation downloads and polling raise authentication,
  permission, and other request errors instead of retrying missing pages forever.
  Temporary gateway, connection, and timeout failures retain the five-attempt
  limit; the pagination loop no longer restarts retries after a failed request.
- Sounding-list requests raise on failed or malformed pages instead of returning
  an empty list that could make an incomplete download look finished. Successful
  empty pages still return an empty list.
- Finite observation and super-observation exports sort and save once after all
  pages succeed, avoiding repeated rewrites of the accumulated data. Output files
  are now written at completion, with the same formats, columns, timestamp order,
  and processed counts. Memory usage is unchanged. Continuous polling and custom
  save callbacks retain intermediate batches, without a duplicate final save.

## 2.0.0

### Added

- Python helpers and CLI commands for published Events, event detail and indexes,
  event initialization times, and event context for locations.
- Webhook and subscription management, including test deliveries. Writes are not
  automatically retried. If a successful write's output cannot be saved or
  printed, `WebhookOutputError.response` retains the result, including any
  one-time signing secret; the CLI writes that recovery response to stderr.
  Response files are written privately with mode `0600` on POSIX systems and
  replace an existing file only after the complete response has been written.
- Hourly climatology, daily and grouped climatology summaries, and Weather Context
  with optional observations and climatology.
- Point forecast conditions with complete JSON output.
- Current tropical cyclone tracker support: detail, index, initialization times,
  calculation times, native GeoJSON, and A-deck exports. Unmatched cyclone track
  exports use member paths when no mean path exists.
  List exports retain available tracks when other cyclones have an explicitly
  empty mean path, with a warning naming those cyclones. The returned JSON is
  unchanged. If storms exist but none have exportable tracks, the export fails
  without overwriting the destination.
  An empty cyclone-index CSV page returns normally without creating or
  overwriting a file, preserving the full pagination response for the caller.
- Documented gridded forecast options for format, regional domain, deterministic
  output, ensemble mean selection, and download-URL metadata. Archive pagination,
  sounding length filters, ASOS high-frequency observations, and documented
  `print_response` aliases are also available.

### Upgrading from 1.7.0

This is a major release because the default tropical cyclone model and return
shape change. Existing function names and positional argument order are retained,
but review the following behavior changes before upgrading:

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
- `get_tropical_cyclones()` and `windborne tropical_cyclones` now default to
  `wm-6` instead of `wm`. Calls that omit the model return the current tracker
  envelope rather than a legacy storm-ID-to-track dictionary. Explicit model
  selections retain their existing routes and response shapes; `gfs` and
  `ecmwf-det` continue to support legacy cyclone lists and track exports.
- The CLI accepts options between positional arguments, including an output
  filename after an option, consistently on Python 3.11 and 3.14.
  Negative leading coordinates still require `--`; Boolean options before
  positional arguments need an explicit `true` or `false`. The README includes
  examples of both forms.
- Continuous observation and super-observation polling advances the cursor
  after reaching the latest page, avoiding repeated processing of that page.
- Observation CSV exports retain `updated_at` when `include_updated_at=True`;
  exports without that option retain their existing columns.
- Constellation output prints restricted locations instead of failing while
  formatting their coordinates.
- `get_interpolated_sounding` accepts the documented `(latitude, longitude)`
  tuple as well as a coordinate string.
- The Variables CLI and `get_variables(print_response=True)` include derived
  variables and distribution selections. The returned catalog is unchanged.
- Conditions CLI help now includes `metamesh`; existing model selection already
  supports it, and its documented invocation is covered by regression tests.
- Credential errors link to the current authentication guide and interpolate
  the URL correctly for malformed API keys.
- Analysis-variable discovery translates the ECMWF analysis-source names to
  the model catalog's names, fixing the default SDK and CLI request.
- Station forecasts for `wm`, `mm`, and `metamesh` use the current MetaMesh
  station-query endpoint, while preserving the helper's single-station return
  format, JSON/CSV exports, and complete forecast fields. Other explicit models
  retain their legacy routes. The default `wm` now selects MetaMesh station data,
  consistent with the documented point-forecast endpoint.

For tropical cyclones, `format` selects the response representation and
`output_file` selects the saved file format. A filename ending in `.geojson` with
the default `format="json"` exports tracks locally and preserves the JSON return
value. Existing model routes retain their ID-to-track dictionary; `wm-6` retains
the current tracker response. Explicit `format="geojson"` returns and saves the
native API GeoJSON, including the additional features and metadata available
with the requested detail options. This applies to both `get_tropical_cyclones`
and `get_tropical_cyclone`.
