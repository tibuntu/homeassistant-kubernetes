"""Services for the Kubernetes integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
import voluptuous as vol

from .const import (
    ATTR_DEPLOYMENT_NAME,
    ATTR_NAMESPACE,
    ATTR_REPLICAS,
    DOMAIN,
    SERVICE_SCALE_DEPLOYMENT,
    SERVICE_START_DEPLOYMENT,
    SERVICE_STOP_DEPLOYMENT,
)

_LOGGER = logging.getLogger(__name__)

# Service schemas
SCALE_DEPLOYMENT_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_DEPLOYMENT_NAME): cv.string,
        vol.Required(ATTR_REPLICAS): vol.All(vol.Coerce(int), vol.Range(min=0)),
        vol.Optional(ATTR_NAMESPACE): cv.string,
    }
)

START_DEPLOYMENT_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_DEPLOYMENT_NAME): cv.string,
        vol.Optional(ATTR_REPLICAS, default=1): vol.All(vol.Coerce(int), vol.Range(min=1)),
        vol.Optional(ATTR_NAMESPACE): cv.string,
    }
)

STOP_DEPLOYMENT_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_DEPLOYMENT_NAME): cv.string,
        vol.Optional(ATTR_NAMESPACE): cv.string,
    }
)


async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up the Kubernetes services."""

    async def scale_deployment(call: ServiceCall) -> None:
        """Scale a deployment to the specified number of replicas."""
        deployment_name = call.data[ATTR_DEPLOYMENT_NAME]
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

        success = await client.scale_deployment(deployment_name, replicas, namespace)
        if success:
            _LOGGER.info("Successfully scaled deployment %s to %d replicas", deployment_name, replicas)
        else:
            _LOGGER.error("Failed to scale deployment %s", deployment_name)

    async def start_deployment(call: ServiceCall) -> None:
        """Start a deployment by scaling it to the specified number of replicas."""
        deployment_name = call.data[ATTR_DEPLOYMENT_NAME]
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

        success = await client.start_deployment(deployment_name, replicas, namespace)
        if success:
            _LOGGER.info("Successfully started deployment %s with %d replicas", deployment_name, replicas)
        else:
            _LOGGER.error("Failed to start deployment %s", deployment_name)

    async def stop_deployment(call: ServiceCall) -> None:
        """Stop a deployment by scaling it to 0 replicas."""
        deployment_name = call.data[ATTR_DEPLOYMENT_NAME]
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

        success = await client.stop_deployment(deployment_name, namespace)
        if success:
            _LOGGER.info("Successfully stopped deployment %s", deployment_name)
        else:
            _LOGGER.error("Failed to stop deployment %s", deployment_name)

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


async def async_unload_services(hass: HomeAssistant) -> None:
    """Unload the Kubernetes services."""
    hass.services.async_remove(DOMAIN, SERVICE_SCALE_DEPLOYMENT)
    hass.services.async_remove(DOMAIN, SERVICE_START_DEPLOYMENT)
    hass.services.async_remove(DOMAIN, SERVICE_STOP_DEPLOYMENT)
