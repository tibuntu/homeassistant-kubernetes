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
