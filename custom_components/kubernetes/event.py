"""Kubernetes cluster event platform."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.event import EventEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_ENABLE_EVENTS,
    DEFAULT_ENABLE_EVENTS,
    EVENT_CURATED_REASONS,
    EVENT_TYPE_OTHER,
    event_signal,
)
from .device import get_cluster_device_info

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the cluster event entity (only when events are enabled)."""
    if not config_entry.options.get(CONF_ENABLE_EVENTS, DEFAULT_ENABLE_EVENTS):
        return
    async_add_entities([KubernetesClusterEventEntity(config_entry)])


class KubernetesClusterEventEntity(EventEntity):
    """Fires Home Assistant events for Kubernetes cluster events."""

    _attr_has_entity_name = True
    _attr_name = "Cluster events"
    _attr_event_types = [*EVENT_CURATED_REASONS, EVENT_TYPE_OTHER]

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize the cluster event entity."""
        self.config_entry = config_entry
        self._attr_unique_id = f"{config_entry.entry_id}_cluster_events"

    @property
    def device_info(self) -> DeviceInfo:
        """Attach to the cluster device."""
        return get_cluster_device_info(self.config_entry)

    async def async_added_to_hass(self) -> None:
        """Subscribe to dispatched cluster events."""
        await super().async_added_to_hass()
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                event_signal(self.config_entry.entry_id),
                self._handle_event,
            )
        )

    @callback
    def _handle_event(self, payload: dict[str, Any]) -> None:
        """Fire an HA event from a dispatched k8s event payload."""
        reason = payload.get("reason") or EVENT_TYPE_OTHER
        event_type = reason if reason in self._attr_event_types else EVENT_TYPE_OTHER
        self._trigger_event(event_type, payload)
        self.async_write_ha_state()
