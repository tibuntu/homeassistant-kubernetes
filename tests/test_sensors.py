"""Tests for the Kubernetes integration sensors."""

from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant

try:
    from homeassistant.components.sensor import SensorStateClass
except ImportError:
    # Fallback for older HomeAssistant versions
    from enum import Enum

    class SensorStateClass(Enum):
        MEASUREMENT = "measurement"
        TOTAL = "total"
        TOTAL_INCREASING = "total_increasing"


import pytest

from custom_components.kubernetes.binary_sensor import KubernetesClusterHealthSensor
from custom_components.kubernetes.const import DOMAIN
from custom_components.kubernetes.sensor import (
    KubernetesCronJobsSensor,
    KubernetesDeploymentsSensor,
    KubernetesNodeSensor,
    KubernetesNodesSensor,
    KubernetesPodsSensor,
    KubernetesStatefulSetsSensor,
)


@pytest.fixture
def mock_hass():
    """Mock Home Assistant instance."""
    return MagicMock(spec=HomeAssistant)


@pytest.fixture
def mock_config_entry():
    """Mock config entry."""
    entry = MagicMock(spec=ConfigEntry)
    entry.entry_id = "test_entry_id"
    entry.data = {
        CONF_NAME: "Test Cluster",
        "host": "test-cluster.example.com",
        "port": 6443,
        "api_token": "test-token",
        "namespace": "default",
        "verify_ssl": True,
    }
    return entry


@pytest.fixture
def mock_client():
    """Mock Kubernetes client."""
    client = MagicMock()
    client.get_pods_count = AsyncMock(return_value=5)
    client.get_nodes_count = AsyncMock(return_value=3)
    client.get_deployments_count = AsyncMock(return_value=2)
    client.get_statefulsets_count = AsyncMock(return_value=1)
    client.is_cluster_healthy = AsyncMock(return_value=True)
    return client


class TestKubernetesPodsSensor:
    """Test Kubernetes pods sensor."""

    def test_sensor_initialization(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test sensor initialization."""
        sensor = KubernetesPodsSensor(mock_coordinator, mock_client, mock_config_entry)

        assert sensor.name == "Pods Count"
        assert sensor.unique_id == "test_entry_id_pods_count"
        assert sensor.native_unit_of_measurement == "pods"

    async def test_sensor_update_success(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test successful sensor update."""
        # Set up coordinator data
        mock_coordinator.data = {"pods_count": 5}

        sensor = KubernetesPodsSensor(mock_coordinator, mock_client, mock_config_entry)

        # The sensor should read from coordinator data
        assert sensor.native_value == 5

    async def test_sensor_update_failure(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test sensor update failure."""
        mock_client.get_pods_count.side_effect = Exception("API Error")

        sensor = KubernetesPodsSensor(mock_coordinator, mock_client, mock_config_entry)

        # Should handle exception gracefully
        await sensor.async_update()

        # Value should be 0 on error
        assert sensor.native_value == 0


class TestKubernetesNodesSensor:
    """Test Kubernetes nodes sensor."""

    def test_sensor_initialization(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test sensor initialization."""
        sensor = KubernetesNodesSensor(mock_coordinator, mock_client, mock_config_entry)

        assert sensor.name == "Nodes Count"
        assert sensor.unique_id == "test_entry_id_nodes_count"
        assert sensor.native_unit_of_measurement == "nodes"

    async def test_sensor_update_success(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test successful sensor update."""
        # Set up coordinator data
        mock_coordinator.data = {"nodes_count": 3}

        sensor = KubernetesNodesSensor(mock_coordinator, mock_client, mock_config_entry)

        # The sensor should read from coordinator data
        assert sensor.native_value == 3

    async def test_sensor_update_failure(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test sensor update failure."""
        mock_client.get_nodes_count.side_effect = Exception("API Error")

        sensor = KubernetesNodesSensor(mock_coordinator, mock_client, mock_config_entry)

        # Should handle exception gracefully
        await sensor.async_update()

        # Value should be 0 on error
        assert sensor.native_value == 0


class TestKubernetesDeploymentsSensor:
    """Test Kubernetes deployments sensor."""

    def test_sensor_initialization(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test sensor initialization."""
        sensor = KubernetesDeploymentsSensor(
            mock_coordinator, mock_client, mock_config_entry
        )

        assert sensor.name == "Deployments Count"
        assert sensor.unique_id == "test_entry_id_deployments_count"
        assert sensor.native_unit_of_measurement == "deployments"

    async def test_sensor_update_success(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test successful sensor update."""
        # Set up coordinator data
        mock_coordinator.data = {"deployments": {"deployment1": {}, "deployment2": {}}}

        sensor = KubernetesDeploymentsSensor(
            mock_coordinator, mock_client, mock_config_entry
        )

        # The sensor should read from coordinator data
        assert sensor.native_value == 2

    async def test_sensor_update_failure(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test sensor update failure."""
        mock_client.get_deployments_count.side_effect = Exception("API Error")

        sensor = KubernetesDeploymentsSensor(
            mock_coordinator, mock_client, mock_config_entry
        )

        # Should handle exception gracefully
        await sensor.async_update()

        # Value should be 0 on error
        assert sensor.native_value == 0


class TestKubernetesStatefulSetsSensor:
    """Test Kubernetes statefulsets sensor."""

    def test_sensor_initialization(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test sensor initialization."""
        sensor = KubernetesStatefulSetsSensor(
            mock_coordinator, mock_client, mock_config_entry
        )

        assert sensor.name == "StatefulSets Count"
        assert sensor.unique_id == "test_entry_id_statefulsets_count"
        assert sensor.native_unit_of_measurement == "statefulsets"

    async def test_sensor_update_success(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test successful sensor update."""
        # Set up coordinator data
        mock_coordinator.data = {"statefulsets": {"statefulset1": {}}}

        sensor = KubernetesStatefulSetsSensor(
            mock_coordinator, mock_client, mock_config_entry
        )

        # The sensor should read from coordinator data
        assert sensor.native_value == 1

    async def test_sensor_update_failure(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test sensor update failure."""
        mock_client.get_statefulsets_count.side_effect = Exception("API Error")

        sensor = KubernetesStatefulSetsSensor(
            mock_coordinator, mock_client, mock_config_entry
        )

        # Should handle exception gracefully
        await sensor.async_update()

        # Value should be 0 on error
        assert sensor.native_value == 0


class TestKubernetesClusterHealthSensor:
    """Test Kubernetes cluster health binary sensor."""

    def test_binary_sensor_initialization(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test binary sensor initialization."""
        sensor = KubernetesClusterHealthSensor(mock_client, mock_config_entry)

        assert sensor.name == "Cluster Health"
        assert sensor.unique_id == "test_entry_id_cluster_health"
        assert sensor.device_class == "connectivity"

    async def test_binary_sensor_update_healthy(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test binary sensor update when cluster is healthy."""
        sensor = KubernetesClusterHealthSensor(mock_client, mock_config_entry)

        await sensor.async_update()

        assert sensor.is_on is True
        mock_client.is_cluster_healthy.assert_called_once()

    async def test_binary_sensor_update_unhealthy(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test binary sensor update when cluster is unhealthy."""
        mock_client.is_cluster_healthy.return_value = False

        sensor = KubernetesClusterHealthSensor(mock_client, mock_config_entry)

        await sensor.async_update()

        assert sensor.is_on is False
        mock_client.is_cluster_healthy.assert_called_once()

    async def test_binary_sensor_update_failure(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test binary sensor update failure."""
        mock_client.is_cluster_healthy.side_effect = Exception("API Error")

        sensor = KubernetesClusterHealthSensor(mock_client, mock_config_entry)

        # Should handle exception gracefully
        await sensor.async_update()

        # Value should be False on error
        assert sensor.is_on is False


class TestSensorSetup:
    """Test sensor setup functions."""

    async def test_async_setup_entry_sensor_success(
        self, mock_hass, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test successful sensor setup."""
        mock_hass.data = {
            "kubernetes": {
                mock_config_entry.entry_id: {
                    "client": mock_client,
                    "coordinator": mock_coordinator,
                }
            }
        }

        from custom_components.kubernetes.sensor import async_setup_entry

        mock_add_entities = AsyncMock()
        await async_setup_entry(mock_hass, mock_config_entry, mock_add_entities)

        # Should add base sensors plus node sensors
        mock_add_entities.assert_called_once()
        sensors = mock_add_entities.call_args[0][0]
        # 5 base sensors + number of node sensors from coordinator
        expected_count = 5 + len(mock_coordinator.get_all_nodes_data())
        assert len(sensors) == expected_count

    async def test_async_setup_entry_binary_sensor_success(
        self, mock_hass, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test successful binary sensor setup."""
        mock_hass.data = {
            "kubernetes": {
                mock_config_entry.entry_id: {
                    "client": mock_client,
                    "coordinator": mock_coordinator,
                }
            }
        }

        from custom_components.kubernetes.binary_sensor import async_setup_entry

        mock_add_entities = AsyncMock()
        await async_setup_entry(mock_hass, mock_config_entry, mock_add_entities)

        # Should add 1 binary sensor
        mock_add_entities.assert_called_once()
        sensors = mock_add_entities.call_args[0][0]
        assert len(sensors) == 1

    async def test_async_setup_entry_sensor_failure(self, mock_hass, mock_config_entry):
        """Test sensor setup failure."""
        mock_hass.data = {}

        from custom_components.kubernetes.sensor import async_setup_entry

        mock_add_entities = AsyncMock()
        with pytest.raises(Exception):
            await async_setup_entry(mock_hass, mock_config_entry, mock_add_entities)

        mock_add_entities.assert_not_called()

    async def test_sensor_setup_exception_handling(self, mock_hass, mock_config_entry):
        """Test sensor setup exception handling."""
        from custom_components.kubernetes.const import DOMAIN
        from custom_components.kubernetes.sensor import async_setup_entry

        # Set up hass.data to cause an exception
        mock_hass.data = {DOMAIN: {}}

        # Mock async_add_entities
        mock_add_entities = MagicMock()

        # This should raise an exception due to missing coordinator
        with pytest.raises(KeyError):
            await async_setup_entry(mock_hass, mock_config_entry, mock_add_entities)

    async def test_sensor_async_added_to_hass(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test sensor async_added_to_hass method."""
        from custom_components.kubernetes.sensor import KubernetesPodsSensor

        sensor = KubernetesPodsSensor(mock_coordinator, mock_client, mock_config_entry)

        # Mock the coordinator's async_add_listener method
        mock_coordinator.async_add_listener = MagicMock(return_value=MagicMock())

        # Mock the async_on_remove method
        sensor.async_on_remove = MagicMock()

        # Call async_added_to_hass
        await sensor.async_added_to_hass()

        # Verify coordinator listener was added
        mock_coordinator.async_add_listener.assert_called_once()

    def test_sensor_handle_coordinator_update(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test sensor coordinator update handler."""
        from custom_components.kubernetes.sensor import KubernetesPodsSensor

        sensor = KubernetesPodsSensor(mock_coordinator, mock_client, mock_config_entry)

        # Mock async_write_ha_state
        sensor.async_write_ha_state = MagicMock()

        # Call the coordinator update handler
        sensor._handle_coordinator_update()

        # Verify state was written
        sensor.async_write_ha_state.assert_called_once()

    def test_sensor_native_value_with_missing_data(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test sensor native value when coordinator data is missing."""
        from custom_components.kubernetes.sensor import KubernetesPodsSensor

        # Set coordinator data to None
        mock_coordinator.data = None

        sensor = KubernetesPodsSensor(mock_coordinator, mock_client, mock_config_entry)

        # Should return 0 when no data
        assert sensor.native_value == 0

    def test_sensor_native_value_with_missing_key(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test sensor native value when specific key is missing from data."""
        from custom_components.kubernetes.sensor import KubernetesPodsSensor

        # Set coordinator data without pods_count key
        mock_coordinator.data = {"deployments": {}, "statefulsets": {}}

        sensor = KubernetesPodsSensor(mock_coordinator, mock_client, mock_config_entry)

        # Should return 0 when key is missing
        assert sensor.native_value == 0


class TestSensorProperties:
    """Test sensor properties."""

    def test_sensor_has_entity_name(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test that sensors have entity name."""
        pods_sensor = KubernetesPodsSensor(
            mock_coordinator, mock_client, mock_config_entry
        )
        nodes_sensor = KubernetesNodesSensor(
            mock_coordinator, mock_client, mock_config_entry
        )
        deployments_sensor = KubernetesDeploymentsSensor(
            mock_coordinator, mock_client, mock_config_entry
        )
        statefulsets_sensor = KubernetesStatefulSetsSensor(
            mock_coordinator, mock_client, mock_config_entry
        )

        assert pods_sensor.has_entity_name is True
        assert nodes_sensor.has_entity_name is True
        assert deployments_sensor.has_entity_name is True
        assert statefulsets_sensor.has_entity_name is True

    def test_sensor_state_class(self, mock_config_entry, mock_client, mock_coordinator):
        """Test that sensors have measurement state class."""
        pods_sensor = KubernetesPodsSensor(
            mock_coordinator, mock_client, mock_config_entry
        )
        nodes_sensor = KubernetesNodesSensor(
            mock_coordinator, mock_client, mock_config_entry
        )
        deployments_sensor = KubernetesDeploymentsSensor(
            mock_coordinator, mock_client, mock_config_entry
        )
        statefulsets_sensor = KubernetesStatefulSetsSensor(
            mock_coordinator, mock_client, mock_config_entry
        )

        assert pods_sensor.state_class == SensorStateClass.MEASUREMENT
        assert nodes_sensor.state_class == SensorStateClass.MEASUREMENT
        assert deployments_sensor.state_class == SensorStateClass.MEASUREMENT
        assert statefulsets_sensor.state_class == SensorStateClass.MEASUREMENT

    def test_binary_sensor_has_entity_name(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test that binary sensors have entity name."""
        health_sensor = KubernetesClusterHealthSensor(mock_client, mock_config_entry)

        assert health_sensor.has_entity_name is True

    def test_sensor_unique_ids(self, mock_config_entry, mock_client, mock_coordinator):
        """Test that sensors have unique IDs."""
        pods_sensor = KubernetesPodsSensor(
            mock_coordinator, mock_client, mock_config_entry
        )
        nodes_sensor = KubernetesNodesSensor(
            mock_coordinator, mock_client, mock_config_entry
        )
        deployments_sensor = KubernetesDeploymentsSensor(
            mock_coordinator, mock_client, mock_config_entry
        )
        statefulsets_sensor = KubernetesStatefulSetsSensor(
            mock_coordinator, mock_client, mock_config_entry
        )
        health_sensor = KubernetesClusterHealthSensor(mock_client, mock_config_entry)

        ids = [
            pods_sensor.unique_id,
            nodes_sensor.unique_id,
            deployments_sensor.unique_id,
            statefulsets_sensor.unique_id,
            health_sensor.unique_id,
        ]

        # All IDs should be unique
        assert len(ids) == len(set(ids))

        # IDs should contain the entry_id
        for sensor_id in ids:
            assert mock_config_entry.entry_id in sensor_id


class TestCronJobsSensor:
    """Test CronJobs sensor."""

    def test_cronjobs_sensor_initialization(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test CronJobs sensor initialization."""
        sensor = KubernetesCronJobsSensor(
            mock_coordinator, mock_client, mock_config_entry
        )

        assert sensor.name == "CronJobs Count"
        assert sensor.unique_id == f"{mock_config_entry.entry_id}_cronjobs_count"
        assert sensor.native_unit_of_measurement == "cronjobs"
        assert sensor.has_entity_name is True
        assert sensor.state_class == SensorStateClass.MEASUREMENT

    def test_cronjobs_sensor_native_value_with_data(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test CronJobs sensor native value when coordinator has data."""
        # Mock coordinator data with CronJobs
        mock_coordinator.data = {
            "cronjobs": {
                "backup-job": {"name": "backup-job", "namespace": "default"},
                "cleanup-job": {"name": "cleanup-job", "namespace": "default"},
                "monitoring-job": {"name": "monitoring-job", "namespace": "default"},
            }
        }

        sensor = KubernetesCronJobsSensor(
            mock_coordinator, mock_client, mock_config_entry
        )

        assert sensor.native_value == 3

    def test_cronjobs_sensor_native_value_without_data(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test CronJobs sensor native value when coordinator has no data."""
        # Mock coordinator with no data
        mock_coordinator.data = None

        sensor = KubernetesCronJobsSensor(
            mock_coordinator, mock_client, mock_config_entry
        )

        assert sensor.native_value == 0

    def test_cronjobs_sensor_native_value_empty_cronjobs(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test CronJobs sensor native value when no CronJobs exist."""
        # Mock coordinator data with empty CronJobs
        mock_coordinator.data = {"cronjobs": {}}

        sensor = KubernetesCronJobsSensor(
            mock_coordinator, mock_client, mock_config_entry
        )

        assert sensor.native_value == 0

    def test_cronjobs_sensor_native_value_missing_cronjobs_key(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test CronJobs sensor native value when cronjobs key is missing."""
        # Mock coordinator data without cronjobs key
        mock_coordinator.data = {"deployments": {}, "statefulsets": {}}

        sensor = KubernetesCronJobsSensor(
            mock_coordinator, mock_client, mock_config_entry
        )

        assert sensor.native_value == 0

    async def test_cronjobs_sensor_async_update_success(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test CronJobs sensor async update when client call succeeds."""
        # Mock coordinator with no data
        mock_coordinator.data = None

        # Mock client method
        mock_client.get_cronjobs_count = AsyncMock(return_value=5)

        sensor = KubernetesCronJobsSensor(
            mock_coordinator, mock_client, mock_config_entry
        )

        await sensor.async_update()

        mock_client.get_cronjobs_count.assert_called_once()

    async def test_cronjobs_sensor_async_update_exception(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test CronJobs sensor async update when client call fails."""
        from custom_components.kubernetes.sensor import KubernetesCronJobsSensor

        # Mock coordinator with no data
        mock_coordinator.data = None

        # Mock client method to raise exception
        mock_client.get_cronjobs_count = AsyncMock(side_effect=Exception("API Error"))

        sensor = KubernetesCronJobsSensor(
            mock_coordinator, mock_client, mock_config_entry
        )

        await sensor.async_update()

        # Should handle exception gracefully and set value to 0
        assert sensor._attr_native_value == 0

    def test_cronjobs_sensor_available(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test CronJobs sensor availability."""
        from custom_components.kubernetes.sensor import KubernetesCronJobsSensor

        sensor = KubernetesCronJobsSensor(
            mock_coordinator, mock_client, mock_config_entry
        )

        # Test when coordinator is successful
        mock_coordinator.last_update_success = True
        assert sensor.available is True

        # Test when coordinator fails
        mock_coordinator.last_update_success = False
        assert sensor.available is False


class TestKubernetesNodeSensor:
    """Test Kubernetes individual node sensor."""

    def test_sensor_initialization(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test sensor initialization."""
        node_name = "worker-node-1"
        sensor = KubernetesNodeSensor(
            mock_coordinator, mock_client, mock_config_entry, node_name
        )

        assert sensor.name == node_name
        assert sensor.unique_id == f"test_entry_id_node_{node_name}"
        assert sensor.native_unit_of_measurement is None
        assert sensor._attr_icon == "mdi:server"

    async def test_sensor_value_with_data(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test sensor value with node data."""
        node_name = "worker-node-1"
        node_data = {
            "name": node_name,
            "status": "Ready",
            "internal_ip": "10.0.0.1",
            "external_ip": "203.0.113.1",
            "memory_capacity_gib": 16.0,
            "memory_allocatable_gib": 14.5,
            "cpu_cores": 4.0,
            "os_image": "Ubuntu 22.04",
            "kernel_version": "5.15.0-56-generic",
            "container_runtime": "containerd://1.6.6",
            "kubelet_version": "v1.25.4",
            "schedulable": True,
            "creation_timestamp": "2023-01-01T00:00:00Z",
        }

        # Set up coordinator data
        mock_coordinator.get_node_data = MagicMock(return_value=node_data)

        sensor = KubernetesNodeSensor(
            mock_coordinator, mock_client, mock_config_entry, node_name
        )

        # Test native value (status)
        assert sensor.native_value == "Ready"

        # Test extra state attributes
        attributes = sensor.extra_state_attributes
        assert attributes["internal_IP"] == "10.0.0.1"
        assert attributes["external_IP"] == "203.0.113.1"
        assert attributes["memory_capacity_GiB"] == "16.0 GiB"
        assert attributes["memory_allocatable_GiB"] == "14.5 GiB"
        assert attributes["CPU_cores"] == "4.0 Cores"
        assert attributes["OS_image"] == "Ubuntu 22.04"
        assert attributes["kernel_version"] == "5.15.0-56-generic"
        assert attributes["container_runtime"] == "containerd://1.6.6"
        assert attributes["kubelet_version"] == "v1.25.4"
        assert attributes["schedulable"] is True
        assert attributes["creation_timestamp"] == "2023-01-01T00:00:00Z"

    async def test_sensor_value_without_data(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test sensor value without node data."""
        node_name = "worker-node-1"

        # Set up coordinator to return None
        mock_coordinator.get_node_data = MagicMock(return_value=None)

        sensor = KubernetesNodeSensor(
            mock_coordinator, mock_client, mock_config_entry, node_name
        )

        # Test native value (status)
        assert sensor.native_value == "Unknown"

        # Test extra state attributes
        attributes = sensor.extra_state_attributes
        assert attributes == {}

    async def test_sensor_update_success(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test successful sensor update."""
        node_name = "worker-node-1"
        sensor = KubernetesNodeSensor(
            mock_coordinator, mock_client, mock_config_entry, node_name
        )

        # Mock the coordinator update
        mock_coordinator.async_request_refresh = AsyncMock()

        # Should complete without error
        await sensor.async_update()

        # Verify coordinator refresh was called
        mock_coordinator.async_request_refresh.assert_called_once()

    async def test_sensor_update_failure(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test sensor update failure."""
        node_name = "worker-node-1"
        sensor = KubernetesNodeSensor(
            mock_coordinator, mock_client, mock_config_entry, node_name
        )

        # Mock the coordinator to raise an exception
        mock_coordinator.async_request_refresh = AsyncMock(
            side_effect=Exception("Update failed")
        )

        # Should handle exception gracefully
        await sensor.async_update()


@pytest.mark.asyncio
class TestDynamicNodeSensorDiscovery:
    """Tests for dynamic node sensor discovery functionality."""

    @pytest.fixture
    def mock_hass(self):
        """Mock HomeAssistant instance."""
        hass = MagicMock()
        hass.data = {}
        return hass

    async def test_discover_new_node_sensors_success(
        self, mock_hass, mock_config_entry, mock_coordinator, mock_client
    ):
        """Test successful discovery of new node sensors."""
        from custom_components.kubernetes.sensor import (
            _async_discover_and_add_new_node_sensors,
        )

        # Set up hass.data with add_entities callback
        mock_hass.data[DOMAIN] = {
            mock_config_entry.entry_id: {
                "sensor_add_entities": MagicMock(),
            }
        }

        # Mock coordinator data with nodes
        mock_coordinator.data = {
            "nodes": {
                "node1": {"status": "Ready"},
                "node2": {"status": "Ready"},
            }
        }

        # Mock entity registry with no existing entities
        mock_entity_registry = MagicMock()
        mock_entity_registry.entities.get_entries_for_config_entry_id.return_value = []

        with patch(
            "custom_components.kubernetes.sensor.async_get_entity_registry",
            return_value=mock_entity_registry,
        ):
            await _async_discover_and_add_new_node_sensors(
                mock_hass, mock_config_entry, mock_coordinator, mock_client
            )

        # Verify add_entities was called with 2 new node sensors
        callback = mock_hass.data[DOMAIN][mock_config_entry.entry_id][
            "sensor_add_entities"
        ]
        callback.assert_called_once()

        # Check that 2 node sensors were created
        call_args = callback.call_args[0][0]  # Get the list of entities passed
        assert len(call_args) == 2
        assert all(hasattr(sensor, "node_name") for sensor in call_args)

    async def test_discover_new_node_sensors_no_callback(
        self, mock_hass, mock_config_entry, mock_coordinator, mock_client
    ):
        """Test discovery when no add_entities callback is available."""
        from custom_components.kubernetes.sensor import (
            _async_discover_and_add_new_node_sensors,
        )

        # Set up hass.data without callback
        mock_hass.data[DOMAIN] = {}

        # Mock entity registry
        mock_entity_registry = MagicMock()
        mock_entity_registry.entities.get_entries_for_config_entry_id.return_value = []

        with patch(
            "custom_components.kubernetes.sensor.async_get_entity_registry",
            return_value=mock_entity_registry,
        ):
            # Should not raise exception
            await _async_discover_and_add_new_node_sensors(
                mock_hass, mock_config_entry, mock_coordinator, mock_client
            )

    async def test_discover_new_node_sensors_existing_entities(
        self, mock_hass, mock_config_entry, mock_coordinator, mock_client
    ):
        """Test discovery with existing node sensors."""
        from custom_components.kubernetes.sensor import (
            _async_discover_and_add_new_node_sensors,
        )

        # Set up hass.data with add_entities callback
        mock_hass.data[DOMAIN] = {
            mock_config_entry.entry_id: {
                "sensor_add_entities": MagicMock(),
            }
        }

        # Mock coordinator data with nodes
        mock_coordinator.data = {
            "nodes": {
                "node1": {"status": "Ready"},
                "node2": {"status": "Ready"},
            }
        }

        # Mock entity registry with existing entities
        existing_entity = MagicMock()
        existing_entity.unique_id = f"{mock_config_entry.entry_id}_node_node1"
        mock_entity_registry = MagicMock()
        mock_entity_registry.entities.get_entries_for_config_entry_id.return_value = [
            existing_entity
        ]

        with patch(
            "custom_components.kubernetes.sensor.async_get_entity_registry",
            return_value=mock_entity_registry,
        ):
            await _async_discover_and_add_new_node_sensors(
                mock_hass, mock_config_entry, mock_coordinator, mock_client
            )

        # Verify add_entities was called with only 1 new node sensor (node2)
        callback = mock_hass.data[DOMAIN][mock_config_entry.entry_id][
            "sensor_add_entities"
        ]
        callback.assert_called_once()

        # Check that only 1 node sensor was created (for node2)
        call_args = callback.call_args[0][0]  # Get the list of entities passed
        assert len(call_args) == 1
        assert call_args[0].node_name == "node2"

    async def test_discover_new_node_sensors_exception(
        self, mock_hass, mock_config_entry, mock_coordinator, mock_client
    ):
        """Test discovery with exception handling."""
        from custom_components.kubernetes.sensor import (
            _async_discover_and_add_new_node_sensors,
        )

        # Set up hass.data with add_entities callback
        mock_hass.data[DOMAIN] = {
            mock_config_entry.entry_id: {
                "sensor_add_entities": MagicMock(),
            }
        }

        # Mock coordinator data
        mock_coordinator.data = {"nodes": {"node1": {"status": "Ready"}}}

        # Mock entity registry to raise exception
        with patch(
            "custom_components.kubernetes.sensor.async_get_entity_registry",
            side_effect=Exception("Registry error"),
        ):
            # Should not raise exception, but handle it gracefully
            await _async_discover_and_add_new_node_sensors(
                mock_hass, mock_config_entry, mock_coordinator, mock_client
            )
