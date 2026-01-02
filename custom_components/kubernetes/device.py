"""Device registry management for Kubernetes integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity import DeviceInfo

from .const import (
    CONF_CLUSTER_NAME,
    CONF_DEVICE_GROUPING_MODE,
    DEFAULT_CLUSTER_NAME,
    DEFAULT_DEVICE_GROUPING_MODE,
    DEVICE_GROUPING_MODE_CLUSTER,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


def get_cluster_device_identifier(config_entry: ConfigEntry) -> str:
    """Get the device identifier for the cluster device."""
    return f"{config_entry.entry_id}_cluster"


def get_namespace_device_identifier(config_entry: ConfigEntry, namespace: str) -> str:
    """Get the device identifier for a namespace device."""
    return f"{config_entry.entry_id}_namespace_{namespace}"


async def get_or_create_cluster_device(
    hass: HomeAssistant, config_entry: ConfigEntry
) -> dr.DeviceEntry:
    """Get or create the cluster device."""
    device_registry = dr.async_get(hass)
    cluster_name = config_entry.data.get(CONF_CLUSTER_NAME, DEFAULT_CLUSTER_NAME)
    device_identifier = get_cluster_device_identifier(config_entry)

    # Check if device already exists
    device = device_registry.async_get_device(identifiers={(DOMAIN, device_identifier)})

    if device:
        _LOGGER.debug("Cluster device already exists: %s", device.name)
        return device

    # Create new cluster device
    device = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={(DOMAIN, device_identifier)},
        name=cluster_name,
        manufacturer="Kubernetes",
        model="Cluster",
        sw_version=None,
    )

    _LOGGER.info(
        "Created cluster device: %s (identifier: %s)", device.name, device_identifier
    )
    return device


async def get_or_create_namespace_device(
    hass: HomeAssistant, config_entry: ConfigEntry, namespace: str
) -> dr.DeviceEntry | None:
    """Get or create a namespace device, or return None if in cluster mode."""
    # In cluster mode, no namespace devices are created
    grouping_mode = config_entry.data.get(
        CONF_DEVICE_GROUPING_MODE, DEFAULT_DEVICE_GROUPING_MODE
    )
    if grouping_mode == DEVICE_GROUPING_MODE_CLUSTER:
        return None

    device_registry = dr.async_get(hass)
    cluster_name = config_entry.data.get(CONF_CLUSTER_NAME, DEFAULT_CLUSTER_NAME)
    device_identifier = get_namespace_device_identifier(config_entry, namespace)

    # Check if device already exists
    device = device_registry.async_get_device(identifiers={(DOMAIN, device_identifier)})

    if device:
        _LOGGER.debug("Namespace device already exists: %s", device.name)
        return device

    # Get or create cluster device first (parent)
    cluster_device = await get_or_create_cluster_device(hass, config_entry)

    # Create new namespace device
    device = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={(DOMAIN, device_identifier)},
        name=f"{cluster_name}: {namespace}",
        manufacturer="Kubernetes",
        model="Namespace",
        sw_version=None,
        via_device=(DOMAIN, get_cluster_device_identifier(config_entry)),
    )

    _LOGGER.info(
        "Created namespace device: %s (identifier: %s, parent: %s)",
        device.name,
        device_identifier,
        cluster_device.name,
    )
    return device


def get_cluster_device_info(config_entry: ConfigEntry) -> DeviceInfo:
    """Get device info for cluster device."""
    device_identifier = get_cluster_device_identifier(config_entry)
    return DeviceInfo(
        identifiers={(DOMAIN, device_identifier)},
        name=config_entry.data.get(CONF_CLUSTER_NAME, DEFAULT_CLUSTER_NAME),
        manufacturer="Kubernetes",
        model="Cluster",
    )


def get_namespace_device_info(config_entry: ConfigEntry, namespace: str) -> DeviceInfo:
    """Get device info for namespace device or cluster device based on grouping mode."""
    grouping_mode = config_entry.data.get(
        CONF_DEVICE_GROUPING_MODE, DEFAULT_DEVICE_GROUPING_MODE
    )

    # In cluster mode, all entities use the cluster device
    if grouping_mode == DEVICE_GROUPING_MODE_CLUSTER:
        return get_cluster_device_info(config_entry)

    # In namespace mode, use namespace devices
    device_identifier = get_namespace_device_identifier(config_entry, namespace)
    cluster_name = config_entry.data.get(CONF_CLUSTER_NAME, DEFAULT_CLUSTER_NAME)
    return DeviceInfo(
        identifiers={(DOMAIN, device_identifier)},
        name=f"{cluster_name}: {namespace}",
        manufacturer="Kubernetes",
        model="Namespace",
        via_device=(DOMAIN, get_cluster_device_identifier(config_entry)),
    )


def _extract_namespaces_from_resources(
    resources: dict[str, dict[str, Any]] | None, namespaces: set[str]
) -> None:
    """Extract namespaces from a resource dictionary and add to the set."""
    if not resources:
        return
    for resource_data in resources.values():
        namespace = resource_data.get("namespace")
        if namespace:
            namespaces.add(namespace)


def get_all_namespaces(coordinator_data: dict[str, Any] | None) -> set[str]:
    """Extract all unique namespaces from coordinator data."""
    namespaces: set[str] = set()

    if not coordinator_data:
        return namespaces

    # Resource types to check for namespaces
    resource_types = ["pods", "deployments", "statefulsets", "cronjobs", "daemonsets"]

    for resource_type in resource_types:
        if resource_type in coordinator_data:
            _extract_namespaces_from_resources(
                coordinator_data[resource_type], namespaces
            )

    return namespaces


async def cleanup_orphaned_namespace_devices(
    hass: HomeAssistant, config_entry: ConfigEntry, current_namespaces: set[str]
) -> None:
    """Remove namespace devices for namespaces that no longer exist."""
    # Only cleanup namespace devices if in namespace grouping mode
    grouping_mode = config_entry.data.get(
        CONF_DEVICE_GROUPING_MODE, DEFAULT_DEVICE_GROUPING_MODE
    )
    if grouping_mode == DEVICE_GROUPING_MODE_CLUSTER:
        # No namespace devices to clean up in cluster mode
        return

    device_registry = dr.async_get(hass)
    entry_id = config_entry.entry_id

    # Get all devices for this config entry
    devices = dr.async_entries_for_config_entry(device_registry, entry_id)

    # Find namespace devices that should be removed
    devices_to_remove = []
    for device in devices:
        # Check if this is a namespace device
        if not device.identifiers:
            continue

        for identifier in device.identifiers:
            if identifier[0] == DOMAIN and identifier[1].startswith(
                f"{entry_id}_namespace_"
            ):
                # Extract namespace from identifier
                namespace = identifier[1].replace(f"{entry_id}_namespace_", "", 1)
                if namespace not in current_namespaces:
                    devices_to_remove.append(device)
                    _LOGGER.info(
                        "Namespace %s no longer exists, marking device for removal: %s",
                        namespace,
                        device.name,
                    )
                break

    # Remove orphaned devices
    for device in devices_to_remove:
        _LOGGER.info("Removing orphaned namespace device: %s", device.name)
        device_registry.async_remove_device(device.id)

    if devices_to_remove:
        _LOGGER.info("Removed %d orphaned namespace devices", len(devices_to_remove))
    else:
        _LOGGER.debug("No orphaned namespace devices found")
