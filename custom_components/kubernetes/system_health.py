"""System Health support for the Kubernetes integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components import system_health
from homeassistant.core import HomeAssistant, callback

from .const import DOMAIN, DOMAIN_META_KEYS


@callback
def async_register(
    hass: HomeAssistant,
    register: system_health.SystemHealthRegistration,
) -> None:
    """Register system health callbacks."""
    register.async_register_info(system_health_info)


def _collect_entry_data(hass: HomeAssistant) -> list[dict[str, Any]]:
    """Return real config entry payloads, skipping integration-wide metadata keys."""
    domain_data = hass.data.get(DOMAIN, {})
    return [
        v
        for k, v in domain_data.items()
        if k not in DOMAIN_META_KEYS and isinstance(v, dict)
    ]


async def system_health_info(hass: HomeAssistant) -> dict[str, Any]:
    """Get info for the system health page."""
    entries = _collect_entry_data(hass)
    total = len(entries)

    if not total:
        return {"clusters_configured": 0, "cluster_health": "no clusters configured"}

    healthy = 0
    total_pods = 0
    total_nodes = 0
    for entry in entries:
        coordinator = entry.get("coordinator")
        if coordinator is None:
            continue
        if coordinator.last_update_success:
            healthy += 1
        data = coordinator.data or {}
        total_pods += data.get("pods_count", 0)
        total_nodes += data.get("nodes_count", 0)

    if healthy == total:
        cluster_health = "ok"
    elif healthy == 0:
        cluster_health = "unreachable"
    else:
        cluster_health = f"{healthy}/{total} reachable"

    return {
        "clusters_configured": total,
        "cluster_health": cluster_health,
        "total_pods": total_pods,
        "total_nodes": total_nodes,
    }
