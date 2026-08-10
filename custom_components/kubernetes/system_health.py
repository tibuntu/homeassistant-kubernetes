"""System Health support for the Kubernetes integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components import system_health
from homeassistant.core import HomeAssistant, callback

from .coordinator import get_loaded_entries


@callback
def async_register(
    hass: HomeAssistant,
    register: system_health.SystemHealthRegistration,
) -> None:
    """Register system health callbacks."""
    register.async_register_info(system_health_info)


async def system_health_info(hass: HomeAssistant) -> dict[str, Any]:
    """Get info for the system health page."""
    entries = get_loaded_entries(hass)
    total = len(entries)

    if not total:
        return {"clusters_configured": 0, "cluster_health": "no clusters configured"}

    healthy = 0
    total_pods = 0
    total_nodes = 0
    for entry in entries:
        coordinator = entry.runtime_data.coordinator
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
