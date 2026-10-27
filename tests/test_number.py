"""Tests for the Kubernetes number platform (replica count)."""

from unittest.mock import AsyncMock, MagicMock

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er
import pytest

from custom_components.kubernetes.const import (
    ATTR_WORKLOAD_TYPE,
    DOMAIN,
    WORKLOAD_TYPE_DEPLOYMENT,
    WORKLOAD_TYPE_STATEFULSET,
)
from custom_components.kubernetes.coordinator import KubernetesEntryData
from custom_components.kubernetes.number import (
    PARALLEL_UPDATES,
    KubernetesReplicaNumber,
    _async_add_new_entities,
    async_setup_entry,
)


def _data():
    return {
        "deployments": {
            "default_web": {
                "name": "web",
                "namespace": "default",
                "replicas": 3,
                "ready_replicas": 2,
                "available_replicas": 1,
            }
        },
        "statefulsets": {
            "db_pg": {"name": "pg", "namespace": "db", "replicas": 1},
        },
    }


@pytest.fixture
def coordinator():
    """Static coordinator with one Deployment and one StatefulSet."""
    coordinator = MagicMock()
    coordinator.data = _data()
    coordinator.last_update_success = True
    coordinator.async_request_refresh = AsyncMock()
    coordinator.client.scale_deployment = AsyncMock(return_value=True)
    coordinator.client.scale_statefulset = AsyncMock(return_value=True)
    return coordinator


def _attach(entry, coordinator):
    entry.runtime_data = KubernetesEntryData(
        config=entry.data, client=coordinator.client, coordinator=coordinator
    )


@pytest.fixture
def deployment_number(mock_config_entry, coordinator):
    """Number entity for the default/web Deployment."""
    entity = KubernetesReplicaNumber(
        coordinator, mock_config_entry, "web", "default", WORKLOAD_TYPE_DEPLOYMENT
    )
    entity.async_write_ha_state = MagicMock()
    return entity


class TestNumberSetup:
    """Platform setup and dynamic discovery."""

    def test_parallel_updates(self):
        """Updates are centralized in the coordinator."""
        assert PARALLEL_UPDATES == 0

    async def test_setup_builds_entities_from_coordinator_data(
        self, hass: HomeAssistant, mock_config_entry, coordinator
    ):
        """One number per Deployment/StatefulSet, never fetched from the client."""
        _attach(mock_config_entry, coordinator)
        add_entities = MagicMock()

        await async_setup_entry(hass, mock_config_entry, add_entities)

        entities = add_entities.call_args[0][0]
        assert {e.unique_id for e in entities} == {
            "test_entry_id_default_web_deployment_replicas",
            "test_entry_id_db_pg_statefulset_replicas",
        }
        assert mock_config_entry.runtime_data.number_add_entities is add_entities
        coordinator.async_add_listener.assert_called_once()
        coordinator.client.get_deployments.assert_not_called()
        coordinator.client.get_statefulsets.assert_not_called()

    async def test_listener_discovers_new_workloads_once(
        self, hass: HomeAssistant, mock_config_entry, coordinator
    ):
        """New workloads are added on coordinator updates without duplicates."""
        _attach(mock_config_entry, coordinator)
        add_entities = MagicMock()
        await async_setup_entry(hass, mock_config_entry, add_entities)
        listener = coordinator.async_add_listener.call_args[0][0]

        coordinator.data["deployments"]["default_api"] = {
            "name": "api",
            "namespace": "default",
            "replicas": 1,
        }
        listener()
        await hass.async_block_till_done()
        listener()
        await hass.async_block_till_done()

        assert add_entities.call_count == 2
        assert [e.unique_id for e in add_entities.call_args[0][0]] == [
            "test_entry_id_default_api_deployment_replicas"
        ]

    async def test_registered_entities_are_skipped(
        self, hass: HomeAssistant, mock_config_entry, coordinator
    ):
        """Entities already in the registry are not re-added; pending is pruned."""
        _attach(mock_config_entry, coordinator)
        registry = er.async_get(hass)
        for unique_id in (
            "test_entry_id_default_web_deployment_replicas",
            "test_entry_id_db_pg_statefulset_replicas",
        ):
            registry.async_get_or_create(
                "number", DOMAIN, unique_id, config_entry=mock_config_entry
            )
        entry_data = mock_config_entry.runtime_data
        entry_data.number_pending_unique_ids.add(
            "test_entry_id_default_web_deployment_replicas"
        )
        entry_data.number_add_entities = add_entities = MagicMock()

        await _async_add_new_entities(hass, mock_config_entry, coordinator)

        add_entities.assert_not_called()
        assert entry_data.number_pending_unique_ids == set()

    async def test_disabled_resources_gate(
        self, hass: HomeAssistant, make_config_entry, coordinator
    ):
        """Opted-out workload types get no number entity."""
        entry = make_config_entry(options={"disabled_resources": ["deployments"]})
        _attach(entry, coordinator)
        add_entities = MagicMock()

        await async_setup_entry(hass, entry, add_entities)

        assert [e.unique_id for e in add_entities.call_args[0][0]] == [
            "test_entry_id_db_pg_statefulset_replicas"
        ]

    async def test_no_data_or_callback_is_noop(
        self, hass: HomeAssistant, mock_config_entry, coordinator
    ):
        """Nothing happens without coordinator data or a stored callback."""
        _attach(mock_config_entry, coordinator)
        await _async_add_new_entities(hass, mock_config_entry, coordinator)

        add_entities = MagicMock()
        mock_config_entry.runtime_data.number_add_entities = add_entities
        coordinator.data = None
        await _async_add_new_entities(hass, mock_config_entry, coordinator)
        add_entities.assert_not_called()


class TestKubernetesReplicaNumber:
    """Entity state and scaling."""

    def test_static_attributes(self, deployment_number):
        """Name, unique id and limits."""
        assert deployment_number.name == "web replicas"
        assert deployment_number.native_min_value == 0
        assert deployment_number.native_max_value == 100
        assert deployment_number.native_step == 1
        assert deployment_number.should_poll is False

    def test_value_and_attributes(self, deployment_number):
        """Value and attributes come straight from coordinator data."""
        assert deployment_number.native_value == 3
        assert deployment_number.extra_state_attributes == {
            "namespace": "default",
            ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_DEPLOYMENT,
            "ready_replicas": 2,
            "available_replicas": 1,
        }

    def test_missing_workload(self, deployment_number, coordinator):
        """A workload that vanished has no value."""
        coordinator.data = None
        assert deployment_number.native_value is None
        assert deployment_number.extra_state_attributes["ready_replicas"] == 0

    def test_available_follows_coordinator(self, deployment_number, coordinator):
        """Availability mirrors the last coordinator refresh."""
        assert deployment_number.available is True
        coordinator.last_update_success = False
        assert deployment_number.available is False

    def test_device_info(self, hass: HomeAssistant, deployment_number):
        """Shares the namespace device with the matching switch."""
        deployment_number.hass = hass
        assert deployment_number.device_info["name"] == "test-cluster: default"

    async def test_added_to_hass_subscribes(self, hass, deployment_number, coordinator):
        """The entity writes state on every coordinator update."""
        deployment_number.hass = hass
        await deployment_number.async_added_to_hass()
        coordinator.async_add_listener.assert_called_once_with(
            deployment_number.async_write_ha_state
        )

    async def test_set_value_scales_deployment(self, deployment_number, coordinator):
        """Setting the value scales the workload and refreshes."""
        await deployment_number.async_set_native_value(5.0)

        coordinator.client.scale_deployment.assert_awaited_once_with(
            "web", 5, namespace="default"
        )
        assert deployment_number.native_value == 5
        deployment_number.async_write_ha_state.assert_called_once()
        coordinator.async_request_refresh.assert_awaited_once()

    async def test_set_value_scales_statefulset(self, mock_config_entry, coordinator):
        """StatefulSets use the StatefulSet scale method."""
        entity = KubernetesReplicaNumber(
            coordinator, mock_config_entry, "pg", "db", WORKLOAD_TYPE_STATEFULSET
        )
        entity.async_write_ha_state = MagicMock()
        coordinator.data = None  # workload vanished meanwhile: no optimistic write

        await entity.async_set_native_value(0)

        coordinator.client.scale_statefulset.assert_awaited_once_with(
            "pg", 0, namespace="db"
        )
        coordinator.async_request_refresh.assert_awaited_once()

    async def test_set_value_failure_raises(self, deployment_number, coordinator):
        """A failed scale raises instead of failing silently."""
        coordinator.client.scale_deployment.return_value = False

        with pytest.raises(HomeAssistantError, match="default/web to 4 replicas"):
            await deployment_number.async_set_native_value(4)

        assert deployment_number.native_value == 3
        coordinator.async_request_refresh.assert_not_awaited()
