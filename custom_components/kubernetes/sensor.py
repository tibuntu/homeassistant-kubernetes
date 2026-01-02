"""Sensor platform for Kubernetes integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry

from .const import ATTR_WORKLOAD_TYPE, DOMAIN, WORKLOAD_TYPE_POD
from .coordinator import KubernetesDataCoordinator
from .device import get_cluster_device_info, get_namespace_device_info

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
            KubernetesDaemonSetsSensor(coordinator, client, config_entry),
            KubernetesCronJobsSensor(coordinator, client, config_entry),
        ]

        # Wait for the coordinator to have initial data
        await coordinator.async_config_entry_first_refresh()

        # Ensure cluster device exists
        from .device import get_or_create_cluster_device

        await get_or_create_cluster_device(hass, config_entry)

        # Create individual sensors for each Kubernetes node
        nodes_data = coordinator.get_all_nodes_data()
        _LOGGER.debug("Creating node sensors for nodes: %s", list(nodes_data.keys()))

        node_sensors_created = 0
        for node_name in nodes_data:
            node_sensor = KubernetesNodeSensor(
                coordinator, client, config_entry, node_name
            )
            sensors.append(node_sensor)
            node_sensors_created += 1
            _LOGGER.debug(
                "Created node sensor for: %s (unique_id: %s)",
                node_name,
                node_sensor.unique_id,
            )

        # Create individual sensors for each Kubernetes pod
        pods_data = coordinator.get_all_pods_data()
        _LOGGER.debug("Creating pod sensors for pods: %s", list(pods_data.keys()))

        # Ensure namespace devices exist for all pod namespaces
        from .device import get_or_create_namespace_device

        pod_namespaces = {
            pod_data.get("namespace", "default") for pod_data in pods_data.values()
        }
        for namespace in pod_namespaces:
            await get_or_create_namespace_device(hass, config_entry, namespace)

        pod_sensors_created = 0
        for pod_key, pod_data in pods_data.items():
            namespace = pod_data.get("namespace", "default")
            pod_name = pod_data.get("name", "unknown")
            pod_sensor = KubernetesPodSensor(
                coordinator, client, config_entry, namespace, pod_name
            )
            sensors.append(pod_sensor)
            pod_sensors_created += 1
            _LOGGER.debug(
                "Created pod sensor for: %s/%s (unique_id: %s)",
                namespace,
                pod_name,
                pod_sensor.unique_id,
            )

        async_add_entities(sensors)

        # Store the add_entities callback for dynamic entity management
        if DOMAIN not in hass.data:
            hass.data[DOMAIN] = {}
        if config_entry.entry_id not in hass.data[DOMAIN]:
            hass.data[DOMAIN][config_entry.entry_id] = {}
        hass.data[DOMAIN][config_entry.entry_id][
            "sensor_add_entities"
        ] = async_add_entities

        # Set up listener for adding new entities dynamically
        @callback
        def _async_add_new_entities() -> None:
            """Add new entities when new resources are discovered."""
            hass.async_create_task(
                _async_discover_and_add_new_sensors(
                    hass, config_entry, coordinator, client
                )
            )

        # Register the callback with the coordinator
        coordinator.async_add_listener(_async_add_new_entities)

        _LOGGER.debug(
            "Successfully set up %d Kubernetes sensors (including %d node sensors, %d pod sensors)",
            len(sensors),
            node_sensors_created,
            pod_sensors_created,
        )
    except Exception as ex:
        _LOGGER.error("Failed to set up Kubernetes sensors: %s", ex)
        raise


def _discover_new_node_sensors(
    coordinator: KubernetesDataCoordinator,
    client: Any,
    config_entry: ConfigEntry,
    existing_unique_ids: set[str],
) -> list[KubernetesNodeSensor]:
    """Discover new node sensors."""
    new_entities = []
    if coordinator.data and "nodes" in coordinator.data:
        for node_name in coordinator.data["nodes"]:
            unique_id = f"{config_entry.entry_id}_node_{node_name}"
            if unique_id not in existing_unique_ids:
                _LOGGER.info("Adding new node sensor for: %s", node_name)
                new_entities.append(
                    KubernetesNodeSensor(coordinator, client, config_entry, node_name)
                )
    return new_entities


def _discover_new_pod_sensors(
    coordinator: KubernetesDataCoordinator,
    client: Any,
    config_entry: ConfigEntry,
    existing_unique_ids: set[str],
) -> list[KubernetesPodSensor]:
    """Discover new pod sensors."""
    new_entities = []
    if coordinator.data and "pods" in coordinator.data:
        for pod_key, pod_data in coordinator.data["pods"].items():
            namespace = pod_data.get("namespace", "default")
            pod_name = pod_data.get("name", "unknown")
            unique_id = f"{config_entry.entry_id}_pod_{namespace}_{pod_name}"
            if unique_id not in existing_unique_ids:
                _LOGGER.info("Adding new pod sensor for: %s/%s", namespace, pod_name)
                new_entities.append(
                    KubernetesPodSensor(
                        coordinator, client, config_entry, namespace, pod_name
                    )
                )
    return new_entities


async def _async_discover_and_add_new_sensors(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    coordinator: KubernetesDataCoordinator,
    client: Any,
) -> None:
    """Discover and add new sensors for newly discovered Kubernetes resources."""
    try:
        entity_registry = async_get_entity_registry(hass)

        # Get the stored add_entities callback
        sensor_data = hass.data[DOMAIN].get(config_entry.entry_id, {})
        add_entities_callback = sensor_data.get("sensor_add_entities")
        if not add_entities_callback:
            _LOGGER.warning(
                "No add_entities callback found for dynamic sensor management"
            )
            return

        # Get existing entities for this config entry
        existing_entities = entity_registry.entities.get_entries_for_config_entry_id(
            config_entry.entry_id
        )
        existing_unique_ids = {
            entity.unique_id for entity in existing_entities if entity.unique_id
        }

        # Ensure cluster device exists
        from .device import get_or_create_cluster_device, get_or_create_namespace_device

        await get_or_create_cluster_device(hass, config_entry)

        # Discover new sensors
        new_entities = []
        new_entities.extend(
            _discover_new_node_sensors(
                coordinator, client, config_entry, existing_unique_ids
            )
        )
        pod_sensors = _discover_new_pod_sensors(
            coordinator, client, config_entry, existing_unique_ids
        )
        # Ensure namespace devices exist for new pod sensors
        pod_namespaces = {sensor.namespace for sensor in pod_sensors}
        for namespace in pod_namespaces:
            await get_or_create_namespace_device(hass, config_entry, namespace)
        new_entities.extend(pod_sensors)

        # Check for new deployments
        # Deployment sensors are removed in favor of attributes on the deployment switch

        # Add new entities if any were found
        if new_entities:
            _LOGGER.info("Adding %d new sensors", len(new_entities))
            add_entities_callback(new_entities)
        else:
            _LOGGER.debug("No new sensors to add")

    except Exception as ex:
        _LOGGER.error("Failed to discover and add new sensors: %s", ex)


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
        return available

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
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        return get_cluster_device_info(self.config_entry)

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
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        return get_cluster_device_info(self.config_entry)

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
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        return get_cluster_device_info(self.config_entry)

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
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        return get_cluster_device_info(self.config_entry)

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


class KubernetesDaemonSetsSensor(KubernetesBaseSensor):
    """Sensor for Kubernetes DaemonSets count."""

    def __init__(
        self, coordinator: KubernetesDataCoordinator, client, config_entry: ConfigEntry
    ) -> None:
        """Initialize the DaemonSets sensor."""
        super().__init__(coordinator, client, config_entry)
        self._attr_name = "DaemonSets Count"
        self._attr_unique_id = f"{config_entry.entry_id}_daemonsets_count"
        self._attr_native_unit_of_measurement = "daemonsets"

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        return get_cluster_device_info(self.config_entry)

    @property
    def native_value(self) -> int:
        """Return the native value of the sensor."""
        if not self.coordinator.data:
            return 0

        # Get daemonsets count from coordinator data
        if "daemonsets" in self.coordinator.data:
            return len(self.coordinator.data["daemonsets"])

        # Fallback to calling client directly if not in coordinator data
        return 0

    async def async_update(self) -> None:
        """Update the daemonsets sensor state."""
        try:
            await super().async_update()
            # If coordinator data is not available, try to get data directly from client
            if not self.coordinator.data or "daemonsets" not in self.coordinator.data:
                if hasattr(self.client, "get_daemonsets_count"):
                    count = await self.client.get_daemonsets_count()
                    self._attr_native_value = count
        except Exception as ex:
            _LOGGER.error("Failed to update daemonsets sensor: %s", ex)
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
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        return get_cluster_device_info(self.config_entry)

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

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        return get_cluster_device_info(self.config_entry)

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
            "memory_capacity_(GiB)": f"{node_data.get('memory_capacity_gib', 0)} GiB",
            "memory_allocatable_(GiB)": f"{node_data.get('memory_allocatable_gib', 0)} GiB",
            "CPU": f"{node_data.get('cpu_cores', 0)} vCPU",
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


class KubernetesPodSensor(KubernetesBaseSensor):
    """Sensor for individual Kubernetes pod with detailed information."""

    def __init__(
        self,
        coordinator: KubernetesDataCoordinator,
        client,
        config_entry: ConfigEntry,
        namespace: str,
        pod_name: str,
    ) -> None:
        """Initialize the pod sensor."""
        super().__init__(coordinator, client, config_entry)
        self.namespace = namespace
        self.pod_name = pod_name
        self._attr_name = f"{pod_name}"
        self._attr_unique_id = f"{config_entry.entry_id}_pod_{namespace}_{pod_name}"
        self._attr_native_unit_of_measurement = None
        self._attr_icon = "mdi:kubernetes"
        # Override state class since this sensor returns string values, not measurements
        self._attr_state_class = None

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        return get_namespace_device_info(self.config_entry, self.namespace)

    @property
    def native_value(self) -> str:
        """Return the native value of the sensor (pod phase)."""
        pod_data = self.coordinator.get_pod_data(self.namespace, self.pod_name)
        if pod_data:
            phase = pod_data.get("phase", "Unknown")
            _LOGGER.debug(
                "Pod %s/%s native_value: %s", self.namespace, self.pod_name, phase
            )
            return phase
        _LOGGER.debug(
            "Pod %s/%s has no data, returning Unknown", self.namespace, self.pod_name
        )
        return "Unknown"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes for the pod."""
        pod_data = self.coordinator.get_pod_data(self.namespace, self.pod_name)
        if not pod_data:
            return {}

        attributes = {
            "namespace": pod_data.get("namespace", "N/A"),
            "phase": pod_data.get("phase", "Unknown"),
            "ready_containers": pod_data.get("ready_containers", 0),
            "total_containers": pod_data.get("total_containers", 0),
            "restart_count": pod_data.get("restart_count", 0),
            "node_name": pod_data.get("node_name", "N/A"),
            "pod_ip": pod_data.get("pod_ip", "N/A"),
            "creation_timestamp": pod_data.get("creation_timestamp", "N/A"),
            "owner_kind": pod_data.get("owner_kind", "N/A"),
            "owner_name": pod_data.get("owner_name", "N/A"),
            ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_POD,
        }

        return attributes

    async def async_update(self) -> None:
        """Update the pod sensor state."""
        try:
            await super().async_update()
            # The base class handles coordinator updates
        except Exception as ex:
            _LOGGER.error(
                "Failed to update pod sensor %s/%s: %s",
                self.namespace,
                self.pod_name,
                ex,
            )
