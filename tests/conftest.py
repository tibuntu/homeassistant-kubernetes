"""Test configuration and fixtures for the Kubernetes integration."""

import logging
from unittest.mock import AsyncMock, MagicMock

from homeassistant.config_entries import ConfigEntryState
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.kubernetes.const import DOMAIN
from custom_components.kubernetes.coordinator import KubernetesEntryData


@pytest.fixture(autouse=True)
def fail_on_ha_deprecations(caplog):
    """Fail tests that trigger Home Assistant deprecation warnings."""
    caplog.set_level(logging.WARNING, logger="homeassistant.helpers.frame")
    yield
    for record in caplog.records:
        if (
            record.name == "homeassistant.helpers.frame"
            and "deprecated" in record.message.lower()
        ):
            pytest.fail(f"HA deprecation warning: {record.message}")


@pytest.fixture
def mock_hass():
    """Mock Home Assistant instance."""
    from homeassistant.core import HomeAssistant

    hass = MagicMock(spec=HomeAssistant)
    hass.config = MagicMock()
    hass.config_entries = MagicMock()
    hass.config_entries.async_forward_entry_setups = AsyncMock()
    hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)
    hass.services = MagicMock()
    hass.services.async_register = AsyncMock()
    hass.services.async_remove = AsyncMock()
    hass.states = MagicMock()
    hass.states.async_set = AsyncMock()
    hass.states.async_remove = AsyncMock()
    hass.data = {}
    hass.bus = MagicMock()
    hass.bus.async_fire = AsyncMock()
    hass.async_add_executor_job = AsyncMock()
    hass.async_create_task = AsyncMock()
    hass.async_run_job = AsyncMock()
    hass.config_entries.async_forward_entry_setups = AsyncMock()
    hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)
    hass.state = MagicMock()
    hass.http = MagicMock()
    hass.http.async_register_static_paths = AsyncMock()
    return hass


@pytest.fixture
def make_config_entry(hass):
    """Factory for a real ``MockConfigEntry`` with the common cluster shape.

    ``_make(**overrides)`` accepts ``entry_id``, ``data`` (merged over the
    common shape), ``options``, and any other ``MockConfigEntry`` kwarg (e.g.
    ``state``). The entry is added to ``hass`` before being returned.
    """

    def _make(
        *, entry_id="test_entry_id", data=None, options=None, **kwargs
    ) -> MockConfigEntry:
        merged_data = {
            "host": "https://kubernetes.example.com",
            "port": 443,
            "verify_ssl": True,
            "cluster_name": "test-cluster",
        }
        merged_data.update(data or {})
        entry = MockConfigEntry(
            domain=DOMAIN,
            entry_id=entry_id,
            data=merged_data,
            options=options or {},
            **kwargs,
        )
        entry.add_to_hass(hass)
        return entry

    return _make


@pytest.fixture
def mock_config_entry(make_config_entry) -> MockConfigEntry:
    """Common config entry shape shared by switch/sensor/binary_sensor/device tests."""
    return make_config_entry()


@pytest.fixture
def add_loaded_entry(hass):
    """Factory: add a config entry in the LOADED state with runtime_data attached.

    ``_add(entry_id="entry_1", *, config=None, options=None, client=None,
    coordinator=None)`` builds a real ``MockConfigEntry`` with the given raw
    ``data``/``options`` (no common-shape merging — callers pass exactly the
    data they need), adds it to hass, and attaches a ``KubernetesEntryData``
    runtime_data wrapping ``client``/``coordinator`` (each defaulting to a
    bare ``MagicMock`` when not given).
    """

    def _add(
        entry_id="entry_1",
        *,
        config=None,
        options=None,
        client=None,
        coordinator=None,
    ) -> MockConfigEntry:
        entry = MockConfigEntry(
            domain=DOMAIN,
            entry_id=entry_id,
            data=config or {},
            options=options or {},
            state=ConfigEntryState.LOADED,
        )
        entry.add_to_hass(hass)
        entry.runtime_data = KubernetesEntryData(
            config=entry.data,
            client=client if client is not None else MagicMock(),
            coordinator=coordinator if coordinator is not None else MagicMock(),
        )
        return entry

    return _add


@pytest.fixture
def make_coordinator():
    """Factory for a static ``MagicMock`` coordinator.

    ``_make(data=None, last_update_success=True, **attrs)`` sets ``.data`` and
    ``.last_update_success`` and applies any extra attrs (e.g.
    ``update_interval``, ``_watch_tasks``, ``client``) via ``setattr``.
    """

    def _make(data=None, last_update_success=True, **attrs) -> MagicMock:
        coordinator = MagicMock()
        coordinator.data = data
        coordinator.last_update_success = last_update_success
        for key, value in attrs.items():
            setattr(coordinator, key, value)
        return coordinator

    return _make


@pytest.fixture
def mock_client():
    """Mock Kubernetes client for sensor tests."""
    client = MagicMock()
    client.get_pods_count = AsyncMock(return_value=5)
    client.get_nodes_count = AsyncMock(return_value=3)
    client.get_deployments_count = AsyncMock(return_value=2)
    client.get_statefulsets_count = AsyncMock(return_value=1)
    client.get_daemonsets_count = AsyncMock(return_value=1)
    client.get_ingresses = AsyncMock(return_value=[])
    client.get_ingresses_count = AsyncMock(return_value=0)
    client.get_services = AsyncMock(return_value=[])
    client.get_services_count = AsyncMock(return_value=0)
    client.is_cluster_healthy = AsyncMock(return_value=True)
    return client


@pytest.fixture
def mock_coordinator():
    """Mock coordinator for sensor tests."""
    coordinator = MagicMock()
    coordinator.data = {}
    coordinator.last_update_success = True
    coordinator.async_add_listener = MagicMock(return_value=lambda: None)
    coordinator.async_config_entry_first_refresh = AsyncMock()
    coordinator.get_all_nodes_data = MagicMock(
        return_value={
            "worker-node-1": {"name": "worker-node-1", "status": "Ready"},
            "worker-node-2": {"name": "worker-node-2", "status": "Ready"},
        }
    )
    coordinator.get_node_data = MagicMock(return_value=None)
    return coordinator
