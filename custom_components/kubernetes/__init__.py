"""The Kubernetes integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .coordinator import KubernetesDataCoordinator
from .kubernetes_client import KubernetesClient
from .services import async_setup_services, async_unload_services


PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.SWITCH]

DOMAIN = "kubernetes"

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Kubernetes from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Check if kubernetes package is available before creating client
    try:
        import kubernetes.client
        _LOGGER.debug("Kubernetes package is available")
    except ImportError as e:
        _LOGGER.error("Kubernetes package not available: %s", e)
        return False

    # Create Kubernetes client
    client = KubernetesClient(entry.data)

    # Create and store the coordinator
    coordinator = KubernetesDataCoordinator(hass, entry, client)
    hass.data[DOMAIN][entry.entry_id] = {
        "config": entry.data,
        "client": client,
        "coordinator": coordinator,
    }

    # Set up services if this is the first config entry
    if len(hass.data[DOMAIN]) == 1:
        await async_setup_services(hass)

    # Start the coordinator
    await coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        # Clean up coordinator
        if entry.entry_id in hass.data[DOMAIN]:
            coordinator = hass.data[DOMAIN][entry.entry_id].get("coordinator")
            if coordinator:
                await coordinator.async_shutdown()

        hass.data[DOMAIN].pop(entry.entry_id)

        # Unload services if this was the last config entry
        if not hass.data[DOMAIN]:
            await async_unload_services(hass)

    return unload_ok
