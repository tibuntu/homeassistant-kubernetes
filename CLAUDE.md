# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Home Assistant custom integration for monitoring and controlling Kubernetes clusters. Python 3.13+, async throughout, uses the official `kubernetes` Python client.

## General Instructions

Always update this CLAUDE.md automatically whenever new changes are implemented, so it stays in sync with the current state of the codebase, architecture, and conventions.

Never add yourself as a git co-author. Do not include `Co-Authored-By` trailers in any commit message.

## Commands

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all tests (includes coverage)
pytest

# Run a single test file or specific test
pytest tests/test_sensors.py
pytest -k test_specific_name

# Run by marker
pytest -m unit
pytest -m integration
pytest -m "not slow"

# Lint and format
ruff check .
ruff format .

# Type checking
mypy custom_components/

# Security scanning
bandit -c pyproject.toml -r custom_components/

# Pre-commit (runs all checks)
pre-commit run --all-files

# Documentation
zensical serve
```

## Architecture

### Data Flow

```
KubernetesClient (API calls) → KubernetesDataCoordinator (polling/caching) → Entities (sensors/switches/binary_sensors)
```

When the experimental **Watch API** is enabled:
```
KubernetesClient.watch_stream() → KubernetesDataCoordinator._run_watch_loop() → coordinator.data updated + async_update_listeners()
```

**Entry point:** `__init__.py` sets up the integration lifecycle. On config entry setup, it creates a `KubernetesClient`, wraps it in a `KubernetesDataCoordinator`, then forwards setup to three platforms: `sensor`, `switch`, `binary_sensor`. If the `enable_watch` option is set, watch tasks are also started after the first refresh.

### Key Modules

- **`kubernetes_client.py`** — Async wrapper around the k8s Python client. Fetches deployments, statefulsets, daemonsets, cronjobs, pods, nodes. Handles SSL, auth, namespace filtering, and error deduplication (5-min cooldown). Also provides `watch_stream()` (async generator), `list_resource_with_version()`, `ResourceVersionExpired` exception, and single-item parse helpers (`_parse_pod_item`, `_parse_node_item`, `_parse_deployment_item`, `_parse_statefulset_item`, `_parse_daemonset_item`) used by the coordinator watch loop.
- **`coordinator.py`** — Extends HA's `DataUpdateCoordinator`. Polls the cluster on an interval (60 s default, 300 s when watch is active), aggregates all resources into lookup dicts, handles orphaned device cleanup. When watch is enabled, also manages background watch tasks (`async_start_watch_tasks`, `async_stop_watch_tasks`, `_run_watch_loop`, `_apply_watch_event`).
- **`sensor.py`** — Aggregate count sensors (pods, nodes, deployments, cronjobs, jobs, etc.) and per-resource sensors (individual node/pod/cronjob/job metrics).
- **`switch.py`** — Scale control for Deployments/StatefulSets (on=running, off=scaled to 0) and CronJob suspension. Includes verification timeouts and cooldowns.
- **`binary_sensor.py`** — Cluster health connectivity indicator and per-node condition binary sensors (MemoryPressure, DiskPressure, PIDPressure, NetworkUnavailable).
- **`services.py`** — Three HA services: `scale_workload`, `start_workload`, `stop_workload`. Support targeting multiple entities.
- **`device.py`** — Device registry management. Two grouping modes: `namespace` (entities grouped by namespace) or `cluster` (all under one device).
- **`config_flow.py`** — UI configuration flow. Validates cluster connectivity. Lazy-imports kubernetes to handle missing dependency gracefully. Contains `KubernetesOptionsFlow` for configuring the experimental watch API toggle. Also contains a reconfigure flow (`async_step_reconfigure` / `async_step_reconfigure_namespaces`) for modifying existing entries without deleting and re-adding the integration.
- **`const.py`** — All constants, config keys, defaults, sensor/switch type identifiers. Includes watch-related constants: `CONF_ENABLE_WATCH`, `DEFAULT_WATCH_TIMEOUT_SECONDS`, `DEFAULT_WATCH_RECONNECT_DELAY`, `DEFAULT_FALLBACK_POLL_INTERVAL`.

### Entity Hierarchy

Cluster device → (optional) Namespace devices → Entity instances. Grouping mode is configurable via `device_grouping_mode`.

### Patterns

- All entities read cached data from the coordinator, never calling the K8s API directly.
- `asyncio_mode = "auto"` in pytest — test functions are automatically treated as async.
- Tests mock HA and the K8s client via fixtures in `conftest.py` (`mock_hass`, `mock_config_entry`, `mock_client`, `mock_coordinator`).
- The kubernetes package is lazy-imported in config_flow and checked at setup to handle missing dependency.

## Code Style

- **Ruff** for linting and formatting (replaces black, isort, flake8). 88-char line length.
- Type hints encouraged but mypy is not strict (`disallow_untyped_defs = false`)
- Prefer `aiohttp` over the blocking kubernetes client for new async HTTP calls
- All integration code must use `async`/`await` — no blocking calls
- Inside coroutines always use `asyncio.get_running_loop()`, never `asyncio.get_event_loop()` (deprecated in Python 3.10+ within a running loop)
- For long-lived aiohttp streams (`total=None`) always set a `sock_read` timeout to guard against stale/half-open TCP connections
- In `async_setup_entry`, start any background tasks **after** `async_forward_entry_setups()` so entity listeners are registered before the first events can arrive

## CI

GitHub Actions runs: pytest + ruff + mypy + bandit (Python 3.14), HACS validation, hassfest (HA manifest validation), mkdocs build. Releases automated via release-please.

## Tests

Whenever changes are implemented to any integration code, always add or update the corresponding unit tests in `tests/`. Follow the existing patterns in the test files:

- Each new class gets a corresponding `Test<ClassName>` test class.
- Each new module-level helper function gets a `TestDiscover<Name>` or similar test class.
- Cover the happy path, edge cases (missing data, `None` coordinator data), and all distinct return values.
- Use the shared fixtures from `conftest.py` (`mock_hass`, `mock_config_entry`, `mock_client`, `mock_coordinator`) rather than creating new ones where possible.
- Do not attempt to run tests locally — the CI pipeline handles test execution.

## Documentation

Whenever changes are implemented, update all relevant documentation to reflect the current state of the code. This includes `README.md`, files in `docs/`, and any other `.md` files in the repository. Do not leave documentation that describes outdated behaviour.

Before finishing any task, fully review **all** `.md` files in the repository — including `README.md`, every file under `docs/`, and `CLAUDE.md` itself — to confirm that no documentation has become stale as a result of the change. Pay particular attention to installation instructions, configuration references, and RBAC/manifest paths, as these are the most likely to drift when the project structure changes.

## Version Management

Renovate handles all dependency updates. When making any change that involves version pinning or introduces a new dependency, always check `renovate.json` and ensure the version is tracked and grouped correctly:

- Versions pinned in `pyproject.toml` are managed by Renovate's pip manager.
- Versions pinned in `custom_components/kubernetes/manifest.json` are tracked via a custom regex manager.
- Pre-commit hook versions in `.pre-commit-config.yaml` are managed by Renovate's pre-commit manager.
- When the same package appears in multiple files, add a `groupName` rule in `renovate.json` so updates are batched into a single PR.
