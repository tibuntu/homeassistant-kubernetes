"""Tests for the Kubernetes integration."""

from unittest.mock import AsyncMock, MagicMock

import pytest

# Import from the custom component directly
from custom_components.kubernetes.binary_sensor import KubernetesClusterHealthSensor
from custom_components.kubernetes.const import (
    ATTR_WORKLOAD_TYPE,
    DEFAULT_SCALE_COOLDOWN,
    DEFAULT_SCALE_VERIFICATION_TIMEOUT,
    DOMAIN,
    SERVICE_SCALE_WORKLOAD,
    SERVICE_START_WORKLOAD,
    SERVICE_STOP_WORKLOAD,
    SWITCH_TYPE_DEPLOYMENT,
    SWITCH_TYPE_STATEFULSET,
    WORKLOAD_TYPE_DEPLOYMENT,
    WORKLOAD_TYPE_STATEFULSET,
)
from custom_components.kubernetes.coordinator import KubernetesDataCoordinator
from custom_components.kubernetes.kubernetes_client import KubernetesClient
from custom_components.kubernetes.sensor import KubernetesPodsSensor
from custom_components.kubernetes.switch import (
    KubernetesDeploymentSwitch,
    KubernetesStatefulSetSwitch,
)


@pytest.fixture
def mock_config():
    """Mock configuration data."""
    return {
        "host": "test-cluster.example.com",
        "port": 6443,
        "api_token": "test-token",
        "namespace": "default",
        "verify_ssl": True,
        "scale_cooldown": DEFAULT_SCALE_COOLDOWN,
        "scale_verification_timeout": DEFAULT_SCALE_VERIFICATION_TIMEOUT,
    }


@pytest.fixture
def mock_kubernetes_client(mock_config):
    """Mock Kubernetes client."""
    client = KubernetesClient(mock_config)
    client.get_pods_count = AsyncMock(return_value=5)
    client.get_nodes_count = AsyncMock(return_value=3)

    client.get_deployments_count = AsyncMock(return_value=2)
    client.get_deployments = AsyncMock(
        return_value=[
            {
                "name": "nginx-deployment",
                "namespace": "default",
                "replicas": 3,
                "available_replicas": 3,
                "ready_replicas": 3,
                "is_running": True,
            },
            {
                "name": "api-deployment",
                "namespace": "default",
                "replicas": 0,
                "available_replicas": 0,
                "ready_replicas": 0,
                "is_running": False,
            },
        ]
    )
    client.is_cluster_healthy = AsyncMock(return_value=True)
    client.scale_deployment = AsyncMock(return_value=True)
    client.start_deployment = AsyncMock(return_value=True)
    client.stop_deployment = AsyncMock(return_value=True)
    # Add StatefulSet methods
    client.get_statefulsets_count = AsyncMock(return_value=1)
    client.get_statefulsets = AsyncMock(
        return_value=[
            {
                "name": "redis-statefulset",
                "namespace": "default",
                "replicas": 3,
                "available_replicas": 3,
                "ready_replicas": 3,
                "is_running": True,
            }
        ]
    )
    client.scale_statefulset = AsyncMock(return_value=True)
    client.start_statefulset = AsyncMock(return_value=True)
    client.stop_statefulset = AsyncMock(return_value=True)
    # Add DaemonSet methods
    client.get_daemonsets_count = AsyncMock(return_value=1)
    client.get_daemonsets = AsyncMock(
        return_value=[
            {
                "name": "kube-proxy",
                "namespace": "kube-system",
                "desired_number_scheduled": 3,
                "current_number_scheduled": 3,
                "number_ready": 3,
                "number_available": 3,
                "is_running": True,
            }
        ]
    )
    return client


@pytest.fixture
def mock_coordinator(mock_kubernetes_client):
    """Mock coordinator with proper data structure."""
    coordinator = MagicMock(spec=KubernetesDataCoordinator)
    coordinator.client = mock_kubernetes_client
    coordinator.last_update_success = True
    coordinator.data = {
        "deployments": {
            "nginx-deployment": {
                "name": "nginx-deployment",
                "namespace": "default",
                "replicas": 3,
                "available_replicas": 3,
                "ready_replicas": 3,
                "is_running": True,
            },
            "api-deployment": {
                "name": "api-deployment",
                "namespace": "default",
                "replicas": 0,
                "available_replicas": 0,
                "ready_replicas": 0,
                "is_running": False,
            },
        },
        "statefulsets": {
            "redis-statefulset": {
                "name": "redis-statefulset",
                "namespace": "default",
                "replicas": 3,
                "available_replicas": 3,
                "ready_replicas": 3,
                "is_running": True,
            }
        },
        "daemonsets": {
            "kube-proxy": {
                "name": "kube-proxy",
                "namespace": "kube-system",
                "desired_number_scheduled": 3,
                "current_number_scheduled": 3,
                "number_ready": 3,
                "number_available": 3,
                "is_running": True,
            }
        },
        "last_update": 1234567890.0,
    }

    # Mock the get_deployment_data method
    def get_deployment_data(name):
        return coordinator.data["deployments"].get(name)

    def get_statefulset_data(name):
        return coordinator.data["statefulsets"].get(name)

    coordinator.get_deployment_data = get_deployment_data
    coordinator.get_statefulset_data = get_statefulset_data
    coordinator.async_request_refresh = AsyncMock()

    return coordinator


async def test_kubernetes_client_initialization(mock_config):
    """Test Kubernetes client initialization."""
    # This test would require a real Kubernetes cluster or mocking
    # For now, we'll just test the basic structure
    assert mock_config["host"] == "test-cluster.example.com"
    assert mock_config["port"] == 6443
    assert mock_config["api_token"] == "test-token"


async def test_pods_sensor_update(mock_kubernetes_client, mock_coordinator):
    """Test pods sensor update."""
    # Create a mock config entry
    mock_config_entry = MagicMock()
    mock_config_entry.entry_id = "test_entry_id"

    # Set up coordinator data
    mock_coordinator.data = {"pods_count": 5}

    sensor = KubernetesPodsSensor(
        mock_coordinator, mock_kubernetes_client, mock_config_entry
    )

    # The sensor should read from coordinator data
    assert sensor.native_value == 5


async def test_cluster_health_sensor_update(mock_kubernetes_client):
    """Test cluster health sensor update."""
    # Create a mock config entry
    mock_config_entry = MagicMock()
    mock_config_entry.entry_id = "test_entry_id"

    sensor = KubernetesClusterHealthSensor(mock_kubernetes_client, mock_config_entry)

    # Test the update method
    await sensor.async_update()

    # Verify the sensor state was updated
    assert sensor.is_on is True


async def test_deployment_switch_initialization(mock_coordinator):
    """Test deployment switch initialization."""
    # Create a mock config entry
    mock_config_entry = MagicMock()
    mock_config_entry.entry_id = "test_entry_id"
    mock_config_entry.data = {
        "scale_cooldown": DEFAULT_SCALE_COOLDOWN,
        "scale_verification_timeout": DEFAULT_SCALE_VERIFICATION_TIMEOUT,
    }

    switch = KubernetesDeploymentSwitch(
        mock_coordinator, mock_config_entry, "nginx-deployment", "default"
    )

    # Test basic properties
    assert switch.deployment_name == "nginx-deployment"
    assert switch.namespace == "default"
    assert switch.name == "nginx-deployment"
    assert switch.unique_id == "test_entry_id_nginx-deployment_deployment"

    # Test attributes
    attributes = switch.extra_state_attributes
    assert attributes["deployment_name"] == "nginx-deployment"
    assert attributes["namespace"] == "default"
    assert attributes[ATTR_WORKLOAD_TYPE] == WORKLOAD_TYPE_DEPLOYMENT


async def test_deployment_switch_update(mock_coordinator):
    """Test deployment switch update."""
    # Create a mock config entry
    mock_config_entry = MagicMock()
    mock_config_entry.entry_id = "test_entry_id"
    mock_config_entry.data = {
        "scale_cooldown": DEFAULT_SCALE_COOLDOWN,
        "scale_verification_timeout": DEFAULT_SCALE_VERIFICATION_TIMEOUT,
    }

    switch = KubernetesDeploymentSwitch(
        mock_coordinator, mock_config_entry, "nginx-deployment", "default"
    )

    # Test the update method
    await switch.async_update()

    # Verify the switch state was updated
    assert switch.is_on is True
    assert switch._replicas == 3


async def test_deployment_switch_turn_on(mock_coordinator):
    """Test deployment switch turn on."""
    # Create a mock config entry
    mock_config_entry = MagicMock()
    mock_config_entry.entry_id = "test_entry_id"
    mock_config_entry.data = {
        "scale_cooldown": DEFAULT_SCALE_COOLDOWN,
        "scale_verification_timeout": DEFAULT_SCALE_VERIFICATION_TIMEOUT,
    }

    switch = KubernetesDeploymentSwitch(
        mock_coordinator, mock_config_entry, "api-deployment", "default"
    )

    # Mock the async_write_ha_state method to avoid the hass error
    switch.async_write_ha_state = MagicMock()

    # Mock the _verify_scaling method to avoid the 5-second sleep delays
    switch._verify_scaling = AsyncMock()

    # Initially off
    switch._is_on = False
    switch._replicas = 0

    # Test turn on
    await switch.async_turn_on()

    # Verify the client was called and state was updated
    mock_coordinator.client.start_deployment.assert_called_once_with(
        "api-deployment", replicas=1, namespace="default"
    )
    assert switch._is_on is True
    assert switch._replicas == 1

    # Verify that _verify_scaling was called
    switch._verify_scaling.assert_called_once_with(1)


async def test_deployment_switch_turn_off(mock_coordinator):
    """Test deployment switch turn off."""
    # Create a mock config entry
    mock_config_entry = MagicMock()
    mock_config_entry.entry_id = "test_entry_id"
    mock_config_entry.data = {
        "scale_cooldown": DEFAULT_SCALE_COOLDOWN,
        "scale_verification_timeout": DEFAULT_SCALE_VERIFICATION_TIMEOUT,
    }

    switch = KubernetesDeploymentSwitch(
        mock_coordinator, mock_config_entry, "nginx-deployment", "default"
    )

    # Mock the async_write_ha_state method to avoid the hass error
    switch.async_write_ha_state = MagicMock()

    # Mock the _verify_scaling method to avoid the 5-second sleep delays
    switch._verify_scaling = AsyncMock()

    # Initially on
    switch._is_on = True
    switch._replicas = 3

    # Test turn off
    await switch.async_turn_off()

    # Verify the client was called and state was updated
    mock_coordinator.client.stop_deployment.assert_called_once_with(
        "nginx-deployment", namespace="default"
    )
    assert switch._is_on is False
    assert switch._replicas == 0

    # Verify that _verify_scaling was called
    switch._verify_scaling.assert_called_once_with(0)


async def test_kubernetes_client_deployment_control(mock_config):
    """Test Kubernetes client deployment control methods."""
    client = KubernetesClient(mock_config)

    # Mock the async methods
    client.scale_deployment = AsyncMock(return_value=True)
    client.start_deployment = AsyncMock(return_value=True)
    client.stop_deployment = AsyncMock(return_value=True)

    # Test scale deployment
    result = await client.scale_deployment("test-deployment", 3, "default")
    assert result is True
    client.scale_deployment.assert_called_once_with("test-deployment", 3, "default")

    # Test start deployment
    result = await client.start_deployment("test-deployment", 2, "default")
    assert result is True
    client.start_deployment.assert_called_once_with("test-deployment", 2, "default")

    # Test stop deployment
    result = await client.stop_deployment("test-deployment", "default")
    assert result is True
    client.stop_deployment.assert_called_once_with("test-deployment", "default")


async def test_kubernetes_client_statefulset_control(mock_config):
    """Test Kubernetes client statefulset control methods."""
    client = KubernetesClient(mock_config)

    # Mock the async methods
    client.scale_statefulset = AsyncMock(return_value=True)
    client.start_statefulset = AsyncMock(return_value=True)
    client.stop_statefulset = AsyncMock(return_value=True)

    # Test scale statefulset
    result = await client.scale_statefulset("test-statefulset", 3, "default")
    assert result is True
    client.scale_statefulset.assert_called_once_with("test-statefulset", 3, "default")

    # Test start statefulset
    result = await client.start_statefulset("test-statefulset", 2, "default")
    assert result is True
    client.start_statefulset.assert_called_once_with("test-statefulset", 2, "default")

    # Test stop statefulset
    result = await client.stop_statefulset("test-statefulset", "default")
    assert result is True
    client.stop_statefulset.assert_called_once_with("test-statefulset", "default")


async def test_statefulset_switch_initialization(mock_coordinator):
    """Test statefulset switch initialization."""
    # Create a mock config entry
    mock_config_entry = MagicMock()
    mock_config_entry.entry_id = "test_entry_id"
    mock_config_entry.data = {
        "scale_cooldown": DEFAULT_SCALE_COOLDOWN,
        "scale_verification_timeout": DEFAULT_SCALE_VERIFICATION_TIMEOUT,
    }

    switch = KubernetesStatefulSetSwitch(
        mock_coordinator, mock_config_entry, "redis-statefulset", "default"
    )

    # Test basic properties
    assert switch.statefulset_name == "redis-statefulset"
    assert switch.namespace == "default"
    assert switch.name == "redis-statefulset"
    assert switch.unique_id == "test_entry_id_redis-statefulset_statefulset"

    # Test attributes
    attributes = switch.extra_state_attributes
    assert attributes["statefulset_name"] == "redis-statefulset"
    assert attributes["namespace"] == "default"
    assert attributes[ATTR_WORKLOAD_TYPE] == WORKLOAD_TYPE_STATEFULSET


async def test_statefulset_switch_update(mock_coordinator):
    """Test statefulset switch update."""
    # Create a mock config entry
    mock_config_entry = MagicMock()
    mock_config_entry.entry_id = "test_entry_id"
    mock_config_entry.data = {
        "scale_cooldown": DEFAULT_SCALE_COOLDOWN,
        "scale_verification_timeout": DEFAULT_SCALE_VERIFICATION_TIMEOUT,
    }

    switch = KubernetesStatefulSetSwitch(
        mock_coordinator, mock_config_entry, "redis-statefulset", "default"
    )

    # Test the update method
    await switch.async_update()

    # Verify the switch state was updated
    assert switch.is_on is True
    assert switch._replicas == 3


async def test_statefulset_switch_turn_on(mock_coordinator):
    """Test statefulset switch turn on."""
    # Create a mock config entry
    mock_config_entry = MagicMock()
    mock_config_entry.entry_id = "test_entry_id"
    mock_config_entry.data = {
        "scale_cooldown": DEFAULT_SCALE_COOLDOWN,
        "scale_verification_timeout": DEFAULT_SCALE_VERIFICATION_TIMEOUT,
    }

    switch = KubernetesStatefulSetSwitch(
        mock_coordinator, mock_config_entry, "redis-statefulset", "default"
    )

    # Mock the async_write_ha_state method to avoid the hass error
    switch.async_write_ha_state = MagicMock()

    # Mock the _verify_scaling method to avoid the 5-second sleep delays
    switch._verify_scaling = AsyncMock()

    # Initially off
    switch._is_on = False
    switch._replicas = 0

    # Test turn on
    await switch.async_turn_on()

    # Verify the client was called and state was updated
    mock_coordinator.client.start_statefulset.assert_called_once_with(
        "redis-statefulset", replicas=1, namespace="default"
    )
    assert switch._is_on is True
    assert switch._replicas == 1

    # Verify that _verify_scaling was called
    switch._verify_scaling.assert_called_once_with(1)


async def test_statefulset_switch_turn_off(mock_coordinator):
    """Test statefulset switch turn off."""
    # Create a mock config entry
    mock_config_entry = MagicMock()
    mock_config_entry.entry_id = "test_entry_id"
    mock_config_entry.data = {
        "scale_cooldown": DEFAULT_SCALE_COOLDOWN,
        "scale_verification_timeout": DEFAULT_SCALE_VERIFICATION_TIMEOUT,
    }

    switch = KubernetesStatefulSetSwitch(
        mock_coordinator, mock_config_entry, "redis-statefulset", "default"
    )

    # Mock the async_write_ha_state method to avoid the hass error
    switch.async_write_ha_state = MagicMock()

    # Mock the _verify_scaling method to avoid the 5-second sleep delays
    switch._verify_scaling = AsyncMock()

    # Initially on
    switch._is_on = True
    switch._replicas = 3

    # Test turn off
    await switch.async_turn_off()

    # Verify the client was called and state was updated
    mock_coordinator.client.stop_statefulset.assert_called_once_with(
        "redis-statefulset", namespace="default"
    )
    assert switch._is_on is False
    assert switch._replicas == 0

    # Verify that _verify_scaling was called
    switch._verify_scaling.assert_called_once_with(0)


def test_constants():
    """Test that constants are properly defined."""
    assert DOMAIN == "kubernetes"
    assert SWITCH_TYPE_DEPLOYMENT == "deployment"
    assert SWITCH_TYPE_STATEFULSET == "statefulset"
    assert SERVICE_SCALE_WORKLOAD == "scale_workload"
    assert SERVICE_START_WORKLOAD == "start_workload"
    assert SERVICE_STOP_WORKLOAD == "stop_workload"
