"""Tests for the Kubernetes system_health platform."""

from __future__ import annotations

from unittest.mock import MagicMock

from homeassistant.core import HomeAssistant
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.kubernetes.const import DOMAIN
from custom_components.kubernetes.system_health import (
    async_register,
    system_health_info,
)

# `add_loaded_entry` (LOADED-state entry + KubernetesEntryData runtime_data)
# and `make_coordinator` (static MagicMock coordinator) come from
# tests/conftest.py's factory fixtures.


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


async def test_info_all_healthy(
    hass: HomeAssistant, add_loaded_entry, make_coordinator
):
    """Aggregates pod/node counts and reports 'ok' when every cluster is up."""
    add_loaded_entry(
        "a",
        coordinator=make_coordinator(
            data={"pods_count": 10, "nodes_count": 3}, last_update_success=True
        ),
    )
    add_loaded_entry(
        "b",
        coordinator=make_coordinator(
            data={"pods_count": 5, "nodes_count": 2}, last_update_success=True
        ),
    )

    info = await system_health_info(hass)

    assert info == {
        "clusters_configured": 2,
        "cluster_health": "ok",
        "total_pods": 15,
        "total_nodes": 5,
    }


async def test_info_partial_outage(
    hass: HomeAssistant, add_loaded_entry, make_coordinator
):
    """Mixed cluster state surfaces the X/Y reachable phrasing."""
    add_loaded_entry(
        "a",
        coordinator=make_coordinator(
            data={"pods_count": 4, "nodes_count": 1}, last_update_success=True
        ),
    )
    add_loaded_entry(
        "b",
        coordinator=make_coordinator(
            data={"pods_count": 0, "nodes_count": 0}, last_update_success=False
        ),
    )
    add_loaded_entry(
        "c",
        coordinator=make_coordinator(
            data={"pods_count": 2, "nodes_count": 1}, last_update_success=True
        ),
    )

    info = await system_health_info(hass)

    assert info == {
        "clusters_configured": 3,
        "cluster_health": "2/3 reachable",
        "total_pods": 6,
        "total_nodes": 2,
    }


async def test_info_all_unreachable(
    hass: HomeAssistant, add_loaded_entry, make_coordinator
):
    """When every coordinator has failed, report 'unreachable' once."""
    add_loaded_entry(
        "a",
        coordinator=make_coordinator(
            data={"pods_count": 0, "nodes_count": 0}, last_update_success=False
        ),
    )
    add_loaded_entry(
        "b",
        coordinator=make_coordinator(
            data={"pods_count": 0, "nodes_count": 0}, last_update_success=False
        ),
    )

    info = await system_health_info(hass)

    assert info["cluster_health"] == "unreachable"
    assert info["clusters_configured"] == 2


async def test_info_skips_entries_that_are_not_loaded(
    hass: HomeAssistant, add_loaded_entry, make_coordinator
):
    """Entries that never finished setup are not counted."""
    add_loaded_entry(
        "a",
        coordinator=make_coordinator(
            data={"pods_count": 1, "nodes_count": 1}, last_update_success=True
        ),
    )
    MockConfigEntry(domain=DOMAIN, entry_id="b").add_to_hass(hass)

    info = await system_health_info(hass)

    assert info["clusters_configured"] == 1
    assert info["cluster_health"] == "ok"


@pytest.mark.parametrize("missing_data", [None, {}])
async def test_info_tolerates_missing_data_payload(
    hass: HomeAssistant,
    missing_data: dict | None,
    add_loaded_entry,
    make_coordinator,
):
    """Coordinator without populated data still contributes to the cluster count."""
    coord = make_coordinator(data=missing_data, last_update_success=True)
    add_loaded_entry("a", coordinator=coord)

    info = await system_health_info(hass)

    assert info["clusters_configured"] == 1
    assert info["cluster_health"] == "ok"
    assert info["total_pods"] == 0
    assert info["total_nodes"] == 0
