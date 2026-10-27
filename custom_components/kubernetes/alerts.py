"""Cluster alert lists shared by the panel overview and the alert sensors."""

from __future__ import annotations

from typing import Any

_PRESSURE_KEYS: tuple[str, ...] = (
    "memory_pressure",
    "disk_pressure",
    "pid_pressure",
    "network_unavailable",
)

# (bucket, display type, desired key, ready/available key)
_WORKLOAD_REPLICA_KEYS: tuple[tuple[str, str, str, str], ...] = (
    ("deployments", "Deployment", "replicas", "available_replicas"),
    ("statefulsets", "StatefulSet", "replicas", "ready_replicas"),
    ("daemonsets", "DaemonSet", "desired_number_scheduled", "number_available"),
)


def nodes_under_pressure(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Return nodes with any pressure / network-unavailable condition set."""
    alerts = []
    for node_name, node in data.get("nodes", {}).items():
        conditions = [k for k in _PRESSURE_KEYS if node.get(k)]
        if conditions:
            alerts.append({"name": node_name, "conditions": conditions})
    return alerts


def degraded_workloads(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Return workloads with fewer ready/available replicas than desired."""
    alerts = []
    for bucket, workload_type, desired_key, ready_key in _WORKLOAD_REPLICA_KEYS:
        for workload in data.get(bucket, {}).values():
            desired = workload.get(desired_key, 0)
            ready = workload.get(ready_key) or 0
            if desired > 0 and ready < desired:
                alerts.append(
                    {
                        "name": workload.get("name", ""),
                        "type": workload_type,
                        "namespace": workload.get("namespace", "unknown"),
                        "ready": ready,
                        "desired": desired,
                    }
                )
    return alerts


def problem_pods(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Return pods the parser flagged as ``problem`` or in phase Failed/Unknown.

    The ``problem`` flag covers CrashLoopBackOff, image pull errors, non-zero
    exit codes, phase Failed and Unschedulable pods; phase Unknown (node lost)
    is the one case it does not derive from container state. ``Failed`` is
    checked again on purpose, so pod data parsed without the flag still alerts.
    ``reason`` is ``problem_reason``, falling back to the phase.
    """
    alerts = []
    for pod in data.get("pods", {}).values():
        phase = pod.get("phase", "")
        if pod.get("problem") or phase in ("Failed", "Unknown"):
            alerts.append(
                {
                    "name": pod.get("name", ""),
                    "namespace": pod.get("namespace", "unknown"),
                    "phase": phase,
                    "reason": pod.get("problem_reason") or phase,
                }
            )
    return alerts


def build_alerts(data: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """Build all alert lists for one cluster's coordinator data."""
    return {
        "nodes_with_pressure": nodes_under_pressure(data),
        "degraded_workloads": degraded_workloads(data),
        "failed_pods": problem_pods(data),
    }
