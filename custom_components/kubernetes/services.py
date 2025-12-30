"""Services for the Kubernetes integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
import voluptuous as vol

from .const import (
    ATTR_NAMESPACE,
    ATTR_REPLICAS,
    ATTR_WORKLOAD_NAME,
    ATTR_WORKLOAD_NAMES,
    ATTR_WORKLOAD_TYPE,
    DOMAIN,
    SERVICE_SCALE_WORKLOAD,
    SERVICE_START_WORKLOAD,
    SERVICE_STOP_WORKLOAD,
    WORKLOAD_TYPE_CRONJOB,
    WORKLOAD_TYPE_DEPLOYMENT,
    WORKLOAD_TYPE_STATEFULSET,
)

_LOGGER = logging.getLogger(__name__)
_LOGGER.info("Kubernetes services module loaded")


def _validate_entity_workload_type(
    hass: HomeAssistant, entity_id_or_name: str, expected_workload_type: str
) -> bool:
    """Validate that an entity represents the expected workload type."""
    try:
        # Only validate if this looks like an entity ID (starts with switch.)
        # If it's a direct resource name, skip validation (for backward compatibility)
        if not entity_id_or_name.startswith("switch."):
            _LOGGER.debug(
                "Skipping workload type validation for direct resource name: %s",
                entity_id_or_name,
            )
            return True

        # If it's already an entity ID, use it directly
        entity_id = entity_id_or_name

        entity = hass.states.get(entity_id)
        if entity and entity.attributes:
            workload_type = entity.attributes.get(ATTR_WORKLOAD_TYPE)
            if workload_type == expected_workload_type:
                _LOGGER.debug(
                    "Entity %s has correct workload type: %s", entity_id, workload_type
                )
                return True
            else:
                _LOGGER.warning(
                    "Entity %s has workload type %s, expected %s",
                    entity_id,
                    workload_type,
                    expected_workload_type,
                )
                return False
        else:
            _LOGGER.debug("Entity %s not found or has no attributes", entity_id)
            return False
    except Exception as e:
        _LOGGER.debug(
            "Error validating workload type for entity %s: %s", entity_id_or_name, e
        )
        return False


def _get_workload_info_from_entity(
    hass: HomeAssistant, entity_id_or_name: str
) -> tuple[str | None, str | None, str | None]:
    """Get namespace, workload name, and workload type from entity attributes.

    Returns:
        Tuple of (namespace, workload_name, workload_type)
    """
    try:
        # If it's already an entity ID, use it directly
        if entity_id_or_name.startswith("switch."):
            entity_id = entity_id_or_name
        else:
            # Try to find the entity by name
            entity_id = f"switch.{entity_id_or_name}"

        entity = hass.states.get(entity_id)
        if entity and entity.attributes:
            namespace = entity.attributes.get("namespace")
            workload_type = entity.attributes.get(ATTR_WORKLOAD_TYPE)
            deployment_name = entity.attributes.get("deployment_name")
            statefulset_name = entity.attributes.get("statefulset_name")
            cronjob_name = entity.attributes.get("cronjob_name")
            workload_name = deployment_name or statefulset_name or cronjob_name

            _LOGGER.debug(
                "Found namespace %s, workload_name %s, workload_type %s for entity %s",
                namespace,
                workload_name,
                workload_type,
                entity_id,
            )
            return namespace, workload_name, workload_type
        else:
            _LOGGER.debug("Entity %s not found or has no attributes", entity_id)
            return None, None, None
    except Exception as e:
        _LOGGER.debug(
            "Error getting workload info for entity %s: %s", entity_id_or_name, e
        )
        return None, None, None


def _extract_workload_info(  # noqa: C901
    call_data: dict[str, Any], hass: HomeAssistant
) -> list[tuple[str, str | None, str]]:
    """Extract workload information (name, namespace, workload_type) from service call data.

    Returns:
        List of tuples: [(workload_name, namespace, workload_type), ...]
    """
    workloads: list[tuple[str, str | None, str]] = []

    _LOGGER.debug("Extracting workload info from call data: %s", call_data)

    # Check for workload_names (multi-select)
    if ATTR_WORKLOAD_NAMES in call_data:
        names = call_data[ATTR_WORKLOAD_NAMES]
        _LOGGER.debug("Found workload_names: %s (type: %s)", names, type(names))

        if isinstance(names, str):
            # Single entity ID as string
            namespace, workload_name, workload_type = _get_workload_info_from_entity(
                hass, names
            )
            if workload_name and workload_type:
                workloads.append((workload_name, namespace, workload_type))
            else:
                _LOGGER.warning(
                    "Failed to extract workload info from entity %s: namespace=%s, workload_name=%s, workload_type=%s",
                    names,
                    namespace,
                    workload_name,
                    workload_type,
                )
        elif isinstance(names, dict) and "entity_id" in names:
            # Home Assistant UI format: {'entity_id': ['switch.entity1', 'switch.entity2']}
            entity_ids = names["entity_id"]
            if isinstance(entity_ids, list):
                for entity_id in entity_ids:
                    if isinstance(entity_id, str) and entity_id.startswith("switch."):
                        namespace, workload_name, workload_type = (
                            _get_workload_info_from_entity(hass, entity_id)
                        )
                        if workload_name and workload_type:
                            workloads.append((workload_name, namespace, workload_type))
                        else:
                            _LOGGER.warning(
                                "Failed to extract workload info from entity %s: namespace=%s, workload_name=%s, workload_type=%s",
                                entity_id,
                                namespace,
                                workload_name,
                                workload_type,
                            )
        elif isinstance(names, list):
            # List of entity IDs or names
            for name in names:
                if isinstance(name, str):
                    namespace, workload_name, workload_type = (
                        _get_workload_info_from_entity(hass, name)
                    )
                    if workload_name and workload_type:
                        workloads.append((workload_name, namespace, workload_type))

    # Check for workload_name (single select)
    if ATTR_WORKLOAD_NAME in call_data:
        name = call_data[ATTR_WORKLOAD_NAME]
        _LOGGER.debug("Found workload_name: %s (type: %s)", name, type(name))

        if isinstance(name, str):
            namespace, workload_name, workload_type = _get_workload_info_from_entity(
                hass, name
            )
            if workload_name and workload_type:
                workloads.append((workload_name, namespace, workload_type))
            else:
                _LOGGER.warning(
                    "Failed to extract workload info from entity %s: namespace=%s, workload_name=%s, workload_type=%s",
                    name,
                    namespace,
                    workload_name,
                    workload_type,
                )
        elif isinstance(name, dict) and "entity_id" in name:
            entity_id = name["entity_id"]
            if isinstance(entity_id, str) and entity_id.startswith("switch."):
                namespace, workload_name, workload_type = (
                    _get_workload_info_from_entity(hass, entity_id)
                )
                if workload_name and workload_type:
                    workloads.append((workload_name, namespace, workload_type))

    # Use provided namespace if available
    provided_namespace = call_data.get(ATTR_NAMESPACE)
    if provided_namespace:
        _LOGGER.debug(
            "Using provided namespace: %s for all workloads", provided_namespace
        )
        workloads = [(name, provided_namespace, wtype) for name, _, wtype in workloads]

    _LOGGER.debug("Extracted workloads: %s", workloads)
    return workloads


def _validate_workload_schema(data: dict) -> dict:
    """Validate that at least one workload field is provided."""
    if ATTR_WORKLOAD_NAME not in data and ATTR_WORKLOAD_NAMES not in data:
        raise vol.Invalid("Either workload_name or workload_names must be provided")
    return data


# Generic service schemas
SCALE_WORKLOAD_SCHEMA = vol.Schema(
    vol.All(
        {
            vol.Optional(ATTR_WORKLOAD_NAME): vol.Any(cv.string, dict),
            vol.Optional(ATTR_WORKLOAD_NAMES): vol.Any(
                cv.string,
                vol.All(cv.ensure_list, [vol.Any(cv.string, dict)]),
                vol.All(cv.ensure_list, [cv.string]),
                dict,
            ),
            vol.Required(ATTR_REPLICAS): vol.All(vol.Coerce(int), vol.Range(min=0)),
            vol.Optional(ATTR_NAMESPACE): cv.string,
        },
        _validate_workload_schema,
    )
)

START_WORKLOAD_SCHEMA = vol.Schema(
    vol.All(
        {
            vol.Optional(ATTR_WORKLOAD_NAME): vol.Any(cv.string, dict),
            vol.Optional(ATTR_WORKLOAD_NAMES): vol.Any(
                cv.string,
                vol.All(cv.ensure_list, [vol.Any(cv.string, dict)]),
                vol.All(cv.ensure_list, [cv.string]),
                dict,
            ),
            vol.Optional(ATTR_REPLICAS, default=1): vol.All(
                vol.Coerce(int), vol.Range(min=1)
            ),
            vol.Optional(ATTR_NAMESPACE): cv.string,
        },
        _validate_workload_schema,
    )
)

STOP_WORKLOAD_SCHEMA = vol.Schema(
    vol.All(
        {
            vol.Optional(ATTR_WORKLOAD_NAME): vol.Any(cv.string, dict),
            vol.Optional(ATTR_WORKLOAD_NAMES): vol.Any(
                cv.string,
                vol.All(cv.ensure_list, [vol.Any(cv.string, dict)]),
                vol.All(cv.ensure_list, [cv.string]),
                dict,
            ),
            vol.Optional(ATTR_NAMESPACE): cv.string,
        },
        _validate_workload_schema,
    )
)


async def async_setup_services(hass: HomeAssistant) -> None:  # noqa: C901
    """Set up the Kubernetes services."""
    _LOGGER.info("Setting up Kubernetes services")

    # Generic service handlers
    async def scale_workload(call: ServiceCall) -> None:
        """Scale one or more Kubernetes workloads to the specified number of replicas."""
        workloads = _extract_workload_info(call.data, hass)

        if not workloads:
            _LOGGER.error("No valid workloads found in service call data")
            return

        replicas = call.data[ATTR_REPLICAS]

        # Get the Kubernetes client from the first config entry
        kubernetes_data = hass.data.get(DOMAIN)
        if not kubernetes_data:
            _LOGGER.error("No Kubernetes integration configured")
            return

        config_entry_id = next(iter(kubernetes_data.keys()))
        config_data = kubernetes_data[config_entry_id]["config"]

        from .kubernetes_client import KubernetesClient

        client = KubernetesClient(config_data)

        for workload_name, namespace, workload_type in workloads:
            namespace = namespace or config_data.get("namespace", "default")

            if workload_type == WORKLOAD_TYPE_DEPLOYMENT:
                success = await client.scale_deployment(
                    workload_name, replicas, namespace
                )
                if success:
                    _LOGGER.info(
                        "Successfully scaled deployment %s to %d replicas in namespace %s",
                        workload_name,
                        replicas,
                        namespace,
                    )
                else:
                    _LOGGER.error(
                        "Failed to scale deployment %s in namespace %s",
                        workload_name,
                        namespace,
                    )
            elif workload_type == WORKLOAD_TYPE_STATEFULSET:
                success = await client.scale_statefulset(
                    workload_name, replicas, namespace
                )
                if success:
                    _LOGGER.info(
                        "Successfully scaled StatefulSet %s to %d replicas in namespace %s",
                        workload_name,
                        replicas,
                        namespace,
                    )
                else:
                    _LOGGER.error(
                        "Failed to scale StatefulSet %s in namespace %s",
                        workload_name,
                        namespace,
                    )
            else:
                _LOGGER.warning(
                    "Cannot scale %s (type: %s) - scaling only supported for Deployments and StatefulSets",
                    workload_name,
                    workload_type,
                )

        if len(workloads) > 1:
            _LOGGER.info("Completed scaling operation for %d workloads", len(workloads))

    async def start_workload(call: ServiceCall) -> None:
        """Start one or more Kubernetes workloads by scaling to specified replicas, or trigger CronJobs."""
        workloads = _extract_workload_info(call.data, hass)

        if not workloads:
            _LOGGER.error(
                "No valid workloads found in service call data. Call data: %s",
                call.data,
            )
            return

        replicas = call.data.get(ATTR_REPLICAS, 1)

        # Get the Kubernetes client from the first config entry
        kubernetes_data = hass.data.get(DOMAIN)
        if not kubernetes_data:
            _LOGGER.error("No Kubernetes integration configured")
            return

        config_entry_id = next(iter(kubernetes_data.keys()))
        config_data = kubernetes_data[config_entry_id]["config"]

        from .kubernetes_client import KubernetesClient

        client = KubernetesClient(config_data)

        for workload_name, namespace, workload_type in workloads:
            namespace = namespace or config_data.get("namespace", "default")

            if workload_type == WORKLOAD_TYPE_DEPLOYMENT:
                success = await client.start_deployment(
                    workload_name, replicas, namespace
                )
                if success:
                    _LOGGER.info(
                        "Successfully started deployment %s with %d replicas in namespace %s",
                        workload_name,
                        replicas,
                        namespace,
                    )
                else:
                    _LOGGER.error(
                        "Failed to start deployment %s in namespace %s",
                        workload_name,
                        namespace,
                    )
            elif workload_type == WORKLOAD_TYPE_STATEFULSET:
                success = await client.start_statefulset(
                    workload_name, replicas, namespace
                )
                if success:
                    _LOGGER.info(
                        "Successfully started StatefulSet %s with %d replicas in namespace %s",
                        workload_name,
                        replicas,
                        namespace,
                    )
                else:
                    _LOGGER.error(
                        "Failed to start StatefulSet %s in namespace %s",
                        workload_name,
                        namespace,
                    )
            elif workload_type == WORKLOAD_TYPE_CRONJOB:
                # For CronJobs, "start" means trigger (create a job from the CronJob)
                result = await client.trigger_cronjob(workload_name, namespace)
                if result.get("success"):
                    _LOGGER.info(
                        "Successfully triggered CronJob %s in namespace %s, created job %s",
                        workload_name,
                        namespace,
                        result.get("job_name", "unknown"),
                    )
                else:
                    _LOGGER.error(
                        "Failed to trigger CronJob %s in namespace %s: %s",
                        workload_name,
                        namespace,
                        result.get("error", "Unknown error"),
                    )
            else:
                _LOGGER.warning(
                    "Unsupported workload type %s for start operation", workload_type
                )

        if len(workloads) > 1:
            _LOGGER.info("Completed start operation for %d workloads", len(workloads))

    async def stop_workload(call: ServiceCall) -> None:
        """Stop one or more Kubernetes workloads by scaling to 0 (Deployments/StatefulSets only)."""
        workloads = _extract_workload_info(call.data, hass)

        if not workloads:
            _LOGGER.error("No valid workloads found in service call data")
            return

        # Get the Kubernetes client from the first config entry
        kubernetes_data = hass.data.get(DOMAIN)
        if not kubernetes_data:
            _LOGGER.error("No Kubernetes integration configured")
            return

        config_entry_id = next(iter(kubernetes_data.keys()))
        config_data = kubernetes_data[config_entry_id]["config"]

        from .kubernetes_client import KubernetesClient

        client = KubernetesClient(config_data)

        for workload_name, namespace, workload_type in workloads:
            namespace = namespace or config_data.get("namespace", "default")

            if workload_type == WORKLOAD_TYPE_DEPLOYMENT:
                success = await client.stop_deployment(workload_name, namespace)
                if success:
                    _LOGGER.info(
                        "Successfully stopped deployment %s in namespace %s",
                        workload_name,
                        namespace,
                    )
                else:
                    _LOGGER.error(
                        "Failed to stop deployment %s in namespace %s",
                        workload_name,
                        namespace,
                    )
            elif workload_type == WORKLOAD_TYPE_STATEFULSET:
                success = await client.stop_statefulset(workload_name, namespace)
                if success:
                    _LOGGER.info(
                        "Successfully stopped StatefulSet %s in namespace %s",
                        workload_name,
                        namespace,
                    )
                else:
                    _LOGGER.error(
                        "Failed to stop StatefulSet %s in namespace %s",
                        workload_name,
                        namespace,
                    )
            elif workload_type == WORKLOAD_TYPE_CRONJOB:
                _LOGGER.warning(
                    "Cannot stop %s (type: %s) - stop operation only supported for Deployments and StatefulSets. Use the switch entity to suspend CronJobs.",
                    workload_name,
                    workload_type,
                )
            else:
                _LOGGER.warning(
                    "Unsupported workload type %s for stop operation", workload_type
                )

        if len(workloads) > 1:
            _LOGGER.info("Completed stop operation for %d workloads", len(workloads))

    # Register the generic services
    hass.services.async_register(
        DOMAIN,
        SERVICE_SCALE_WORKLOAD,
        scale_workload,
        schema=SCALE_WORKLOAD_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_START_WORKLOAD,
        start_workload,
        schema=START_WORKLOAD_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_STOP_WORKLOAD,
        stop_workload,
        schema=STOP_WORKLOAD_SCHEMA,
    )


async def async_unload_services(hass: HomeAssistant) -> None:
    """Unload the Kubernetes services."""
    hass.services.async_remove(DOMAIN, SERVICE_SCALE_WORKLOAD)
    hass.services.async_remove(DOMAIN, SERVICE_START_WORKLOAD)
    hass.services.async_remove(DOMAIN, SERVICE_STOP_WORKLOAD)
