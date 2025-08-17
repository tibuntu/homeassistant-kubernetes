"""Services for the Kubernetes integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
import voluptuous as vol

from .const import (
    ATTR_DEPLOYMENT_NAME,
    ATTR_DEPLOYMENT_NAMES,
    ATTR_NAMESPACE,
    ATTR_REPLICAS,
    ATTR_STATEFULSET_NAME,
    ATTR_STATEFULSET_NAMES,
    DOMAIN,
    SERVICE_SCALE_DEPLOYMENT,
    SERVICE_SCALE_STATEFULSET,
    SERVICE_START_DEPLOYMENT,
    SERVICE_START_STATEFULSET,
    SERVICE_STOP_DEPLOYMENT,
    SERVICE_STOP_STATEFULSET,
)

_LOGGER = logging.getLogger(__name__)


def _extract_deployment_names_and_namespaces(  # noqa: C901
    call_data: dict[str, Any], hass: HomeAssistant
) -> tuple[list[str], list[str | None]]:
    """Extract deployment names and namespaces from service call data, supporting both single and multiple selections."""
    deployment_names = []
    namespaces = []

    _LOGGER.debug(
        "Extracting deployment names and namespaces from call data: %s", call_data
    )

    if ATTR_DEPLOYMENT_NAMES in call_data:
        names = call_data[ATTR_DEPLOYMENT_NAMES]
        _LOGGER.debug("Found deployment_names: %s (type: %s)", names, type(names))

        if isinstance(names, str):
            deployment_names.append(names)
            # Try to get namespace from entity attributes
            namespace, deployment_name = _get_namespace_from_entity(hass, names)
            namespaces.append(namespace)
            _LOGGER.debug(
                "Extracted namespace: %s for deployment name: %s", namespace, names
            )
        elif isinstance(names, dict) and "entity_id" in names:
            # Handle Home Assistant UI format: {'entity_id': ['switch.break_time', 'switch.cert_manager']}
            entity_ids = names["entity_id"]
            if isinstance(entity_ids, list):
                for entity_id in entity_ids:
                    if isinstance(entity_id, str) and entity_id.startswith("switch."):
                        # Get namespace and deployment name from entity attributes
                        namespace, deployment_name = _get_namespace_from_entity(
                            hass, entity_id
                        )
                        if deployment_name:
                            deployment_names.append(deployment_name)
                            namespaces.append(namespace)
                            _LOGGER.debug(
                                "Extracted deployment name: %s from entity: %s",
                                deployment_name,
                                entity_id,
                            )
                            _LOGGER.debug(
                                "Extracted namespace: %s for entity: %s",
                                namespace,
                                entity_id,
                            )
                        else:
                            # Fallback: extract from entity ID (for backward compatibility)
                            deployment_name = entity_id.replace("switch.", "")
                            # Remove _deployment suffix if present
                            if deployment_name.endswith("_deployment"):
                                deployment_name = deployment_name[
                                    :-11
                                ]  # Remove '_deployment'
                            deployment_names.append(deployment_name)
                            namespaces.append(namespace)
                            _LOGGER.debug(
                                "Fallback: extracted deployment name: %s from entity ID: %s",
                                deployment_name,
                                entity_id,
                            )
                            _LOGGER.debug(
                                "Extracted namespace: %s for entity: %s",
                                namespace,
                                entity_id,
                            )
        elif isinstance(names, list):
            # Handle list of dictionaries or strings
            for item in names:
                if isinstance(item, str):
                    deployment_names.append(item)
                    # Try to get namespace from entity attributes
                    namespace, _ = _get_namespace_from_entity(hass, item)
                    namespaces.append(namespace)
                elif isinstance(item, dict) and "entity_id" in item:
                    # Handle Home Assistant UI format: [{'entity_id': ['switch.break_time', 'switch.cert_manager']}]
                    entity_ids = item["entity_id"]
                    if isinstance(entity_ids, list):
                        for entity_id in entity_ids:
                            if isinstance(entity_id, str) and entity_id.startswith(
                                "switch."
                            ):
                                # Get namespace and deployment name from entity attributes
                                namespace, deployment_name = _get_namespace_from_entity(
                                    hass, entity_id
                                )
                                if deployment_name:
                                    deployment_names.append(deployment_name)
                                    namespaces.append(namespace)
                                    _LOGGER.debug(
                                        "Extracted deployment name: %s from entity: %s",
                                        deployment_name,
                                        entity_id,
                                    )
                                    _LOGGER.debug(
                                        "Extracted namespace: %s for entity: %s",
                                        namespace,
                                        entity_id,
                                    )
                                else:
                                    # Fallback: extract from entity ID (for backward compatibility)
                                    deployment_name = entity_id.replace("switch.", "")
                                    # Remove _deployment suffix if present
                                    if deployment_name.endswith("_deployment"):
                                        deployment_name = deployment_name[
                                            :-11
                                        ]  # Remove '_deployment'
                                    deployment_names.append(deployment_name)
                                    namespaces.append(namespace)
                                    _LOGGER.debug(
                                        "Fallback: extracted deployment name: %s from entity ID: %s",
                                        deployment_name,
                                        entity_id,
                                    )
                                    _LOGGER.debug(
                                        "Extracted namespace: %s for entity: %s",
                                        namespace,
                                        entity_id,
                                    )

    elif ATTR_DEPLOYMENT_NAME in call_data:
        name = call_data[ATTR_DEPLOYMENT_NAME]
        _LOGGER.debug("Found deployment_name: %s (type: %s)", name, type(name))
        if isinstance(name, str):
            deployment_names.append(name)
            # Try to get namespace from entity attributes
            namespace, _ = _get_namespace_from_entity(hass, name)
            namespaces.append(namespace)
            _LOGGER.debug(
                "Extracted namespace: %s for deployment name: %s", namespace, name
            )
        elif isinstance(name, dict) and "entity_id" in name:
            # Handle single entity selection
            entity_id = name["entity_id"]
            if isinstance(entity_id, str) and entity_id.startswith("switch."):
                # Get namespace and deployment name from entity attributes
                namespace, deployment_name = _get_namespace_from_entity(hass, entity_id)
                if deployment_name:
                    deployment_names.append(deployment_name)
                    namespaces.append(namespace)
                    _LOGGER.debug(
                        "Extracted deployment name: %s from entity: %s",
                        deployment_name,
                        entity_id,
                    )
                    _LOGGER.debug(
                        "Extracted namespace: %s for entity: %s", namespace, entity_id
                    )
                else:
                    # Fallback: extract from entity ID (for backward compatibility)
                    deployment_name = entity_id.replace("switch.", "")
                    # Remove _deployment suffix if present
                    if deployment_name.endswith("_deployment"):
                        deployment_name = deployment_name[:-11]  # Remove '_deployment'
                    deployment_names.append(deployment_name)
                    namespaces.append(namespace)
                    _LOGGER.debug(
                        "Fallback: extracted deployment name: %s from entity ID: %s",
                        deployment_name,
                        entity_id,
                    )
                    _LOGGER.debug(
                        "Extracted namespace: %s for entity: %s", namespace, entity_id
                    )

    _LOGGER.debug("Final deployment names: %s", deployment_names)
    _LOGGER.debug("Final namespaces: %s", namespaces)
    return deployment_names, namespaces


def _extract_statefulset_names_and_namespaces(  # noqa: C901
    call_data: dict[str, Any], hass: HomeAssistant
) -> tuple[list[str], list[str | None]]:
    """Extract StatefulSet names and namespaces from service call data, supporting both single and multiple selections."""
    statefulset_names = []
    namespaces = []

    _LOGGER.debug(
        "Extracting statefulset names and namespaces from call data: %s", call_data
    )

    if ATTR_STATEFULSET_NAMES in call_data:
        names = call_data[ATTR_STATEFULSET_NAMES]
        _LOGGER.debug("Found statefulset_names: %s (type: %s)", names, type(names))

        if isinstance(names, str):
            statefulset_names.append(names)
            # Try to get namespace from entity attributes
            namespace, _ = _get_namespace_from_entity(hass, names)
            namespaces.append(namespace)
            _LOGGER.debug(
                "Extracted namespace: %s for statefulset name: %s", namespace, names
            )
        elif isinstance(names, dict) and "entity_id" in names:
            # Handle Home Assistant UI format: {'entity_id': ['switch.redis_statefulset', 'switch.postgres_statefulset']}
            entity_ids = names["entity_id"]
            if isinstance(entity_ids, list):
                for entity_id in entity_ids:
                    if isinstance(entity_id, str) and entity_id.startswith("switch."):
                        # Get namespace and statefulset name from entity attributes
                        namespace, statefulset_name = _get_namespace_from_entity(
                            hass, entity_id
                        )
                        if statefulset_name:
                            statefulset_names.append(statefulset_name)
                            namespaces.append(namespace)
                            _LOGGER.debug(
                                "Extracted statefulset name: %s from entity: %s",
                                statefulset_name,
                                entity_id,
                            )
                            _LOGGER.debug(
                                "Extracted namespace: %s for entity: %s",
                                namespace,
                                entity_id,
                            )
                        else:
                            # Fallback: extract from entity ID (for backward compatibility)
                            statefulset_name = entity_id.replace("switch.", "")
                            # Remove _statefulset suffix if present
                            if statefulset_name.endswith("_statefulset"):
                                statefulset_name = statefulset_name[
                                    :-12
                                ]  # Remove '_statefulset'
                            statefulset_names.append(statefulset_name)
                            namespaces.append(namespace)
                            _LOGGER.debug(
                                "Fallback: extracted statefulset name: %s from entity ID: %s",
                                statefulset_name,
                                entity_id,
                            )
                            _LOGGER.debug(
                                "Extracted namespace: %s for entity: %s",
                                namespace,
                                entity_id,
                            )
        elif isinstance(names, list):
            # Handle list of dictionaries or strings
            for item in names:
                if isinstance(item, str):
                    statefulset_names.append(item)
                    # Try to get namespace from entity attributes
                    namespace, _ = _get_namespace_from_entity(hass, item)
                    namespaces.append(namespace)
                elif isinstance(item, dict) and "entity_id" in item:
                    # Handle Home Assistant UI format: [{'entity_id': ['switch.redis_statefulset', 'switch.postgres_statefulset']}]
                    entity_ids = item["entity_id"]
                    if isinstance(entity_ids, list):
                        for entity_id in entity_ids:
                            if isinstance(entity_id, str) and entity_id.startswith(
                                "switch."
                            ):
                                # Get namespace and statefulset name from entity attributes
                                namespace, statefulset_name = (
                                    _get_namespace_from_entity(hass, entity_id)
                                )
                                if statefulset_name:
                                    statefulset_names.append(statefulset_name)
                                    namespaces.append(namespace)
                                    _LOGGER.debug(
                                        "Extracted statefulset name: %s from entity: %s",
                                        statefulset_name,
                                        entity_id,
                                    )
                                    _LOGGER.debug(
                                        "Extracted namespace: %s for entity: %s",
                                        namespace,
                                        entity_id,
                                    )
                                else:
                                    # Fallback: extract from entity ID (for backward compatibility)
                                    statefulset_name = entity_id.replace("switch.", "")
                                    # Remove _statefulset suffix if present
                                    if statefulset_name.endswith("_statefulset"):
                                        statefulset_name = statefulset_name[
                                            :-12
                                        ]  # Remove '_statefulset'
                                    statefulset_names.append(statefulset_name)
                                    namespaces.append(namespace)
                                    _LOGGER.debug(
                                        "Fallback: extracted statefulset name: %s from entity ID: %s",
                                        statefulset_name,
                                        entity_id,
                                    )
                                    _LOGGER.debug(
                                        "Extracted namespace: %s for entity: %s",
                                        namespace,
                                        entity_id,
                                    )

    elif ATTR_STATEFULSET_NAME in call_data:
        name = call_data[ATTR_STATEFULSET_NAME]
        _LOGGER.debug("Found statefulset_name: %s (type: %s)", name, type(name))
        if isinstance(name, str):
            statefulset_names.append(name)
            # Try to get namespace from entity attributes
            namespace, _ = _get_namespace_from_entity(hass, name)
            namespaces.append(namespace)
            _LOGGER.debug(
                "Extracted namespace: %s for statefulset name: %s", namespace, name
            )
        elif isinstance(name, dict) and "entity_id" in name:
            # Handle single entity selection
            entity_id = name["entity_id"]
            if isinstance(entity_id, str) and entity_id.startswith("switch."):
                # Get namespace and statefulset name from entity attributes
                namespace, statefulset_name = _get_namespace_from_entity(
                    hass, entity_id
                )
                if statefulset_name:
                    statefulset_names.append(statefulset_name)
                    namespaces.append(namespace)
                    _LOGGER.debug(
                        "Extracted statefulset name: %s from entity: %s",
                        statefulset_name,
                        entity_id,
                    )
                    _LOGGER.debug(
                        "Extracted namespace: %s for entity: %s", namespace, entity_id
                    )
                else:
                    # Fallback: extract from entity ID (for backward compatibility)
                    statefulset_name = entity_id.replace("switch.", "")
                    # Remove _statefulset suffix if present
                    if statefulset_name.endswith("_statefulset"):
                        statefulset_name = statefulset_name[
                            :-12
                        ]  # Remove '_statefulset'
                    statefulset_names.append(statefulset_name)
                    namespaces.append(namespace)
                    _LOGGER.debug(
                        "Fallback: extracted statefulset name: %s from entity ID: %s",
                        statefulset_name,
                        entity_id,
                    )
                    _LOGGER.debug(
                        "Extracted namespace: %s for entity: %s", namespace, entity_id
                    )

    _LOGGER.debug("Final statefulset names: %s", statefulset_names)
    _LOGGER.debug("Final namespaces: %s", namespaces)
    return statefulset_names, namespaces


def _get_namespace_from_entity(
    hass: HomeAssistant, entity_id_or_name: str
) -> tuple[str | None, str | None]:
    """Get namespace and deployment name from entity attributes."""
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
            deployment_name = entity.attributes.get("deployment_name")
            statefulset_name = entity.attributes.get("statefulset_name")
            _LOGGER.debug(
                "Found namespace %s, deployment_name %s, statefulset_name %s for entity %s",
                namespace,
                deployment_name,
                statefulset_name,
                entity_id,
            )
            return namespace, deployment_name or statefulset_name
        else:
            _LOGGER.debug("Entity %s not found or has no attributes", entity_id)
            return None, None
    except Exception as e:
        _LOGGER.debug("Error getting namespace for entity %s: %s", entity_id_or_name, e)
        return None, None


def _validate_deployment_schema(data: dict) -> dict:
    """Validate that at least one deployment field is provided."""
    if ATTR_DEPLOYMENT_NAME not in data and ATTR_DEPLOYMENT_NAMES not in data:
        raise vol.Invalid("Either deployment_name or deployment_names must be provided")
    return data


def _validate_statefulset_schema(data: dict) -> dict:
    """Validate that at least one StatefulSet field is provided."""
    if ATTR_STATEFULSET_NAME not in data and ATTR_STATEFULSET_NAMES not in data:
        raise vol.Invalid(
            "Either statefulset_name or statefulset_names must be provided"
        )
    return data


# Service schemas
SCALE_DEPLOYMENT_SCHEMA = vol.Schema(
    vol.All(
        {
            vol.Optional(ATTR_DEPLOYMENT_NAME): vol.Any(cv.string, dict),
            vol.Optional(ATTR_DEPLOYMENT_NAMES): vol.Any(
                cv.string,
                vol.All(cv.ensure_list, [vol.Any(cv.string, dict)]),
                vol.All(cv.ensure_list, [cv.string]),
                dict,
            ),
            vol.Required(ATTR_REPLICAS): vol.All(vol.Coerce(int), vol.Range(min=0)),
            vol.Optional(ATTR_NAMESPACE): cv.string,
        },
        _validate_deployment_schema,
    )
)

START_DEPLOYMENT_SCHEMA = vol.Schema(
    vol.All(
        {
            vol.Optional(ATTR_DEPLOYMENT_NAME): vol.Any(cv.string, dict),
            vol.Optional(ATTR_DEPLOYMENT_NAMES): vol.Any(
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
        _validate_deployment_schema,
    )
)

STOP_DEPLOYMENT_SCHEMA = vol.Schema(
    vol.All(
        {
            vol.Optional(ATTR_DEPLOYMENT_NAME): vol.Any(cv.string, dict),
            vol.Optional(ATTR_DEPLOYMENT_NAMES): vol.Any(
                cv.string,
                vol.All(cv.ensure_list, [vol.Any(cv.string, dict)]),
                vol.All(cv.ensure_list, [cv.string]),
                dict,
            ),
            vol.Optional(ATTR_NAMESPACE): cv.string,
        },
        _validate_deployment_schema,
    )
)

# StatefulSet service schemas
SCALE_STATEFULSET_SCHEMA = vol.Schema(
    vol.All(
        {
            vol.Optional(ATTR_STATEFULSET_NAME): vol.Any(cv.string, dict),
            vol.Optional(ATTR_STATEFULSET_NAMES): vol.Any(
                cv.string,
                vol.All(cv.ensure_list, [vol.Any(cv.string, dict)]),
                vol.All(cv.ensure_list, [cv.string]),
                dict,
            ),
            vol.Required(ATTR_REPLICAS): vol.All(vol.Coerce(int), vol.Range(min=0)),
            vol.Optional(ATTR_NAMESPACE): cv.string,
        },
        _validate_statefulset_schema,
    )
)

START_STATEFULSET_SCHEMA = vol.Schema(
    vol.All(
        {
            vol.Optional(ATTR_STATEFULSET_NAME): vol.Any(cv.string, dict),
            vol.Optional(ATTR_STATEFULSET_NAMES): vol.Any(
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
        _validate_statefulset_schema,
    )
)

STOP_STATEFULSET_SCHEMA = vol.Schema(
    vol.All(
        {
            vol.Optional(ATTR_STATEFULSET_NAME): vol.Any(cv.string, dict),
            vol.Optional(ATTR_STATEFULSET_NAMES): vol.Any(
                cv.string,
                vol.All(cv.ensure_list, [vol.Any(cv.string, dict)]),
                vol.All(cv.ensure_list, [cv.string]),
                dict,
            ),
            vol.Optional(ATTR_NAMESPACE): cv.string,
        },
        _validate_statefulset_schema,
    )
)


async def async_setup_services(hass: HomeAssistant) -> None:  # noqa: C901
    """Set up the Kubernetes services."""

    async def scale_deployment(call: ServiceCall) -> None:
        """Scale a deployment to the specified number of replicas."""
        deployment_names, namespaces = _extract_deployment_names_and_namespaces(
            call.data, hass
        )
        # _validate_deployment_names(deployment_names) # Removed old validation

        if not deployment_names:
            _LOGGER.error("No valid deployment names found in service call data")
            return

        replicas = call.data[ATTR_REPLICAS]

        # Use provided namespace if available, otherwise use extracted namespaces
        provided_namespace = call.data.get(ATTR_NAMESPACE)
        if provided_namespace:
            _LOGGER.info(
                "Using provided namespace: %s for all deployments", provided_namespace
            )
            namespaces = [provided_namespace] * len(deployment_names)
        else:
            _LOGGER.info("Using extracted namespaces: %s", namespaces)

        # Get the Kubernetes client from the first config entry
        kubernetes_data = hass.data.get(DOMAIN)
        if not kubernetes_data:
            _LOGGER.error("No Kubernetes integration configured")
            return

        # Use the first config entry
        config_entry_id = next(iter(kubernetes_data.keys()))
        config_data = kubernetes_data[config_entry_id]["config"]

        from .kubernetes_client import KubernetesClient

        client = KubernetesClient(config_data)

        for deployment_name, namespace in zip(deployment_names, namespaces):
            success = await client.scale_deployment(
                deployment_name, replicas, namespace
            )
            if success:
                _LOGGER.info(
                    "Successfully scaled deployment %s to %d replicas in namespace %s",
                    deployment_name,
                    replicas,
                    namespace,
                )
            else:
                _LOGGER.error(
                    "Failed to scale deployment %s in namespace %s",
                    deployment_name,
                    namespace,
                )

        if len(deployment_names) > 1:
            _LOGGER.info(
                "Completed scaling operation for %d deployments", len(deployment_names)
            )

    async def start_deployment(call: ServiceCall) -> None:
        """Start a deployment by scaling it to the specified number of replicas."""
        deployment_names, namespaces = _extract_deployment_names_and_namespaces(
            call.data, hass
        )
        # _validate_deployment_names(deployment_names) # Removed old validation

        if not deployment_names:
            _LOGGER.error("No valid deployment names found in service call data")
            return

        replicas = call.data.get(ATTR_REPLICAS, 1)

        # Use provided namespace if available, otherwise use extracted namespaces
        provided_namespace = call.data.get(ATTR_NAMESPACE)
        if provided_namespace:
            _LOGGER.info(
                "Using provided namespace: %s for all deployments", provided_namespace
            )
            namespaces = [provided_namespace] * len(deployment_names)
        else:
            _LOGGER.info("Using extracted namespaces: %s", namespaces)

        # Get the Kubernetes client from the first config entry
        kubernetes_data = hass.data.get(DOMAIN)
        if not kubernetes_data:
            _LOGGER.error("No Kubernetes integration configured")
            return

        # Use the first config entry
        config_entry_id = next(iter(kubernetes_data.keys()))
        config_data = kubernetes_data[config_entry_id]["config"]

        from .kubernetes_client import KubernetesClient

        client = KubernetesClient(config_data)

        for deployment_name, namespace in zip(deployment_names, namespaces):
            success = await client.start_deployment(
                deployment_name, replicas, namespace
            )
            if success:
                _LOGGER.info(
                    "Successfully started deployment %s with %d replicas in namespace %s",
                    deployment_name,
                    replicas,
                    namespace,
                )
            else:
                _LOGGER.error(
                    "Failed to start deployment %s in namespace %s",
                    deployment_name,
                    namespace,
                )

        if len(deployment_names) > 1:
            _LOGGER.info(
                "Completed start operation for %d deployments", len(deployment_names)
            )

    async def stop_deployment(call: ServiceCall) -> None:
        """Stop a deployment by scaling it to 0 replicas."""
        _LOGGER.info("stop_deployment called with data: %s", call.data)
        _LOGGER.info("stop_deployment call.data type: %s", type(call.data))
        _LOGGER.info(
            "stop_deployment call.data keys: %s",
            list(call.data.keys()) if isinstance(call.data, dict) else "Not a dict",
        )

        deployment_names, namespaces = _extract_deployment_names_and_namespaces(
            call.data, hass
        )
        _LOGGER.info("Extracted deployment names: %s", deployment_names)
        _LOGGER.info("Extracted namespaces: %s", namespaces)

        # _validate_deployment_names(deployment_names) # Removed old validation

        if not deployment_names:
            _LOGGER.error("No valid deployment names found in service call data")
            return

        # Use provided namespace if available, otherwise use extracted namespaces
        provided_namespace = call.data.get(ATTR_NAMESPACE)
        if provided_namespace:
            _LOGGER.info(
                "Using provided namespace: %s for all deployments", provided_namespace
            )
            namespaces = [provided_namespace] * len(deployment_names)
        else:
            _LOGGER.info("Using extracted namespaces: %s", namespaces)

        # Get the Kubernetes client from the first config entry
        kubernetes_data = hass.data.get(DOMAIN)
        if not kubernetes_data:
            _LOGGER.error("No Kubernetes integration configured")
            return

        # Use the first config entry
        config_entry_id = next(iter(kubernetes_data.keys()))
        config_data = kubernetes_data[config_entry_id]["config"]
        _LOGGER.debug("Using config data: %s", config_data)

        from .kubernetes_client import KubernetesClient

        client = KubernetesClient(config_data)

        for deployment_name, namespace in zip(deployment_names, namespaces):
            success = await client.stop_deployment(deployment_name, namespace)
            if success:
                _LOGGER.info(
                    "Successfully stopped deployment %s in namespace %s",
                    deployment_name,
                    namespace,
                )
            else:
                _LOGGER.error(
                    "Failed to stop deployment %s in namespace %s",
                    deployment_name,
                    namespace,
                )

        if len(deployment_names) > 1:
            _LOGGER.info(
                "Completed stop operation for %d deployments", len(deployment_names)
            )

    # StatefulSet services
    async def scale_statefulset(call: ServiceCall) -> None:
        """Scale a StatefulSet to the specified number of replicas."""
        statefulset_names, namespaces = _extract_statefulset_names_and_namespaces(
            call.data, hass
        )
        # _validate_statefulset_names(statefulset_names) # Removed old validation

        if not statefulset_names:
            _LOGGER.error("No valid StatefulSet names found in service call data")
            return

        replicas = call.data[ATTR_REPLICAS]

        # Use provided namespace if available, otherwise use extracted namespaces
        provided_namespace = call.data.get(ATTR_NAMESPACE)
        if provided_namespace:
            _LOGGER.info(
                "Using provided namespace: %s for all StatefulSets", provided_namespace
            )
            namespaces = [provided_namespace] * len(statefulset_names)
        else:
            _LOGGER.info("Using extracted namespaces: %s", namespaces)

        # Get the Kubernetes client from the first config entry
        kubernetes_data = hass.data.get(DOMAIN)
        if not kubernetes_data:
            _LOGGER.error("No Kubernetes integration configured")
            return

        # Use the first config entry
        config_entry_id = next(iter(kubernetes_data.keys()))
        config_data = kubernetes_data[config_entry_id]["config"]

        from .kubernetes_client import KubernetesClient

        client = KubernetesClient(config_data)

        for statefulset_name, namespace in zip(statefulset_names, namespaces):
            success = await client.scale_statefulset(
                statefulset_name, replicas, namespace
            )
            if success:
                _LOGGER.info(
                    "Successfully scaled StatefulSet %s to %d replicas in namespace %s",
                    statefulset_name,
                    replicas,
                    namespace,
                )
            else:
                _LOGGER.error(
                    "Failed to scale StatefulSet %s in namespace %s",
                    statefulset_name,
                    namespace,
                )

        if len(statefulset_names) > 1:
            _LOGGER.info(
                "Completed scaling operation for %d StatefulSets",
                len(statefulset_names),
            )

    async def start_statefulset(call: ServiceCall) -> None:
        """Start a StatefulSet by scaling it to the specified number of replicas."""
        statefulset_names, namespaces = _extract_statefulset_names_and_namespaces(
            call.data, hass
        )
        # _validate_statefulset_names(statefulset_names) # Removed old validation

        if not statefulset_names:
            _LOGGER.error("No valid StatefulSet names found in service call data")
            return

        replicas = call.data.get(ATTR_REPLICAS, 1)

        # Use provided namespace if available, otherwise use extracted namespaces
        provided_namespace = call.data.get(ATTR_NAMESPACE)
        if provided_namespace:
            _LOGGER.info(
                "Using provided namespace: %s for all StatefulSets", provided_namespace
            )
            namespaces = [provided_namespace] * len(statefulset_names)
        else:
            _LOGGER.info("Using extracted namespaces: %s", namespaces)

        # Get the Kubernetes client from the first config entry
        kubernetes_data = hass.data.get(DOMAIN)
        if not kubernetes_data:
            _LOGGER.error("No Kubernetes integration configured")
            return

        # Use the first config entry
        config_entry_id = next(iter(kubernetes_data.keys()))
        config_data = kubernetes_data[config_entry_id]["config"]

        from .kubernetes_client import KubernetesClient

        client = KubernetesClient(config_data)

        for statefulset_name, namespace in zip(statefulset_names, namespaces):
            success = await client.start_statefulset(
                statefulset_name, replicas, namespace
            )
            if success:
                _LOGGER.info(
                    "Successfully started StatefulSet %s with %d replicas in namespace %s",
                    statefulset_name,
                    replicas,
                    namespace,
                )
            else:
                _LOGGER.error(
                    "Failed to start StatefulSet %s in namespace %s",
                    statefulset_name,
                    namespace,
                )

        if len(statefulset_names) > 1:
            _LOGGER.info(
                "Completed start operation for %d StatefulSets", len(statefulset_names)
            )

    async def stop_statefulset(call: ServiceCall) -> None:
        """Stop a StatefulSet by scaling it to 0 replicas."""
        statefulset_names, namespaces = _extract_statefulset_names_and_namespaces(
            call.data, hass
        )
        # _validate_statefulset_names(statefulset_names) # Removed old validation

        if not statefulset_names:
            _LOGGER.error("No valid StatefulSet names found in service call data")
            return

        # Use provided namespace if available, otherwise use extracted namespaces
        provided_namespace = call.data.get(ATTR_NAMESPACE)
        if provided_namespace:
            _LOGGER.info(
                "Using provided namespace: %s for all StatefulSets", provided_namespace
            )
            namespaces = [provided_namespace] * len(statefulset_names)
        else:
            _LOGGER.info("Using extracted namespaces: %s", namespaces)

        # Get the Kubernetes client from the first config entry
        kubernetes_data = hass.data.get(DOMAIN)
        if not kubernetes_data:
            _LOGGER.error("No Kubernetes integration configured")
            return

        # Use the first config entry
        config_entry_id = next(iter(kubernetes_data.keys()))
        config_data = kubernetes_data[config_entry_id]["config"]

        from .kubernetes_client import KubernetesClient

        client = KubernetesClient(config_data)

        for statefulset_name, namespace in zip(statefulset_names, namespaces):
            success = await client.stop_statefulset(statefulset_name, namespace)
            if success:
                _LOGGER.info(
                    "Successfully stopped StatefulSet %s in namespace %s",
                    statefulset_name,
                    namespace,
                )
            else:
                _LOGGER.error(
                    "Failed to stop StatefulSet %s in namespace %s",
                    statefulset_name,
                    namespace,
                )

        if len(statefulset_names) > 1:
            _LOGGER.info(
                "Completed stop operation for %d StatefulSets", len(statefulset_names)
            )

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
