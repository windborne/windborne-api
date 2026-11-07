---
name: sdk-sync
description: "Use whenever you change the windborne Python SDK or CLI, or validate a release: a helper, its arguments or defaults, a CLI command or flag, how a response is handled, or the package version. Keeps the SDK in sync with WindBorne's API docs and backends, and covers versioning and release validation."
---

# Keep the SDK in sync, and version it

The `windborne` package wraps WindBorne's public API. Engine's docs at api.windbornesystems.com (`windborne/engine`) describe each endpoint, and DLViz (`windborne/dlviz`), WindMC (`windborne/windmc`) or sensor-data-api (`windborne/sensor-data-api`) serves it. Engine's `api_infra/nginx.conf` maps each public path to its backend.

## Before you change anything

1. Read the endpoint in Engine and in its backend, both on their latest `origin` default branch, not a local checkout. In Engine, read the contract in `api_infra/schemas/` and the page under `frontends/api/src/pages/`.
2. Validate that the SDK matches the docs and the backend. If they disagree, tell the user instead of picking one.
3. Confirm compatibility with the user, and tell them backward compatibility is standard, though some changes call for a break. By default, keep existing calls working: add new keyword arguments after the existing ones.

## Release conventions

The release PR changes the version in `pyproject.toml` and adds release notes under the same number in `CHANGELOG.md`. See "Publishing a new version" in `README_dev.md`.

- **Patch** (2.1.1 → 2.1.2): bug fixes, and small changes or updates to an existing endpoint, such as a new optional parameter.
- **Minor** (2.1.2 → 2.2.0): a new endpoint or set of endpoints.
- **Major** (2.2.0 → 3.0.0): a large overhaul, which should be very rare.

Always ask the user before setting the version. Keep release notes concise and precise, and follow the existing style in `CHANGELOG.md`.

This is a public PyPI package: leave Claude attribution out of commits and PR descriptions.

## Validate the release

Before calling a release ready to publish, follow the build and installed-wheel procedure in `README_dev.md`:

1. Build the wheel and source distribution from the final release commit. Check both with `twine check --strict`, rebuild a wheel from the source distribution, and confirm the packaged code matches. Install the wheel in clean Python 3.11 and 3.14 environments, run `pip check` and the entire test suite, and exercise the installed `windborne` command. Run outside the checkout so imports use the installed package.
2. Test the installed Python helpers and CLI against production with a user-approved credential. Cover the changed behavior, existing calls and defaults, and bounded checks across the SDK's endpoint families. Check returned data and saved files, not just HTTP status. Test pagination, retry limits, access failures, and webhook writes with local fixtures; production writes or deliveries need separate approval.
3. Report the commit, artifact hashes, Python versions, test results, and anything not verified live. Access denials or unavailable data are coverage gaps, not passing tests. Fix or explicitly flag failures before recommending publication. Publish only the tested artifacts, with approval; if the release code changes, rebuild and repeat the checks.

## Before you finish

Tell the user which version you chose and why, and whether Engine's docs need the same change. Engine's CI checks the Python and CLI examples on its docs pages against the published package, so publish the release before the Engine docs PR merges.

On every PR in this windborne-api repo, request a review from Rohin (`@RohinJ444`), who can publish to PyPI. Kai (`@KMarshland`) and Vivek (`@VivekChaurasia03`) can also review and publish.
