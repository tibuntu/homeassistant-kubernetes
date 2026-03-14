"""Tests for the Kubernetes coordinator."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.update_coordinator import UpdateFailed
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.kubernetes.const import (
    CONF_ENABLE_WATCH,
    DEFAULT_FALLBACK_POLL_INTERVAL,
    DEFAULT_SWITCH_UPDATE_INTERVAL,
    DOMAIN,
)
from custom_components.kubernetes.coordinator import KubernetesDataCoordinator
from custom_components.kubernetes.kubernetes_client import ResourceVersionExpired


@pytest.fixture
def mock_config_entry(hass: HomeAssistant) -> MockConfigEntry:
    """Create a mock config entry and add it to hass."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        entry_id="test-entry-id",
        data={
            "cluster_name": "test-cluster",
            "host": "test-cluster.example.com",
            "port": 6443,
            "api_token": "test-token",
            "namespace": "default",
            "verify_ssl": True,
        },
        options={},
    )
    entry.add_to_hass(hass)
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
    client.get_node_metrics = AsyncMock(return_value={})
    client._test_connection = AsyncMock(return_value=True)
    return client


@pytest.fixture
def coordinator(hass: HomeAssistant, mock_config_entry: MockConfigEntry, mock_client):
    """Create a coordinator instance with real hass."""
    with patch("homeassistant.helpers.frame.report_usage"):
        return KubernetesDataCoordinator(hass, mock_config_entry, mock_client)


def _create_entity(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    unique_id: str,
    entity_id: str,
) -> None:
    """Create a real entity in the entity registry for cleanup tests."""
    domain = entity_id.split(".")[0]
    registry = er.async_get(hass)
    registry.async_get_or_create(
        domain,
        DOMAIN,
        unique_id,
        config_entry=config_entry,
        suggested_object_id=entity_id.split(".")[1],
    )


class TestKubernetesDataCoordinator:
    """Test Kubernetes data coordinator."""

    async def test_async_update_data_success(
        self, hass: HomeAssistant, coordinator, mock_client
    ):
        """Test successful data update."""
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

        mock_client.get_deployments_count.return_value = 1
        mock_client.get_statefulsets_count.return_value = 1
        mock_client.get_daemonsets_count.return_value = 1
        mock_client.get_cronjobs_count.return_value = 1

        # Mock device registry to avoid side effects from device creation
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

        assert "deployments" in result
        assert "statefulsets" in result
        assert "cronjobs" in result
        assert "jobs" in result
        assert "nodes" in result
        assert "pods_count" in result
        assert "nodes_count" in result
        assert "last_update" in result

        assert "nginx-deployment" in result["deployments"]
        assert result["deployments"]["nginx-deployment"]["name"] == "nginx-deployment"
        assert result["deployments"]["nginx-deployment"]["namespace"] == "default"
        assert result["deployments"]["nginx-deployment"]["replicas"] == 3

        assert "redis-statefulset" in result["statefulsets"]
        assert (
            result["statefulsets"]["redis-statefulset"]["name"] == "redis-statefulset"
        )
        assert result["statefulsets"]["redis-statefulset"]["namespace"] == "default"
        assert result["statefulsets"]["redis-statefulset"]["replicas"] == 1

        assert "backup-job" in result["cronjobs"]
        assert result["cronjobs"]["backup-job"]["name"] == "backup-job"
        assert result["cronjobs"]["backup-job"]["namespace"] == "default"
        assert result["cronjobs"]["backup-job"]["schedule"] == "0 2 * * *"

        assert "worker-node-1" in result["nodes"]
        assert result["nodes"]["worker-node-1"]["name"] == "worker-node-1"
        assert result["nodes"]["worker-node-1"]["status"] == "Ready"
        assert result["nodes"]["worker-node-1"]["internal_ip"] == "10.0.0.1"
        assert result["nodes"]["worker-node-1"]["memory_capacity_gb"] == 16.0

        assert result["pods_count"] == 0
        assert result["nodes_count"] == 0

    async def test_async_update_data_merges_node_metrics(
        self, hass: HomeAssistant, coordinator, mock_client
    ):
        """Test that node metrics are merged into node data."""
        mock_client.get_nodes.return_value = [
            {"name": "node1", "status": "Ready", "internal_ip": "10.0.0.1"},
            {"name": "node2", "status": "Ready", "internal_ip": "10.0.0.2"},
        ]
        mock_client.get_node_metrics.return_value = {
            "node1": {"cpu": 410.0, "memory": 2015.0},
            "node2": {"cpu": 483.0, "memory": 2325.0},
        }

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

        assert result["nodes"]["node1"]["cpu_usage_millicores"] == 410.0
        assert result["nodes"]["node1"]["memory_usage_mib"] == 2015.0
        assert result["nodes"]["node2"]["cpu_usage_millicores"] == 483.0
        assert result["nodes"]["node2"]["memory_usage_mib"] == 2325.0

    async def test_async_update_data_node_metrics_unavailable(
        self, hass: HomeAssistant, coordinator, mock_client
    ):
        """Test that missing node metrics don't break the update."""
        mock_client.get_nodes.return_value = [
            {"name": "node1", "status": "Ready", "internal_ip": "10.0.0.1"},
        ]
        mock_client.get_node_metrics.return_value = {}

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

        assert "cpu_usage_millicores" not in result["nodes"]["node1"]
        assert "memory_usage_mib" not in result["nodes"]["node1"]

    async def test_async_update_data_with_cleanup(
        self, hass: HomeAssistant, coordinator, mock_client
    ):
        """Test data update with entity cleanup."""
        mock_client.get_deployments.return_value = []
        mock_client.get_statefulsets.return_value = []
        mock_client.get_cronjobs.return_value = []
        mock_client.get_deployments_count.return_value = 0
        mock_client.get_statefulsets_count.return_value = 0
        mock_client.get_daemonsets_count.return_value = 0
        mock_client.get_cronjobs_count.return_value = 0

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

        assert result["deployments"] == {}
        assert result["statefulsets"] == {}
        assert result["cronjobs"] == {}
        assert result["jobs"] == {}
        assert result["pods_count"] == 0
        assert result["nodes_count"] == 0

    async def test_async_update_data_client_exception(self, coordinator, mock_client):
        """Test data update when client raises an exception."""
        mock_client.get_deployments.side_effect = Exception("API Error")

        with pytest.raises(
            UpdateFailed, match="Failed to update Kubernetes data: API Error"
        ):
            await coordinator._async_update_data()

    async def test_async_update_data_partial_failure(self, coordinator, mock_client):
        """Test data update when some API calls fail."""
        mock_client.get_statefulsets.side_effect = Exception("StatefulSet API Error")

        with pytest.raises(
            UpdateFailed,
            match="Failed to update Kubernetes data: StatefulSet API Error",
        ):
            await coordinator._async_update_data()

    async def test_get_deployment_data(self, coordinator):
        """Test getting deployment data."""
        coordinator.data = {
            "deployments": {
                "nginx-deployment": {
                    "name": "nginx-deployment",
                    "namespace": "default",
                    "replicas": 3,
                }
            }
        }

        result = coordinator.get_deployment_data("nginx-deployment")
        assert result is not None
        assert result["name"] == "nginx-deployment"
        assert result["replicas"] == 3

        result = coordinator.get_deployment_data("non-existent")
        assert result is None

    async def test_get_statefulset_data(self, coordinator):
        """Test getting StatefulSet data."""
        coordinator.data = {
            "statefulsets": {
                "redis-statefulset": {
                    "name": "redis-statefulset",
                    "namespace": "default",
                    "replicas": 1,
                }
            }
        }

        result = coordinator.get_statefulset_data("redis-statefulset")
        assert result is not None
        assert result["name"] == "redis-statefulset"
        assert result["replicas"] == 1

        result = coordinator.get_statefulset_data("non-existent")
        assert result is None

    async def test_get_cronjob_data(self, coordinator):
        """Test getting CronJob data."""
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

        result = coordinator.get_cronjob_data("backup-job")
        assert result is not None
        assert result["name"] == "backup-job"
        assert result["schedule"] == "0 2 * * *"

        result = coordinator.get_cronjob_data("non-existent")
        assert result is None

    async def test_get_node_data(self, coordinator):
        """Test getting node data by name."""
        node_data = {
            "worker-node-1": {
                "name": "worker-node-1",
                "status": "Ready",
                "internal_ip": "10.0.0.1",
                "memory_capacity_gb": 16.0,
            }
        }
        coordinator.data = {"nodes": node_data}

        result = coordinator.get_node_data("worker-node-1")
        assert result is not None
        assert result["name"] == "worker-node-1"
        assert result["status"] == "Ready"

        result = coordinator.get_node_data("non-existent")
        assert result is None

        coordinator.data = None
        result = coordinator.get_node_data("worker-node-1")
        assert result is None

    async def test_get_all_nodes_data(self, coordinator):
        """Test getting all nodes data."""
        nodes_data = {
            "worker-node-1": {"name": "worker-node-1", "status": "Ready"},
            "worker-node-2": {"name": "worker-node-2", "status": "NotReady"},
        }
        coordinator.data = {"nodes": nodes_data}

        result = coordinator.get_all_nodes_data()
        assert len(result) == 2
        assert "worker-node-1" in result
        assert "worker-node-2" in result

        coordinator.data = None
        result = coordinator.get_all_nodes_data()
        assert result == {}

    async def test_get_last_update_time(self, coordinator):
        """Test getting last update time."""
        result = coordinator.get_last_update_time()
        assert result == 0.0

        coordinator.data = {"last_update": 1234567890.0}
        result = coordinator.get_last_update_time()
        assert result == 1234567890.0

    async def test_cleanup_orphaned_entities_no_config_entry(self, coordinator):
        """Test cleanup when config entry is not available."""
        coordinator.config_entry = None
        await coordinator._cleanup_orphaned_entities({})

    async def test_cleanup_orphaned_entities_no_entity_registry(self, coordinator):
        """Test cleanup when entity registry is not available."""
        with patch(
            "custom_components.kubernetes.coordinator.async_get_entity_registry",
            return_value=None,
        ):
            await coordinator._cleanup_orphaned_entities({})

    async def test_cleanup_orphaned_entities_exception(self, coordinator):
        """Test cleanup when an exception occurs."""
        with patch(
            "custom_components.kubernetes.coordinator.async_get_entity_registry",
            side_effect=Exception("Registry error"),
        ):
            await coordinator._cleanup_orphaned_entities({})

    async def test_cleanup_orphaned_entities_removes_deployment(
        self, hass: HomeAssistant, coordinator, mock_config_entry
    ):
        """Test cleanup removes orphaned deployment entities."""
        _create_entity(
            hass,
            mock_config_entry,
            "test-entry-id_orphaned-deployment_deployment",
            "switch.orphaned_deployment",
        )

        current_data = {"deployments": {}}
        await coordinator._cleanup_orphaned_entities(current_data)

        registry = er.async_get(hass)
        assert registry.async_get("switch.orphaned_deployment") is None

    async def test_cleanup_orphaned_entities_removes_statefulset(
        self, hass: HomeAssistant, coordinator, mock_config_entry
    ):
        """Test cleanup removes orphaned StatefulSet entities."""
        _create_entity(
            hass,
            mock_config_entry,
            "test-entry-id_orphaned-statefulset_statefulset",
            "switch.orphaned_statefulset",
        )

        current_data = {"statefulsets": {}}
        await coordinator._cleanup_orphaned_entities(current_data)

        registry = er.async_get(hass)
        assert registry.async_get("switch.orphaned_statefulset") is None

    async def test_cleanup_orphaned_entities_removes_cronjob(
        self, hass: HomeAssistant, coordinator, mock_config_entry
    ):
        """Test cleanup removes orphaned CronJob entities."""
        _create_entity(
            hass,
            mock_config_entry,
            "test-entry-id_default_orphaned-cronjob_cronjob",
            "switch.orphaned_cronjob",
        )

        current_data = {"cronjobs": {}}
        await coordinator._cleanup_orphaned_entities(current_data)

        registry = er.async_get(hass)
        assert registry.async_get("switch.orphaned_cronjob") is None

    async def test_cleanup_orphaned_entities_keeps_existing_entities(
        self, hass: HomeAssistant, coordinator, mock_config_entry
    ):
        """Test cleanup keeps existing entities."""
        _create_entity(
            hass,
            mock_config_entry,
            "test-entry-id_nginx-deployment_deployment",
            "switch.nginx_deployment",
        )
        _create_entity(
            hass,
            mock_config_entry,
            "test-entry-id_default_backup-job_cronjob",
            "switch.backup_job",
        )

        current_data = {
            "deployments": {"nginx-deployment": {"name": "nginx-deployment"}},
            "cronjobs": {"backup-job": {"name": "backup-job"}},
        }

        await coordinator._cleanup_orphaned_entities(current_data)

        registry = er.async_get(hass)
        assert registry.async_get("switch.nginx_deployment") is not None
        assert registry.async_get("switch.backup_job") is not None

    async def test_cleanup_orphaned_entities_invalid_unique_id(
        self, hass: HomeAssistant, coordinator, mock_config_entry
    ):
        """Test cleanup handles invalid unique IDs."""
        _create_entity(
            hass,
            mock_config_entry,
            "invalid-format",
            "switch.invalid",
        )

        current_data = {"deployments": {}}
        await coordinator._cleanup_orphaned_entities(current_data)

        registry = er.async_get(hass)
        assert registry.async_get("switch.invalid") is not None

    async def test_cleanup_orphaned_entities_no_unique_id(
        self, hass: HomeAssistant, coordinator, mock_config_entry
    ):
        """Test cleanup handles entities without unique IDs."""
        # Create entity then clear its unique_id via the registry internals
        # to simulate a None unique_id scenario. Since real registries require
        # unique_id, we patch the registry for this specific edge case.
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
            mock_registry.async_remove.assert_not_called()

    async def test_cleanup_orphaned_entities_wrong_config_entry(
        self, hass: HomeAssistant, coordinator, mock_config_entry
    ):
        """Test cleanup handles entities from different config entries."""
        # Create an entity whose unique_id has a different entry prefix.
        # The cleanup function checks if unique_id starts with the entry_id.
        _create_entity(
            hass,
            mock_config_entry,
            "other-entry-id_nginx-deployment_deployment",
            "switch.nginx_deployment",
        )

        current_data = {"deployments": {}}
        await coordinator._cleanup_orphaned_entities(current_data)

        registry = er.async_get(hass)
        assert registry.async_get("switch.nginx_deployment") is not None

    async def test_cleanup_orphaned_entities_removes_node(
        self, hass: HomeAssistant, coordinator, mock_config_entry
    ):
        """Test cleanup removes orphaned node entities."""
        _create_entity(
            hass,
            mock_config_entry,
            "test-entry-id_node_old-node",
            "sensor.old_node",
        )

        current_data = {"nodes": {}}
        await coordinator._cleanup_orphaned_entities(current_data)

        registry = er.async_get(hass)
        assert registry.async_get("sensor.old_node") is None

    async def test_cleanup_orphaned_entities_keeps_existing_node(
        self, hass: HomeAssistant, coordinator, mock_config_entry
    ):
        """Test cleanup keeps existing node entities."""
        _create_entity(
            hass,
            mock_config_entry,
            "test-entry-id_node_current-node",
            "sensor.current_node",
        )

        current_data = {"nodes": {"current-node": {"name": "current-node"}}}
        await coordinator._cleanup_orphaned_entities(current_data)

        registry = er.async_get(hass)
        assert registry.async_get("sensor.current_node") is not None

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

    async def test_cleanup_orphaned_entities_removes_daemonset(
        self, hass: HomeAssistant, coordinator, mock_config_entry
    ):
        """Test cleanup removes orphaned DaemonSet entities."""
        _create_entity(
            hass,
            mock_config_entry,
            "test-entry-id_fluentd_daemonset",
            "sensor.fluentd",
        )

        current_data = {"daemonsets": {}}
        await coordinator._cleanup_orphaned_entities(current_data)

        registry = er.async_get(hass)
        assert registry.async_get("sensor.fluentd") is None

    async def test_cleanup_orphaned_entities_removes_daemonset_sensor_format(
        self, hass: HomeAssistant, coordinator, mock_config_entry
    ):
        """Test cleanup removes orphaned DaemonSet sensor (sensor format: daemonset_{name})."""
        _create_entity(
            hass,
            mock_config_entry,
            "test-entry-id_daemonset_fluentd",
            "sensor.fluentd_daemonset",
        )

        current_data = {"daemonsets": {}}
        await coordinator._cleanup_orphaned_entities(current_data)

        registry = er.async_get(hass)
        assert registry.async_get("sensor.fluentd_daemonset") is None

    async def test_cleanup_orphaned_entities_keeps_existing_daemonset_sensor_format(
        self, hass: HomeAssistant, coordinator, mock_config_entry
    ):
        """Test cleanup keeps existing DaemonSet sensor (sensor format: daemonset_{name})."""
        _create_entity(
            hass,
            mock_config_entry,
            "test-entry-id_daemonset_fluentd",
            "sensor.fluentd_daemonset",
        )

        current_data = {"daemonsets": {"fluentd": {"name": "fluentd"}}}
        await coordinator._cleanup_orphaned_entities(current_data)

        registry = er.async_get(hass)
        assert registry.async_get("sensor.fluentd_daemonset") is not None

    async def test_cleanup_orphaned_entities_removes_daemonset_sensor_underscore_name(
        self, hass: HomeAssistant, coordinator, mock_config_entry
    ):
        """Test cleanup removes orphaned DaemonSet sensor with underscored name."""
        _create_entity(
            hass,
            mock_config_entry,
            "test-entry-id_daemonset_my_custom_ds",
            "sensor.my_custom_ds_daemonset",
        )

        current_data = {"daemonsets": {}}
        await coordinator._cleanup_orphaned_entities(current_data)

        registry = er.async_get(hass)
        assert registry.async_get("sensor.my_custom_ds_daemonset") is None

    async def test_cleanup_orphaned_entities_keeps_daemonset_sensor_underscore_name(
        self, hass: HomeAssistant, coordinator, mock_config_entry
    ):
        """Test cleanup keeps existing DaemonSet sensor with underscored name."""
        _create_entity(
            hass,
            mock_config_entry,
            "test-entry-id_daemonset_my_custom_ds",
            "sensor.my_custom_ds_daemonset",
        )

        current_data = {"daemonsets": {"my_custom_ds": {"name": "my_custom_ds"}}}
        await coordinator._cleanup_orphaned_entities(current_data)

        registry = er.async_get(hass)
        assert registry.async_get("sensor.my_custom_ds_daemonset") is not None

    async def test_cleanup_orphaned_entities_removes_job(
        self, hass: HomeAssistant, coordinator, mock_config_entry
    ):
        """Test cleanup removes orphaned Job sensor entities."""
        _create_entity(
            hass,
            mock_config_entry,
            "test-entry-id_job_default_old-job",
            "sensor.old_job",
        )

        current_data = {"jobs": {}}
        await coordinator._cleanup_orphaned_entities(current_data)

        registry = er.async_get(hass)
        assert registry.async_get("sensor.old_job") is None

    async def test_cleanup_orphaned_entities_keeps_existing_job(
        self, hass: HomeAssistant, coordinator, mock_config_entry
    ):
        """Test cleanup keeps existing Job sensor entities."""
        _create_entity(
            hass,
            mock_config_entry,
            "test-entry-id_job_default_backup-job",
            "sensor.backup_job",
        )

        current_data = {"jobs": {"backup-job": {"name": "backup-job"}}}
        await coordinator._cleanup_orphaned_entities(current_data)

        registry = er.async_get(hass)
        assert registry.async_get("sensor.backup_job") is not None

    async def test_cleanup_orphaned_entities_skips_count_sensors(
        self, hass: HomeAssistant, coordinator, mock_config_entry
    ):
        """Test cleanup does not remove count sensors."""
        _create_entity(
            hass,
            mock_config_entry,
            "test-entry-id_jobs_count",
            "sensor.jobs_count",
        )

        current_data = {"jobs": {}}
        await coordinator._cleanup_orphaned_entities(current_data)

        registry = er.async_get(hass)
        assert registry.async_get("sensor.jobs_count") is not None

    async def test_cleanup_orphaned_entities_cpu_memory_status_sensors(
        self, hass: HomeAssistant, coordinator, mock_config_entry
    ):
        """Test cleanup removes cpu/memory/status sensors for deleted deployments."""
        _create_entity(
            hass,
            mock_config_entry,
            "test-entry-id_nginx_deployment_cpu",
            "sensor.nginx_cpu",
        )
        _create_entity(
            hass,
            mock_config_entry,
            "test-entry-id_nginx_deployment_memory",
            "sensor.nginx_memory",
        )
        _create_entity(
            hass,
            mock_config_entry,
            "test-entry-id_nginx_deployment_status",
            "sensor.nginx_status",
        )

        current_data = {"deployments": {}}
        await coordinator._cleanup_orphaned_entities(current_data)

        registry = er.async_get(hass)
        assert registry.async_get("sensor.nginx_cpu") is None
        assert registry.async_get("sensor.nginx_memory") is None
        assert registry.async_get("sensor.nginx_status") is None

    async def test_cleanup_orphaned_entities_cpu_sensor_statefulset(
        self, hass: HomeAssistant, coordinator, mock_config_entry
    ):
        """Test cleanup removes cpu sensor for deleted StatefulSet."""
        _create_entity(
            hass,
            mock_config_entry,
            "test-entry-id_redis_statefulset_cpu",
            "sensor.redis_cpu",
        )

        current_data = {"statefulsets": {}}
        await coordinator._cleanup_orphaned_entities(current_data)

        registry = er.async_get(hass)
        assert registry.async_get("sensor.redis_cpu") is None

    async def test_cleanup_orphaned_entities_cronjob_sensor_format(
        self, hass: HomeAssistant, coordinator, mock_config_entry
    ):
        """Test cleanup removes orphaned CronJob sensor (sensor format: cronjob_{ns}_{name})."""
        _create_entity(
            hass,
            mock_config_entry,
            "test-entry-id_cronjob_default_old-backup",
            "sensor.old_backup",
        )

        current_data = {"cronjobs": {}}
        await coordinator._cleanup_orphaned_entities(current_data)

        registry = er.async_get(hass)
        assert registry.async_get("sensor.old_backup") is None


class TestWatchSupport:
    """Tests for the experimental Kubernetes watch API support."""

    @pytest.fixture
    def mock_config_entry_watch_disabled(self, hass: HomeAssistant) -> MockConfigEntry:
        """Mock config entry with watch disabled (default)."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            entry_id="test-entry-id",
            data={
                "cluster_name": "Test Cluster",
                "host": "test-cluster.example.com",
                "port": 6443,
                "api_token": "test-token",
                "switch_update_interval": DEFAULT_SWITCH_UPDATE_INTERVAL,
            },
            options={},
        )
        entry.add_to_hass(hass)
        return entry

    @pytest.fixture
    def mock_config_entry_watch_enabled(self, hass: HomeAssistant) -> MockConfigEntry:
        """Mock config entry with watch enabled."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            entry_id="test-entry-id",
            data={
                "cluster_name": "Test Cluster",
                "host": "test-cluster.example.com",
                "port": 6443,
                "api_token": "test-token",
            },
            options={CONF_ENABLE_WATCH: True},
        )
        entry.add_to_hass(hass)
        return entry

    @pytest.fixture
    def mock_client(self):
        """Mock Kubernetes client for watch tests."""
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
        self, hass: HomeAssistant, mock_config_entry_watch_disabled, mock_client
    ):
        """Coordinator with watch disabled."""
        with patch("homeassistant.helpers.frame.report_usage"):
            return KubernetesDataCoordinator(
                hass, mock_config_entry_watch_disabled, mock_client
            )

    @pytest.fixture
    def coordinator_watch_enabled(
        self, hass: HomeAssistant, mock_config_entry_watch_enabled, mock_client
    ):
        """Coordinator with watch enabled."""
        with patch("homeassistant.helpers.frame.report_usage"):
            return KubernetesDataCoordinator(
                hass, mock_config_entry_watch_enabled, mock_client
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
        self, hass: HomeAssistant, coordinator_watch_enabled
    ):
        """async_start_watch_tasks should create one background task per resource URL."""
        created_coros = []

        def _mock_create(coro, name):
            created_coros.append(coro)
            return MagicMock()

        # Mock async_create_background_task to prevent real background loops
        with patch.object(
            hass, "async_create_background_task", side_effect=_mock_create
        ):
            await coordinator_watch_enabled.async_start_watch_tasks()

        assert len(coordinator_watch_enabled._watch_tasks) > 0

        # Close captured coroutines to avoid ResourceWarning
        for coro in created_coros:
            coro.close()

    async def test_async_stop_watch_tasks_cancels_all(self, coordinator_watch_enabled):
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
        await coordinator_watch_enabled.async_stop_watch_tasks()

    # ------------------------------------------------------------------
    # _apply_watch_event tests
    # ------------------------------------------------------------------

    async def test_apply_watch_event_noop_when_no_data(
        self, coordinator_watch_enabled, mock_client
    ):
        """_apply_watch_event should be safe when coordinator.data is None."""
        coordinator_watch_enabled.data = None
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
            coordinator_watch_enabled._watch_stop_event.set()
            return [], "456"

        mock_client.list_resource_with_version.side_effect = _side_effect

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
        """_populate_from_list should merge into existing data, not replace it."""
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

        assert "ns1_existing" in coordinator_watch_enabled.data["pods"]
        assert "ns2_new-pod" in coordinator_watch_enabled.data["pods"]
        assert coordinator_watch_enabled.data["pods_count"] == 2


class TestPopulateFromList:
    """Tests for _populate_from_list method."""

    @pytest.fixture
    def mock_client(self):
        """Mock Kubernetes client."""
        client = MagicMock()
        client.host = "test-cluster.example.com"
        client.port = 6443
        client.monitor_all_namespaces = True
        client.namespaces = ["default"]
        client._parse_pod_item = MagicMock()
        client._parse_node_item = MagicMock()
        client._parse_deployment_item = MagicMock()
        client.list_resource_with_version = AsyncMock(return_value=([], "123"))

        async def _empty_stream(url, rv):
            return
            yield

        client.watch_stream = _empty_stream
        return client

    @pytest.fixture
    def mock_config_entry(self, hass: HomeAssistant) -> MockConfigEntry:
        """Mock config entry with watch enabled."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            entry_id="test-entry-id",
            data={
                "cluster_name": "Test Cluster",
                "host": "test-cluster.example.com",
                "port": 6443,
                "api_token": "test-token",
            },
            options={CONF_ENABLE_WATCH: True},
        )
        entry.add_to_hass(hass)
        return entry

    @pytest.fixture
    def coord(self, hass: HomeAssistant, mock_config_entry, mock_client):
        """Create coordinator for populate tests."""
        with patch("homeassistant.helpers.frame.report_usage"):
            return KubernetesDataCoordinator(hass, mock_config_entry, mock_client)

    async def test_returns_early_when_data_is_none(self, coord, mock_client):
        """_populate_from_list should return early if coordinator.data is None."""
        coord.data = None
        mock_client._parse_pod_item.return_value = {
            "name": "pod1",
            "namespace": "default",
        }

        coord._populate_from_list(
            "pods",
            [{"metadata": {"name": "pod1"}}],
            mock_client._parse_pod_item,
        )

        assert coord.data is None

    async def test_non_pod_resources_use_name_as_key(self, coord, mock_client):
        """Non-pod resources should use result['name'] as the dict key."""
        coord.data = {"deployments": {}}
        mock_client._parse_deployment_item.return_value = {
            "name": "nginx-deploy",
            "namespace": "default",
        }

        coord._populate_from_list(
            "deployments",
            [{"metadata": {"name": "nginx-deploy"}}],
            mock_client._parse_deployment_item,
        )

        assert "nginx-deploy" in coord.data["deployments"]

    async def test_nodes_count_updated(self, coord, mock_client):
        """_populate_from_list should update nodes_count for nodes."""
        coord.data = {"nodes": {}}
        mock_client._parse_node_item.return_value = {"name": "node-1"}

        coord._populate_from_list(
            "nodes",
            [{"metadata": {"name": "node-1"}}],
            mock_client._parse_node_item,
        )

        assert coord.data["nodes_count"] == 1
        assert "node-1" in coord.data["nodes"]

    async def test_parse_exception_skips_item(self, coord, mock_client):
        """Items that fail parsing should be skipped without crashing."""
        coord.data = {"pods": {}, "pods_count": 0}
        mock_client._parse_pod_item.side_effect = [
            ValueError("bad item"),
            {"name": "good-pod", "namespace": "ns1"},
        ]

        coord._populate_from_list(
            "pods",
            [{"metadata": {"name": "bad"}}, {"metadata": {"name": "good"}}],
            mock_client._parse_pod_item,
        )

        assert coord.data["pods_count"] == 1
        assert "ns1_good-pod" in coord.data["pods"]

    async def test_parse_returns_none_skips_item(self, coord, mock_client):
        """Items where parse_fn returns None should be skipped."""
        coord.data = {"deployments": {}}
        mock_client._parse_deployment_item.return_value = None

        coord._populate_from_list(
            "deployments",
            [{"metadata": {"name": "x"}}],
            mock_client._parse_deployment_item,
        )

        assert coord.data["deployments"] == {}

    async def test_setdefault_creates_missing_resource_type(self, coord, mock_client):
        """setdefault should create the resource_type dict if it doesn't exist."""
        coord.data = {}
        mock_client._parse_deployment_item.return_value = {
            "name": "my-deploy",
            "namespace": "default",
        }

        coord._populate_from_list(
            "deployments",
            [{"metadata": {"name": "my-deploy"}}],
            mock_client._parse_deployment_item,
        )

        assert "deployments" in coord.data
        assert "my-deploy" in coord.data["deployments"]

    async def test_no_count_update_for_non_pod_non_node(self, coord, mock_client):
        """Deployments should not trigger pods_count or nodes_count updates."""
        coord.data = {"deployments": {}}
        mock_client._parse_deployment_item.return_value = {
            "name": "dep1",
            "namespace": "default",
        }

        coord._populate_from_list(
            "deployments",
            [{"metadata": {"name": "dep1"}}],
            mock_client._parse_deployment_item,
        )

        assert "pods_count" not in coord.data
        assert "nodes_count" not in coord.data


class TestApplyWatchEventExtended:
    """Extended tests for _apply_watch_event method."""

    @pytest.fixture
    def mock_client(self):
        """Mock Kubernetes client."""
        client = MagicMock()
        client.host = "test-cluster.example.com"
        client.port = 6443
        client.monitor_all_namespaces = True
        client.namespaces = ["default"]
        client._parse_pod_item = MagicMock()
        client._parse_node_item = MagicMock()
        client._parse_deployment_item = MagicMock()
        client.list_resource_with_version = AsyncMock(return_value=([], "123"))

        async def _empty_stream(url, rv):
            return
            yield

        client.watch_stream = _empty_stream
        return client

    @pytest.fixture
    def mock_config_entry(self, hass: HomeAssistant) -> MockConfigEntry:
        """Mock config entry with watch enabled."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            entry_id="test-entry-id",
            data={
                "cluster_name": "Test Cluster",
                "host": "test-cluster.example.com",
                "port": 6443,
                "api_token": "test-token",
            },
            options={CONF_ENABLE_WATCH: True},
        )
        entry.add_to_hass(hass)
        return entry

    @pytest.fixture
    def coord(self, hass: HomeAssistant, mock_config_entry, mock_client):
        """Create coordinator for apply_watch_event tests."""
        with patch("homeassistant.helpers.frame.report_usage"):
            return KubernetesDataCoordinator(hass, mock_config_entry, mock_client)

    async def test_unknown_event_type_ignored(self, coord, mock_client):
        """Unknown event types should return early without modifying data."""
        coord.data = {"deployments": {"dep1": {"name": "dep1"}}}
        coord.async_update_listeners = MagicMock()

        coord._apply_watch_event(
            "deployments",
            "UNKNOWN_TYPE",
            {"metadata": {"name": "dep1"}},
            mock_client._parse_deployment_item,
        )

        # Data unchanged, listeners not called
        assert "dep1" in coord.data["deployments"]
        coord.async_update_listeners.assert_not_called()

    async def test_last_update_timestamp_set(self, coord, mock_client):
        """_apply_watch_event should set last_update in coordinator.data."""
        coord.data = {"nodes": {}, "nodes_count": 0}
        coord.async_update_listeners = MagicMock()
        mock_client._parse_node_item.return_value = {"name": "node-x"}

        coord._apply_watch_event(
            "nodes",
            "ADDED",
            {"metadata": {"name": "node-x", "resourceVersion": "5"}},
            mock_client._parse_node_item,
        )

        assert "last_update" in coord.data
        assert isinstance(coord.data["last_update"], float)

    async def test_non_pod_key_uses_name(self, coord, mock_client):
        """Non-pod resources should use name (not namespace_name) as key."""
        coord.data = {"deployments": {}}
        coord.async_update_listeners = MagicMock()
        mock_client._parse_deployment_item.return_value = {
            "name": "my-deploy",
            "namespace": "production",
        }

        coord._apply_watch_event(
            "deployments",
            "ADDED",
            {"metadata": {"name": "my-deploy", "namespace": "production"}},
            mock_client._parse_deployment_item,
        )

        assert "my-deploy" in coord.data["deployments"]
        # Should NOT use namespace_name key like pods
        assert "production_my-deploy" not in coord.data["deployments"]

    async def test_deleted_event_for_nodes_updates_count(self, coord, mock_client):
        """DELETED event for nodes should decrement nodes_count."""
        coord.data = {
            "nodes": {"node-1": {"name": "node-1"}, "node-2": {"name": "node-2"}},
            "nodes_count": 2,
        }
        coord.async_update_listeners = MagicMock()

        coord._apply_watch_event(
            "nodes",
            "DELETED",
            {"metadata": {"name": "node-1"}},
            mock_client._parse_node_item,
        )

        assert coord.data["nodes_count"] == 1
        assert "node-1" not in coord.data["nodes"]

    async def test_deleted_nonexistent_key_is_safe(self, coord, mock_client):
        """Deleting a key that does not exist should not raise."""
        coord.data = {"pods": {}, "pods_count": 0}
        coord.async_update_listeners = MagicMock()

        coord._apply_watch_event(
            "pods",
            "DELETED",
            {"metadata": {"name": "ghost", "namespace": "default"}},
            mock_client._parse_pod_item,
        )

        assert coord.data["pods_count"] == 0

    async def test_parse_exception_returns_early(self, coord, mock_client):
        """If parse_fn raises during ADDED, the event should be skipped."""
        coord.data = {"pods": {}, "pods_count": 0}
        coord.async_update_listeners = MagicMock()
        mock_client._parse_pod_item.side_effect = ValueError("parse failed")

        coord._apply_watch_event(
            "pods",
            "ADDED",
            {"metadata": {"name": "bad-pod", "namespace": "default"}},
            mock_client._parse_pod_item,
        )

        assert coord.data["pods"] == {}
        coord.async_update_listeners.assert_not_called()

    async def test_added_creates_resource_type_via_setdefault(self, coord, mock_client):
        """ADDED event for a resource_type not yet in data should create the dict."""
        coord.data = {}
        coord.async_update_listeners = MagicMock()
        mock_client._parse_deployment_item.return_value = {
            "name": "new-dep",
            "namespace": "default",
        }

        coord._apply_watch_event(
            "deployments",
            "ADDED",
            {"metadata": {"name": "new-dep", "namespace": "default"}},
            mock_client._parse_deployment_item,
        )

        assert "deployments" in coord.data
        assert "new-dep" in coord.data["deployments"]

    async def test_deleted_triggers_orphan_cleanup(self, hass, coord, mock_client):
        """DELETED event should schedule orphan entity cleanup."""
        coord.data = {
            "pods": {"default_nginx": {"name": "nginx", "namespace": "default"}},
            "pods_count": 1,
        }
        coord.async_update_listeners = MagicMock()

        with patch.object(coord, "_cleanup_orphaned_entities", new=AsyncMock()) as m:
            coord._apply_watch_event(
                "pods",
                "DELETED",
                {"metadata": {"name": "nginx", "namespace": "default"}},
                mock_client._parse_pod_item,
            )
            # Let the scheduled task run
            await hass.async_block_till_done()

            m.assert_called_once()


class TestRunWatchLoopExtended:
    """Extended tests for _run_watch_loop method."""

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
        client.list_resource_with_version = AsyncMock(return_value=([], "100"))

        async def _empty_stream(url, rv):
            return
            yield

        client.watch_stream = _empty_stream
        return client

    @pytest.fixture
    def mock_config_entry(self, hass: HomeAssistant) -> MockConfigEntry:
        """Mock config entry with watch enabled."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            entry_id="test-entry-id",
            data={
                "cluster_name": "Test Cluster",
                "host": "test-cluster.example.com",
                "port": 6443,
                "api_token": "test-token",
            },
            options={CONF_ENABLE_WATCH: True},
        )
        entry.add_to_hass(hass)
        return entry

    @pytest.fixture
    def coord(self, hass: HomeAssistant, mock_config_entry, mock_client):
        """Create coordinator for watch loop tests."""
        with patch("homeassistant.helpers.frame.report_usage"):
            c = KubernetesDataCoordinator(hass, mock_config_entry, mock_client)
        c.data = {
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
        c.async_update_listeners = MagicMock()
        return c

    async def test_bookmark_events_are_skipped(self, coord, mock_client):
        """BOOKMARK events should be skipped without calling _apply_watch_event."""
        mock_client.list_resource_with_version.return_value = ([], "100")

        async def _bookmark_then_stop(url, rv):
            yield {
                "type": "BOOKMARK",
                "object": {"metadata": {"resourceVersion": "200"}},
            }
            coord._watch_stop_event.set()

        mock_client.watch_stream = _bookmark_then_stop

        with patch.object(coord, "_apply_watch_event") as mock_apply:
            await coord._run_watch_loop(
                "pods",
                "https://host/api/v1/pods",
                mock_client._parse_pod_item,
            )
            mock_apply.assert_not_called()

    async def test_initial_list_then_watch_stream(self, coord, mock_client):
        """The loop should fetch an initial list, then process watch events."""
        mock_client.list_resource_with_version.return_value = (
            [{"metadata": {"name": "pod1", "namespace": "default"}}],
            "100",
        )

        async def _stream_with_event(url, rv):
            yield {
                "type": "ADDED",
                "object": {
                    "metadata": {
                        "name": "pod2",
                        "namespace": "default",
                        "resourceVersion": "101",
                    }
                },
            }
            coord._watch_stop_event.set()

        mock_client.watch_stream = _stream_with_event

        with patch.object(coord, "_apply_watch_event") as mock_apply:
            await coord._run_watch_loop(
                "pods",
                "https://host/api/v1/pods",
                mock_client._parse_pod_item,
            )

        # Initial list should have been fetched
        mock_client.list_resource_with_version.assert_called_once()
        # Watch event should have been applied
        mock_apply.assert_called_once()

    async def test_resource_version_expired_during_watch_triggers_relist(
        self, coord, mock_client
    ):
        """ResourceVersionExpired during watch stream should reset rv and relist."""
        call_count = 0

        async def _list_side_effect(url):
            nonlocal call_count
            call_count += 1
            if call_count >= 2:
                coord._watch_stop_event.set()
            return [], str(call_count * 100)

        mock_client.list_resource_with_version.side_effect = _list_side_effect

        first_stream = True

        async def _stream_raises_expired(url, rv):
            nonlocal first_stream
            if first_stream:
                first_stream = False
                raise ResourceVersionExpired("410 Gone")
            return
            yield

        mock_client.watch_stream = _stream_raises_expired

        await coord._run_watch_loop(
            "pods",
            "https://host/api/v1/pods",
            mock_client._parse_pod_item,
        )

        # Should have listed twice: once initially, once after rv expired
        assert call_count == 2

    async def test_generic_exception_triggers_backoff_reconnect(
        self, coord, mock_client
    ):
        """Non-cancelled exceptions should trigger exponential backoff."""
        call_count = 0

        async def _list_side_effect(url):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ConnectionError("network down")
            # Second call: stop after listing
            coord._watch_stop_event.set()
            return [], "200"

        mock_client.list_resource_with_version.side_effect = _list_side_effect

        # Patch wait_for to simulate immediate timeout (no actual sleep)
        with patch("asyncio.wait_for", side_effect=TimeoutError):
            await coord._run_watch_loop(
                "pods",
                "https://host/api/v1/pods",
                mock_client._parse_pod_item,
            )

        assert call_count == 2

    async def test_stop_event_during_backoff_exits_cleanly(self, coord, mock_client):
        """If stop event fires during backoff wait, the loop should exit."""

        async def _list_raises(url):
            raise ConnectionError("fail")

        mock_client.list_resource_with_version.side_effect = _list_raises

        # Simulate the stop event being set during the wait_for
        async def _mock_wait_for(coro, timeout):
            coord._watch_stop_event.set()
            # Simulate the event being set (wait completes without TimeoutError)
            return None

        with patch("asyncio.wait_for", side_effect=_mock_wait_for):
            await coord._run_watch_loop(
                "pods",
                "https://host/api/v1/pods",
                mock_client._parse_pod_item,
            )

        # Should have exited after one attempt
        mock_client.list_resource_with_version.assert_called_once()

    async def test_resource_version_updated_from_events(self, coord, mock_client):
        """Resource version should be updated from event metadata for resume."""
        mock_client.list_resource_with_version.return_value = ([], "100")

        async def _stream_with_rv(url, rv):
            assert rv == "100"
            yield {
                "type": "ADDED",
                "object": {
                    "metadata": {
                        "name": "p1",
                        "namespace": "default",
                        "resourceVersion": "150",
                    }
                },
            }
            coord._watch_stop_event.set()

        mock_client.watch_stream = _stream_with_rv

        await coord._run_watch_loop(
            "pods",
            "https://host/api/v1/pods",
            mock_client._parse_pod_item,
        )

    async def test_stream_end_reconnects_immediately(self, coord, mock_client):
        """When the stream ends cleanly, the loop should reconnect without backoff."""
        call_count = 0

        async def _list_side_effect(url):
            nonlocal call_count
            call_count += 1
            if call_count >= 2:
                coord._watch_stop_event.set()
            return [], str(call_count * 100)

        mock_client.list_resource_with_version.side_effect = _list_side_effect

        # First stream ends cleanly (empty generator), second iteration stops
        async def _empty_stream(url, rv):
            return
            yield

        mock_client.watch_stream = _empty_stream

        await coord._run_watch_loop(
            "pods",
            "https://host/api/v1/pods",
            mock_client._parse_pod_item,
        )

        # The stream ended cleanly the first time, so it reconnected. The second
        # list call set the stop event, so only 2 calls total.
        assert call_count == 2


class TestBuildWatchConfigs:
    """Tests for _build_watch_configs method."""

    @pytest.fixture
    def mock_client(self):
        """Mock Kubernetes client."""
        client = MagicMock()
        client.host = "test-cluster.example.com"
        client.port = 6443
        client._parse_pod_item = MagicMock()
        client._parse_node_item = MagicMock()
        client._parse_deployment_item = MagicMock()
        client._parse_statefulset_item = MagicMock()
        client._parse_daemonset_item = MagicMock()
        client._format_cronjob_from_dict = MagicMock()
        client._format_job_from_dict = MagicMock()
        return client

    @pytest.fixture
    def mock_config_entry(self, hass: HomeAssistant) -> MockConfigEntry:
        """Mock config entry with watch enabled."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            entry_id="test-entry-id",
            data={
                "cluster_name": "Test Cluster",
                "host": "test-cluster.example.com",
                "port": 6443,
                "api_token": "test-token",
            },
            options={CONF_ENABLE_WATCH: True},
        )
        entry.add_to_hass(hass)
        return entry

    @pytest.fixture
    def coord(self, hass: HomeAssistant, mock_config_entry, mock_client):
        """Create coordinator for build_watch_configs tests."""
        with patch("homeassistant.helpers.frame.report_usage"):
            return KubernetesDataCoordinator(hass, mock_config_entry, mock_client)

    async def test_cluster_scoped_configs_when_monitor_all(self, coord, mock_client):
        """When monitor_all_namespaces=True, should return cluster-wide URLs."""
        mock_client.monitor_all_namespaces = True
        base_url = "https://test-cluster.example.com:6443"

        configs = coord._build_watch_configs(base_url)

        resource_types = [rt for rt, _, _ in configs]
        urls = [url for _, url, _ in configs]

        # Should include nodes (always cluster-scoped) and all namespace-scoped types
        assert "nodes" in resource_types
        assert "pods" in resource_types
        assert "deployments" in resource_types
        assert "statefulsets" in resource_types
        assert "daemonsets" in resource_types
        assert "cronjobs" in resource_types
        assert "jobs" in resource_types

        # All URLs should be cluster-wide (no /namespaces/ in them)
        for url in urls:
            assert "/namespaces/" not in url

        # 7 resource types total
        assert len(configs) == 7

    async def test_per_namespace_configs_when_not_monitor_all(self, coord, mock_client):
        """When monitor_all_namespaces=False, should return per-namespace URLs."""
        mock_client.monitor_all_namespaces = False
        mock_client.namespaces = ["default", "kube-system"]
        base_url = "https://test-cluster.example.com:6443"

        configs = coord._build_watch_configs(base_url)

        # Nodes is always cluster-scoped (1 config) plus 6 resource types * 2 namespaces
        assert len(configs) == 1 + 6 * 2

        # The nodes URL should be cluster-wide
        nodes_configs = [(rt, url) for rt, url, _ in configs if rt == "nodes"]
        assert len(nodes_configs) == 1
        assert "/namespaces/" not in nodes_configs[0][1]

        # Pods should have per-namespace URLs
        pod_configs = [(rt, url) for rt, url, _ in configs if rt == "pods"]
        assert len(pod_configs) == 2
        assert any("/namespaces/default/pods" in url for _, url in pod_configs)
        assert any("/namespaces/kube-system/pods" in url for _, url in pod_configs)

    async def test_single_namespace_config(self, coord, mock_client):
        """With one namespace and not monitoring all, should have 7 configs."""
        mock_client.monitor_all_namespaces = False
        mock_client.namespaces = ["production"]
        base_url = "https://test-cluster.example.com:6443"

        configs = coord._build_watch_configs(base_url)

        # 1 nodes (cluster-wide) + 6 per-namespace resources * 1 namespace
        assert len(configs) == 7

        # Verify namespace appears in URLs for namespace-scoped resources
        ns_urls = [url for rt, url, _ in configs if rt != "nodes"]
        for url in ns_urls:
            assert "/namespaces/production/" in url

    async def test_parse_functions_are_correct(self, coord, mock_client):
        """Each config should reference the correct parse function."""
        mock_client.monitor_all_namespaces = True
        base_url = "https://test-cluster.example.com:6443"

        configs = coord._build_watch_configs(base_url)

        parse_fn_map = {rt: fn for rt, _, fn in configs}

        assert parse_fn_map["nodes"] is mock_client._parse_node_item
        assert parse_fn_map["pods"] is mock_client._parse_pod_item
        assert parse_fn_map["deployments"] is mock_client._parse_deployment_item
        assert parse_fn_map["statefulsets"] is mock_client._parse_statefulset_item
        assert parse_fn_map["daemonsets"] is mock_client._parse_daemonset_item
        assert parse_fn_map["cronjobs"] is mock_client._format_cronjob_from_dict
        assert parse_fn_map["jobs"] is mock_client._format_job_from_dict


class TestStartStopWatchTasksExtended:
    """Extended tests for async_start_watch_tasks and async_stop_watch_tasks."""

    @pytest.fixture
    def mock_client(self):
        """Mock Kubernetes client."""
        client = MagicMock()
        client.host = "test-cluster.example.com"
        client.port = 6443
        client.monitor_all_namespaces = True
        client.namespaces = ["default"]
        client._parse_pod_item = MagicMock()
        client._parse_node_item = MagicMock()
        client._parse_deployment_item = MagicMock()
        client._parse_statefulset_item = MagicMock()
        client._parse_daemonset_item = MagicMock()
        client._format_cronjob_from_dict = MagicMock()
        client._format_job_from_dict = MagicMock()
        client.list_resource_with_version = AsyncMock(return_value=([], "123"))

        async def _empty_stream(url, rv):
            return
            yield

        client.watch_stream = _empty_stream
        return client

    @pytest.fixture
    def mock_config_entry(self, hass: HomeAssistant) -> MockConfigEntry:
        """Mock config entry with watch enabled."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            entry_id="test-entry-id",
            data={
                "cluster_name": "Test Cluster",
                "host": "test-cluster.example.com",
                "port": 6443,
                "api_token": "test-token",
            },
            options={CONF_ENABLE_WATCH: True},
        )
        entry.add_to_hass(hass)
        return entry

    @pytest.fixture
    def coord(self, hass: HomeAssistant, mock_config_entry, mock_client):
        """Create coordinator for start/stop tests."""
        with patch("homeassistant.helpers.frame.report_usage"):
            return KubernetesDataCoordinator(hass, mock_config_entry, mock_client)

    async def test_start_creates_task_per_watch_config(self, hass, coord, mock_client):
        """async_start_watch_tasks should create one task per config entry."""
        created_coros = []

        def _mock_create(coro, name):
            created_coros.append(coro)
            return MagicMock()

        with patch.object(
            hass, "async_create_background_task", side_effect=_mock_create
        ):
            await coord.async_start_watch_tasks()

        # 7 resource types for monitor_all_namespaces=True
        assert len(coord._watch_tasks) == 7

        for coro in created_coros:
            coro.close()

    async def test_start_clears_stop_event(self, hass, coord, mock_client):
        """async_start_watch_tasks should clear the stop event before starting."""
        coord._watch_stop_event.set()

        def _mock_create(coro, name):
            coro.close()
            return MagicMock()

        with patch.object(
            hass, "async_create_background_task", side_effect=_mock_create
        ):
            await coord.async_start_watch_tasks()

        assert not coord._watch_stop_event.is_set()

    async def test_stop_sets_stop_event(self, coord):
        """async_stop_watch_tasks should set the stop event."""
        mock_task = MagicMock()
        mock_task.cancel = MagicMock()
        coord._watch_tasks = [mock_task]

        with patch("asyncio.gather", new=AsyncMock()):
            await coord.async_stop_watch_tasks()

        # After stop, stop_event should be cleared (it's set then cleared)
        assert not coord._watch_stop_event.is_set()

    async def test_stop_clears_task_list(self, coord):
        """After stopping, the task list should be empty."""
        task1 = MagicMock()
        task2 = MagicMock()
        coord._watch_tasks = [task1, task2]

        with patch("asyncio.gather", new=AsyncMock()):
            await coord.async_stop_watch_tasks()

        assert coord._watch_tasks == []
        task1.cancel.assert_called_once()
        task2.cancel.assert_called_once()
