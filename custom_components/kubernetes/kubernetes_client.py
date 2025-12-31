"""Kubernetes client for Home Assistant integration."""

from __future__ import annotations

import asyncio
import logging
import ssl
import time
from typing import Any

import aiohttp

# Use absolute import to avoid circular import with our custom component named 'kubernetes'
try:
    import kubernetes.client as k8s_client
    from kubernetes.client.rest import ApiException

except ImportError as e:
    raise ImportError(f"kubernetes package not installed: {e}") from e

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
        self.monitor_all_namespaces = config_data.get(
            CONF_MONITOR_ALL_NAMESPACES, DEFAULT_MONITOR_ALL_NAMESPACES
        )
        self.ca_cert = config_data.get(CONF_CA_CERT)
        self.verify_ssl = config_data.get(CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL)

        # Error deduplication tracking
        self._last_auth_error_time = 0.0
        self._auth_error_cooldown = 300.0  # 5 minutes between auth error logs

        # Initialize Kubernetes client
        self._setup_kubernetes_client()

    def _log_error(self, operation: str, error: Exception, context: str = "") -> None:
        """Log errors with structured context and actionable information."""
        cluster_info = f"cluster={self.cluster_name}, host={self.host}:{self.port}"
        namespace_info = (
            f"namespace={self.namespace}"
            if not self.monitor_all_namespaces
            else "all_namespaces"
        )

        if isinstance(error, ApiException):
            # Handle Kubernetes API exceptions
            if error.status == 401:
                # Deduplicate authentication errors to reduce log noise
                current_time = time.time()
                if (
                    current_time - self._last_auth_error_time
                    > self._auth_error_cooldown
                ):
                    _LOGGER.error(
                        "Authentication failed for %s (%s, %s). Check API token and RBAC permissions. "
                        "This error will be suppressed for 5 minutes to reduce log noise. "
                        "Error details: status=%s, reason='%s'",
                        operation,
                        cluster_info,
                        namespace_info,
                        error.status,
                        error.reason,
                    )
                    self._last_auth_error_time = current_time
                else:
                    _LOGGER.debug(
                        "Authentication failed for %s (%s, %s) - using fallback method",
                        operation,
                        cluster_info,
                        namespace_info,
                    )
            elif error.status == 403:
                _LOGGER.error(
                    "Permission denied for %s (%s, %s). Check RBAC roles and namespace access.",
                    operation,
                    cluster_info,
                    namespace_info,
                )
            elif error.status == 404:
                _LOGGER.error(
                    "Resource not found for %s (%s, %s). Check namespace and resource names.",
                    operation,
                    cluster_info,
                    namespace_info,
                )
            elif error.status >= 500:
                _LOGGER.error(
                    "Kubernetes API server error during %s (%s, %s): %s (status: %s)",
                    operation,
                    cluster_info,
                    namespace_info,
                    error.reason,
                    error.status,
                )
            else:
                _LOGGER.error(
                    "API error during %s (%s, %s): %s (status: %s)",
                    operation,
                    cluster_info,
                    namespace_info,
                    error.reason,
                    error.status,
                )
        elif isinstance(error, aiohttp.ClientError):
            # Handle network/HTTP errors
            _LOGGER.error(
                "Network error during %s (%s, %s): %s",
                operation,
                cluster_info,
                namespace_info,
                str(error),
            )
        elif isinstance(error, asyncio.TimeoutError):
            _LOGGER.error(
                "Timeout during %s (%s, %s). Check network connectivity and API server response time.",
                operation,
                cluster_info,
                namespace_info,
            )
        else:
            # Handle other exceptions
            _LOGGER.error(
                "Unexpected error during %s (%s, %s): %s",
                operation,
                cluster_info,
                namespace_info,
                str(error),
            )

    def _log_success(self, operation: str, details: str = "") -> None:
        """Log successful operations with context."""
        cluster_info = f"cluster={self.cluster_name}, host={self.host}:{self.port}"
        namespace_info = (
            f"namespace={self.namespace}"
            if not self.monitor_all_namespaces
            else "all_namespaces"
        )

        if details:
            _LOGGER.debug(
                "Successfully completed %s (%s, %s): %s",
                operation,
                cluster_info,
                namespace_info,
                details,
            )
        else:
            _LOGGER.debug(
                "Successfully completed %s (%s, %s)",
                operation,
                cluster_info,
                namespace_info,
            )

    def _setup_kubernetes_client(self) -> None:
        """Set up the Kubernetes client configuration."""
        configuration = k8s_client.Configuration()
        configuration.host = f"https://{self.host}:{self.port}"
        configuration.api_key = {"authorization": f"Bearer {self.api_token}"}
        configuration.api_key_prefix = {"authorization": "Bearer"}
        configuration.verify_ssl = self.verify_ssl

        if self.ca_cert:
            configuration.ssl_ca_cert = self.ca_cert

        # Create API clients
        api_client = k8s_client.ApiClient(configuration)
        self.core_v1 = k8s_client.CoreV1Api(api_client)
        self.apps_v1 = k8s_client.AppsV1Api(api_client)
        self.batch_v1 = k8s_client.BatchV1Api(api_client)  # Added BatchV1Api

        _LOGGER.debug(
            "Kubernetes client configured: host=%s, verify_ssl=%s, ca_cert=%s",
            configuration.host,
            self.verify_ssl,
            "provided" if self.ca_cert else "none",
        )

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
                    ssl=self.verify_ssl,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status == 200:
                        self._log_success("connection test", "using aiohttp")
                        return True
                    else:
                        _LOGGER.error(
                            "aiohttp connection test failed with status: %s",
                            response.status,
                        )
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
        # Use aiohttp directly since it's more reliable
        return await self._get_pods_count_aiohttp()

    async def _get_pods_count_all_namespaces(self) -> int:
        """Get pods count across all namespaces."""
        # Use aiohttp directly since it's more reliable
        return await self._get_pods_count_all_namespaces_aiohttp()

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
                    ssl=self.verify_ssl,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return len(data.get("items", []))
                    else:
                        _LOGGER.error(
                            "aiohttp pods request failed with status: %s",
                            response.status,
                        )
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
                    ssl=self.verify_ssl,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return len(data.get("items", []))
                    else:
                        _LOGGER.error(
                            "aiohttp all pods request failed with status: %s",
                            response.status,
                        )
                        return 0
        except Exception as ex:
            self._log_error("aiohttp get all pods count", ex)
            return 0

    async def get_pods(self) -> list[dict[str, Any]]:
        """Get detailed information about all pods in the namespace(s)."""
        try:
            # Test connection first
            if not await self._test_connection():
                _LOGGER.error("Cannot connect to Kubernetes API")
                return []

            # Use aiohttp as primary since it works better with SSL configuration
            if self.monitor_all_namespaces:
                result = await self._get_pods_all_namespaces_aiohttp()
            else:
                result = await self._get_pods_aiohttp()

            if result is not None:
                self._log_success("get pods", f"retrieved {len(result)} pods")
            return result

        except Exception as ex:
            self._log_error("get pods", ex)
            return []

    async def _get_pods_aiohttp(self) -> list[dict[str, Any]]:
        """Get pods using aiohttp for single namespace."""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Accept": "application/json",
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://{self.host}:{self.port}/api/v1/namespaces/{self.namespace}/pods",
                    headers=headers,
                    ssl=self.verify_ssl,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_pods_data(data.get("items", []))
                    else:
                        _LOGGER.error(
                            "aiohttp pods request failed with status: %s",
                            response.status,
                        )
                        return []
        except Exception as ex:
            self._log_error("aiohttp get pods", ex)
            return []

    async def _get_pods_all_namespaces_aiohttp(self) -> list[dict[str, Any]]:
        """Get pods using aiohttp for all namespaces."""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Accept": "application/json",
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://{self.host}:{self.port}/api/v1/pods",
                    headers=headers,
                    ssl=self.verify_ssl,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_pods_data(data.get("items", []))
                    else:
                        _LOGGER.error(
                            "aiohttp all pods request failed with status: %s",
                            response.status,
                        )
                        return []
        except Exception as ex:
            self._log_error("aiohttp get all pods", ex)
            return []

    def _parse_pods_data(self, pods: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Parse raw pod data from Kubernetes API into standardized format."""
        parsed_pods = []

        for pod in pods:
            try:
                metadata = pod.get("metadata", {})
                spec = pod.get("spec", {})
                status = pod.get("status", {})

                # Get pod phase
                phase = status.get("phase", "Unknown")

                # Get container statuses
                container_statuses = status.get("containerStatuses", [])
                ready_containers = 0
                total_containers = len(container_statuses)

                for container_status in container_statuses:
                    if container_status.get("ready", False):
                        ready_containers += 1

                # Get restart count
                restart_count = 0
                for container_status in container_statuses:
                    restart_count += container_status.get("restartCount", 0)

                # Get node name
                node_name = spec.get("nodeName", "N/A")

                # Get pod IP
                pod_ip = status.get("podIP", "N/A")

                # Get creation timestamp
                creation_timestamp = metadata.get("creationTimestamp", "N/A")

                # Get labels
                labels = metadata.get("labels", {})

                # Get owner references (to identify which workload owns this pod)
                owner_references = metadata.get("ownerReferences", [])
                owner_kind = "N/A"
                owner_name = "N/A"
                if owner_references:
                    owner = owner_references[0]
                    owner_kind = owner.get("kind", "N/A")
                    owner_name = owner.get("name", "N/A")

                parsed_pod = {
                    "name": metadata.get("name", "Unknown"),
                    "namespace": metadata.get("namespace", "default"),
                    "phase": phase,
                    "ready_containers": ready_containers,
                    "total_containers": total_containers,
                    "restart_count": restart_count,
                    "node_name": node_name,
                    "pod_ip": pod_ip,
                    "creation_timestamp": creation_timestamp,
                    "labels": labels,
                    "owner_kind": owner_kind,
                    "owner_name": owner_name,
                    "uid": metadata.get("uid", ""),
                }

                parsed_pods.append(parsed_pod)

            except Exception as ex:
                _LOGGER.warning("Failed to parse pod data: %s", ex)
                continue

        return parsed_pods

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
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return len(data.get("items", []))
                    else:
                        _LOGGER.error(
                            "aiohttp nodes request failed with status: %s",
                            response.status,
                        )
                        return 0
        except Exception as ex:
            self._log_error("aiohttp get nodes count", ex)
            return 0

    async def get_nodes(self) -> list[dict[str, Any]]:
        """Get detailed information about all nodes in the cluster."""
        try:
            _LOGGER.debug("Starting get_nodes() call")
            # Use aiohttp as primary since it works better with SSL configuration
            result = await self._get_nodes_aiohttp()
            _LOGGER.debug("get_nodes() successful: retrieved %d nodes", len(result))
            self._log_success("get nodes", f"retrieved {len(result)} nodes")
            return result
        except Exception as ex:
            _LOGGER.error("get_nodes() failed with exception: %s", ex, exc_info=True)
            self._log_error("get nodes", ex)
            return []

    async def _get_nodes_aiohttp(self) -> list[dict[str, Any]]:
        """Get detailed nodes information using aiohttp."""
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
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        _LOGGER.debug(
                            "Received nodes API response with %d items",
                            len(data.get("items", [])),
                        )
                        nodes = []
                        for i, item in enumerate(data.get("items", [])):
                            try:
                                _LOGGER.debug("Processing node item %d", i)
                                # Extract node information
                                metadata = item.get("metadata", {})
                                status = item.get("status", {})
                                spec = item.get("spec", {})

                                # Get node name
                                node_name = metadata.get("name", "unknown")
                                # Get node status
                                conditions = status.get("conditions", [])
                                ready_condition: dict[str, Any] = next(
                                    (c for c in conditions if c.get("type") == "Ready"),
                                    {},
                                )
                                node_status = (
                                    "Ready"
                                    if ready_condition.get("status") == "True"
                                    else "NotReady"
                                )

                                # Get IP addresses
                                addresses = status.get("addresses", [])
                                internal_ip = next(
                                    (
                                        addr["address"]
                                        for addr in addresses
                                        if addr.get("type") == "InternalIP"
                                    ),
                                    "N/A",
                                )
                                external_ip = next(
                                    (
                                        addr["address"]
                                        for addr in addresses
                                        if addr.get("type") == "ExternalIP"
                                    ),
                                    "N/A",
                                )

                                # Get resource information
                                capacity = status.get("capacity", {})
                                allocatable = status.get("allocatable", {})

                                # Parse memory (in GiB)
                                memory_capacity_str = capacity.get("memory", "0Ki")
                                memory_capacity_gib = self._parse_memory(
                                    memory_capacity_str, "GiB"
                                )
                                memory_allocatable_str = allocatable.get(
                                    "memory", "0Ki"
                                )
                                memory_allocatable_gib = self._parse_memory(
                                    memory_allocatable_str, "GiB"
                                )

                                # Parse CPU String
                                cpu_capacity = capacity.get("cpu", "0")
                                cpu_cores = self._parse_cpu(cpu_capacity, "cores")

                                # Get node info
                                node_info = status.get("nodeInfo", {})
                                os_image = node_info.get("osImage", "N/A")
                                kernel_version = node_info.get("kernelVersion", "N/A")
                                container_runtime = node_info.get(
                                    "containerRuntimeVersion", "N/A"
                                )
                                kubelet_version = node_info.get("kubeletVersion", "N/A")

                                # Check if node is schedulable
                                unschedulable = spec.get("unschedulable", False)
                                node_data = {
                                    "name": node_name,
                                    "status": node_status,
                                    "internal_ip": internal_ip,
                                    "external_ip": external_ip,
                                    "memory_capacity_gib": memory_capacity_gib,
                                    "memory_allocatable_gib": memory_allocatable_gib,
                                    "cpu_cores": cpu_cores,
                                    "os_image": os_image,
                                    "kernel_version": kernel_version,
                                    "container_runtime": container_runtime,
                                    "kubelet_version": kubelet_version,
                                    "schedulable": not unschedulable,
                                    "creation_timestamp": metadata.get(
                                        "creationTimestamp", "N/A"
                                    ),
                                }

                                nodes.append(node_data)
                                _LOGGER.debug(
                                    "Successfully processed node: %s (status: %s)",
                                    node_name,
                                    node_status,
                                )

                            except Exception as ex:
                                _LOGGER.error(
                                    "Failed to parse node data for item %d: %s",
                                    i,
                                    ex,
                                    exc_info=True,
                                )
                                continue
                        _LOGGER.debug("Successfully parsed %d nodes", len(nodes))
                        return nodes
                    else:
                        _LOGGER.error(
                            "aiohttp nodes request failed with status: %s",
                            response.status,
                        )
                        return []
        except Exception as ex:
            _LOGGER.error("Exception in _get_nodes_aiohttp: %s", ex, exc_info=True)
            self._log_error("aiohttp get nodes", ex)
            return []

    def _parse_memory(self, memory_str: str, output_type: str = "MiB") -> float:
        """Parse Kubernetes memory string to specified unit (KiB, MiB, or GiB)"""
        try:
            # Binary prefix multipliers (Ki, Mi, Gi, Ti, Pi, Ei)
            binary_prefixes = {
                "Ki": 1024,
                "Mi": 1024**2,
                "Gi": 1024**3,
                "Ti": 1024**4,
                "Pi": 1024**5,
                "Ei": 1024**6,
            }
            # Decimal prefix multipliers (k, M, G, T, P, E)
            decimal_prefixes = {
                "k": 1000,
                "M": 1000**2,
                "G": 1000**3,
                "T": 1000**4,
                "P": 1000**5,
                "E": 1000**6,
            }

            # Convert to bytes
            bytes_value = 0.0
            for suffix, multiplier in binary_prefixes.items():
                if memory_str.endswith(suffix):
                    bytes_value = float(memory_str[: -len(suffix)]) * multiplier
                    break
            else:
                for suffix, multiplier in decimal_prefixes.items():
                    if memory_str.endswith(suffix):
                        bytes_value = float(memory_str[: -len(suffix)]) * multiplier
                        break
                else:
                    # Plain bytes
                    bytes_value = float(memory_str)

            # Convert to requested output type
            output_multipliers = {
                "KiB": 1024,
                "MiB": 1024**2,
                "GiB": 1024**3,
            }
            multiplier = output_multipliers.get(output_type, 1024**2)
            if output_type not in output_multipliers:
                _LOGGER.warning(
                    "Invalid output type '%s', defaulting to MiB", output_type
                )
            value = bytes_value / multiplier

            # Round up to 2 decimal places
            return round(value, 2)

        except (ValueError, IndexError):
            _LOGGER.warning("Failed to parse memory string: %s", memory_str)
            return 0.0

    def _parse_cpu(self, cpu_str: str, output_type: str = "cores") -> float:
        """Parse Kubernetes CPU string to specified unit (n, u, m, or cores)"""
        try:
            # Input multipliers (to nanocores)
            input_multipliers = {
                "n": 1,
                "u": 1000,
                "m": 1_000_000,
            }
            # Output divisors (from nanocores)
            output_divisors = {
                "n": 1,
                "u": 1000,
                "m": 1_000_000,
                "cores": 1_000_000_000,
            }

            # Parse input to nanocores
            nanocores = 0.0
            for suffix, multiplier in input_multipliers.items():
                if cpu_str.endswith(suffix):
                    nanocores = float(cpu_str[: -len(suffix)]) * multiplier
                    break
            else:
                # Cores to nanocores
                nanocores = float(cpu_str) * 1_000_000_000

            # Convert to requested output type
            divisor = output_divisors.get(output_type, 1_000_000_000)
            if output_type not in output_divisors:
                _LOGGER.warning(
                    "Invalid output type '%s', defaulting to cores", output_type
                )
            value = nanocores / divisor

            # Round based on output type - cores get whole numbers, others get 2 decimal places
            if output_type == "cores" or output_type not in output_divisors:
                return int(round(value))
            return round(value, 2)

        except (ValueError, IndexError):
            _LOGGER.warning("Failed to parse CPU string: %s", cpu_str)
            return 0.0

    async def get_deployments_count(self) -> int:
        """Get the count of deployments in the namespace(s)."""
        try:
            # Use aiohttp as primary since it works better with SSL configuration
            if self.monitor_all_namespaces:
                result = await self._get_deployments_count_all_namespaces_aiohttp()
            else:
                result = await self._get_deployments_count_aiohttp()

            if result is not None:
                self._log_success(
                    "get deployments count", f"retrieved {result} deployments"
                )
            return result
        except Exception as ex:
            self._log_error("get deployments count", ex)
            return 0

    async def _get_deployments_count_single_namespace(self) -> int:
        """Get deployments count for a single namespace."""
        # Use aiohttp directly since it's more reliable
        return await self._get_deployments_count_aiohttp()

    async def _get_deployments_count_all_namespaces(self) -> int:
        """Get deployments count across all namespaces."""
        # Use aiohttp directly since it's more reliable
        return await self._get_deployments_count_all_namespaces_aiohttp()

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
                    ssl=self.verify_ssl,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return len(data.get("items", []))
                    else:
                        _LOGGER.error(
                            "aiohttp deployments request failed with status: %s",
                            response.status,
                        )
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
                    ssl=self.verify_ssl,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return len(data.get("items", []))
                    else:
                        _LOGGER.error(
                            "aiohttp all deployments request failed with status: %s",
                            response.status,
                        )
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
                await self._enrich_deployments_with_metrics(result)
                self._log_success(
                    "get deployments", f"retrieved {len(result)} deployments"
                )
            return result
        except Exception as ex:
            self._log_error("get deployments", ex)
            return []

    async def _get_deployments_single_namespace(self) -> list[dict[str, Any]]:
        """Get deployments for a single namespace."""
        # Use aiohttp directly since it's more reliable
        return await self._get_deployments_aiohttp()

    async def _get_deployments_all_namespaces(self) -> list[dict[str, Any]]:
        """Get deployments across all namespaces."""
        loop = asyncio.get_event_loop()
        deployments = await loop.run_in_executor(
            None, self.apps_v1.list_deployment_for_all_namespaces
        )

        deployment_list = []
        for deployment in deployments.items:
            deployment_info = {
                "name": deployment.metadata.name,
                "namespace": deployment.metadata.namespace,
                "replicas": deployment.spec.replicas if deployment.spec.replicas else 0,
                "available_replicas": (
                    deployment.status.available_replicas
                    if deployment.status.available_replicas
                    else 0
                ),
                "ready_replicas": (
                    deployment.status.ready_replicas
                    if deployment.status.ready_replicas
                    else 0
                ),
                "is_running": (
                    deployment.status.available_replicas > 0
                    if deployment.status.available_replicas
                    else False
                ),
                "selector": (
                    deployment.spec.selector.match_labels
                    if deployment.spec.selector
                    else {}
                ),
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
                    ssl=self.verify_ssl,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        deployment_list = []
                        for deployment in data.get("items", []):
                            deployment_info = {
                                "name": deployment["metadata"]["name"],
                                "namespace": deployment["metadata"]["namespace"],
                                "replicas": deployment["spec"].get("replicas", 0),
                                "available_replicas": deployment["status"].get(
                                    "availableReplicas", 0
                                ),
                                "ready_replicas": deployment["status"].get(
                                    "readyReplicas", 0
                                ),
                                "is_running": deployment["status"].get(
                                    "availableReplicas", 0
                                )
                                > 0,
                                "selector": deployment.get("spec", {})
                                .get("selector", {})
                                .get("matchLabels", {}),
                            }
                            deployment_list.append(deployment_info)
                        return deployment_list
                    else:
                        _LOGGER.error(
                            "aiohttp deployments request failed with status: %s",
                            response.status,
                        )
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
                    ssl=self.verify_ssl,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        deployment_list = []
                        for deployment in data.get("items", []):
                            deployment_info = {
                                "name": deployment["metadata"]["name"],
                                "namespace": deployment["metadata"]["namespace"],
                                "replicas": deployment["spec"].get("replicas", 0),
                                "available_replicas": deployment["status"].get(
                                    "availableReplicas", 0
                                ),
                                "ready_replicas": deployment["status"].get(
                                    "readyReplicas", 0
                                ),
                                "is_running": deployment["status"].get(
                                    "availableReplicas", 0
                                )
                                > 0,
                                "selector": deployment.get("spec", {})
                                .get("selector", {})
                                .get("matchLabels", {}),
                            }
                            deployment_list.append(deployment_info)
                        return deployment_list
                    else:
                        _LOGGER.error(
                            "aiohttp all deployments request failed with status: %s",
                            response.status,
                        )
                        return []
        except Exception as ex:
            self._log_error("aiohttp get all deployments count", ex)
            return []

    async def scale_deployment(
        self, deployment_name: str, replicas: int, namespace: str | None = None
    ) -> bool:
        """Scale a deployment to the specified number of replicas."""
        try:
            # Try aiohttp first since it works better with SSL configuration
            result = await self._scale_deployment_aiohttp(
                deployment_name, replicas, namespace
            )
            if result:
                _LOGGER.info(
                    "Successfully scaled deployment %s to %d replicas",
                    deployment_name,
                    replicas,
                )
                return result

            # Fallback to official Kubernetes client
            _LOGGER.debug(
                "aiohttp failed, trying official Kubernetes client for deployment scaling"
            )
            result = await self._scale_deployment_kubernetes(
                deployment_name, replicas, namespace
            )
            if result:
                _LOGGER.info(
                    "Successfully scaled deployment %s to %d replicas using official client",
                    deployment_name,
                    replicas,
                )
            return result
        except Exception as ex:
            self._log_error(
                f"scale deployment {deployment_name}", ex, f"target_replicas={replicas}"
            )
            return False

    async def _scale_deployment_aiohttp(
        self, deployment_name: str, replicas: int, namespace: str | None = None
    ) -> bool:
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
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status in [200, 201]:
                        _LOGGER.info(
                            "Successfully scaled deployment %s to %d replicas using aiohttp",
                            deployment_name,
                            replicas,
                        )
                        return True
                    else:
                        response_text = await response.text()
                        _LOGGER.error(
                            "aiohttp scale deployment failed with status %s: %s",
                            response.status,
                            response_text,
                        )
                        return False
        except Exception as ex:
            self._log_error(
                f"aiohttp scale deployment {deployment_name}",
                ex,
                f"target_replicas={replicas}",
            )
            return False

    async def _scale_deployment_kubernetes(
        self, deployment_name: str, replicas: int, namespace: str | None = None
    ) -> bool:
        """Scale deployment using the official Kubernetes client."""
        try:
            target_namespace = namespace or self.namespace

            # Get the current deployment
            loop = asyncio.get_event_loop()
            deployment = await loop.run_in_executor(
                None,
                self.apps_v1.read_namespaced_deployment,
                deployment_name,
                target_namespace,
            )

            # Update the replicas
            deployment.spec.replicas = replicas

            # Apply the update
            await loop.run_in_executor(
                None,
                self.apps_v1.replace_namespaced_deployment,
                deployment_name,
                target_namespace,
                deployment,
            )

            _LOGGER.info(
                "Successfully scaled deployment %s to %d replicas using official client",
                deployment_name,
                replicas,
            )
            return True
        except Exception as ex:
            self._log_error(
                f"official client scale deployment {deployment_name}",
                ex,
                f"target_replicas={replicas}",
            )
            return False

    async def stop_deployment(
        self, deployment_name: str, namespace: str | None = None
    ) -> bool:
        """Stop a deployment by scaling it to 0 replicas."""
        return await self.scale_deployment(deployment_name, 0, namespace)

    async def start_deployment(
        self, deployment_name: str, replicas: int = 1, namespace: str | None = None
    ) -> bool:
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
        statefulsets = await loop.run_in_executor(
            None, self.apps_v1.list_stateful_set_for_all_namespaces
        )
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
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return len(data.get("items", []))
                    else:
                        _LOGGER.error(
                            "aiohttp statefulsets count request failed with status: %s",
                            response.status,
                        )
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
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return len(data.get("items", []))
                    else:
                        _LOGGER.error(
                            "aiohttp statefulsets count all namespaces request failed with status: %s",
                            response.status,
                        )
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
                await self._enrich_statefulsets_with_metrics(result)
                self._log_success(
                    "get statefulsets", f"retrieved {len(result)} statefulsets"
                )
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
                "replicas": (
                    statefulset.spec.replicas if statefulset.spec.replicas else 0
                ),
                "available_replicas": (
                    statefulset.status.available_replicas
                    if statefulset.status.available_replicas
                    else 0
                ),
                "ready_replicas": (
                    statefulset.status.ready_replicas
                    if statefulset.status.ready_replicas
                    else 0
                ),
                "is_running": (
                    statefulset.status.available_replicas > 0
                    if statefulset.status.available_replicas
                    else False
                ),
                "selector": (
                    statefulset.spec.selector.match_labels
                    if statefulset.spec.selector
                    else {}
                ),
            }
            statefulset_list.append(statefulset_info)

        return statefulset_list

    async def _get_statefulsets_all_namespaces(self) -> list[dict[str, Any]]:
        """Get StatefulSets across all namespaces."""
        loop = asyncio.get_event_loop()
        statefulsets = await loop.run_in_executor(
            None, self.apps_v1.list_stateful_set_for_all_namespaces
        )

        statefulset_list = []
        for statefulset in statefulsets.items:
            statefulset_info = {
                "name": statefulset.metadata.name,
                "namespace": statefulset.metadata.namespace,
                "replicas": (
                    statefulset.spec.replicas if statefulset.spec.replicas else 0
                ),
                "available_replicas": (
                    statefulset.status.available_replicas
                    if statefulset.status.available_replicas
                    else 0
                ),
                "ready_replicas": (
                    statefulset.status.ready_replicas
                    if statefulset.status.ready_replicas
                    else 0
                ),
                "is_running": (
                    statefulset.status.available_replicas > 0
                    if statefulset.status.available_replicas
                    else False
                ),
                "selector": (
                    statefulset.spec.selector.match_labels
                    if statefulset.spec.selector
                    else {}
                ),
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
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        statefulset_list = []
                        for statefulset in data.get("items", []):
                            statefulset_info = {
                                "name": statefulset["metadata"]["name"],
                                "namespace": statefulset["metadata"]["namespace"],
                                "replicas": statefulset["spec"].get("replicas", 0),
                                "available_replicas": statefulset["status"].get(
                                    "availableReplicas", 0
                                ),
                                "ready_replicas": statefulset["status"].get(
                                    "readyReplicas", 0
                                ),
                                "is_running": statefulset["status"].get(
                                    "availableReplicas", 0
                                )
                                > 0,
                                "selector": statefulset.get("spec", {})
                                .get("selector", {})
                                .get("matchLabels", {}),
                            }
                            statefulset_list.append(statefulset_info)
                        return statefulset_list
                    else:
                        _LOGGER.error(
                            "aiohttp statefulsets request failed with status: %s",
                            response.status,
                        )
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
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        statefulset_list = []
                        for statefulset in data.get("items", []):
                            statefulset_info = {
                                "name": statefulset["metadata"]["name"],
                                "namespace": statefulset["metadata"]["namespace"],
                                "replicas": statefulset["spec"].get("replicas", 0),
                                "available_replicas": statefulset["status"].get(
                                    "availableReplicas", 0
                                ),
                                "ready_replicas": statefulset["status"].get(
                                    "readyReplicas", 0
                                ),
                                "is_running": statefulset["status"].get(
                                    "availableReplicas", 0
                                )
                                > 0,
                                "selector": statefulset.get("spec", {})
                                .get("selector", {})
                                .get("matchLabels", {}),
                            }
                            statefulset_list.append(statefulset_info)
                        return statefulset_list
                    else:
                        _LOGGER.error(
                            "aiohttp all statefulsets request failed with status: %s",
                            response.status,
                        )
                        return []
        except Exception as ex:
            self._log_error("aiohttp get all statefulsets count", ex)
            return []

    async def scale_statefulset(
        self, statefulset_name: str, replicas: int, namespace: str | None = None
    ) -> bool:
        """Scale a StatefulSet to the specified number of replicas."""
        try:
            # Try aiohttp first since it works better with SSL configuration
            result = await self._scale_statefulset_aiohttp(
                statefulset_name, replicas, namespace
            )
            if result:
                _LOGGER.info(
                    "Successfully scaled statefulset %s to %d replicas",
                    statefulset_name,
                    replicas,
                )
                return result

            # Fallback to official Kubernetes client
            _LOGGER.debug(
                "aiohttp failed, trying official Kubernetes client for StatefulSet scaling"
            )
            result = await self._scale_statefulset_kubernetes(
                statefulset_name, replicas, namespace
            )
            if result:
                _LOGGER.info(
                    "Successfully scaled statefulset %s to %d replicas using official client",
                    statefulset_name,
                    replicas,
                )
            return result
        except Exception as ex:
            self._log_error(
                f"scale statefulset {statefulset_name}",
                ex,
                f"target_replicas={replicas}",
            )
            return False

    async def _scale_statefulset_aiohttp(
        self, statefulset_name: str, replicas: int, namespace: str | None = None
    ) -> bool:
        """Scale StatefulSet using aiohttp as fallback."""
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
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status in [200, 201]:
                        _LOGGER.info(
                            "Successfully scaled statefulset %s to %d replicas using aiohttp",
                            statefulset_name,
                            replicas,
                        )
                        return True
                    else:
                        response_text = await response.text()
                        _LOGGER.error(
                            "aiohttp scale statefulset failed with status %s: %s",
                            response.status,
                            response_text,
                        )
                        return False
        except Exception as ex:
            self._log_error(
                f"aiohttp scale statefulset {statefulset_name}",
                ex,
                f"target_replicas={replicas}",
            )
            return False

    async def _scale_statefulset_kubernetes(
        self, statefulset_name: str, replicas: int, namespace: str | None = None
    ) -> bool:
        """Scale StatefulSet using the official Kubernetes client."""
        try:
            target_namespace = namespace or self.namespace

            # Get the current StatefulSet
            loop = asyncio.get_event_loop()
            statefulset = await loop.run_in_executor(
                None,
                self.apps_v1.read_namespaced_stateful_set,
                statefulset_name,
                target_namespace,
            )

            # Update the replicas
            statefulset.spec.replicas = replicas

            # Apply the update
            await loop.run_in_executor(
                None,
                self.apps_v1.replace_namespaced_stateful_set,
                statefulset_name,
                target_namespace,
                statefulset,
            )

            _LOGGER.info(
                "Successfully scaled statefulset %s to %d replicas using official client",
                statefulset_name,
                replicas,
            )
            return True
        except Exception as ex:
            self._log_error(
                f"official client scale statefulset {statefulset_name}",
                ex,
                f"target_replicas={replicas}",
            )
            return False

    async def stop_statefulset(
        self, statefulset_name: str, namespace: str | None = None
    ) -> bool:
        """Stop a StatefulSet by scaling it to 0 replicas."""
        return await self.scale_statefulset(statefulset_name, 0, namespace)

    async def start_statefulset(
        self, statefulset_name: str, replicas: int = 1, namespace: str | None = None
    ) -> bool:
        """Start a StatefulSet by scaling it to the specified number of replicas."""
        return await self.scale_statefulset(statefulset_name, replicas, namespace)

    async def get_pod_metrics(self) -> dict[str, dict[str, float]]:
        """Get pod metrics (CPU and memory usage)."""
        # Metrics API is usually accessed via /apis/metrics.k8s.io/v1beta1/pods
        return await self._get_pod_metrics_aiohttp()

    async def _get_pod_metrics_aiohttp(self) -> dict[str, dict[str, float]]:
        """Get pod metrics using aiohttp."""
        try:
            headers = {"Authorization": f"Bearer {self.api_token}"}
            if self.monitor_all_namespaces:
                url = (
                    f"https://{self.host}:{self.port}/apis/metrics.k8s.io/v1beta1/pods"
                )
            else:
                url = f"https://{self.host}:{self.port}/apis/metrics.k8s.io/v1beta1/namespaces/{self.namespace}/pods"

            ssl_context: ssl.SSLContext | bool = False
            if self.verify_ssl:
                ssl_context = ssl.create_default_context(cafile=self.ca_cert)

            connector = aiohttp.TCPConnector(ssl=ssl_context)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(url, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        metrics: dict[str, dict[str, float]] = {}
                        for item in data.get("items", []):
                            metadata = item.get("metadata", {})
                            name = metadata.get("name")
                            namespace = metadata.get("namespace")
                            containers = item.get("containers", [])

                            cpu_usage = 0.0
                            memory_usage = 0.0

                            for container in containers:
                                usage = container.get("usage", {})
                                cpu_str = usage.get("cpu", "0")
                                memory_str = usage.get("memory", "0")

                                # Debug log for first few items to verify parsing
                                if len(metrics) < 5:
                                    _LOGGER.debug(
                                        "Parsing metrics for %s/%s: cpu=%s, memory=%s",
                                        namespace,
                                        name,
                                        cpu_str,
                                        memory_str,
                                    )

                                cpu_usage += self._parse_cpu(cpu_str, "m")
                                memory_usage += self._parse_memory(memory_str, "MiB")

                            # Key by namespace/name to be unique across namespaces
                            key = f"{namespace}/{name}"
                            metrics[key] = {"cpu": cpu_usage, "memory": memory_usage}
                        _LOGGER.debug(
                            "Successfully fetched metrics for %d pods", len(metrics)
                        )
                        return metrics
                    elif response.status == 403:
                        _LOGGER.warning(
                            "Failed to fetch pod metrics: 403 Forbidden. "
                            "The service account does not have permission to access the metrics API. "
                            "To enable CPU and Memory usage metrics, add the following to your ClusterRole: "
                            "apiGroups: ['metrics.k8s.io'], resources: ['pods', 'nodes'], verbs: ['get', 'list']"
                        )
                        return {}
                    else:
                        _LOGGER.warning(
                            "Failed to fetch pod metrics: %s. Metrics API might not be available.",
                            response.status,
                        )
                        return {}
        except Exception as ex:
            _LOGGER.warning("Exception in _get_pod_metrics_aiohttp: %s", ex)
            return {}

    def _pod_matches_selector(
        self, pod_labels: dict[str, Any], selector: dict[str, Any]
    ) -> bool:
        """Check if a pod matches a selector."""
        if not selector:
            return False
        return all(pod_labels.get(key) == value for key, value in selector.items())

    def _calculate_resource_usage(
        self,
        workload: dict[str, Any],
        pods: list[dict[str, Any]],
        metrics: dict[str, dict[str, float]],
    ) -> tuple[float, float]:
        """Calculate CPU and memory usage for a workload from its pods."""
        selector = workload.get("selector", {})
        namespace = workload.get("namespace")
        workload_name = workload.get("name", "unknown")

        cpu_usage = 0.0
        memory_usage = 0.0
        matched_pods = 0

        for pod in pods:
            pod_name = pod.get("name")
            pod_ns = pod.get("namespace")
            pod_labels = pod.get("labels", {})

            if pod_ns == namespace and self._pod_matches_selector(pod_labels, selector):
                matched_pods += 1
                pod_metric_key = f"{namespace}/{pod_name}"
                pod_metric = metrics.get(pod_metric_key)
                if pod_metric:
                    cpu_usage += pod_metric.get("cpu", 0.0)
                    memory_usage += pod_metric.get("memory", 0.0)
                else:
                    _LOGGER.debug(
                        "No metrics found for pod %s/%s (key: %s) belonging to workload %s/%s",
                        pod_ns,
                        pod_name,
                        pod_metric_key,
                        namespace,
                        workload_name,
                    )

        if matched_pods == 0:
            _LOGGER.debug(
                "No pods matched selector %s for workload %s/%s",
                selector,
                namespace,
                workload_name,
            )

        return cpu_usage, memory_usage

    async def _enrich_deployments_with_metrics(
        self, deployments: list[dict[str, Any]]
    ) -> None:
        """Enrich deployments with CPU and memory usage metrics."""
        # Initialize all deployments with 0.0 values first
        for deployment in deployments:
            deployment.setdefault("cpu_usage", 0.0)
            deployment.setdefault("memory_usage", 0.0)

        try:
            # Get pods based on namespace monitoring configuration
            if self.monitor_all_namespaces:
                pods = await self._get_pods_all_namespaces_aiohttp()
            else:
                pods = await self._get_pods_aiohttp()
            metrics = await self._get_pod_metrics_aiohttp()

            if not pods:
                _LOGGER.debug("No pods found for deployment metrics enrichment")
                return
            if not metrics:
                _LOGGER.debug(
                    "No pod metrics available for deployment metrics enrichment"
                )
                return

            _LOGGER.debug(
                "Enriching %d deployments with metrics from %d pods and %d metric entries",
                len(deployments),
                len(pods),
                len(metrics),
            )

            for deployment in deployments:
                cpu_usage, memory_usage = self._calculate_resource_usage(
                    deployment, pods, metrics
                )
                deployment["cpu_usage"] = cpu_usage
                deployment["memory_usage"] = memory_usage
                _LOGGER.debug(
                    "Deployment %s/%s: CPU=%.2f m, Memory=%.2f MiB",
                    deployment.get("namespace", "unknown"),
                    deployment.get("name", "unknown"),
                    cpu_usage,
                    memory_usage,
                )
        except Exception as ex:
            _LOGGER.error("Error enriching deployments with metrics: %s", ex)

    async def _enrich_statefulsets_with_metrics(
        self, statefulsets: list[dict[str, Any]]
    ) -> None:
        """Enrich StatefulSets with CPU and memory usage metrics."""
        # Initialize all StatefulSets with 0.0 values first
        for statefulset in statefulsets:
            statefulset.setdefault("cpu_usage", 0.0)
            statefulset.setdefault("memory_usage", 0.0)

        try:
            # Get pods based on namespace monitoring configuration
            if self.monitor_all_namespaces:
                pods = await self._get_pods_all_namespaces_aiohttp()
            else:
                pods = await self._get_pods_aiohttp()
            metrics = await self._get_pod_metrics_aiohttp()

            if not pods:
                _LOGGER.debug("No pods found for StatefulSet metrics enrichment")
                return
            if not metrics:
                _LOGGER.debug(
                    "No pod metrics available for StatefulSet metrics enrichment"
                )
                return

            _LOGGER.debug(
                "Enriching %d StatefulSets with metrics from %d pods and %d metric entries",
                len(statefulsets),
                len(pods),
                len(metrics),
            )

            for statefulset in statefulsets:
                cpu_usage, memory_usage = self._calculate_resource_usage(
                    statefulset, pods, metrics
                )
                statefulset["cpu_usage"] = cpu_usage
                statefulset["memory_usage"] = memory_usage
                _LOGGER.debug(
                    "StatefulSet %s/%s: CPU=%.2f m, Memory=%.2f MiB",
                    statefulset.get("namespace", "unknown"),
                    statefulset.get("name", "unknown"),
                    cpu_usage,
                    memory_usage,
                )
        except Exception as ex:
            _LOGGER.error("Error enriching statefulsets with metrics: %s", ex)

    async def compare_authentication_methods(self) -> dict[str, Any]:
        """Compare authentication methods to help diagnose issues."""
        result = {
            "kubernetes_client": {
                "host": f"https://{self.host}:{self.port}",
                "headers": {
                    "authorization": (
                        f"Bearer {self.api_token[:10]}..."
                        if len(self.api_token) > 10
                        else "Bearer [token]"
                    )
                },
                "verify_ssl": self.verify_ssl,
                "ca_cert": "provided" if self.ca_cert else "none",
            },
            "aiohttp_fallback": {
                "url": f"https://{self.host}:{self.port}/api/v1/",
                "headers": {
                    "Authorization": (
                        f"Bearer {self.api_token[:10]}..."
                        if len(self.api_token) > 10
                        else "Bearer [token]"
                    )
                },
                "ssl": False,
            },
            "token_info": {
                "length": len(self.api_token),
                "starts_with_ey": self.api_token.startswith("ey"),
                "contains_dots": self.api_token.count(".") == 2,
            },
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
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    result["aiohttp_fallback"]["success"] = response.status == 200
                    result["aiohttp_fallback"]["status_code"] = response.status
                    result["aiohttp_fallback"]["error"] = (
                        None if response.status == 200 else f"HTTP {response.status}"
                    )
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
            "details": {},
        }

        # Test with kubernetes client first
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self.core_v1.get_api_resources)
            result["authenticated"] = True
            result["method"] = "kubernetes_client"
            result["details"]["api_resources"] = "success"  # type: ignore
            return result
        except ApiException as ex:
            result["error"] = f"API Exception: {ex.status} - {ex.reason}"
            result["details"]["api_status"] = ex.status  # type: ignore
            result["details"]["api_reason"] = ex.reason  # type: ignore
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
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status == 200:
                        result["authenticated"] = True
                        result["method"] = "aiohttp_fallback"
                        result["details"]["http_status"] = response.status  # type: ignore
                        result["error"] = None
                    else:
                        result["error"] = f"HTTP error: {response.status}"
                        result["details"]["http_status"] = response.status  # type: ignore
        except Exception as ex:
            if not result["error"]:
                result["error"] = f"aiohttp error: {str(ex)}"

        return result

    async def is_cluster_healthy(self) -> bool:
        """Check if the cluster is healthy."""
        return await self._test_connection()

    # CronJob methods
    async def get_cronjobs_count(self) -> int:
        """Get the count of CronJobs in the cluster."""
        try:
            if self.monitor_all_namespaces:
                return await self._get_cronjobs_count_all_namespaces()
            else:
                return await self._get_cronjobs_count_single_namespace()
        except Exception as ex:
            self._log_error("get_cronjobs_count", ex)
            return 0

    async def _get_cronjobs_count_single_namespace(self) -> int:
        """Get CronJobs count for a single namespace."""
        try:
            loop = asyncio.get_event_loop()
            cronjobs = await loop.run_in_executor(
                None, self.batch_v1.list_namespaced_cron_job, self.namespace
            )
            return len(cronjobs.items)
        except Exception as ex:
            self._log_error("_get_cronjobs_count_single_namespace", ex)
            return await self._get_cronjobs_count_aiohttp()

    async def _get_cronjobs_count_all_namespaces(self) -> int:
        """Get CronJobs count for all namespaces."""
        # Use aiohttp directly since the kubernetes client method may not exist
        # or may have authentication issues
        return await self._get_cronjobs_count_all_namespaces_aiohttp()

    async def _get_cronjobs_count_aiohttp(self) -> int:
        """Get CronJobs count using aiohttp fallback for single namespace."""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Accept": "application/json",
            }
            url = f"https://{self.host}:{self.port}/apis/batch/v1/namespaces/{self.namespace}/cronjobs"

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers=headers,
                    ssl=False,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return len(data.get("items", []))
                    else:
                        _LOGGER.error(
                            "Failed to get CronJobs count via aiohttp: HTTP %d",
                            response.status,
                        )
                        return 0
        except Exception as ex:
            self._log_error("_get_cronjobs_count_aiohttp", ex)
            return 0

    async def _get_cronjobs_count_all_namespaces_aiohttp(self) -> int:
        """Get CronJobs count using aiohttp fallback for all namespaces."""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Accept": "application/json",
            }
            url = f"https://{self.host}:{self.port}/apis/batch/v1/cronjobs"

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers=headers,
                    ssl=False,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return len(data.get("items", []))
                    else:
                        _LOGGER.error(
                            "Failed to get CronJobs count via aiohttp: HTTP %d",
                            response.status,
                        )
                        return 0
        except Exception as ex:
            self._log_error("_get_cronjobs_count_all_namespaces_aiohttp", ex)
            return 0

    async def get_cronjobs(self) -> list[dict[str, Any]]:
        """Get detailed information about CronJobs in the cluster."""
        try:
            if self.monitor_all_namespaces:
                return await self._get_cronjobs_all_namespaces()
            else:
                return await self._get_cronjobs_single_namespace()
        except Exception as ex:
            self._log_error("get_cronjobs", ex)
            return []

    async def _get_cronjobs_single_namespace(self) -> list[dict[str, Any]]:
        """Get CronJobs for a single namespace."""
        try:
            loop = asyncio.get_event_loop()
            cronjobs = await loop.run_in_executor(
                None, self.batch_v1.list_namespaced_cron_job, self.namespace
            )
            return [self._format_cronjob(cronjob) for cronjob in cronjobs.items]
        except Exception as ex:
            self._log_error("_get_cronjobs_single_namespace", ex)
            return await self._get_cronjobs_aiohttp()

    async def _get_cronjobs_all_namespaces(self) -> list[dict[str, Any]]:
        """Get CronJobs for all namespaces."""
        # Use aiohttp directly since the kubernetes client method may not exist
        # or may have authentication issues
        _LOGGER.debug(
            "Getting CronJobs for all namespaces using aiohttp from %s:%s",
            self.host,
            self.port,
        )
        return await self._get_cronjobs_all_namespaces_aiohttp()

    async def _get_cronjobs_aiohttp(self) -> list[dict[str, Any]]:
        """Get CronJobs using aiohttp fallback for single namespace."""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Accept": "application/json",
            }
            url = f"https://{self.host}:{self.port}/apis/batch/v1/namespaces/{self.namespace}/cronjobs"

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers=headers,
                    ssl=self.verify_ssl,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return [
                            self._format_cronjob_from_dict(item)
                            for item in data.get("items", [])
                        ]
                    else:
                        _LOGGER.error(
                            "Failed to get CronJobs via aiohttp: HTTP %d",
                            response.status,
                        )
                        return []
        except Exception as ex:
            self._log_error("_get_cronjobs_aiohttp", ex)
            return []

    async def _get_cronjobs_all_namespaces_aiohttp(self) -> list[dict[str, Any]]:
        """Get CronJobs using aiohttp fallback for all namespaces."""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Accept": "application/json",
            }
            url = f"https://{self.host}:{self.port}/apis/batch/v1/cronjobs"

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers=headers,
                    ssl=self.verify_ssl,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return [
                            self._format_cronjob_from_dict(item)
                            for item in data.get("items", [])
                        ]
                    else:
                        _LOGGER.error(
                            "Failed to get CronJobs via aiohttp: HTTP %d",
                            response.status,
                        )
                        return []
        except Exception as ex:
            self._log_error("_get_cronjobs_all_namespaces_aiohttp", ex)
            return []

    async def _suspend_cronjob_aiohttp(
        self, cronjob_name: str, namespace: str
    ) -> dict[str, Any]:
        """Suspend a CronJob using aiohttp."""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Accept": "application/json",
                "Content-Type": "application/strategic-merge-patch+json",
            }
            url = f"https://{self.host}:{self.port}/apis/batch/v1/namespaces/{namespace}/cronjobs/{cronjob_name}"
            patch_body = {"spec": {"suspend": True}}

            async with aiohttp.ClientSession() as session:
                async with session.patch(
                    url,
                    headers=headers,
                    json=patch_body,
                    ssl=self.verify_ssl,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status == 200:
                        _LOGGER.info(
                            "Successfully suspended CronJob '%s' in namespace '%s' via aiohttp",
                            cronjob_name,
                            namespace,
                        )
                        return {
                            "success": True,
                            "cronjob_name": cronjob_name,
                            "namespace": namespace,
                        }
                    else:
                        error_msg = f"Failed to suspend CronJob '{cronjob_name}' via aiohttp: HTTP {response.status}"
                        _LOGGER.error(error_msg)
                        return {
                            "success": False,
                            "error": error_msg,
                            "cronjob_name": cronjob_name,
                            "namespace": namespace,
                        }
        except Exception as ex:
            error_msg = (
                f"Failed to suspend CronJob '{cronjob_name}' via aiohttp: {str(ex)}"
            )
            self._log_error("_suspend_cronjob_aiohttp", ex)
            return {
                "success": False,
                "error": error_msg,
                "cronjob_name": cronjob_name,
                "namespace": namespace,
            }

    async def _resume_cronjob_aiohttp(
        self, cronjob_name: str, namespace: str
    ) -> dict[str, Any]:
        """Resume a CronJob using aiohttp."""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Accept": "application/json",
                "Content-Type": "application/strategic-merge-patch+json",
            }
            url = f"https://{self.host}:{self.port}/apis/batch/v1/namespaces/{namespace}/cronjobs/{cronjob_name}"
            patch_body = {"spec": {"suspend": False}}

            async with aiohttp.ClientSession() as session:
                async with session.patch(
                    url,
                    headers=headers,
                    json=patch_body,
                    ssl=self.verify_ssl,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status == 200:
                        _LOGGER.info(
                            "Successfully resumed CronJob '%s' in namespace '%s' via aiohttp",
                            cronjob_name,
                            namespace,
                        )
                        return {
                            "success": True,
                            "cronjob_name": cronjob_name,
                            "namespace": namespace,
                        }
                    else:
                        error_msg = f"Failed to resume CronJob '{cronjob_name}' via aiohttp: HTTP {response.status}"
                        _LOGGER.error(error_msg)
                        return {
                            "success": False,
                            "error": error_msg,
                            "cronjob_name": cronjob_name,
                            "namespace": namespace,
                        }
        except Exception as ex:
            error_msg = (
                f"Failed to resume CronJob '{cronjob_name}' via aiohttp: {str(ex)}"
            )
            self._log_error("_resume_cronjob_aiohttp", ex)
            return {
                "success": False,
                "error": error_msg,
                "cronjob_name": cronjob_name,
                "namespace": namespace,
            }

    async def _trigger_cronjob_aiohttp(
        self, cronjob_name: str, namespace: str
    ) -> dict[str, Any]:
        """Trigger a CronJob using aiohttp by creating a job from it."""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            }

            # Step 1: Get the CronJob to extract the job template
            cronjob_url = f"https://{self.host}:{self.port}/apis/batch/v1/namespaces/{namespace}/cronjobs/{cronjob_name}"

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    cronjob_url,
                    headers=headers,
                    ssl=self.verify_ssl,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status != 200:
                        error_msg = f"Failed to get CronJob '{cronjob_name}' via aiohttp: HTTP {response.status}"
                        _LOGGER.error(error_msg)
                        return {
                            "success": False,
                            "error": error_msg,
                            "cronjob_name": cronjob_name,
                            "namespace": namespace,
                        }

                    cronjob_data = await response.json()

                    # Step 2: Create a job from the CronJob template
                    job_name = f"{cronjob_name}-manual-{int(time.time())}"

                    # Extract the job template from the CronJob
                    job_template = cronjob_data.get("spec", {}).get("jobTemplate", {})
                    if not job_template:
                        error_msg = f"CronJob '{cronjob_name}' has no job template"
                        _LOGGER.error(error_msg)
                        return {
                            "success": False,
                            "error": error_msg,
                            "cronjob_name": cronjob_name,
                            "namespace": namespace,
                        }

                    # Create the job object
                    job_data = {
                        "apiVersion": "batch/v1",
                        "kind": "Job",
                        "metadata": {
                            "name": job_name,
                            "namespace": namespace,
                            "labels": {
                                "cronjob.kubernetes.io/manual": "true",
                                "cronjob.kubernetes.io/name": cronjob_name,
                            },
                        },
                        "spec": job_template.get("spec", {}),
                    }

                    # Create the job
                    jobs_url = f"https://{self.host}:{self.port}/apis/batch/v1/namespaces/{namespace}/jobs"

                    async with session.post(
                        jobs_url,
                        headers=headers,
                        json=job_data,
                        ssl=self.verify_ssl,
                        timeout=aiohttp.ClientTimeout(total=10),
                    ) as job_response:
                        if job_response.status == 201:  # Created
                            job_result = await job_response.json()
                            _LOGGER.info(
                                "Successfully triggered CronJob '%s' in namespace '%s' via aiohttp, created job '%s'",
                                cronjob_name,
                                namespace,
                                job_name,
                            )
                            return {
                                "success": True,
                                "job_name": job_name,
                                "namespace": namespace,
                                "cronjob_name": cronjob_name,
                                "job_uid": job_result.get("metadata", {}).get(
                                    "uid", ""
                                ),
                            }
                        else:
                            error_msg = f"Failed to create job for CronJob '{cronjob_name}' via aiohttp: HTTP {job_response.status}"
                            _LOGGER.error(error_msg)
                            return {
                                "success": False,
                                "error": error_msg,
                                "cronjob_name": cronjob_name,
                                "namespace": namespace,
                            }

        except Exception as ex:
            error_msg = (
                f"Failed to trigger CronJob '{cronjob_name}' via aiohttp: {str(ex)}"
            )
            self._log_error("_trigger_cronjob_aiohttp", ex)
            return {
                "success": False,
                "error": error_msg,
                "cronjob_name": cronjob_name,
                "namespace": namespace,
            }

    def _format_cronjob(self, cronjob) -> dict[str, Any]:
        """Format CronJob object to dictionary."""
        return {
            "name": cronjob.metadata.name,
            "namespace": cronjob.metadata.namespace,
            "schedule": cronjob.spec.schedule if cronjob.spec.schedule else "",
            "suspend": cronjob.spec.suspend if cronjob.spec.suspend else False,
            "last_schedule_time": (
                cronjob.status.last_schedule_time.isoformat()
                if cronjob.status.last_schedule_time
                else None
            ),
            "next_schedule_time": (
                cronjob.status.next_schedule_time.isoformat()
                if cronjob.status.next_schedule_time
                else None
            ),
            "active_jobs_count": (
                len(cronjob.status.active) if cronjob.status.active else 0
            ),
            "successful_jobs_history_limit": (
                cronjob.spec.successful_jobs_history_limit
                if cronjob.spec.successful_jobs_history_limit
                else 3
            ),
            "failed_jobs_history_limit": (
                cronjob.spec.failed_jobs_history_limit
                if cronjob.spec.failed_jobs_history_limit
                else 1
            ),
            "concurrency_policy": (
                cronjob.spec.concurrency_policy
                if cronjob.spec.concurrency_policy
                else "Allow"
            ),
            "uid": cronjob.metadata.uid,
            "creation_timestamp": (
                cronjob.metadata.creation_timestamp.isoformat()
                if cronjob.metadata.creation_timestamp
                else None
            ),
        }

    def _format_cronjob_from_dict(self, cronjob_dict: dict[str, Any]) -> dict[str, Any]:
        """Format CronJob dictionary from API response."""
        metadata = cronjob_dict.get("metadata", {})
        spec = cronjob_dict.get("spec", {})
        status = cronjob_dict.get("status", {})

        return {
            "name": metadata.get("name", ""),
            "namespace": metadata.get("namespace", ""),
            "schedule": spec.get("schedule", ""),
            "suspend": spec.get("suspend", False),
            "last_schedule_time": status.get("lastScheduleTime"),
            "next_schedule_time": status.get("nextScheduleTime"),
            "active_jobs_count": len(status.get("active", [])),
            "successful_jobs_history_limit": spec.get("successfulJobsHistoryLimit", 3),
            "failed_jobs_history_limit": spec.get("failedJobsHistoryLimit", 1),
            "concurrency_policy": spec.get("concurrencyPolicy", "Allow"),
            "uid": metadata.get("uid", ""),
            "creation_timestamp": metadata.get("creationTimestamp"),
        }

    async def trigger_cronjob(
        self, cronjob_name: str, namespace: str | None = None
    ) -> dict[str, Any]:
        """Trigger a CronJob by creating a job from it."""
        _LOGGER.debug(
            "trigger_cronjob called with cronjob_name: %s, namespace: %s",
            cronjob_name,
            namespace,
        )
        target_namespace = namespace or self.namespace

        # Check namespace permissions
        if not self.monitor_all_namespaces and target_namespace != self.namespace:
            error_msg = (
                f"Cannot trigger CronJob '{cronjob_name}' in namespace '{target_namespace}': "
                f"Integration is configured to monitor only namespace '{self.namespace}'. "
                f"Enable 'monitor_all_namespaces' in configuration to access other namespaces."
            )
            _LOGGER.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "cronjob_name": cronjob_name,
                "namespace": target_namespace,
            }

        try:
            # Try using aiohttp first since it's more reliable
            return await self._trigger_cronjob_aiohttp(cronjob_name, target_namespace)
        except Exception:
            # Fallback to kubernetes client
            try:
                # First, get the CronJob to extract the job template
                loop = asyncio.get_event_loop()
                cronjob = await loop.run_in_executor(
                    None,
                    self.batch_v1.read_namespaced_cron_job,
                    cronjob_name,
                    target_namespace,
                )

                # Create a job from the CronJob template
                job_name = f"{cronjob_name}-manual-{int(time.time())}"

                # Create job object from CronJob template
                job = k8s_client.V1Job(
                    metadata=k8s_client.V1ObjectMeta(
                        name=job_name,
                        namespace=target_namespace,
                        labels={
                            "cronjob.kubernetes.io/manual": "true",
                            "cronjob.kubernetes.io/name": cronjob_name,
                        },
                    ),
                    spec=cronjob.spec.job_template.spec,
                )

                # Create the job
                created_job = await loop.run_in_executor(
                    None, self.batch_v1.create_namespaced_job, target_namespace, job
                )

                _LOGGER.info(
                    "Successfully triggered CronJob '%s' in namespace '%s', created job '%s'",
                    cronjob_name,
                    target_namespace,
                    job_name,
                )

                return {
                    "success": True,
                    "job_name": job_name,
                    "namespace": target_namespace,
                    "cronjob_name": cronjob_name,
                    "job_uid": created_job.metadata.uid,
                }

            except ApiException as ex:
                error_msg = f"Failed to trigger CronJob '{cronjob_name}': {ex.status} - {ex.reason}"
                _LOGGER.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "cronjob_name": cronjob_name,
                    "namespace": target_namespace,
                }
            except Exception as ex:
                error_msg = f"Failed to trigger CronJob '{cronjob_name}': {str(ex)}"
                self._log_error("trigger_cronjob", ex)
                return {
                    "success": False,
                    "error": error_msg,
                    "cronjob_name": cronjob_name,
                    "namespace": target_namespace,
                }

    async def suspend_cronjob(
        self, cronjob_name: str, namespace: str | None = None
    ) -> dict[str, Any]:
        """Suspend a CronJob by setting suspend=true."""
        target_namespace = namespace or self.namespace

        # Check namespace permissions
        if not self.monitor_all_namespaces and target_namespace != self.namespace:
            error_msg = (
                f"Cannot suspend CronJob '{cronjob_name}' in namespace '{target_namespace}': "
                f"Integration is configured to monitor only namespace '{self.namespace}'. "
                f"Enable 'monitor_all_namespaces' in configuration to access other namespaces."
            )
            _LOGGER.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "cronjob_name": cronjob_name,
                "namespace": target_namespace,
            }

        try:
            # Try using aiohttp first since it's more reliable
            return await self._suspend_cronjob_aiohttp(cronjob_name, target_namespace)
        except Exception:
            # Fallback to kubernetes client
            try:
                # Create a patch to set suspend=true
                patch_body = {"spec": {"suspend": True}}

                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None,
                    self.batch_v1.patch_namespaced_cron_job,
                    cronjob_name,
                    target_namespace,
                    patch_body,
                )

                _LOGGER.info(
                    "Successfully suspended CronJob '%s' in namespace '%s'",
                    cronjob_name,
                    target_namespace,
                )

                return {
                    "success": True,
                    "cronjob_name": cronjob_name,
                    "namespace": target_namespace,
                }

            except ApiException as ex:
                error_msg = f"Failed to suspend CronJob '{cronjob_name}': {ex.status} - {ex.reason}"
                _LOGGER.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "cronjob_name": cronjob_name,
                    "namespace": target_namespace,
                }
            except Exception as ex:
                error_msg = f"Failed to suspend CronJob '{cronjob_name}': {str(ex)}"
                self._log_error("suspend_cronjob", ex)
                return {
                    "success": False,
                    "error": error_msg,
                    "cronjob_name": cronjob_name,
                    "namespace": target_namespace,
                }

    async def resume_cronjob(
        self, cronjob_name: str, namespace: str | None = None
    ) -> dict[str, Any]:
        """Resume a CronJob by setting suspend=false."""
        target_namespace = namespace or self.namespace

        # Check namespace permissions
        if not self.monitor_all_namespaces and target_namespace != self.namespace:
            error_msg = (
                f"Cannot resume CronJob '{cronjob_name}' in namespace '{target_namespace}': "
                f"Integration is configured to monitor only namespace '{self.namespace}'. "
                f"Enable 'monitor_all_namespaces' in configuration to access other namespaces."
            )
            _LOGGER.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "cronjob_name": cronjob_name,
                "namespace": target_namespace,
            }

        try:
            # Try using aiohttp first since it's more reliable
            return await self._resume_cronjob_aiohttp(cronjob_name, target_namespace)
        except Exception:
            # Fallback to kubernetes client
            try:
                # Create a patch to set suspend=false
                patch_body = {"spec": {"suspend": False}}

                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None,
                    self.batch_v1.patch_namespaced_cron_job,
                    cronjob_name,
                    target_namespace,
                    patch_body,
                )

                _LOGGER.info(
                    "Successfully resumed CronJob '%s' in namespace '%s'",
                    cronjob_name,
                    target_namespace,
                )

                return {
                    "success": True,
                    "cronjob_name": cronjob_name,
                    "namespace": target_namespace,
                }

            except ApiException as ex:
                error_msg = f"Failed to resume CronJob '{cronjob_name}': {ex.status} - {ex.reason}"
                _LOGGER.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "cronjob_name": cronjob_name,
                    "namespace": target_namespace,
                }
            except Exception as ex:
                error_msg = f"Failed to resume CronJob '{cronjob_name}': {str(ex)}"
                self._log_error("resume_cronjob", ex)
                return {
                    "success": False,
                    "error": error_msg,
                    "cronjob_name": cronjob_name,
                    "namespace": target_namespace,
                }
