"""Data coordinator for Kubernetes integration."""

from __future__ import annotations

import asyncio
from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_SWITCH_UPDATE_INTERVAL, DEFAULT_SWITCH_UPDATE_INTERVAL, DOMAIN
from .kubernetes_client import KubernetesClient

_LOGGER = logging.getLogger(__name__)


class KubernetesDataCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Kubernetes data."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        client: KubernetesClient,
    ) -> None:
        """Initialize the coordinator."""
        # Get update interval from config, with fallback to default
        update_interval = config_entry.data.get(
            CONF_SWITCH_UPDATE_INTERVAL, DEFAULT_SWITCH_UPDATE_INTERVAL
        )

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{config_entry.entry_id}",
            update_interval=timedelta(seconds=update_interval),
        )

        # Set attributes after super().__init__() to ensure they're not overridden
        self.config_entry = config_entry
        self.client = client

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data via Kubernetes client."""
        try:
            _LOGGER.debug("Updating Kubernetes data for coordinator")

            # Fetch deployments, statefulsets, daemonsets, cronjobs, pods count, nodes count, and detailed nodes info
            deployments = await self.client.get_deployments()
            statefulsets = await self.client.get_statefulsets()
            daemonsets = await self.client.get_daemonsets()
            cronjobs = await self.client.get_cronjobs()
            pods_count = await self.client.get_pods_count()
            nodes_count = await self.client.get_nodes_count()

            _LOGGER.debug("Starting to fetch detailed node information")
            nodes = await self.client.get_nodes()
            _LOGGER.debug(
                "Successfully fetched %d nodes with detailed information", len(nodes)
            )

            _LOGGER.debug("Starting to fetch detailed pod information")
            pods = await self.client.get_pods()
            _LOGGER.debug(
                "Successfully fetched %d pods with detailed information", len(pods)
            )

            # Log node names for debugging
            if nodes:
                node_names = [node.get("name", "Unknown") for node in nodes]
                _LOGGER.debug("Fetched nodes: %s", node_names)

            # Create a lookup dictionary for quick access
            data = {
                "deployments": {
                    deployment["name"]: deployment for deployment in deployments
                },
                "statefulsets": {
                    statefulset["name"]: statefulset for statefulset in statefulsets
                },
                "daemonsets": {
                    daemonset["name"]: daemonset for daemonset in daemonsets
                },
                "cronjobs": {cronjob["name"]: cronjob for cronjob in cronjobs},
                "nodes": {node["name"]: node for node in nodes},
                "pods": {f"{pod['namespace']}_{pod['name']}": pod for pod in pods},
                "pods_count": pods_count,
                "nodes_count": nodes_count,
                "last_update": asyncio.get_event_loop().time(),
            }

            _LOGGER.debug(
                "Successfully updated Kubernetes data: %d deployments, %d statefulsets, %d daemonsets, %d cronjobs, %d pods (detailed: %d), %d nodes (detailed: %d)",
                len(deployments),
                len(statefulsets),
                len(daemonsets),
                len(cronjobs),
                pods_count,
                len(pods),
                nodes_count,
                len(nodes),
            )

            # Clean up entities for resources that no longer exist
            await self._cleanup_orphaned_entities(data)

            return data

        except Exception as ex:
            _LOGGER.error("Failed to update Kubernetes data: %s", ex)
            raise UpdateFailed(f"Failed to update Kubernetes data: {ex}") from ex

    def get_deployment_data(self, deployment_name: str) -> dict[str, Any] | None:
        """Get deployment data by name."""
        if not self.data or "deployments" not in self.data:
            return None
        return self.data["deployments"].get(deployment_name)

    def get_statefulset_data(self, statefulset_name: str) -> dict[str, Any] | None:
        """Get statefulset data by name."""
        if not self.data or "statefulsets" not in self.data:
            return None
        return self.data["statefulsets"].get(statefulset_name)

    def get_daemonset_data(self, daemonset_name: str) -> dict[str, Any] | None:
        """Get daemonset data by name."""
        if not self.data or "daemonsets" not in self.data:
            return None
        return self.data["daemonsets"].get(daemonset_name)

    def get_cronjob_data(self, cronjob_name: str) -> dict[str, Any] | None:
        """Get cronjob data by name."""
        if not self.data or "cronjobs" not in self.data:
            return None
        return self.data["cronjobs"].get(cronjob_name)

    def get_node_data(self, node_name: str) -> dict[str, Any] | None:
        """Get node data by name."""
        if not self.data or "nodes" not in self.data:
            _LOGGER.debug(
                "No coordinator data or nodes data available for node %s", node_name
            )
            return None

        node_data = self.data["nodes"].get(node_name)
        if node_data is None:
            _LOGGER.warning(
                "Node %s not found in coordinator data. Available nodes: %s",
                node_name,
                list(self.data["nodes"].keys()),
            )
        else:
            _LOGGER.debug(
                "Retrieved data for node %s: status=%s",
                node_name,
                node_data.get("status", "Unknown"),
            )
        return node_data

    def get_all_nodes_data(self) -> dict[str, dict[str, Any]]:
        """Get all nodes data."""
        if not self.data or "nodes" not in self.data:
            return {}
        return self.data["nodes"]

    def get_pod_data(self, namespace: str, pod_name: str) -> dict[str, Any] | None:
        """Get pod data by namespace and name."""
        if not self.data or "pods" not in self.data:
            return None
        pod_key = f"{namespace}_{pod_name}"
        return self.data["pods"].get(pod_key)

    def get_all_pods_data(self) -> dict[str, dict[str, Any]]:
        """Get all pods data."""
        if not self.data or "pods" not in self.data:
            return {}
        return self.data["pods"]

    def get_last_update_time(self) -> float:
        """Get the timestamp of the last successful update."""
        if not self.data or "last_update" not in self.data:
            return 0.0
        return self.data["last_update"]

    async def _cleanup_orphaned_entities(
        self, current_data: dict[str, Any]
    ) -> None:  # noqa: C901
        """Remove entities for Kubernetes resources that no longer exist."""
        try:
            # Skip cleanup if config_entry is not available (e.g., in tests)
            if not self.config_entry or not hasattr(self.config_entry, "entry_id"):
                _LOGGER.debug("Skipping entity cleanup: config_entry not available")
                return

            entity_registry = async_get_entity_registry(self.hass)

            # Get all entities for this integration
            entities = entity_registry.entities.get_entries_for_config_entry_id(
                self.config_entry.entry_id
            )

            _LOGGER.debug(
                "Entity cleanup: Found %d entities for config entry %s",
                len(entities),
                self.config_entry.entry_id,
            )

            # Log current data for debugging
            current_nodes = list(current_data.get("nodes", {}).keys())
            current_pods = list(current_data.get("pods", {}).keys())
            _LOGGER.debug("Current nodes in data: %s", current_nodes)
            _LOGGER.debug("Current pods in data: %s", current_pods)

            # Track which entities should be removed
            entities_to_remove = []

            for entity in entities:
                if not entity.unique_id:
                    continue

                # Parse the unique_id to determine resource type and name
                # Format: {config_entry.entry_id}_{resource_name}_{resource_type} or {config_entry.entry_id}_{namespace}_{resource_name}_{resource_type}
                if not entity.unique_id.startswith(f"{self.config_entry.entry_id}_"):
                    continue

                # Remove the config entry ID prefix
                suffix = entity.unique_id[len(f"{self.config_entry.entry_id}_") :]
                parts = suffix.split("_")
                if len(parts) < 2:
                    continue

                resource_type = parts[-1]  # 'deployment', 'statefulset', or 'cronjob'

                _LOGGER.debug(
                    "Processing entity cleanup - unique_id: %s, suffix: %s, parts: %s, initial resource_type: %s",
                    entity.unique_id,
                    suffix,
                    parts,
                    resource_type,
                )

                # Skip count sensors - they are not tracking individual resources
                if resource_type in (
                    "count",
                    "pods_count",
                    "nodes_count",
                    "deployments_count",
                    "statefulsets_count",
                    "daemonsets_count",
                    "cronjobs_count",
                ):
                    _LOGGER.debug(
                        "Skipping cleanup for count sensor: %s", entity.unique_id
                    )
                    continue

                # Handle different formats:
                # - Node format: node_{node_name}
                # - Pod format: pod_{namespace}_{pod_name}
                # - CronJob format: {namespace}_{resource_name}_{resource_type}
                # - Old format: {resource_name}_{resource_type}
                if len(parts) >= 2 and parts[0] == "node":
                    # Node format: node_{node_name}
                    resource_type = "node"
                    resource_name = "_".join(parts[1:])  # Everything after 'node'
                    _LOGGER.debug(
                        "Detected node entity format - node_name: %s", resource_name
                    )
                elif len(parts) >= 3 and parts[0] == "pod":
                    # Pod format: pod_{namespace}_{pod_name}
                    resource_type = "pod"
                    namespace = parts[1]
                    resource_name = "_".join(parts[2:])  # Everything after namespace
                    pod_key = f"{namespace}_{resource_name}"
                    _LOGGER.debug(
                        "Detected pod entity format - namespace: %s, pod_name: %s, key: %s",
                        namespace,
                        resource_name,
                        pod_key,
                    )
                elif resource_type == "cronjob" and len(parts) >= 3:
                    # New CronJob format: {namespace}_{resource_name}_cronjob
                    resource_name = "_".join(
                        parts[1:-1]
                    )  # Everything between namespace and 'cronjob'
                else:
                    # Old format: {resource_name}_{resource_type}
                    resource_name = "_".join(
                        parts[:-1]
                    )  # Handle names with underscores

                _LOGGER.debug(
                    "Parsed entity - resource_type: %s, resource_name: %s",
                    resource_type,
                    resource_name,
                )
                should_remove = False

                if resource_type in ("deployment", "deployments"):
                    if resource_name not in current_data.get("deployments", {}):
                        should_remove = True
                        _LOGGER.info(
                            "Deployment %s no longer exists, marking entity for removal",
                            resource_name,
                        )
                elif resource_type in ("statefulset", "statefulsets"):
                    if resource_name not in current_data.get("statefulsets", {}):
                        should_remove = True
                        _LOGGER.info(
                            "StatefulSet %s no longer exists, marking entity for removal",
                            resource_name,
                        )
                elif resource_type in ("daemonset", "daemonsets"):
                    if resource_name not in current_data.get("daemonsets", {}):
                        should_remove = True
                        _LOGGER.info(
                            "DaemonSet %s no longer exists, marking entity for removal",
                            resource_name,
                        )
                elif resource_type in ("cronjob", "cronjobs"):
                    if resource_name not in current_data.get("cronjobs", {}):
                        should_remove = True
                        _LOGGER.info(
                            "CronJob %s no longer exists, marking entity for removal",
                            resource_name,
                        )
                elif resource_type in ("node", "nodes"):
                    if resource_name not in current_data.get("nodes", {}):
                        should_remove = True
                        _LOGGER.info(
                            "Node %s no longer exists, marking entity for removal",
                            resource_name,
                        )
                elif resource_type in ("pod", "pods"):
                    if len(parts) >= 3 and parts[0] == "pod":
                        # For pod entities, check using the pod_key format
                        pod_key = f"{namespace}_{resource_name}"
                        if pod_key not in current_data.get("pods", {}):
                            should_remove = True
                            _LOGGER.info(
                                "Pod %s in namespace %s no longer exists, marking entity for removal",
                                resource_name,
                                namespace,
                            )
                    else:
                        # Fallback for other pod formats
                        if resource_name not in current_data.get("pods", {}):
                            should_remove = True
                            _LOGGER.info(
                                "Pod %s no longer exists, marking entity for removal",
                                resource_name,
                            )
                else:
                    # Handle other entity types like sensors that might track deployments/statefulsets/cronjobs/nodes/pods
                    # Check if this entity is tracking a resource that no longer exists
                    if (
                        resource_name not in current_data.get("deployments", {})
                        and resource_name not in current_data.get("statefulsets", {})
                        and resource_name not in current_data.get("daemonsets", {})
                        and resource_name not in current_data.get("cronjobs", {})
                        and resource_name not in current_data.get("nodes", {})
                        and resource_name not in current_data.get("pods", {})
                    ):
                        should_remove = True
                        _LOGGER.info(
                            "Resource %s (type: %s) no longer exists, marking entity for removal",
                            resource_name,
                            resource_type,
                        )

                if should_remove:
                    entities_to_remove.append(entity.entity_id)

            # Remove the orphaned entities
            for entity_id in entities_to_remove:
                _LOGGER.info("Removing orphaned entity: %s", entity_id)
                entity_registry.async_remove(entity_id)

            if entities_to_remove:
                _LOGGER.info("Removed %d orphaned entities", len(entities_to_remove))
            else:
                _LOGGER.debug("No orphaned entities found")

        except Exception as ex:
            _LOGGER.error("Failed to cleanup orphaned entities: %s", ex)
