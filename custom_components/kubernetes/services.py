"""Services for the Kubernetes integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
import voluptuous as vol

from .const import (
    ATTR_DEPLOYMENT_NAME,
    ATTR_STATEFULSET_NAME,
    ATTR_NAMESPACE,
    ATTR_REPLICAS,
    ATTR_DEPLOYMENT_NAMES,
    ATTR_STATEFULSET_NAMES,
    DOMAIN,
    SERVICE_SCALE_DEPLOYMENT,
    SERVICE_START_DEPLOYMENT,
    SERVICE_STOP_DEPLOYMENT,
    SERVICE_SCALE_STATEFULSET,
    SERVICE_START_STATEFULSET,
    SERVICE_STOP_STATEFULSET,
)

_LOGGER = logging.getLogger(__name__)


def _extract_deployment_names(call_data: dict[str, Any]) -> list[str]:
    """Extract deployment names from service call data, supporting both single and multiple selections."""
    if ATTR_DEPLOYMENT_NAMES in call_data:
        names = call_data[ATTR_DEPLOYMENT_NAMES]
        if isinstance(names, str):
            return [names]
        return names
    elif ATTR_DEPLOYMENT_NAME in call_data:
        name = call_data[ATTR_DEPLOYMENT_NAME]
        if isinstance(name, str):
            return [name]
        return name
    return []


def _extract_statefulset_names(call_data: dict[str, Any]) -> list[str]:
    """Extract StatefulSet names from service call data, supporting both single and multiple selections."""
    if ATTR_STATEFULSET_NAMES in call_data:
        names = call_data[ATTR_STATEFULSET_NAMES]
        if isinstance(names, str):
            return [names]
        return names
    elif ATTR_STATEFULSET_NAME in call_data:
        name = call_data[ATTR_STATEFULSET_NAME]
        if isinstance(name, str):
            return [name]
        return name
    return []


def _validate_deployment_names(deployment_names: list[str]) -> None:
    """Validate that at least one deployment name is provided."""
    if not deployment_names:
        raise vol.Invalid("Either deployment_name or deployment_names must be provided")


def _validate_statefulset_names(statefulset_names: list[str]) -> None:
    """Validate that at least one StatefulSet name is provided."""
    if not statefulset_names:
        raise vol.Invalid("Either statefulset_name or statefulset_names must be provided")


# Service schemas
SCALE_DEPLOYMENT_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_DEPLOYMENT_NAME): cv.string,
        vol.Optional(ATTR_DEPLOYMENT_NAMES): vol.Any(cv.string, vol.All(cv.ensure_list, [cv.string])),
        vol.Required(ATTR_REPLICAS): vol.All(vol.Coerce(int), vol.Range(min=0)),
        vol.Optional(ATTR_NAMESPACE): cv.string,
    }
)

START_DEPLOYMENT_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_DEPLOYMENT_NAME): cv.string,
        vol.Optional(ATTR_DEPLOYMENT_NAMES): vol.Any(cv.string, vol.All(cv.ensure_list, [cv.string])),
        vol.Optional(ATTR_REPLICAS, default=1): vol.All(vol.Coerce(int), vol.Range(min=1)),
        vol.Optional(ATTR_NAMESPACE): cv.string,
    }
)

STOP_DEPLOYMENT_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_DEPLOYMENT_NAME): cv.string,
        vol.Optional(ATTR_DEPLOYMENT_NAMES): vol.Any(cv.string, vol.All(cv.ensure_list, [cv.string])),
        vol.Optional(ATTR_NAMESPACE): cv.string,
    }
)

# StatefulSet service schemas
SCALE_STATEFULSET_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_STATEFULSET_NAME): cv.string,
        vol.Optional(ATTR_STATEFULSET_NAMES): vol.Any(cv.string, vol.All(cv.ensure_list, [cv.string])),
        vol.Required(ATTR_REPLICAS): vol.All(vol.Coerce(int), vol.Range(min=0)),
        vol.Optional(ATTR_NAMESPACE): cv.string,
    }
)

START_STATEFULSET_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_STATEFULSET_NAME): cv.string,
        vol.Optional(ATTR_STATEFULSET_NAMES): vol.Any(cv.string, vol.All(cv.ensure_list, [cv.string])),
        vol.Optional(ATTR_REPLICAS, default=1): vol.All(vol.Coerce(int), vol.Range(min=1)),
        vol.Optional(ATTR_NAMESPACE): cv.string,
    }
)

STOP_STATEFULSET_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_STATEFULSET_NAME): cv.string,
        vol.Optional(ATTR_STATEFULSET_NAMES): vol.Any(cv.string, vol.All(cv.ensure_list, [cv.string])),
        vol.Optional(ATTR_NAMESPACE): cv.string,
    }
)


async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up the Kubernetes services."""

    async def scale_deployment(call: ServiceCall) -> None:
        """Scale a deployment to the specified number of replicas."""
        deployment_names = _extract_deployment_names(call.data)
        _validate_deployment_names(deployment_names)
        replicas = call.data[ATTR_REPLICAS]
        namespace = call.data.get(ATTR_NAMESPACE)

        # Get the Kubernetes client from the first config entry
        kubernetes_data = hass.data.get(DOMAIN)
        if not kubernetes_data:
            _LOGGER.error("No Kubernetes integration configured")
            return

        # Use the first config entry (you might want to make this more sophisticated)
        config_entry_id = next(iter(kubernetes_data.keys()))
        config_data = kubernetes_data[config_entry_id]

        from .kubernetes_client import KubernetesClient
        client = KubernetesClient(config_data)

        for deployment_name in deployment_names:
            success = await client.scale_deployment(deployment_name, replicas, namespace)
            if success:
                _LOGGER.info("Successfully scaled deployment %s to %d replicas", deployment_name, replicas)
            else:
                _LOGGER.error("Failed to scale deployment %s", deployment_name)

        if len(deployment_names) > 1:
            _LOGGER.info("Completed scaling operation for %d deployments", len(deployment_names))

    async def start_deployment(call: ServiceCall) -> None:
        """Start a deployment by scaling it to the specified number of replicas."""
        deployment_names = _extract_deployment_names(call.data)
        _validate_deployment_names(deployment_names)
        replicas = call.data.get(ATTR_REPLICAS, 1)
        namespace = call.data.get(ATTR_NAMESPACE)

        # Get the Kubernetes client from the first config entry
        kubernetes_data = hass.data.get(DOMAIN)
        if not kubernetes_data:
            _LOGGER.error("No Kubernetes integration configured")
            return

        # Use the first config entry
        config_entry_id = next(iter(kubernetes_data.keys()))
        config_data = kubernetes_data[config_entry_id]

        from .kubernetes_client import KubernetesClient
        client = KubernetesClient(config_data)

        for deployment_name in deployment_names:
            success = await client.start_deployment(deployment_name, replicas, namespace)
            if success:
                _LOGGER.info("Successfully started deployment %s with %d replicas", deployment_name, replicas)
            else:
                _LOGGER.error("Failed to start deployment %s", deployment_name)

        if len(deployment_names) > 1:
            _LOGGER.info("Completed start operation for %d deployments", len(deployment_names))

    async def stop_deployment(call: ServiceCall) -> None:
        """Stop a deployment by scaling it to 0 replicas."""
        deployment_names = _extract_deployment_names(call.data)
        _validate_deployment_names(deployment_names)
        namespace = call.data.get(ATTR_NAMESPACE)

        # Get the Kubernetes client from the first config entry
        kubernetes_data = hass.data.get(DOMAIN)
        if not kubernetes_data:
            _LOGGER.error("No Kubernetes integration configured")
            return

        # Use the first config entry
        config_entry_id = next(iter(kubernetes_data.keys()))
        config_data = kubernetes_data[config_entry_id]

        from .kubernetes_client import KubernetesClient
        client = KubernetesClient(config_data)

        for deployment_name in deployment_names:
            success = await client.stop_deployment(deployment_name, namespace)
            if success:
                _LOGGER.info("Successfully stopped deployment %s", deployment_name)
            else:
                _LOGGER.error("Failed to stop deployment %s", deployment_name)

        if len(deployment_names) > 1:
            _LOGGER.info("Completed stop operation for %d deployments", len(deployment_names))

    # StatefulSet services
    async def scale_statefulset(call: ServiceCall) -> None:
        """Scale a StatefulSet to the specified number of replicas."""
        statefulset_names = _extract_statefulset_names(call.data)
        _validate_statefulset_names(statefulset_names)
        replicas = call.data[ATTR_REPLICAS]
        namespace = call.data.get(ATTR_NAMESPACE)

        # Get the Kubernetes client from the first config entry
        kubernetes_data = hass.data.get(DOMAIN)
        if not kubernetes_data:
            _LOGGER.error("No Kubernetes integration configured")
            return

        # Use the first config entry
        config_entry_id = next(iter(kubernetes_data.keys()))
        config_data = kubernetes_data[config_entry_id]

        from .kubernetes_client import KubernetesClient
        client = KubernetesClient(config_data)

        for statefulset_name in statefulset_names:
            success = await client.scale_statefulset(statefulset_name, replicas, namespace)
            if success:
                _LOGGER.info("Successfully scaled StatefulSet %s to %d replicas", statefulset_name, replicas)
            else:
                _LOGGER.error("Failed to scale StatefulSet %s", statefulset_name)

        if len(statefulset_names) > 1:
            _LOGGER.info("Completed scaling operation for %d StatefulSets", len(statefulset_names))

    async def start_statefulset(call: ServiceCall) -> None:
        """Start a StatefulSet by scaling it to the specified number of replicas."""
        statefulset_names = _extract_statefulset_names(call.data)
        _validate_statefulset_names(statefulset_names)
        replicas = call.data.get(ATTR_REPLICAS, 1)
        namespace = call.data.get(ATTR_NAMESPACE)

        # Get the Kubernetes client from the first config entry
        kubernetes_data = hass.data.get(DOMAIN)
        if not kubernetes_data:
            _LOGGER.error("No Kubernetes integration configured")
            return

        # Use the first config entry
        config_entry_id = next(iter(kubernetes_data.keys()))
        config_data = kubernetes_data[config_entry_id]

        from .kubernetes_client import KubernetesClient
        client = KubernetesClient(config_data)

        for statefulset_name in statefulset_names:
            success = await client.start_statefulset(statefulset_name, replicas, namespace)
            if success:
                _LOGGER.info("Successfully started StatefulSet %s with %d replicas", statefulset_name, replicas)
            else:
                _LOGGER.error("Failed to start StatefulSet %s", statefulset_name)

        if len(statefulset_names) > 1:
            _LOGGER.info("Completed start operation for %d StatefulSets", len(statefulset_names))

    async def stop_statefulset(call: ServiceCall) -> None:
        """Stop a StatefulSet by scaling it to 0 replicas."""
        statefulset_names = _extract_statefulset_names(call.data)
        _validate_statefulset_names(statefulset_names)
        namespace = call.data.get(ATTR_NAMESPACE)

        # Get the Kubernetes client from the first config entry
        kubernetes_data = hass.data.get(DOMAIN)
        if not kubernetes_data:
            _LOGGER.error("No Kubernetes integration configured")
            return

        # Use the first config entry
        config_entry_id = next(iter(kubernetes_data.keys()))
        config_data = kubernetes_data[config_entry_id]

        from .kubernetes_client import KubernetesClient
        client = KubernetesClient(config_data)

        for statefulset_name in statefulset_names:
            success = await client.stop_statefulset(statefulset_name, namespace)
            if success:
                _LOGGER.info("Successfully stopped StatefulSet %s", statefulset_name)
            else:
                _LOGGER.error("Failed to stop StatefulSet %s", statefulset_name)

        if len(statefulset_names) > 1:
            _LOGGER.info("Completed stop operation for %d StatefulSets", len(statefulset_names))

    # Register the services
    hass.services.async_register(
        DOMAIN,
        SERVICE_SCALE_DEPLOYMENT,
        scale_deployment,
        schema=SCALE_DEPLOYMENT_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_START_DEPLOYMENT,
        start_deployment,
        schema=START_DEPLOYMENT_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_STOP_DEPLOYMENT,
        stop_deployment,
        schema=STOP_DEPLOYMENT_SCHEMA,
    )

    # Register StatefulSet services
    hass.services.async_register(
        DOMAIN,
        SERVICE_SCALE_STATEFULSET,
        scale_statefulset,
        schema=SCALE_STATEFULSET_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_START_STATEFULSET,
        start_statefulset,
        schema=START_STATEFULSET_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_STOP_STATEFULSET,
        stop_statefulset,
        schema=STOP_STATEFULSET_SCHEMA,
    )


async def async_unload_services(hass: HomeAssistant) -> None:
    """Unload the Kubernetes services."""
    hass.services.async_remove(DOMAIN, SERVICE_SCALE_DEPLOYMENT)
    hass.services.async_remove(DOMAIN, SERVICE_START_DEPLOYMENT)
    hass.services.async_remove(DOMAIN, SERVICE_STOP_DEPLOYMENT)
    hass.services.async_remove(DOMAIN, SERVICE_SCALE_STATEFULSET)
    hass.services.async_remove(DOMAIN, SERVICE_START_STATEFULSET)
    hass.services.async_remove(DOMAIN, SERVICE_STOP_STATEFULSET)
