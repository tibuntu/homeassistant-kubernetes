"""Sensor platform for Kubernetes integration."""

from __future__ import annotations

import logging

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .kubernetes_client import KubernetesClient

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Kubernetes sensors based on a config entry."""
    client = KubernetesClient(config_entry.data)

    # Create sensors for different Kubernetes resources
    sensors = [
        KubernetesPodsSensor(client, config_entry),
        KubernetesNodesSensor(client, config_entry),
        KubernetesDeploymentsSensor(client, config_entry),
        KubernetesStatefulSetsSensor(client, config_entry),
    ]

    async_add_entities(sensors)


class KubernetesBaseSensor(SensorEntity):
    """Base class for Kubernetes sensors."""

    def __init__(self, client: KubernetesClient, config_entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        self.client = client
        self.config_entry = config_entry
        self._attr_has_entity_name = True
        self._attr_state_class = SensorStateClass.MEASUREMENT


class KubernetesPodsSensor(KubernetesBaseSensor):
    """Sensor for Kubernetes pods count."""

    def __init__(self, client: KubernetesClient, config_entry: ConfigEntry) -> None:
        """Initialize the pods sensor."""
        super().__init__(client, config_entry)
        self._attr_name = "Pods Count"
        self._attr_unique_id = f"{config_entry.entry_id}_pods_count"
        self._attr_native_unit_of_measurement = "pods"

    async def async_update(self) -> None:
        """Update the sensor state."""
        try:
            count = await self.client.get_pods_count()
            self._attr_native_value = count
        except Exception as ex:
            _LOGGER.error("Failed to update pods sensor: %s", ex)
            self._attr_native_value = 0


class KubernetesNodesSensor(KubernetesBaseSensor):
    """Sensor for Kubernetes nodes count."""

    def __init__(self, client: KubernetesClient, config_entry: ConfigEntry) -> None:
        """Initialize the nodes sensor."""
        super().__init__(client, config_entry)
        self._attr_name = "Nodes Count"
        self._attr_unique_id = f"{config_entry.entry_id}_nodes_count"
        self._attr_native_unit_of_measurement = "nodes"

    async def async_update(self) -> None:
        """Update the sensor state."""
        try:
            count = await self.client.get_nodes_count()
            self._attr_native_value = count
        except Exception as ex:
            _LOGGER.error("Failed to update nodes sensor: %s", ex)
            self._attr_native_value = 0


class KubernetesDeploymentsSensor(KubernetesBaseSensor):
    """Sensor for Kubernetes deployments count."""

    def __init__(self, client: KubernetesClient, config_entry: ConfigEntry) -> None:
        """Initialize the deployments sensor."""
        super().__init__(client, config_entry)
        self._attr_name = "Deployments Count"
        self._attr_unique_id = f"{config_entry.entry_id}_deployments_count"
        self._attr_native_unit_of_measurement = "deployments"

    async def async_update(self) -> None:
        """Update the sensor state."""
        try:
            count = await self.client.get_deployments_count()
            self._attr_native_value = count
        except Exception as ex:
            _LOGGER.error("Failed to update deployments sensor: %s", ex)
            self._attr_native_value = 0


class KubernetesStatefulSetsSensor(KubernetesBaseSensor):
    """Sensor for Kubernetes StatefulSets count."""

    def __init__(self, client: KubernetesClient, config_entry: ConfigEntry) -> None:
        """Initialize the StatefulSets sensor."""
        super().__init__(client, config_entry)
        self._attr_name = "StatefulSets Count"
        self._attr_unique_id = f"{config_entry.entry_id}_statefulsets_count"
        self._attr_native_unit_of_measurement = "statefulsets"

    async def async_update(self) -> None:
        """Update the sensor state."""
        try:
            count = await self.client.get_statefulsets_count()
            self._attr_native_value = count
        except Exception as ex:
            _LOGGER.error("Failed to update StatefulSets sensor: %s", ex)
            self._attr_native_value = 0
