"""Sensor platform for Kubernetes integration."""

from __future__ import annotations

import logging

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import KubernetesDataCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Kubernetes sensors based on a config entry."""
    try:
        # Get the coordinator and client from hass.data
        coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
        client = hass.data[DOMAIN][config_entry.entry_id]["client"]

        # Create sensors for different Kubernetes resources
        sensors = [
            KubernetesPodsSensor(coordinator, client, config_entry),
            KubernetesNodesSensor(coordinator, client, config_entry),
            KubernetesDeploymentsSensor(coordinator, client, config_entry),
            KubernetesStatefulSetsSensor(coordinator, client, config_entry),
        ]

        async_add_entities(sensors)
        _LOGGER.debug("Successfully set up %d Kubernetes sensors", len(sensors))
    except Exception as ex:
        _LOGGER.error("Failed to set up Kubernetes sensors: %s", ex)
        raise


class KubernetesBaseSensor(SensorEntity):
    """Base class for Kubernetes sensors."""

    def __init__(
        self, coordinator: KubernetesDataCoordinator, client, config_entry: ConfigEntry
    ) -> None:
        """Initialize the sensor."""
        self.coordinator = coordinator
        self.client = client
        self.config_entry = config_entry
        self._attr_has_entity_name = True
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.last_update_success

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        self.async_on_remove(
            self.coordinator.async_add_listener(self._handle_coordinator_update)
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()


class KubernetesPodsSensor(KubernetesBaseSensor):
    """Sensor for Kubernetes pods count."""

    def __init__(
        self, coordinator: KubernetesDataCoordinator, client, config_entry: ConfigEntry
    ) -> None:
        """Initialize the pods sensor."""
        super().__init__(coordinator, client, config_entry)
        self._attr_name = "Pods Count"
        self._attr_unique_id = f"{config_entry.entry_id}_pods_count"
        self._attr_native_unit_of_measurement = "pods"

    @property
    def native_value(self) -> int:
        """Return the native value of the sensor."""
        if not self.coordinator.data:
            return 0

        # Get pods count from coordinator data if available, otherwise call client
        if "pods_count" in self.coordinator.data:
            return self.coordinator.data["pods_count"]

        # Fallback to calling client directly if not in coordinator data
        return 0

    async def async_update(self) -> None:
        """Update the sensor state."""
        try:
            # If coordinator doesn't have pods count, fetch it directly
            if not self.coordinator.data or "pods_count" not in self.coordinator.data:
                count = await self.client.get_pods_count()
                self._attr_native_value = count
        except Exception as ex:
            _LOGGER.error("Failed to update pods sensor: %s", ex)
            self._attr_native_value = 0


class KubernetesNodesSensor(KubernetesBaseSensor):
    """Sensor for Kubernetes nodes count."""

    def __init__(
        self, coordinator: KubernetesDataCoordinator, client, config_entry: ConfigEntry
    ) -> None:
        """Initialize the nodes sensor."""
        super().__init__(coordinator, client, config_entry)
        self._attr_name = "Nodes Count"
        self._attr_unique_id = f"{config_entry.entry_id}_nodes_count"
        self._attr_native_unit_of_measurement = "nodes"

    @property
    def native_value(self) -> int:
        """Return the native value of the sensor."""
        if not self.coordinator.data:
            return 0

        # Get nodes count from coordinator data if available, otherwise call client
        if "nodes_count" in self.coordinator.data:
            return self.coordinator.data["nodes_count"]

        # Fallback to calling client directly if not in coordinator data
        return 0

    async def async_update(self) -> None:
        """Update the sensor state."""
        try:
            # If coordinator doesn't have nodes count, fetch it directly
            if not self.coordinator.data or "nodes_count" not in self.coordinator.data:
                count = await self.client.get_nodes_count()
                self._attr_native_value = count
        except Exception as ex:
            _LOGGER.error("Failed to update nodes sensor: %s", ex)
            self._attr_native_value = 0


class KubernetesDeploymentsSensor(KubernetesBaseSensor):
    """Sensor for Kubernetes deployments count."""

    def __init__(
        self, coordinator: KubernetesDataCoordinator, client, config_entry: ConfigEntry
    ) -> None:
        """Initialize the deployments sensor."""
        super().__init__(coordinator, client, config_entry)
        self._attr_name = "Deployments Count"
        self._attr_unique_id = f"{config_entry.entry_id}_deployments_count"
        self._attr_native_unit_of_measurement = "deployments"

    @property
    def native_value(self) -> int:
        """Return the native value of the sensor."""
        if not self.coordinator.data:
            return 0

        # Get deployments count from coordinator data
        if "deployments" in self.coordinator.data:
            return len(self.coordinator.data["deployments"])

        # Fallback to calling client directly if not in coordinator data
        return 0

    async def async_update(self) -> None:
        """Update the sensor state."""
        try:
            # If coordinator doesn't have deployments data, fetch it directly
            if not self.coordinator.data or "deployments" not in self.coordinator.data:
                count = await self.client.get_deployments_count()
                self._attr_native_value = count
        except Exception as ex:
            _LOGGER.error("Failed to update deployments sensor: %s", ex)
            self._attr_native_value = 0


class KubernetesStatefulSetsSensor(KubernetesBaseSensor):
    """Sensor for Kubernetes StatefulSets count."""

    def __init__(
        self, coordinator: KubernetesDataCoordinator, client, config_entry: ConfigEntry
    ) -> None:
        """Initialize the StatefulSets sensor."""
        super().__init__(coordinator, client, config_entry)
        self._attr_name = "StatefulSets Count"
        self._attr_unique_id = f"{config_entry.entry_id}_statefulsets_count"
        self._attr_native_unit_of_measurement = "statefulsets"

    @property
    def native_value(self) -> int:
        """Return the native value of the sensor."""
        if not self.coordinator.data:
            return 0

        # Get statefulsets count from coordinator data
        if "statefulsets" in self.coordinator.data:
            return len(self.coordinator.data["statefulsets"])

        # Fallback to calling client directly if not in coordinator data
        return 0

    async def async_update(self) -> None:
        """Update the sensor state."""
        try:
            # If coordinator doesn't have statefulsets data, fetch it directly
            if not self.coordinator.data or "statefulsets" not in self.coordinator.data:
                count = await self.client.get_statefulsets_count()
                self._attr_native_value = count
        except Exception as ex:
            _LOGGER.error("Failed to update StatefulSets sensor: %s", ex)
            self._attr_native_value = 0
