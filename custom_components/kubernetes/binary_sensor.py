"""Binary sensor platform for Kubernetes integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .kubernetes_client import KubernetesClient

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Kubernetes binary sensors based on a config entry."""
    client = KubernetesClient(config_entry.data)

    # Create binary sensors for cluster health
    binary_sensors = [
        KubernetesClusterHealthSensor(client, config_entry),
    ]

    async_add_entities(binary_sensors)


class KubernetesBaseBinarySensor(BinarySensorEntity):
    """Base class for Kubernetes binary sensors."""

    def __init__(self, client: KubernetesClient, config_entry: ConfigEntry) -> None:
        """Initialize the binary sensor."""
        self.client = client
        self.config_entry = config_entry
        self._attr_has_entity_name = True


class KubernetesClusterHealthSensor(KubernetesBaseBinarySensor):
    """Binary sensor for Kubernetes cluster health."""

    def __init__(self, client: KubernetesClient, config_entry: ConfigEntry) -> None:
        """Initialize the cluster health sensor."""
        super().__init__(client, config_entry)
        self._attr_name = "Cluster Health"
        self._attr_unique_id = f"{config_entry.entry_id}_cluster_health"
        self._attr_device_class = "connectivity"

    async def async_update(self) -> None:
        """Update the binary sensor state."""
        try:
            is_healthy = await self.client.is_cluster_healthy()
            self._attr_is_on = is_healthy
        except Exception as ex:
            _LOGGER.error("Failed to update cluster health sensor: %s", ex)
            self._attr_is_on = False
