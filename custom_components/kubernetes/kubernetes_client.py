"""Kubernetes client for Home Assistant integration."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp
from kubernetes import client, config
from kubernetes.client.rest import ApiException

from .const import (
    CONF_API_TOKEN,
    CONF_CA_CERT,
    CONF_CLUSTER_NAME,
    CONF_HOST,
    CONF_MONITOR_ALL_NAMESPACES,
    CONF_NAMESPACE,
    CONF_PORT,
    CONF_VERIFY_SSL,
    DEFAULT_MONITOR_ALL_NAMESPACES,
    DEFAULT_NAMESPACE,
    DEFAULT_PORT,
    DEFAULT_VERIFY_SSL,
)

_LOGGER = logging.getLogger(__name__)


class KubernetesClient:
    """Kubernetes client for Home Assistant integration."""

    def __init__(self, config_data: dict[str, Any]) -> None:
        """Initialize the Kubernetes client."""
        self.host = config_data[CONF_HOST]
        self.port = config_data.get(CONF_PORT, DEFAULT_PORT)
        self.api_token = config_data[CONF_API_TOKEN]
        self.cluster_name = config_data.get(CONF_CLUSTER_NAME, "default")
        self.namespace = config_data.get(CONF_NAMESPACE, DEFAULT_NAMESPACE)
        self.monitor_all_namespaces = config_data.get(CONF_MONITOR_ALL_NAMESPACES, DEFAULT_MONITOR_ALL_NAMESPACES)
        self.ca_cert = config_data.get(CONF_CA_CERT)
        self.verify_ssl = config_data.get(CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL)

        # Initialize Kubernetes client
        self._setup_kubernetes_client()

    def _setup_kubernetes_client(self) -> None:
        """Set up the Kubernetes client configuration."""
        configuration = client.Configuration()
        configuration.host = f"https://{self.host}:{self.port}"
        configuration.api_key = {"authorization": f"Bearer {self.api_token}"}
        configuration.api_key_prefix = {"authorization": "Bearer"}
        configuration.verify_ssl = self.verify_ssl

        if self.ca_cert:
            configuration.ssl_ca_cert = self.ca_cert

        # Create API clients
        api_client = client.ApiClient(configuration)
        self.core_v1 = client.CoreV1Api(api_client)
        self.apps_v1 = client.AppsV1Api(api_client)

    async def _test_connection(self) -> bool:
        """Test the connection to Kubernetes."""
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self.core_v1.get_api_resources)
            return True
        except Exception as ex:
            _LOGGER.error("Failed to test connection: %s", ex)
            # Fallback to aiohttp
            return await self._test_connection_aiohttp()

    async def _test_connection_aiohttp(self) -> bool:
        """Test the connection using aiohttp as fallback."""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Accept": "application/json",
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://{self.host}:{self.port}/api/v1/",
                    headers=headers,
                    ssl=False,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    return response.status == 200
        except Exception as ex:
            _LOGGER.error("aiohttp connection test failed: %s", ex)
            return False

    async def get_pods_count(self) -> int:
        """Get the count of pods in the namespace(s)."""
        try:
            # Test connection first
            if not await self._test_connection():
                _LOGGER.error("Cannot connect to Kubernetes API")
                return 0

            if self.monitor_all_namespaces:
                return await self._get_pods_count_all_namespaces()
            else:
                return await self._get_pods_count_single_namespace()

        except Exception as ex:
            _LOGGER.error("Failed to get pods count: %s", ex)
            # Fallback to aiohttp
            if self.monitor_all_namespaces:
                return await self._get_pods_count_all_namespaces_aiohttp()
            else:
                return await self._get_pods_count_aiohttp()

    async def _get_pods_count_single_namespace(self) -> int:
        """Get pods count for a single namespace."""
        loop = asyncio.get_event_loop()
        pods = await loop.run_in_executor(
            None, self.core_v1.list_namespaced_pod, self.namespace
        )
        return len(pods.items)

    async def _get_pods_count_all_namespaces(self) -> int:
        """Get pods count across all namespaces."""
        loop = asyncio.get_event_loop()
        pods = await loop.run_in_executor(None, self.core_v1.list_pod_for_all_namespaces)
        return len(pods.items)

    async def _get_pods_count_aiohttp(self) -> int:
        """Get pods count using aiohttp as fallback for single namespace."""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Accept": "application/json",
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://{self.host}:{self.port}/api/v1/namespaces/{self.namespace}/pods",
                    headers=headers,
                    ssl=False,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return len(data.get("items", []))
                    else:
                        _LOGGER.error("aiohttp pods request failed with status: %s", response.status)
                        return 0
        except Exception as ex:
            _LOGGER.error("aiohttp pods request failed: %s", ex)
            return 0

    async def _get_pods_count_all_namespaces_aiohttp(self) -> int:
        """Get pods count using aiohttp as fallback for all namespaces."""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Accept": "application/json",
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://{self.host}:{self.port}/api/v1/pods",
                    headers=headers,
                    ssl=False,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return len(data.get("items", []))
                    else:
                        _LOGGER.error("aiohttp all pods request failed with status: %s", response.status)
                        return 0
        except Exception as ex:
            _LOGGER.error("aiohttp all pods request failed: %s", ex)
            return 0

    async def get_nodes_count(self) -> int:
        """Get the count of nodes in the cluster."""
        try:
            loop = asyncio.get_event_loop()
            nodes = await loop.run_in_executor(None, self.core_v1.list_node)
            return len(nodes.items)
        except Exception as ex:
            _LOGGER.error("Failed to get nodes count: %s", ex)
            # Fallback to aiohttp
            return await self._get_nodes_count_aiohttp()

    async def _get_nodes_count_aiohttp(self) -> int:
        """Get nodes count using aiohttp as fallback."""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Accept": "application/json",
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://{self.host}:{self.port}/api/v1/nodes",
                    headers=headers,
                    ssl=False,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return len(data.get("items", []))
                    else:
                        _LOGGER.error("aiohttp nodes request failed with status: %s", response.status)
                        return 0
        except Exception as ex:
            _LOGGER.error("aiohttp nodes request failed: %s", ex)
            return 0

    async def get_services_count(self) -> int:
        """Get the count of services in the namespace(s)."""
        try:
            if self.monitor_all_namespaces:
                return await self._get_services_count_all_namespaces()
            else:
                return await self._get_services_count_single_namespace()
        except Exception as ex:
            _LOGGER.error("Failed to get services count: %s", ex)
            # Fallback to aiohttp
            if self.monitor_all_namespaces:
                return await self._get_services_count_all_namespaces_aiohttp()
            else:
                return await self._get_services_count_aiohttp()

    async def _get_services_count_single_namespace(self) -> int:
        """Get services count for a single namespace."""
        loop = asyncio.get_event_loop()
        services = await loop.run_in_executor(
            None, self.core_v1.list_namespaced_service, self.namespace
        )
        return len(services.items)

    async def _get_services_count_all_namespaces(self) -> int:
        """Get services count across all namespaces."""
        loop = asyncio.get_event_loop()
        services = await loop.run_in_executor(None, self.core_v1.list_service_for_all_namespaces)
        return len(services.items)

    async def _get_services_count_aiohttp(self) -> int:
        """Get services count using aiohttp as fallback for single namespace."""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Accept": "application/json",
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://{self.host}:{self.port}/api/v1/namespaces/{self.namespace}/services",
                    headers=headers,
                    ssl=False,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return len(data.get("items", []))
                    else:
                        _LOGGER.error("aiohttp services request failed with status: %s", response.status)
                        return 0
        except Exception as ex:
            _LOGGER.error("aiohttp services request failed: %s", ex)
            return 0

    async def _get_services_count_all_namespaces_aiohttp(self) -> int:
        """Get services count using aiohttp as fallback for all namespaces."""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Accept": "application/json",
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://{self.host}:{self.port}/api/v1/services",
                    headers=headers,
                    ssl=False,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return len(data.get("items", []))
                    else:
                        _LOGGER.error("aiohttp all services request failed with status: %s", response.status)
                        return 0
        except Exception as ex:
            _LOGGER.error("aiohttp all services request failed: %s", ex)
            return 0

    async def get_deployments_count(self) -> int:
        """Get the count of deployments in the namespace(s)."""
        try:
            if self.monitor_all_namespaces:
                return await self._get_deployments_count_all_namespaces()
            else:
                return await self._get_deployments_count_single_namespace()
        except Exception as ex:
            _LOGGER.error("Failed to get deployments count: %s", ex)
            # Fallback to aiohttp
            if self.monitor_all_namespaces:
                return await self._get_deployments_count_all_namespaces_aiohttp()
            else:
                return await self._get_deployments_count_aiohttp()

    async def _get_deployments_count_single_namespace(self) -> int:
        """Get deployments count for a single namespace."""
        loop = asyncio.get_event_loop()
        deployments = await loop.run_in_executor(
            None, self.apps_v1.list_namespaced_deployment, self.namespace
        )
        return len(deployments.items)

    async def _get_deployments_count_all_namespaces(self) -> int:
        """Get deployments count across all namespaces."""
        loop = asyncio.get_event_loop()
        deployments = await loop.run_in_executor(None, self.apps_v1.list_deployment_for_all_namespaces)
        return len(deployments.items)

    async def _get_deployments_count_aiohttp(self) -> int:
        """Get deployments count using aiohttp as fallback for single namespace."""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Accept": "application/json",
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://{self.host}:{self.port}/apis/apps/v1/namespaces/{self.namespace}/deployments",
                    headers=headers,
                    ssl=False,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return len(data.get("items", []))
                    else:
                        _LOGGER.error("aiohttp deployments request failed with status: %s", response.status)
                        return 0
        except Exception as ex:
            _LOGGER.error("aiohttp deployments request failed: %s", ex)
            return 0

    async def _get_deployments_count_all_namespaces_aiohttp(self) -> int:
        """Get deployments count using aiohttp as fallback for all namespaces."""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Accept": "application/json",
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://{self.host}:{self.port}/apis/apps/v1/deployments",
                    headers=headers,
                    ssl=False,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return len(data.get("items", []))
                    else:
                        _LOGGER.error("aiohttp all deployments request failed with status: %s", response.status)
                        return 0
        except Exception as ex:
            _LOGGER.error("aiohttp all deployments request failed: %s", ex)
            return 0

    async def get_deployments(self) -> list[dict[str, Any]]:
        """Get all deployments in the namespace(s) with their details."""
        try:
            if self.monitor_all_namespaces:
                return await self._get_deployments_all_namespaces()
            else:
                return await self._get_deployments_single_namespace()
        except Exception as ex:
            _LOGGER.error("Failed to get deployments: %s", ex)
            # Fallback to aiohttp
            if self.monitor_all_namespaces:
                return await self._get_deployments_all_namespaces_aiohttp()
            else:
                return await self._get_deployments_aiohttp()

    async def _get_deployments_single_namespace(self) -> list[dict[str, Any]]:
        """Get deployments for a single namespace."""
        loop = asyncio.get_event_loop()
        deployments = await loop.run_in_executor(
            None, self.apps_v1.list_namespaced_deployment, self.namespace
        )

        deployment_list = []
        for deployment in deployments.items:
            deployment_info = {
                "name": deployment.metadata.name,
                "namespace": deployment.metadata.namespace,
                "replicas": deployment.spec.replicas if deployment.spec.replicas else 0,
                "available_replicas": deployment.status.available_replicas if deployment.status.available_replicas else 0,
                "ready_replicas": deployment.status.ready_replicas if deployment.status.ready_replicas else 0,
                "is_running": deployment.status.available_replicas > 0 if deployment.status.available_replicas else False,
            }
            deployment_list.append(deployment_info)

        return deployment_list

    async def _get_deployments_all_namespaces(self) -> list[dict[str, Any]]:
        """Get deployments across all namespaces."""
        loop = asyncio.get_event_loop()
        deployments = await loop.run_in_executor(None, self.apps_v1.list_deployment_for_all_namespaces)

        deployment_list = []
        for deployment in deployments.items:
            deployment_info = {
                "name": deployment.metadata.name,
                "namespace": deployment.metadata.namespace,
                "replicas": deployment.spec.replicas if deployment.spec.replicas else 0,
                "available_replicas": deployment.status.available_replicas if deployment.status.available_replicas else 0,
                "ready_replicas": deployment.status.ready_replicas if deployment.status.ready_replicas else 0,
                "is_running": deployment.status.available_replicas > 0 if deployment.status.available_replicas else False,
            }
            deployment_list.append(deployment_info)

        return deployment_list

    async def _get_deployments_aiohttp(self) -> list[dict[str, Any]]:
        """Get deployments using aiohttp as fallback for single namespace."""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Accept": "application/json",
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://{self.host}:{self.port}/apis/apps/v1/namespaces/{self.namespace}/deployments",
                    headers=headers,
                    ssl=False,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        deployment_list = []
                        for deployment in data.get("items", []):
                            deployment_info = {
                                "name": deployment["metadata"]["name"],
                                "namespace": deployment["metadata"]["namespace"],
                                "replicas": deployment["spec"].get("replicas", 0),
                                "available_replicas": deployment["status"].get("availableReplicas", 0),
                                "ready_replicas": deployment["status"].get("readyReplicas", 0),
                                "is_running": deployment["status"].get("availableReplicas", 0) > 0,
                            }
                            deployment_list.append(deployment_info)
                        return deployment_list
                    else:
                        _LOGGER.error("aiohttp deployments request failed with status: %s", response.status)
                        return []
        except Exception as ex:
            _LOGGER.error("aiohttp deployments request failed: %s", ex)
            return []

    async def _get_deployments_all_namespaces_aiohttp(self) -> list[dict[str, Any]]:
        """Get deployments using aiohttp as fallback for all namespaces."""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Accept": "application/json",
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://{self.host}:{self.port}/apis/apps/v1/deployments",
                    headers=headers,
                    ssl=False,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        deployment_list = []
                        for deployment in data.get("items", []):
                            deployment_info = {
                                "name": deployment["metadata"]["name"],
                                "namespace": deployment["metadata"]["namespace"],
                                "replicas": deployment["spec"].get("replicas", 0),
                                "available_replicas": deployment["status"].get("availableReplicas", 0),
                                "ready_replicas": deployment["status"].get("readyReplicas", 0),
                                "is_running": deployment["status"].get("availableReplicas", 0) > 0,
                            }
                            deployment_list.append(deployment_info)
                        return deployment_list
                    else:
                        _LOGGER.error("aiohttp all deployments request failed with status: %s", response.status)
                        return []
        except Exception as ex:
            _LOGGER.error("aiohttp all deployments request failed: %s", ex)
            return []

    async def scale_deployment(self, deployment_name: str, replicas: int, namespace: str = None) -> bool:
        """Scale a deployment to the specified number of replicas."""
        try:
            target_namespace = namespace or self.namespace
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None, self.apps_v1.patch_namespaced_deployment_scale,
                deployment_name, target_namespace, {"spec": {"replicas": replicas}}
            )
            return True
        except Exception as ex:
            _LOGGER.error("Failed to scale deployment: %s", ex)
            # Fallback to aiohttp
            return await self._scale_deployment_aiohttp(deployment_name, replicas, namespace)

    async def _scale_deployment_aiohttp(self, deployment_name: str, replicas: int, namespace: str = None) -> bool:
        """Scale deployment using aiohttp as fallback."""
        try:
            target_namespace = namespace or self.namespace
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Accept": "application/json",
                "Content-Type": "application/strategic-merge-patch+json",
            }

            patch_data = {"spec": {"replicas": replicas}}

            async with aiohttp.ClientSession() as session:
                async with session.patch(
                    f"https://{self.host}:{self.port}/apis/apps/v1/namespaces/{target_namespace}/deployments/{deployment_name}/scale",
                    headers=headers,
                    json=patch_data,
                    ssl=False,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    return response.status in [200, 201]
        except Exception as ex:
            _LOGGER.error("aiohttp scale deployment failed: %s", ex)
            return False

    async def stop_deployment(self, deployment_name: str, namespace: str = None) -> bool:
        """Stop a deployment by scaling it to 0 replicas."""
        return await self.scale_deployment(deployment_name, 0, namespace)

    async def start_deployment(self, deployment_name: str, replicas: int = 1, namespace: str = None) -> bool:
        """Start a deployment by scaling it to the specified number of replicas."""
        return await self.scale_deployment(deployment_name, replicas, namespace)

    async def is_cluster_healthy(self) -> bool:
        """Check if the cluster is healthy."""
        return await self._test_connection()
