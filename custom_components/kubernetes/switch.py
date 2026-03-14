"""Switch platform for Kubernetes integration."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry

from .const import (
    ATTR_WORKLOAD_TYPE,
    CONF_SCALE_COOLDOWN,
    CONF_SCALE_VERIFICATION_TIMEOUT,
    DEFAULT_SCALE_COOLDOWN,
    DEFAULT_SCALE_VERIFICATION_TIMEOUT,
    DOMAIN,
    WORKLOAD_TYPE_CRONJOB,
    WORKLOAD_TYPE_DEPLOYMENT,
    WORKLOAD_TYPE_STATEFULSET,
)
from .coordinator import KubernetesDataCoordinator
from .device import get_namespace_device_info

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Kubernetes switches based on a config entry."""
    # Get the coordinator from hass.data
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    client = hass.data[DOMAIN][config_entry.entry_id]["client"]

    # Ensure namespace devices exist
    from .device import get_or_create_namespace_device

    # Store the add_entities callback for dynamic entity management
    switches: list[SwitchEntity] = []

    # Get all deployments and create switches for them
    deployments = await client.get_deployments()
    deployment_namespaces = set()
    for deployment in deployments:
        namespace = deployment.get("namespace", "default")
        deployment_namespaces.add(namespace)
        switches.append(
            KubernetesDeploymentSwitch(
                coordinator, config_entry, deployment["name"], namespace
            )
        )

    # Get all StatefulSets and create switches for them
    statefulsets = await client.get_statefulsets()
    statefulset_namespaces = set()
    for statefulset in statefulsets:
        namespace = statefulset.get("namespace", "default")
        statefulset_namespaces.add(namespace)
        switches.append(
            KubernetesStatefulSetSwitch(
                coordinator, config_entry, statefulset["name"], namespace
            )
        )

    # Get all CronJobs and create switches for them
    cronjobs = await client.get_cronjobs()
    cronjob_namespaces = set()
    for cronjob in cronjobs:
        namespace = cronjob.get("namespace", "default")
        cronjob_namespaces.add(namespace)
        switches.append(
            KubernetesCronJobSwitch(
                coordinator, config_entry, cronjob["name"], namespace
            )
        )

    # Ensure all namespace devices exist
    all_namespaces = deployment_namespaces | statefulset_namespaces | cronjob_namespaces
    for namespace in all_namespaces:
        await get_or_create_namespace_device(hass, config_entry, namespace)

    async_add_entities(switches)

    # Store the add_entities callback for dynamic entity management
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    hass.data[DOMAIN]["switch_add_entities"] = async_add_entities
    if config_entry.entry_id not in hass.data[DOMAIN]:
        hass.data[DOMAIN][config_entry.entry_id] = {}
    hass.data[DOMAIN][config_entry.entry_id]["switch_pending_unique_ids"] = set()

    # Set up listener for adding new entities dynamically
    @callback
    def _async_add_new_entities() -> None:
        """Add new entities when new resources are discovered."""
        hass.async_create_task(
            _async_discover_and_add_new_entities(
                hass, config_entry, coordinator, client
            )
        )

    # Register the callback with the coordinator
    coordinator.async_add_listener(_async_add_new_entities)


async def _async_discover_and_add_new_entities(  # noqa: C901
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    coordinator: KubernetesDataCoordinator,
    client: Any,
) -> None:
    """Discover and add new entities for newly created Kubernetes resources."""
    try:
        entity_registry = async_get_entity_registry(hass)

        # Get the stored add_entities callback
        add_entities_callback = hass.data[DOMAIN].get("switch_add_entities")
        if not add_entities_callback:
            _LOGGER.warning(
                "No add_entities callback found for dynamic entity management"
            )
            return

        # Get existing entities for this config entry, plus any that were already
        # passed to add_entities_callback but may not be in the registry yet.
        existing_entities = entity_registry.entities.get_entries_for_config_entry_id(
            config_entry.entry_id
        )
        existing_unique_ids = {
            entity.unique_id for entity in existing_entities if entity.unique_id
        }
        entry_data = hass.data[DOMAIN].get(config_entry.entry_id, {})
        pending_ids: set[str] = entry_data.get("switch_pending_unique_ids", set())
        # Prune IDs that are now in the registry — keeps the set bounded
        pending_ids -= existing_unique_ids
        existing_unique_ids |= pending_ids

        new_entities: list[SwitchEntity] = []

        # Ensure namespace devices exist for new entities
        from .device import get_or_create_namespace_device

        # Check for new deployments
        if coordinator.data and "deployments" in coordinator.data:
            for deployment_name, deployment_data in coordinator.data[
                "deployments"
            ].items():
                unique_id = f"{config_entry.entry_id}_{deployment_name}_deployment"
                if unique_id not in existing_unique_ids:
                    namespace = deployment_data.get("namespace", "default")
                    await get_or_create_namespace_device(hass, config_entry, namespace)
                    _LOGGER.info(
                        "Adding new entity for deployment: %s", deployment_name
                    )
                    new_entities.append(
                        KubernetesDeploymentSwitch(
                            coordinator,
                            config_entry,
                            deployment_name,
                            namespace,
                        )
                    )

        # Check for new StatefulSets
        if coordinator.data and "statefulsets" in coordinator.data:
            for statefulset_name, statefulset_data in coordinator.data[
                "statefulsets"
            ].items():
                unique_id = f"{config_entry.entry_id}_{statefulset_name}_statefulset"
                if unique_id not in existing_unique_ids:
                    namespace = statefulset_data.get("namespace", "default")
                    await get_or_create_namespace_device(hass, config_entry, namespace)
                    _LOGGER.info(
                        "Adding new entity for StatefulSet: %s", statefulset_name
                    )
                    new_entities.append(
                        KubernetesStatefulSetSwitch(
                            coordinator,
                            config_entry,
                            statefulset_name,
                            namespace,
                        )
                    )

        # Check for new CronJobs
        if coordinator.data and "cronjobs" in coordinator.data:
            for cronjob_name, cronjob_data in coordinator.data["cronjobs"].items():
                namespace = cronjob_data.get("namespace", "default")
                unique_id = (
                    f"{config_entry.entry_id}_{namespace}_{cronjob_name}_cronjob"
                )
                if unique_id not in existing_unique_ids:
                    await get_or_create_namespace_device(hass, config_entry, namespace)
                    _LOGGER.info("Adding new entity for CronJob: %s", cronjob_name)
                    new_entities.append(
                        KubernetesCronJobSwitch(
                            coordinator,
                            config_entry,
                            cronjob_name,
                            namespace,
                        )
                    )

        # Add new entities if any were found
        if new_entities:
            _LOGGER.info("Adding %d new entities", len(new_entities))
            pending_ids.update(e.unique_id for e in new_entities if e.unique_id)
            add_entities_callback(new_entities)
        else:
            _LOGGER.debug("No new entities to add")

    except Exception as ex:
        _LOGGER.error("Failed to discover and add new entities: %s", ex)


class KubernetesReplicaWorkloadSwitch(SwitchEntity):
    """Base switch for replica-based Kubernetes workloads (Deployments, StatefulSets)."""

    def __init__(
        self,
        coordinator: KubernetesDataCoordinator,
        config_entry: ConfigEntry,
        workload_name: str,
        namespace: str,
        *,
        workload_type: str,
        resource_key: str,
        unique_id_suffix: str,
        start_method: str,
        stop_method: str,
        log_label: str,
        attr_name_key: str,
    ) -> None:
        """Initialize the replica workload switch."""
        self.coordinator = coordinator
        self.config_entry = config_entry
        self.workload_name = workload_name
        self.namespace = namespace
        self._workload_type = workload_type
        self._resource_key = resource_key
        self._start_method = start_method
        self._stop_method = stop_method
        self._log_label = log_label
        self._attr_name_key = attr_name_key
        self._attr_has_entity_name = True
        self._attr_name = workload_name
        self._attr_unique_id = (
            f"{config_entry.entry_id}_{workload_name}_{unique_id_suffix}"
        )
        self._attr_icon = "mdi:kubernetes"
        self._is_on = False
        self._replicas = 0
        self._last_scale_time = 0.0
        self._scale_cooldown = config_entry.data.get(
            CONF_SCALE_COOLDOWN, DEFAULT_SCALE_COOLDOWN
        )
        self._scale_verification_timeout = config_entry.data.get(
            CONF_SCALE_VERIFICATION_TIMEOUT, DEFAULT_SCALE_VERIFICATION_TIMEOUT
        )
        self._last_scale_attempt_failed = False
        self._cpu_usage = 0.0
        self._memory_usage = 0.0

    def _get_workload_data(self) -> dict[str, Any] | None:
        """Get workload data from coordinator."""
        if not self.coordinator.data or self._resource_key not in self.coordinator.data:
            return None
        return self.coordinator.data[self._resource_key].get(self.workload_name)

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return get_namespace_device_info(self.config_entry, self.namespace)

    @property
    def is_on(self) -> bool:
        """Return true if the workload is running (has replicas > 0)."""
        return self._is_on

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes."""
        return {
            self._attr_name_key: self.workload_name,
            "namespace": self.namespace,
            "replicas": self._replicas,
            ATTR_WORKLOAD_TYPE: self._workload_type,
            "last_scale_attempt_failed": self._last_scale_attempt_failed,
            "cpu_usage_(millicores)": f"{int(self._cpu_usage)}",
            "memory_usage_(MiB)": f"{int(self._memory_usage)}",
        }

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
        workload_data = self._get_workload_data()
        if workload_data:
            self._replicas = workload_data.get("replicas", 0)
            self._is_on = workload_data.get("is_running", False)
            old_cpu = self._cpu_usage
            old_memory = self._memory_usage
            self._cpu_usage = workload_data.get("cpu_usage", 0.0)
            self._memory_usage = workload_data.get("memory_usage", 0.0)
            if old_cpu != self._cpu_usage or old_memory != self._memory_usage:
                _LOGGER.debug(
                    "%s %s metrics updated: CPU=%.2f m (was %.2f), Memory=%.2f MiB (was %.2f)",
                    self._log_label,
                    self.workload_name,
                    self._cpu_usage,
                    old_cpu,
                    self._memory_usage,
                    old_memory,
                )
        else:
            _LOGGER.warning(
                "%s %s not found in coordinator data during update",
                self._log_label,
                self.workload_name,
            )
        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the workload on by scaling to 1 replica."""
        _LOGGER.info("Scaling %s %s to 1 replica", self._log_label, self.workload_name)

        client = self.coordinator.client
        start_fn = getattr(client, self._start_method)
        success = await start_fn(
            self.workload_name, replicas=1, namespace=self.namespace
        )

        if success:
            self._is_on = True
            self._replicas = 1
            self._last_scale_time = time.time()
            self._last_scale_attempt_failed = False
            self.async_write_ha_state()
            _LOGGER.info(
                "Successfully scaled %s %s to 1 replica",
                self._log_label,
                self.workload_name,
            )
            await self._verify_scaling(1)
        else:
            _LOGGER.error("Failed to start %s %s", self._log_label, self.workload_name)
            self._last_scale_attempt_failed = True
            self.async_write_ha_state()
            await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the workload off by scaling to 0 replicas."""
        _LOGGER.info("Scaling %s %s to 0 replicas", self._log_label, self.workload_name)

        client = self.coordinator.client
        stop_fn = getattr(client, self._stop_method)
        success = await stop_fn(self.workload_name, namespace=self.namespace)

        if success:
            self._is_on = False
            self._replicas = 0
            self._last_scale_time = time.time()
            self._last_scale_attempt_failed = False
            self.async_write_ha_state()
            _LOGGER.info(
                "Successfully scaled %s %s to 0 replicas",
                self._log_label,
                self.workload_name,
            )
            await self._verify_scaling(0)
        else:
            _LOGGER.error("Failed to stop %s %s", self._log_label, self.workload_name)
            self._last_scale_attempt_failed = True
            self.async_write_ha_state()
            await self.coordinator.async_request_refresh()

    async def async_update(self) -> None:
        """Update the switch state from coordinator data."""
        if time.time() - self._last_scale_time < self._scale_cooldown:
            _LOGGER.debug(
                "Skipping state update for %s (scaled recently, cooldown: %.1fs remaining)",
                self.workload_name,
                self._scale_cooldown - (time.time() - self._last_scale_time),
            )
            return

        workload_data = self._get_workload_data()

        if workload_data is None:
            _LOGGER.warning(
                "%s %s not found in coordinator data",
                self._log_label,
                self.workload_name,
            )
            return

        old_replicas = self._replicas
        old_state = self._is_on

        self._replicas = workload_data["replicas"]
        self._is_on = workload_data["is_running"]
        self._cpu_usage = workload_data.get("cpu_usage", 0.0)
        self._memory_usage = workload_data.get("memory_usage", 0.0)

        if old_replicas != self._replicas:
            _LOGGER.info(
                "%s %s replicas changed: %d -> %d",
                self._log_label,
                self.workload_name,
                old_replicas,
                self._replicas,
            )
        if old_state != self._is_on:
            _LOGGER.info(
                "%s %s state changed: %s -> %s",
                self._log_label,
                self.workload_name,
                old_state,
                self._is_on,
            )
        else:
            _LOGGER.debug(
                "%s %s state unchanged: replicas=%d, is_running=%s",
                self._log_label,
                self.workload_name,
                self._replicas,
                self._is_on,
            )

    async def _verify_scaling(self, target_replicas: int) -> None:
        """Verify that scaling actually took effect."""
        max_attempts = self._scale_verification_timeout // 5
        for attempt in range(max_attempts):
            await asyncio.sleep(5)

            try:
                await self.coordinator.async_request_refresh()

                workload_data = self._get_workload_data()
                if workload_data is None:
                    _LOGGER.warning(
                        "%s %s not found during scaling verification",
                        self._log_label,
                        self.workload_name,
                    )
                    continue

                current_replicas = workload_data["replicas"]
                if current_replicas == target_replicas:
                    _LOGGER.info(
                        "%s %s scaling verified: %d replicas",
                        self._log_label,
                        self.workload_name,
                        current_replicas,
                    )
                    return
                else:
                    _LOGGER.debug(
                        "%s %s still scaling: %d replicas (target: %d)",
                        self._log_label,
                        self.workload_name,
                        current_replicas,
                        target_replicas,
                    )
            except Exception as ex:
                _LOGGER.warning(
                    "Failed to verify scaling for %s (attempt %d): %s",
                    self.workload_name,
                    attempt + 1,
                    ex,
                )

        _LOGGER.warning(
            "%s %s scaling verification timed out after %d attempts",
            self._log_label,
            self.workload_name,
            max_attempts,
        )


class KubernetesDeploymentSwitch(KubernetesReplicaWorkloadSwitch):
    """Switch for controlling a Kubernetes Deployment."""

    def __init__(
        self,
        coordinator: KubernetesDataCoordinator,
        config_entry: ConfigEntry,
        deployment_name: str,
        namespace: str,
    ) -> None:
        """Initialize the deployment switch."""
        super().__init__(
            coordinator,
            config_entry,
            deployment_name,
            namespace,
            workload_type=WORKLOAD_TYPE_DEPLOYMENT,
            resource_key="deployments",
            unique_id_suffix="deployment",
            start_method="start_deployment",
            stop_method="stop_deployment",
            log_label="Deployment",
            attr_name_key="deployment_name",
        )
        self.deployment_name = deployment_name


class KubernetesStatefulSetSwitch(KubernetesReplicaWorkloadSwitch):
    """Switch for controlling a Kubernetes StatefulSet."""

    def __init__(
        self,
        coordinator: KubernetesDataCoordinator,
        config_entry: ConfigEntry,
        statefulset_name: str,
        namespace: str,
    ) -> None:
        """Initialize the StatefulSet switch."""
        super().__init__(
            coordinator,
            config_entry,
            statefulset_name,
            namespace,
            workload_type=WORKLOAD_TYPE_STATEFULSET,
            resource_key="statefulsets",
            unique_id_suffix="statefulset",
            start_method="start_statefulset",
            stop_method="stop_statefulset",
            log_label="StatefulSet",
            attr_name_key="statefulset_name",
        )
        self.statefulset_name = statefulset_name


class KubernetesCronJobSwitch(SwitchEntity):
    """Switch for controlling a Kubernetes CronJob suspension state."""

    def __init__(
        self,
        coordinator: KubernetesDataCoordinator,
        config_entry: ConfigEntry,
        cronjob_name: str,
        namespace: str,
    ) -> None:
        """Initialize the CronJob switch."""
        self.coordinator = coordinator
        self.config_entry = config_entry
        self.cronjob_name = cronjob_name
        self.namespace = namespace
        self._attr_has_entity_name = True
        self._attr_name = cronjob_name
        self._attr_unique_id = (
            f"{config_entry.entry_id}_{namespace}_{cronjob_name}_cronjob"
        )
        self._attr_icon = "mdi:clock-outline"
        self._is_on = False  # True = enabled (not suspended), False = suspended
        self._active_jobs_count = 0
        self._schedule = ""
        self._suspend = False
        self._last_schedule_time: str | None = None
        self._next_schedule_time: str | None = None
        self._last_suspend_time: float | None = None
        self._last_resume_time: float | None = None

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return get_namespace_device_info(self.config_entry, self.namespace)

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.last_update_success

    @property
    def is_on(self) -> bool:
        """Return True if the CronJob is enabled (not suspended)."""
        return self._is_on

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes."""
        return {
            "namespace": self.namespace,
            "cronjob_name": self.cronjob_name,
            "schedule": self._schedule,
            "suspend": self._suspend,
            "suspended": self._suspend,  # Alias for clarity
            "active_jobs_count": self._active_jobs_count,
            "last_schedule_time": self._last_schedule_time,
            "next_schedule_time": self._next_schedule_time,
            "last_suspend_time": self._last_suspend_time,
            "last_resume_time": self._last_resume_time,
            ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_CRONJOB,
        }

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

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Resume the CronJob by setting suspend=false."""
        try:
            _LOGGER.info("Resuming CronJob: %s", self.cronjob_name)

            # Get the client from hass.data
            client = self.hass.data[DOMAIN][self.config_entry.entry_id]["client"]

            # Resume the CronJob
            result = await client.resume_cronjob(self.cronjob_name, self.namespace)

            if result["success"]:
                self._last_resume_time = time.time()
                self._is_on = True
                self._suspend = False
                _LOGGER.info(
                    "Successfully resumed CronJob '%s'",
                    self.cronjob_name,
                )
            else:
                _LOGGER.error(
                    "Failed to resume CronJob '%s': %s",
                    self.cronjob_name,
                    result["error"],
                )
                raise Exception(result["error"])

        except Exception as ex:
            _LOGGER.error("Failed to resume CronJob %s: %s", self.cronjob_name, ex)
            raise

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Suspend the CronJob by setting suspend=true."""
        try:
            _LOGGER.info("Suspending CronJob: %s", self.cronjob_name)

            # Get the client from hass.data
            client = self.hass.data[DOMAIN][self.config_entry.entry_id]["client"]

            # Suspend the CronJob
            result = await client.suspend_cronjob(self.cronjob_name, self.namespace)

            if result["success"]:
                self._last_suspend_time = time.time()
                self._is_on = False
                self._suspend = True
                _LOGGER.info(
                    "Successfully suspended CronJob '%s'",
                    self.cronjob_name,
                )
            else:
                _LOGGER.error(
                    "Failed to suspend CronJob '%s': %s",
                    self.cronjob_name,
                    result["error"],
                )
                raise Exception(result["error"])

        except Exception as ex:
            _LOGGER.error("Failed to suspend CronJob %s: %s", self.cronjob_name, ex)
            raise

    async def async_update(self) -> None:
        """Update the switch state from coordinator data."""
        # Get data from coordinator
        cronjob_data = self.coordinator.get_cronjob_data(self.cronjob_name)

        if cronjob_data is None:
            _LOGGER.warning(
                "CronJob %s not found in coordinator data", self.cronjob_name
            )
            return

        old_state = self._is_on
        old_active_jobs = self._active_jobs_count

        # Update state based on CronJob data
        self._active_jobs_count = cronjob_data["active_jobs_count"]
        self._schedule = cronjob_data["schedule"]
        # Ensure suspend is always a boolean
        suspend_value = cronjob_data["suspend"]
        if suspend_value is True:
            self._suspend = True
        elif suspend_value is False:
            self._suspend = False
        elif isinstance(suspend_value, str):
            suspend_str = str(suspend_value).lower()
            is_true = suspend_str in ("true", "1", "yes", "on")
            self._suspend = is_true
        else:
            self._suspend = False

        # Handle schedule time fields with proper type conversion
        last_schedule_value = cronjob_data["last_schedule_time"]
        self._last_schedule_time = (
            str(last_schedule_value) if last_schedule_value is not None else None
        )

        next_schedule_value = cronjob_data["next_schedule_time"]
        self._next_schedule_time = (
            str(next_schedule_value) if next_schedule_value is not None else None
        )

        # Consider the CronJob "on" if it is not suspended (enabled)
        self._is_on = not self._suspend

        # Log state changes for debugging
        if old_active_jobs != self._active_jobs_count:
            _LOGGER.info(
                "CronJob %s active jobs changed: %d -> %d",
                self.cronjob_name,
                old_active_jobs,
                self._active_jobs_count,
            )
        if old_state != self._is_on:
            _LOGGER.info(
                "CronJob %s suspension state changed: %s -> %s (suspended=%s)",
                self.cronjob_name,
                old_state,
                self._is_on,
                self._suspend,
            )
        else:
            _LOGGER.debug(
                "CronJob %s state unchanged: suspended=%s, active_jobs=%d, schedule=%s",
                self.cronjob_name,
                self._suspend,
                self._active_jobs_count,
                self._schedule,
            )
