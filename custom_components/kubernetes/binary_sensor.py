"""Binary sensor platform for Kubernetes integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry

from .const import DOMAIN
from .coordinator import KubernetesDataCoordinator
from .device import get_cluster_device_info
from .kubernetes_client import KubernetesClient

_LOGGER = logging.getLogger(__name__)

# Node conditions exposed as binary sensors: condition_key -> display name
_NODE_CONDITIONS: dict[str, str] = {
    "memory_pressure": "Memory Pressure",
    "disk_pressure": "Disk Pressure",
    "pid_pressure": "PID Pressure",
    "network_unavailable": "Network Unavailable",
}


def _discover_new_node_condition_sensors(
    coordinator: KubernetesDataCoordinator,
    config_entry: ConfigEntry,
    existing_unique_ids: set[str],
) -> list[KubernetesNodeConditionBinarySensor]:
    """Discover new node condition binary sensors for nodes not yet registered."""
    new_entities: list[KubernetesNodeConditionBinarySensor] = []
    if not coordinator.data or "nodes" not in coordinator.data:
        return new_entities
    for node_name in coordinator.data["nodes"]:
        for condition_key in _NODE_CONDITIONS:
            unique_id = f"{config_entry.entry_id}_node_{node_name}_{condition_key}"
            if unique_id not in existing_unique_ids:
                _LOGGER.info(
                    "Adding new node condition binary sensor: %s %s",
                    node_name,
                    condition_key,
                )
                new_entities.append(
                    KubernetesNodeConditionBinarySensor(
                        coordinator, config_entry, node_name, condition_key
                    )
                )
    return new_entities


async def _async_discover_and_add_new_binary_sensors(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    coordinator: KubernetesDataCoordinator,
) -> None:
    """Discover and add new binary sensors for newly discovered nodes."""
    try:
        entity_registry = async_get_entity_registry(hass)

        sensor_data = hass.data[DOMAIN].get(config_entry.entry_id, {})
        add_entities_callback = sensor_data.get("binary_sensor_add_entities")
        if not add_entities_callback:
            _LOGGER.warning(
                "No add_entities callback found for dynamic binary sensor management"
            )
            return

        existing_entities = entity_registry.entities.get_entries_for_config_entry_id(
            config_entry.entry_id
        )
        existing_unique_ids = {
            entity.unique_id for entity in existing_entities if entity.unique_id
        }
        pending_ids: set[str] = sensor_data.get(
            "binary_sensor_pending_unique_ids", set()
        )
        pending_ids -= existing_unique_ids
        existing_unique_ids |= pending_ids

        new_entities = _discover_new_node_condition_sensors(
            coordinator, config_entry, existing_unique_ids
        )

        if new_entities:
            _LOGGER.info("Adding %d new binary sensors", len(new_entities))
            pending_ids.update(e.unique_id for e in new_entities if e.unique_id)
            add_entities_callback(new_entities)
        else:
            _LOGGER.debug("No new binary sensors to add")

    except Exception as ex:
        _LOGGER.error("Failed to discover and add new binary sensors: %s", ex)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Kubernetes binary sensors based on a config entry."""
    coordinator: KubernetesDataCoordinator = hass.data[DOMAIN][config_entry.entry_id][
        "coordinator"
    ]
    client: KubernetesClient = hass.data[DOMAIN][config_entry.entry_id]["client"]

    # Ensure coordinator has initial data
    await coordinator.async_config_entry_first_refresh()

    # Ensure cluster device exists
    from .device import get_or_create_cluster_device

    await get_or_create_cluster_device(hass, config_entry)

    binary_sensors: list[BinarySensorEntity] = [
        KubernetesClusterHealthSensor(client, config_entry),
    ]

    # Create condition binary sensors for every known node
    for node_name in coordinator.data.get("nodes", {}):
        for condition_key in _NODE_CONDITIONS:
            binary_sensors.append(
                KubernetesNodeConditionBinarySensor(
                    coordinator, config_entry, node_name, condition_key
                )
            )

    async_add_entities(binary_sensors)

    # Store callback and pending set for dynamic discovery
    hass.data[DOMAIN][config_entry.entry_id]["binary_sensor_add_entities"] = (
        async_add_entities
    )
    hass.data[DOMAIN][config_entry.entry_id]["binary_sensor_pending_unique_ids"] = set()

    # Set up listener for adding new entities dynamically
    @callback
    def _async_add_new_binary_sensors() -> None:
        """Add new binary sensors when new nodes are discovered."""
        hass.async_create_task(
            _async_discover_and_add_new_binary_sensors(hass, config_entry, coordinator)
        )

    coordinator.async_add_listener(_async_add_new_binary_sensors)


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
        self._attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return get_cluster_device_info(self.config_entry)

    async def async_update(self) -> None:
        """Update the binary sensor state."""
        try:
            is_healthy = await self.client.is_cluster_healthy()
            self._attr_is_on = is_healthy
        except Exception as ex:
            _LOGGER.error("Failed to update cluster health sensor: %s", ex)
            self._attr_is_on = False


class KubernetesNodeConditionBinarySensor(BinarySensorEntity):
    """Binary sensor for an individual Kubernetes node condition."""

    def __init__(
        self,
        coordinator: KubernetesDataCoordinator,
        config_entry: ConfigEntry,
        node_name: str,
        condition_key: str,
    ) -> None:
        """Initialize the node condition binary sensor."""
        self.coordinator = coordinator
        self.config_entry = config_entry
        self.node_name = node_name
        self.condition_key = condition_key
        self._attr_has_entity_name = True
        self._attr_name = f"{node_name} {_NODE_CONDITIONS[condition_key]}"
        self._attr_unique_id = (
            f"{config_entry.entry_id}_node_{node_name}_{condition_key}"
        )
        self._attr_device_class = BinarySensorDeviceClass.PROBLEM

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return get_cluster_device_info(self.config_entry)

    @property
    def available(self) -> bool:
        """Return True if the coordinator last update succeeded."""
        return self.coordinator.last_update_success

    @property
    def is_on(self) -> bool | None:
        """Return True when the condition is active (problem detected)."""
        if not self.coordinator.data:
            return None
        node_data: dict[str, Any] | None = self.coordinator.data.get("nodes", {}).get(
            self.node_name
        )
        if node_data is None:
            return None
        return bool(node_data.get(self.condition_key, False))

    async def async_added_to_hass(self) -> None:
        """Register coordinator listener when added to HA."""
        await super().async_added_to_hass()
        self.async_on_remove(
            self.coordinator.async_add_listener(self._handle_coordinator_update)
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
