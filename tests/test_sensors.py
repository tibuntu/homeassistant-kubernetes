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
from custom_components.kubernetes.sensor import (
    KubernetesDeploymentsSensor,
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

        # Should add 5 sensors (including CronJobs sensor)
        mock_add_entities.assert_called_once()
        sensors = mock_add_entities.call_args[0][0]
        assert len(sensors) == 5

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
        from custom_components.kubernetes.sensor import KubernetesCronJobsSensor

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
        from custom_components.kubernetes.sensor import KubernetesCronJobsSensor

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
        from custom_components.kubernetes.sensor import KubernetesCronJobsSensor

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
        from custom_components.kubernetes.sensor import KubernetesCronJobsSensor

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
        from custom_components.kubernetes.sensor import KubernetesCronJobsSensor

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
        from custom_components.kubernetes.sensor import KubernetesCronJobsSensor

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
