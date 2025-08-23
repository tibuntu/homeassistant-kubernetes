"""Tests for the Kubernetes integration coordinator."""

from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant

try:
    from homeassistant.exceptions import ConfigEntryNotReady
except ImportError:
    # Fallback for older HomeAssistant versions
    class ConfigEntryNotReady(Exception):
        pass


try:
    from homeassistant.helpers.update_coordinator import UpdateFailed
except ImportError:
    # Fallback for older HomeAssistant versions
    class UpdateFailed(Exception):
        pass


import pytest

from custom_components.kubernetes.const import (
    CONF_CLUSTER_NAME,
    CONF_MONITOR_ALL_NAMESPACES,
    CONF_SWITCH_UPDATE_INTERVAL,
    DEFAULT_SWITCH_UPDATE_INTERVAL,
    DOMAIN,
)
from custom_components.kubernetes.coordinator import KubernetesDataCoordinator


@pytest.fixture
def mock_hass():
    """Mock Home Assistant instance."""
    hass = MagicMock(spec=HomeAssistant)
    return hass


@pytest.fixture
def mock_config_entry():
    """Mock config entry."""
    config_entry = MagicMock()
    config_entry.entry_id = "test_entry_id"
    config_entry.data = {
        CONF_HOST: "https://kubernetes.example.com",
        CONF_PORT: 6443,
        CONF_CLUSTER_NAME: "test-cluster",
        CONF_MONITOR_ALL_NAMESPACES: True,
    }
    return config_entry


@pytest.fixture
def mock_client():
    """Mock Kubernetes client."""
    client = MagicMock()
    client.get_deployments = AsyncMock(return_value=[])
    client.get_statefulsets = AsyncMock(return_value=[])
    client.get_pods_count = AsyncMock(return_value=0)
    client.get_nodes_count = AsyncMock(return_value=0)
    return client


@pytest.fixture
def coordinator(mock_hass, mock_config_entry, mock_client):
    """Create a coordinator instance."""
    with patch("homeassistant.helpers.frame.report_usage"):
        return KubernetesDataCoordinator(mock_hass, mock_config_entry, mock_client)


def test_coordinator_initialization(mock_hass, mock_config_entry, mock_client):
    """Test coordinator initialization."""
    with patch("homeassistant.helpers.frame.report_usage"):
        coordinator = KubernetesDataCoordinator(
            mock_hass, mock_config_entry, mock_client
        )

        assert coordinator.config_entry == mock_config_entry
        assert coordinator.client == mock_client
        assert coordinator.name == f"{DOMAIN}_{mock_config_entry.entry_id}"


def test_coordinator_initialization_with_custom_update_interval(
    mock_hass, mock_config_entry, mock_client
):
    """Test coordinator initialization with custom update interval."""
    mock_config_entry.data[CONF_SWITCH_UPDATE_INTERVAL] = 30

    with patch("homeassistant.helpers.frame.report_usage"):
        coordinator = KubernetesDataCoordinator(
            mock_hass, mock_config_entry, mock_client
        )

    assert coordinator.update_interval.total_seconds() == 30


def test_coordinator_initialization_with_default_update_interval(
    mock_hass, mock_config_entry, mock_client
):
    """Test coordinator initialization with default update interval."""
    # Remove custom interval from config
    if CONF_SWITCH_UPDATE_INTERVAL in mock_config_entry.data:
        del mock_config_entry.data[CONF_SWITCH_UPDATE_INTERVAL]

    with patch("homeassistant.helpers.frame.report_usage"):
        coordinator = KubernetesDataCoordinator(
            mock_hass, mock_config_entry, mock_client
        )

    assert coordinator.update_interval.total_seconds() == DEFAULT_SWITCH_UPDATE_INTERVAL


async def test_async_update_data_success(coordinator, mock_client):
    """Test successful data update."""
    # Mock deployments and statefulsets
    mock_deployments = [
        {
            "name": "nginx-deployment",
            "namespace": "default",
            "replicas": 3,
            "available_replicas": 3,
            "ready_replicas": 3,
            "is_running": True,
        }
    ]

    mock_statefulsets = [
        {
            "name": "redis-statefulset",
            "namespace": "default",
            "replicas": 3,
            "available_replicas": 3,
            "ready_replicas": 3,
            "is_running": True,
        }
    ]

    mock_client.get_deployments.return_value = mock_deployments
    mock_client.get_statefulsets.return_value = mock_statefulsets

    with patch(
        "custom_components.kubernetes.coordinator.asyncio.get_event_loop"
    ) as mock_loop:
        mock_loop.return_value.time.return_value = 1234567890.0

        result = await coordinator._async_update_data()

        assert result["deployments"]["nginx-deployment"] == mock_deployments[0]
        assert result["statefulsets"]["redis-statefulset"] == mock_statefulsets[0]
        assert result["last_update"] == 1234567890.0

        mock_client.get_deployments.assert_called_once()
        mock_client.get_statefulsets.assert_called_once()


async def test_async_update_data_client_exception(coordinator, mock_client):
    """Test data update when client raises an exception."""
    mock_client.get_deployments.side_effect = Exception("API Error")

    with pytest.raises(
        UpdateFailed, match="Failed to update Kubernetes data: API Error"
    ):
        await coordinator._async_update_data()


async def test_async_update_data_with_cleanup(coordinator, mock_client):
    """Test data update with entity cleanup."""
    mock_deployments = [
        {
            "name": "nginx-deployment",
            "namespace": "default",
            "replicas": 3,
            "available_replicas": 3,
            "ready_replicas": 3,
            "is_running": True,
        }
    ]

    mock_statefulsets = []

    mock_client.get_deployments.return_value = mock_deployments
    mock_client.get_statefulsets.return_value = mock_statefulsets

    with (
        patch(
            "custom_components.kubernetes.coordinator.asyncio.get_event_loop"
        ) as mock_loop,
        patch(
            "custom_components.kubernetes.coordinator.KubernetesDataCoordinator._cleanup_orphaned_entities"
        ) as mock_cleanup,
    ):
        mock_loop.return_value.time.return_value = 1234567890.0

        result = await coordinator._async_update_data()

        assert result["deployments"]["nginx-deployment"] == mock_deployments[0]
        assert result["statefulsets"] == {}
        mock_cleanup.assert_called_once_with(result)


def test_get_deployment_data_with_data(coordinator):
    """Test getting deployment data when data exists."""
    coordinator.data = {
        "deployments": {
            "nginx-deployment": {
                "name": "nginx-deployment",
                "replicas": 3,
            }
        }
    }

    result = coordinator.get_deployment_data("nginx-deployment")
    assert result["name"] == "nginx-deployment"
    assert result["replicas"] == 3


def test_get_deployment_data_without_data(coordinator):
    """Test getting deployment data when no data exists."""
    result = coordinator.get_deployment_data("nginx-deployment")
    assert result is None


def test_get_deployment_data_deployment_not_found(coordinator):
    """Test getting deployment data for non-existent deployment."""
    coordinator.data = {
        "deployments": {
            "other-deployment": {
                "name": "other-deployment",
                "replicas": 1,
            }
        }
    }

    result = coordinator.get_deployment_data("nginx-deployment")
    assert result is None


def test_get_statefulset_data_with_data(coordinator):
    """Test getting statefulset data when data exists."""
    coordinator.data = {
        "statefulsets": {
            "redis-statefulset": {
                "name": "redis-statefulset",
                "replicas": 3,
            }
        }
    }

    result = coordinator.get_statefulset_data("redis-statefulset")
    assert result["name"] == "redis-statefulset"
    assert result["replicas"] == 3


def test_get_statefulset_data_without_data(coordinator):
    """Test getting statefulset data when no data exists."""
    result = coordinator.get_statefulset_data("redis-statefulset")
    assert result is None


def test_get_statefulset_data_statefulset_not_found(coordinator):
    """Test getting statefulset data for non-existent statefulset."""
    coordinator.data = {
        "statefulsets": {
            "other-statefulset": {
                "name": "other-statefulset",
                "replicas": 1,
            }
        }
    }

    result = coordinator.get_statefulset_data("redis-statefulset")
    assert result is None


def test_get_last_update_time_with_data(coordinator):
    """Test getting last update time when data exists."""
    coordinator.data = {"last_update": 1234567890.0}

    result = coordinator.get_last_update_time()
    assert result == 1234567890.0


def test_get_last_update_time_without_data(coordinator):
    """Test getting last update time when no data exists."""
    result = coordinator.get_last_update_time()
    assert result == 0.0


async def test_cleanup_orphaned_entities(mock_hass, mock_config_entry, mock_client):
    """Test cleanup of orphaned entities."""
    with patch("homeassistant.helpers.frame.report_usage"):
        coordinator = KubernetesDataCoordinator(
            mock_hass, mock_config_entry, mock_client
        )

        # Ensure coordinator has a proper config_entry
        assert coordinator.config_entry is not None
        assert hasattr(coordinator.config_entry, "entry_id")

    # Mock entity registry
    mock_entity_registry = MagicMock()
    mock_entities_collection = MagicMock()

    # Create mock entities with proper unique_id attributes
    config_entry_id = coordinator.config_entry.entry_id
    mock_entities = [
        MagicMock(
            entity_id="switch.nginx_deployment",
            unique_id=f"{config_entry_id}_nginx_deployment",
        ),
        MagicMock(
            entity_id="switch.redis_statefulset",
            unique_id=f"{config_entry_id}_redis_statefulset",
        ),
        MagicMock(
            entity_id="switch.orphaned_deployment",
            unique_id=f"{config_entry_id}_orphaned_deployment",
        ),
    ]

    mock_entities_collection.get_entries_for_config_entry_id.return_value = (
        mock_entities
    )
    mock_entity_registry.entities = mock_entities_collection

    with patch(
        "custom_components.kubernetes.coordinator.async_get_entity_registry",
        return_value=mock_entity_registry,
    ):
        # Current data only has nginx and redis
        current_data = {
            "deployments": {"nginx": {"name": "nginx"}},
            "statefulsets": {"redis": {"name": "redis"}},
        }

        await coordinator._cleanup_orphaned_entities(current_data)

        # Verify that orphaned entity was removed
        mock_entity_registry.async_remove.assert_called_once_with(
            "switch.orphaned_deployment"
        )


async def test_cleanup_orphaned_entities_no_orphans(coordinator):
    """Test cleanup when no orphaned entities exist."""
    # Mock entity registry
    mock_entity_registry = MagicMock()
    mock_entities = [
        MagicMock(entity_id="switch.nginx-deployment_deployment"),
        MagicMock(entity_id="switch.redis-statefulset_statefulset"),
    ]
    mock_entity_registry.async_get_entities.return_value = mock_entities

    with patch(
        "custom_components.kubernetes.coordinator.async_get_entity_registry",
        return_value=mock_entity_registry,
    ):
        # Current data has all entities
        current_data = {
            "deployments": {"nginx-deployment": {"name": "nginx-deployment"}},
            "statefulsets": {"redis-statefulset": {"name": "redis-statefulset"}},
        }

        await coordinator._cleanup_orphaned_entities(current_data)

        # Verify no entities were removed
        mock_entity_registry.async_remove.assert_not_called()
