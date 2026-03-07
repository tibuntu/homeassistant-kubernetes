"""The Kubernetes integration."""

from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components.frontend import (
    async_register_built_in_panel,
    async_remove_panel,
)
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv

from .config_flow import KubernetesConfigFlow  # noqa: F401
from .const import (
    CONF_ENABLE_PANEL,
    CONF_ENABLE_WATCH,
    DEFAULT_ENABLE_PANEL,
    DEFAULT_ENABLE_WATCH,
    DOMAIN_META_KEYS,
    PANEL_FILENAME,
    PANEL_ICON,
    PANEL_TITLE,
    PANEL_URL,
)
from .coordinator import KubernetesDataCoordinator
from .kubernetes_client import KubernetesClient
from .services import async_setup_services, async_unload_services
from .websocket_api import async_register_websocket_commands

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.SWITCH]

DOMAIN = "kubernetes"

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Kubernetes integration."""
    async_register_websocket_commands(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Kubernetes from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Check if kubernetes package is available before creating client
    try:
        import kubernetes.client  # noqa: F401

        _LOGGER.debug("Kubernetes package is available")
    except ImportError as e:
        _LOGGER.error("Kubernetes package not available: %s", e)
        return False

    # Create Kubernetes client
    client = KubernetesClient(dict(entry.data))

    # Create and store the coordinator
    coordinator = KubernetesDataCoordinator(hass, entry, client)
    hass.data[DOMAIN][entry.entry_id] = {
        "config": entry.data,
        "client": client,
        "coordinator": coordinator,
    }

    # Set up services if this is the first config entry
    if _count_config_entries(hass) == 1:
        await async_setup_services(hass)

    # Register or remove the sidebar panel based on the enable_panel option
    await _async_sync_panel(hass, entry)

    # Start the coordinator
    await coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Start watch tasks after platforms are set up so that the first watch events
    # are delivered to already-registered entity listeners.
    if entry.options.get(CONF_ENABLE_WATCH, DEFAULT_ENABLE_WATCH):
        await coordinator.async_start_watch_tasks()

    # Reload the config entry when the user changes options so that the watch
    # tasks (or lack thereof) are correctly started/stopped.
    entry.async_on_unload(entry.add_update_listener(_async_update_options))

    return True


async def _async_sync_panel(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Register or remove the sidebar panel based on the enable_panel option."""
    panel_wanted = entry.options.get(CONF_ENABLE_PANEL, DEFAULT_ENABLE_PANEL)
    panel_registered = hass.data.get(DOMAIN, {}).get("panel_registered", False)

    if panel_wanted and not panel_registered:
        await _async_register_panel(hass)
    elif not panel_wanted and panel_registered:
        # Only remove if no other entry still wants the panel
        if not _any_entry_wants_panel(hass, exclude_entry_id=entry.entry_id):
            _async_remove_panel(hass)


def _any_entry_wants_panel(
    hass: HomeAssistant, exclude_entry_id: str | None = None
) -> bool:
    """Check if any config entry (except excluded) has the panel enabled."""
    domain_data = hass.data.get(DOMAIN, {})
    for entry_id, entry_data in domain_data.items():
        if entry_id in DOMAIN_META_KEYS or not isinstance(entry_data, dict):
            continue
        if entry_id == exclude_entry_id:
            continue
        coordinator = entry_data.get("coordinator")
        if coordinator is None:
            continue
        if coordinator.config_entry.options.get(
            CONF_ENABLE_PANEL, DEFAULT_ENABLE_PANEL
        ):
            return True
    return False


async def _async_register_panel(hass: HomeAssistant) -> None:
    """Register the Kubernetes sidebar panel."""
    if hass.data.get(DOMAIN, {}).get("panel_registered"):
        return

    panel_dir = Path(__file__).parent / "frontend"
    panel_js = panel_dir / PANEL_FILENAME

    if not panel_js.is_file():
        _LOGGER.warning(
            "Frontend panel file not found at %s; skipping panel registration",
            panel_js,
        )
        return

    # Static paths persist in HA's HTTP server across panel remove/register
    # cycles and across config entry reloads. Attempting to re-register the
    # same path raises, so we catch and ignore.
    try:
        await hass.http.async_register_static_paths(
            [StaticPathConfig(PANEL_URL, str(panel_dir), False)]
        )
    except Exception:  # noqa: BLE001
        _LOGGER.debug("Static path %s already registered, skipping", PANEL_URL)

    async_register_built_in_panel(
        hass,
        component_name="custom",
        sidebar_title=PANEL_TITLE,
        sidebar_icon=PANEL_ICON,
        frontend_url_path=DOMAIN,
        config={
            "_panel_custom": {
                "name": "kubernetes-panel",
                "embed_iframe": False,
                "trust_external": False,
                "module_url": f"{PANEL_URL}/{PANEL_FILENAME}",
            }
        },
        require_admin=False,
    )

    hass.data[DOMAIN]["panel_registered"] = True
    _LOGGER.info("Registered Kubernetes sidebar panel")


def _async_remove_panel(hass: HomeAssistant) -> None:
    """Remove the Kubernetes sidebar panel."""
    if not hass.data.get(DOMAIN, {}).get("panel_registered"):
        return
    async_remove_panel(hass, DOMAIN)
    hass.data[DOMAIN]["panel_registered"] = False
    _LOGGER.info("Removed Kubernetes sidebar panel")


async def _async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options updates by reloading the config entry."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    coordinator: KubernetesDataCoordinator = hass.data[DOMAIN][entry.entry_id][
        "coordinator"
    ]
    await coordinator.async_stop_watch_tasks()

    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

        # Clean up when the last config entry is removed
        if _count_config_entries(hass) == 0:
            _async_remove_panel(hass)
            await async_unload_services(hass)
            hass.data.pop(DOMAIN, None)
        elif not _any_entry_wants_panel(hass):
            # Remove panel if no remaining entries want it
            _async_remove_panel(hass)

    return unload_ok


def _count_config_entries(hass: HomeAssistant) -> int:
    """Count real config entry keys in hass.data[DOMAIN], excluding metadata."""
    domain_data = hass.data.get(DOMAIN, {})
    return sum(1 for k in domain_data if k not in DOMAIN_META_KEYS)
