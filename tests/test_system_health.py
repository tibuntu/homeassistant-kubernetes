"""Tests for the Kubernetes system_health platform."""

from __future__ import annotations

from unittest.mock import MagicMock

from homeassistant.core import HomeAssistant
import pytest

from custom_components.kubernetes.const import DOMAIN
from custom_components.kubernetes.system_health import (
    async_register,
    system_health_info,
)


def _coordinator(
    *, healthy: bool, pods_count: int = 0, nodes_count: int = 0
) -> MagicMock:
    coordinator = MagicMock()
    coordinator.last_update_success = healthy
    coordinator.data = {"pods_count": pods_count, "nodes_count": nodes_count}
    return coordinator


def _populate(hass: HomeAssistant, entry_id: str, coordinator: MagicMock) -> None:
    hass.data.setdefault(DOMAIN, {})[entry_id] = {"coordinator": coordinator}


def test_async_register_invokes_register_info():
    """async_register must hand the info function to the framework."""
    hass = MagicMock(spec=HomeAssistant)
    register = MagicMock()

    async_register(hass, register)

    register.async_register_info.assert_called_once_with(system_health_info)


async def test_info_no_clusters(hass: HomeAssistant):
    """With no config entries the response is a friendly placeholder."""
    info = await system_health_info(hass)
    assert info == {
        "clusters_configured": 0,
        "cluster_health": "no clusters configured",
    }


async def test_info_all_healthy(hass: HomeAssistant):
    """Aggregates pod/node counts and reports 'ok' when every cluster is up."""
    _populate(hass, "a", _coordinator(healthy=True, pods_count=10, nodes_count=3))
    _populate(hass, "b", _coordinator(healthy=True, pods_count=5, nodes_count=2))

    info = await system_health_info(hass)

    assert info == {
        "clusters_configured": 2,
        "cluster_health": "ok",
        "total_pods": 15,
        "total_nodes": 5,
    }


async def test_info_partial_outage(hass: HomeAssistant):
    """Mixed cluster state surfaces the X/Y reachable phrasing."""
    _populate(hass, "a", _coordinator(healthy=True, pods_count=4, nodes_count=1))
    _populate(hass, "b", _coordinator(healthy=False, pods_count=0, nodes_count=0))
    _populate(hass, "c", _coordinator(healthy=True, pods_count=2, nodes_count=1))

    info = await system_health_info(hass)

    assert info == {
        "clusters_configured": 3,
        "cluster_health": "2/3 reachable",
        "total_pods": 6,
        "total_nodes": 2,
    }


async def test_info_all_unreachable(hass: HomeAssistant):
    """When every coordinator has failed, report 'unreachable' once."""
    _populate(hass, "a", _coordinator(healthy=False))
    _populate(hass, "b", _coordinator(healthy=False))

    info = await system_health_info(hass)

    assert info["cluster_health"] == "unreachable"
    assert info["clusters_configured"] == 2


async def test_info_skips_metadata_keys(hass: HomeAssistant):
    """Non-entry keys in hass.data[DOMAIN] (panel_registered, etc.) are ignored."""
    _populate(hass, "a", _coordinator(healthy=True, pods_count=1, nodes_count=1))
    hass.data[DOMAIN]["panel_registered"] = True
    hass.data[DOMAIN]["switch_add_entities"] = MagicMock()

    info = await system_health_info(hass)

    assert info["clusters_configured"] == 1
    assert info["cluster_health"] == "ok"


async def test_info_handles_missing_coordinator(hass: HomeAssistant):
    """An entry without a coordinator (mid-setup) does not crash and counts as unhealthy."""
    hass.data.setdefault(DOMAIN, {})["a"] = {"coordinator": None}
    _populate(hass, "b", _coordinator(healthy=True, pods_count=3, nodes_count=1))

    info = await system_health_info(hass)

    assert info["clusters_configured"] == 2
    assert info["cluster_health"] == "1/2 reachable"
    assert info["total_pods"] == 3
    assert info["total_nodes"] == 1


@pytest.mark.parametrize("missing_data", [None, {}])
async def test_info_tolerates_missing_data_payload(
    hass: HomeAssistant, missing_data: dict | None
):
    """Coordinator without populated data still contributes to the cluster count."""
    coord = _coordinator(healthy=True)
    coord.data = missing_data
    _populate(hass, "a", coord)

    info = await system_health_info(hass)

    assert info["clusters_configured"] == 1
    assert info["cluster_health"] == "ok"
    assert info["total_pods"] == 0
    assert info["total_nodes"] == 0
