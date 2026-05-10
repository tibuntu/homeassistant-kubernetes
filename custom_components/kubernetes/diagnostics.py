"""Diagnostics support for the Kubernetes integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    CONF_API_TOKEN,
    CONF_CA_CERT,
    CONF_ENABLE_PANEL,
    CONF_ENABLE_WATCH,
    DEFAULT_ENABLE_PANEL,
    DEFAULT_ENABLE_WATCH,
    DOMAIN,
)

TO_REDACT = {CONF_API_TOKEN, CONF_CA_CERT}

_COUNT_KEYS = (
    "deployments",
    "statefulsets",
    "daemonsets",
    "cronjobs",
    "jobs",
    "pods",
    "nodes",
)


def _coordinator_diagnostics(coordinator: Any) -> dict[str, Any]:
    """Summarize coordinator state without leaking workload names."""
    update_interval = coordinator.update_interval
    data = coordinator.data or {}

    counts: dict[str, int | None] = {}
    for key in _COUNT_KEYS:
        bucket = data.get(key)
        counts[key] = len(bucket) if isinstance(bucket, dict) else None

    # Scalar fields fetched separately by the coordinator. Mismatch with
    # len(pods)/len(nodes) above signals stale or partial data.
    counts["pods_count"] = data.get("pods_count")
    counts["nodes_count"] = data.get("nodes_count")

    watch_tasks = getattr(coordinator, "_watch_tasks", None) or []
    watch_status = {
        "task_count": len(watch_tasks),
        "active_count": sum(1 for t in watch_tasks if not t.done()),
    }

    return {
        "last_update_success": coordinator.last_update_success,
        "last_update": data.get("last_update"),
        "update_interval_seconds": (
            update_interval.total_seconds() if update_interval else None
        ),
        "counts": counts,
        "watch": watch_status,
    }


def _client_diagnostics(client: Any) -> dict[str, Any]:
    """Summarize client config. Host is included intentionally for debugging."""
    # 0.0 is the "no error yet" sentinel set in KubernetesClient.__init__.
    auth_error_time = getattr(client, "_last_auth_error_time", 0.0)
    return {
        "host": getattr(client, "host", None),
        "port": getattr(client, "port", None),
        "cluster_name": getattr(client, "cluster_name", None),
        "monitor_all_namespaces": getattr(client, "monitor_all_namespaces", None),
        "namespaces": list(getattr(client, "namespaces", []) or []),
        "verify_ssl": getattr(client, "verify_ssl", None),
        "ca_cert_configured": bool(getattr(client, "ca_cert", None)),
        "last_auth_error_at": auth_error_time if auth_error_time else None,
    }


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    entry_section = {
        "title": entry.title,
        "data": async_redact_data(entry.data, TO_REDACT),
        "options": async_redact_data(entry.options, TO_REDACT),
    }

    # Setup may have failed (cluster unreachable, missing dependency, etc.). HA
    # still offers the diagnostics download in that state — return what we can.
    entry_data = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if not entry_data:
        return {"entry": {**entry_section, "state": "not_loaded"}}

    coordinator = entry_data["coordinator"]
    client = entry_data["client"]

    return {
        "entry": entry_section,
        # Resolved-with-defaults view of the same flags carried in entry.options.
        "integration": {
            "panel_enabled": entry.options.get(CONF_ENABLE_PANEL, DEFAULT_ENABLE_PANEL),
            "watch_enabled": entry.options.get(CONF_ENABLE_WATCH, DEFAULT_ENABLE_WATCH),
        },
        "coordinator": _coordinator_diagnostics(coordinator),
        "client": _client_diagnostics(client),
    }
