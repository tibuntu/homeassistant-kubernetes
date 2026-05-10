"""Tests for the Kubernetes diagnostics platform."""

from __future__ import annotations

import asyncio
from datetime import timedelta
from unittest.mock import MagicMock

from homeassistant.core import HomeAssistant
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.kubernetes.const import (
    CONF_API_TOKEN,
    CONF_CA_CERT,
    DOMAIN,
)
from custom_components.kubernetes.diagnostics import (
    async_get_config_entry_diagnostics,
)


def _make_client() -> MagicMock:
    """Build a mock KubernetesClient with realistic attributes."""
    client = MagicMock()
    client.host = "test-cluster.example.com"
    client.port = 6443
    client.cluster_name = "test-cluster"
    client.namespaces = ["default", "kube-system"]
    client.monitor_all_namespaces = False
    client.verify_ssl = True
    client.ca_cert = "-----BEGIN CERTIFICATE-----\nfake\n-----END CERTIFICATE-----"
    client._last_auth_error_time = 0.0
    return client


def _make_coordinator(data: dict | None) -> MagicMock:
    """Build a mock coordinator with the given .data payload."""
    coordinator = MagicMock()
    coordinator.data = data
    coordinator.last_update_success = True
    coordinator.update_interval = timedelta(seconds=60)
    coordinator._watch_tasks = []
    return coordinator


@pytest.fixture
def populated_entry(hass: HomeAssistant) -> MockConfigEntry:
    """Create a config entry with realistic data + a populated coordinator."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        entry_id="diag_entry",
        title="Prod cluster",
        data={
            "host": "test-cluster.example.com",
            "port": 6443,
            CONF_API_TOKEN: "super-secret-token",
            CONF_CA_CERT: "-----BEGIN CERTIFICATE-----\nfake\n-----END CERTIFICATE-----",
            "namespace": "default",
            "verify_ssl": True,
        },
        options={"enable_panel": True, "enable_watch": False},
    )
    entry.add_to_hass(hass)

    coordinator = _make_coordinator(
        {
            "deployments": {"a": {}, "b": {}},
            "statefulsets": {"x": {}},
            "daemonsets": {},
            "cronjobs": {"c1": {}, "c2": {}, "c3": {}},
            "jobs": {},
            "pods": {"ns_p1": {}, "ns_p2": {}},
            "nodes": {"n1": {}, "n2": {}, "n3": {}},
            "pods_count": 2,
            "nodes_count": 3,
            "last_update": 1_700_000_000.0,
        }
    )
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "coordinator": coordinator,
        "client": _make_client(),
        "config": entry.data,
    }
    return entry


async def test_diagnostics_basic_shape(
    hass: HomeAssistant, populated_entry: MockConfigEntry
):
    """Diagnostics returns all expected sections with sensible values."""
    result = await async_get_config_entry_diagnostics(hass, populated_entry)

    assert set(result.keys()) == {"entry", "integration", "coordinator", "client"}

    # Top-level entry section
    assert result["entry"]["title"] == "Prod cluster"
    assert result["entry"]["data"]["host"] == "test-cluster.example.com"

    # Integration flags reflect options
    assert result["integration"] == {"panel_enabled": True, "watch_enabled": False}

    # Coordinator counts mirror the bucket sizes
    counts = result["coordinator"]["counts"]
    assert counts["deployments"] == 2
    assert counts["statefulsets"] == 1
    assert counts["daemonsets"] == 0
    assert counts["cronjobs"] == 3
    assert counts["jobs"] == 0
    assert counts["pods"] == 2
    assert counts["nodes"] == 3
    assert counts["pods_count"] == 2
    assert counts["nodes_count"] == 3

    assert result["coordinator"]["last_update_success"] is True
    assert result["coordinator"]["last_update"] == 1_700_000_000.0
    assert result["coordinator"]["update_interval_seconds"] == 60.0
    assert result["coordinator"]["watch"] == {"task_count": 0, "active_count": 0}

    # Client section exposes config but not secrets
    assert result["client"]["host"] == "test-cluster.example.com"
    assert result["client"]["port"] == 6443
    assert result["client"]["cluster_name"] == "test-cluster"
    assert result["client"]["namespaces"] == ["default", "kube-system"]
    assert result["client"]["verify_ssl"] is True
    assert result["client"]["ca_cert_configured"] is True
    assert result["client"]["last_auth_error_at"] is None


async def test_diagnostics_redacts_secrets(
    hass: HomeAssistant, populated_entry: MockConfigEntry
):
    """API token and CA cert must not appear in the diagnostics dump."""
    result = await async_get_config_entry_diagnostics(hass, populated_entry)

    assert result["entry"]["data"][CONF_API_TOKEN] != "super-secret-token"
    assert result["entry"]["data"][CONF_CA_CERT] != populated_entry.data[CONF_CA_CERT]
    # The raw secret string must not appear anywhere in the rendered payload.
    assert "super-secret-token" not in repr(result)
    assert "BEGIN CERTIFICATE" not in repr(result)


async def test_diagnostics_handles_empty_coordinator(hass: HomeAssistant):
    """When the coordinator has no data yet, diagnostics still succeeds."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        entry_id="empty_entry",
        title="Empty cluster",
        data={"host": "h", "port": 6443, CONF_API_TOKEN: "t"},
        options={},
    )
    entry.add_to_hass(hass)

    coordinator = _make_coordinator(None)
    coordinator.last_update_success = False

    client = _make_client()
    client.ca_cert = None

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "coordinator": coordinator,
        "client": client,
        "config": entry.data,
    }

    result = await async_get_config_entry_diagnostics(hass, entry)

    counts = result["coordinator"]["counts"]
    assert all(counts[k] is None for k in ("deployments", "pods", "nodes"))
    assert counts["pods_count"] is None
    assert counts["nodes_count"] is None
    assert result["coordinator"]["last_update"] is None
    assert result["coordinator"]["last_update_success"] is False
    assert result["client"]["ca_cert_configured"] is False


async def test_diagnostics_counts_active_watch_tasks(
    hass: HomeAssistant, populated_entry: MockConfigEntry
):
    """Active vs total watch task counts are reported separately."""
    coordinator = hass.data[DOMAIN][populated_entry.entry_id]["coordinator"]

    done_task = MagicMock(spec=asyncio.Task)
    done_task.done.return_value = True
    running_task = MagicMock(spec=asyncio.Task)
    running_task.done.return_value = False
    coordinator._watch_tasks = [done_task, running_task, running_task]

    result = await async_get_config_entry_diagnostics(hass, populated_entry)

    assert result["coordinator"]["watch"] == {"task_count": 3, "active_count": 2}


async def test_diagnostics_handles_setup_failure(hass: HomeAssistant):
    """If setup never populated hass.data, diagnostics still returns useful output."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        entry_id="not_loaded_entry",
        title="Broken cluster",
        data={
            "host": "unreachable.example.com",
            "port": 6443,
            CONF_API_TOKEN: "still-secret",
        },
        options={},
    )
    entry.add_to_hass(hass)
    # Deliberately do NOT populate hass.data[DOMAIN][entry.entry_id].

    result = await async_get_config_entry_diagnostics(hass, entry)

    assert result == {
        "entry": {
            "title": "Broken cluster",
            "data": result["entry"]["data"],  # asserted below
            "options": {},
            "state": "not_loaded",
        }
    }
    assert result["entry"]["data"][CONF_API_TOKEN] != "still-secret"
    assert "still-secret" not in repr(result)
    assert "coordinator" not in result
    assert "client" not in result
