"""Tests for the Kubernetes binary sensor platform."""

from unittest.mock import AsyncMock, MagicMock

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_VERIFY_SSL
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.kubernetes.binary_sensor import (
    KubernetesBaseBinarySensor,
    KubernetesClusterHealthSensor,
    KubernetesNodeConditionBinarySensor,
    _async_discover_and_add_new_binary_sensors,
    _discover_new_node_condition_sensors,
    async_setup_entry,
)
from custom_components.kubernetes.const import DOMAIN


@pytest.fixture
def mock_config_entry(hass: HomeAssistant) -> MockConfigEntry:
    """Create a mock config entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        entry_id="test_entry_id",
        data={
            CONF_HOST: "https://kubernetes.example.com",
            CONF_PORT: 443,
            CONF_VERIFY_SSL: True,
        },
    )
    entry.add_to_hass(hass)
    return entry


@pytest.fixture
def mock_client():
    """Create a minimal mock client for binary sensor tests.

    Shadows the conftest mock_client intentionally — binary sensor tests only
    need ``is_cluster_healthy``, so a minimal fixture avoids coupling to the
    broader conftest mock that carries deployment/statefulset helpers.
    """
    client = MagicMock()
    client.is_cluster_healthy = AsyncMock(return_value=True)
    return client


@pytest.fixture
def mock_coordinator():
    """Create a minimal mock coordinator for binary sensor tests.

    Shadows the conftest mock_coordinator intentionally — binary sensor tests
    only need node data and basic coordinator attributes, not the full
    deployment/statefulset/daemonset data provided by the conftest version.
    """
    coordinator = MagicMock()
    coordinator.data = {"nodes": {}}
    coordinator.last_update_success = True
    coordinator.async_config_entry_first_refresh = AsyncMock()
    coordinator.async_add_listener = MagicMock(return_value=MagicMock())
    return coordinator


@pytest.fixture
def setup_domain_data(
    hass: HomeAssistant, mock_config_entry, mock_coordinator, mock_client
) -> None:
    """Set up hass.data with kubernetes domain data."""
    hass.data.setdefault(DOMAIN, {})[mock_config_entry.entry_id] = {
        "coordinator": mock_coordinator,
        "client": mock_client,
    }


class TestKubernetesBinarySensorSetup:
    """Test binary sensor setup."""

    async def test_async_setup_entry_success(
        self,
        hass: HomeAssistant,
        mock_config_entry,
        mock_client,
        setup_domain_data,
    ):
        """Test successful binary sensor setup with no nodes yields 1 entity."""
        mock_add_entities = MagicMock()

        await async_setup_entry(hass, mock_config_entry, mock_add_entities)

        mock_add_entities.assert_called_once()
        added_entities = mock_add_entities.call_args[0][0]
        assert len(added_entities) == 1
        assert isinstance(added_entities[0], KubernetesClusterHealthSensor)

    async def test_async_setup_entry_with_nodes(
        self,
        hass: HomeAssistant,
        mock_config_entry,
        mock_client,
        mock_coordinator,
        setup_domain_data,
    ):
        """Test setup creates 4 condition sensors per node."""
        mock_coordinator.data = {
            "nodes": {
                "node-1": {
                    "memory_pressure": False,
                    "disk_pressure": False,
                    "pid_pressure": False,
                    "network_unavailable": False,
                },
                "node-2": {
                    "memory_pressure": False,
                    "disk_pressure": False,
                    "pid_pressure": False,
                    "network_unavailable": False,
                },
            }
        }
        mock_add_entities = MagicMock()

        await async_setup_entry(hass, mock_config_entry, mock_add_entities)

        added_entities = mock_add_entities.call_args[0][0]
        # 1 cluster health + 2 nodes × 4 conditions = 9
        assert len(added_entities) == 9
        condition_sensors = [
            e
            for e in added_entities
            if isinstance(e, KubernetesNodeConditionBinarySensor)
        ]
        assert len(condition_sensors) == 8

    async def test_async_setup_entry_missing_client(
        self,
        hass: HomeAssistant,
        mock_config_entry,
        mock_coordinator,
    ):
        """Test binary sensor setup when client is missing."""
        hass.data.setdefault(DOMAIN, {})[mock_config_entry.entry_id] = {
            "coordinator": mock_coordinator
        }

        mock_add_entities = MagicMock()

        with pytest.raises(KeyError, match="'client'"):
            await async_setup_entry(hass, mock_config_entry, mock_add_entities)


class TestKubernetesBaseBinarySensor:
    """Test base binary sensor class."""

    def test_base_binary_sensor_initialization(self, mock_config_entry, mock_client):
        """Test base binary sensor initialization."""
        sensor = KubernetesBaseBinarySensor(mock_client, mock_config_entry)

        assert sensor.client == mock_client
        assert sensor.config_entry == mock_config_entry
        assert sensor._attr_has_entity_name is True


class TestKubernetesClusterHealthSensor:
    """Test Kubernetes cluster health binary sensor."""

    def test_sensor_initialization(self, mock_config_entry, mock_client):
        """Test cluster health sensor initialization."""
        sensor = KubernetesClusterHealthSensor(mock_client, mock_config_entry)

        assert sensor.name == "Cluster Health"
        assert sensor.unique_id == "test_entry_id_cluster_health"
        assert sensor.device_class == BinarySensorDeviceClass.CONNECTIVITY
        assert sensor._attr_has_entity_name is True

    async def test_sensor_update_success(self, mock_config_entry, mock_client):
        """Test successful sensor update."""
        mock_client.is_cluster_healthy.return_value = True

        sensor = KubernetesClusterHealthSensor(mock_client, mock_config_entry)

        await sensor.async_update()

        assert sensor.is_on is True
        mock_client.is_cluster_healthy.assert_called_once()

    async def test_sensor_update_cluster_unhealthy(
        self, mock_config_entry, mock_client
    ):
        """Test sensor update when cluster is unhealthy."""
        mock_client.is_cluster_healthy.return_value = False

        sensor = KubernetesClusterHealthSensor(mock_client, mock_config_entry)

        await sensor.async_update()

        assert sensor.is_on is False
        mock_client.is_cluster_healthy.assert_called_once()

    async def test_sensor_update_exception(self, mock_config_entry, mock_client):
        """Test sensor update when client call fails."""
        mock_client.is_cluster_healthy.side_effect = Exception("API Error")

        sensor = KubernetesClusterHealthSensor(mock_client, mock_config_entry)

        await sensor.async_update()

        # Should handle exception gracefully and set to False
        assert sensor.is_on is False
        mock_client.is_cluster_healthy.assert_called_once()

    async def test_sensor_update_connection_error(self, mock_config_entry, mock_client):
        """Test sensor update with connection error."""
        mock_client.is_cluster_healthy.side_effect = ConnectionError(
            "Connection failed"
        )

        sensor = KubernetesClusterHealthSensor(mock_client, mock_config_entry)

        await sensor.async_update()

        # Should handle connection error gracefully
        assert sensor.is_on is False
        mock_client.is_cluster_healthy.assert_called_once()

    def test_sensor_properties(self, mock_config_entry, mock_client):
        """Test sensor properties."""
        sensor = KubernetesClusterHealthSensor(mock_client, mock_config_entry)

        # Test initial state
        assert sensor.is_on is None

        # Test after setting state
        sensor._attr_is_on = True
        assert sensor.is_on is True

        sensor._attr_is_on = False
        assert sensor.is_on is False

    def test_sensor_unique_id_format(self, mock_config_entry, mock_client):
        """Test sensor unique ID format."""
        sensor = KubernetesClusterHealthSensor(mock_client, mock_config_entry)

        expected_unique_id = f"{mock_config_entry.entry_id}_cluster_health"
        assert sensor.unique_id == expected_unique_id

    def test_sensor_device_class(self, mock_config_entry, mock_client):
        """Test sensor device class."""
        sensor = KubernetesClusterHealthSensor(mock_client, mock_config_entry)

        assert sensor.device_class == BinarySensorDeviceClass.CONNECTIVITY

    async def test_sensor_multiple_updates(self, mock_config_entry, mock_client):
        """Test multiple sensor updates."""
        # First update - healthy
        mock_client.is_cluster_healthy.return_value = True
        sensor = KubernetesClusterHealthSensor(mock_client, mock_config_entry)

        await sensor.async_update()
        assert sensor.is_on is True

        # Second update - unhealthy
        mock_client.is_cluster_healthy.return_value = False
        await sensor.async_update()
        assert sensor.is_on is False

        # Verify client was called twice
        assert mock_client.is_cluster_healthy.call_count == 2

    async def test_sensor_update_with_none_client(self, mock_config_entry):
        """Test sensor update with None client."""
        sensor = KubernetesClusterHealthSensor(None, mock_config_entry)

        # Should handle None client gracefully
        await sensor.async_update()
        assert sensor.is_on is False

    def test_sensor_entity_attributes(self, mock_config_entry, mock_client):
        """Test sensor entity attributes."""
        sensor = KubernetesClusterHealthSensor(mock_client, mock_config_entry)

        # Test that the sensor has the expected attributes
        assert hasattr(sensor, "_attr_name")
        assert hasattr(sensor, "_attr_unique_id")
        assert hasattr(sensor, "_attr_device_class")
        assert hasattr(sensor, "_attr_has_entity_name")
        assert hasattr(sensor, "_attr_is_on")

        assert sensor._attr_name == "Cluster Health"
        assert sensor._attr_unique_id == "test_entry_id_cluster_health"
        assert sensor._attr_device_class == BinarySensorDeviceClass.CONNECTIVITY
        assert sensor._attr_has_entity_name is True


class TestKubernetesNodeConditionBinarySensor:
    """Test node condition binary sensors."""

    def _make_sensor(
        self, mock_coordinator, mock_config_entry, condition="memory_pressure"
    ):
        return KubernetesNodeConditionBinarySensor(
            mock_coordinator, mock_config_entry, "node-1", condition
        )

    def test_initialization(self, mock_coordinator, mock_config_entry):
        """Test name, unique_id, device_class, and has_entity_name."""
        sensor = self._make_sensor(
            mock_coordinator, mock_config_entry, "memory_pressure"
        )

        assert sensor.name == "node-1 Memory Pressure"
        assert sensor.unique_id == "test_entry_id_node_node-1_memory_pressure"
        assert sensor.device_class == BinarySensorDeviceClass.PROBLEM
        assert sensor._attr_has_entity_name is True

    def test_unique_ids_are_distinct_per_condition(
        self, mock_coordinator, mock_config_entry
    ):
        """Test that each condition produces a unique ID."""
        conditions = [
            "memory_pressure",
            "disk_pressure",
            "pid_pressure",
            "network_unavailable",
        ]
        sensors = [
            self._make_sensor(mock_coordinator, mock_config_entry, c)
            for c in conditions
        ]
        unique_ids = {s.unique_id for s in sensors}
        assert len(unique_ids) == 4

    def test_names_for_all_conditions(self, mock_coordinator, mock_config_entry):
        """Test display names for all four conditions."""
        expected = {
            "memory_pressure": "node-1 Memory Pressure",
            "disk_pressure": "node-1 Disk Pressure",
            "pid_pressure": "node-1 PID Pressure",
            "network_unavailable": "node-1 Network Unavailable",
        }
        for condition, name in expected.items():
            sensor = self._make_sensor(mock_coordinator, mock_config_entry, condition)
            assert sensor.name == name

    def test_device_info_uses_cluster_device(self, mock_coordinator, mock_config_entry):
        """Test sensor is attached to the cluster device."""
        sensor = self._make_sensor(mock_coordinator, mock_config_entry)
        device_info = sensor.device_info
        assert device_info["identifiers"] == {("kubernetes", "test_entry_id_cluster")}

    def test_is_on_false_when_no_pressure(self, mock_coordinator, mock_config_entry):
        """Test is_on is False when the condition is not active."""
        mock_coordinator.data = {"nodes": {"node-1": {"memory_pressure": False}}}
        sensor = self._make_sensor(
            mock_coordinator, mock_config_entry, "memory_pressure"
        )
        assert sensor.is_on is False

    def test_is_on_true_when_pressure_active(self, mock_coordinator, mock_config_entry):
        """Test is_on is True when the condition is active."""
        mock_coordinator.data = {"nodes": {"node-1": {"memory_pressure": True}}}
        sensor = self._make_sensor(
            mock_coordinator, mock_config_entry, "memory_pressure"
        )
        assert sensor.is_on is True

    def test_is_on_none_when_no_coordinator_data(
        self, mock_coordinator, mock_config_entry
    ):
        """Test is_on is None when coordinator has no data."""
        mock_coordinator.data = None
        sensor = self._make_sensor(mock_coordinator, mock_config_entry)
        assert sensor.is_on is None

    def test_is_on_none_when_node_missing(self, mock_coordinator, mock_config_entry):
        """Test is_on is None when the node is absent from coordinator data."""
        mock_coordinator.data = {"nodes": {}}
        sensor = self._make_sensor(mock_coordinator, mock_config_entry)
        assert sensor.is_on is None

    def test_available_reflects_coordinator_success(
        self, mock_coordinator, mock_config_entry
    ):
        """Test availability mirrors coordinator.last_update_success."""
        mock_coordinator.last_update_success = True
        sensor = self._make_sensor(mock_coordinator, mock_config_entry)
        assert sensor.available is True

        mock_coordinator.last_update_success = False
        assert sensor.available is False

    def test_all_four_conditions_readable(self, mock_coordinator, mock_config_entry):
        """Test that all four condition fields are read correctly."""
        mock_coordinator.data = {
            "nodes": {
                "node-1": {
                    "memory_pressure": True,
                    "disk_pressure": False,
                    "pid_pressure": True,
                    "network_unavailable": False,
                }
            }
        }
        expected = {
            "memory_pressure": True,
            "disk_pressure": False,
            "pid_pressure": True,
            "network_unavailable": False,
        }
        for condition, value in expected.items():
            sensor = self._make_sensor(mock_coordinator, mock_config_entry, condition)
            assert sensor.is_on is value


class TestDiscoverNewNodeConditionSensors:
    """Test _discover_new_node_condition_sensors helper."""

    def test_discovers_new_node(self, mock_coordinator, mock_config_entry):
        """Test discovering sensors for a brand-new node."""
        mock_coordinator.data = {
            "nodes": {
                "new-node": {
                    "memory_pressure": False,
                    "disk_pressure": False,
                    "pid_pressure": False,
                    "network_unavailable": False,
                }
            }
        }
        result = _discover_new_node_condition_sensors(
            mock_coordinator, mock_config_entry, existing_unique_ids=set()
        )
        assert len(result) == 4
        conditions = {s.condition_key for s in result}
        assert conditions == {
            "memory_pressure",
            "disk_pressure",
            "pid_pressure",
            "network_unavailable",
        }

    def test_skips_existing_node(self, mock_coordinator, mock_config_entry):
        """Test that already-registered nodes are not duplicated."""
        mock_coordinator.data = {
            "nodes": {
                "node-1": {
                    "memory_pressure": False,
                    "disk_pressure": False,
                    "pid_pressure": False,
                    "network_unavailable": False,
                }
            }
        }
        existing = {
            f"{mock_config_entry.entry_id}_node_node-1_{c}"
            for c in [
                "memory_pressure",
                "disk_pressure",
                "pid_pressure",
                "network_unavailable",
            ]
        }
        result = _discover_new_node_condition_sensors(
            mock_coordinator, mock_config_entry, existing_unique_ids=existing
        )
        assert len(result) == 0

    def test_returns_empty_when_no_data(self, mock_coordinator, mock_config_entry):
        """Test returns empty list when coordinator has no data."""
        mock_coordinator.data = None
        result = _discover_new_node_condition_sensors(
            mock_coordinator, mock_config_entry, existing_unique_ids=set()
        )
        assert result == []

    def test_returns_empty_when_no_nodes(self, mock_coordinator, mock_config_entry):
        """Test returns empty list when coordinator data has no nodes key."""
        mock_coordinator.data = {"pods": {}}
        result = _discover_new_node_condition_sensors(
            mock_coordinator, mock_config_entry, existing_unique_ids=set()
        )
        assert result == []

    def test_discovers_only_new_nodes(self, mock_coordinator, mock_config_entry):
        """Test only new nodes get sensors when some already exist."""
        mock_coordinator.data = {
            "nodes": {
                "old-node": {"memory_pressure": False},
                "new-node": {"memory_pressure": False},
            }
        }
        existing = {
            f"{mock_config_entry.entry_id}_node_old-node_{c}"
            for c in [
                "memory_pressure",
                "disk_pressure",
                "pid_pressure",
                "network_unavailable",
            ]
        }
        result = _discover_new_node_condition_sensors(
            mock_coordinator, mock_config_entry, existing_unique_ids=existing
        )
        assert len(result) == 4
        assert all(s.node_name == "new-node" for s in result)


class TestDynamicBinarySensorDiscovery:
    """Test dynamic binary sensor discovery via coordinator listener."""

    async def test_setup_stores_callback(
        self,
        hass: HomeAssistant,
        mock_config_entry,
        mock_client,
        mock_coordinator,
        setup_domain_data,
    ):
        """Test setup stores the add_entities callback for dynamic discovery."""
        mock_add_entities = MagicMock()
        await async_setup_entry(hass, mock_config_entry, mock_add_entities)

        entry_data = hass.data[DOMAIN][mock_config_entry.entry_id]
        assert entry_data["binary_sensor_add_entities"] is mock_add_entities
        assert isinstance(entry_data["binary_sensor_pending_unique_ids"], set)

    async def test_setup_registers_coordinator_listener(
        self,
        hass: HomeAssistant,
        mock_config_entry,
        mock_client,
        mock_coordinator,
        setup_domain_data,
    ):
        """Test setup registers a listener on the coordinator for dynamic discovery."""
        mock_add_entities = MagicMock()
        await async_setup_entry(hass, mock_config_entry, mock_add_entities)

        # The coordinator should have had async_add_listener called
        # (once for each condition sensor via async_added_to_hass, plus once for discovery)
        assert mock_coordinator.async_add_listener.called

    async def test_discover_adds_new_node_sensors(
        self,
        hass: HomeAssistant,
        mock_config_entry,
        mock_coordinator,
        setup_domain_data,
    ):
        """Test discovery adds binary sensors for a newly appeared node."""
        mock_add_entities = MagicMock()
        entry_data = hass.data[DOMAIN][mock_config_entry.entry_id]
        entry_data["binary_sensor_add_entities"] = mock_add_entities
        entry_data["binary_sensor_pending_unique_ids"] = set()

        # Simulate new node appearing
        mock_coordinator.data = {
            "nodes": {
                "new-node": {
                    "memory_pressure": False,
                    "disk_pressure": False,
                    "pid_pressure": False,
                    "network_unavailable": False,
                }
            }
        }

        await _async_discover_and_add_new_binary_sensors(
            hass, mock_config_entry, mock_coordinator
        )

        mock_add_entities.assert_called_once()
        added = mock_add_entities.call_args[0][0]
        assert len(added) == 4
        assert all(isinstance(s, KubernetesNodeConditionBinarySensor) for s in added)

    async def test_discover_skips_already_registered_nodes(
        self,
        hass: HomeAssistant,
        mock_config_entry,
        mock_coordinator,
        setup_domain_data,
    ):
        """Test discovery does not re-add nodes already in the entity registry."""
        mock_add_entities = MagicMock()
        entry_data = hass.data[DOMAIN][mock_config_entry.entry_id]
        entry_data["binary_sensor_add_entities"] = mock_add_entities
        entry_data["binary_sensor_pending_unique_ids"] = set()

        # Register existing entities in the registry
        registry = er.async_get(hass)
        for condition in [
            "memory_pressure",
            "disk_pressure",
            "pid_pressure",
            "network_unavailable",
        ]:
            registry.async_get_or_create(
                "binary_sensor",
                DOMAIN,
                f"{mock_config_entry.entry_id}_node_existing-node_{condition}",
                config_entry=mock_config_entry,
            )

        mock_coordinator.data = {"nodes": {"existing-node": {"memory_pressure": False}}}

        await _async_discover_and_add_new_binary_sensors(
            hass, mock_config_entry, mock_coordinator
        )

        # No new entities should be added
        mock_add_entities.assert_not_called()

    async def test_discover_respects_pending_ids(
        self,
        hass: HomeAssistant,
        mock_config_entry,
        mock_coordinator,
        setup_domain_data,
    ):
        """Test discovery does not re-add nodes in the pending set."""
        mock_add_entities = MagicMock()
        entry_data = hass.data[DOMAIN][mock_config_entry.entry_id]
        entry_data["binary_sensor_add_entities"] = mock_add_entities
        pending = {
            f"{mock_config_entry.entry_id}_node_pending-node_{c}"
            for c in [
                "memory_pressure",
                "disk_pressure",
                "pid_pressure",
                "network_unavailable",
            ]
        }
        entry_data["binary_sensor_pending_unique_ids"] = pending

        mock_coordinator.data = {"nodes": {"pending-node": {"memory_pressure": False}}}

        await _async_discover_and_add_new_binary_sensors(
            hass, mock_config_entry, mock_coordinator
        )

        mock_add_entities.assert_not_called()

    async def test_discover_handles_missing_callback(
        self,
        hass: HomeAssistant,
        mock_config_entry,
        mock_coordinator,
        setup_domain_data,
    ):
        """Test discovery handles missing add_entities callback gracefully."""
        # Remove the callback
        hass.data[DOMAIN][mock_config_entry.entry_id].pop(
            "binary_sensor_add_entities", None
        )

        mock_coordinator.data = {"nodes": {"node-1": {"memory_pressure": False}}}

        # Should not raise
        await _async_discover_and_add_new_binary_sensors(
            hass, mock_config_entry, mock_coordinator
        )
