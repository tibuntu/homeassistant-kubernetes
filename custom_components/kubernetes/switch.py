"""Switch platform for Kubernetes integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import DOMAIN, SWITCH_TYPE_DEPLOYMENT
from .kubernetes_client import KubernetesClient

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Kubernetes switches based on a config entry."""
    client = KubernetesClient(config_entry.data)

    # Get all deployments and create switches for them
    deployments = await client.get_deployments()

    switches = []
    for deployment in deployments:
        switches.append(
            KubernetesDeploymentSwitch(
                client,
                config_entry,
                deployment["name"],
                deployment["namespace"]
            )
        )

    async_add_entities(switches)


class KubernetesDeploymentSwitch(SwitchEntity):
    """Switch for controlling a Kubernetes deployment."""

    def __init__(
        self,
        client: KubernetesClient,
        config_entry: ConfigEntry,
        deployment_name: str,
        namespace: str
    ) -> None:
        """Initialize the deployment switch."""
        self.client = client
        self.config_entry = config_entry
        self.deployment_name = deployment_name
        self.namespace = namespace
        self._attr_has_entity_name = True
        self._attr_name = f"{deployment_name} Deployment"
        self._attr_unique_id = f"{config_entry.entry_id}_{deployment_name}_deployment"
        self._attr_icon = "mdi:kubernetes"
        self._is_on = False
        self._replicas = 0

    @property
    def is_on(self) -> bool:
        """Return true if the deployment is running (has replicas > 0)."""
        return self._is_on

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes."""
        return {
            "deployment_name": self.deployment_name,
            "namespace": self.namespace,
            "replicas": self._replicas,
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the deployment on by scaling to 1 replica."""
        success = await self.client.start_deployment(
            self.deployment_name,
            replicas=1,
            namespace=self.namespace
        )
        if success:
            self._is_on = True
            self._replicas = 1
            self.async_write_ha_state()
        else:
            _LOGGER.error("Failed to start deployment %s", self.deployment_name)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the deployment off by scaling to 0 replicas."""
        success = await self.client.stop_deployment(
            self.deployment_name,
            namespace=self.namespace
        )
        if success:
            self._is_on = False
            self._replicas = 0
            self.async_write_ha_state()
        else:
            _LOGGER.error("Failed to stop deployment %s", self.deployment_name)

    async def async_update(self) -> None:
        """Update the switch state."""
        try:
            deployments = await self.client.get_deployments()
            for deployment in deployments:
                if deployment["name"] == self.deployment_name:
                    self._replicas = deployment["replicas"]
                    self._is_on = deployment["is_running"]
                    break
        except Exception as ex:
            _LOGGER.error("Failed to update deployment switch %s: %s", self.deployment_name, ex)
