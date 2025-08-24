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

            # Fetch deployments, statefulsets, cronjobs, pods count, and nodes count
            deployments = await self.client.get_deployments()
            statefulsets = await self.client.get_statefulsets()
            cronjobs = await self.client.get_cronjobs()
            pods_count = await self.client.get_pods_count()
            nodes_count = await self.client.get_nodes_count()

            # Create a lookup dictionary for quick access
            data = {
                "deployments": {
                    deployment["name"]: deployment for deployment in deployments
                },
                "statefulsets": {
                    statefulset["name"]: statefulset for statefulset in statefulsets
                },
                "cronjobs": {cronjob["name"]: cronjob for cronjob in cronjobs},
                "pods_count": pods_count,
                "nodes_count": nodes_count,
                "last_update": asyncio.get_event_loop().time(),
            }

            _LOGGER.debug(
                "Successfully updated Kubernetes data: %d deployments, %d statefulsets, %d cronjobs, %d pods, %d nodes",
                len(deployments),
                len(statefulsets),
                len(cronjobs),
                pods_count,
                nodes_count,
            )

            # Clean up entities for resources that no longer exist
            await self._cleanup_orphaned_entities(data)

            # Trigger discovery of new entities (listeners will handle this)
            self.async_update_listeners()

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

    def get_cronjob_data(self, cronjob_name: str) -> dict[str, Any] | None:
        """Get cronjob data by name."""
        if not self.data or "cronjobs" not in self.data:
            return None
        return self.data["cronjobs"].get(cronjob_name)

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

                # Handle different formats:
                # - Old format: {resource_name}_{resource_type}
                # - New CronJob format: {namespace}_{resource_name}_{resource_type}
                if resource_type == "cronjob" and len(parts) >= 3:
                    # New CronJob format: {namespace}_{resource_name}_cronjob
                    resource_name = "_".join(
                        parts[1:-1]
                    )  # Everything between namespace and 'cronjob'
                else:
                    # Old format: {resource_name}_{resource_type}
                    resource_name = "_".join(
                        parts[:-1]
                    )  # Handle names with underscores

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
                elif resource_type in ("cronjob", "cronjobs"):
                    if resource_name not in current_data.get("cronjobs", {}):
                        should_remove = True
                        _LOGGER.info(
                            "CronJob %s no longer exists, marking entity for removal",
                            resource_name,
                        )
                else:
                    # Handle other entity types like sensors that might track deployments/statefulsets/cronjobs
                    # Check if this entity is tracking a resource that no longer exists
                    if (
                        resource_name not in current_data.get("deployments", {})
                        and resource_name not in current_data.get("statefulsets", {})
                        and resource_name not in current_data.get("cronjobs", {})
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
