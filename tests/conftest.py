"""Test configuration and fixtures for the Kubernetes integration."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Try to import HomeAssistant, fall back to mocks if not available
try:
    from homeassistant.core import HomeAssistant
    from homeassistant.setup import async_setup_component

    HASS_AVAILABLE = True
except ImportError:
    HASS_AVAILABLE = False

    # Create minimal mocks only if homeassistant is not available
    class HomeAssistant:
        pass

    def async_setup_component(*args, **kwargs):
        return True


@pytest.fixture
def mock_hass():
    """Mock Home Assistant instance."""
    hass = MagicMock(spec=HomeAssistant)
    hass.config = MagicMock()
    hass.config_entries = MagicMock()
    hass.config_entries.async_forward_entry_setups = AsyncMock()
    hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)
    hass.services = MagicMock()
    hass.services.async_register = AsyncMock()
    hass.services.async_remove = AsyncMock()
    hass.states = MagicMock()
    hass.states.async_set = AsyncMock()
    hass.states.async_remove = AsyncMock()
    hass.data = {}
    hass.bus = MagicMock()
    hass.bus.async_fire = AsyncMock()
    hass.async_add_executor_job = AsyncMock()
    hass.async_create_task = AsyncMock()
    hass.async_run_job = AsyncMock()
    # Add missing attributes that might be accessed
    hass.config_entries.async_forward_entry_setups = AsyncMock()
    hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)
    # Add state attribute
    hass.state = MagicMock()
    return hass


@pytest.fixture
def mock_config_entry():
    """Mock config entry."""
    entry = MagicMock()
    entry.entry_id = "test_entry_id"
    entry.unique_id = "test_unique_id"
    entry.data = {
        "name": "Test Cluster",
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
def mock_kubernetes_client():
    """Mock Kubernetes client."""
    client = MagicMock()
    client._core_api = MagicMock()
    client._apps_api = MagicMock()
    client._core_api.list_namespaced_pod = AsyncMock()
    client._core_api.list_node = AsyncMock()
    client._apps_api.list_namespaced_deployment = AsyncMock()
    client._apps_api.list_namespaced_stateful_set = AsyncMock()
    client._apps_api.patch_namespaced_deployment = AsyncMock()
    client._apps_api.patch_namespaced_stateful_set = AsyncMock()
    return client


@pytest.fixture
def mock_client():
    """Mock Kubernetes client for sensor tests."""
    client = MagicMock()
    client.get_pods_count = AsyncMock(return_value=5)
    client.get_nodes_count = AsyncMock(return_value=3)
    client.get_deployments_count = AsyncMock(return_value=2)
    client.get_statefulsets_count = AsyncMock(return_value=1)
    client.is_cluster_healthy = AsyncMock(return_value=True)
    return client


@pytest.fixture
def mock_coordinator():
    """Mock coordinator for sensor tests."""
    coordinator = MagicMock()
    coordinator.data = {}
    coordinator.last_update_success = True
    coordinator.async_add_listener = MagicMock(return_value=lambda: None)
    coordinator.async_config_entry_first_refresh = AsyncMock()
    coordinator.get_all_nodes_data = MagicMock(
        return_value={
            "worker-node-1": {"name": "worker-node-1", "status": "Ready"},
            "worker-node-2": {"name": "worker-node-2", "status": "Ready"},
        }
    )
    coordinator.get_node_data = MagicMock(return_value=None)
    return coordinator


@pytest.fixture
def mock_kubernetes_api():
    """Mock Kubernetes API responses."""
    with patch(
        "custom_components.kubernetes.kubernetes_client.k8s_client"
    ) as mock_client:
        # Mock CoreV1Api
        mock_core_api = MagicMock()
        mock_core_api.list_namespaced_pod = AsyncMock()
        mock_core_api.list_node = AsyncMock()

        # Mock AppsV1Api
        mock_apps_api = MagicMock()
        mock_apps_api.list_namespaced_deployment = AsyncMock()
        mock_apps_api.list_namespaced_stateful_set = AsyncMock()
        mock_apps_api.patch_namespaced_deployment = AsyncMock()
        mock_apps_api.patch_namespaced_stateful_set = AsyncMock()

        # Mock client
        mock_client.CoreV1Api.return_value = mock_core_api
        mock_client.AppsV1Api.return_value = mock_apps_api

        yield mock_client


@pytest.fixture
def mock_homeassistant_setup():
    """Mock Home Assistant setup."""
    with patch("homeassistant.setup.async_setup_component") as mock_setup:
        mock_setup.return_value = True
        yield mock_setup


@pytest.fixture
def mock_frame_helper():
    """Mock Home Assistant frame helper."""
    with patch("homeassistant.helpers.frame.report_usage") as mock_report:
        mock_report.return_value = None
        yield mock_report


@pytest.fixture
def mock_services():
    """Mock Home Assistant services."""
    with patch(
        "custom_components.kubernetes.services.hass.services.async_register"
    ) as mock_register:
        with patch(
            "custom_components.kubernetes.services.hass.services.async_remove"
        ) as mock_remove:
            mock_register.return_value = None
            mock_remove.return_value = None
            yield mock_register, mock_remove
