"""Tests for the Kubernetes integration client."""

from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from custom_components.kubernetes.kubernetes_client import KubernetesClient


@pytest.fixture
def mock_config():
    """Mock configuration data."""
    return {
        "host": "https://kubernetes.example.com",
        "port": 6443,
        "api_token": "test-token",
        "namespace": "default",
        "verify_ssl": True,
    }


@pytest.fixture
def mock_client(mock_config):
    """Mock Kubernetes client."""
    with patch(
        "custom_components.kubernetes.kubernetes_client.k8s_client"
    ) as mock_k8s_client:
        mock_api = MagicMock()
        mock_k8s_client.CoreV1Api.return_value = mock_api
        mock_k8s_client.AppsV1Api.return_value = mock_api

        client = KubernetesClient(mock_config)
        client._core_api = mock_api
        client._apps_api = mock_api
        return client


def test_kubernetes_client_initialization(mock_config):
    """Test Kubernetes client initialization."""
    with patch(
        "custom_components.kubernetes.kubernetes_client.k8s_client"
    ) as mock_k8s_client:
        mock_api = MagicMock()
        mock_k8s_client.CoreV1Api.return_value = mock_api
        mock_k8s_client.AppsV1Api.return_value = mock_api

        client = KubernetesClient(mock_config)

        assert client.host == mock_config["host"]
        assert client.port == mock_config["port"]
        assert client.api_token == mock_config["api_token"]
        assert client.namespace == mock_config["namespace"]
        assert client.verify_ssl == mock_config["verify_ssl"]


def test_kubernetes_client_initialization_with_ca_cert(mock_config):
    """Test Kubernetes client initialization with CA certificate."""
    mock_config["ca_cert"] = "test-ca-cert"

    with patch(
        "custom_components.kubernetes.kubernetes_client.k8s_client"
    ) as mock_k8s_client:
        mock_api = MagicMock()
        mock_k8s_client.CoreV1Api.return_value = mock_api
        mock_k8s_client.AppsV1Api.return_value = mock_api

        client = KubernetesClient(mock_config)

        assert client.ca_cert == "test-ca-cert"


async def test_get_pods_count_success(mock_client):
    """Test successful pods count retrieval."""
    # Mock the connection test to return True
    mock_client._test_connection = AsyncMock(return_value=True)

    # Mock the aiohttp method to return the expected count
    mock_client._get_pods_count_aiohttp = AsyncMock(return_value=3)

    count = await mock_client.get_pods_count()

    assert count == 3


async def test_get_pods_count_empty(mock_client):
    """Test pods count retrieval when no pods exist."""
    mock_client._core_api.list_namespaced_pod.return_value = MagicMock(items=[])

    count = await mock_client.get_pods_count()

    assert count == 0


async def test_get_pods_count_api_exception(mock_client):
    """Test pods count retrieval when API raises exception."""
    # Mock aiohttp session to simulate connection failure
    mock_session = MagicMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mock_session.get = AsyncMock(side_effect=Exception("Connection failed"))

    with patch(
        "custom_components.kubernetes.kubernetes_client.aiohttp.ClientSession",
        return_value=mock_session,
    ):
        count = await mock_client.get_pods_count()

    assert count == 0


async def test_get_nodes_count_success(mock_client):
    """Test successful nodes count retrieval."""
    # Mock the connection test to return True
    mock_client._test_connection = AsyncMock(return_value=True)

    # Mock the aiohttp method to return the expected count
    mock_client._get_nodes_count_aiohttp = AsyncMock(return_value=2)

    count = await mock_client.get_nodes_count()

    assert count == 2


async def test_get_nodes_count_empty(mock_client):
    """Test nodes count retrieval when no nodes exist."""
    mock_client._core_api.list_node.return_value = MagicMock(items=[])

    count = await mock_client.get_nodes_count()

    assert count == 0


async def test_get_deployments_success(mock_client):
    """Test successful deployments retrieval."""
    # Mock the connection test to return True
    mock_client._test_connection = AsyncMock(return_value=True)

    # Mock the aiohttp method to return the expected deployments
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
    mock_client._get_deployments_aiohttp = AsyncMock(return_value=mock_deployments)

    deployments = await mock_client.get_deployments()

    assert len(deployments) == 1
    assert deployments[0]["name"] == "nginx-deployment"
    assert deployments[0]["namespace"] == "default"
    assert deployments[0]["replicas"] == 3
    assert deployments[0]["available_replicas"] == 3
    assert deployments[0]["ready_replicas"] == 3
    assert deployments[0]["is_running"] is True


async def test_get_deployments_not_running(mock_client):
    """Test deployments retrieval for non-running deployment."""
    # Mock the connection test to return True
    mock_client._test_connection = AsyncMock(return_value=True)

    # Mock the aiohttp method to return the expected deployments
    mock_deployments = [
        {
            "name": "api-deployment",
            "namespace": "default",
            "replicas": 0,
            "available_replicas": 0,
            "ready_replicas": 0,
            "is_running": False,
        }
    ]
    mock_client._get_deployments_aiohttp = AsyncMock(return_value=mock_deployments)

    deployments = await mock_client.get_deployments()

    assert len(deployments) == 1
    assert deployments[0]["name"] == "api-deployment"
    assert deployments[0]["is_running"] is False


async def test_get_deployments_empty(mock_client):
    """Test deployments retrieval when no deployments exist."""
    # Mock aiohttp session for connection test
    mock_conn_response = MagicMock()
    mock_conn_response.status = 200

    # Mock aiohttp session for deployments API call
    mock_deployments_response = MagicMock()
    mock_deployments_response.status = 200
    mock_deployments_response.json = AsyncMock(return_value={"items": []})

    mock_session = MagicMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mock_session.get = AsyncMock(
        side_effect=[mock_conn_response, mock_deployments_response]
    )

    with patch("aiohttp.ClientSession", return_value=mock_session):
        deployments = await mock_client.get_deployments()

    assert deployments == []


async def test_get_deployments_count_success(mock_client):
    """Test successful deployments count retrieval."""
    # Mock the connection test to return True
    mock_client._test_connection = AsyncMock(return_value=True)

    # Mock the aiohttp method to return the expected count
    mock_client._get_deployments_count_aiohttp = AsyncMock(return_value=2)

    count = await mock_client.get_deployments_count()

    assert count == 2


async def test_get_statefulsets_success(mock_client):
    """Test successful statefulsets retrieval."""
    # Mock the connection test to return True
    mock_client._test_connection = AsyncMock(return_value=True)

    # Mock the aiohttp method to return the expected statefulsets
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
    mock_client._get_statefulsets_aiohttp = AsyncMock(return_value=mock_statefulsets)

    statefulsets = await mock_client.get_statefulsets()

    assert len(statefulsets) == 1
    assert statefulsets[0]["name"] == "redis-statefulset"
    assert statefulsets[0]["namespace"] == "default"
    assert statefulsets[0]["replicas"] == 3
    assert statefulsets[0]["available_replicas"] == 3
    assert statefulsets[0]["ready_replicas"] == 3
    assert statefulsets[0]["is_running"] is True


async def test_get_statefulsets_not_running(mock_client):
    """Test statefulsets retrieval for non-running statefulset."""
    # Mock the connection test to return True
    mock_client._test_connection = AsyncMock(return_value=True)

    # Mock the aiohttp method to return the expected statefulsets
    mock_statefulsets = [
        {
            "name": "api-statefulset",
            "namespace": "default",
            "replicas": 0,
            "available_replicas": 0,
            "ready_replicas": 0,
            "is_running": False,
        }
    ]
    mock_client._get_statefulsets_aiohttp = AsyncMock(return_value=mock_statefulsets)

    statefulsets = await mock_client.get_statefulsets()

    assert len(statefulsets) == 1
    assert statefulsets[0]["name"] == "api-statefulset"
    assert statefulsets[0]["is_running"] is False


async def test_get_statefulsets_empty(mock_client):
    """Test statefulsets retrieval when no statefulsets exist."""
    # Mock aiohttp session for connection test
    mock_conn_response = MagicMock()
    mock_conn_response.status = 200

    # Mock aiohttp session for statefulsets API call
    mock_statefulsets_response = MagicMock()
    mock_statefulsets_response.status = 200
    mock_statefulsets_response.json = AsyncMock(return_value={"items": []})

    mock_session = MagicMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mock_session.get = AsyncMock(
        side_effect=[mock_conn_response, mock_statefulsets_response]
    )

    with patch("aiohttp.ClientSession", return_value=mock_session):
        statefulsets = await mock_client.get_statefulsets()

    assert statefulsets == []


async def test_get_statefulsets_count_success(mock_client):
    """Test successful statefulsets count retrieval."""
    # Mock the connection test to return True
    mock_client._test_connection = AsyncMock(return_value=True)

    # Mock the aiohttp method to return the expected count
    mock_client._get_statefulsets_count_aiohttp = AsyncMock(return_value=3)

    count = await mock_client.get_statefulsets_count()

    assert count == 3


async def test_is_cluster_healthy_success(mock_client):
    """Test successful cluster health check."""
    # Mock the connection test to return True
    mock_client._test_connection = AsyncMock(return_value=True)

    # Mock the nodes count to return a positive number
    mock_client._get_nodes_count_aiohttp = AsyncMock(return_value=2)

    is_healthy = await mock_client.is_cluster_healthy()

    assert is_healthy is True


async def test_is_cluster_healthy_no_nodes(mock_client):
    """Test cluster health check when no nodes exist."""
    # Mock aiohttp session for connection test
    mock_conn_response = MagicMock()
    mock_conn_response.status = 200

    # Mock aiohttp session for nodes API call
    mock_nodes_response = MagicMock()
    mock_nodes_response.status = 200
    mock_nodes_response.json = AsyncMock(return_value={"items": []})

    mock_session = MagicMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mock_session.get = AsyncMock(side_effect=[mock_conn_response, mock_nodes_response])

    with patch("aiohttp.ClientSession", return_value=mock_session):
        is_healthy = await mock_client.is_cluster_healthy()

    assert is_healthy is False


async def test_is_cluster_healthy_unready_nodes(mock_client):
    """Test cluster health check when nodes are not ready."""
    # Mock aiohttp session for connection test
    mock_conn_response = MagicMock()
    mock_conn_response.status = 200

    # Mock aiohttp session for nodes API call
    mock_nodes_response = MagicMock()
    mock_nodes_response.status = 200
    mock_nodes_response.json = AsyncMock(
        return_value={
            "items": [
                {"status": {"conditions": [{"type": "Ready", "status": "False"}]}}
            ]
        }
    )

    mock_session = MagicMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mock_session.get = AsyncMock(side_effect=[mock_conn_response, mock_nodes_response])

    with patch("aiohttp.ClientSession", return_value=mock_session):
        is_healthy = await mock_client.is_cluster_healthy()

    assert is_healthy is False


async def test_scale_deployment_success(mock_client):
    """Test successful deployment scaling."""
    # Mock aiohttp session for connection test
    mock_conn_response = MagicMock()
    mock_conn_response.status = 200

    # Mock aiohttp session for deployment API calls
    mock_deployment_response = MagicMock()
    mock_deployment_response.status = 200
    mock_deployment_response.json = AsyncMock(
        return_value={"spec": {"replicas": 3}, "status": {"availableReplicas": 3}}
    )

    mock_patch_response = MagicMock()
    mock_patch_response.status = 200

    mock_session = MagicMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mock_session.get = AsyncMock(return_value=mock_deployment_response)
    mock_session.patch = AsyncMock(return_value=mock_patch_response)

    with patch("aiohttp.ClientSession", return_value=mock_session):
        result = await mock_client.scale_deployment("nginx-deployment", 5, "default")

    assert result is True


async def test_start_deployment_success(mock_client):
    """Test successful deployment start."""
    # Mock aiohttp session for connection test
    mock_conn_response = MagicMock()
    mock_conn_response.status = 200

    # Mock aiohttp session for deployment API calls
    mock_deployment_response = MagicMock()
    mock_deployment_response.status = 200
    mock_deployment_response.json = AsyncMock(
        return_value={"spec": {"replicas": 0}, "status": {"availableReplicas": 0}}
    )

    mock_patch_response = MagicMock()
    mock_patch_response.status = 200

    mock_session = MagicMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mock_session.get = AsyncMock(return_value=mock_deployment_response)
    mock_session.patch = AsyncMock(return_value=mock_patch_response)

    with patch("aiohttp.ClientSession", return_value=mock_session):
        result = await mock_client.start_deployment("nginx-deployment", 1, "default")

    assert result is True


async def test_stop_deployment_success(mock_client):
    """Test successful deployment stop."""
    # Mock aiohttp session for connection test
    mock_conn_response = MagicMock()
    mock_conn_response.status = 200

    # Mock aiohttp session for deployment API calls
    mock_deployment_response = MagicMock()
    mock_deployment_response.status = 200
    mock_deployment_response.json = AsyncMock(
        return_value={"spec": {"replicas": 3}, "status": {"availableReplicas": 3}}
    )

    mock_patch_response = MagicMock()
    mock_patch_response.status = 200

    mock_session = MagicMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mock_session.get = AsyncMock(return_value=mock_deployment_response)
    mock_session.patch = AsyncMock(return_value=mock_patch_response)

    with patch("aiohttp.ClientSession", return_value=mock_session):
        result = await mock_client.stop_deployment("nginx-deployment", "default")

    assert result is True


async def test_scale_statefulset_success(mock_client):
    """Test successful statefulset scaling."""
    # Mock aiohttp session for connection test
    mock_conn_response = MagicMock()
    mock_conn_response.status = 200

    # Mock aiohttp session for statefulset API calls
    mock_statefulset_response = MagicMock()
    mock_statefulset_response.status = 200
    mock_statefulset_response.json = AsyncMock(
        return_value={"spec": {"replicas": 3}, "status": {"availableReplicas": 3}}
    )

    mock_patch_response = MagicMock()
    mock_patch_response.status = 200

    mock_session = MagicMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mock_session.get = AsyncMock(return_value=mock_statefulset_response)
    mock_session.patch = AsyncMock(return_value=mock_patch_response)

    with patch("aiohttp.ClientSession", return_value=mock_session):
        result = await mock_client.scale_statefulset("redis-statefulset", 5, "default")

    assert result is True


async def test_start_statefulset_success(mock_client):
    """Test successful statefulset start."""
    # Mock aiohttp session for connection test
    mock_conn_response = MagicMock()
    mock_conn_response.status = 200

    # Mock aiohttp session for statefulset API calls
    mock_statefulset_response = MagicMock()
    mock_statefulset_response.status = 200
    mock_statefulset_response.json = AsyncMock(
        return_value={"spec": {"replicas": 0}, "status": {"availableReplicas": 0}}
    )

    mock_patch_response = MagicMock()
    mock_patch_response.status = 200

    mock_session = MagicMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mock_session.get = AsyncMock(return_value=mock_statefulset_response)
    mock_session.patch = AsyncMock(return_value=mock_patch_response)

    with patch("aiohttp.ClientSession", return_value=mock_session):
        result = await mock_client.start_statefulset("redis-statefulset", 1, "default")

    assert result is True


async def test_stop_statefulset_success(mock_client):
    """Test successful statefulset stop."""
    # Mock aiohttp session for connection test
    mock_conn_response = MagicMock()
    mock_conn_response.status = 200

    # Mock aiohttp session for statefulset API calls
    mock_statefulset_response = MagicMock()
    mock_statefulset_response.status = 200
    mock_statefulset_response.json = AsyncMock(
        return_value={"spec": {"replicas": 3}, "status": {"availableReplicas": 3}}
    )

    mock_patch_response = MagicMock()
    mock_patch_response.status = 200

    mock_session = MagicMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mock_session.get = AsyncMock(return_value=mock_statefulset_response)
    mock_session.patch = AsyncMock(return_value=mock_patch_response)

    with patch("aiohttp.ClientSession", return_value=mock_session):
        result = await mock_client.stop_statefulset("redis-statefulset", "default")

    assert result is True


async def test_scale_deployment_api_exception(mock_client):
    """Test deployment scaling when API raises exception."""
    from kubernetes.client.rest import ApiException

    mock_client._apps_api.read_namespaced_deployment.side_effect = ApiException(
        status=404, reason="Not Found"
    )

    result = await mock_client.scale_deployment("nginx-deployment", 5, "default")

    assert result is False


async def test_start_deployment_api_exception(mock_client):
    """Test deployment start when API raises exception."""
    from kubernetes.client.rest import ApiException

    mock_client._apps_api.read_namespaced_deployment.side_effect = ApiException(
        status=404, reason="Not Found"
    )

    result = await mock_client.start_deployment("nginx-deployment", 1, "default")

    assert result is False


async def test_stop_deployment_api_exception(mock_client):
    """Test deployment stop when API raises exception."""
    from kubernetes.client.rest import ApiException

    mock_client._apps_api.read_namespaced_deployment.side_effect = ApiException(
        status=404, reason="Not Found"
    )

    result = await mock_client.stop_deployment("nginx-deployment", "default")

    assert result is False


async def test_scale_statefulset_api_exception(mock_client):
    """Test statefulset scaling when API raises exception."""
    from kubernetes.client.rest import ApiException

    mock_client._apps_api.read_namespaced_stateful_set.side_effect = ApiException(
        status=404, reason="Not Found"
    )

    result = await mock_client.scale_statefulset("redis-statefulset", 5, "default")

    assert result is False


async def test_start_statefulset_api_exception(mock_client):
    """Test statefulset start when API raises exception."""
    from kubernetes.client.rest import ApiException

    mock_client._apps_api.read_namespaced_stateful_set.side_effect = ApiException(
        status=404, reason="Not Found"
    )

    result = await mock_client.start_statefulset("redis-statefulset", 1, "default")

    assert result is False


async def test_stop_statefulset_api_exception(mock_client):
    """Test statefulset stop when API raises exception."""
    from kubernetes.client.rest import ApiException

    mock_client._apps_api.read_namespaced_stateful_set.side_effect = ApiException(
        status=404, reason="Not Found"
    )

    result = await mock_client.stop_statefulset("redis-statefulset", "default")

    assert result is False
