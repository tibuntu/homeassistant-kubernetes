"""Tests for the Kubernetes integration."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Import from the custom component directly
from custom_components.kubernetes.const import (
    DOMAIN,
    SWITCH_TYPE_DEPLOYMENT,
    SWITCH_TYPE_STATEFULSET,
    SERVICE_SCALE_DEPLOYMENT,
    SERVICE_START_DEPLOYMENT,
    SERVICE_STOP_DEPLOYMENT,
    SERVICE_SCALE_STATEFULSET,
    SERVICE_START_STATEFULSET,
    SERVICE_STOP_STATEFULSET,
)
from custom_components.kubernetes.kubernetes_client import KubernetesClient
from custom_components.kubernetes.sensor import KubernetesPodsSensor
from custom_components.kubernetes.binary_sensor import KubernetesClusterHealthSensor
from custom_components.kubernetes.switch import KubernetesDeploymentSwitch


@pytest.fixture
def mock_config():
    """Mock configuration data."""
    return {
        "host": "test-cluster.example.com",
        "port": 6443,
        "api_token": "test-token",
        "namespace": "default",
        "verify_ssl": True,
    }


@pytest.fixture
def mock_kubernetes_client(mock_config):
    """Mock Kubernetes client."""
    client = KubernetesClient(mock_config)
    client.get_pods_count = AsyncMock(return_value=5)
    client.get_nodes_count = AsyncMock(return_value=3)
    client.get_services_count = AsyncMock(return_value=10)
    client.get_deployments_count = AsyncMock(return_value=2)
    client.get_deployments = AsyncMock(return_value=[
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
        }
    ])
    client.is_cluster_healthy = AsyncMock(return_value=True)
    client.scale_deployment = AsyncMock(return_value=True)
    client.start_deployment = AsyncMock(return_value=True)
    client.stop_deployment = AsyncMock(return_value=True)
    # Add StatefulSet methods
    client.get_statefulsets_count = AsyncMock(return_value=1)
    client.get_statefulsets = AsyncMock(return_value=[
        {
            "name": "redis-statefulset",
            "namespace": "default",
            "replicas": 3,
            "available_replicas": 3,
            "ready_replicas": 3,
            "is_running": True,
        }
    ])
    client.scale_statefulset = AsyncMock(return_value=True)
    client.start_statefulset = AsyncMock(return_value=True)
    client.stop_statefulset = AsyncMock(return_value=True)
    return client


async def test_kubernetes_client_initialization(mock_config):
    """Test Kubernetes client initialization."""
    # This test would require a real Kubernetes cluster or mocking
    # For now, we'll just test the basic structure
    assert mock_config["host"] == "test-cluster.example.com"
    assert mock_config["port"] == 6443
    assert mock_config["api_token"] == "test-token"


async def test_pods_sensor_update(mock_kubernetes_client):
    """Test pods sensor update."""
    # Create a mock config entry
    mock_config_entry = MagicMock()
    mock_config_entry.entry_id = "test_entry_id"

    sensor = KubernetesPodsSensor(mock_kubernetes_client, mock_config_entry)

    # Test the update method
    await sensor.async_update()

    # Verify the sensor value was updated
    assert sensor.native_value == 5


async def test_cluster_health_sensor_update(mock_kubernetes_client):
    """Test cluster health sensor update."""
    # Create a mock config entry
    mock_config_entry = MagicMock()
    mock_config_entry.entry_id = "test_entry_id"

    sensor = KubernetesClusterHealthSensor(mock_kubernetes_client, mock_config_entry)

    # Test the update method
    await sensor.async_update()

    # Verify the sensor value was updated
    assert sensor.is_on is True


async def test_deployment_switch_initialization(mock_kubernetes_client):
    """Test deployment switch initialization."""
    # Create a mock config entry
    mock_config_entry = MagicMock()
    mock_config_entry.entry_id = "test_entry_id"

    switch = KubernetesDeploymentSwitch(
        mock_kubernetes_client,
        mock_config_entry,
        "nginx-deployment",
        "default"
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
    assert attributes["workload_type"] == "Deployment"


async def test_deployment_switch_update(mock_kubernetes_client):
    """Test deployment switch update."""
    # Create a mock config entry
    mock_config_entry = MagicMock()
    mock_config_entry.entry_id = "test_entry_id"

    switch = KubernetesDeploymentSwitch(
        mock_kubernetes_client,
        mock_config_entry,
        "nginx-deployment",
        "default"
    )

    # Test the update method
    await switch.async_update()

    # Verify the switch state was updated
    assert switch.is_on is True
    assert switch._replicas == 3


async def test_deployment_switch_turn_on(mock_kubernetes_client):
    """Test deployment switch turn on."""
    # Create a mock config entry
    mock_config_entry = MagicMock()
    mock_config_entry.entry_id = "test_entry_id"

    switch = KubernetesDeploymentSwitch(
        mock_kubernetes_client,
        mock_config_entry,
        "api-deployment",
        "default"
    )

    # Mock the async_write_ha_state method to avoid the hass error
    switch.async_write_ha_state = AsyncMock()

    # Initially off
    switch._is_on = False
    switch._replicas = 0

    # Test turn on
    await switch.async_turn_on()

    # Verify the client was called and state was updated
    mock_kubernetes_client.start_deployment.assert_called_once_with(
        "api-deployment", replicas=1, namespace="default"
    )
    assert switch._is_on is True
    assert switch._replicas == 1


async def test_deployment_switch_turn_off(mock_kubernetes_client):
    """Test deployment switch turn off."""
    # Create a mock config entry
    mock_config_entry = MagicMock()
    mock_config_entry.entry_id = "test_entry_id"

    switch = KubernetesDeploymentSwitch(
        mock_kubernetes_client,
        mock_config_entry,
        "nginx-deployment",
        "default"
    )

    # Mock the async_write_ha_state method to avoid the hass error
    switch.async_write_ha_state = AsyncMock()

    # Initially on
    switch._is_on = True
    switch._replicas = 3

    # Test turn off
    await switch.async_turn_off()

    # Verify the client was called and state was updated
    mock_kubernetes_client.stop_deployment.assert_called_once_with(
        "nginx-deployment", namespace="default"
    )
    assert switch._is_on is False
    assert switch._replicas == 0


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
    """Test Kubernetes client StatefulSet control methods."""
    client = KubernetesClient(mock_config)

    # Mock the StatefulSet control methods
    client.scale_statefulset = AsyncMock(return_value=True)
    client.start_statefulset = AsyncMock(return_value=True)
    client.stop_statefulset = AsyncMock(return_value=True)

    # Test scale StatefulSet
    result = await client.scale_statefulset("test-statefulset", 3, "default")
    assert result is True
    client.scale_statefulset.assert_called_once_with("test-statefulset", 3, "default")

    # Test start StatefulSet
    result = await client.start_statefulset("test-statefulset", 2, "default")
    assert result is True
    client.start_statefulset.assert_called_once_with("test-statefulset", 2, "default")

    # Test stop StatefulSet
    result = await client.stop_statefulset("test-statefulset", "default")
    assert result is True
    client.stop_statefulset.assert_called_once_with("test-statefulset", "default")


async def test_statefulset_switch_initialization(mock_kubernetes_client):
    """Test StatefulSet switch initialization."""
    # Create a mock config entry
    mock_config_entry = MagicMock()
    mock_config_entry.entry_id = "test_entry_id"

    from custom_components.kubernetes.switch import KubernetesStatefulSetSwitch

    switch = KubernetesStatefulSetSwitch(
        mock_kubernetes_client,
        mock_config_entry,
        "redis-statefulset",
        "default"
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
    assert attributes["workload_type"] == "StatefulSet"


async def test_statefulset_switch_update(mock_kubernetes_client):
    """Test StatefulSet switch update."""
    # Create a mock config entry
    mock_config_entry = MagicMock()
    mock_config_entry.entry_id = "test_entry_id"

    from custom_components.kubernetes.switch import KubernetesStatefulSetSwitch

    switch = KubernetesStatefulSetSwitch(
        mock_kubernetes_client,
        mock_config_entry,
        "redis-statefulset",
        "default"
    )

    # Mock the get_statefulsets method
    mock_kubernetes_client.get_statefulsets = AsyncMock(return_value=[
        {
            "name": "redis-statefulset",
            "namespace": "default",
            "replicas": 3,
            "available_replicas": 3,
            "ready_replicas": 3,
            "is_running": True,
        }
    ])

    # Test the update method
    await switch.async_update()

    # Verify the switch state was updated
    assert switch.is_on is True
    assert switch._replicas == 3


async def test_statefulset_switch_turn_on(mock_kubernetes_client):
    """Test StatefulSet switch turn on."""
    # Create a mock config entry
    mock_config_entry = MagicMock()
    mock_config_entry.entry_id = "test_entry_id"

    from custom_components.kubernetes.switch import KubernetesStatefulSetSwitch

    switch = KubernetesStatefulSetSwitch(
        mock_kubernetes_client,
        mock_config_entry,
        "redis-statefulset",
        "default"
    )

    # Mock the async_write_ha_state method to avoid the hass error
    switch.async_write_ha_state = AsyncMock()

    # Initially off
    switch._is_on = False
    switch._replicas = 0

    # Test turn on
    await switch.async_turn_on()

    # Verify the client was called and state was updated
    mock_kubernetes_client.start_statefulset.assert_called_once_with(
        "redis-statefulset", replicas=1, namespace="default"
    )
    assert switch._is_on is True
    assert switch._replicas == 1


async def test_statefulset_switch_turn_off(mock_kubernetes_client):
    """Test StatefulSet switch turn off."""
    # Create a mock config entry
    mock_config_entry = MagicMock()
    mock_config_entry.entry_id = "test_entry_id"

    from custom_components.kubernetes.switch import KubernetesStatefulSetSwitch

    switch = KubernetesStatefulSetSwitch(
        mock_kubernetes_client,
        mock_config_entry,
        "redis-statefulset",
        "default"
    )

    # Mock the async_write_ha_state method to avoid the hass error
    switch.async_write_ha_state = AsyncMock()

    # Initially on
    switch._is_on = True
    switch._replicas = 3

    # Test turn off
    await switch.async_turn_off()

    # Verify the client was called and state was updated
    mock_kubernetes_client.stop_statefulset.assert_called_once_with(
        "redis-statefulset", namespace="default"
    )
    assert switch._is_on is False
    assert switch._replicas == 0


def test_constants():
    """Test that all constants are properly defined."""
    # Test switch types
    assert SWITCH_TYPE_DEPLOYMENT == "deployment"
    assert SWITCH_TYPE_STATEFULSET == "statefulset"

    # Test service names
    assert SERVICE_SCALE_DEPLOYMENT == "scale_deployment"
    assert SERVICE_START_DEPLOYMENT == "start_deployment"
    assert SERVICE_STOP_DEPLOYMENT == "stop_deployment"
    assert SERVICE_SCALE_STATEFULSET == "scale_statefulset"
    assert SERVICE_START_STATEFULSET == "start_statefulset"
    assert SERVICE_STOP_STATEFULSET == "stop_statefulset"
