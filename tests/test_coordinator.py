"""Tests for the Kubernetes coordinator."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed
import pytest

from custom_components.kubernetes.const import (
    CONF_ENABLE_WATCH,
    DEFAULT_FALLBACK_POLL_INTERVAL,
    DEFAULT_SWITCH_UPDATE_INTERVAL,
)
from custom_components.kubernetes.coordinator import KubernetesDataCoordinator
from custom_components.kubernetes.kubernetes_client import ResourceVersionExpired


@pytest.fixture
def mock_hass():
    """Mock Home Assistant instance."""
    hass = MagicMock(spec=HomeAssistant)
    hass.data = {}
    hass.config = MagicMock()
    hass.config.config_dir = "/tmp"
    return hass


@pytest.fixture
def mock_config_entry():
    """Mock config entry."""
    entry = MagicMock(spec=ConfigEntry)
    entry.entry_id = "test-entry-id"
    entry.data = {
        CONF_NAME: "Test Cluster",
        "host": "test-cluster.example.com",
        "port": 6443,
        "api_token": "test-token",
        "cluster_name": "test-cluster",
        "namespace": "default",
        "verify_ssl": True,
    }
    entry.options = {}
    return entry


@pytest.fixture
def mock_client():
    """Mock Kubernetes client."""
    client = MagicMock()
    client.get_deployments = AsyncMock(return_value=[])
    client.get_statefulsets = AsyncMock(return_value=[])
    client.get_daemonsets = AsyncMock(return_value=[])
    client.get_cronjobs = AsyncMock(return_value=[])
    client.get_jobs = AsyncMock(return_value=[])
    client.get_deployments_count = AsyncMock(return_value=0)
    client.get_statefulsets_count = AsyncMock(return_value=0)
    client.get_daemonsets_count = AsyncMock(return_value=0)
    client.get_cronjobs_count = AsyncMock(return_value=0)
    client.get_jobs_count = AsyncMock(return_value=0)
    client.get_pods_count = AsyncMock(return_value=0)
    client.get_pods = AsyncMock(return_value=[])
    client.get_nodes_count = AsyncMock(return_value=0)
    client.get_nodes = AsyncMock(return_value=[])
    client._test_connection = AsyncMock(return_value=True)
    return client


@pytest.fixture
def coordinator(mock_hass, mock_config_entry, mock_client):
    """Create a coordinator instance."""
    with patch("homeassistant.helpers.frame.report_usage"):
        return KubernetesDataCoordinator(mock_hass, mock_config_entry, mock_client)


class TestKubernetesDataCoordinator:
    """Test Kubernetes data coordinator."""

    async def test_async_update_data_success(self, coordinator, mock_client):
        """Test successful data update."""
        # Mock deployment data
        mock_deployments = [
            {
                "name": "nginx-deployment",
                "namespace": "default",
                "replicas": 3,
                "available_replicas": 3,
                "ready_replicas": 3,
                "updated_replicas": 3,
            }
        ]
        mock_client.get_deployments.return_value = mock_deployments

        # Mock StatefulSet data
        mock_statefulsets = [
            {
                "name": "redis-statefulset",
                "namespace": "default",
                "replicas": 1,
                "ready_replicas": 1,
                "current_replicas": 1,
                "updated_replicas": 1,
            }
        ]
        mock_client.get_statefulsets.return_value = mock_statefulsets

        # Mock CronJob data
        mock_cronjobs = [
            {
                "name": "backup-job",
                "namespace": "default",
                "schedule": "0 2 * * *",
                "suspend": False,
                "active_jobs_count": 0,
                "last_schedule_time": None,
                "next_schedule_time": None,
            }
        ]
        mock_client.get_cronjobs.return_value = mock_cronjobs

        # Mock detailed nodes data
        mock_nodes = [
            {
                "name": "worker-node-1",
                "status": "Ready",
                "internal_ip": "10.0.0.1",
                "external_ip": "203.0.113.1",
                "memory_capacity_gb": 16.0,
                "memory_allocatable_gb": 14.5,
                "cpu_cores": 4.0,
                "os_image": "Ubuntu 22.04",
                "kernel_version": "5.15.0-56-generic",
                "container_runtime": "containerd://1.6.6",
                "kubelet_version": "v1.25.4",
                "schedulable": True,
                "creation_timestamp": "2023-01-01T00:00:00Z",
            }
        ]
        mock_client.get_nodes.return_value = mock_nodes

        # Mock count data
        mock_client.get_deployments_count.return_value = 1
        mock_client.get_statefulsets_count.return_value = 1
        mock_client.get_daemonsets_count.return_value = 1
        mock_client.get_cronjobs_count.return_value = 1

        # Mock device registry
        mock_device_registry = MagicMock()
        mock_device_registry.async_get_device = MagicMock(return_value=None)
        mock_device_registry.async_get_or_create = MagicMock(return_value=MagicMock())

        with (
            patch(
                "custom_components.kubernetes.device.dr.async_get",
                return_value=mock_device_registry,
            ),
            patch(
                "custom_components.kubernetes.device.dr.async_entries_for_config_entry",
                return_value=[],
            ),
        ):
            result = await coordinator._async_update_data()

        # Verify the result structure
        assert "deployments" in result
        assert "statefulsets" in result
        assert "cronjobs" in result
        assert "jobs" in result
        assert "nodes" in result
        assert "pods_count" in result
        assert "nodes_count" in result
        assert "last_update" in result

        # Verify deployment data
        assert "nginx-deployment" in result["deployments"]
        assert result["deployments"]["nginx-deployment"]["name"] == "nginx-deployment"
        assert result["deployments"]["nginx-deployment"]["namespace"] == "default"
        assert result["deployments"]["nginx-deployment"]["replicas"] == 3

        # Verify StatefulSet data
        assert "redis-statefulset" in result["statefulsets"]
        assert (
            result["statefulsets"]["redis-statefulset"]["name"] == "redis-statefulset"
        )
        assert result["statefulsets"]["redis-statefulset"]["namespace"] == "default"
        assert result["statefulsets"]["redis-statefulset"]["replicas"] == 1

        # Verify CronJob data
        assert "backup-job" in result["cronjobs"]
        assert result["cronjobs"]["backup-job"]["name"] == "backup-job"
        assert result["cronjobs"]["backup-job"]["namespace"] == "default"
        assert result["cronjobs"]["backup-job"]["schedule"] == "0 2 * * *"

        # Verify nodes data
        assert "worker-node-1" in result["nodes"]
        assert result["nodes"]["worker-node-1"]["name"] == "worker-node-1"
        assert result["nodes"]["worker-node-1"]["status"] == "Ready"
        assert result["nodes"]["worker-node-1"]["internal_ip"] == "10.0.0.1"
        assert result["nodes"]["worker-node-1"]["memory_capacity_gb"] == 16.0

        # Verify counts
        assert result["pods_count"] == 0
        assert result["nodes_count"] == 0

    async def test_async_update_data_with_cleanup(self, coordinator, mock_client):
        """Test data update with entity cleanup."""
        # Mock empty data
        mock_client.get_deployments.return_value = []
        mock_client.get_statefulsets.return_value = []
        mock_client.get_cronjobs.return_value = []
        mock_client.get_deployments_count.return_value = 0
        mock_client.get_statefulsets_count.return_value = 0
        mock_client.get_daemonsets_count.return_value = 0
        mock_client.get_cronjobs_count.return_value = 0

        # Mock device registry
        mock_device_registry = MagicMock()
        mock_device_registry.async_get_device = MagicMock(return_value=None)
        mock_device_registry.async_get_or_create = MagicMock(return_value=MagicMock())

        with (
            patch(
                "custom_components.kubernetes.device.dr.async_get",
                return_value=mock_device_registry,
            ),
            patch(
                "custom_components.kubernetes.device.dr.async_entries_for_config_entry",
                return_value=[],
            ),
        ):
            result = await coordinator._async_update_data()

        # Verify empty data structure
        assert result["deployments"] == {}
        assert result["statefulsets"] == {}
        assert result["cronjobs"] == {}
        assert result["jobs"] == {}
        assert result["pods_count"] == 0
        assert result["nodes_count"] == 0

    async def test_async_update_data_client_exception(self, coordinator, mock_client):
        """Test data update when client raises an exception."""
        # Mock client to raise an exception
        mock_client.get_deployments.side_effect = Exception("API Error")

        with pytest.raises(
            UpdateFailed, match="Failed to update Kubernetes data: API Error"
        ):
            await coordinator._async_update_data()

    async def test_async_update_data_partial_failure(self, coordinator, mock_client):
        """Test data update when some API calls fail."""
        # Mock StatefulSet to fail
        mock_client.get_statefulsets.side_effect = Exception("StatefulSet API Error")

        with pytest.raises(
            UpdateFailed,
            match="Failed to update Kubernetes data: StatefulSet API Error",
        ):
            await coordinator._async_update_data()

    async def test_get_deployment_data(self, coordinator):
        """Test getting deployment data."""
        # Set up test data
        coordinator.data = {
            "deployments": {
                "nginx-deployment": {
                    "name": "nginx-deployment",
                    "namespace": "default",
                    "replicas": 3,
                }
            }
        }

        # Test getting existing deployment
        result = coordinator.get_deployment_data("nginx-deployment")
        assert result is not None
        assert result["name"] == "nginx-deployment"
        assert result["replicas"] == 3

        # Test getting non-existent deployment
        result = coordinator.get_deployment_data("non-existent")
        assert result is None

    async def test_get_statefulset_data(self, coordinator):
        """Test getting StatefulSet data."""
        # Set up test data
        coordinator.data = {
            "statefulsets": {
                "redis-statefulset": {
                    "name": "redis-statefulset",
                    "namespace": "default",
                    "replicas": 1,
                }
            }
        }

        # Test getting existing StatefulSet
        result = coordinator.get_statefulset_data("redis-statefulset")
        assert result is not None
        assert result["name"] == "redis-statefulset"
        assert result["replicas"] == 1

        # Test getting non-existent StatefulSet
        result = coordinator.get_statefulset_data("non-existent")
        assert result is None

    async def test_get_cronjob_data(self, coordinator):
        """Test getting CronJob data."""
        # Set up test data
        coordinator.data = {
            "cronjobs": {
                "backup-job": {
                    "name": "backup-job",
                    "namespace": "default",
                    "schedule": "0 2 * * *",
                    "suspend": False,
                }
            }
        }

        # Test getting existing CronJob
        result = coordinator.get_cronjob_data("backup-job")
        assert result is not None
        assert result["name"] == "backup-job"
        assert result["schedule"] == "0 2 * * *"

        # Test getting non-existent CronJob
        result = coordinator.get_cronjob_data("non-existent")
        assert result is None

    async def test_get_node_data(self, coordinator):
        """Test getting node data by name."""
        # Set up mock node data
        node_data = {
            "worker-node-1": {
                "name": "worker-node-1",
                "status": "Ready",
                "internal_ip": "10.0.0.1",
                "memory_capacity_gb": 16.0,
            }
        }
        coordinator.data = {"nodes": node_data}

        # Test getting existing node
        result = coordinator.get_node_data("worker-node-1")
        assert result is not None
        assert result["name"] == "worker-node-1"
        assert result["status"] == "Ready"

        # Test getting non-existent node
        result = coordinator.get_node_data("non-existent")
        assert result is None

        # Test with no data
        coordinator.data = None
        result = coordinator.get_node_data("worker-node-1")
        assert result is None

    async def test_get_all_nodes_data(self, coordinator):
        """Test getting all nodes data."""
        # Set up mock nodes data
        nodes_data = {
            "worker-node-1": {"name": "worker-node-1", "status": "Ready"},
            "worker-node-2": {"name": "worker-node-2", "status": "NotReady"},
        }
        coordinator.data = {"nodes": nodes_data}

        # Test getting all nodes
        result = coordinator.get_all_nodes_data()
        assert len(result) == 2
        assert "worker-node-1" in result
        assert "worker-node-2" in result

        # Test with no data
        coordinator.data = None
        result = coordinator.get_all_nodes_data()
        assert result == {}

    async def test_get_last_update_time(self, coordinator):
        """Test getting last update time."""
        # Test with no data
        result = coordinator.get_last_update_time()
        assert result == 0.0

        # Test with data
        coordinator.data = {"last_update": 1234567890.0}
        result = coordinator.get_last_update_time()
        assert result == 1234567890.0

    async def test_cleanup_orphaned_entities_no_config_entry(self, coordinator):
        """Test cleanup when config entry is not available."""
        # Remove config_entry to simulate unavailable state
        coordinator.config_entry = None

        # Should not raise an exception
        await coordinator._cleanup_orphaned_entities({})

    async def test_cleanup_orphaned_entities_no_entity_registry(self, coordinator):
        """Test cleanup when entity registry is not available."""
        with patch(
            "custom_components.kubernetes.coordinator.async_get_entity_registry",
            return_value=None,
        ):
            # Should not raise an exception
            await coordinator._cleanup_orphaned_entities({})

    async def test_cleanup_orphaned_entities_exception(self, coordinator):
        """Test cleanup when an exception occurs."""
        with patch(
            "custom_components.kubernetes.coordinator.async_get_entity_registry",
            side_effect=Exception("Registry error"),
        ):
            # Should not raise an exception
            await coordinator._cleanup_orphaned_entities({})

    async def test_cleanup_orphaned_entities_removes_deployment(self, coordinator):
        """Test cleanup removes orphaned deployment entities."""
        # Mock entity registry with an orphaned deployment entity
        mock_entity = MagicMock()
        mock_entity.unique_id = "test-entry-id_orphaned-deployment_deployment"
        mock_entity.entity_id = "switch.orphaned_deployment"

        mock_registry = MagicMock()
        mock_registry.entities.get_entries_for_config_entry_id.return_value = [
            mock_entity
        ]

        with patch(
            "custom_components.kubernetes.coordinator.async_get_entity_registry",
            return_value=mock_registry,
        ):
            # Current data has no deployments
            current_data = {"deployments": {}}

            await coordinator._cleanup_orphaned_entities(current_data)

            # Should remove the orphaned entity
            mock_registry.async_remove.assert_called_once_with(
                "switch.orphaned_deployment"
            )

    async def test_cleanup_orphaned_entities_removes_statefulset(self, coordinator):
        """Test cleanup removes orphaned StatefulSet entities."""
        # Mock entity registry with an orphaned StatefulSet entity
        mock_entity = MagicMock()
        mock_entity.unique_id = "test-entry-id_orphaned-statefulset_statefulset"
        mock_entity.entity_id = "switch.orphaned_statefulset"

        mock_registry = MagicMock()
        mock_registry.entities.get_entries_for_config_entry_id.return_value = [
            mock_entity
        ]

        with patch(
            "custom_components.kubernetes.coordinator.async_get_entity_registry",
            return_value=mock_registry,
        ):
            # Current data has no StatefulSets
            current_data = {"statefulsets": {}}

            await coordinator._cleanup_orphaned_entities(current_data)

            # Should remove the orphaned entity
            mock_registry.async_remove.assert_called_once_with(
                "switch.orphaned_statefulset"
            )

    async def test_cleanup_orphaned_entities_removes_cronjob(self, coordinator):
        """Test cleanup removes orphaned CronJob entities."""
        # Mock entity registry with an orphaned CronJob entity
        mock_entity = MagicMock()
        mock_entity.unique_id = "test-entry-id_default_orphaned-cronjob_cronjob"
        mock_entity.entity_id = "switch.orphaned_cronjob"

        mock_registry = MagicMock()
        mock_registry.entities.get_entries_for_config_entry_id.return_value = [
            mock_entity
        ]

        with patch(
            "custom_components.kubernetes.coordinator.async_get_entity_registry",
            return_value=mock_registry,
        ):
            # Current data has no CronJobs
            current_data = {"cronjobs": {}}

            await coordinator._cleanup_orphaned_entities(current_data)

            # Should remove the orphaned entity
            mock_registry.async_remove.assert_called_once_with(
                "switch.orphaned_cronjob"
            )

    async def test_cleanup_orphaned_entities_keeps_existing_entities(self, coordinator):
        """Test cleanup keeps existing entities."""
        # Mock entity registry with existing entities
        mock_deployment_entity = MagicMock()
        mock_deployment_entity.unique_id = "test-entry-id_nginx-deployment_deployment"
        mock_deployment_entity.entity_id = "switch.nginx_deployment"

        mock_cronjob_entity = MagicMock()
        mock_cronjob_entity.unique_id = "test-entry-id_default_backup-job_cronjob"
        mock_cronjob_entity.entity_id = "switch.backup_job"

        mock_registry = MagicMock()
        mock_registry.entities.get_entries_for_config_entry_id.return_value = [
            mock_deployment_entity,
            mock_cronjob_entity,
        ]

        with patch(
            "custom_components.kubernetes.coordinator.async_get_entity_registry",
            return_value=mock_registry,
        ):
            # Current data has the entities
            current_data = {
                "deployments": {"nginx-deployment": {"name": "nginx-deployment"}},
                "cronjobs": {"backup-job": {"name": "backup-job"}},
            }

            await coordinator._cleanup_orphaned_entities(current_data)

            # Should not remove any entities
            mock_registry.async_remove.assert_not_called()

    async def test_cleanup_orphaned_entities_invalid_unique_id(self, coordinator):
        """Test cleanup handles invalid unique IDs."""
        # Mock entity registry with invalid unique ID
        mock_entity = MagicMock()
        mock_entity.unique_id = "invalid-format"
        mock_entity.entity_id = "switch.invalid"

        mock_registry = MagicMock()
        mock_registry.entities.get_entries_for_config_entry_id.return_value = [
            mock_entity
        ]

        with patch(
            "custom_components.kubernetes.coordinator.async_get_entity_registry",
            return_value=mock_registry,
        ):
            current_data = {"deployments": {}}

            await coordinator._cleanup_orphaned_entities(current_data)

            # Should not remove the entity with invalid format
            mock_registry.async_remove.assert_not_called()

    async def test_cleanup_orphaned_entities_no_unique_id(self, coordinator):
        """Test cleanup handles entities without unique IDs."""
        # Mock entity registry with entity without unique ID
        mock_entity = MagicMock()
        mock_entity.unique_id = None
        mock_entity.entity_id = "switch.no_unique_id"

        mock_registry = MagicMock()
        mock_registry.entities.get_entries_for_config_entry_id.return_value = [
            mock_entity
        ]

        with patch(
            "custom_components.kubernetes.coordinator.async_get_entity_registry",
            return_value=mock_registry,
        ):
            current_data = {"deployments": {}}

            await coordinator._cleanup_orphaned_entities(current_data)

            # Should not remove the entity without unique ID
            mock_registry.async_remove.assert_not_called()

    async def test_cleanup_orphaned_entities_wrong_config_entry(self, coordinator):
        """Test cleanup handles entities from different config entries."""
        # Mock entity registry with entity from different config entry
        mock_entity = MagicMock()
        mock_entity.unique_id = "other-entry-id_nginx-deployment_deployment"
        mock_entity.entity_id = "switch.nginx_deployment"

        mock_registry = MagicMock()
        mock_registry.entities.get_entries_for_config_entry_id.return_value = [
            mock_entity
        ]

        with patch(
            "custom_components.kubernetes.coordinator.async_get_entity_registry",
            return_value=mock_registry,
        ):
            current_data = {"deployments": {}}

            await coordinator._cleanup_orphaned_entities(current_data)

            # Should not remove the entity from different config entry
            mock_registry.async_remove.assert_not_called()

    async def test_cleanup_orphaned_entities_removes_node(self, coordinator):
        """Test cleanup removes orphaned node entities."""
        # Mock entity with node that no longer exists
        mock_entity = MagicMock()
        mock_entity.unique_id = "test-entry-id_node_old-node"
        mock_entity.entity_id = "sensor.old_node"

        mock_registry = MagicMock()
        mock_registry.entities.get_entries_for_config_entry_id.return_value = [
            mock_entity
        ]

        with patch(
            "custom_components.kubernetes.coordinator.async_get_entity_registry",
            return_value=mock_registry,
        ):
            # Current data has no nodes (the old node is gone)
            current_data = {"nodes": {}}

            await coordinator._cleanup_orphaned_entities(current_data)

            # Should remove the orphaned node entity
            mock_registry.async_remove.assert_called_once_with("sensor.old_node")

    async def test_cleanup_orphaned_entities_keeps_existing_node(self, coordinator):
        """Test cleanup keeps existing node entities."""
        # Mock entity with node that still exists
        mock_entity = MagicMock()
        mock_entity.unique_id = "test-entry-id_node_current-node"
        mock_entity.entity_id = "sensor.current_node"

        mock_registry = MagicMock()
        mock_registry.entities.get_entries_for_config_entry_id.return_value = [
            mock_entity
        ]

        with patch(
            "custom_components.kubernetes.coordinator.async_get_entity_registry",
            return_value=mock_registry,
        ):
            # Current data still has the node
            current_data = {"nodes": {"current-node": {"name": "current-node"}}}

            await coordinator._cleanup_orphaned_entities(current_data)

            # Should not remove the existing node entity
            mock_registry.async_remove.assert_not_called()

    async def test_get_daemonset_data(self, coordinator):
        """Test getting DaemonSet data by name."""
        coordinator.data = {
            "daemonsets": {
                "fluentd": {"name": "fluentd", "namespace": "logging"},
            }
        }
        result = coordinator.get_daemonset_data("fluentd")
        assert result is not None
        assert result["name"] == "fluentd"

        result = coordinator.get_daemonset_data("non-existent")
        assert result is None

        coordinator.data = None
        result = coordinator.get_daemonset_data("fluentd")
        assert result is None

    async def test_get_job_data(self, coordinator):
        """Test getting Job data by name."""
        coordinator.data = {
            "jobs": {
                "backup-job": {
                    "name": "backup-job",
                    "namespace": "default",
                    "succeeded": 1,
                    "completions": 1,
                }
            }
        }
        result = coordinator.get_job_data("backup-job")
        assert result is not None
        assert result["name"] == "backup-job"

        result = coordinator.get_job_data("non-existent")
        assert result is None

        coordinator.data = None
        result = coordinator.get_job_data("backup-job")
        assert result is None

    async def test_get_pod_data(self, coordinator):
        """Test getting pod data by namespace and name."""
        coordinator.data = {
            "pods": {
                "default_nginx-abc": {
                    "name": "nginx-abc",
                    "namespace": "default",
                    "status": "Running",
                }
            }
        }
        result = coordinator.get_pod_data("default", "nginx-abc")
        assert result is not None
        assert result["name"] == "nginx-abc"

        result = coordinator.get_pod_data("default", "non-existent")
        assert result is None

        coordinator.data = None
        result = coordinator.get_pod_data("default", "nginx-abc")
        assert result is None

    async def test_get_all_pods_data(self, coordinator):
        """Test getting all pods data."""
        coordinator.data = {
            "pods": {
                "default_nginx": {"name": "nginx", "namespace": "default"},
                "prod_api": {"name": "api", "namespace": "prod"},
            }
        }
        result = coordinator.get_all_pods_data()
        assert len(result) == 2

        coordinator.data = None
        result = coordinator.get_all_pods_data()
        assert result == {}

    async def test_get_all_namespaces(self, coordinator):
        """Test getting all unique namespaces from coordinator data."""
        coordinator.data = {
            "deployments": {"nginx": {"namespace": "default"}},
            "pods": {"default_app": {"namespace": "default"}},
            "statefulsets": {"redis": {"namespace": "production"}},
        }
        namespaces = coordinator.get_all_namespaces()
        assert "default" in namespaces
        assert "production" in namespaces

    async def test_cleanup_orphaned_entities_removes_daemonset(self, coordinator):
        """Test cleanup removes orphaned DaemonSet entities."""
        mock_entity = MagicMock()
        mock_entity.unique_id = "test-entry-id_fluentd_daemonset"
        mock_entity.entity_id = "sensor.fluentd"

        mock_registry = MagicMock()
        mock_registry.entities.get_entries_for_config_entry_id.return_value = [
            mock_entity
        ]

        with patch(
            "custom_components.kubernetes.coordinator.async_get_entity_registry",
            return_value=mock_registry,
        ):
            current_data = {"daemonsets": {}}
            await coordinator._cleanup_orphaned_entities(current_data)
            mock_registry.async_remove.assert_called_once_with("sensor.fluentd")

    async def test_cleanup_orphaned_entities_removes_job(self, coordinator):
        """Test cleanup removes orphaned Job sensor entities."""
        mock_entity = MagicMock()
        mock_entity.unique_id = "test-entry-id_job_default_old-job"
        mock_entity.entity_id = "sensor.old_job"

        mock_registry = MagicMock()
        mock_registry.entities.get_entries_for_config_entry_id.return_value = [
            mock_entity
        ]

        with patch(
            "custom_components.kubernetes.coordinator.async_get_entity_registry",
            return_value=mock_registry,
        ):
            current_data = {"jobs": {}}
            await coordinator._cleanup_orphaned_entities(current_data)
            mock_registry.async_remove.assert_called_once_with("sensor.old_job")

    async def test_cleanup_orphaned_entities_keeps_existing_job(self, coordinator):
        """Test cleanup keeps existing Job sensor entities."""
        mock_entity = MagicMock()
        mock_entity.unique_id = "test-entry-id_job_default_backup-job"
        mock_entity.entity_id = "sensor.backup_job"

        mock_registry = MagicMock()
        mock_registry.entities.get_entries_for_config_entry_id.return_value = [
            mock_entity
        ]

        with patch(
            "custom_components.kubernetes.coordinator.async_get_entity_registry",
            return_value=mock_registry,
        ):
            current_data = {"jobs": {"backup-job": {"name": "backup-job"}}}
            await coordinator._cleanup_orphaned_entities(current_data)
            mock_registry.async_remove.assert_not_called()

    async def test_cleanup_orphaned_entities_skips_count_sensors(self, coordinator):
        """Test cleanup does not remove count sensors."""
        mock_entity = MagicMock()
        mock_entity.unique_id = "test-entry-id_jobs_count"
        mock_entity.entity_id = "sensor.jobs_count"

        mock_registry = MagicMock()
        mock_registry.entities.get_entries_for_config_entry_id.return_value = [
            mock_entity
        ]

        with patch(
            "custom_components.kubernetes.coordinator.async_get_entity_registry",
            return_value=mock_registry,
        ):
            current_data = {"jobs": {}}
            await coordinator._cleanup_orphaned_entities(current_data)
            mock_registry.async_remove.assert_not_called()

    async def test_cleanup_orphaned_entities_cpu_memory_status_sensors(
        self, coordinator
    ):
        """Test cleanup removes cpu/memory/status sensors for deleted deployments."""
        cpu_entity = MagicMock()
        cpu_entity.unique_id = "test-entry-id_nginx_deployment_cpu"
        cpu_entity.entity_id = "sensor.nginx_cpu"

        mem_entity = MagicMock()
        mem_entity.unique_id = "test-entry-id_nginx_deployment_memory"
        mem_entity.entity_id = "sensor.nginx_memory"

        status_entity = MagicMock()
        status_entity.unique_id = "test-entry-id_nginx_deployment_status"
        status_entity.entity_id = "sensor.nginx_status"

        mock_registry = MagicMock()
        mock_registry.entities.get_entries_for_config_entry_id.return_value = [
            cpu_entity,
            mem_entity,
            status_entity,
        ]

        with patch(
            "custom_components.kubernetes.coordinator.async_get_entity_registry",
            return_value=mock_registry,
        ):
            # Deployment no longer exists
            current_data = {"deployments": {}}
            await coordinator._cleanup_orphaned_entities(current_data)
            assert mock_registry.async_remove.call_count == 3

    async def test_cleanup_orphaned_entities_cpu_sensor_statefulset(self, coordinator):
        """Test cleanup removes cpu sensor for deleted StatefulSet."""
        entity = MagicMock()
        entity.unique_id = "test-entry-id_redis_statefulset_cpu"
        entity.entity_id = "sensor.redis_cpu"

        mock_registry = MagicMock()
        mock_registry.entities.get_entries_for_config_entry_id.return_value = [entity]

        with patch(
            "custom_components.kubernetes.coordinator.async_get_entity_registry",
            return_value=mock_registry,
        ):
            current_data = {"statefulsets": {}}
            await coordinator._cleanup_orphaned_entities(current_data)
            mock_registry.async_remove.assert_called_once_with("sensor.redis_cpu")

    async def test_cleanup_orphaned_entities_cronjob_sensor_format(self, coordinator):
        """Test cleanup removes orphaned CronJob sensor (sensor format: cronjob_{ns}_{name})."""
        mock_entity = MagicMock()
        mock_entity.unique_id = "test-entry-id_cronjob_default_old-backup"
        mock_entity.entity_id = "sensor.old_backup"

        mock_registry = MagicMock()
        mock_registry.entities.get_entries_for_config_entry_id.return_value = [
            mock_entity
        ]

        with patch(
            "custom_components.kubernetes.coordinator.async_get_entity_registry",
            return_value=mock_registry,
        ):
            current_data = {"cronjobs": {}}
            await coordinator._cleanup_orphaned_entities(current_data)
            mock_registry.async_remove.assert_called_once_with("sensor.old_backup")


class TestWatchSupport:
    """Tests for the experimental Kubernetes watch API support."""

    @pytest.fixture
    def mock_hass(self):
        """Mock Home Assistant instance."""
        hass = MagicMock(spec=HomeAssistant)
        hass.data = {}
        hass.config = MagicMock()
        hass.config.config_dir = "/tmp"
        hass.async_create_background_task = MagicMock(
            return_value=MagicMock(cancel=MagicMock())
        )
        hass.async_create_task = MagicMock()
        return hass

    @pytest.fixture
    def mock_config_entry_watch_disabled(self):
        """Mock config entry with watch disabled (default)."""
        entry = MagicMock(spec=ConfigEntry)
        entry.entry_id = "test-entry-id"
        entry.options = {}  # watch disabled by default
        entry.data = {
            CONF_NAME: "Test Cluster",
            "host": "test-cluster.example.com",
            "port": 6443,
            "api_token": "test-token",
            "switch_update_interval": DEFAULT_SWITCH_UPDATE_INTERVAL,
        }
        return entry

    @pytest.fixture
    def mock_config_entry_watch_enabled(self):
        """Mock config entry with watch enabled."""
        entry = MagicMock(spec=ConfigEntry)
        entry.entry_id = "test-entry-id"
        entry.options = {CONF_ENABLE_WATCH: True}
        entry.data = {
            CONF_NAME: "Test Cluster",
            "host": "test-cluster.example.com",
            "port": 6443,
            "api_token": "test-token",
        }
        return entry

    @pytest.fixture
    def mock_client(self):
        """Mock Kubernetes client."""
        client = MagicMock()
        client.host = "test-cluster.example.com"
        client.port = 6443
        client.monitor_all_namespaces = True
        client.namespaces = ["default"]
        client._parse_pod_item = MagicMock(
            return_value={"name": "pod", "namespace": "default"}
        )
        client._parse_node_item = MagicMock(return_value={"name": "node"})
        client._parse_deployment_item = MagicMock(
            return_value={"name": "deploy", "namespace": "default"}
        )
        client._parse_statefulset_item = MagicMock(
            return_value={"name": "sts", "namespace": "default"}
        )
        client._parse_daemonset_item = MagicMock(
            return_value={"name": "ds", "namespace": "default"}
        )
        client._format_cronjob_from_dict = MagicMock(
            return_value={"name": "cj", "namespace": "default"}
        )
        client._format_job_from_dict = MagicMock(
            return_value={"name": "job", "namespace": "default"}
        )
        client.list_resource_with_version = AsyncMock(return_value=([], "123"))

        async def _default_empty_stream(url, rv):
            return
            yield  # make it an async generator

        client.watch_stream = _default_empty_stream
        return client

    @pytest.fixture
    def coordinator_watch_disabled(
        self, mock_hass, mock_config_entry_watch_disabled, mock_client
    ):
        """Coordinator with watch disabled."""
        with patch("homeassistant.helpers.frame.report_usage"):
            return KubernetesDataCoordinator(
                mock_hass, mock_config_entry_watch_disabled, mock_client
            )

    @pytest.fixture
    def coordinator_watch_enabled(
        self, mock_hass, mock_config_entry_watch_enabled, mock_client
    ):
        """Coordinator with watch enabled."""
        with patch("homeassistant.helpers.frame.report_usage"):
            return KubernetesDataCoordinator(
                mock_hass, mock_config_entry_watch_enabled, mock_client
            )

    # ------------------------------------------------------------------
    # Poll interval tests
    # ------------------------------------------------------------------

    async def test_coordinator_uses_normal_poll_interval_when_watch_disabled(
        self, coordinator_watch_disabled
    ):
        """Coordinator should use the standard poll interval when watch is disabled."""
        assert (
            coordinator_watch_disabled.update_interval.total_seconds()
            == DEFAULT_SWITCH_UPDATE_INTERVAL
        )

    async def test_coordinator_uses_fallback_poll_interval_when_watch_enabled(
        self, coordinator_watch_enabled
    ):
        """Coordinator should use the long fallback poll interval when watch is enabled."""
        assert (
            coordinator_watch_enabled.update_interval.total_seconds()
            == DEFAULT_FALLBACK_POLL_INTERVAL
        )

    # ------------------------------------------------------------------
    # Task start / stop
    # ------------------------------------------------------------------

    async def test_async_start_watch_tasks_creates_tasks(
        self, coordinator_watch_enabled, mock_hass
    ):
        """async_start_watch_tasks should create one background task per resource URL."""
        await coordinator_watch_enabled.async_start_watch_tasks()
        assert mock_hass.async_create_background_task.called
        assert len(coordinator_watch_enabled._watch_tasks) > 0

    async def test_async_stop_watch_tasks_cancels_all(
        self, coordinator_watch_enabled, mock_hass
    ):
        """async_stop_watch_tasks should cancel all tasks and clear the list."""
        mock_task = MagicMock()
        mock_task.cancel = MagicMock()
        coordinator_watch_enabled._watch_tasks = [mock_task]

        with patch("asyncio.gather", new=AsyncMock()):
            await coordinator_watch_enabled.async_stop_watch_tasks()

        mock_task.cancel.assert_called_once()
        assert coordinator_watch_enabled._watch_tasks == []

    async def test_async_stop_watch_tasks_noop_when_empty(
        self, coordinator_watch_enabled
    ):
        """async_stop_watch_tasks should do nothing if no tasks are running."""
        # Should not raise
        await coordinator_watch_enabled.async_stop_watch_tasks()

    # ------------------------------------------------------------------
    # _apply_watch_event tests
    # ------------------------------------------------------------------

    async def test_apply_watch_event_noop_when_no_data(
        self, coordinator_watch_enabled, mock_client
    ):
        """_apply_watch_event should be safe when coordinator.data is None."""
        coordinator_watch_enabled.data = None
        # Should not raise
        coordinator_watch_enabled._apply_watch_event(
            "pods",
            "ADDED",
            {"metadata": {"name": "x", "namespace": "default"}},
            mock_client._parse_pod_item,
        )

    async def test_apply_watch_event_added(
        self, coordinator_watch_enabled, mock_client
    ):
        """ADDED event should insert the parsed object into coordinator.data."""
        coordinator_watch_enabled.data = {
            "pods": {},
            "pods_count": 0,
        }
        coordinator_watch_enabled.async_update_listeners = MagicMock()

        obj = {
            "metadata": {
                "name": "nginx",
                "namespace": "default",
                "resourceVersion": "1",
            }
        }
        mock_client._parse_pod_item.return_value = {
            "name": "nginx",
            "namespace": "default",
        }

        coordinator_watch_enabled._apply_watch_event(
            "pods", "ADDED", obj, mock_client._parse_pod_item
        )

        assert "default_nginx" in coordinator_watch_enabled.data["pods"]
        assert coordinator_watch_enabled.data["pods_count"] == 1
        coordinator_watch_enabled.async_update_listeners.assert_called_once()

    async def test_apply_watch_event_modified(
        self, coordinator_watch_enabled, mock_client
    ):
        """MODIFIED event should update an existing entry in coordinator.data."""
        coordinator_watch_enabled.data = {
            "pods": {
                "default_nginx": {
                    "name": "nginx",
                    "namespace": "default",
                    "phase": "Pending",
                }
            },
            "pods_count": 1,
        }
        coordinator_watch_enabled.async_update_listeners = MagicMock()

        obj = {
            "metadata": {
                "name": "nginx",
                "namespace": "default",
                "resourceVersion": "2",
            }
        }
        mock_client._parse_pod_item.return_value = {
            "name": "nginx",
            "namespace": "default",
            "phase": "Running",
        }

        coordinator_watch_enabled._apply_watch_event(
            "pods", "MODIFIED", obj, mock_client._parse_pod_item
        )

        assert (
            coordinator_watch_enabled.data["pods"]["default_nginx"]["phase"]
            == "Running"
        )

    async def test_apply_watch_event_deleted(
        self, coordinator_watch_enabled, mock_client
    ):
        """DELETED event should remove the object from coordinator.data."""
        coordinator_watch_enabled.data = {
            "pods": {"default_nginx": {"name": "nginx", "namespace": "default"}},
            "pods_count": 1,
        }
        coordinator_watch_enabled.async_update_listeners = MagicMock()
        coordinator_watch_enabled.hass.async_create_task = MagicMock()

        obj = {
            "metadata": {
                "name": "nginx",
                "namespace": "default",
                "resourceVersion": "3",
            }
        }

        coordinator_watch_enabled._apply_watch_event(
            "pods", "DELETED", obj, mock_client._parse_pod_item
        )

        assert "default_nginx" not in coordinator_watch_enabled.data["pods"]
        assert coordinator_watch_enabled.data["pods_count"] == 0
        coordinator_watch_enabled.async_update_listeners.assert_called_once()

    async def test_apply_watch_event_nodes_count_synced(
        self, coordinator_watch_enabled, mock_client
    ):
        """nodes_count should be updated when node events arrive."""
        coordinator_watch_enabled.data = {"nodes": {}, "nodes_count": 0}
        coordinator_watch_enabled.async_update_listeners = MagicMock()

        mock_client._parse_node_item.return_value = {"name": "node1"}
        obj = {"metadata": {"name": "node1", "resourceVersion": "1"}}

        coordinator_watch_enabled._apply_watch_event(
            "nodes", "ADDED", obj, mock_client._parse_node_item
        )

        assert coordinator_watch_enabled.data["nodes_count"] == 1

    # ------------------------------------------------------------------
    # _run_watch_loop tests
    # ------------------------------------------------------------------

    async def test_run_watch_loop_handles_cancel(
        self, coordinator_watch_enabled, mock_client
    ):
        """CancelledError should exit the loop cleanly."""

        async def _raise_cancel(url):
            raise asyncio.CancelledError

        mock_client.list_resource_with_version.side_effect = _raise_cancel

        # Should return without raising
        await coordinator_watch_enabled._run_watch_loop(
            "pods", "https://host/api/v1/pods", mock_client._parse_pod_item
        )

    async def test_run_watch_loop_handles_resource_version_expired(
        self, coordinator_watch_enabled, mock_client
    ):
        """ResourceVersionExpired during listing should trigger a relist (rv reset to '0')."""
        call_count = 0

        async def _side_effect(url):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ResourceVersionExpired("gone")
            # Second call succeeds; stop the loop after
            coordinator_watch_enabled._watch_stop_event.set()
            return [], "456"

        mock_client.list_resource_with_version.side_effect = _side_effect

        # Provide a proper async generator so async-for doesn't hang on MagicMock
        async def _empty_stream(url, rv):
            return
            yield  # make it an async generator

        mock_client.watch_stream = _empty_stream

        coordinator_watch_enabled.data = {
            "pods": {},
            "pods_count": 0,
            "nodes": {},
            "nodes_count": 0,
            "deployments": {},
            "statefulsets": {},
            "daemonsets": {},
            "cronjobs": {},
            "jobs": {},
        }
        coordinator_watch_enabled.async_update_listeners = MagicMock()

        await coordinator_watch_enabled._run_watch_loop(
            "pods", "https://host/api/v1/pods", mock_client._parse_pod_item
        )

        assert call_count == 2

    async def test_run_watch_loop_stops_on_stop_event(
        self, coordinator_watch_enabled, mock_client
    ):
        """Setting the stop event after the initial list should exit the loop."""
        coordinator_watch_enabled.data = {
            "pods": {},
            "pods_count": 0,
        }
        coordinator_watch_enabled.async_update_listeners = MagicMock()

        async def _stop_after_list(url):
            coordinator_watch_enabled._watch_stop_event.set()
            return [], "789"

        mock_client.list_resource_with_version.side_effect = _stop_after_list

        # watch_stream should not be called because stop_event is set before it
        async def _empty_stream(url, rv):
            return
            yield  # make it a generator

        mock_client.watch_stream = _empty_stream

        await coordinator_watch_enabled._run_watch_loop(
            "pods", "https://host/api/v1/pods", mock_client._parse_pod_item
        )

    async def test_populate_from_list_merges_across_namespaces(
        self, coordinator_watch_enabled, mock_client
    ):
        """_populate_from_list should merge into existing data, not replace it.

        When watch tasks for multiple namespaces both call _populate_from_list
        for the same resource_type, the second call must not discard the data
        written by the first.
        """
        coordinator_watch_enabled.data = {
            "pods": {
                "ns1_existing": {"name": "existing", "namespace": "ns1"},
            },
            "pods_count": 1,
        }

        mock_client._parse_pod_item.return_value = {
            "name": "new-pod",
            "namespace": "ns2",
        }

        coordinator_watch_enabled._populate_from_list(
            "pods",
            [{"metadata": {"name": "new-pod", "namespace": "ns2"}}],
            mock_client._parse_pod_item,
        )

        # Both namespaces' pods must be present after the merge
        assert "ns1_existing" in coordinator_watch_enabled.data["pods"]
        assert "ns2_new-pod" in coordinator_watch_enabled.data["pods"]
        assert coordinator_watch_enabled.data["pods_count"] == 2
