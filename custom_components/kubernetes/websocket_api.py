"""WebSocket API for the Kubernetes integration panel."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback
import voluptuous as vol

from .const import (
    CONF_CLUSTER_NAME,
    CONF_ENABLE_WATCH,
    DEFAULT_CLUSTER_NAME,
    DEFAULT_ENABLE_WATCH,
    DOMAIN,
    DOMAIN_META_KEYS,
)
from .coordinator import KubernetesDataCoordinator

_LOGGER = logging.getLogger(__name__)


@callback
def async_register_websocket_commands(hass: HomeAssistant) -> None:
    """Register all Kubernetes WebSocket commands."""
    websocket_api.async_register_command(hass, websocket_cluster_overview)


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


def _get_cluster_overview_data(hass: HomeAssistant) -> dict[str, Any]:
    """Gather cluster overview data from all config entries."""
    domain_data = hass.data.get(DOMAIN, {})
    clusters: list[dict[str, Any]] = []

    for entry_id, entry_data in domain_data.items():
        if entry_id in DOMAIN_META_KEYS:
            continue
        if not isinstance(entry_data, dict):
            continue

        coordinator: KubernetesDataCoordinator | None = entry_data.get("coordinator")
        config: dict[str, Any] = entry_data.get("config", {})

        if coordinator is None:
            continue

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
    watch_enabled = coordinator.config_entry.options.get(
        CONF_ENABLE_WATCH, DEFAULT_ENABLE_WATCH
    )

    if not data:
        return {
            "entry_id": entry_id,
            "cluster_name": config.get(CONF_CLUSTER_NAME, DEFAULT_CLUSTER_NAME),
            "healthy": None,
            "watch_enabled": watch_enabled,
            "last_update": 0.0,
            "counts": _empty_counts(),
            "namespaces": {},
            "alerts": _empty_alerts(),
        }

    counts = {
        "pods": data.get("pods_count", 0),
        "nodes": data.get("nodes_count", 0),
        "deployments": len(data.get("deployments", {})),
        "statefulsets": len(data.get("statefulsets", {})),
        "daemonsets": len(data.get("daemonsets", {})),
        "cronjobs": len(data.get("cronjobs", {})),
        "jobs": len(data.get("jobs", {})),
    }

    namespaces = _build_namespace_breakdown(data)
    alerts = _build_alerts(data)

    return {
        "entry_id": entry_id,
        "cluster_name": config.get(CONF_CLUSTER_NAME, DEFAULT_CLUSTER_NAME),
        "healthy": coordinator.last_update_success,
        "watch_enabled": watch_enabled,
        "last_update": data.get("last_update", 0.0),
        "counts": counts,
        "namespaces": namespaces,
        "alerts": alerts,
    }


def _build_namespace_breakdown(data: dict[str, Any]) -> dict[str, dict[str, int]]:
    """Build per-namespace resource counts."""
    ns_counts: dict[str, dict[str, int]] = {}

    for pod in data.get("pods", {}).values():
        ns = pod.get("namespace", "unknown")
        ns_counts.setdefault(ns, _empty_ns_counts())
        ns_counts[ns]["pods"] += 1

    for deploy in data.get("deployments", {}).values():
        ns = deploy.get("namespace", "unknown")
        ns_counts.setdefault(ns, _empty_ns_counts())
        ns_counts[ns]["deployments"] += 1

    for sts in data.get("statefulsets", {}).values():
        ns = sts.get("namespace", "unknown")
        ns_counts.setdefault(ns, _empty_ns_counts())
        ns_counts[ns]["statefulsets"] += 1

    for ds in data.get("daemonsets", {}).values():
        ns = ds.get("namespace", "unknown")
        ns_counts.setdefault(ns, _empty_ns_counts())
        ns_counts[ns]["daemonsets"] += 1

    for cj in data.get("cronjobs", {}).values():
        ns = cj.get("namespace", "unknown")
        ns_counts.setdefault(ns, _empty_ns_counts())
        ns_counts[ns]["cronjobs"] += 1

    for job in data.get("jobs", {}).values():
        ns = job.get("namespace", "unknown")
        ns_counts.setdefault(ns, _empty_ns_counts())
        ns_counts[ns]["jobs"] += 1

    return ns_counts


def _build_alerts(data: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """Build alert lists for nodes with pressure, degraded workloads, failed pods."""
    nodes_with_pressure: list[dict[str, Any]] = []
    degraded_workloads: list[dict[str, Any]] = []
    failed_pods: list[dict[str, Any]] = []

    # Check node conditions
    pressure_keys = [
        "memory_pressure",
        "disk_pressure",
        "pid_pressure",
        "network_unavailable",
    ]
    for node_name, node in data.get("nodes", {}).items():
        conditions = [k for k in pressure_keys if node.get(k)]
        if conditions:
            nodes_with_pressure.append({"name": node_name, "conditions": conditions})

    # Check degraded deployments
    for name, deploy in data.get("deployments", {}).items():
        desired = deploy.get("replicas", 0)
        available = deploy.get("available_replicas") or 0
        if desired > 0 and available < desired:
            degraded_workloads.append(
                {
                    "name": name,
                    "type": "Deployment",
                    "namespace": deploy.get("namespace", "unknown"),
                    "ready": available,
                    "desired": desired,
                }
            )

    # Check degraded statefulsets
    for name, sts in data.get("statefulsets", {}).items():
        desired = sts.get("replicas", 0)
        ready = sts.get("ready_replicas") or 0
        if desired > 0 and ready < desired:
            degraded_workloads.append(
                {
                    "name": name,
                    "type": "StatefulSet",
                    "namespace": sts.get("namespace", "unknown"),
                    "ready": ready,
                    "desired": desired,
                }
            )

    # Check degraded daemonsets
    for name, ds in data.get("daemonsets", {}).items():
        desired = ds.get("desired_number_scheduled", 0)
        available = ds.get("number_available") or 0
        if desired > 0 and available < desired:
            degraded_workloads.append(
                {
                    "name": name,
                    "type": "DaemonSet",
                    "namespace": ds.get("namespace", "unknown"),
                    "ready": available,
                    "desired": desired,
                }
            )

    # Check failed pods
    for pod in data.get("pods", {}).values():
        phase = pod.get("phase", "")
        if phase in ("Failed", "Unknown"):
            failed_pods.append(
                {
                    "name": pod.get("name", ""),
                    "namespace": pod.get("namespace", "unknown"),
                    "phase": phase,
                }
            )

    return {
        "nodes_with_pressure": nodes_with_pressure,
        "degraded_workloads": degraded_workloads,
        "failed_pods": failed_pods,
    }


def _empty_counts() -> dict[str, int]:
    """Return empty resource counts."""
    return {
        "pods": 0,
        "nodes": 0,
        "deployments": 0,
        "statefulsets": 0,
        "daemonsets": 0,
        "cronjobs": 0,
        "jobs": 0,
    }


def _empty_ns_counts() -> dict[str, int]:
    """Return empty per-namespace counts."""
    return {
        "pods": 0,
        "deployments": 0,
        "statefulsets": 0,
        "daemonsets": 0,
        "cronjobs": 0,
        "jobs": 0,
    }


def _empty_alerts() -> dict[str, list]:
    """Return empty alerts."""
    return {
        "nodes_with_pressure": [],
        "degraded_workloads": [],
        "failed_pods": [],
    }
