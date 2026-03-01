"""Tests for the Kubernetes integration client."""

from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
from kubernetes.client import ApiException
import pytest

from custom_components.kubernetes.kubernetes_client import (
    KubernetesClient,
    ResourceVersionExpired,
)


@pytest.fixture
def mock_config():
    """Mock configuration data."""
    return {
        "host": "https://kubernetes.example.com",
        "port": 6443,
        "api_token": "test-token",
        "namespace": "default",
        "verify_ssl": True,
        "monitor_all_namespaces": False,
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


async def test_get_daemonsets_count_success(mock_client):
    """Test successful daemonsets count retrieval."""
    # Mock the connection test to return True
    mock_client._test_connection = AsyncMock(return_value=True)

    # Mock the aiohttp method to return the expected count
    mock_client._get_daemonsets_count_aiohttp = AsyncMock(return_value=2)

    count = await mock_client.get_daemonsets_count()

    assert count == 2


async def test_get_daemonsets_count_all_namespaces(mock_client):
    """Test daemonsets count retrieval for all namespaces."""
    mock_client.monitor_all_namespaces = True
    mock_client._test_connection = AsyncMock(return_value=True)
    mock_client._get_daemonsets_count_all_namespaces_aiohttp = AsyncMock(return_value=5)

    count = await mock_client.get_daemonsets_count()

    assert count == 5
    mock_client._get_daemonsets_count_all_namespaces_aiohttp.assert_called_once()


async def test_get_daemonsets_success(mock_client):
    """Test successful daemonsets retrieval."""
    mock_client._test_connection = AsyncMock(return_value=True)
    mock_client._get_daemonsets_aiohttp = AsyncMock(
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

    daemonsets = await mock_client.get_daemonsets()

    assert len(daemonsets) == 1
    assert daemonsets[0]["name"] == "kube-proxy"
    assert daemonsets[0]["number_ready"] == 3


async def test_get_daemonsets_all_namespaces(mock_client):
    """Test daemonsets retrieval for all namespaces."""
    mock_client.monitor_all_namespaces = True
    mock_client._test_connection = AsyncMock(return_value=True)
    mock_client._get_daemonsets_all_namespaces_aiohttp = AsyncMock(
        return_value=[
            {
                "name": "kube-proxy",
                "namespace": "kube-system",
                "desired_number_scheduled": 3,
                "current_number_scheduled": 3,
                "number_ready": 3,
                "number_available": 3,
                "is_running": True,
            },
            {
                "name": "fluentd",
                "namespace": "default",
                "desired_number_scheduled": 2,
                "current_number_scheduled": 2,
                "number_ready": 2,
                "number_available": 2,
                "is_running": True,
            },
        ]
    )

    daemonsets = await mock_client.get_daemonsets()

    assert len(daemonsets) == 2
    mock_client._get_daemonsets_all_namespaces_aiohttp.assert_called_once()


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


# CronJob Tests
async def test_get_cronjobs_count_success(mock_client):
    """Test successful CronJobs count retrieval."""
    # Mock the batch API
    mock_batch_api = MagicMock()
    mock_batch_api.list_namespaced_cron_job.return_value = MagicMock(items=[1, 2, 3])
    mock_client.batch_v1 = mock_batch_api

    count = await mock_client.get_cronjobs_count()

    assert count == 3
    mock_batch_api.list_namespaced_cron_job.assert_called_once_with("default")


async def test_get_cronjobs_count_empty(mock_client):
    """Test CronJobs count retrieval when no CronJobs exist."""
    mock_batch_api = MagicMock()
    mock_batch_api.list_namespaced_cron_job.return_value = MagicMock(items=[])
    mock_client.batch_v1 = mock_batch_api

    count = await mock_client.get_cronjobs_count()

    assert count == 0


async def test_get_cronjobs_count_all_namespaces(mock_client):
    """Test CronJobs count retrieval for all namespaces."""
    mock_client.monitor_all_namespaces = True
    # Mock the aiohttp method since we now use it directly
    mock_client._get_cronjobs_count_all_namespaces_aiohttp = AsyncMock(return_value=2)

    count = await mock_client.get_cronjobs_count()

    assert count == 2
    mock_client._get_cronjobs_count_all_namespaces_aiohttp.assert_called_once()


async def test_get_cronjobs_count_api_exception(mock_client):
    """Test CronJobs count retrieval when API raises exception."""
    # Mock the Kubernetes client to raise an exception
    mock_client.batch_v1.list_namespaced_cron_job.side_effect = Exception("API Error")

    # Mock aiohttp fallback
    mock_client._get_cronjobs_count_aiohttp = AsyncMock(return_value=2)

    count = await mock_client.get_cronjobs_count()

    assert count == 2


async def test_get_cronjobs_success(mock_client):
    """Test successful CronJobs retrieval."""
    # Mock CronJob objects
    mock_cronjob1 = MagicMock()
    mock_cronjob1.metadata.name = "backup-job"
    mock_cronjob1.metadata.namespace = "default"
    mock_cronjob1.metadata.uid = "uid-1"
    mock_cronjob1.metadata.creation_timestamp = MagicMock()
    mock_cronjob1.metadata.creation_timestamp.isoformat.return_value = (
        "2023-01-01T00:00:00Z"
    )
    mock_cronjob1.spec.schedule = "0 2 * * *"
    mock_cronjob1.spec.suspend = False
    mock_cronjob1.spec.successful_jobs_history_limit = 3
    mock_cronjob1.spec.failed_jobs_history_limit = 1
    mock_cronjob1.spec.concurrency_policy = "Allow"
    mock_cronjob1.status.last_schedule_time = MagicMock()
    mock_cronjob1.status.last_schedule_time.isoformat.return_value = (
        "2023-01-01T02:00:00Z"
    )
    mock_cronjob1.status.next_schedule_time = MagicMock()
    mock_cronjob1.status.next_schedule_time.isoformat.return_value = (
        "2023-01-02T02:00:00Z"
    )
    mock_cronjob1.status.active = [MagicMock(), MagicMock()]

    mock_cronjob2 = MagicMock()
    mock_cronjob2.metadata.name = "cleanup-job"
    mock_cronjob2.metadata.namespace = "default"
    mock_cronjob2.metadata.uid = "uid-2"
    mock_cronjob2.metadata.creation_timestamp = MagicMock()
    mock_cronjob2.metadata.creation_timestamp.isoformat.return_value = (
        "2023-01-01T00:00:00Z"
    )
    mock_cronjob2.spec.schedule = "0 3 * * *"
    mock_cronjob2.spec.suspend = True
    mock_cronjob2.spec.successful_jobs_history_limit = 5
    mock_cronjob2.spec.failed_jobs_history_limit = 2
    mock_cronjob2.spec.concurrency_policy = "Forbid"
    mock_cronjob2.status.last_schedule_time = None
    mock_cronjob2.status.next_schedule_time = None
    mock_cronjob2.status.active = []

    mock_batch_api = MagicMock()
    mock_batch_api.list_namespaced_cron_job.return_value = MagicMock(
        items=[mock_cronjob1, mock_cronjob2]
    )
    mock_client.batch_v1 = mock_batch_api

    cronjobs = await mock_client.get_cronjobs()

    assert len(cronjobs) == 2
    assert cronjobs[0]["name"] == "backup-job"
    assert cronjobs[0]["schedule"] == "0 2 * * *"
    assert cronjobs[0]["suspend"] is False
    assert cronjobs[0]["active_jobs_count"] == 2
    assert cronjobs[0]["last_schedule_time"] == "2023-01-01T02:00:00Z"
    assert cronjobs[0]["next_schedule_time"] == "2023-01-02T02:00:00Z"
    assert cronjobs[0]["successful_jobs_history_limit"] == 3
    assert cronjobs[0]["failed_jobs_history_limit"] == 1
    assert cronjobs[0]["concurrency_policy"] == "Allow"

    assert cronjobs[1]["name"] == "cleanup-job"
    assert cronjobs[1]["schedule"] == "0 3 * * *"
    assert cronjobs[1]["suspend"] is True
    assert cronjobs[1]["active_jobs_count"] == 0
    assert cronjobs[1]["last_schedule_time"] is None
    assert cronjobs[1]["next_schedule_time"] is None
    assert cronjobs[1]["successful_jobs_history_limit"] == 5
    assert cronjobs[1]["failed_jobs_history_limit"] == 2
    assert cronjobs[1]["concurrency_policy"] == "Forbid"


async def test_get_cronjobs_all_namespaces(mock_client):
    """Test CronJobs retrieval for all namespaces."""
    mock_client.monitor_all_namespaces = True
    # Mock the aiohttp method since we now use it directly
    mock_client._get_cronjobs_all_namespaces_aiohttp = AsyncMock(return_value=[])

    cronjobs = await mock_client.get_cronjobs()

    assert len(cronjobs) == 0
    mock_client._get_cronjobs_all_namespaces_aiohttp.assert_called_once()


async def test_get_cronjobs_api_exception(mock_client):
    """Test CronJobs retrieval when API raises exception."""
    # Mock aiohttp fallback
    mock_client._get_cronjobs_aiohttp = AsyncMock(return_value=[])

    cronjobs = await mock_client.get_cronjobs()

    assert len(cronjobs) == 0


async def test_trigger_cronjob_success(mock_client):
    """Test successful CronJob triggering."""
    # Mock the aiohttp method since we now use it first
    mock_client._trigger_cronjob_aiohttp = AsyncMock(
        return_value={
            "success": True,
            "cronjob_name": "backup-job",
            "namespace": "default",
            "job_uid": "job-uid-123",
            "job_name": "backup-job-manual-1234567890",
        }
    )

    result = await mock_client.trigger_cronjob("backup-job", "default")

    assert result["success"] is True
    assert result["cronjob_name"] == "backup-job"
    assert result["namespace"] == "default"
    assert result["job_uid"] == "job-uid-123"
    assert "job_name" in result
    assert result["job_name"].startswith("backup-job-manual-")

    # Verify the aiohttp method was called
    mock_client._trigger_cronjob_aiohttp.assert_called_once_with(
        "backup-job", "default"
    )


async def test_trigger_cronjob_api_exception(mock_client):
    """Test CronJob triggering when API raises exception."""
    # Mock the aiohttp method to fail
    mock_client._trigger_cronjob_aiohttp = AsyncMock(
        return_value={
            "success": False,
            "cronjob_name": "nonexistent-job",
            "namespace": "default",
            "error": "Failed to get CronJob 'nonexistent-job' via aiohttp: HTTP 404",
        }
    )

    result = await mock_client.trigger_cronjob("nonexistent-job", "default")

    assert result["success"] is False
    assert result["cronjob_name"] == "nonexistent-job"
    assert result["namespace"] == "default"
    assert "error" in result
    assert "404" in result["error"]


async def test_trigger_cronjob_general_exception(mock_client):
    """Test CronJob triggering when general exception occurs."""
    # Mock the aiohttp method to fail
    mock_client._trigger_cronjob_aiohttp = AsyncMock(
        return_value={
            "success": False,
            "cronjob_name": "backup-job",
            "namespace": "default",
            "error": "Failed to trigger CronJob 'backup-job' via aiohttp: Connection error",
        }
    )

    result = await mock_client.trigger_cronjob("backup-job", "default")

    assert result["success"] is False
    assert result["cronjob_name"] == "backup-job"
    assert result["namespace"] == "default"
    assert "error" in result
    assert "Connection error" in result["error"]


async def test_trigger_cronjob_default_namespace(mock_client):
    """Test CronJob triggering with default namespace."""
    # Mock the aiohttp method since we now use it first
    mock_client._trigger_cronjob_aiohttp = AsyncMock(
        return_value={
            "success": True,
            "cronjob_name": "backup-job",
            "namespace": "default",
            "job_uid": "job-uid-123",
            "job_name": "backup-job-manual-1234567890",
        }
    )

    result = await mock_client.trigger_cronjob("backup-job")

    assert result["success"] is True
    assert result["namespace"] == "default"  # Should use client's default namespace
    # Verify the aiohttp method was called with default namespace
    mock_client._trigger_cronjob_aiohttp.assert_called_once_with(
        "backup-job", "default"
    )


async def test_scale_deployment_api_exception(mock_client):
    """Test deployment scaling when API raises exception."""
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


class TestKubernetesClientCronJobOperations:
    """Test CronJob operations in Kubernetes client."""

    async def test_suspend_cronjob_success(self, mock_client):
        """Test successful CronJob suspension."""
        # Mock the aiohttp method since we now use it first
        mock_client._suspend_cronjob_aiohttp = AsyncMock(
            return_value={
                "success": True,
                "cronjob_name": "test-cronjob",
                "namespace": "default",
            }
        )

        # Execute
        result = await mock_client.suspend_cronjob("test-cronjob", "default")

        # Verify
        assert result["success"] is True
        assert result["cronjob_name"] == "test-cronjob"
        assert result["namespace"] == "default"

        # Verify the aiohttp method was called
        mock_client._suspend_cronjob_aiohttp.assert_called_once_with(
            "test-cronjob", "default"
        )

    async def test_suspend_cronjob_namespace_permission_error(self, mock_client):
        """Test CronJob suspension with namespace permission error."""
        # Test with different namespace when monitor_all_namespaces is False
        result = await mock_client.suspend_cronjob("test-cronjob", "other-namespace")

        # Verify
        assert result["success"] is False
        assert "Cannot suspend CronJob" in result["error"]
        assert (
            "monitor_all_namespaces" in result["error"]
            or "namespace(s)" in result["error"]
        )

    async def test_suspend_cronjob_api_exception(self, mock_client):
        """Test CronJob suspension with API exception."""
        # Mock the aiohttp method to fail
        mock_client._suspend_cronjob_aiohttp = AsyncMock(
            return_value={
                "success": False,
                "cronjob_name": "test-cronjob",
                "namespace": "default",
                "error": "Failed to suspend CronJob 'test-cronjob' via aiohttp: HTTP 404",
            }
        )

        # Execute
        result = await mock_client.suspend_cronjob("test-cronjob", "default")

        # Verify
        assert result["success"] is False
        assert "Failed to suspend CronJob" in result["error"]
        assert "404" in result["error"]

    async def test_suspend_cronjob_general_exception(self, mock_client):
        """Test CronJob suspension with general exception."""
        # Mock the aiohttp method to fail
        mock_client._suspend_cronjob_aiohttp = AsyncMock(
            return_value={
                "success": False,
                "cronjob_name": "test-cronjob",
                "namespace": "default",
                "error": "Failed to suspend CronJob 'test-cronjob' via aiohttp: Network error",
            }
        )

        # Execute
        result = await mock_client.suspend_cronjob("test-cronjob", "default")

        # Verify
        assert result["success"] is False
        assert "Failed to suspend CronJob" in result["error"]
        assert "Network error" in result["error"]

    async def test_suspend_cronjob_default_namespace(self, mock_client):
        """Test CronJob suspension with default namespace."""
        # Mock the aiohttp method since we now use it first
        mock_client._suspend_cronjob_aiohttp = AsyncMock(
            return_value={
                "success": True,
                "cronjob_name": "test-cronjob",
                "namespace": "default",
            }
        )

        # Execute without specifying namespace
        result = await mock_client.suspend_cronjob("test-cronjob")

        # Verify
        assert result["success"] is True
        assert result["namespace"] == "default"

        # Verify the aiohttp method was called with default namespace
        mock_client._suspend_cronjob_aiohttp.assert_called_once_with(
            "test-cronjob", "default"
        )

    async def test_resume_cronjob_success(self, mock_client):
        """Test successful CronJob resume."""
        # Mock the aiohttp method since we now use it first
        mock_client._resume_cronjob_aiohttp = AsyncMock(
            return_value={
                "success": True,
                "cronjob_name": "test-cronjob",
                "namespace": "default",
            }
        )

        # Execute
        result = await mock_client.resume_cronjob("test-cronjob", "default")

        # Verify
        assert result["success"] is True
        assert result["cronjob_name"] == "test-cronjob"
        assert result["namespace"] == "default"

        # Verify the aiohttp method was called
        mock_client._resume_cronjob_aiohttp.assert_called_once_with(
            "test-cronjob", "default"
        )

    async def test_resume_cronjob_namespace_permission_error(self, mock_client):
        """Test CronJob resume with namespace permission error."""
        # Test with different namespace when monitor_all_namespaces is False
        result = await mock_client.resume_cronjob("test-cronjob", "other-namespace")

        # Verify
        assert result["success"] is False
        assert "Cannot resume CronJob" in result["error"]
        assert (
            "monitor_all_namespaces" in result["error"]
            or "namespace(s)" in result["error"]
        )

    async def test_suspend_cronjob_namespace_permission_error_multiple_namespaces(
        self, mock_client
    ):
        """Test CronJob suspension with namespace permission error when multiple namespaces are configured."""
        # Configure client with multiple namespaces
        mock_client.namespaces = ["default", "kube-system", "production"]
        mock_client.monitor_all_namespaces = False

        # Test with namespace not in the list
        result = await mock_client.suspend_cronjob("test-cronjob", "other-namespace")

        # Verify
        assert result["success"] is False
        assert "Cannot suspend CronJob" in result["error"]
        assert "namespace(s)" in result["error"]
        # Verify all namespaces are listed in the error message
        assert "default" in result["error"]
        assert "kube-system" in result["error"]
        assert "production" in result["error"]

    async def test_resume_cronjob_namespace_permission_error_multiple_namespaces(
        self, mock_client
    ):
        """Test CronJob resume with namespace permission error when multiple namespaces are configured."""
        # Configure client with multiple namespaces
        mock_client.namespaces = ["default", "kube-system", "production"]
        mock_client.monitor_all_namespaces = False

        # Test with namespace not in the list
        result = await mock_client.resume_cronjob("test-cronjob", "other-namespace")

        # Verify
        assert result["success"] is False
        assert "Cannot resume CronJob" in result["error"]
        assert "namespace(s)" in result["error"]
        # Verify all namespaces are listed in the error message
        assert "default" in result["error"]
        assert "kube-system" in result["error"]
        assert "production" in result["error"]

    async def test_resume_cronjob_api_exception(self, mock_client):
        """Test CronJob resume with API exception."""
        # Mock the aiohttp method to fail
        mock_client._resume_cronjob_aiohttp = AsyncMock(
            return_value={
                "success": False,
                "cronjob_name": "test-cronjob",
                "namespace": "default",
                "error": "Failed to resume CronJob 'test-cronjob' via aiohttp: HTTP 404",
            }
        )

        # Execute
        result = await mock_client.resume_cronjob("test-cronjob", "default")

        # Verify
        assert result["success"] is False
        assert "Failed to resume CronJob" in result["error"]
        assert "404" in result["error"]

    async def test_resume_cronjob_general_exception(self, mock_client):
        """Test CronJob resume with general exception."""
        # Mock the aiohttp method to fail
        mock_client._resume_cronjob_aiohttp = AsyncMock(
            return_value={
                "success": False,
                "cronjob_name": "test-cronjob",
                "namespace": "default",
                "error": "Failed to resume CronJob 'test-cronjob' via aiohttp: Network error",
            }
        )

        # Execute
        result = await mock_client.resume_cronjob("test-cronjob", "default")

        # Verify
        assert result["success"] is False
        assert "Failed to resume CronJob" in result["error"]
        assert "Network error" in result["error"]

    async def test_resume_cronjob_default_namespace(self, mock_client):
        """Test CronJob resume with default namespace."""
        # Mock the aiohttp method since we now use it first
        mock_client._resume_cronjob_aiohttp = AsyncMock(
            return_value={
                "success": True,
                "cronjob_name": "test-cronjob",
                "namespace": "default",
            }
        )

        # Execute without specifying namespace
        result = await mock_client.resume_cronjob("test-cronjob")

        # Verify
        assert result["success"] is True
        assert result["namespace"] == "default"

        # Verify the aiohttp method was called with default namespace
        mock_client._resume_cronjob_aiohttp.assert_called_once_with(
            "test-cronjob", "default"
        )

    async def test_suspend_cronjob_with_monitor_all_namespaces(self, mock_config):
        """Test CronJob suspension when monitor_all_namespaces is True."""
        # Update config to allow all namespaces
        mock_config["monitor_all_namespaces"] = True

        with patch("kubernetes.config"):
            with patch("kubernetes.client") as mock_client_module:
                # Mock the Kubernetes client
                mock_apps_v1 = MagicMock()
                mock_core_v1 = MagicMock()
                mock_batch_v1 = MagicMock()

                mock_client_module.AppsV1Api.return_value = mock_apps_v1
                mock_client_module.CoreV1Api.return_value = mock_core_v1
                mock_client_module.BatchV1Api.return_value = mock_batch_v1

                client = KubernetesClient(mock_config)
                client.apps_v1 = mock_apps_v1
                client.core_v1 = mock_core_v1
                client.batch_v1 = mock_batch_v1

                # Mock the aiohttp method since we now use it first
                client._suspend_cronjob_aiohttp = AsyncMock(
                    return_value={
                        "success": True,
                        "cronjob_name": "test-cronjob",
                        "namespace": "other-namespace",
                    }
                )

                # Execute with different namespace
                result = await client.suspend_cronjob("test-cronjob", "other-namespace")

                # Verify
                assert result["success"] is True
                assert result["namespace"] == "other-namespace"

                # Verify the aiohttp method was called with the specified namespace
                client._suspend_cronjob_aiohttp.assert_called_once_with(
                    "test-cronjob", "other-namespace"
                )

    async def test_resume_cronjob_with_monitor_all_namespaces(self, mock_config):
        """Test CronJob resume when monitor_all_namespaces is True."""
        # Update config to allow all namespaces
        mock_config["monitor_all_namespaces"] = True

        with patch("kubernetes.config"):
            with patch("kubernetes.client") as mock_client_module:
                # Mock the Kubernetes client
                mock_apps_v1 = MagicMock()
                mock_core_v1 = MagicMock()
                mock_batch_v1 = MagicMock()

                mock_client_module.AppsV1Api.return_value = mock_apps_v1
                mock_client_module.CoreV1Api.return_value = mock_core_v1
                mock_client_module.BatchV1Api.return_value = mock_batch_v1

                client = KubernetesClient(mock_config)
                client.apps_v1 = mock_apps_v1
                client.core_v1 = mock_core_v1
                client.batch_v1 = mock_batch_v1

                # Mock the aiohttp method since we now use it first
                client._resume_cronjob_aiohttp = AsyncMock(
                    return_value={
                        "success": True,
                        "cronjob_name": "test-cronjob",
                        "namespace": "other-namespace",
                    }
                )

                # Execute with different namespace
                result = await client.resume_cronjob("test-cronjob", "other-namespace")

                # Verify
                assert result["success"] is True
                assert result["namespace"] == "other-namespace"

                # Verify the aiohttp method was called with the specified namespace
                client._resume_cronjob_aiohttp.assert_called_once_with(
                    "test-cronjob", "other-namespace"
                )


def test_parse_memory(mock_client):
    """Test memory parsing."""
    # Binary prefixes
    assert mock_client._parse_memory("1Ki", "KiB") == 1.0
    assert mock_client._parse_memory("1Mi", "MiB") == 1.0
    assert mock_client._parse_memory("1Gi", "GiB") == 1.0

    # Decimal prefixes
    assert mock_client._parse_memory("1k", "KiB") == 0.98  # 1000/1024
    assert mock_client._parse_memory("1M", "MiB") == 0.95  # 1000^2/1024^2

    # Bytes
    assert mock_client._parse_memory("1024", "KiB") == 1.0

    # Default output type (MiB)
    assert mock_client._parse_memory("1Gi") == 1024.0


def test_parse_cpu(mock_client):
    """Test CPU parsing."""
    # Nanocores
    assert mock_client._parse_cpu("1000000000n", "cores") == 1.0

    # Microcores
    assert mock_client._parse_cpu("1000000u", "cores") == 1.0

    # Millicores
    assert mock_client._parse_cpu("1000m", "cores") == 1.0

    # Cores
    assert mock_client._parse_cpu("1", "cores") == 1.0

    # Output types
    assert mock_client._parse_cpu("1", "m") == 1000.0
    assert mock_client._parse_cpu("1000m", "m") == 1000.0


async def test_enrich_deployments_with_metrics(mock_client):
    """Test enriching deployments with metrics."""
    deployments = [
        {
            "name": "test-deployment",
            "namespace": "default",
            "selector": {"app": "test"},
        }
    ]

    mock_client._get_pods_aiohttp = AsyncMock(
        return_value=[
            {
                "name": "test-pod",
                "namespace": "default",
                "labels": {"app": "test"},
            }
        ]
    )

    mock_client._get_pod_metrics_aiohttp = AsyncMock(
        return_value={"default/test-pod": {"cpu": 0.5, "memory": 128.0}}
    )

    await mock_client._enrich_deployments_with_metrics(deployments)

    assert deployments[0]["cpu_usage"] == 0.5
    assert deployments[0]["memory_usage"] == 128.0


async def test_enrich_statefulsets_with_metrics(mock_client):
    """Test enriching statefulsets with metrics."""
    statefulsets = [
        {
            "name": "test-statefulset",
            "namespace": "default",
            "selector": {"app": "test"},
        }
    ]

    mock_client._get_pods_aiohttp = AsyncMock(
        return_value=[
            {
                "name": "test-pod",
                "namespace": "default",
                "labels": {"app": "test"},
            }
        ]
    )

    mock_client._get_pod_metrics_aiohttp = AsyncMock(
        return_value={"default/test-pod": {"cpu": 0.5, "memory": 128.0}}
    )

    await mock_client._enrich_statefulsets_with_metrics(statefulsets)

    assert statefulsets[0]["cpu_usage"] == 0.5
    assert statefulsets[0]["memory_usage"] == 128.0


@pytest.fixture
def extended_client(mock_config):
    """Create a Kubernetes client instance for extended tests."""
    with (
        patch("kubernetes.client.Configuration"),
        patch("kubernetes.client.ApiClient"),
        patch("kubernetes.client.CoreV1Api"),
        patch("kubernetes.client.AppsV1Api"),
        patch("kubernetes.client.BatchV1Api"),
    ):
        return KubernetesClient(mock_config)


class TestKubernetesClientExtended:
    """Extended tests for Kubernetes client."""

    def test_log_error(self, extended_client):
        """Test _log_error method with various exceptions."""
        # Test ApiException 401 (Auth)
        error_401 = ApiException(status=401, reason="Unauthorized")
        with patch(
            "custom_components.kubernetes.kubernetes_client._LOGGER"
        ) as mock_logger:
            extended_client._log_error("test_op", error_401)
            mock_logger.error.assert_called()

            # Test deduplication (should be debug)
            extended_client._log_error("test_op", error_401)
            mock_logger.debug.assert_called()

        # Test ApiException 403 (Forbidden)
        error_403 = ApiException(status=403, reason="Forbidden")
        with patch(
            "custom_components.kubernetes.kubernetes_client._LOGGER"
        ) as mock_logger:
            extended_client._log_error("test_op", error_403)
            mock_logger.error.assert_called()

        # Test ApiException 404 (Not Found)
        error_404 = ApiException(status=404, reason="Not Found")
        with patch(
            "custom_components.kubernetes.kubernetes_client._LOGGER"
        ) as mock_logger:
            extended_client._log_error("test_op", error_404)
            mock_logger.error.assert_called()

        # Test ApiException 500 (Server Error)
        error_500 = ApiException(status=500, reason="Server Error")
        with patch(
            "custom_components.kubernetes.kubernetes_client._LOGGER"
        ) as mock_logger:
            extended_client._log_error("test_op", error_500)
            mock_logger.error.assert_called()

        # Test aiohttp.ClientError
        error_aiohttp = aiohttp.ClientError("Network error")
        with patch(
            "custom_components.kubernetes.kubernetes_client._LOGGER"
        ) as mock_logger:
            extended_client._log_error("test_op", error_aiohttp)
            mock_logger.error.assert_called()

        # Test asyncio.TimeoutError
        error_timeout = TimeoutError()
        with patch(
            "custom_components.kubernetes.kubernetes_client._LOGGER"
        ) as mock_logger:
            extended_client._log_error("test_op", error_timeout)
            mock_logger.error.assert_called()

        # Test generic Exception
        error_generic = Exception("Generic error")
        with patch(
            "custom_components.kubernetes.kubernetes_client._LOGGER"
        ) as mock_logger:
            extended_client._log_error("test_op", error_generic)
            mock_logger.error.assert_called()

    async def test_test_connection_aiohttp_failure(self, extended_client):
        """Test _test_connection_aiohttp failure scenarios."""
        # Test non-200 status
        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 401
            mock_get.return_value.__aenter__.return_value = mock_response

            assert await extended_client._test_connection_aiohttp() is False

        # Test exception
        with patch(
            "aiohttp.ClientSession.get", side_effect=Exception("Connection error")
        ):
            assert await extended_client._test_connection_aiohttp() is False

    async def test_get_pods_count_aiohttp_failure(self, extended_client):
        """Test _get_pods_count_aiohttp failure scenarios."""
        # Test non-200 status
        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 500
            mock_get.return_value.__aenter__.return_value = mock_response

            assert await extended_client._get_pods_count_aiohttp() == 0

        # Test exception
        with patch("aiohttp.ClientSession.get", side_effect=Exception("Network error")):
            assert await extended_client._get_pods_count_aiohttp() == 0

    async def test_get_pods_count_all_namespaces_aiohttp_failure(self, extended_client):
        """Test _get_pods_count_all_namespaces_aiohttp failure scenarios."""
        # Test non-200 status
        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 500
            mock_get.return_value.__aenter__.return_value = mock_response

            assert await extended_client._get_pods_count_all_namespaces_aiohttp() == 0

        # Test exception
        with patch("aiohttp.ClientSession.get", side_effect=Exception("Network error")):
            assert await extended_client._get_pods_count_all_namespaces_aiohttp() == 0

    async def test_get_nodes_count_aiohttp_failure(self, extended_client):
        """Test _get_nodes_count_aiohttp failure scenarios."""
        # Test non-200 status
        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 500
            mock_get.return_value.__aenter__.return_value = mock_response

            assert await extended_client._get_nodes_count_aiohttp() == 0

        # Test exception
        with patch("aiohttp.ClientSession.get", side_effect=Exception("Network error")):
            assert await extended_client._get_nodes_count_aiohttp() == 0

    async def test_get_nodes_aiohttp_parsing(self, extended_client):
        """Test _get_nodes_aiohttp parsing logic."""
        mock_node_data = {
            "items": [
                {
                    "metadata": {
                        "name": "node1",
                        "creationTimestamp": "2023-01-01T00:00:00Z",
                    },
                    "status": {
                        "conditions": [{"type": "Ready", "status": "True"}],
                        "addresses": [
                            {"type": "InternalIP", "address": "10.0.0.1"},
                            {"type": "ExternalIP", "address": "1.2.3.4"},
                        ],
                        "capacity": {"memory": "16Gi", "cpu": "4"},
                        "allocatable": {"memory": "15Gi", "cpu": "4"},
                        "nodeInfo": {
                            "osImage": "Linux",
                            "kernelVersion": "5.15",
                            "containerRuntimeVersion": "docker",
                            "kubeletVersion": "v1.25",
                        },
                    },
                    "spec": {"unschedulable": False},
                }
            ]
        }

        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = mock_node_data
            mock_get.return_value.__aenter__.return_value = mock_response

            nodes = await extended_client._get_nodes_aiohttp()
            assert len(nodes) == 1
            node = nodes[0]
            assert node["name"] == "node1"
            assert node["status"] == "Ready"
            assert node["internal_ip"] == "10.0.0.1"
            assert node["external_ip"] == "1.2.3.4"
            assert node["schedulable"] is True

    async def test_get_nodes_aiohttp_parsing_error(self, extended_client):
        """Test _get_nodes_aiohttp parsing error handling."""
        # Malformed data that causes parsing error
        mock_node_data = {"items": [{"metadata": {}}]}  # Missing status, spec, etc.

        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = mock_node_data
            mock_get.return_value.__aenter__.return_value = mock_response

            # Should handle parsing error gracefully and return a node with "unknown" status
            nodes = await extended_client._get_nodes_aiohttp()
            assert len(nodes) == 1
            assert nodes[0]["name"] == "unknown"
            assert nodes[0]["status"] == "NotReady"

    async def test_get_nodes_aiohttp_failure(self, extended_client):
        """Test _get_nodes_aiohttp failure scenarios."""
        # Test non-200 status
        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 500
            mock_get.return_value.__aenter__.return_value = mock_response

            assert await extended_client._get_nodes_aiohttp() == []

        # Test exception
        with patch("aiohttp.ClientSession.get", side_effect=Exception("Network error")):
            assert await extended_client._get_nodes_aiohttp() == []


class TestKubernetesClientGetPods:
    """Test cases for Kubernetes client get_pods method."""

    @pytest.mark.asyncio
    async def test_get_pods_success(self, mock_client):
        """Test successful get_pods call."""
        # Mock the aiohttp response
        mock_response_data = {
            "items": [
                {
                    "metadata": {
                        "name": "test-pod-1",
                        "namespace": "default",
                        "uid": "pod-uid-1",
                        "creationTimestamp": "2023-01-01T00:00:00Z",
                        "labels": {"app": "test-app", "version": "v1.0"},
                    },
                    "spec": {"nodeName": "worker-node-1"},
                    "status": {
                        "phase": "Running",
                        "podIP": "10.244.1.5",
                        "containerStatuses": [
                            {"ready": True, "restartCount": 0},
                            {"ready": True, "restartCount": 0},
                        ],
                    },
                },
                {
                    "metadata": {
                        "name": "test-pod-2",
                        "namespace": "default",
                        "uid": "pod-uid-2",
                        "creationTimestamp": "2023-01-01T00:00:00Z",
                        "labels": {"app": "test-app-2"},
                        "ownerReferences": [
                            {"kind": "ReplicaSet", "name": "test-app-2-7d4b8c9f6b"}
                        ],
                    },
                    "spec": {"nodeName": "worker-node-2"},
                    "status": {
                        "phase": "Pending",
                        "podIP": "10.244.1.6",
                        "containerStatuses": [{"ready": False, "restartCount": 1}],
                    },
                },
            ]
        }

        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_get.return_value.__aenter__.return_value = mock_response

            result = await mock_client.get_pods()

            assert len(result) == 2

            # Check first pod
            pod1 = result[0]
            assert pod1["name"] == "test-pod-1"
            assert pod1["namespace"] == "default"
            assert pod1["phase"] == "Running"
            assert pod1["ready_containers"] == 2
            assert pod1["total_containers"] == 2
            assert pod1["restart_count"] == 0
            assert pod1["node_name"] == "worker-node-1"
            assert pod1["pod_ip"] == "10.244.1.5"
            assert pod1["owner_kind"] == "N/A"
            assert pod1["owner_name"] == "N/A"
            assert pod1["labels"]["app"] == "test-app"
            assert pod1["labels"]["version"] == "v1.0"

            # Check second pod
            pod2 = result[1]
            assert pod2["name"] == "test-pod-2"
            assert pod2["namespace"] == "default"
            assert pod2["phase"] == "Pending"
            assert pod2["ready_containers"] == 0
            assert pod2["total_containers"] == 1
            assert pod2["restart_count"] == 1
            assert pod2["node_name"] == "worker-node-2"
            assert pod2["pod_ip"] == "10.244.1.6"
            assert pod2["owner_kind"] == "ReplicaSet"
            assert pod2["owner_name"] == "test-app-2-7d4b8c9f6b"

    @pytest.mark.asyncio
    async def test_get_pods_empty_response(self, mock_client):
        """Test get_pods with empty response."""
        mock_response_data = {"items": []}

        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_get.return_value.__aenter__.return_value = mock_response

            result = await mock_client.get_pods()
            assert result == []

    @pytest.mark.asyncio
    async def test_get_pods_http_error(self, mock_client):
        """Test get_pods with HTTP error."""
        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 500
            mock_get.return_value.__aenter__.return_value = mock_response

            result = await mock_client.get_pods()
            assert result == []

    @pytest.mark.asyncio
    async def test_get_pods_connection_error(self, mock_client):
        """Test get_pods with connection error."""
        with patch(
            "aiohttp.ClientSession.get",
            side_effect=aiohttp.ClientError("Connection error"),
        ):
            result = await mock_client.get_pods()
            assert result == []

    @pytest.mark.asyncio
    async def test_get_pods_all_namespaces(self, mock_client):
        """Test get_pods with monitor_all_namespaces enabled."""
        mock_client.monitor_all_namespaces = True

        mock_response_data = {"items": []}

        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_get.return_value.__aenter__.return_value = mock_response

            await mock_client.get_pods()

            # Verify the correct URL was called (all namespaces)
            # get_pods() calls _test_connection() first, then the actual pods endpoint
            assert mock_get.call_count >= 1
            # Find the call to the pods endpoint
            pods_call = None
            for call in mock_get.call_args_list:
                if call[0] and "/api/v1/pods" in call[0][0]:
                    pods_call = call
                    break
            assert pods_call is not None, "Expected call to /api/v1/pods endpoint"
            assert "/api/v1/pods" in pods_call[0][0]

    def test_parse_pods_data(self, mock_client):
        """Test _parse_pods_data method."""
        raw_pods = [
            {
                "metadata": {
                    "name": "test-pod",
                    "namespace": "default",
                    "uid": "pod-uid",
                    "creationTimestamp": "2023-01-01T00:00:00Z",
                    "labels": {"app": "test-app"},
                },
                "spec": {"nodeName": "worker-node-1"},
                "status": {
                    "phase": "Running",
                    "podIP": "10.244.1.5",
                    "containerStatuses": [
                        {"ready": True, "restartCount": 0},
                        {"ready": False, "restartCount": 1},
                    ],
                },
            }
        ]

        result = mock_client._parse_pods_data(raw_pods)

        assert len(result) == 1
        pod = result[0]
        assert pod["name"] == "test-pod"
        assert pod["namespace"] == "default"
        assert pod["phase"] == "Running"
        assert pod["ready_containers"] == 1
        assert pod["total_containers"] == 2
        assert pod["restart_count"] == 1
        assert pod["node_name"] == "worker-node-1"
        assert pod["pod_ip"] == "10.244.1.5"
        assert pod["labels"]["app"] == "test-app"


# ---------------------------------------------------------------------------
# Additional tests for uncovered kubernetes_client.py paths
# ---------------------------------------------------------------------------


class TestGetDeploymentsCountAiohttp:
    """Test _get_deployments_count_aiohttp and _get_deployments_count_all_namespaces_aiohttp."""

    async def test_get_deployments_count_aiohttp_success(self, mock_client):
        """Test _get_deployments_count_aiohttp returns count on success."""
        mock_client.namespaces = ["default"]

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(
            return_value={
                "items": [
                    {"metadata": {"name": "nginx"}},
                    {"metadata": {"name": "api"}},
                ]
            }
        )
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.get = MagicMock(return_value=mock_response)

        with patch(
            "custom_components.kubernetes.kubernetes_client.aiohttp.ClientSession",
            return_value=mock_session,
        ):
            count = await mock_client._get_deployments_count_aiohttp()

        assert count == 2

    async def test_get_deployments_count_aiohttp_error_status(self, mock_client):
        """Test _get_deployments_count_aiohttp returns 0 on non-200 status."""
        mock_client.namespaces = ["default"]

        mock_response = MagicMock()
        mock_response.status = 403
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.get = MagicMock(return_value=mock_response)

        with patch(
            "custom_components.kubernetes.kubernetes_client.aiohttp.ClientSession",
            return_value=mock_session,
        ):
            count = await mock_client._get_deployments_count_aiohttp()

        assert count == 0

    async def test_get_deployments_count_aiohttp_exception(self, mock_client):
        """Test _get_deployments_count_aiohttp handles exception per namespace."""
        mock_client.namespaces = ["default", "production"]

        mock_response_ok = MagicMock()
        mock_response_ok.status = 200
        mock_response_ok.json = AsyncMock(
            return_value={"items": [{"metadata": {"name": "nginx"}}]}
        )
        mock_response_ok.__aenter__ = AsyncMock(return_value=mock_response_ok)
        mock_response_ok.__aexit__ = AsyncMock(return_value=None)

        call_count = 0

        def make_get(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return mock_response_ok
            raise Exception("Namespace not accessible")

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.get = MagicMock(side_effect=make_get)

        with patch(
            "custom_components.kubernetes.kubernetes_client.aiohttp.ClientSession",
            return_value=mock_session,
        ):
            count = await mock_client._get_deployments_count_aiohttp()

        assert count == 1

    async def test_get_deployments_count_all_namespaces_aiohttp_success(
        self, mock_client
    ):
        """Test _get_deployments_count_all_namespaces_aiohttp on success."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(
            return_value={
                "items": [
                    {"metadata": {"name": "nginx"}},
                    {"metadata": {"name": "api"}},
                    {"metadata": {"name": "worker"}},
                ]
            }
        )
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.get = MagicMock(return_value=mock_response)

        with patch(
            "custom_components.kubernetes.kubernetes_client.aiohttp.ClientSession",
            return_value=mock_session,
        ):
            count = await mock_client._get_deployments_count_all_namespaces_aiohttp()

        assert count == 3

    async def test_get_deployments_count_all_namespaces_aiohttp_error_status(
        self, mock_client
    ):
        """Test _get_deployments_count_all_namespaces_aiohttp on non-200 status."""
        mock_response = MagicMock()
        mock_response.status = 500
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.get = MagicMock(return_value=mock_response)

        with patch(
            "custom_components.kubernetes.kubernetes_client.aiohttp.ClientSession",
            return_value=mock_session,
        ):
            count = await mock_client._get_deployments_count_all_namespaces_aiohttp()

        assert count == 0

    async def test_get_deployments_count_all_namespaces_aiohttp_exception(
        self, mock_client
    ):
        """Test _get_deployments_count_all_namespaces_aiohttp on exception."""
        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.get = MagicMock(side_effect=Exception("Network error"))

        with patch(
            "custom_components.kubernetes.kubernetes_client.aiohttp.ClientSession",
            return_value=mock_session,
        ):
            count = await mock_client._get_deployments_count_all_namespaces_aiohttp()

        assert count == 0


class TestCompareAuthenticationMethods:
    """Test compare_authentication_methods method."""

    async def test_compare_both_succeed(self, mock_client):
        """Test compare_authentication_methods when both methods succeed."""
        mock_client.api_token = "test-token-longer-than-10"
        mock_client.ca_cert = None

        # Mock the kubernetes client call
        mock_executor = AsyncMock(return_value=None)

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.get = MagicMock(return_value=mock_response)

        import asyncio

        loop = asyncio.get_event_loop()

        with (
            patch.object(loop, "run_in_executor", new=mock_executor),
            patch(
                "custom_components.kubernetes.kubernetes_client.aiohttp.ClientSession",
                return_value=mock_session,
            ),
        ):
            result = await mock_client.compare_authentication_methods()

        assert result["kubernetes_client"]["success"] is True
        assert result["aiohttp_fallback"]["success"] is True
        assert "token_info" in result

    async def test_compare_k8s_fails_aiohttp_succeeds(self, mock_client):
        """Test compare_authentication_methods when k8s client fails."""
        mock_client.api_token = "short"
        mock_client.ca_cert = "some-cert"

        mock_executor = AsyncMock(side_effect=Exception("K8s client error"))

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.get = MagicMock(return_value=mock_response)

        import asyncio

        loop = asyncio.get_event_loop()

        with (
            patch.object(loop, "run_in_executor", new=mock_executor),
            patch(
                "custom_components.kubernetes.kubernetes_client.aiohttp.ClientSession",
                return_value=mock_session,
            ),
        ):
            result = await mock_client.compare_authentication_methods()

        assert result["kubernetes_client"]["success"] is False
        assert result["aiohttp_fallback"]["success"] is True
        assert result["kubernetes_client"]["ca_cert"] == "provided"

    async def test_compare_both_fail(self, mock_client):
        """Test compare_authentication_methods when both methods fail."""
        mock_client.api_token = "test-token-longer-than-10"
        mock_client.ca_cert = None

        mock_executor = AsyncMock(side_effect=Exception("K8s error"))

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.get = MagicMock(side_effect=Exception("Network error"))

        import asyncio

        loop = asyncio.get_event_loop()

        with (
            patch.object(loop, "run_in_executor", new=mock_executor),
            patch(
                "custom_components.kubernetes.kubernetes_client.aiohttp.ClientSession",
                return_value=mock_session,
            ),
        ):
            result = await mock_client.compare_authentication_methods()

        assert result["kubernetes_client"]["success"] is False
        assert result["aiohttp_fallback"]["success"] is False

    async def test_compare_aiohttp_non_200(self, mock_client):
        """Test compare_authentication_methods when aiohttp returns non-200."""
        mock_client.api_token = "test-token-longer"
        mock_client.ca_cert = None

        mock_executor = AsyncMock(return_value=None)

        mock_response = MagicMock()
        mock_response.status = 403
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.get = MagicMock(return_value=mock_response)

        import asyncio

        loop = asyncio.get_event_loop()

        with (
            patch.object(loop, "run_in_executor", new=mock_executor),
            patch(
                "custom_components.kubernetes.kubernetes_client.aiohttp.ClientSession",
                return_value=mock_session,
            ),
        ):
            result = await mock_client.compare_authentication_methods()

        assert result["kubernetes_client"]["success"] is True
        assert result["aiohttp_fallback"]["success"] is False
        assert result["aiohttp_fallback"]["status_code"] == 403

    async def test_token_info_short_token(self, mock_client):
        """Test compare_authentication_methods token_info for short token."""
        mock_client.api_token = "short"
        mock_client.ca_cert = None

        mock_executor = AsyncMock(return_value=None)

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.get = MagicMock(return_value=mock_response)

        import asyncio

        loop = asyncio.get_event_loop()

        with (
            patch.object(loop, "run_in_executor", new=mock_executor),
            patch(
                "custom_components.kubernetes.kubernetes_client.aiohttp.ClientSession",
                return_value=mock_session,
            ),
        ):
            result = await mock_client.compare_authentication_methods()

        assert result["token_info"]["length"] == 5
        assert (
            result["kubernetes_client"]["headers"]["authorization"] == "Bearer [token]"
        )


class TestTestAuthentication:
    """Test test_authentication method."""

    async def test_authentication_via_k8s_client_success(self, mock_client):
        """Test test_authentication succeeds via kubernetes client."""
        mock_executor = AsyncMock(return_value=MagicMock())

        import asyncio

        loop = asyncio.get_event_loop()

        with patch.object(loop, "run_in_executor", new=mock_executor):
            result = await mock_client.test_authentication()

        assert result["authenticated"] is True
        assert result["method"] == "kubernetes_client"
        assert result["error"] is None

    async def test_authentication_via_api_exception_aiohttp_success(self, mock_client):
        """Test test_authentication falls back to aiohttp on ApiException."""
        from kubernetes.client import ApiException

        api_exc = ApiException(status=401, reason="Unauthorized")

        mock_executor = AsyncMock(side_effect=api_exc)

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.get = MagicMock(return_value=mock_response)

        import asyncio

        loop = asyncio.get_event_loop()

        with (
            patch.object(loop, "run_in_executor", new=mock_executor),
            patch(
                "custom_components.kubernetes.kubernetes_client.aiohttp.ClientSession",
                return_value=mock_session,
            ),
        ):
            result = await mock_client.test_authentication()

        assert result["authenticated"] is True
        assert result["method"] == "aiohttp_fallback"
        assert result["error"] is None

    async def test_authentication_via_generic_exception_aiohttp_success(
        self, mock_client
    ):
        """Test test_authentication falls back to aiohttp on generic exception."""
        mock_executor = AsyncMock(side_effect=Exception("SSL error"))

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.get = MagicMock(return_value=mock_response)

        import asyncio

        loop = asyncio.get_event_loop()

        with (
            patch.object(loop, "run_in_executor", new=mock_executor),
            patch(
                "custom_components.kubernetes.kubernetes_client.aiohttp.ClientSession",
                return_value=mock_session,
            ),
        ):
            result = await mock_client.test_authentication()

        assert result["authenticated"] is True
        assert result["method"] == "aiohttp_fallback"

    async def test_authentication_both_fail(self, mock_client):
        """Test test_authentication when both methods fail."""
        mock_executor = AsyncMock(side_effect=Exception("K8s error"))

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.get = MagicMock(side_effect=Exception("Network error"))

        import asyncio

        loop = asyncio.get_event_loop()

        with (
            patch.object(loop, "run_in_executor", new=mock_executor),
            patch(
                "custom_components.kubernetes.kubernetes_client.aiohttp.ClientSession",
                return_value=mock_session,
            ),
        ):
            result = await mock_client.test_authentication()

        assert result["authenticated"] is False
        assert result["error"] is not None

    async def test_authentication_aiohttp_non_200(self, mock_client):
        """Test test_authentication when aiohttp returns non-200."""
        from kubernetes.client import ApiException

        api_exc = ApiException(status=403, reason="Forbidden")
        mock_executor = AsyncMock(side_effect=api_exc)

        mock_response = MagicMock()
        mock_response.status = 403
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.get = MagicMock(return_value=mock_response)

        import asyncio

        loop = asyncio.get_event_loop()

        with (
            patch.object(loop, "run_in_executor", new=mock_executor),
            patch(
                "custom_components.kubernetes.kubernetes_client.aiohttp.ClientSession",
                return_value=mock_session,
            ),
        ):
            result = await mock_client.test_authentication()

        assert result["authenticated"] is False
        assert "403" in result["error"] or result["error"] is not None


class TestTriggerCronjobAiohttp:
    """Test _trigger_cronjob_aiohttp method."""

    async def test_trigger_cronjob_success(self, mock_client):
        """Test _trigger_cronjob_aiohttp succeeds."""
        cronjob_data = {
            "spec": {
                "jobTemplate": {
                    "spec": {
                        "template": {
                            "spec": {
                                "containers": [{"name": "job", "image": "busybox"}]
                            }
                        }
                    }
                }
            }
        }
        job_result = {
            "metadata": {
                "name": "test-cron-manual-12345",
                "uid": "abc123",
            }
        }

        get_response = MagicMock()
        get_response.status = 200
        get_response.json = AsyncMock(return_value=cronjob_data)
        get_response.__aenter__ = AsyncMock(return_value=get_response)
        get_response.__aexit__ = AsyncMock(return_value=None)

        post_response = MagicMock()
        post_response.status = 201
        post_response.json = AsyncMock(return_value=job_result)
        post_response.__aenter__ = AsyncMock(return_value=post_response)
        post_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.get = MagicMock(return_value=get_response)
        mock_session.post = MagicMock(return_value=post_response)

        with patch(
            "custom_components.kubernetes.kubernetes_client.aiohttp.ClientSession",
            return_value=mock_session,
        ):
            result = await mock_client._trigger_cronjob_aiohttp("test-cron", "default")

        assert result["success"] is True
        assert result["cronjob_name"] == "test-cron"
        assert result["namespace"] == "default"
        assert "job_name" in result

    async def test_trigger_cronjob_get_fails(self, mock_client):
        """Test _trigger_cronjob_aiohttp when GET cronjob returns non-200."""
        get_response = MagicMock()
        get_response.status = 404
        get_response.__aenter__ = AsyncMock(return_value=get_response)
        get_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.get = MagicMock(return_value=get_response)

        with patch(
            "custom_components.kubernetes.kubernetes_client.aiohttp.ClientSession",
            return_value=mock_session,
        ):
            result = await mock_client._trigger_cronjob_aiohttp(
                "missing-cron", "default"
            )

        assert result["success"] is False
        assert "404" in result["error"]

    async def test_trigger_cronjob_no_job_template(self, mock_client):
        """Test _trigger_cronjob_aiohttp when cronjob has no job template."""
        cronjob_data = {"spec": {}}  # No jobTemplate

        get_response = MagicMock()
        get_response.status = 200
        get_response.json = AsyncMock(return_value=cronjob_data)
        get_response.__aenter__ = AsyncMock(return_value=get_response)
        get_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.get = MagicMock(return_value=get_response)

        with patch(
            "custom_components.kubernetes.kubernetes_client.aiohttp.ClientSession",
            return_value=mock_session,
        ):
            result = await mock_client._trigger_cronjob_aiohttp("test-cron", "default")

        assert result["success"] is False
        assert "no job template" in result["error"]

    async def test_trigger_cronjob_post_fails(self, mock_client):
        """Test _trigger_cronjob_aiohttp when POST job returns non-201."""
        cronjob_data = {
            "spec": {
                "jobTemplate": {"spec": {"template": {"spec": {"containers": []}}}}
            }
        }

        get_response = MagicMock()
        get_response.status = 200
        get_response.json = AsyncMock(return_value=cronjob_data)
        get_response.__aenter__ = AsyncMock(return_value=get_response)
        get_response.__aexit__ = AsyncMock(return_value=None)

        post_response = MagicMock()
        post_response.status = 409  # Conflict
        post_response.__aenter__ = AsyncMock(return_value=post_response)
        post_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.get = MagicMock(return_value=get_response)
        mock_session.post = MagicMock(return_value=post_response)

        with patch(
            "custom_components.kubernetes.kubernetes_client.aiohttp.ClientSession",
            return_value=mock_session,
        ):
            result = await mock_client._trigger_cronjob_aiohttp("test-cron", "default")

        assert result["success"] is False
        assert "409" in result["error"]

    async def test_trigger_cronjob_exception(self, mock_client):
        """Test _trigger_cronjob_aiohttp handles exceptions."""
        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.get = MagicMock(side_effect=Exception("Network error"))

        with patch(
            "custom_components.kubernetes.kubernetes_client.aiohttp.ClientSession",
            return_value=mock_session,
        ):
            result = await mock_client._trigger_cronjob_aiohttp("test-cron", "default")

        assert result["success"] is False
        assert "Network error" in result["error"]


# ---------------------------------------------------------------------------
# Daemonset aiohttp method tests
# ---------------------------------------------------------------------------


class TestGetDaemonsetsCountAiohttp:
    """Test _get_daemonsets_count_aiohttp and _get_daemonsets_count_all_namespaces_aiohttp."""

    async def test_get_daemonsets_count_aiohttp_success(self, mock_client):
        """Test _get_daemonsets_count_aiohttp returns count on success."""
        mock_client.namespaces = ["default"]

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(
            return_value={
                "items": [{"metadata": {"name": "ds1"}}, {"metadata": {"name": "ds2"}}]
            }
        )
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.get = MagicMock(return_value=mock_response)

        with patch(
            "custom_components.kubernetes.kubernetes_client.aiohttp.ClientSession",
            return_value=mock_session,
        ):
            count = await mock_client._get_daemonsets_count_aiohttp()

        assert count == 2

    async def test_get_daemonsets_count_aiohttp_error_status(self, mock_client):
        """Test _get_daemonsets_count_aiohttp handles non-200 status."""
        mock_client.namespaces = ["default"]

        mock_response = MagicMock()
        mock_response.status = 403
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.get = MagicMock(return_value=mock_response)

        with patch(
            "custom_components.kubernetes.kubernetes_client.aiohttp.ClientSession",
            return_value=mock_session,
        ):
            count = await mock_client._get_daemonsets_count_aiohttp()

        assert count == 0

    async def test_get_daemonsets_count_aiohttp_exception(self, mock_client):
        """Test _get_daemonsets_count_aiohttp handles per-namespace exception."""
        mock_client.namespaces = ["default"]

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.get = MagicMock(side_effect=Exception("Connection refused"))

        with patch(
            "custom_components.kubernetes.kubernetes_client.aiohttp.ClientSession",
            return_value=mock_session,
        ):
            count = await mock_client._get_daemonsets_count_aiohttp()

        assert count == 0

    async def test_get_daemonsets_count_all_namespaces_aiohttp_success(
        self, mock_client
    ):
        """Test _get_daemonsets_count_all_namespaces_aiohttp returns count."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(
            return_value={"items": [{"metadata": {"name": "ds1"}}]}
        )
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.get = MagicMock(return_value=mock_response)

        with patch(
            "custom_components.kubernetes.kubernetes_client.aiohttp.ClientSession",
            return_value=mock_session,
        ):
            count = await mock_client._get_daemonsets_count_all_namespaces_aiohttp()

        assert count == 1

    async def test_get_daemonsets_count_all_namespaces_aiohttp_error(self, mock_client):
        """Test _get_daemonsets_count_all_namespaces_aiohttp handles non-200."""
        mock_response = MagicMock()
        mock_response.status = 500
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.get = MagicMock(return_value=mock_response)

        with patch(
            "custom_components.kubernetes.kubernetes_client.aiohttp.ClientSession",
            return_value=mock_session,
        ):
            count = await mock_client._get_daemonsets_count_all_namespaces_aiohttp()

        assert count == 0

    async def test_get_daemonsets_count_all_namespaces_aiohttp_exception(
        self, mock_client
    ):
        """Test _get_daemonsets_count_all_namespaces_aiohttp handles exception."""
        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(side_effect=Exception("Timeout"))
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "custom_components.kubernetes.kubernetes_client.aiohttp.ClientSession",
            return_value=mock_session,
        ):
            count = await mock_client._get_daemonsets_count_all_namespaces_aiohttp()

        assert count == 0


class TestGetDaemonsetsAiohttp:
    """Test _get_daemonsets_aiohttp and _get_daemonsets_all_namespaces_aiohttp."""

    def _make_daemonset_item(self, name="ds1", namespace="default"):
        return {
            "metadata": {"name": name, "namespace": namespace},
            "status": {
                "desiredNumberScheduled": 3,
                "currentNumberScheduled": 3,
                "numberReady": 3,
                "numberAvailable": 3,
            },
            "spec": {"selector": {"matchLabels": {"app": name}}},
        }

    async def test_get_daemonsets_aiohttp_success(self, mock_client):
        """Test _get_daemonsets_aiohttp returns parsed daemonset list."""
        mock_client.namespaces = ["default"]

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(
            return_value={"items": [self._make_daemonset_item()]}
        )
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.get = MagicMock(return_value=mock_response)

        with patch(
            "custom_components.kubernetes.kubernetes_client.aiohttp.ClientSession",
            return_value=mock_session,
        ):
            result = await mock_client._get_daemonsets_aiohttp()

        assert len(result) == 1
        assert result[0]["name"] == "ds1"
        assert result[0]["is_running"] is True

    async def test_get_daemonsets_aiohttp_error_status(self, mock_client):
        """Test _get_daemonsets_aiohttp handles non-200 status."""
        mock_client.namespaces = ["default"]

        mock_response = MagicMock()
        mock_response.status = 403
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.get = MagicMock(return_value=mock_response)

        with patch(
            "custom_components.kubernetes.kubernetes_client.aiohttp.ClientSession",
            return_value=mock_session,
        ):
            result = await mock_client._get_daemonsets_aiohttp()

        assert result == []

    async def test_get_daemonsets_aiohttp_exception(self, mock_client):
        """Test _get_daemonsets_aiohttp handles per-namespace exception."""
        mock_client.namespaces = ["default"]

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.get = MagicMock(side_effect=Exception("Network error"))

        with patch(
            "custom_components.kubernetes.kubernetes_client.aiohttp.ClientSession",
            return_value=mock_session,
        ):
            result = await mock_client._get_daemonsets_aiohttp()

        assert result == []

    async def test_get_daemonsets_all_namespaces_aiohttp_success(self, mock_client):
        """Test _get_daemonsets_all_namespaces_aiohttp returns parsed list."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(
            return_value={
                "items": [self._make_daemonset_item("kube-proxy", "kube-system")]
            }
        )
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.get = MagicMock(return_value=mock_response)

        with patch(
            "custom_components.kubernetes.kubernetes_client.aiohttp.ClientSession",
            return_value=mock_session,
        ):
            result = await mock_client._get_daemonsets_all_namespaces_aiohttp()

        assert len(result) == 1
        assert result[0]["name"] == "kube-proxy"

    async def test_get_daemonsets_all_namespaces_aiohttp_error(self, mock_client):
        """Test _get_daemonsets_all_namespaces_aiohttp handles non-200."""
        mock_response = MagicMock()
        mock_response.status = 500
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.get = MagicMock(return_value=mock_response)

        with patch(
            "custom_components.kubernetes.kubernetes_client.aiohttp.ClientSession",
            return_value=mock_session,
        ):
            result = await mock_client._get_daemonsets_all_namespaces_aiohttp()

        assert result == []

    async def test_get_daemonsets_all_namespaces_aiohttp_exception(self, mock_client):
        """Test _get_daemonsets_all_namespaces_aiohttp handles exception."""
        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(side_effect=Exception("SSL error"))
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "custom_components.kubernetes.kubernetes_client.aiohttp.ClientSession",
            return_value=mock_session,
        ):
            result = await mock_client._get_daemonsets_all_namespaces_aiohttp()

        assert result == []


# ---------------------------------------------------------------------------
# CronJob aiohttp count/list method tests
# ---------------------------------------------------------------------------


class TestGetCronjobsCountAiohttp:
    """Test _get_cronjobs_count_aiohttp and _get_cronjobs_count_all_namespaces_aiohttp."""

    async def test_get_cronjobs_count_aiohttp_success(self, mock_client):
        """Test _get_cronjobs_count_aiohttp returns count on success."""
        mock_client.namespaces = ["default"]

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(
            return_value={
                "items": [
                    {"metadata": {"name": "backup"}},
                    {"metadata": {"name": "report"}},
                ]
            }
        )
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.get = MagicMock(return_value=mock_response)

        with patch(
            "custom_components.kubernetes.kubernetes_client.aiohttp.ClientSession",
            return_value=mock_session,
        ):
            count = await mock_client._get_cronjobs_count_aiohttp()

        assert count == 2

    async def test_get_cronjobs_count_aiohttp_error_status(self, mock_client):
        """Test _get_cronjobs_count_aiohttp handles non-200 status."""
        mock_client.namespaces = ["default"]

        mock_response = MagicMock()
        mock_response.status = 403
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.get = MagicMock(return_value=mock_response)

        with patch(
            "custom_components.kubernetes.kubernetes_client.aiohttp.ClientSession",
            return_value=mock_session,
        ):
            count = await mock_client._get_cronjobs_count_aiohttp()

        assert count == 0

    async def test_get_cronjobs_count_aiohttp_exception(self, mock_client):
        """Test _get_cronjobs_count_aiohttp handles per-namespace exception."""
        mock_client.namespaces = ["default"]

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.get = MagicMock(side_effect=Exception("Timeout"))

        with patch(
            "custom_components.kubernetes.kubernetes_client.aiohttp.ClientSession",
            return_value=mock_session,
        ):
            count = await mock_client._get_cronjobs_count_aiohttp()

        assert count == 0

    async def test_get_cronjobs_count_all_namespaces_aiohttp_success(self, mock_client):
        """Test _get_cronjobs_count_all_namespaces_aiohttp returns count."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(
            return_value={"items": [{"metadata": {"name": "backup"}}]}
        )
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.get = MagicMock(return_value=mock_response)

        with patch(
            "custom_components.kubernetes.kubernetes_client.aiohttp.ClientSession",
            return_value=mock_session,
        ):
            count = await mock_client._get_cronjobs_count_all_namespaces_aiohttp()

        assert count == 1

    async def test_get_cronjobs_count_all_namespaces_aiohttp_error(self, mock_client):
        """Test _get_cronjobs_count_all_namespaces_aiohttp handles non-200."""
        mock_response = MagicMock()
        mock_response.status = 500
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.get = MagicMock(return_value=mock_response)

        with patch(
            "custom_components.kubernetes.kubernetes_client.aiohttp.ClientSession",
            return_value=mock_session,
        ):
            count = await mock_client._get_cronjobs_count_all_namespaces_aiohttp()

        assert count == 0

    async def test_get_cronjobs_count_all_namespaces_aiohttp_exception(
        self, mock_client
    ):
        """Test _get_cronjobs_count_all_namespaces_aiohttp handles exception."""
        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(side_effect=Exception("SSL error"))
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "custom_components.kubernetes.kubernetes_client.aiohttp.ClientSession",
            return_value=mock_session,
        ):
            count = await mock_client._get_cronjobs_count_all_namespaces_aiohttp()

        assert count == 0


class TestGetCronjobsAiohttp:
    """Test _get_cronjobs_aiohttp and _get_cronjobs_all_namespaces_aiohttp."""

    def _make_cronjob_item(self, name="backup", namespace="default"):
        return {
            "metadata": {"name": name, "namespace": namespace, "uid": "uid-123"},
            "spec": {"schedule": "0 2 * * *", "suspend": False},
            "status": {},
        }

    async def test_get_cronjobs_aiohttp_success(self, mock_client):
        """Test _get_cronjobs_aiohttp returns parsed cronjob list."""
        mock_client.namespaces = ["default"]

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(
            return_value={"items": [self._make_cronjob_item()]}
        )
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.get = MagicMock(return_value=mock_response)

        with patch(
            "custom_components.kubernetes.kubernetes_client.aiohttp.ClientSession",
            return_value=mock_session,
        ):
            result = await mock_client._get_cronjobs_aiohttp()

        assert len(result) == 1
        assert result[0]["name"] == "backup"

    async def test_get_cronjobs_aiohttp_error_status(self, mock_client):
        """Test _get_cronjobs_aiohttp handles non-200 status."""
        mock_client.namespaces = ["default"]

        mock_response = MagicMock()
        mock_response.status = 403
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.get = MagicMock(return_value=mock_response)

        with patch(
            "custom_components.kubernetes.kubernetes_client.aiohttp.ClientSession",
            return_value=mock_session,
        ):
            result = await mock_client._get_cronjobs_aiohttp()

        assert result == []

    async def test_get_cronjobs_aiohttp_exception(self, mock_client):
        """Test _get_cronjobs_aiohttp handles per-namespace exception."""
        mock_client.namespaces = ["default"]

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.get = MagicMock(side_effect=Exception("Network error"))

        with patch(
            "custom_components.kubernetes.kubernetes_client.aiohttp.ClientSession",
            return_value=mock_session,
        ):
            result = await mock_client._get_cronjobs_aiohttp()

        assert result == []

    async def test_get_cronjobs_all_namespaces_aiohttp_success(self, mock_client):
        """Test _get_cronjobs_all_namespaces_aiohttp returns parsed list."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(
            return_value={"items": [self._make_cronjob_item("report", "monitoring")]}
        )
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.get = MagicMock(return_value=mock_response)

        with patch(
            "custom_components.kubernetes.kubernetes_client.aiohttp.ClientSession",
            return_value=mock_session,
        ):
            result = await mock_client._get_cronjobs_all_namespaces_aiohttp()

        assert len(result) == 1
        assert result[0]["name"] == "report"

    async def test_get_cronjobs_all_namespaces_aiohttp_error(self, mock_client):
        """Test _get_cronjobs_all_namespaces_aiohttp handles non-200."""
        mock_response = MagicMock()
        mock_response.status = 500
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.get = MagicMock(return_value=mock_response)

        with patch(
            "custom_components.kubernetes.kubernetes_client.aiohttp.ClientSession",
            return_value=mock_session,
        ):
            result = await mock_client._get_cronjobs_all_namespaces_aiohttp()

        assert result == []

    async def test_get_cronjobs_all_namespaces_aiohttp_exception(self, mock_client):
        """Test _get_cronjobs_all_namespaces_aiohttp handles exception."""
        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(side_effect=Exception("Connection refused"))
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "custom_components.kubernetes.kubernetes_client.aiohttp.ClientSession",
            return_value=mock_session,
        ):
            result = await mock_client._get_cronjobs_all_namespaces_aiohttp()

        assert result == []


# ---------------------------------------------------------------------------
# Watch API tests
# ---------------------------------------------------------------------------


def _make_aiohttp_stream_mock(lines: list[bytes], status: int = 200):
    """Return a mock aiohttp ClientSession that streams the given byte lines."""
    mock_response = MagicMock()
    mock_response.status = status
    mock_response.raise_for_status = MagicMock()

    async def _async_iter_lines():
        for line in lines:
            yield line

    mock_response.content.__aiter__ = _async_iter_lines

    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_response)
    mock_cm.__aexit__ = AsyncMock(return_value=None)

    mock_session = MagicMock()
    mock_session.get = MagicMock(return_value=mock_cm)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    return mock_session


class TestListResourceWithVersion:
    """Tests for KubernetesClient.list_resource_with_version."""

    async def test_returns_items_and_resource_version(self, mock_client):
        """list_resource_with_version should return (items, resourceVersion)."""
        payload = {
            "metadata": {"resourceVersion": "42"},
            "items": [{"metadata": {"name": "pod1"}}, {"metadata": {"name": "pod2"}}],
        }

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json = AsyncMock(return_value=payload)

        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_response)
        mock_cm.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_cm)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "custom_components.kubernetes.kubernetes_client.aiohttp.ClientSession",
            return_value=mock_session,
        ):
            items, rv = await mock_client.list_resource_with_version(
                "https://host/api/v1/pods"
            )

        assert rv == "42"
        assert len(items) == 2
        assert items[0]["metadata"]["name"] == "pod1"

    async def test_returns_zero_resource_version_when_missing(self, mock_client):
        """If metadata.resourceVersion is absent, '0' should be returned."""
        payload = {"metadata": {}, "items": []}

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json = AsyncMock(return_value=payload)

        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_response)
        mock_cm.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_cm)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "custom_components.kubernetes.kubernetes_client.aiohttp.ClientSession",
            return_value=mock_session,
        ):
            items, rv = await mock_client.list_resource_with_version(
                "https://host/api/v1/pods"
            )

        assert rv == "0"
        assert items == []


class TestWatchStream:
    """Tests for KubernetesClient.watch_stream."""

    async def test_watch_stream_yields_events(self, mock_client):
        """watch_stream should yield parsed JSON objects from the streaming response."""
        import json as _json

        events = [
            {"type": "ADDED", "object": {"metadata": {"name": "pod1"}}},
            {"type": "MODIFIED", "object": {"metadata": {"name": "pod1"}}},
        ]
        lines = [_json.dumps(e).encode() for e in events]

        mock_session = _make_aiohttp_stream_mock(lines)

        with patch(
            "custom_components.kubernetes.kubernetes_client.aiohttp.ClientSession",
            return_value=mock_session,
        ):
            collected = []
            async for event in mock_client.watch_stream(
                "https://host/api/v1/pods", "0"
            ):
                collected.append(event)

        assert len(collected) == 2
        assert collected[0]["type"] == "ADDED"
        assert collected[1]["type"] == "MODIFIED"

    async def test_watch_stream_raises_on_410(self, mock_client):
        """watch_stream should raise ResourceVersionExpired when the server returns 410."""
        mock_response = MagicMock()
        mock_response.status = 410

        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_response)
        mock_cm.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_cm)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "custom_components.kubernetes.kubernetes_client.aiohttp.ClientSession",
            return_value=mock_session,
        ):
            with pytest.raises(ResourceVersionExpired):
                async for _ in mock_client.watch_stream(
                    "https://host/api/v1/pods", "old-rv"
                ):
                    pass

    async def test_watch_stream_skips_empty_lines(self, mock_client):
        """Empty lines in the stream should be silently ignored."""
        import json as _json

        events = [{"type": "ADDED", "object": {"metadata": {"name": "pod1"}}}]
        lines = [b"", b"   ", _json.dumps(events[0]).encode(), b""]

        mock_session = _make_aiohttp_stream_mock(lines)

        with patch(
            "custom_components.kubernetes.kubernetes_client.aiohttp.ClientSession",
            return_value=mock_session,
        ):
            collected = []
            async for event in mock_client.watch_stream(
                "https://host/api/v1/pods", "1"
            ):
                collected.append(event)

        assert len(collected) == 1


class TestParseHelpers:
    """Tests for the single-item parse methods used by the watch loop."""

    async def test_parse_pod_item(self, mock_client):
        """_parse_pod_item should return a dict with standard pod fields."""
        raw = {
            "metadata": {
                "name": "nginx-abc",
                "namespace": "default",
                "creationTimestamp": "2024-01-01T00:00:00Z",
                "labels": {},
                "ownerReferences": [],
                "uid": "uid-1",
            },
            "spec": {"nodeName": "node1"},
            "status": {
                "phase": "Running",
                "podIP": "10.0.0.1",
                "containerStatuses": [{"ready": True, "restartCount": 0}],
            },
        }
        result = mock_client._parse_pod_item(raw)
        assert result is not None
        assert result["name"] == "nginx-abc"
        assert result["namespace"] == "default"
        assert result["phase"] == "Running"
        assert result["ready_containers"] == 1

    async def test_parse_pod_item_returns_none_for_empty(self, mock_client):
        """_parse_pod_item should return None for an empty dict."""
        result = mock_client._parse_pod_item({})
        assert result is None

    async def test_parse_node_item(self, mock_client):
        """_parse_node_item should return a dict with standard node fields."""
        raw = {
            "metadata": {
                "name": "worker-1",
                "creationTimestamp": "2024-01-01T00:00:00Z",
            },
            "spec": {},
            "status": {
                "conditions": [{"type": "Ready", "status": "True"}],
                "addresses": [{"type": "InternalIP", "address": "10.0.0.5"}],
                "capacity": {"memory": "16Gi", "cpu": "4"},
                "allocatable": {"memory": "14Gi"},
                "nodeInfo": {
                    "osImage": "Ubuntu 22.04",
                    "kernelVersion": "5.15",
                    "containerRuntimeVersion": "containerd://1.6",
                    "kubeletVersion": "v1.28",
                },
            },
        }
        result = mock_client._parse_node_item(raw)
        assert result is not None
        assert result["name"] == "worker-1"
        assert result["status"] == "Ready"
        assert result["internal_ip"] == "10.0.0.5"
        assert result["cpu_cores"] == 4

    async def test_parse_node_item_not_ready(self, mock_client):
        """_parse_node_item should return NotReady when the Ready condition is False."""
        raw = {
            "metadata": {
                "name": "worker-2",
                "creationTimestamp": "2024-01-01T00:00:00Z",
            },
            "spec": {},
            "status": {
                "conditions": [{"type": "Ready", "status": "False"}],
                "addresses": [],
                "capacity": {"memory": "8Gi", "cpu": "2"},
                "allocatable": {"memory": "7Gi"},
                "nodeInfo": {},
            },
        }
        result = mock_client._parse_node_item(raw)
        assert result is not None
        assert result["status"] == "NotReady"

    async def test_parse_deployment_item(self, mock_client):
        """_parse_deployment_item should return a dict with standard deployment fields."""
        raw = {
            "metadata": {"name": "nginx", "namespace": "default"},
            "spec": {"replicas": 3, "selector": {"matchLabels": {"app": "nginx"}}},
            "status": {"availableReplicas": 3, "readyReplicas": 3},
        }
        result = mock_client._parse_deployment_item(raw)
        assert result is not None
        assert result["name"] == "nginx"
        assert result["replicas"] == 3
        assert result["is_running"] is True

    async def test_parse_statefulset_item(self, mock_client):
        """_parse_statefulset_item should return a dict with standard statefulset fields."""
        raw = {
            "metadata": {"name": "redis", "namespace": "default"},
            "spec": {"replicas": 1, "selector": {"matchLabels": {"app": "redis"}}},
            "status": {"availableReplicas": 1, "readyReplicas": 1},
        }
        result = mock_client._parse_statefulset_item(raw)
        assert result is not None
        assert result["name"] == "redis"
        assert result["is_running"] is True

    async def test_parse_daemonset_item(self, mock_client):
        """_parse_daemonset_item should return a dict with standard daemonset fields."""
        raw = {
            "metadata": {"name": "fluentd", "namespace": "logging"},
            "spec": {"selector": {"matchLabels": {"app": "fluentd"}}},
            "status": {
                "desiredNumberScheduled": 3,
                "currentNumberScheduled": 3,
                "numberReady": 3,
                "numberAvailable": 3,
            },
        }
        result = mock_client._parse_daemonset_item(raw)
        assert result is not None
        assert result["name"] == "fluentd"
        assert result["number_ready"] == 3
        assert result["is_running"] is True
