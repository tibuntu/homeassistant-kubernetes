"""Sensor platform for Kubernetes integration."""

from __future__ import annotations

import logging
from typing import Any

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
            KubernetesCronJobsSensor(coordinator, client, config_entry),
        ]

        # Wait for the coordinator to have initial data
        await coordinator.async_config_entry_first_refresh()

        # Create individual sensors for each Kubernetes node
        nodes_data = coordinator.get_all_nodes_data()
        _LOGGER.debug("Creating node sensors for nodes: %s", list(nodes_data.keys()))
        
        node_sensors_created = 0
        for node_name in nodes_data:
            node_sensor = KubernetesNodeSensor(coordinator, client, config_entry, node_name)
            sensors.append(node_sensor)
            node_sensors_created += 1
            _LOGGER.debug("Created node sensor for: %s (unique_id: %s)", node_name, node_sensor.unique_id)

        async_add_entities(sensors)
        _LOGGER.debug("Successfully set up %d Kubernetes sensors (including %d node sensors)", len(sensors), node_sensors_created)
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
        available = self.coordinator.last_update_success
        # Add specific logging for node sensors to track availability issues
        if hasattr(self, 'node_name'):
            _LOGGER.debug("Node sensor %s availability: %s (coordinator success: %s)",
                         self.node_name, available, self.coordinator.last_update_success)
        return available

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        # Add specific logging for node sensors
        if hasattr(self, 'node_name'):
            _LOGGER.info("Node sensor %s added to Home Assistant", self.node_name)
        self.async_on_remove(
            self.coordinator.async_add_listener(self._handle_coordinator_update)
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        # Add specific logging for node sensors during updates
        if hasattr(self, 'node_name'):
            _LOGGER.debug("Node sensor %s received coordinator update", self.node_name)
        self.async_write_ha_state()

    async def async_update(self) -> None:
        """Update the sensor state."""
        # This method is called by tests and can be used for direct updates
        # In normal operation, the coordinator handles updates
        try:
            # Trigger coordinator update if needed
            await self.coordinator.async_request_refresh()
        except Exception as ex:
            _LOGGER.error("Failed to update sensor %s: %s", self.name, ex)


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
        """Update the pods sensor state."""
        try:
            await super().async_update()
            # If coordinator data is not available, try to get data directly from client
            if not self.coordinator.data or "pods_count" not in self.coordinator.data:
                if hasattr(self.client, "get_pods_count"):
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
        """Update the nodes sensor state."""
        try:
            await super().async_update()
            # If coordinator data is not available, try to get data directly from client
            if not self.coordinator.data or "nodes_count" not in self.coordinator.data:
                if hasattr(self.client, "get_nodes_count"):
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
        """Update the deployments sensor state."""
        try:
            await super().async_update()
            # If coordinator data is not available, try to get data directly from client
            if not self.coordinator.data or "deployments" not in self.coordinator.data:
                if hasattr(self.client, "get_deployments_count"):
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
        """Update the statefulsets sensor state."""
        try:
            await super().async_update()
            # If coordinator data is not available, try to get data directly from client
            if not self.coordinator.data or "statefulsets" not in self.coordinator.data:
                if hasattr(self.client, "get_statefulsets_count"):
                    count = await self.client.get_statefulsets_count()
                    self._attr_native_value = count
        except Exception as ex:
            _LOGGER.error("Failed to update statefulsets sensor: %s", ex)
            self._attr_native_value = 0


class KubernetesCronJobsSensor(KubernetesBaseSensor):
    """Sensor for Kubernetes CronJobs count."""

    def __init__(
        self, coordinator: KubernetesDataCoordinator, client, config_entry: ConfigEntry
    ) -> None:
        """Initialize the CronJobs sensor."""
        super().__init__(coordinator, client, config_entry)
        self._attr_name = "CronJobs Count"
        self._attr_unique_id = f"{config_entry.entry_id}_cronjobs_count"
        self._attr_native_unit_of_measurement = "cronjobs"

    @property
    def native_value(self) -> int:
        """Return the native value of the sensor."""
        if not self.coordinator.data:
            return 0

        # Get cronjobs count from coordinator data
        if "cronjobs" in self.coordinator.data:
            return len(self.coordinator.data["cronjobs"])

        # Fallback to calling client directly if not in coordinator data
        return 0

    async def async_update(self) -> None:
        """Update the cronjobs sensor state."""
        try:
            await super().async_update()
            # If coordinator data is not available, try to get data directly from client
            if not self.coordinator.data or "cronjobs" not in self.coordinator.data:
                if hasattr(self.client, "get_cronjobs_count"):
                    count = await self.client.get_cronjobs_count()
                    self._attr_native_value = count
        except Exception as ex:
            _LOGGER.error("Failed to update cronjobs sensor: %s", ex)
            self._attr_native_value = 0


class KubernetesNodeSensor(KubernetesBaseSensor):
    """Sensor for individual Kubernetes node with detailed information."""

    def __init__(
        self, 
        coordinator: KubernetesDataCoordinator, 
        client, 
        config_entry: ConfigEntry,
        node_name: str,
    ) -> None:
        """Initialize the node sensor."""
        super().__init__(coordinator, client, config_entry)
        self.node_name = node_name
        self._attr_name = f"{node_name}"
        self._attr_unique_id = f"{config_entry.entry_id}_node_{node_name}"
        self._attr_native_unit_of_measurement = None
        self._attr_icon = "mdi:server"
        # Override state class since this sensor returns string values, not measurements
        self._attr_state_class = None
        
        _LOGGER.debug("Initialized node sensor for %s with unique_id: %s", node_name, self._attr_unique_id)

    @property
    def native_value(self) -> str:
        """Return the native value of the sensor (node status)."""
        node_data = self.coordinator.get_node_data(self.node_name)
        if node_data:
            status = node_data.get("status", "Unknown")
            _LOGGER.debug("Node %s native_value: %s", self.node_name, status)
            return status
        _LOGGER.debug("Node %s has no data, returning Unknown", self.node_name)
        return "Unknown"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes for the node."""
        node_data = self.coordinator.get_node_data(self.node_name)
        if not node_data:
            return {}

        attributes = {
            "internal_IP": node_data.get("internal_ip", "N/A"),
            "external_IP": node_data.get("external_ip", "N/A"),
            "memory_capacity_GB": node_data.get("memory_capacity_gb", 0),
            "memory_allocatable_GB": node_data.get("memory_allocatable_gb", 0),
            "CPU_cores": node_data.get("cpu_cores", 0),
            "OS_image": node_data.get("os_image", "N/A"),
            "kernel_version": node_data.get("kernel_version", "N/A"),
            "container_runtime": node_data.get("container_runtime", "N/A"),
            "kubelet_version": node_data.get("kubelet_version", "N/A"),
            "schedulable": node_data.get("schedulable", True),
            "creation_timestamp": node_data.get("creation_timestamp", "N/A"),
        }

        return attributes

    async def async_update(self) -> None:
        """Update the node sensor state."""
        try:
            await super().async_update()
            # The base class handles coordinator updates
        except Exception as ex:
            _LOGGER.error("Failed to update node sensor %s: %s", self.node_name, ex)
