"""Switch platform for Kubernetes integration."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry

from .const import (
    ATTR_WORKLOAD_TYPE,
    CONF_SCALE_COOLDOWN,
    CONF_SCALE_VERIFICATION_TIMEOUT,
    DEFAULT_SCALE_COOLDOWN,
    DEFAULT_SCALE_VERIFICATION_TIMEOUT,
    DOMAIN,
    WORKLOAD_TYPE_DEPLOYMENT,
    WORKLOAD_TYPE_STATEFULSET,
)
from .coordinator import KubernetesDataCoordinator

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

    # Store the add_entities callback for dynamic entity management
    switches = []

    # Get all deployments and create switches for them
    deployments = await client.get_deployments()
    for deployment in deployments:
        switches.append(
            KubernetesDeploymentSwitch(
                coordinator, config_entry, deployment["name"], deployment["namespace"]
            )
        )

    # Get all StatefulSets and create switches for them
    statefulsets = await client.get_statefulsets()
    for statefulset in statefulsets:
        switches.append(
            KubernetesStatefulSetSwitch(
                coordinator, config_entry, statefulset["name"], statefulset["namespace"]
            )
        )

    async_add_entities(switches)

    # Store the add_entities callback for dynamic entity management
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    hass.data[DOMAIN]["switch_add_entities"] = async_add_entities

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

        # Get existing entities for this config entry
        existing_entities = entity_registry.entities.get_entries_for_config_entry_id(
            config_entry.entry_id
        )
        existing_unique_ids = {
            entity.unique_id for entity in existing_entities if entity.unique_id
        }

        new_entities = []

        # Check for new deployments
        if coordinator.data and "deployments" in coordinator.data:
            for deployment_name, deployment_data in coordinator.data[
                "deployments"
            ].items():
                unique_id = f"{config_entry.entry_id}_{deployment_name}_deployment"
                if unique_id not in existing_unique_ids:
                    _LOGGER.info(
                        "Adding new entity for deployment: %s", deployment_name
                    )
                    new_entities.append(
                        KubernetesDeploymentSwitch(
                            coordinator,
                            config_entry,
                            deployment_name,
                            deployment_data.get("namespace", "default"),
                        )
                    )

        # Check for new StatefulSets
        if coordinator.data and "statefulsets" in coordinator.data:
            for statefulset_name, statefulset_data in coordinator.data[
                "statefulsets"
            ].items():
                unique_id = f"{config_entry.entry_id}_{statefulset_name}_statefulset"
                if unique_id not in existing_unique_ids:
                    _LOGGER.info(
                        "Adding new entity for StatefulSet: %s", statefulset_name
                    )
                    new_entities.append(
                        KubernetesStatefulSetSwitch(
                            coordinator,
                            config_entry,
                            statefulset_name,
                            statefulset_data.get("namespace", "default"),
                        )
                    )

        # Add new entities if any were found
        if new_entities:
            _LOGGER.info("Adding %d new entities", len(new_entities))
            add_entities_callback(new_entities)
        else:
            _LOGGER.debug("No new entities to add")

    except Exception as ex:
        _LOGGER.error("Failed to discover and add new entities: %s", ex)


class KubernetesDeploymentSwitch(SwitchEntity):
    """Switch for controlling a Kubernetes deployment."""

    def __init__(
        self,
        coordinator: KubernetesDataCoordinator,
        config_entry: ConfigEntry,
        deployment_name: str,
        namespace: str,
    ) -> None:
        """Initialize the deployment switch."""
        self.coordinator = coordinator
        self.config_entry = config_entry
        self.deployment_name = deployment_name
        self.namespace = namespace
        self._attr_has_entity_name = True
        self._attr_name = deployment_name
        self._attr_unique_id = f"{config_entry.entry_id}_{deployment_name}_deployment"
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
            ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_DEPLOYMENT,
            "last_scale_attempt_failed": self._last_scale_attempt_failed,
        }

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.last_update_success

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the deployment on by scaling to 1 replica."""
        _LOGGER.info("Scaling deployment %s to 1 replica", self.deployment_name)

        # Get the client from the coordinator's config entry
        client = self.coordinator.client

        success = await client.start_deployment(
            self.deployment_name, replicas=1, namespace=self.namespace
        )

        if success:
            # Set optimistic state immediately
            self._is_on = True
            self._replicas = 1
            self._last_scale_time = time.time()
            self._last_scale_attempt_failed = False
            self.async_write_ha_state()
            _LOGGER.info(
                "Successfully scaled deployment %s to 1 replica", self.deployment_name
            )

            # Verify the scaling actually took effect
            await self._verify_scaling(1)
        else:
            _LOGGER.error("Failed to start deployment %s", self.deployment_name)
            self._last_scale_attempt_failed = True
            self.async_write_ha_state()

            # Force an immediate update to get the actual state
            await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the deployment off by scaling to 0 replicas."""
        _LOGGER.info("Scaling deployment %s to 0 replicas", self.deployment_name)

        # Get the client from the coordinator's config entry
        client = self.coordinator.client

        success = await client.stop_deployment(
            self.deployment_name, namespace=self.namespace
        )

        if success:
            # Set optimistic state immediately
            self._is_on = False
            self._replicas = 0
            self._last_scale_time = time.time()
            self._last_scale_attempt_failed = False
            self.async_write_ha_state()
            _LOGGER.info(
                "Successfully scaled deployment %s to 0 replicas", self.deployment_name
            )

            # Verify the scaling actually took effect
            await self._verify_scaling(0)
        else:
            _LOGGER.error("Failed to stop deployment %s", self.deployment_name)
            self._last_scale_attempt_failed = True
            self.async_write_ha_state()

            # Force an immediate update to get the actual state
            await self.coordinator.async_request_refresh()

    async def async_update(self) -> None:
        """Update the switch state from coordinator data."""
        # Don't update state immediately after scaling to allow Kubernetes time to propagate changes
        if time.time() - self._last_scale_time < self._scale_cooldown:
            _LOGGER.debug(
                "Skipping state update for %s (scaled recently, cooldown: %.1fs remaining)",
                self.deployment_name,
                self._scale_cooldown - (time.time() - self._last_scale_time),
            )
            return

        # Get data from coordinator
        deployment_data = self.coordinator.get_deployment_data(self.deployment_name)

        if deployment_data is None:
            _LOGGER.warning(
                "Deployment %s not found in coordinator data", self.deployment_name
            )
            return

        old_replicas = self._replicas
        old_state = self._is_on

        self._replicas = deployment_data["replicas"]
        self._is_on = deployment_data["is_running"]

        # Log state changes for debugging
        if old_replicas != self._replicas:
            _LOGGER.info(
                "Deployment %s replicas changed: %d -> %d",
                self.deployment_name,
                old_replicas,
                self._replicas,
            )
        if old_state != self._is_on:
            _LOGGER.info(
                "Deployment %s state changed: %s -> %s",
                self.deployment_name,
                old_state,
                self._is_on,
            )
        else:
            _LOGGER.debug(
                "Deployment %s state unchanged: replicas=%d, is_running=%s",
                self.deployment_name,
                self._replicas,
                self._is_on,
            )

    async def _verify_scaling(self, target_replicas: int) -> None:
        """Verify that scaling actually took effect."""
        max_attempts = self._scale_verification_timeout // 5  # Try every 5 seconds
        for attempt in range(max_attempts):
            await asyncio.sleep(5)  # Wait 5 seconds between checks

            try:
                # Force a coordinator refresh to get latest data
                await self.coordinator.async_request_refresh()

                deployment_data = self.coordinator.get_deployment_data(
                    self.deployment_name
                )
                if deployment_data is None:
                    _LOGGER.warning(
                        "Deployment %s not found during scaling verification",
                        self.deployment_name,
                    )
                    continue

                current_replicas = deployment_data["replicas"]
                if current_replicas == target_replicas:
                    _LOGGER.info(
                        "Deployment %s scaling verified: %d replicas",
                        self.deployment_name,
                        current_replicas,
                    )
                    return
                else:
                    _LOGGER.debug(
                        "Deployment %s still scaling: %d replicas (target: %d)",
                        self.deployment_name,
                        current_replicas,
                        target_replicas,
                    )
            except Exception as ex:
                _LOGGER.warning(
                    "Failed to verify scaling for %s (attempt %d): %s",
                    self.deployment_name,
                    attempt + 1,
                    ex,
                )

        _LOGGER.warning(
            "Deployment %s scaling verification timed out after %d attempts",
            self.deployment_name,
            max_attempts,
        )


class KubernetesStatefulSetSwitch(SwitchEntity):
    """Switch for controlling a Kubernetes StatefulSet."""

    def __init__(
        self,
        coordinator: KubernetesDataCoordinator,
        config_entry: ConfigEntry,
        statefulset_name: str,
        namespace: str,
    ) -> None:
        """Initialize the StatefulSet switch."""
        self.coordinator = coordinator
        self.config_entry = config_entry
        self.statefulset_name = statefulset_name
        self.namespace = namespace
        self._attr_has_entity_name = True
        self._attr_name = statefulset_name
        self._attr_unique_id = f"{config_entry.entry_id}_{statefulset_name}_statefulset"
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

    @property
    def is_on(self) -> bool:
        """Return true if the StatefulSet is running (has replicas > 0)."""
        return self._is_on

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes."""
        return {
            "statefulset_name": self.statefulset_name,
            "namespace": self.namespace,
            "replicas": self._replicas,
            ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_STATEFULSET,
            "last_scale_attempt_failed": self._last_scale_attempt_failed,
        }

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.last_update_success

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the StatefulSet on by scaling to 1 replica."""
        _LOGGER.info("Scaling StatefulSet %s to 1 replica", self.statefulset_name)

        # Get the client from the coordinator's config entry
        client = self.coordinator.client

        success = await client.start_statefulset(
            self.statefulset_name, replicas=1, namespace=self.namespace
        )

        if success:
            # Set optimistic state immediately
            self._is_on = True
            self._replicas = 1
            self._last_scale_time = time.time()
            self._last_scale_attempt_failed = False
            self.async_write_ha_state()
            _LOGGER.info(
                "Successfully scaled StatefulSet %s to 1 replica", self.statefulset_name
            )

            # Verify the scaling actually took effect
            await self._verify_scaling(1)
        else:
            _LOGGER.error("Failed to start StatefulSet %s", self.statefulset_name)
            self._last_scale_attempt_failed = True
            self.async_write_ha_state()

            # Force an immediate update to get the actual state
            await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the StatefulSet off by scaling to 0 replicas."""
        _LOGGER.info("Scaling StatefulSet %s to 0 replicas", self.statefulset_name)

        # Get the client from the coordinator's config entry
        client = self.coordinator.client

        success = await client.stop_statefulset(
            self.statefulset_name, namespace=self.namespace
        )

        if success:
            # Set optimistic state immediately
            self._is_on = False
            self._replicas = 0
            self._last_scale_time = time.time()
            self._last_scale_attempt_failed = False
            self.async_write_ha_state()
            _LOGGER.info(
                "Successfully scaled StatefulSet %s to 0 replicas",
                self.statefulset_name,
            )

            # Verify the scaling actually took effect
            await self._verify_scaling(0)
        else:
            _LOGGER.error("Failed to stop StatefulSet %s", self.statefulset_name)
            self._last_scale_attempt_failed = True
            self.async_write_ha_state()

            # Force an immediate update to get the actual state
            await self.coordinator.async_request_refresh()

    async def async_update(self) -> None:
        """Update the switch state from coordinator data."""
        # Don't update state immediately after scaling to allow Kubernetes time to propagate changes
        if time.time() - self._last_scale_time < self._scale_cooldown:
            _LOGGER.debug(
                "Skipping state update for %s (scaled recently, cooldown: %.1fs remaining)",
                self.statefulset_name,
                self._scale_cooldown - (time.time() - self._last_scale_time),
            )
            return

        # Get data from coordinator
        statefulset_data = self.coordinator.get_statefulset_data(self.statefulset_name)

        if statefulset_data is None:
            _LOGGER.warning(
                "StatefulSet %s not found in coordinator data", self.statefulset_name
            )
            return

        old_replicas = self._replicas
        old_state = self._is_on

        self._replicas = statefulset_data["replicas"]
        self._is_on = statefulset_data["is_running"]

        # Log state changes for debugging
        if old_replicas != self._replicas:
            _LOGGER.info(
                "StatefulSet %s replicas changed: %d -> %d",
                self.statefulset_name,
                old_replicas,
                self._replicas,
            )
        if old_state != self._is_on:
            _LOGGER.info(
                "StatefulSet %s state changed: %s -> %s",
                self.statefulset_name,
                old_state,
                self._is_on,
            )
        else:
            _LOGGER.debug(
                "StatefulSet %s state unchanged: replicas=%d, is_running=%s",
                self.statefulset_name,
                self._replicas,
                self._is_on,
            )

    async def _verify_scaling(self, target_replicas: int) -> None:
        """Verify that scaling actually took effect."""
        max_attempts = self._scale_verification_timeout // 5  # Try every 5 seconds
        for attempt in range(max_attempts):
            await asyncio.sleep(5)  # Wait 5 seconds between checks

            try:
                # Force a coordinator refresh to get latest data
                await self.coordinator.async_request_refresh()

                statefulset_data = self.coordinator.get_statefulset_data(
                    self.statefulset_name
                )
                if statefulset_data is None:
                    _LOGGER.warning(
                        "StatefulSet %s not found during scaling verification",
                        self.statefulset_name,
                    )
                    continue

                current_replicas = statefulset_data["replicas"]
                if current_replicas == target_replicas:
                    _LOGGER.info(
                        "StatefulSet %s scaling verified: %d replicas",
                        self.statefulset_name,
                        current_replicas,
                    )
                    return
                else:
                    _LOGGER.debug(
                        "StatefulSet %s still scaling: %d replicas (target: %d)",
                        self.statefulset_name,
                        current_replicas,
                        target_replicas,
                    )
            except Exception as ex:
                _LOGGER.warning(
                    "Failed to verify scaling for %s (attempt %d): %s",
                    self.statefulset_name,
                    attempt + 1,
                    ex,
                )

        _LOGGER.warning(
            "StatefulSet %s scaling verification timed out after %d attempts",
            self.statefulset_name,
            max_attempts,
        )
