"""Kubernetes client for Home Assistant integration."""
from __future__ import annotations

import asyncio
import logging
import time
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

        # Error deduplication tracking
        self._last_auth_error_time = 0
        self._auth_error_cooldown = 300  # 5 minutes between auth error logs

        # Initialize Kubernetes client
        self._setup_kubernetes_client()

    def _log_error(self, operation: str, error: Exception, context: str = "") -> None:
        """Log errors with structured context and actionable information."""
        cluster_info = f"cluster={self.cluster_name}, host={self.host}:{self.port}"
        namespace_info = f"namespace={self.namespace}" if not self.monitor_all_namespaces else "all_namespaces"

        if isinstance(error, ApiException):
            # Handle Kubernetes API exceptions
            if error.status == 401:
                # Deduplicate authentication errors to reduce log noise
                current_time = time.time()
                if current_time - self._last_auth_error_time > self._auth_error_cooldown:
                    _LOGGER.error(
                        "Authentication failed for %s (%s, %s). Check API token and RBAC permissions. "
                        "This error will be suppressed for 5 minutes to reduce log noise.",
                        operation, cluster_info, namespace_info
                    )
                    self._last_auth_error_time = current_time
                else:
                    _LOGGER.debug(
                        "Authentication failed for %s (%s, %s) - using fallback method",
                        operation, cluster_info, namespace_info
                    )
            elif error.status == 403:
                _LOGGER.error(
                    "Permission denied for %s (%s, %s). Check RBAC roles and namespace access.",
                    operation, cluster_info, namespace_info
                )
            elif error.status == 404:
                _LOGGER.error(
                    "Resource not found for %s (%s, %s). Check namespace and resource names.",
                    operation, cluster_info, namespace_info
                )
            elif error.status >= 500:
                _LOGGER.error(
                    "Kubernetes API server error during %s (%s, %s): %s (status: %s)",
                    operation, cluster_info, namespace_info, error.reason, error.status
                )
            else:
                _LOGGER.error(
                    "API error during %s (%s, %s): %s (status: %s)",
                    operation, cluster_info, namespace_info, error.reason, error.status
                )
        elif isinstance(error, aiohttp.ClientError):
            # Handle network/HTTP errors
            _LOGGER.error(
                "Network error during %s (%s, %s): %s",
                operation, cluster_info, namespace_info, str(error)
            )
        elif isinstance(error, asyncio.TimeoutError):
            _LOGGER.error(
                "Timeout during %s (%s, %s). Check network connectivity and API server response time.",
                operation, cluster_info, namespace_info
            )
        else:
            # Handle other exceptions
            _LOGGER.error(
                "Unexpected error during %s (%s, %s): %s",
                operation, cluster_info, namespace_info, str(error)
            )

    def _log_success(self, operation: str, details: str = "") -> None:
        """Log successful operations with context."""
        cluster_info = f"cluster={self.cluster_name}, host={self.host}:{self.port}"
        namespace_info = f"namespace={self.namespace}" if not self.monitor_all_namespaces else "all_namespaces"

        if details:
            _LOGGER.debug("Successfully completed %s (%s, %s): %s", operation, cluster_info, namespace_info, details)
        else:
            _LOGGER.debug("Successfully completed %s (%s, %s)", operation, cluster_info, namespace_info)

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

        _LOGGER.debug("Kubernetes client configured: host=%s, verify_ssl=%s, ca_cert=%s",
                     configuration.host, self.verify_ssl, "provided" if self.ca_cert else "none")

    async def _test_connection(self) -> bool:
        """Test the connection to Kubernetes."""
        # Use aiohttp as primary since it works better with SSL configuration
        return await self._test_connection_aiohttp()

    async def _test_connection_aiohttp(self) -> bool:
        """Test the connection using aiohttp as primary method."""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Accept": "application/json",
            }

            _LOGGER.debug("Testing connection with aiohttp...")
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://{self.host}:{self.port}/api/v1/",
                    headers=headers,
                    ssl=False,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        self._log_success("connection test", "using aiohttp")
                        return True
                    else:
                        _LOGGER.error("aiohttp connection test failed with status: %s", response.status)
                        return False
        except Exception as ex:
            self._log_error("aiohttp connection test", ex)
            return False

    async def get_pods_count(self) -> int:
        """Get the count of pods in the namespace(s)."""
        try:
            # Test connection first
            if not await self._test_connection():
                _LOGGER.error("Cannot connect to Kubernetes API")
                return 0

            # Use aiohttp as primary since it works better with SSL configuration
            if self.monitor_all_namespaces:
                result = await self._get_pods_count_all_namespaces_aiohttp()
            else:
                result = await self._get_pods_count_aiohttp()

            if result is not None:
                self._log_success("get pods count", f"retrieved {result} pods")
            return result

        except Exception as ex:
            self._log_error("get pods count", ex)
            return 0

    async def _get_pods_count_single_namespace(self) -> int:
        """Get pods count for a single namespace."""
        loop = asyncio.get_event_loop()
        pods = await loop.run_in_executor(
            None, self.core_v1.list_namespaced_pod, self.namespace
        )
        count = len(pods.items)
        self._log_success("get pods count", f"found {count} pods")
        return count

    async def _get_pods_count_all_namespaces(self) -> int:
        """Get pods count across all namespaces."""
        loop = asyncio.get_event_loop()
        pods = await loop.run_in_executor(None, self.core_v1.list_pod_for_all_namespaces)
        count = len(pods.items)
        self._log_success("get pods count", f"found {count} pods across all namespaces")
        return count

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
            self._log_error("aiohttp get pods count", ex)
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
            self._log_error("aiohttp get all pods count", ex)
            return 0

    async def get_nodes_count(self) -> int:
        """Get the count of nodes in the cluster."""
        try:
            # Use aiohttp as primary since it works better with SSL configuration
            result = await self._get_nodes_count_aiohttp()
            if result is not None:
                self._log_success("get nodes count", f"retrieved {result} nodes")
            return result
        except Exception as ex:
            self._log_error("get nodes count", ex)
            return 0

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
            self._log_error("aiohttp get nodes count", ex)
            return 0


    async def get_deployments_count(self) -> int:
        """Get the count of deployments in the namespace(s)."""
        try:
            # Use aiohttp as primary since it works better with SSL configuration
            if self.monitor_all_namespaces:
                result = await self._get_deployments_count_all_namespaces_aiohttp()
            else:
                result = await self._get_deployments_count_aiohttp()

            if result is not None:
                self._log_success("get deployments count", f"retrieved {result} deployments")
            return result
        except Exception as ex:
            self._log_error("get deployments count", ex)
            return 0

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
            self._log_error("aiohttp get deployments count", ex)
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
            self._log_error("aiohttp get all deployments count", ex)
            return 0

    async def get_deployments(self) -> list[dict[str, Any]]:
        """Get all deployments in the namespace(s) with their details."""
        try:
            # Use aiohttp as primary since it works better with SSL configuration
            if self.monitor_all_namespaces:
                result = await self._get_deployments_all_namespaces_aiohttp()
            else:
                result = await self._get_deployments_aiohttp()

            if result:
                self._log_success("get deployments", f"retrieved {len(result)} deployments")
            return result
        except Exception as ex:
            self._log_error("get deployments", ex)
            return []

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
            self._log_error("aiohttp get deployments", ex)
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
            self._log_error("aiohttp get all deployments", ex)
            return []

    async def scale_deployment(self, deployment_name: str, replicas: int, namespace: str = None) -> bool:
        """Scale a deployment to the specified number of replicas."""
        try:
            # Try aiohttp first since it works better with SSL configuration
            result = await self._scale_deployment_aiohttp(deployment_name, replicas, namespace)
            if result:
                _LOGGER.info("Successfully scaled deployment %s to %d replicas", deployment_name, replicas)
                return result

            # Fallback to official Kubernetes client
            _LOGGER.debug("aiohttp failed, trying official Kubernetes client for deployment scaling")
            result = await self._scale_deployment_kubernetes(deployment_name, replicas, namespace)
            if result:
                _LOGGER.info("Successfully scaled deployment %s to %d replicas using official client", deployment_name, replicas)
            return result
        except Exception as ex:
            self._log_error(f"scale deployment {deployment_name}", ex, f"target_replicas={replicas}")
            return False

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
                    if response.status in [200, 201]:
                        _LOGGER.info("Successfully scaled deployment %s to %d replicas using aiohttp", deployment_name, replicas)
                        return True
                    else:
                        response_text = await response.text()
                        _LOGGER.error("aiohttp scale deployment failed with status %s: %s", response.status, response_text)
                        return False
        except Exception as ex:
            self._log_error(f"aiohttp scale deployment {deployment_name}", ex, f"target_replicas={replicas}")
            return False

    async def _scale_deployment_kubernetes(self, deployment_name: str, replicas: int, namespace: str = None) -> bool:
        """Scale deployment using the official Kubernetes client."""
        try:
            target_namespace = namespace or self.namespace

            # Get the current deployment
            loop = asyncio.get_event_loop()
            deployment = await loop.run_in_executor(
                None, self.apps_v1.read_namespaced_deployment, deployment_name, target_namespace
            )

            # Update the replicas
            deployment.spec.replicas = replicas

            # Apply the update
            await loop.run_in_executor(
                None, self.apps_v1.replace_namespaced_deployment,
                deployment_name, target_namespace, deployment
            )

            _LOGGER.info("Successfully scaled deployment %s to %d replicas using official client", deployment_name, replicas)
            return True
        except Exception as ex:
            self._log_error(f"official client scale deployment {deployment_name}", ex, f"target_replicas={replicas}")
            return False

    async def stop_deployment(self, deployment_name: str, namespace: str = None) -> bool:
        """Stop a deployment by scaling it to 0 replicas."""
        return await self.scale_deployment(deployment_name, 0, namespace)

    async def start_deployment(self, deployment_name: str, replicas: int = 1, namespace: str = None) -> bool:
        """Start a deployment by scaling it to the specified number of replicas."""
        return await self.scale_deployment(deployment_name, replicas, namespace)

    # StatefulSet methods
    async def get_statefulsets_count(self) -> int:
        """Get the count of StatefulSets in the namespace(s)."""
        try:
            if self.monitor_all_namespaces:
                result = await self._get_statefulsets_count_all_namespaces_aiohttp()
            else:
                result = await self._get_statefulsets_count_aiohttp()

            if result is not None:
                self._log_success("get statefulsets count", f"count: {result}")
            return result or 0
        except Exception as ex:
            self._log_error("get statefulsets count", ex)
            return 0

    async def _get_statefulsets_count_single_namespace(self) -> int:
        """Get StatefulSets count for a single namespace."""
        loop = asyncio.get_event_loop()
        statefulsets = await loop.run_in_executor(
            None, self.apps_v1.list_namespaced_stateful_set, self.namespace
        )
        return len(statefulsets.items)

    async def _get_statefulsets_count_all_namespaces(self) -> int:
        """Get StatefulSets count across all namespaces."""
        loop = asyncio.get_event_loop()
        statefulsets = await loop.run_in_executor(None, self.apps_v1.list_stateful_set_for_all_namespaces)
        return len(statefulsets.items)

    async def _get_statefulsets_count_aiohttp(self) -> int:
        """Get StatefulSets count using aiohttp as fallback for single namespace."""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Accept": "application/json",
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://{self.host}:{self.port}/apis/apps/v1/namespaces/{self.namespace}/statefulsets",
                    headers=headers,
                    ssl=False,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return len(data.get("items", []))
                    else:
                        _LOGGER.error("aiohttp statefulsets count request failed with status: %s", response.status)
                        return 0
        except Exception as ex:
            self._log_error("aiohttp get statefulsets count", ex)
            return 0

    async def _get_statefulsets_count_all_namespaces_aiohttp(self) -> int:
        """Get StatefulSets count using aiohttp as fallback for all namespaces."""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Accept": "application/json",
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://{self.host}:{self.port}/apis/apps/v1/statefulsets",
                    headers=headers,
                    ssl=False,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return len(data.get("items", []))
                    else:
                        _LOGGER.error("aiohttp statefulsets count all namespaces request failed with status: %s", response.status)
                        return 0
        except Exception as ex:
            self._log_error("aiohttp get statefulsets count all namespaces", ex)
            return 0

    async def get_statefulsets(self) -> list[dict[str, Any]]:
        """Get all StatefulSets in the namespace(s) with their details."""
        try:
            # Use aiohttp as primary since it works better with SSL configuration
            if self.monitor_all_namespaces:
                result = await self._get_statefulsets_all_namespaces_aiohttp()
            else:
                result = await self._get_statefulsets_aiohttp()

            if result:
                self._log_success("get statefulsets", f"retrieved {len(result)} statefulsets")
            return result
        except Exception as ex:
            self._log_error("get statefulsets", ex)
            return []

    async def _get_statefulsets_single_namespace(self) -> list[dict[str, Any]]:
        """Get StatefulSets for a single namespace."""
        loop = asyncio.get_event_loop()
        statefulsets = await loop.run_in_executor(
            None, self.apps_v1.list_namespaced_stateful_set, self.namespace
        )

        statefulset_list = []
        for statefulset in statefulsets.items:
            statefulset_info = {
                "name": statefulset.metadata.name,
                "namespace": statefulset.metadata.namespace,
                "replicas": statefulset.spec.replicas if statefulset.spec.replicas else 0,
                "available_replicas": statefulset.status.available_replicas if statefulset.status.available_replicas else 0,
                "ready_replicas": statefulset.status.ready_replicas if statefulset.status.ready_replicas else 0,
                "is_running": statefulset.status.available_replicas > 0 if statefulset.status.available_replicas else False,
            }
            statefulset_list.append(statefulset_info)

        return statefulset_list

    async def _get_statefulsets_all_namespaces(self) -> list[dict[str, Any]]:
        """Get StatefulSets across all namespaces."""
        loop = asyncio.get_event_loop()
        statefulsets = await loop.run_in_executor(None, self.apps_v1.list_stateful_set_for_all_namespaces)

        statefulset_list = []
        for statefulset in statefulsets.items:
            statefulset_info = {
                "name": statefulset.metadata.name,
                "namespace": statefulset.metadata.namespace,
                "replicas": statefulset.spec.replicas if statefulset.spec.replicas else 0,
                "available_replicas": statefulset.status.available_replicas if statefulset.status.available_replicas else 0,
                "ready_replicas": statefulset.status.ready_replicas if statefulset.status.ready_replicas else 0,
                "is_running": statefulset.status.available_replicas > 0 if statefulset.status.available_replicas else False,
            }
            statefulset_list.append(statefulset_info)

        return statefulset_list

    async def _get_statefulsets_aiohttp(self) -> list[dict[str, Any]]:
        """Get StatefulSets using aiohttp as fallback for single namespace."""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Accept": "application/json",
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://{self.host}:{self.port}/apis/apps/v1/namespaces/{self.namespace}/statefulsets",
                    headers=headers,
                    ssl=False,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        statefulset_list = []
                        for statefulset in data.get("items", []):
                            statefulset_info = {
                                "name": statefulset["metadata"]["name"],
                                "namespace": statefulset["metadata"]["namespace"],
                                "replicas": statefulset["spec"].get("replicas", 0),
                                "available_replicas": statefulset["status"].get("availableReplicas", 0),
                                "ready_replicas": statefulset["status"].get("readyReplicas", 0),
                                "is_running": statefulset["status"].get("availableReplicas", 0) > 0,
                            }
                            statefulset_list.append(statefulset_info)
                        return statefulset_list
                    else:
                        _LOGGER.error("aiohttp statefulsets request failed with status: %s", response.status)
                        return []
        except Exception as ex:
            self._log_error("aiohttp get statefulsets", ex)
            return []

    async def _get_statefulsets_all_namespaces_aiohttp(self) -> list[dict[str, Any]]:
        """Get StatefulSets using aiohttp as fallback for all namespaces."""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Accept": "application/json",
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://{self.host}:{self.port}/apis/apps/v1/statefulsets",
                    headers=headers,
                    ssl=False,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        statefulset_list = []
                        for statefulset in data.get("items", []):
                            statefulset_info = {
                                "name": statefulset["metadata"]["name"],
                                "namespace": statefulset["metadata"]["namespace"],
                                "replicas": statefulset["spec"].get("replicas", 0),
                                "available_replicas": statefulset["status"].get("availableReplicas", 0),
                                "ready_replicas": statefulset["status"].get("readyReplicas", 0),
                                "is_running": statefulset["status"].get("availableReplicas", 0) > 0,
                            }
                            statefulset_list.append(statefulset_info)
                        return statefulset_list
                    else:
                        _LOGGER.error("aiohttp statefulsets all namespaces request failed with status: %s", response.status)
                        return []
        except Exception as ex:
            self._log_error("aiohttp get statefulsets all namespaces", ex)
            return []

    async def scale_statefulset(self, statefulset_name: str, replicas: int, namespace: str = None) -> bool:
        """Scale a StatefulSet to the specified number of replicas."""
        try:
            # Try aiohttp first since it works better with SSL configuration
            result = await self._scale_statefulset_aiohttp(statefulset_name, replicas, namespace)
            if result:
                _LOGGER.info("Successfully scaled statefulset %s to %d replicas", statefulset_name, replicas)
                return result

            # Fallback to official Kubernetes client
            _LOGGER.debug("aiohttp failed, trying official Kubernetes client for StatefulSet scaling")
            result = await self._scale_statefulset_kubernetes(statefulset_name, replicas, namespace)
            if result:
                _LOGGER.info("Successfully scaled statefulset %s to %d replicas using official client", statefulset_name, replicas)
            return result
        except Exception as ex:
            self._log_error(f"scale statefulset {statefulset_name}", ex, f"target_replicas={replicas}")
            return False

    async def _scale_statefulset_aiohttp(self, statefulset_name: str, replicas: int, namespace: str = None) -> bool:
        """Scale StatefulSet using aiohttp."""
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
                    f"https://{self.host}:{self.port}/apis/apps/v1/namespaces/{target_namespace}/statefulsets/{statefulset_name}/scale",
                    headers=headers,
                    json=patch_data,
                    ssl=False,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status in [200, 201]:
                        _LOGGER.info("Successfully scaled statefulset %s to %d replicas using aiohttp", statefulset_name, replicas)
                        return True
                    else:
                        response_text = await response.text()
                        _LOGGER.error("aiohttp scale statefulset failed with status %s: %s", response.status, response_text)
                        return False
        except Exception as ex:
            self._log_error(f"aiohttp scale statefulset {statefulset_name}", ex, f"target_replicas={replicas}")
            return False

    async def _scale_statefulset_kubernetes(self, statefulset_name: str, replicas: int, namespace: str = None) -> bool:
        """Scale StatefulSet using the official Kubernetes client."""
        try:
            target_namespace = namespace or self.namespace

            # Get the current StatefulSet
            loop = asyncio.get_event_loop()
            statefulset = await loop.run_in_executor(
                None, self.apps_v1.read_namespaced_stateful_set, statefulset_name, target_namespace
            )

            # Update the replicas
            statefulset.spec.replicas = replicas

            # Apply the update
            await loop.run_in_executor(
                None, self.apps_v1.replace_namespaced_stateful_set,
                statefulset_name, target_namespace, statefulset
            )

            _LOGGER.info("Successfully scaled statefulset %s to %d replicas using official client", statefulset_name, replicas)
            return True
        except Exception as ex:
            self._log_error(f"official client scale statefulset {statefulset_name}", ex, f"target_replicas={replicas}")
            return False

    async def stop_statefulset(self, statefulset_name: str, namespace: str = None) -> bool:
        """Stop a StatefulSet by scaling it to 0 replicas."""
        return await self.scale_statefulset(statefulset_name, 0, namespace)

    async def start_statefulset(self, statefulset_name: str, replicas: int = 1, namespace: str = None) -> bool:
        """Start a StatefulSet by scaling it to the specified number of replicas."""
        return await self.scale_statefulset(statefulset_name, replicas, namespace)

    async def compare_authentication_methods(self) -> dict[str, Any]:
        """Compare authentication methods to help diagnose issues."""
        result = {
            "kubernetes_client": {
                "host": f"https://{self.host}:{self.port}",
                "headers": {"authorization": f"Bearer {self.api_token[:10]}..." if len(self.api_token) > 10 else "Bearer [token]"},
                "verify_ssl": self.verify_ssl,
                "ca_cert": "provided" if self.ca_cert else "none"
            },
            "aiohttp_fallback": {
                "url": f"https://{self.host}:{self.port}/api/v1/",
                "headers": {"Authorization": f"Bearer {self.api_token[:10]}..." if len(self.api_token) > 10 else "Bearer [token]"},
                "ssl": False
            },
            "token_info": {
                "length": len(self.api_token),
                "starts_with_ey": self.api_token.startswith("ey"),
                "contains_dots": self.api_token.count(".") == 2
            }
        }

        # Test both methods
        try:
            # Test kubernetes client
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self.core_v1.get_api_resources)
            result["kubernetes_client"]["success"] = True
            result["kubernetes_client"]["error"] = None
        except Exception as ex:
            result["kubernetes_client"]["success"] = False
            result["kubernetes_client"]["error"] = str(ex)

        try:
            # Test aiohttp
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
                    result["aiohttp_fallback"]["success"] = response.status == 200
                    result["aiohttp_fallback"]["status_code"] = response.status
                    result["aiohttp_fallback"]["error"] = None if response.status == 200 else f"HTTP {response.status}"
        except Exception as ex:
            result["aiohttp_fallback"]["success"] = False
            result["aiohttp_fallback"]["error"] = str(ex)

        return result

    async def test_authentication(self) -> dict[str, Any]:
        """Test authentication and return detailed status information."""
        result = {
            "authenticated": False,
            "method": "unknown",
            "error": None,
            "details": {}
        }

        # Test with kubernetes client first
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self.core_v1.get_api_resources)
            result["authenticated"] = True
            result["method"] = "kubernetes_client"
            result["details"]["api_resources"] = "success"
            return result
        except ApiException as ex:
            result["error"] = f"API Exception: {ex.status} - {ex.reason}"
            result["details"]["api_status"] = ex.status
            result["details"]["api_reason"] = ex.reason
        except Exception as ex:
            result["error"] = f"Kubernetes client error: {str(ex)}"

        # Test with aiohttp fallback
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
                    if response.status == 200:
                        result["authenticated"] = True
                        result["method"] = "aiohttp_fallback"
                        result["details"]["http_status"] = response.status
                        result["error"] = None
                    else:
                        result["error"] = f"HTTP error: {response.status}"
                        result["details"]["http_status"] = response.status
        except Exception as ex:
            if not result["error"]:
                result["error"] = f"aiohttp error: {str(ex)}"

        return result

    async def is_cluster_healthy(self) -> bool:
        """Check if the cluster is healthy."""
        return await self._test_connection()
