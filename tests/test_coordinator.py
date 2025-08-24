"""Tests for the Kubernetes coordinator."""

from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed
import pytest

from custom_components.kubernetes.coordinator import KubernetesDataCoordinator


@pytest.fixture
def mock_hass():
    """Mock Home Assistant instance."""
    return MagicMock(spec=HomeAssistant)


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
        "namespace": "default",
        "verify_ssl": True,
    }
    return entry


@pytest.fixture
def mock_client():
    """Mock Kubernetes client."""
    client = MagicMock()
    client.get_deployments = AsyncMock(return_value=[])
    client.get_statefulsets = AsyncMock(return_value=[])
    client.get_cronjobs = AsyncMock(return_value=[])
    client.get_deployments_count = AsyncMock(return_value=0)
    client.get_statefulsets_count = AsyncMock(return_value=0)
    client.get_cronjobs_count = AsyncMock(return_value=0)
    client.get_pods_count = AsyncMock(return_value=0)
    client.get_nodes_count = AsyncMock(return_value=0)
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

        # Mock count data
        mock_client.get_deployments_count.return_value = 1
        mock_client.get_statefulsets_count.return_value = 1
        mock_client.get_cronjobs_count.return_value = 1

        result = await coordinator._async_update_data()

        # Verify the result structure
        assert "deployments" in result
        assert "statefulsets" in result
        assert "cronjobs" in result
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
        mock_client.get_cronjobs_count.return_value = 0

        result = await coordinator._async_update_data()

        # Verify empty data structure
        assert result["deployments"] == {}
        assert result["statefulsets"] == {}
        assert result["cronjobs"] == {}
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
