"""WebSocket API for the Kubernetes integration panel."""

from __future__ import annotations

from collections.abc import Callable
import logging
from typing import Any

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback
import voluptuous as vol

from .alerts import build_alerts
from .const import (
    CONF_CLUSTER_NAME,
    CONF_DEVICE_GROUPING_MODE,
    CONF_ENABLE_PANEL,
    CONF_ENABLE_POD_LOGS,
    CONF_ENABLE_WATCH,
    CONF_HOST,
    CONF_MONITOR_ALL_NAMESPACES,
    CONF_NAMESPACE,
    CONF_PORT,
    CONF_SCALE_COOLDOWN,
    CONF_SCALE_VERIFICATION_TIMEOUT,
    CONF_SWITCH_UPDATE_INTERVAL,
    CONF_VERIFY_SSL,
    DEFAULT_CLUSTER_NAME,
    DEFAULT_DEVICE_GROUPING_MODE,
    DEFAULT_ENABLE_PANEL,
    DEFAULT_ENABLE_POD_LOGS,
    DEFAULT_ENABLE_WATCH,
    DEFAULT_MONITOR_ALL_NAMESPACES,
    DEFAULT_PORT,
    DEFAULT_SCALE_COOLDOWN,
    DEFAULT_SCALE_VERIFICATION_TIMEOUT,
    DEFAULT_SWITCH_UPDATE_INTERVAL,
    DEFAULT_VERIFY_SSL,
    POD_LOGS_MAX_TAIL_LINES,
    POD_LOGS_MIN_TAIL_LINES,
    WORKLOAD_TYPE_DEPLOYMENT,
    WORKLOAD_TYPE_STATEFULSET,
)
from .coordinator import (
    KubernetesDataCoordinator,
    disabled_resources,
    get_hpa_for,
    get_loaded_entries,
    hpa_attributes,
)
from .kubernetes_client import (
    KubernetesApiError,
    is_valid_k8s_name,
    is_valid_k8s_namespace,
)

_LOGGER = logging.getLogger(__name__)


def _valid_job_name(value: Any) -> str:
    """Validate a job name as a DNS-1123 subdomain."""
    if not is_valid_k8s_name(value):
        raise vol.Invalid("job_name must be a DNS-1123 subdomain")
    return str(value)


def _valid_namespace(value: Any) -> str:
    """Validate a namespace as a DNS-1123 label."""
    if not is_valid_k8s_namespace(value):
        raise vol.Invalid("namespace must be a DNS-1123 label")
    return str(value)


# Kubernetes object names (DNS-1123 subdomain). Rejects "..", "/" and the like
# before a name is put into an API path.
_K8S_NAME = vol.All(str, vol.Match(r"^[a-z0-9]([-a-z0-9.]*[a-z0-9])?$"))

# Resource buckets that are keyed "{namespace}_{name}" in coordinator.data and
# broken down per-namespace in the cluster overview. Order matches the
# previous hand-written counts dicts.
_NAMESPACED_KEYS: tuple[str, ...] = (
    "pods",
    "deployments",
    "statefulsets",
    "daemonsets",
    "cronjobs",
    "jobs",
    "ingresses",
    "services",
)
# All resource buckets counted in the cluster-wide overview (nodes are
# cluster-scoped, so they're not part of the namespace breakdown above).
_COUNT_KEYS: tuple[str, ...] = ("pods", "nodes", *_NAMESPACED_KEYS[1:])
# Workload kind each HPA-targetable bucket is matched against (scaleTargetRef).
_HPA_TARGET_KINDS = {
    "deployments": WORKLOAD_TYPE_DEPLOYMENT,
    "statefulsets": WORKLOAD_TYPE_STATEFULSET,
}


def _get_coordinator(
    hass: HomeAssistant, entry_id: str
) -> KubernetesDataCoordinator | None:
    """Return the coordinator of a loaded config entry, or None."""
    for entry in get_loaded_entries(hass):
        if entry.entry_id == entry_id:
            return entry.runtime_data.coordinator
    return None


def _pod_logs_enabled(entry: Any) -> bool:
    """Whether the opt-in pod log viewer is enabled for this config entry."""
    return bool(entry.options.get(CONF_ENABLE_POD_LOGS, DEFAULT_ENABLE_POD_LOGS))


@callback
def async_register_websocket_commands(hass: HomeAssistant) -> None:
    """Register all Kubernetes WebSocket commands."""
    websocket_api.async_register_command(hass, websocket_cluster_overview)
    websocket_api.async_register_command(hass, websocket_nodes_list)
    websocket_api.async_register_command(hass, websocket_pods_list)
    websocket_api.async_register_command(hass, websocket_workloads_list)
    websocket_api.async_register_command(hass, websocket_ingresses_list)
    websocket_api.async_register_command(hass, websocket_services_list)
    websocket_api.async_register_command(hass, websocket_config_list)
    websocket_api.async_register_command(hass, websocket_delete_pod)
    websocket_api.async_register_command(hass, websocket_pod_logs)
    websocket_api.async_register_command(hass, websocket_delete_job)
    websocket_api.async_register_command(hass, websocket_suspend_cronjob)
    websocket_api.async_register_command(hass, websocket_subscribe_updates)


@websocket_api.websocket_command({vol.Required("type"): "kubernetes/cluster/overview"})
@websocket_api.async_response
async def websocket_cluster_overview(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Return aggregated cluster overview data from all config entries."""
    result = _get_cluster_overview_data(hass)
    connection.send_result(msg["id"], result)


@websocket_api.websocket_command({vol.Required("type"): "kubernetes/nodes/list"})
@websocket_api.async_response
async def websocket_nodes_list(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Return all nodes from all config entries."""
    result = _list_data(hass, "nodes")
    connection.send_result(msg["id"], result)


@websocket_api.websocket_command({vol.Required("type"): "kubernetes/pods/list"})
@websocket_api.async_response
async def websocket_pods_list(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Return all pods from all config entries."""
    result = _list_data(hass, "pods")
    # _list_data builds one cluster per loaded entry, in the same order.
    for cluster, entry in zip(
        result["clusters"], get_loaded_entries(hass), strict=True
    ):
        cluster["pod_logs_enabled"] = _pod_logs_enabled(entry)
        # With pod collection disabled the coordinator never fetches pods, so
        # list them live for the panel (Pods tab, logs, delete). Not stored.
        if "pods" in disabled_resources(entry):
            try:
                cluster["pods"] = await entry.runtime_data.client.get_pods()
            except Exception:
                # The client already logged it (deduplicated).
                _LOGGER.debug("Live pod list failed for %s", entry.entry_id)
    connection.send_result(msg["id"], result)


@websocket_api.websocket_command({vol.Required("type"): "kubernetes/workloads/list"})
@websocket_api.async_response
async def websocket_workloads_list(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Return all workloads from all config entries."""
    result = _get_workloads_list_data(hass)
    connection.send_result(msg["id"], result)


@websocket_api.websocket_command({vol.Required("type"): "kubernetes/ingresses/list"})
@websocket_api.async_response
async def websocket_ingresses_list(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Return all ingresses from all config entries."""
    result = _list_data(hass, "ingresses")
    connection.send_result(msg["id"], result)


@websocket_api.websocket_command({vol.Required("type"): "kubernetes/services/list"})
@websocket_api.async_response
async def websocket_services_list(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Return all services from all config entries."""
    result = _list_data(hass, "services")
    connection.send_result(msg["id"], result)


def _get_cluster_overview_data(hass: HomeAssistant) -> dict[str, Any]:
    """Gather cluster overview data from all config entries."""
    clusters: list[dict[str, Any]] = []

    for entry in get_loaded_entries(hass):
        entry_id = entry.entry_id
        entry_data = entry.runtime_data
        coordinator = entry_data.coordinator
        config = entry_data.config

        cluster_info = _build_cluster_overview(entry_id, config, coordinator)
        clusters.append(cluster_info)

    return {"clusters": clusters}


def _build_cluster_overview(
    entry_id: str,
    config: dict[str, Any],
    coordinator: KubernetesDataCoordinator,
) -> dict[str, Any]:
    """Build overview data for a single cluster."""
    data = coordinator.data

    if not data:
        return {
            "entry_id": entry_id,
            "cluster_name": config.get(CONF_CLUSTER_NAME, DEFAULT_CLUSTER_NAME),
            "healthy": None,
            "server_version": None,
            "last_update": 0.0,
            "counts": _empty_counts(),
            "namespaces": {},
            "alerts": _empty_alerts(),
        }

    # Same precedence as the count sensors: a fully-disabled type has an empty
    # bucket but a ``{key}_count`` from the cheap count endpoint.
    counts = {
        key: data.get(f"{key}_count", len(data.get(key, {}))) for key in _COUNT_KEYS
    }

    namespaces = _build_namespace_breakdown(data)
    alerts = build_alerts(data)

    return {
        "entry_id": entry_id,
        "cluster_name": config.get(CONF_CLUSTER_NAME, DEFAULT_CLUSTER_NAME),
        "healthy": coordinator.last_update_success,
        "server_version": data.get("server_version"),
        "last_update": data.get("last_update", 0.0),
        "counts": counts,
        "namespaces": namespaces,
        "alerts": alerts,
    }


def _build_namespace_breakdown(data: dict[str, Any]) -> dict[str, dict[str, int]]:
    """Build per-namespace resource counts."""
    ns_counts: dict[str, dict[str, int]] = {}

    for key in _NAMESPACED_KEYS:
        for item in data.get(key, {}).values():
            ns = item.get("namespace", "unknown")
            ns_counts.setdefault(ns, _empty_ns_counts())
            ns_counts[ns][key] += 1

    return ns_counts


def _empty_counts() -> dict[str, int]:
    """Return empty resource counts."""
    return dict.fromkeys(_COUNT_KEYS, 0)


def _empty_ns_counts() -> dict[str, int]:
    """Return empty per-namespace counts."""
    return dict.fromkeys(_NAMESPACED_KEYS, 0)


def _empty_alerts() -> dict[str, list]:
    """Return empty alerts."""
    return {
        "nodes_with_pressure": [],
        "degraded_workloads": [],
        "failed_pods": [],
    }


def _list_data(hass: HomeAssistant, key: str) -> dict[str, Any]:
    """Gather a single resource list (nodes/pods/ingresses/services) from all
    config entries, keyed the same as the coordinator's data bucket."""
    clusters: list[dict[str, Any]] = []

    for entry in get_loaded_entries(hass):
        entry_data = entry.runtime_data
        data = entry_data.coordinator.data

        clusters.append(
            {
                "entry_id": entry.entry_id,
                "cluster_name": entry_data.config.get(
                    CONF_CLUSTER_NAME, DEFAULT_CLUSTER_NAME
                ),
                key: list(data.get(key, {}).values()) if data else [],
            }
        )

    return {"clusters": clusters}


def _with_hpa(data: dict[str, Any], bucket: str) -> list[dict[str, Any]]:
    """List a Deployment/StatefulSet bucket with the HPA fields merged in."""
    kind = _HPA_TARGET_KINDS[bucket]
    return [
        {
            **w,
            **hpa_attributes(get_hpa_for(data, kind, w["namespace"], w["name"])),
        }
        for w in data.get(bucket, {}).values()
    ]


def _get_workloads_list_data(hass: HomeAssistant) -> dict[str, Any]:
    """Gather workload data from all config entries."""
    clusters: list[dict[str, Any]] = []

    for entry in get_loaded_entries(hass):
        entry_id = entry.entry_id
        entry_data = entry.runtime_data
        coordinator = entry_data.coordinator
        config = entry_data.config

        data = coordinator.data

        if data:
            deployments = _with_hpa(data, "deployments")
            statefulsets = _with_hpa(data, "statefulsets")
            daemonsets = list(data.get("daemonsets", {}).values())
            cronjobs = list(data.get("cronjobs", {}).values())
            jobs = list(data.get("jobs", {}).values())
        else:
            deployments = []
            statefulsets = []
            daemonsets = []
            cronjobs = []
            jobs = []

        clusters.append(
            {
                "entry_id": entry_id,
                "cluster_name": config.get(CONF_CLUSTER_NAME, DEFAULT_CLUSTER_NAME),
                "deployments": deployments,
                "statefulsets": statefulsets,
                "daemonsets": daemonsets,
                "cronjobs": cronjobs,
                "jobs": jobs,
            }
        )

    return {"clusters": clusters}


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): "kubernetes/pods/delete",
        vol.Required("entry_id"): str,
        vol.Required("pod_name"): str,
        vol.Required("namespace"): str,
    }
)
@websocket_api.async_response
async def websocket_delete_pod(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Delete a pod."""
    entry_id = msg["entry_id"]
    pod_name = msg["pod_name"]
    namespace = msg["namespace"]

    coordinator = _get_coordinator(hass, entry_id)
    if coordinator is None:
        connection.send_error(msg["id"], "not_found", "Config entry not found")
        return

    client = coordinator.client
    success = await client.delete_pod(pod_name, namespace)

    if success:
        # Trigger a data refresh so the UI updates
        await coordinator.async_request_refresh()
        connection.send_result(msg["id"], {"success": True})
    else:
        connection.send_error(
            msg["id"],
            "delete_failed",
            f"Failed to delete pod {pod_name} in namespace {namespace}",
        )


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): "kubernetes/pods/logs",
        vol.Required("entry_id"): str,
        vol.Required("pod_name"): _K8S_NAME,
        vol.Required("namespace"): _K8S_NAME,
        vol.Optional("container"): str,
        vol.Optional("tail_lines", default=200): vol.All(
            int, vol.Range(min=POD_LOGS_MIN_TAIL_LINES, max=POD_LOGS_MAX_TAIL_LINES)
        ),
        vol.Optional("previous", default=False): bool,
    }
)
@websocket_api.async_response
async def websocket_pod_logs(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Return a log snapshot of a pod.

    Admin-only: logs routinely contain secrets. The text is passed straight
    through to the caller and never stored anywhere.
    """
    coordinator = _get_coordinator(hass, msg["entry_id"])
    if coordinator is None:
        connection.send_error(msg["id"], "not_found", "Config entry not found")
        return
    if not _pod_logs_enabled(hass.config_entries.async_get_entry(msg["entry_id"])):
        connection.send_error(
            msg["id"], "disabled", "Pod logs are disabled in the integration options"
        )
        return

    try:
        logs, truncated = await coordinator.client.get_pod_logs(
            msg["pod_name"],
            msg["namespace"],
            container=msg.get("container"),
            tail_lines=msg["tail_lines"],
            previous=msg["previous"],
        )
    except KubernetesApiError as ex:
        code = "forbidden" if ex.status == 403 else "logs_failed"
        connection.send_error(msg["id"], code, str(ex))
        return
    except Exception:
        # Transport errors can carry hosts/URLs; keep them in the log only.
        _LOGGER.exception("Failed to fetch logs of pod %s", msg["pod_name"])
        connection.send_error(msg["id"], "logs_failed", "Failed to fetch logs")
        return

    connection.send_result(msg["id"], {"logs": logs, "truncated": truncated})


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): "kubernetes/jobs/delete",
        vol.Required("entry_id"): str,
        vol.Required("job_name"): _valid_job_name,
        vol.Required("namespace"): _valid_namespace,
    }
)
@websocket_api.async_response
async def websocket_delete_job(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Delete a job."""
    entry_id = msg["entry_id"]
    job_name = msg["job_name"]
    namespace = msg["namespace"]

    coordinator = _get_coordinator(hass, entry_id)
    if coordinator is None:
        connection.send_error(msg["id"], "not_found", "Config entry not found")
        return

    client = coordinator.client
    try:
        success = await client.delete_job(job_name, namespace)
    except ValueError as err:
        connection.send_error(msg["id"], "invalid_format", str(err))
        return

    if success:
        # Trigger a data refresh so the UI updates
        await coordinator.async_request_refresh()
        connection.send_result(msg["id"], {"success": True})
    else:
        connection.send_error(
            msg["id"],
            "delete_failed",
            f"Failed to delete job {job_name} in namespace {namespace}",
        )


@websocket_api.websocket_command({vol.Required("type"): "kubernetes/config/list"})
@websocket_api.async_response
async def websocket_config_list(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Return sanitized config entry data (no secrets)."""
    result = _get_config_list_data(hass)
    connection.send_result(msg["id"], result)


def _get_config_list_data(hass: HomeAssistant) -> dict[str, Any]:
    """Gather config entry data from all entries, excluding secrets."""
    entries: list[dict[str, Any]] = []

    for entry in get_loaded_entries(hass):
        entry_id = entry.entry_id
        entry_data = entry.runtime_data
        coordinator = entry_data.coordinator
        config = entry_data.config

        panel_enabled = entry.options.get(CONF_ENABLE_PANEL, DEFAULT_ENABLE_PANEL)
        watch_enabled = entry.options.get(CONF_ENABLE_WATCH, DEFAULT_ENABLE_WATCH)

        namespaces = config.get(CONF_NAMESPACE, [])
        if isinstance(namespaces, str):
            namespaces = [namespaces]

        entries.append(
            {
                "entry_id": entry_id,
                "cluster_name": config.get(CONF_CLUSTER_NAME, DEFAULT_CLUSTER_NAME),
                "host": config.get(CONF_HOST, ""),
                "port": config.get(CONF_PORT, DEFAULT_PORT),
                "verify_ssl": config.get(CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL),
                "monitor_all_namespaces": config.get(
                    CONF_MONITOR_ALL_NAMESPACES, DEFAULT_MONITOR_ALL_NAMESPACES
                ),
                "namespaces": namespaces,
                "device_grouping_mode": config.get(
                    CONF_DEVICE_GROUPING_MODE, DEFAULT_DEVICE_GROUPING_MODE
                ),
                "switch_update_interval": config.get(
                    CONF_SWITCH_UPDATE_INTERVAL, DEFAULT_SWITCH_UPDATE_INTERVAL
                ),
                "scale_verification_timeout": config.get(
                    CONF_SCALE_VERIFICATION_TIMEOUT,
                    DEFAULT_SCALE_VERIFICATION_TIMEOUT,
                ),
                "scale_cooldown": config.get(
                    CONF_SCALE_COOLDOWN, DEFAULT_SCALE_COOLDOWN
                ),
                "panel_enabled": panel_enabled,
                "watch_enabled": watch_enabled,
                "pod_logs_enabled": _pod_logs_enabled(entry),
                "healthy": coordinator.last_update_success,
            }
        )

    return {"entries": entries}


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): "kubernetes/cronjobs/suspend",
        vol.Required("entry_id"): str,
        vol.Required("cronjob_name"): str,
        vol.Required("namespace"): str,
        vol.Required("suspend"): bool,
    }
)
@websocket_api.async_response
async def websocket_suspend_cronjob(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Suspend (``suspend: true``) or resume (``suspend: false``) a CronJob.

    The panel goes through WebSocket here because the dedicated
    ``suspend_cronjob``/``resume_cronjob`` services were retired in favor of
    the CronJob switch, and the panel works with workload names, not entity ids.
    """
    entry_id = msg["entry_id"]
    cronjob_name = msg["cronjob_name"]
    namespace = msg["namespace"]
    suspend = msg["suspend"]

    coordinator = _get_coordinator(hass, entry_id)
    if coordinator is None:
        connection.send_error(msg["id"], "not_found", "Config entry not found")
        return

    client = coordinator.client
    action = client.suspend_cronjob if suspend else client.resume_cronjob
    result = await action(cronjob_name, namespace)

    if result.get("success"):
        await coordinator.async_request_refresh()
        connection.send_result(msg["id"], {"success": True})
    else:
        verb = "suspend" if suspend else "resume"
        connection.send_error(
            msg["id"],
            f"{verb}_failed",
            result.get("error")
            or f"Failed to {verb} CronJob {cronjob_name} in namespace {namespace}",
        )


@callback
@websocket_api.websocket_command({vol.Required("type"): "kubernetes/subscribe_updates"})
def websocket_subscribe_updates(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Push a lightweight event whenever any cluster coordinator updates."""

    @callback
    def _push_update() -> None:
        connection.send_message(
            websocket_api.event_message(msg["id"], {"event": "updated"})
        )

    unsubs: list[Callable[[], None]] = [
        entry.runtime_data.coordinator.async_add_listener(_push_update)
        for entry in get_loaded_entries(hass)
    ]

    @callback
    def _unsubscribe() -> None:
        for unsub in unsubs:
            unsub()

    connection.subscriptions[msg["id"]] = _unsubscribe
    connection.send_result(msg["id"])
