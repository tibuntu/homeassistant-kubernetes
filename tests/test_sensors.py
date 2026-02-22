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
from custom_components.kubernetes.const import (
    ATTR_WORKLOAD_TYPE,
    DOMAIN,
    WORKLOAD_TYPE_POD,
)
from custom_components.kubernetes.sensor import (
    KubernetesCronJobsSensor,
    KubernetesDaemonSetSensor,
    KubernetesDaemonSetsSensor,
    KubernetesDeploymentsSensor,
    KubernetesNodeSensor,
    KubernetesNodesSensor,
    KubernetesPodSensor,
    KubernetesPodsSensor,
    KubernetesStatefulSetsSensor,
    KubernetesWorkloadMetricSensor,
    KubernetesWorkloadStatusSensor,
    _discover_new_daemonset_sensors,
    _discover_new_workload_metric_sensors,
    _discover_new_workload_status_sensors,
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
        "cluster_name": "test-cluster",
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
    client.get_daemonsets_count = AsyncMock(return_value=1)
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

    def test_sensor_device_info(self, mock_config_entry, mock_client, mock_coordinator):
        """Test sensor device info."""
        sensor = KubernetesPodsSensor(mock_coordinator, mock_client, mock_config_entry)
        device_info = sensor.device_info
        assert device_info["identifiers"] == {("kubernetes", "test_entry_id_cluster")}
        assert device_info["name"] == "test-cluster"

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

    def test_sensor_device_info(self, mock_config_entry, mock_client, mock_coordinator):
        """Test sensor device info."""
        sensor = KubernetesNodesSensor(mock_coordinator, mock_client, mock_config_entry)
        device_info = sensor.device_info
        assert device_info["identifiers"] == {("kubernetes", "test_entry_id_cluster")}
        assert device_info["name"] == "test-cluster"

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


class TestKubernetesDaemonSetsSensor:
    """Test Kubernetes daemonsets sensor."""

    def test_sensor_initialization(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test sensor initialization."""
        sensor = KubernetesDaemonSetsSensor(
            mock_coordinator, mock_client, mock_config_entry
        )

        assert sensor.name == "DaemonSets Count"
        assert sensor.unique_id == "test_entry_id_daemonsets_count"
        assert sensor.native_unit_of_measurement == "daemonsets"

    async def test_sensor_update_success(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test successful sensor update."""
        # Set up coordinator data
        mock_coordinator.data = {"daemonsets": {"daemonset1": {}}}

        sensor = KubernetesDaemonSetsSensor(
            mock_coordinator, mock_client, mock_config_entry
        )

        # The sensor should read from coordinator data
        assert sensor.native_value == 1

    async def test_sensor_update_failure(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test sensor update failure."""
        mock_client.get_daemonsets_count.side_effect = Exception("API Error")

        sensor = KubernetesDaemonSetsSensor(
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

        # Mock device registry
        mock_device_registry = MagicMock()
        mock_device_registry.async_get_device = MagicMock(return_value=None)
        mock_device_registry.async_get_or_create = MagicMock(return_value=MagicMock())

        mock_add_entities = AsyncMock()
        with patch(
            "custom_components.kubernetes.device.dr.async_get",
            return_value=mock_device_registry,
        ):
            await async_setup_entry(mock_hass, mock_config_entry, mock_add_entities)

        # Should add base sensors plus node sensors
        mock_add_entities.assert_called_once()
        sensors = mock_add_entities.call_args[0][0]
        # 6 base sensors (Pods, Nodes, Deployments, StatefulSets, DaemonSets, CronJobs) + number of node sensors from coordinator
        expected_count = 6 + len(mock_coordinator.get_all_nodes_data())
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

        # Mock device registry
        mock_device_registry = MagicMock()
        mock_device_registry.async_get_device = MagicMock(return_value=None)
        mock_device_registry.async_get_or_create = MagicMock(return_value=MagicMock())

        mock_add_entities = AsyncMock()
        with patch(
            "custom_components.kubernetes.device.dr.async_get",
            return_value=mock_device_registry,
        ):
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
        with pytest.raises(KeyError):
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

    def test_node_sensor_device_info(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test node sensor device info."""
        node_name = "worker-node-1"
        sensor = KubernetesNodeSensor(
            mock_coordinator, mock_client, mock_config_entry, node_name
        )
        device_info = sensor.device_info
        assert device_info["identifiers"] == {("kubernetes", "test_entry_id_cluster")}
        assert device_info["name"] == "test-cluster"

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
        assert attributes["memory_capacity_(GiB)"] == "16.0 GiB"
        assert attributes["memory_allocatable_(GiB)"] == "14.5 GiB"
        assert attributes["CPU"] == "4.0 vCPU"
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
            _async_discover_and_add_new_sensors,
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

        # Mock device registry
        mock_device_registry = MagicMock()
        mock_device_registry.async_get_device = MagicMock(return_value=None)
        mock_device_registry.async_get_or_create = MagicMock(return_value=MagicMock())

        with (
            patch(
                "custom_components.kubernetes.sensor.async_get_entity_registry",
                return_value=mock_entity_registry,
            ),
            patch(
                "custom_components.kubernetes.device.dr.async_get",
                return_value=mock_device_registry,
            ),
        ):
            await _async_discover_and_add_new_sensors(
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
            _async_discover_and_add_new_sensors,
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
            await _async_discover_and_add_new_sensors(
                mock_hass, mock_config_entry, mock_coordinator, mock_client
            )

    async def test_discover_new_node_sensors_existing_entities(
        self, mock_hass, mock_config_entry, mock_coordinator, mock_client
    ):
        """Test discovery with existing node sensors."""
        from custom_components.kubernetes.sensor import (
            _async_discover_and_add_new_sensors,
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

        # Mock device registry
        mock_device_registry = MagicMock()
        mock_device_registry.async_get_device = MagicMock(return_value=None)
        mock_device_registry.async_get_or_create = MagicMock(return_value=MagicMock())

        with (
            patch(
                "custom_components.kubernetes.sensor.async_get_entity_registry",
                return_value=mock_entity_registry,
            ),
            patch(
                "custom_components.kubernetes.device.dr.async_get",
                return_value=mock_device_registry,
            ),
        ):
            await _async_discover_and_add_new_sensors(
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
            _async_discover_and_add_new_sensors,
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
            await _async_discover_and_add_new_sensors(
                mock_hass, mock_config_entry, mock_coordinator, mock_client
            )


class TestKubernetesPodSensor:
    """Test cases for KubernetesPodSensor."""

    def test_pod_sensor_initialization(
        self, mock_hass, mock_config_entry, mock_coordinator, mock_client
    ):
        """Test pod sensor initialization."""
        namespace = "default"
        pod_name = "test-pod"

        sensor = KubernetesPodSensor(
            mock_coordinator, mock_client, mock_config_entry, namespace, pod_name
        )

        assert sensor.namespace == namespace
        assert sensor.pod_name == pod_name
        assert sensor.name == pod_name
        assert (
            sensor.unique_id
            == f"{mock_config_entry.entry_id}_pod_{namespace}_{pod_name}"
        )
        assert sensor.icon == "mdi:kubernetes"
        assert sensor.state_class is None

    def test_pod_sensor_native_value_with_data(
        self, mock_hass, mock_config_entry, mock_coordinator, mock_client
    ):
        """Test pod sensor native value when data is available."""
        namespace = "default"
        pod_name = "test-pod"

        # Mock coordinator data
        mock_coordinator.get_pod_data.return_value = {
            "name": pod_name,
            "namespace": namespace,
            "phase": "Running",
            "ready_containers": 2,
            "total_containers": 2,
            "restart_count": 0,
            "node_name": "worker-node-1",
            "pod_ip": "10.244.1.5",
            "creation_timestamp": "2023-01-01T00:00:00Z",
            "owner_kind": "ReplicaSet",
            "owner_name": "test-app-7d4b8c9f6b",
            "uid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            "labels": {"app": "test-app", "version": "v1.0"},
        }

        sensor = KubernetesPodSensor(
            mock_coordinator, mock_client, mock_config_entry, namespace, pod_name
        )

        assert sensor.native_value == "Running"

    def test_pod_sensor_native_value_no_data(
        self, mock_hass, mock_config_entry, mock_coordinator, mock_client
    ):
        """Test pod sensor native value when no data is available."""
        namespace = "default"
        pod_name = "test-pod"

        # Mock coordinator to return no data
        mock_coordinator.get_pod_data.return_value = None

        sensor = KubernetesPodSensor(
            mock_coordinator, mock_client, mock_config_entry, namespace, pod_name
        )

        assert sensor.native_value == "Unknown"

    def test_pod_sensor_extra_state_attributes(
        self, mock_hass, mock_config_entry, mock_coordinator, mock_client
    ):
        """Test pod sensor extra state attributes."""
        namespace = "default"
        pod_name = "test-pod"

        # Mock coordinator data
        mock_coordinator.get_pod_data.return_value = {
            "name": pod_name,
            "namespace": namespace,
            "phase": "Running",
            "ready_containers": 2,
            "total_containers": 2,
            "restart_count": 0,
            "node_name": "worker-node-1",
            "pod_ip": "10.244.1.5",
            "creation_timestamp": "2023-01-01T00:00:00Z",
            "owner_kind": "ReplicaSet",
            "owner_name": "test-app-7d4b8c9f6b",
            "uid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            "labels": {"app": "test-app", "version": "v1.0"},
        }

        sensor = KubernetesPodSensor(
            mock_coordinator, mock_client, mock_config_entry, namespace, pod_name
        )

        attributes = sensor.extra_state_attributes

        assert attributes["namespace"] == namespace
        assert attributes["phase"] == "Running"
        assert attributes["ready_containers"] == 2
        assert attributes["total_containers"] == 2
        assert attributes["restart_count"] == 0
        assert attributes["node_name"] == "worker-node-1"
        assert attributes["pod_ip"] == "10.244.1.5"
        assert attributes["creation_timestamp"] == "2023-01-01T00:00:00Z"
        assert attributes["owner_kind"] == "ReplicaSet"
        assert attributes["owner_name"] == "test-app-7d4b8c9f6b"
        assert attributes[ATTR_WORKLOAD_TYPE] == WORKLOAD_TYPE_POD

    def test_pod_sensor_workload_type_always_present(
        self, mock_hass, mock_config_entry, mock_coordinator, mock_client
    ):
        """Test that workload_type is always present when pod data exists."""
        namespace = "default"
        pod_name = "test-pod"

        # Mock coordinator data with minimal fields
        mock_coordinator.get_pod_data.return_value = {
            "name": pod_name,
            "namespace": namespace,
            "phase": "Pending",
        }

        sensor = KubernetesPodSensor(
            mock_coordinator, mock_client, mock_config_entry, namespace, pod_name
        )

        attributes = sensor.extra_state_attributes

        # Verify workload_type is always present when data exists
        assert ATTR_WORKLOAD_TYPE in attributes
        assert attributes[ATTR_WORKLOAD_TYPE] == WORKLOAD_TYPE_POD

    def test_pod_sensor_extra_state_attributes_no_data(
        self, mock_hass, mock_config_entry, mock_coordinator, mock_client
    ):
        """Test pod sensor extra state attributes when no data is available."""
        namespace = "default"
        pod_name = "test-pod"

        # Mock coordinator to return no data
        mock_coordinator.get_pod_data.return_value = None

        sensor = KubernetesPodSensor(
            mock_coordinator, mock_client, mock_config_entry, namespace, pod_name
        )

        attributes = sensor.extra_state_attributes
        assert attributes == {}

    def test_pod_sensor_phase_attribute_for_filtering(
        self, mock_hass, mock_config_entry, mock_coordinator, mock_client
    ):
        """Test pod sensor phase attribute for auto-entities filtering."""
        namespace = "default"
        pod_name = "failed-pod"

        # Test with Failed phase
        mock_coordinator.get_pod_data.return_value = {
            "name": pod_name,
            "namespace": namespace,
            "phase": "Failed",
            "ready_containers": 0,
            "total_containers": 1,
        }

        sensor = KubernetesPodSensor(
            mock_coordinator, mock_client, mock_config_entry, namespace, pod_name
        )

        attributes = sensor.extra_state_attributes
        assert attributes["phase"] == "Failed"
        assert sensor.native_value == "Failed"

        # Test with Pending phase
        mock_coordinator.get_pod_data.return_value = {
            "name": pod_name,
            "namespace": namespace,
            "phase": "Pending",
        }

        attributes = sensor.extra_state_attributes
        assert attributes["phase"] == "Pending"
        assert sensor.native_value == "Pending"

        # Test with Succeeded phase
        mock_coordinator.get_pod_data.return_value = {
            "name": pod_name,
            "namespace": namespace,
            "phase": "Succeeded",
        }

        attributes = sensor.extra_state_attributes
        assert attributes["phase"] == "Succeeded"
        assert sensor.native_value == "Succeeded"

    async def test_pod_sensor_async_update(
        self, mock_hass, mock_config_entry, mock_coordinator, mock_client
    ):
        """Test pod sensor async update."""
        namespace = "default"
        pod_name = "test-pod"

        sensor = KubernetesPodSensor(
            mock_coordinator, mock_client, mock_config_entry, namespace, pod_name
        )

        # Mock the parent class async_update method
        with patch.object(
            sensor.__class__.__bases__[0], "async_update"
        ) as mock_parent_update:
            await sensor.async_update()
            mock_parent_update.assert_called_once()

    def test_pod_sensor_device_info(
        self, mock_hass, mock_config_entry, mock_coordinator, mock_client
    ):
        """Test pod sensor device info."""
        namespace = "default"
        pod_name = "test-pod"
        sensor = KubernetesPodSensor(
            mock_coordinator, mock_client, mock_config_entry, namespace, pod_name
        )
        device_info = sensor.device_info
        assert device_info["identifiers"] == {
            ("kubernetes", "test_entry_id_namespace_default")
        }
        assert device_info["name"] == "test-cluster: default"


class TestKubernetesWorkloadMetricSensor:
    """Test CPU/memory metric sensors for deployments and statefulsets."""

    def test_cpu_sensor_initialization(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test CPU metric sensor initialization for a deployment."""
        sensor = KubernetesWorkloadMetricSensor(
            mock_coordinator,
            mock_client,
            mock_config_entry,
            workload_name="my-app",
            namespace="default",
            workload_type="deployment",
            metric="cpu",
        )

        assert sensor.name == "my-app CPU Usage"
        assert sensor.unique_id == "test_entry_id_my-app_deployment_cpu"
        assert sensor.native_unit_of_measurement == "m"
        assert sensor.icon == "mdi:cpu-64-bit"
        assert sensor.state_class == SensorStateClass.MEASUREMENT

    def test_memory_sensor_initialization(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test memory metric sensor initialization for a statefulset."""
        sensor = KubernetesWorkloadMetricSensor(
            mock_coordinator,
            mock_client,
            mock_config_entry,
            workload_name="my-db",
            namespace="production",
            workload_type="statefulset",
            metric="memory",
        )

        assert sensor.name == "my-db Memory Usage"
        assert sensor.unique_id == "test_entry_id_my-db_statefulset_memory"
        assert sensor.native_unit_of_measurement == "MiB"
        assert sensor.icon == "mdi:memory"

    def test_unique_ids_are_distinct(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test that CPU, memory, deployment, and statefulset sensors have distinct IDs."""
        dep_cpu = KubernetesWorkloadMetricSensor(
            mock_coordinator,
            mock_client,
            mock_config_entry,
            "my-app",
            "default",
            "deployment",
            "cpu",
        )
        dep_mem = KubernetesWorkloadMetricSensor(
            mock_coordinator,
            mock_client,
            mock_config_entry,
            "my-app",
            "default",
            "deployment",
            "memory",
        )
        sts_cpu = KubernetesWorkloadMetricSensor(
            mock_coordinator,
            mock_client,
            mock_config_entry,
            "my-app",
            "default",
            "statefulset",
            "cpu",
        )

        assert dep_cpu.unique_id != dep_mem.unique_id
        assert dep_cpu.unique_id != sts_cpu.unique_id
        assert dep_mem.unique_id != sts_cpu.unique_id

    def test_device_info_uses_namespace_device(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test that metric sensors are attached to their namespace device."""
        sensor = KubernetesWorkloadMetricSensor(
            mock_coordinator,
            mock_client,
            mock_config_entry,
            "my-app",
            "default",
            "deployment",
            "cpu",
        )
        device_info = sensor.device_info
        assert device_info["identifiers"] == {
            ("kubernetes", "test_entry_id_namespace_default")
        }
        assert device_info["name"] == "test-cluster: default"

    def test_native_value_cpu_with_data(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test CPU native value is read from coordinator data."""
        mock_coordinator.data = {
            "deployments": {
                "my-app": {
                    "name": "my-app",
                    "namespace": "default",
                    "cpu_usage": 142.5,
                    "memory_usage": 256.0,
                }
            }
        }
        sensor = KubernetesWorkloadMetricSensor(
            mock_coordinator,
            mock_client,
            mock_config_entry,
            "my-app",
            "default",
            "deployment",
            "cpu",
        )
        assert sensor.native_value == 142.5

    def test_native_value_memory_with_data(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test memory native value is read from coordinator data."""
        mock_coordinator.data = {
            "deployments": {
                "my-app": {
                    "name": "my-app",
                    "namespace": "default",
                    "cpu_usage": 142.5,
                    "memory_usage": 256.0,
                }
            }
        }
        sensor = KubernetesWorkloadMetricSensor(
            mock_coordinator,
            mock_client,
            mock_config_entry,
            "my-app",
            "default",
            "deployment",
            "memory",
        )
        assert sensor.native_value == 256.0

    def test_native_value_no_coordinator_data(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test native value returns 0.0 when coordinator data is None."""
        mock_coordinator.data = None
        sensor = KubernetesWorkloadMetricSensor(
            mock_coordinator,
            mock_client,
            mock_config_entry,
            "my-app",
            "default",
            "deployment",
            "cpu",
        )
        assert sensor.native_value == 0.0

    def test_native_value_workload_not_found(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test native value returns 0.0 when workload is absent from coordinator data."""
        mock_coordinator.data = {"deployments": {}}
        sensor = KubernetesWorkloadMetricSensor(
            mock_coordinator,
            mock_client,
            mock_config_entry,
            "missing-app",
            "default",
            "deployment",
            "cpu",
        )
        assert sensor.native_value == 0.0

    def test_native_value_metric_key_missing(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test native value returns 0.0 when metric key is absent from workload data."""
        mock_coordinator.data = {
            "deployments": {"my-app": {"name": "my-app", "namespace": "default"}}
        }
        cpu_sensor = KubernetesWorkloadMetricSensor(
            mock_coordinator,
            mock_client,
            mock_config_entry,
            "my-app",
            "default",
            "deployment",
            "cpu",
        )
        mem_sensor = KubernetesWorkloadMetricSensor(
            mock_coordinator,
            mock_client,
            mock_config_entry,
            "my-app",
            "default",
            "deployment",
            "memory",
        )
        assert cpu_sensor.native_value == 0.0
        assert mem_sensor.native_value == 0.0

    def test_native_value_rounds_to_two_decimals(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test that native value is rounded to 2 decimal places."""
        mock_coordinator.data = {
            "deployments": {
                "my-app": {
                    "name": "my-app",
                    "namespace": "default",
                    "cpu_usage": 142.5678,
                }
            }
        }
        sensor = KubernetesWorkloadMetricSensor(
            mock_coordinator,
            mock_client,
            mock_config_entry,
            "my-app",
            "default",
            "deployment",
            "cpu",
        )
        assert sensor.native_value == 142.57

    def test_statefulset_metric_sensor(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test metric sensor reads from the statefulsets key in coordinator data."""
        mock_coordinator.data = {
            "statefulsets": {
                "my-db": {
                    "name": "my-db",
                    "namespace": "production",
                    "cpu_usage": 55.0,
                    "memory_usage": 512.0,
                }
            }
        }
        cpu_sensor = KubernetesWorkloadMetricSensor(
            mock_coordinator,
            mock_client,
            mock_config_entry,
            "my-db",
            "production",
            "statefulset",
            "cpu",
        )
        mem_sensor = KubernetesWorkloadMetricSensor(
            mock_coordinator,
            mock_client,
            mock_config_entry,
            "my-db",
            "production",
            "statefulset",
            "memory",
        )
        assert cpu_sensor.native_value == 55.0
        assert mem_sensor.native_value == 512.0


class TestDiscoverWorkloadMetricSensors:
    """Tests for the _discover_new_workload_metric_sensors helper."""

    def test_discovers_cpu_and_memory_for_new_deployment(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test that both CPU and memory sensors are created for a new deployment."""
        mock_coordinator.data = {
            "deployments": {"my-app": {"name": "my-app", "namespace": "default"}},
            "statefulsets": {},
        }
        new_sensors = _discover_new_workload_metric_sensors(
            mock_coordinator, mock_client, mock_config_entry, set()
        )

        assert len(new_sensors) == 2
        unique_ids = {s.unique_id for s in new_sensors}
        assert "test_entry_id_my-app_deployment_cpu" in unique_ids
        assert "test_entry_id_my-app_deployment_memory" in unique_ids

    def test_skips_already_existing_sensor(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test that an already-registered sensor unique ID is not duplicated."""
        mock_coordinator.data = {
            "deployments": {"my-app": {"name": "my-app", "namespace": "default"}},
            "statefulsets": {},
        }
        existing_ids = {"test_entry_id_my-app_deployment_cpu"}
        new_sensors = _discover_new_workload_metric_sensors(
            mock_coordinator, mock_client, mock_config_entry, existing_ids
        )

        assert len(new_sensors) == 1
        assert new_sensors[0].unique_id == "test_entry_id_my-app_deployment_memory"

    def test_discovers_sensors_for_statefulsets(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test that sensors are discovered for statefulsets."""
        mock_coordinator.data = {
            "deployments": {},
            "statefulsets": {"my-db": {"name": "my-db", "namespace": "production"}},
        }
        new_sensors = _discover_new_workload_metric_sensors(
            mock_coordinator, mock_client, mock_config_entry, set()
        )

        assert len(new_sensors) == 2
        unique_ids = {s.unique_id for s in new_sensors}
        assert "test_entry_id_my-db_statefulset_cpu" in unique_ids
        assert "test_entry_id_my-db_statefulset_memory" in unique_ids

    def test_discovers_sensors_for_multiple_workloads(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test discovery across multiple deployments and statefulsets."""
        mock_coordinator.data = {
            "deployments": {
                "app-a": {"name": "app-a", "namespace": "default"},
                "app-b": {"name": "app-b", "namespace": "default"},
            },
            "statefulsets": {
                "db-a": {"name": "db-a", "namespace": "default"},
            },
        }
        new_sensors = _discover_new_workload_metric_sensors(
            mock_coordinator, mock_client, mock_config_entry, set()
        )

        # 2 deployments × 2 metrics + 1 statefulset × 2 metrics = 6
        assert len(new_sensors) == 6

    def test_returns_empty_when_no_coordinator_data(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test that an empty list is returned when coordinator has no data."""
        mock_coordinator.data = None
        new_sensors = _discover_new_workload_metric_sensors(
            mock_coordinator, mock_client, mock_config_entry, set()
        )
        assert new_sensors == []

    def test_returns_empty_when_all_sensors_exist(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test that nothing is returned when all sensors are already registered."""
        mock_coordinator.data = {
            "deployments": {"my-app": {"name": "my-app", "namespace": "default"}},
            "statefulsets": {},
        }
        existing_ids = {
            "test_entry_id_my-app_deployment_cpu",
            "test_entry_id_my-app_deployment_memory",
        }
        new_sensors = _discover_new_workload_metric_sensors(
            mock_coordinator, mock_client, mock_config_entry, existing_ids
        )
        assert new_sensors == []


class TestKubernetesDaemonSetSensor:
    """Test individual DaemonSet status sensor."""

    def test_sensor_initialization(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test sensor initialization."""
        sensor = KubernetesDaemonSetSensor(
            mock_coordinator, mock_client, mock_config_entry, "fluentd", "kube-system"
        )

        assert sensor.name == "fluentd"
        assert sensor.unique_id == "test_entry_id_daemonset_fluentd"
        assert sensor.native_unit_of_measurement is None
        assert sensor.icon == "mdi:layers"
        assert sensor.state_class is None

    def test_device_info_uses_namespace_device(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test that the sensor belongs to its namespace device."""
        sensor = KubernetesDaemonSetSensor(
            mock_coordinator, mock_client, mock_config_entry, "fluentd", "kube-system"
        )
        device_info = sensor.device_info
        assert device_info["identifiers"] == {
            ("kubernetes", "test_entry_id_namespace_kube-system")
        }
        assert device_info["name"] == "test-cluster: kube-system"

    def test_native_value_ready(self, mock_config_entry, mock_client, mock_coordinator):
        """Test native value is 'Ready' when all desired pods are running."""
        mock_coordinator.data = {
            "daemonsets": {
                "fluentd": {
                    "name": "fluentd",
                    "namespace": "kube-system",
                    "desired_number_scheduled": 3,
                    "current_number_scheduled": 3,
                    "number_ready": 3,
                    "number_available": 3,
                }
            }
        }
        sensor = KubernetesDaemonSetSensor(
            mock_coordinator, mock_client, mock_config_entry, "fluentd", "kube-system"
        )
        assert sensor.native_value == "Ready"

    def test_native_value_degraded(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test native value is 'Degraded' when only some pods are ready."""
        mock_coordinator.data = {
            "daemonsets": {
                "fluentd": {
                    "name": "fluentd",
                    "namespace": "kube-system",
                    "desired_number_scheduled": 3,
                    "current_number_scheduled": 3,
                    "number_ready": 1,
                    "number_available": 1,
                }
            }
        }
        sensor = KubernetesDaemonSetSensor(
            mock_coordinator, mock_client, mock_config_entry, "fluentd", "kube-system"
        )
        assert sensor.native_value == "Degraded"

    def test_native_value_not_ready(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test native value is 'Not Ready' when no pods are ready."""
        mock_coordinator.data = {
            "daemonsets": {
                "fluentd": {
                    "name": "fluentd",
                    "namespace": "kube-system",
                    "desired_number_scheduled": 3,
                    "current_number_scheduled": 0,
                    "number_ready": 0,
                    "number_available": 0,
                }
            }
        }
        sensor = KubernetesDaemonSetSensor(
            mock_coordinator, mock_client, mock_config_entry, "fluentd", "kube-system"
        )
        assert sensor.native_value == "Not Ready"

    def test_native_value_unknown_no_coordinator_data(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test native value is 'Unknown' when coordinator has no data."""
        mock_coordinator.data = None
        sensor = KubernetesDaemonSetSensor(
            mock_coordinator, mock_client, mock_config_entry, "fluentd", "kube-system"
        )
        assert sensor.native_value == "Unknown"

    def test_native_value_unknown_daemonset_missing(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test native value is 'Unknown' when DaemonSet is absent from data."""
        mock_coordinator.data = {"daemonsets": {}}
        sensor = KubernetesDaemonSetSensor(
            mock_coordinator, mock_client, mock_config_entry, "fluentd", "kube-system"
        )
        assert sensor.native_value == "Unknown"

    def test_native_value_unknown_zero_desired(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test native value is 'Unknown' when desired count is 0."""
        mock_coordinator.data = {
            "daemonsets": {
                "fluentd": {
                    "name": "fluentd",
                    "namespace": "kube-system",
                    "desired_number_scheduled": 0,
                    "number_ready": 0,
                }
            }
        }
        sensor = KubernetesDaemonSetSensor(
            mock_coordinator, mock_client, mock_config_entry, "fluentd", "kube-system"
        )
        assert sensor.native_value == "Unknown"

    def test_extra_state_attributes(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test extra state attributes contain scheduling information."""
        mock_coordinator.data = {
            "daemonsets": {
                "fluentd": {
                    "name": "fluentd",
                    "namespace": "kube-system",
                    "desired_number_scheduled": 3,
                    "current_number_scheduled": 3,
                    "number_ready": 2,
                    "number_available": 2,
                }
            }
        }
        sensor = KubernetesDaemonSetSensor(
            mock_coordinator, mock_client, mock_config_entry, "fluentd", "kube-system"
        )
        attrs = sensor.extra_state_attributes

        assert attrs["namespace"] == "kube-system"
        assert attrs["desired"] == 3
        assert attrs["current"] == 3
        assert attrs["ready"] == 2
        assert attrs["available"] == 2

    def test_extra_state_attributes_no_data(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test extra state attributes return empty dict when no data."""
        mock_coordinator.data = None
        sensor = KubernetesDaemonSetSensor(
            mock_coordinator, mock_client, mock_config_entry, "fluentd", "kube-system"
        )
        assert sensor.extra_state_attributes == {}


class TestDiscoverDaemonSetSensors:
    """Tests for the _discover_new_daemonset_sensors helper."""

    def test_discovers_sensor_for_new_daemonset(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test that a sensor is created for a new DaemonSet."""
        mock_coordinator.data = {
            "daemonsets": {"fluentd": {"name": "fluentd", "namespace": "kube-system"}}
        }
        new_sensors = _discover_new_daemonset_sensors(
            mock_coordinator, mock_client, mock_config_entry, set()
        )

        assert len(new_sensors) == 1
        assert new_sensors[0].unique_id == "test_entry_id_daemonset_fluentd"
        assert new_sensors[0].daemonset_name == "fluentd"
        assert new_sensors[0].namespace == "kube-system"

    def test_skips_already_existing_sensor(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test that an already-registered sensor is not duplicated."""
        mock_coordinator.data = {
            "daemonsets": {
                "fluentd": {"name": "fluentd", "namespace": "kube-system"},
                "node-exporter": {"name": "node-exporter", "namespace": "monitoring"},
            }
        }
        existing_ids = {"test_entry_id_daemonset_fluentd"}
        new_sensors = _discover_new_daemonset_sensors(
            mock_coordinator, mock_client, mock_config_entry, existing_ids
        )

        assert len(new_sensors) == 1
        assert new_sensors[0].daemonset_name == "node-exporter"

    def test_discovers_multiple_daemonsets(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test discovery across multiple DaemonSets."""
        mock_coordinator.data = {
            "daemonsets": {
                "fluentd": {"name": "fluentd", "namespace": "kube-system"},
                "node-exporter": {"name": "node-exporter", "namespace": "monitoring"},
                "calico": {"name": "calico", "namespace": "kube-system"},
            }
        }
        new_sensors = _discover_new_daemonset_sensors(
            mock_coordinator, mock_client, mock_config_entry, set()
        )

        assert len(new_sensors) == 3
        names = {s.daemonset_name for s in new_sensors}
        assert names == {"fluentd", "node-exporter", "calico"}

    def test_returns_empty_when_no_coordinator_data(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test that an empty list is returned when coordinator has no data."""
        mock_coordinator.data = None
        new_sensors = _discover_new_daemonset_sensors(
            mock_coordinator, mock_client, mock_config_entry, set()
        )
        assert new_sensors == []

    def test_returns_empty_when_all_sensors_exist(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test that nothing is returned when all sensors are already registered."""
        mock_coordinator.data = {
            "daemonsets": {"fluentd": {"name": "fluentd", "namespace": "kube-system"}}
        }
        existing_ids = {"test_entry_id_daemonset_fluentd"}
        new_sensors = _discover_new_daemonset_sensors(
            mock_coordinator, mock_client, mock_config_entry, existing_ids
        )
        assert new_sensors == []


class TestKubernetesWorkloadStatusSensor:
    """Test readiness status sensors for deployments and statefulsets."""

    def test_deployment_sensor_initialization(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test sensor initialization for a deployment."""
        sensor = KubernetesWorkloadStatusSensor(
            mock_coordinator,
            mock_client,
            mock_config_entry,
            "my-app",
            "default",
            "deployment",
        )

        assert sensor.name == "my-app"
        assert sensor.unique_id == "test_entry_id_my-app_deployment_status"
        assert sensor.native_unit_of_measurement is None
        assert sensor.icon == "mdi:kubernetes"
        assert sensor.state_class is None

    def test_statefulset_sensor_unique_id(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test unique ID is distinct for statefulset vs deployment."""
        dep = KubernetesWorkloadStatusSensor(
            mock_coordinator,
            mock_client,
            mock_config_entry,
            "my-app",
            "default",
            "deployment",
        )
        sts = KubernetesWorkloadStatusSensor(
            mock_coordinator,
            mock_client,
            mock_config_entry,
            "my-app",
            "default",
            "statefulset",
        )
        assert dep.unique_id != sts.unique_id

    def test_device_info_uses_namespace_device(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test sensor is attached to its namespace device."""
        sensor = KubernetesWorkloadStatusSensor(
            mock_coordinator,
            mock_client,
            mock_config_entry,
            "my-app",
            "default",
            "deployment",
        )
        device_info = sensor.device_info
        assert device_info["identifiers"] == {
            ("kubernetes", "test_entry_id_namespace_default")
        }
        assert device_info["name"] == "test-cluster: default"

    def test_native_value_ready(self, mock_config_entry, mock_client, mock_coordinator):
        """Test native value is 'Ready' when all replicas are ready."""
        mock_coordinator.data = {
            "deployments": {
                "my-app": {
                    "namespace": "default",
                    "replicas": 3,
                    "ready_replicas": 3,
                    "available_replicas": 3,
                }
            }
        }
        sensor = KubernetesWorkloadStatusSensor(
            mock_coordinator,
            mock_client,
            mock_config_entry,
            "my-app",
            "default",
            "deployment",
        )
        assert sensor.native_value == "Ready"

    def test_native_value_degraded(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test native value is 'Degraded' when only some replicas are ready."""
        mock_coordinator.data = {
            "deployments": {
                "my-app": {
                    "namespace": "default",
                    "replicas": 3,
                    "ready_replicas": 1,
                    "available_replicas": 1,
                }
            }
        }
        sensor = KubernetesWorkloadStatusSensor(
            mock_coordinator,
            mock_client,
            mock_config_entry,
            "my-app",
            "default",
            "deployment",
        )
        assert sensor.native_value == "Degraded"

    def test_native_value_not_ready(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test native value is 'Not Ready' when no replicas are ready."""
        mock_coordinator.data = {
            "deployments": {
                "my-app": {
                    "namespace": "default",
                    "replicas": 3,
                    "ready_replicas": 0,
                    "available_replicas": 0,
                }
            }
        }
        sensor = KubernetesWorkloadStatusSensor(
            mock_coordinator,
            mock_client,
            mock_config_entry,
            "my-app",
            "default",
            "deployment",
        )
        assert sensor.native_value == "Not Ready"

    def test_native_value_scaled_down(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test native value is 'Scaled Down' when replicas is zero."""
        mock_coordinator.data = {
            "deployments": {
                "my-app": {
                    "namespace": "default",
                    "replicas": 0,
                    "ready_replicas": 0,
                    "available_replicas": 0,
                }
            }
        }
        sensor = KubernetesWorkloadStatusSensor(
            mock_coordinator,
            mock_client,
            mock_config_entry,
            "my-app",
            "default",
            "deployment",
        )
        assert sensor.native_value == "Scaled Down"

    def test_native_value_unknown_no_data(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test native value is 'Unknown' when coordinator has no data."""
        mock_coordinator.data = None
        sensor = KubernetesWorkloadStatusSensor(
            mock_coordinator,
            mock_client,
            mock_config_entry,
            "my-app",
            "default",
            "deployment",
        )
        assert sensor.native_value == "Unknown"

    def test_native_value_unknown_workload_missing(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test native value is 'Unknown' when workload is absent from data."""
        mock_coordinator.data = {"deployments": {}}
        sensor = KubernetesWorkloadStatusSensor(
            mock_coordinator,
            mock_client,
            mock_config_entry,
            "missing-app",
            "default",
            "deployment",
        )
        assert sensor.native_value == "Unknown"

    def test_extra_state_attributes(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test extra state attributes contain replica counts."""
        mock_coordinator.data = {
            "deployments": {
                "my-app": {
                    "namespace": "default",
                    "replicas": 3,
                    "ready_replicas": 2,
                    "available_replicas": 2,
                }
            }
        }
        sensor = KubernetesWorkloadStatusSensor(
            mock_coordinator,
            mock_client,
            mock_config_entry,
            "my-app",
            "default",
            "deployment",
        )
        attrs = sensor.extra_state_attributes

        assert attrs["namespace"] == "default"
        assert attrs["replicas"] == 3
        assert attrs["ready_replicas"] == 2
        assert attrs["available_replicas"] == 2

    def test_extra_state_attributes_no_data(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test extra state attributes return empty dict when no data."""
        mock_coordinator.data = None
        sensor = KubernetesWorkloadStatusSensor(
            mock_coordinator,
            mock_client,
            mock_config_entry,
            "my-app",
            "default",
            "deployment",
        )
        assert sensor.extra_state_attributes == {}

    def test_statefulset_reads_from_correct_key(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test that a statefulset sensor reads from the statefulsets key."""
        mock_coordinator.data = {
            "statefulsets": {
                "my-db": {
                    "namespace": "default",
                    "replicas": 1,
                    "ready_replicas": 1,
                    "available_replicas": 1,
                }
            }
        }
        sensor = KubernetesWorkloadStatusSensor(
            mock_coordinator,
            mock_client,
            mock_config_entry,
            "my-db",
            "default",
            "statefulset",
        )
        assert sensor.native_value == "Ready"


class TestDiscoverWorkloadStatusSensors:
    """Tests for the _discover_new_workload_status_sensors helper."""

    def test_discovers_sensor_for_new_deployment(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test that a status sensor is created for a new deployment."""
        mock_coordinator.data = {
            "deployments": {"my-app": {"name": "my-app", "namespace": "default"}},
            "statefulsets": {},
        }
        new_sensors = _discover_new_workload_status_sensors(
            mock_coordinator, mock_client, mock_config_entry, set()
        )

        assert len(new_sensors) == 1
        assert new_sensors[0].unique_id == "test_entry_id_my-app_deployment_status"

    def test_discovers_sensor_for_statefulset(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test that a status sensor is created for a statefulset."""
        mock_coordinator.data = {
            "deployments": {},
            "statefulsets": {"my-db": {"name": "my-db", "namespace": "production"}},
        }
        new_sensors = _discover_new_workload_status_sensors(
            mock_coordinator, mock_client, mock_config_entry, set()
        )

        assert len(new_sensors) == 1
        assert new_sensors[0].unique_id == "test_entry_id_my-db_statefulset_status"

    def test_skips_existing_sensor(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test that an already-registered sensor is not duplicated."""
        mock_coordinator.data = {
            "deployments": {"my-app": {"name": "my-app", "namespace": "default"}},
            "statefulsets": {},
        }
        existing_ids = {"test_entry_id_my-app_deployment_status"}
        new_sensors = _discover_new_workload_status_sensors(
            mock_coordinator, mock_client, mock_config_entry, existing_ids
        )
        assert new_sensors == []

    def test_discovers_across_multiple_workloads(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test discovery across multiple deployments and statefulsets."""
        mock_coordinator.data = {
            "deployments": {
                "app-a": {"name": "app-a", "namespace": "default"},
                "app-b": {"name": "app-b", "namespace": "default"},
            },
            "statefulsets": {
                "db-a": {"name": "db-a", "namespace": "default"},
            },
        }
        new_sensors = _discover_new_workload_status_sensors(
            mock_coordinator, mock_client, mock_config_entry, set()
        )
        assert len(new_sensors) == 3

    def test_returns_empty_when_no_coordinator_data(
        self, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test that an empty list is returned when coordinator has no data."""
        mock_coordinator.data = None
        new_sensors = _discover_new_workload_status_sensors(
            mock_coordinator, mock_client, mock_config_entry, set()
        )
        assert new_sensors == []
