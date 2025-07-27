"""Data coordinator for Kubernetes integration."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_SWITCH_UPDATE_INTERVAL,
    DEFAULT_SWITCH_UPDATE_INTERVAL,
    DOMAIN,
)
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
        self.config_entry = config_entry
        self.client = client

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

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data via Kubernetes client."""
        try:
            _LOGGER.debug("Updating Kubernetes data for coordinator")

            # Fetch both deployments and statefulsets
            deployments = await self.client.get_deployments()
            statefulsets = await self.client.get_statefulsets()

            # Create a lookup dictionary for quick access
            data = {
                "deployments": {deployment["name"]: deployment for deployment in deployments},
                "statefulsets": {statefulset["name"]: statefulset for statefulset in statefulsets},
                "last_update": asyncio.get_event_loop().time(),
            }

            _LOGGER.debug("Successfully updated Kubernetes data: %d deployments, %d statefulsets",
                         len(deployments), len(statefulsets))

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

    def get_last_update_time(self) -> float:
        """Get the timestamp of the last successful update."""
        if not self.data or "last_update" not in self.data:
            return 0.0
        return self.data["last_update"]
