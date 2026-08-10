# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Home Assistant custom integration for monitoring and controlling Kubernetes clusters. Python 3.13+, async throughout, uses the official `kubernetes` Python client.

## General Instructions

Always update this CLAUDE.md automatically whenever new changes are implemented, so it stays in sync with the current state of the codebase, architecture, and conventions.

Never add yourself as a git co-author. Do not include `Co-Authored-By` trailers in any commit message.

## Commands

```bash
# Install Python dev dependencies
pip install -e ".[dev]"

# Install frontend dependencies and build
cd frontend && npm install && npm run build

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

# RBAC: edit chart/templates/, then regenerate manifests/
scripts/render-manifests.sh
helm lint chart --set mode=full && helm lint chart --set mode=minimal
```

## Architecture

### Data Flow

```
KubernetesClient (API calls) → KubernetesDataCoordinator (polling/caching) → Entities (sensors/switches/binary_sensors)
```

When the **Watch API** is enabled (the default):
```
KubernetesClient.watch_stream() → KubernetesDataCoordinator._run_watch_loop() → coordinator.data updated + async_update_listeners()
```

When the opt-in **Cluster Events** platform is enabled:
```
KubernetesClient.watch_stream() → KubernetesDataCoordinator._run_event_watch_loop() → _dispatch_event() → async_dispatcher_send(event_signal) → KubernetesClusterEventEntity._handle_event()
```

**Sidebar panel:**
```
Browser (kubernetes-panel) → hass.callWS() → websocket_api.py → KubernetesDataCoordinator
Coordinator update → kubernetes/subscribe_updates push → panel views refetch (debounced)
```

**Entry point:** `__init__.py` sets up the integration lifecycle. `async_setup` registers the WebSocket commands and the HA services (Bronze `action-setup`) — services are registered once at HA start, independent of any config entry, and are never unregistered. On config entry setup, it creates a `KubernetesClient`, wraps it in a `KubernetesDataCoordinator`, stores both on `entry.runtime_data` as a `KubernetesEntryData` (Bronze `runtime-data`), then forwards setup to four platforms: `sensor`, `switch`, `binary_sensor`, and `event` (`Platform.EVENT`). On the first config entry, it also registers the sidebar panel. After the first refresh it runs `_async_migrate_unique_ids()`, a one-time entity-registry migration that inserts the namespace into pre-namespaced unique_ids (deployment/statefulset switches, status/metric sensors, daemonset sensors) when the workload name resolves to exactly one namespace. Unless the `enable_watch` option is disabled (it defaults to on), watch tasks are also started after the first refresh. If `enable_events` is set, `coordinator.async_start_event_watch_tasks()` is also called after platform setup so the event entity is registered before the first dispatched event arrives. `async_unload_entry` only stops the watch tasks, clears the repair issues and tidies up the panel — HA discards `entry.runtime_data` itself. `hass.data[DOMAIN]` holds nothing but the integration-wide `panel_registered` flag; `_loaded_entries_except()` / `_any_entry_wants_panel()` enumerate entries via `coordinator.get_loaded_entries(hass)`.

### Key Modules

- **`kubernetes_client.py`** — Async wrapper around the k8s Python client. Fetches deployments, statefulsets, daemonsets, cronjobs, jobs, pods, nodes, ingresses. Uses generic `_fetch_resource_list(api_path, resource_name, parse_fn)` and `_fetch_resource_count(api_path, resource_name)` methods to eliminate per-resource boilerplate. `get_ingresses()`/`get_ingresses_count()` fetch from `apis/networking.k8s.io/v1`. The module-level `normalize_host(host)` helper brackets bare IPv6 literals (e.g. `2001:db8::1` → `[2001:db8::1]`); it is applied to `self.host` in `__init__` (so every `https://{host}:{port}/...` URL is valid) and is reused by `config_flow._test_connection` — idempotent, so already-bracketed hosts, hostnames, and IPv4 addresses pass through unchanged. Handles SSL via a single shared, lazily-built `ssl.SSLContext` (`_get_ssl_param()` — built once from `ca_cert` in the executor and cached, so every aiohttp call honors a cluster-issued CA instead of only the system trust store; returns `False` when `verify_ssl` is off), auth, namespace filtering (per-namespace loop vs cluster-wide), and error deduplication (5-min cooldown). Also provides `watch_stream()` (async generator), `list_resource_with_version()`, `ResourceVersionExpired` exception, single-item parse helpers (`_parse_pod_item`, `_parse_node_item`, `_parse_replica_workload_item` aliased as `_parse_deployment_item`/`_parse_statefulset_item`, `_parse_daemonset_item`, `_parse_ingress_item`) used by the coordinator watch loop, `_enrich_workloads_with_metrics(workloads, workload_type_label)` for deployment/statefulset metrics enrichment, `get_node_metrics()` for real-time CPU/memory usage from the Metrics API (CPU/memory quantity parsing lives in the pure `metrics_parser.py` module via `parse_cpu_quantity`/`parse_memory_quantity`; the client's `_parse_cpu`/`_parse_memory` are thin delegators), `delete_pod(pod_name, namespace)` for pod deletion (aiohttp primary + official client fallback), `delete_job(job_name, namespace)` for Job deletion with Background propagation (pods also cascade-deleted; aiohttp primary + official client fallback), and `rollout_restart_deployment/statefulset/daemonset(name, namespace)` for rolling restarts (strategic-merge-patch on `kubectl.kubernetes.io/restartedAt` annotation, aiohttp primary + `patch_namespaced_*` fallback), plus `cordon_node(node_name)`/`uncordon_node(node_name)` (strategic-merge-patch on `spec.unschedulable`, aiohttp primary + `core_v1.patch_node` fallback). `_parse_pods_data` extracts container waiting/terminated/lastState reasons from each pod's container statuses and derives a `problem`/`problem_reason` flag (True for non-benign waiting, non-zero exit code, phase Failed, or Unschedulable Pending; benign `ContainerCreating`/`PodInitializing` and a recovered OOMKill are excluded); `_parse_pod_item` (used by the coordinator watch loop) inherits the same logic. When `use_in_cluster=True` is set on the config entry, `api_token` is a property that re-reads `IN_CLUSTER_TOKEN_PATH` (with a 60 s TTL cache) so projected SA token rotations are picked up without a config-flow restart; `_refresh_api_key_hook` ensures the official client's `Configuration.api_key` is updated before each call, and 401 responses invalidate the cache via `invalidate_token_cache()`. The connection probe (`_test_connection_aiohttp`, run on every poll cycle by `get_pods`/`get_pods_count`) is the single source of the reauth signal: `_probe_api(session)` returns the raw status of a `GET /api/v1/`, and the public `auth_failed` flag is set **only** by a confirmed 401 there and cleared by any other status. For `use_in_cluster` entries a 401 first triggers `invalidate_token_cache()` plus one retry, so routine projected-token rotation never flags an auth failure. A transport error leaves the flag untouched (it says nothing about the token).
- **`coordinator.py`** — Home of the per-entry runtime-data types and the coordinator. `KubernetesEntryData` is the dataclass stored on `entry.runtime_data` (`config`, `client`, `coordinator`, plus the per-platform `*_add_entities` callbacks and `*_pending_unique_ids` sets used by dynamic entity discovery); `type KubernetesConfigEntry = ConfigEntry[KubernetesEntryData]` is the typed entry alias used across the integration; `get_loaded_entries(hass)` wraps `hass.config_entries.async_loaded_entries(DOMAIN)` and is the single way modules enumerate entries. `KubernetesDataCoordinator` extends HA's `DataUpdateCoordinator`. Polls the cluster on an interval (300 s while watch — the default — is active, 60 s otherwise; while any watch loop is in sustained failure, `_sync_watch_repair_issue` temporarily restores the fast interval so data stays fresh), aggregates all resources into lookup dicts (namespaced resources — deployments, statefulsets, daemonsets, cronjobs, jobs, pods, ingresses — are keyed by `"{namespace}_{name}"` so same-named workloads in different namespaces don't collide; nodes are keyed by name; getters take `(namespace, name)`), handles orphaned device cleanup. Merges node metrics (`cpu_usage_millicores`, `memory_usage_mib`) from the Metrics API into node data when available. Uses `_data_lock` (`asyncio.Lock`) to prevent watch events from modifying `self.data` during a polling cycle. After the fetch calls it checks `self.client.auth_failed is True` (explicit identity comparison — coordinator tests pass a `MagicMock` client whose attributes are always truthy) and raises `ConfigEntryAuthFailed` instead of `UpdateFailed`, which makes HA start the reauth flow; the check sits before the orphan cleanup so a 401's empty results never prune entities or namespace devices, and a dedicated `except ConfigEntryAuthFailed: raise` keeps the generic handler from re-wrapping it. Watch loops are deliberately *not* wired to reauth — they have their own repair issue. When watch is enabled, also manages background watch tasks (`async_start_watch_tasks`, `async_stop_watch_tasks`, `_run_watch_loop`, `_apply_watch_event`). The watch reconnect uses jittered exponential backoff (`WATCH_MAX_RECONNECT_DELAY`/`WATCH_RECONNECT_JITTER`) and raises a `watch_connection_failing_<entry_id>` repair issue after `WATCH_MAX_FAILURE_STREAK` consecutive failures (`_sync_watch_repair_issue`), cleared on reconnect and on unload. Each loop tracks its failure state under a per-`(resource_type, url)` key (`f"{resource_type}:{url}"`), so in per-namespace mode one namespace's loop recovering does not clear the issue while another namespace's loop for the same resource type is still failing — the issue stays raised while *any* loop is failing. Tracks the per-entry `metrics_server_unavailable` repair issue via `_sync_metrics_repair_issue()` (raised when nodes are present but metrics are empty, dismissed when metrics return) and `async_clear_repair_issues()` (called from `async_unload_entry`). When `enable_events` is set, `async_start_event_watch_tasks()` starts background tasks that tail the Kubernetes Events API (`/api/v1/events` or per-namespace equivalents) using the same watch infrastructure; `_run_event_watch_loop(url)` drives each stream and calls `_dispatch_event(obj)` which filters by `event_types` (`warning`-only by default, or `all`) and dispatches matching events via `async_dispatcher_send` on the `event_signal(entry_id)` channel — no state is stored in `coordinator.data`. **Data-collection opt-out**: `disabled_resources(entry)` (module-level helper next to `get_loaded_entries`) reads the `disabled_resources` option; the coordinator caches it as `self._disabled` at construction (options change → entry reload → rebuilt). Fully-off categories (`pods`, `daemonsets`, `jobs`, `ingresses` — `FULLY_DISABLEABLE_RESOURCES` in const) skip their fetch entirely (bucket stays `{}`) and are filtered out of `_build_watch_configs`; sensors-off categories (`nodes`, `deployments`, `statefulsets`, `cronjobs`) keep their fetch because switches read the data. `metrics` disabled → `get_node_metrics()` never called, `get_deployments/get_statefulsets(include_metrics=False)`, and `_sync_metrics_repair_issue` is bypassed. `counts` disabled → no count API calls (`pods_count`/`nodes_count` fall back to `len()`); when a fully-off type is disabled while counts stay on, the coordinator stores `{type}_count` keys from the cheap count endpoints and the count sensors prefer those keys. **Reauth-probe invariant**: `get_pods`/`get_pods_count` carry the client's connection probe, so when both `pods` and `counts` are disabled the coordinator calls `is_cluster_healthy()` explicitly each cycle — never remove that call, or a persistent 401 stops triggering reauthentication. `_build_expected_unique_ids` also respects `self._disabled` (switch unique_ids always stay expected; sensor unique_ids of disabled categories drop out), which is how the existing `_cleanup_orphaned_entities` pass removes a disabled category's entities automatically.
- **`sensor.py`** — Aggregate count sensors (pods, nodes, deployments, cronjobs, jobs, ingresses, etc.) and per-resource sensors (individual node/pod/cronjob/job metrics). `KubernetesPodSensor` exposes 8 container-state diagnostic attributes: `container_waiting_reason` (e.g. CrashLoopBackOff, ImagePullBackOff), `container_terminated_reason` + `container_terminated_exit_code` (current termination), `last_terminated_reason` + `last_terminated_exit_code` (previous run — catches a recovered OOMKill), `pending_reason` (e.g. Unschedulable), and a derived `problem` (bool) + `problem_reason` flag that is `true` only when the pod is currently broken (benign transient states like `ContainerCreating` and a recovered OOMKill do not set it). Setup and the `_discover_new_*` helpers consult `disabled_resources(config_entry)`: count sensors require `counts` enabled, node sensors `nodes`, per-type status sensors their type, and workload CPU/memory sensors both their type and `metrics`. The daemonsets/jobs/ingresses count sensors prefer the coordinator's `{type}_count` key over `len(bucket)` (present only when the type is fully off), so watch-driven bucket updates stay live when the type is enabled.
- **`switch.py`** — Scale control for Deployments/StatefulSets (on=running, off=scaled to 0), CronJob suspension, and node cordon/uncordon (`KubernetesNodeSchedulableSwitch`, on=schedulable, off=cordoned — patches `spec.unschedulable` via the client's `cordon_node`/`uncordon_node`). `KubernetesReplicaWorkloadSwitch` is the parameterized base class for replica-based workloads; `KubernetesDeploymentSwitch` and `KubernetesStatefulSetSwitch` are thin subclasses that pass workload-specific config (resource key, client methods, log label). `KubernetesCronJobSwitch` remains separate (suspension vs scaling). Includes verification timeouts and cooldowns.
- **`binary_sensor.py`** — Cluster health connectivity indicator and per-node condition binary sensors (MemoryPressure, DiskPressure, PIDPressure, NetworkUnavailable). Supports dynamic discovery of new nodes via coordinator listener (same pattern as `sensor.py`), storing the `async_add_entities` callback and pending unique_ids on `config_entry.runtime_data`. Node condition sensors are skipped (setup and discovery) when `nodes` is in `disabled_resources`; the cluster health sensor always stays.
- **`event.py`** — `KubernetesClusterEventEntity` (one per cluster, attached to the cluster device). Only created when `enable_events` is on. Subscribes to the `event_signal(entry_id)` dispatcher channel via `async_dispatcher_connect` and calls `_trigger_event(event_type, payload)` on each dispatch. The `event_type` is the k8s `reason` if it appears in `EVENT_CURATED_REASONS`, else `EVENT_TYPE_OTHER`. The entity does not poll or store state — it is purely event-driven.
- **`services.py`** — Seven HA services: `scale_workload`, `start_workload`, `stop_workload`, `restart_workload`, `delete_job`, `cordon_node`, and `uncordon_node`. `async_setup_services(hass)` is awaited from `__init__.async_setup` (Bronze `action-setup`), so the services exist for the lifetime of HA — there is no unload counterpart. The node services accept raw node names (`node_name`/`node_names`, no namespace — nodes are cluster-scoped) and require the `patch` verb on `nodes`. The first four reuse the coordinator's `KubernetesClient` instance (`_get_entry_data(hass, call.data).coordinator.client`, resolved from `entry.runtime_data`) and support targeting multiple entities via `_collect_entity_ids()` helper (handles string/list/dict/target selector formats). Also accept raw workload names (not just entity IDs) via `_resolve_raw_workload_name` to resolve workload types. The `delete_job` service deletes one or more Jobs by name (not entity IDs since Jobs are sensors, not switches); it resolves the namespace from monitored data and falls back to the configured default namespace.

  **Error handling (Silver `action-exceptions`)** — handlers raise instead of logging: `ServiceValidationError` for caller mistakes (`_get_entry_data` when nothing is configured or `entry_id` matches no loaded entry; `_no_workloads_error` when nothing resolves; `_validate_workload_types` when a target's type does not support the operation — checked up front, so an unsupported type rejects the *whole* call before any target is touched; empty job/node name lists). `HomeAssistantError` for operations that actually failed. Multi-target calls never abort on the first failure: `_attempt(action, label, failures)` awaits each client call, swallows a `False`/`{"success": False}` result *or* an exception into the `failures` list, and `_raise_failures(failures, operation)` raises a single error naming every failed target at the end. Node cordon/uncordon still refreshes the coordinator before raising when at least one node changed. Voluptuous schema validation (`_validate_*_schema` raising `vol.Invalid`) is unchanged.
- **`device.py`** — Device registry management. Two grouping modes: `namespace` (entities grouped by namespace) or `cluster` (all under one device).
- **`config_flow.py`** — UI configuration flow. Validates cluster connectivity. Lazy-imports kubernetes via `_ensure_kubernetes_imported()` with thread-safe double-checked locking (`threading.Lock`) to handle missing dependency gracefully. Contains `KubernetesOptionsFlow` for configuring the sidebar panel toggle (`enable_panel`, default True), the watch API toggle (`enable_watch`, default True), and the `disabled_resources` data-collection opt-out (multi-select `SelectSelector` over `DISABLABLE_RESOURCES`, translated via the `selector.disabled_resources` block in `translations/en.json`). Also contains a reconfigure flow (`async_step_reconfigure` / `async_step_reconfigure_namespaces`) for modifying existing entries without deleting and re-adding the integration, and a reauthentication flow (`async_step_reauth` → `async_step_reauth_confirm`, HA quality scale `reauthentication-flow`) triggered when the coordinator raises `ConfigEntryAuthFailed`. The confirm step asks only for a new `api_token`, validates it with `_test_connection` against a throwaway copy of the entry's stored settings (`_test_connection` mutates the dict it is given — it normalizes the host), and on success calls `async_update_reload_and_abort(self._get_reauth_entry(), data_updates=…)`; on failure it re-shows the form with the `invalid_auth` error. The `data_updates` dict carries the new `api_token` and, **for `use_in_cluster` entries only, `CONF_USE_IN_CLUSTER: False`** — the client's 401 retry means such an entry reaches reauth only when the projected ServiceAccount token is persistently rejected, so leaving in-cluster mode on would keep the pasted token inert (`api_token` prefers the file) and re-prompt forever. The step description says so, and the user can re-enable the checkbox via Reconfigure. When HA runs inside the cluster, `async_detect_in_cluster_config()` reads the pod's ServiceAccount (`KUBERNETES_SERVICE_HOST` env var + `/var/run/secrets/kubernetes.io/serviceaccount/{token,ca.crt}`) off the event loop and pre-fills host/port/api_token/ca_cert on the user step via voluptuous `description={"suggested_value": …}`. The user step also exposes a `use_in_cluster` checkbox (default True iff detection succeeded) — when enabled, the entry is flagged so the runtime client re-reads the SA token on each request.
- **`websocket_api.py`** — WebSocket API for the sidebar panel. Registers `kubernetes/cluster/overview`, `kubernetes/nodes/list`, `kubernetes/pods/list`, `kubernetes/pods/delete`, `kubernetes/jobs/delete`, `kubernetes/workloads/list`, `kubernetes/workloads/restart`, `kubernetes/ingresses/list`, and `kubernetes/config/list` commands that aggregate coordinator data across all loaded config entries (`get_loaded_entries`, then `entry.runtime_data`; `_get_coordinator(hass, entry_id)` resolves the single-entry commands and sends a `not_found` error when the entry is not loaded). Overview returns cluster health, resource counts, namespace breakdown, and alerts. Nodes/pods list commands return full resource details per cluster. The `kubernetes/pods/delete` command accepts `entry_id`, `pod_name`, and `namespace` to delete a pod and trigger a coordinator refresh. The `kubernetes/jobs/delete` command accepts `entry_id`, `job_name`, and `namespace` to delete a Job (admin-only) and trigger a coordinator refresh. Workloads list returns deployments, statefulsets, daemonsets, cronjobs, and jobs per cluster. The `kubernetes/workloads/restart` command accepts `entry_id`, `workload_name`, `namespace`, and `workload_type` to perform a rollout restart. The `kubernetes/ingresses/list` command forwards the coordinator's parsed ingress dicts per cluster (`ingress_class`, `rules`, `urls`, `tls_hosts`, …) for the Network tab — the TLS badge is derived client-side. Config list returns sanitized config entry settings (no secrets) for the settings tab.
- **`const.py`** — All constants, config keys, defaults, sensor/switch type identifiers. Service names: `SERVICE_SCALE_WORKLOAD`, `SERVICE_START_WORKLOAD`, `SERVICE_STOP_WORKLOAD`, `SERVICE_RESTART_WORKLOAD`, `SERVICE_DELETE_JOB`, `SERVICE_CORDON_NODE`, `SERVICE_UNCORDON_NODE`. Includes panel constants: `CONF_ENABLE_PANEL`, `DEFAULT_ENABLE_PANEL`, `PANEL_TITLE`, `PANEL_ICON`, `PANEL_URL`, `PANEL_FILENAME`. Watch-related: `CONF_ENABLE_WATCH`, `DEFAULT_WATCH_TIMEOUT_SECONDS`, `DEFAULT_WATCH_RECONNECT_DELAY`, `DEFAULT_FALLBACK_POLL_INTERVAL`, `WATCH_MAX_RECONNECT_DELAY`, `WATCH_RECONNECT_JITTER`, `WATCH_MAX_FAILURE_STREAK`. Event platform: `CONF_ENABLE_EVENTS` (opt-in, default `False`), `CONF_EVENT_TYPES`, `EVENT_TYPES_WARNING` / `EVENT_TYPES_ALL`, `DEFAULT_EVENT_TYPES`, `EVENT_CURATED_REASONS` (tuple of k8s reasons surfaced as distinct HA event types), `EVENT_TYPE_OTHER` (fallback for unrecognised reasons), and `event_signal(entry_id)` (dispatcher signal helper). Data-collection opt-out: `CONF_DISABLED_RESOURCES` (list option, default empty), `DISABLABLE_RESOURCES` (the 10 selectable categories), `FULLY_DISABLEABLE_RESOURCES` (the subset whose fetch is skipped entirely: pods, daemonsets, jobs, ingresses).
- **`diagnostics.py`** — HA Diagnostics platform. Implements `async_get_config_entry_diagnostics`; entries that are not `ConfigEntryState.LOADED` short-circuit to `{"state": "not_loaded"}`, otherwise it reads `entry.runtime_data` and returns a dict with the entry's redacted config/options (`CONF_API_TOKEN` and `CONF_CA_CERT` redacted via `homeassistant.components.diagnostics.async_redact_data`), integration flags, coordinator state (`last_update_success`, `last_update`, `update_interval_seconds`, per-resource bucket counts, watch task counts), and client config (host, port, namespaces, ssl/ca status, last auth error timestamp). HA auto-discovers the module — no registration in `__init__.py` needed.
- **`system_health.py`** — HA System Health platform. Registers a single info callback that aggregates across all loaded config entries (`get_loaded_entries`) and returns `clusters_configured`, `cluster_health` (`"ok"` / `"unreachable"` / `"X/Y reachable"` derived from each coordinator's `last_update_success`), `total_pods`, and `total_nodes`. Uses coordinator state rather than a URL ping so self-signed clusters and auth-required APIs report correctly. HA auto-discovers the module.
- **Repair issues** — Three `is_fixable=False` issues raised through `homeassistant.helpers.issue_registry`: `kubernetes_package_missing` (raised in `__init__.py:async_setup_entry` on `ImportError`, severity error), `metrics_server_unavailable_<entry_id>` (raised by the coordinator when nodes exist but the metrics API returns empty, severity warning), and `watch_connection_failing_<entry_id>` (raised by the coordinator when a watch loop fails `WATCH_MAX_FAILURE_STREAK` times in a row, severity warning). All auto-clear when the underlying condition resolves. Translation strings live in `translations/en.json` under `issues`.
- **`frontend/`** — Built sidebar panel JS bundle (`kubernetes-panel.js`). Source lives in `frontend/` at project root (Lit 3 + TypeScript + Vite).

### RBAC (outside `custom_components/`)

`chart/` is the **single source of truth** for the integration's Kubernetes RBAC — a Helm chart rendering the ServiceAccount, ClusterRole, ClusterRoleBinding, and the long-lived token Secret. `values.yaml` exposes `mode` (`full` | `minimal`), `nameOverride`, `serviceAccount.create`/`.annotations`, `tokenSecret.create`, `rbac.create`, and `rbac.extraRules`. Values are validated by `chart/values.schema.json` (Helm enforces it on every `install`/`upgrade`/`lint`/`template`) — `mode` is an `enum` there rather than a template-level `fail`, because a `fail` inside `if rbac.create` is skipped when `rbac.create=false`. Add every new value to the schema.

`manifests/{full,minimal}/*.yaml` are **generated** from the chart by `scripts/render-manifests.sh` and committed so the `kubectl apply -f <raw URL>` path keeps working. Never hand-edit them. `.github/workflows/helm.yaml` lints both modes, asserts an invalid `mode` is rejected (with and without `rbac.create=false`), and fails the build if `manifests/` drifts from a fresh render — compared via `git status --porcelain`, not `git diff`, so a new template rendering a new *untracked* manifest is caught. It pins the Helm CLI version so output stays byte-stable — Renovate tracks that pin via a custom regex manager.

When adding a feature that needs a new verb or resource: edit `chart/templates/clusterrole.yaml`, run `scripts/render-manifests.sh`, commit both, and update the permission matrix in `docs/RBAC.md`. `chart/templates/` is excluded from the `check-yaml` and `prettier` pre-commit hooks (Go templates); `manifests/` is excluded from `prettier` (generated).

Docs tell users migrating from the plain manifests to pass `--take-ownership` on the first `helm install` (Helm 3.17+; the objects already exist and are unowned), and `--reset-then-reuse-values` — not `--reuse-values` — on upgrade so newly added chart defaults actually apply.

The chart version is bumped by release-please (generic updater on `chart/Chart.yaml`) and pushed to `oci://ghcr.io/tibuntu/charts` by the `publish-chart` job in `release.yaml` when a release is created.

### Entity Hierarchy

Cluster device → (optional) Namespace devices → Entity instances. Grouping mode is configurable via `device_grouping_mode`.

### Patterns

- All entities read cached data from the coordinator, never calling the K8s API directly.
- Per-config-entry state lives on `entry.runtime_data` as a `KubernetesEntryData` dataclass, never in `hass.data[DOMAIN]` (HA quality scale `runtime-data`). Type entry parameters as `KubernetesConfigEntry` wherever the entry flows through, and enumerate entries with `get_loaded_entries(hass)` — both come from `coordinator.py`. `hass.data[DOMAIN]` is reserved for genuinely integration-wide state (currently only `panel_registered`).
- All four entity platforms (`sensor`, `switch`, `binary_sensor`, `event`) set module-level `PARALLEL_UPDATES = 0` — updates are centralized in the coordinator, so per-entity throttling is unnecessary (HA quality scale `parallel-updates` rule).
- The pytest coverage gate is `--cov-fail-under=95` in `pyproject.toml`; keep new code tested so overall coverage stays above 95%.
- `asyncio_mode = "auto"` in pytest — test functions are automatically treated as async. `asyncio_default_fixture_loop_scope = "function"` is set for compatibility with `pytest-homeassistant-custom-component`.
- Tests use `pytest-homeassistant-custom-component` for real HA test fixtures. Most test files (`test_init.py`, `test_device.py`, `test_config_flow.py`, `test_coordinator.py`, `test_services.py`, `test_binary_sensor.py`, `test_switch.py`, `test_sensors.py`, `test_kubernetes_integration.py`) use the real `hass` fixture and `MockConfigEntry`. Config flow tests register the handler via `HANDLERS` + `DATA_COMPONENTS` fixture (see `register_config_flow` in `test_config_flow.py`). `test_switch_platform.py` has been merged into `test_switch.py`. Only `test_websocket_api.py` still uses `mock_hass` from `conftest.py` — its local `_make_entry()`/`_load_entries()` helpers build mock entries with `runtime_data` and stub `hass.config_entries.async_loaded_entries`. Tests that need a real loaded entry use `MockConfigEntry` + `add_to_hass()` + `mock_state(hass, ConfigEntryState.LOADED)` and assign `entry.runtime_data = KubernetesEntryData(...)` (see `_add_loaded_entry` in `test_init.py` / `test_services.py`). K8s-specific mock fixtures (`mock_client`, `mock_coordinator`, `mock_kubernetes_client`, `mock_kubernetes_api`) remain in `conftest.py`.
- The kubernetes package is lazy-imported in config_flow via `_ensure_kubernetes_imported()` using thread-safe double-checked locking and checked at setup to handle missing dependency.

## Quality Scale

The integration voluntarily complies with Home Assistant's [Integration Quality Scale](https://developers.home-assistant.io/docs/core/integration-quality-scale/) at **Bronze and Silver** level (custom integrations cannot be officially certified — the rules are treated as binding conventions here). Any change must preserve these invariants:

- **action-setup / action-exceptions**: services are registered in `async_setup` (never per config entry, never unregistered) and handlers raise `ServiceValidationError` (caller mistakes) or `HomeAssistantError` (failed operations) — no silent failures. Multi-target calls attempt every target, then raise one aggregated error.
- **runtime-data**: per-entry state lives on `entry.runtime_data` (`KubernetesEntryData` in `coordinator.py`); `hass.data[DOMAIN]` holds only the global `panel_registered` flag. Enumerate entries via `get_loaded_entries(hass)`, never by iterating `hass.data`.
- **parallel-updates**: every platform module sets `PARALLEL_UPDATES = 0`.
- **config-flow-test-coverage**: `config_flow.py` stays at 100% line **and** branch coverage; the overall gate is `--cov-fail-under=95`, and codecov patch coverage on PRs should be 100%.
- **test-before-configure / unique-config-entry / reauthentication-flow**: the config flow validates connectivity before creating or updating entries, aborts on duplicate cluster names, and provides reconfigure and reauth flows. A persistent 401 sets `client.auth_failed` (connection probe with in-cluster retry) and the coordinator raises `ConfigEntryAuthFailed`.
- **entity conventions**: `has_entity_name = True`, stable unique IDs, `available` derived from `coordinator.last_update_success`.

When adding features, check the current rule set at the link above before implementing — new Bronze/Silver rules apply here too.

## Code Style

- **Ruff** for linting and formatting (replaces black, isort, flake8). 88-char line length.
- Type hints encouraged but mypy is not strict (`disallow_untyped_defs = false`)
- Prefer `aiohttp` over the blocking kubernetes client for new async HTTP calls
- All integration code must use `async`/`await` — no blocking calls
- Inside coroutines always use `asyncio.get_running_loop()`, never `asyncio.get_event_loop()` (deprecated in Python 3.10+ within a running loop)
- For long-lived aiohttp streams (`total=None`) always set a `sock_read` timeout to guard against stale/half-open TCP connections
- In `async_setup_entry`, start any background tasks **after** `async_forward_entry_setups()` so entity listeners are registered before the first events can arrive
- When adding support for a new Kubernetes resource type, always wire it into the Watch API as well (`coordinator._build_watch_configs` + a single-item parse helper on the client) — watch support is preferred over poll-only for every resource

## CI

GitHub Actions runs: pytest + ruff + mypy + bandit (Python 3.14), HACS validation, hassfest (HA manifest validation), mkdocs build, frontend lint + build (ESLint, Prettier, Vite), Helm chart lint + `manifests/` drift check (`.github/workflows/helm.yaml`), and CodeQL (`.github/workflows/codeql.yml`). The frontend workflow also verifies the committed `kubernetes-panel.js` bundle matches a fresh build — if a developer edits `.ts` source without rebuilding, CI will fail. Releases automated via release-please.

CodeQL uses **advanced setup** (a committed workflow) rather than GitHub's default setup, because default setup does not run on pull requests from forks — its required status checks could never be satisfied by an external contributor's PR. The matrix job name must stay `Analyze (<language>)` for `actions`, `javascript-typescript`, and `python`: branch protection on `main` requires those exact context names. The separate `CodeQL` context is posted by the code-scanning service (the `github-advanced-security` app) on SARIF upload, not by this workflow.

## Tests

Whenever changes are implemented to any integration code, always add or update the corresponding unit tests in `tests/`. Follow the existing patterns in the test files:

- Each new class gets a corresponding `Test<ClassName>` test class.
- Each new module-level helper function gets a `TestDiscover<Name>` or similar test class.
- Cover the happy path, edge cases (missing data, `None` coordinator data), and all distinct return values.
- Use `MockConfigEntry` from `pytest_homeassistant_custom_component.common` and the real `hass` fixture for platform setup tests. Entity unit tests (testing properties, state, edge cases) can directly instantiate entities with `MockConfigEntry` + mock coordinator/client. Use the shared K8s-specific fixtures from `conftest.py` (`mock_client`, `mock_coordinator`) rather than creating new ones where possible.

### Test directory structure

Pure unit tests (no HA dependency) live in `tests/unit/`. Currently `test_kubernetes_client.py` is the only file there — it tests the K8s API wrapper in isolation. All other test files in `tests/` use HA fixtures via `pytest-homeassistant-custom-component`. pytest discovers both directories recursively via `testpaths = ["tests"]`.
- Do not attempt to run tests locally — the CI pipeline handles test execution.
- Do not install packages locally (no `pip install`). All dependencies are managed by the CI pipeline.

## Documentation

Whenever changes are implemented, update all relevant documentation to reflect the current state of the code. This includes `README.md`, files in `docs/`, and any other `.md` files in the repository. Do not leave documentation that describes outdated behaviour.

Before finishing any task, fully review **all** `.md` files in the repository — including `README.md`, every file under `docs/`, and `CLAUDE.md` itself — to confirm that no documentation has become stale as a result of the change. Pay particular attention to installation instructions, configuration references, and RBAC/manifest paths, as these are the most likely to drift when the project structure changes.

## Version Management

Renovate handles all dependency updates. When making any change that involves version pinning or introduces a new dependency, always check `renovate.json` and ensure the version is tracked and grouped correctly:

- Versions pinned in `pyproject.toml` are managed by Renovate's pip manager.
- Versions pinned in `custom_components/kubernetes/manifest.json` are tracked via a custom regex manager.
- Pre-commit hook versions in `.pre-commit-config.yaml` are managed by Renovate's pre-commit manager.
- The Helm CLI version pinned in `.github/workflows/{helm,release}.yaml` is tracked via a custom regex manager (`helm/helm`, github-releases) and grouped as `helm`. Keep both workflows on the same version — the `manifests/` drift check depends on it.
- `chart/Chart.yaml` `version`/`appVersion` are bumped by release-please (generic updater, `x-release-please-version` comments), not Renovate.
- When the same package appears in multiple files, add a `groupName` rule in `renovate.json` so updates are batched into a single PR.
