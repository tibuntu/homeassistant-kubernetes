"""Number platform for Kubernetes integration (replica count control)."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry

from .const import (
    ATTR_WORKLOAD_TYPE,
    WORKLOAD_TYPE_DEPLOYMENT,
    WORKLOAD_TYPE_STATEFULSET,
)
from .coordinator import (
    KubernetesConfigEntry,
    KubernetesDataCoordinator,
    disabled_resources,
)
from .device import get_namespace_device_info, get_or_create_namespace_device

_LOGGER = logging.getLogger(__name__)

# Data updates are centralized in the coordinator (quality scale: parallel-updates)
PARALLEL_UPDATES = 0

# workload type -> (coordinator bucket / disabled_resources key, client scale
# method, unique_id suffix shared with the switch and _build_expected_unique_ids)
_WORKLOADS = {
    WORKLOAD_TYPE_DEPLOYMENT: ("deployments", "scale_deployment", "deployment"),
    WORKLOAD_TYPE_STATEFULSET: ("statefulsets", "scale_statefulset", "statefulset"),
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: KubernetesConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Kubernetes replica number entities based on a config entry."""
    entry_data = config_entry.runtime_data
    coordinator = entry_data.coordinator
    entry_data.number_add_entities = async_add_entities

    # Built from the coordinator's first refresh — never from the client, whose
    # get_* methods raise and would fail the whole platform setup.
    await _async_add_new_entities(hass, config_entry, coordinator)

    @callback
    def _on_coordinator_update() -> None:
        hass.async_create_task(_async_add_new_entities(hass, config_entry, coordinator))

    config_entry.async_on_unload(coordinator.async_add_listener(_on_coordinator_update))


async def _async_add_new_entities(
    hass: HomeAssistant,
    config_entry: KubernetesConfigEntry,
    coordinator: KubernetesDataCoordinator,
) -> None:
    """Add number entities for workloads that do not have one yet."""
    entry_data = config_entry.runtime_data
    add_entities = entry_data.number_add_entities
    if not add_entities or not coordinator.data:
        return

    registry = async_get_entity_registry(hass)
    known = {
        entity.unique_id
        for entity in registry.entities.get_entries_for_config_entry_id(
            config_entry.entry_id
        )
    }
    pending = entry_data.number_pending_unique_ids
    # Prune IDs that are now in the registry — keeps the set bounded
    pending -= known
    known |= pending

    disabled = disabled_resources(config_entry)
    new_entities: list[KubernetesReplicaNumber] = []
    for workload_type, (bucket, _, _) in _WORKLOADS.items():
        if bucket in disabled:
            continue
        for workload in coordinator.data.get(bucket, {}).values():
            entity = KubernetesReplicaNumber(
                coordinator,
                config_entry,
                workload["name"],
                workload.get("namespace", "default"),
                workload_type,
            )
            if entity.unique_id in known:
                continue
            await get_or_create_namespace_device(hass, config_entry, entity.namespace)
            new_entities.append(entity)

    if new_entities:
        pending.update(e.unique_id for e in new_entities if e.unique_id)
        add_entities(new_entities)


class KubernetesReplicaNumber(NumberEntity):
    """Replica count of a Deployment or StatefulSet."""

    _attr_should_poll = False
    _attr_has_entity_name = True
    _attr_icon = "mdi:counter"
    _attr_mode = NumberMode.BOX
    _attr_native_min_value = 0
    # Fixed max; add an option if anyone needs more than 100 replicas
    _attr_native_max_value = 100
    _attr_native_step = 1

    def __init__(
        self,
        coordinator: KubernetesDataCoordinator,
        config_entry: KubernetesConfigEntry,
        workload_name: str,
        namespace: str,
        workload_type: str,
    ) -> None:
        """Initialize the replica number entity."""
        self.coordinator = coordinator
        self.config_entry = config_entry
        self.workload_name = workload_name
        self.namespace = namespace
        self._workload_type = workload_type
        self._bucket, self._scale_method, id_suffix = _WORKLOADS[workload_type]
        self._attr_name = f"{workload_name} replicas"
        # Same format as the matching switch, plus a "_replicas" suffix
        self._attr_unique_id = (
            f"{config_entry.entry_id}_{namespace}_{workload_name}_{id_suffix}_replicas"
        )

    def _workload_data(self) -> dict[str, Any] | None:
        """Return this workload's entry from coordinator data."""
        return (
            (self.coordinator.data or {})
            .get(self._bucket, {})
            .get(f"{self.namespace}_{self.workload_name}")
        )

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return get_namespace_device_info(self.hass, self.config_entry, self.namespace)

    @property
    def available(self) -> bool:
        """Return True if the coordinator's last refresh succeeded."""
        return self.coordinator.last_update_success

    @property
    def native_value(self) -> int | None:
        """Return the desired replica count."""
        data = self._workload_data()
        return data.get("replicas", 0) if data else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes."""
        data = self._workload_data() or {}
        return {
            "namespace": self.namespace,
            ATTR_WORKLOAD_TYPE: self._workload_type,
            "ready_replicas": data.get("ready_replicas", 0),
            "available_replicas": data.get("available_replicas", 0),
        }

    async def async_added_to_hass(self) -> None:
        """Subscribe to coordinator updates."""
        await super().async_added_to_hass()
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )

    async def async_set_native_value(self, value: float) -> None:
        """Scale the workload to the requested replica count."""
        replicas = int(value)
        scale = getattr(self.coordinator.client, self._scale_method)
        if not await scale(self.workload_name, replicas, namespace=self.namespace):
            raise HomeAssistantError(
                f"Failed to scale {self._workload_type} "
                f"{self.namespace}/{self.workload_name} to {replicas} replicas"
            )
        # replicas is spec.replicas, which the API just accepted — show it
        # now instead of waiting for the refresh/watch event to confirm it.
        # Written without _data_lock: there is no await between the lookup
        # and the write, so no poll or watch event can interleave.
        if data := self._workload_data():
            data["replicas"] = replicas
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()
