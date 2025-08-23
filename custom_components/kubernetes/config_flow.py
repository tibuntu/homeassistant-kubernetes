"""Config flow for Kubernetes integration."""

from __future__ import annotations

import logging
import sys
from typing import Any

import aiohttp
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.data_entry_flow import AbortFlow, FlowResult
import voluptuous as vol

# Global variables for lazy import
KUBERNETES_AVAILABLE: bool | None = None
client: Any | None = None
ApiException: type = Exception

from .const import (
    CONF_API_TOKEN,
    CONF_CA_CERT,
    CONF_CLUSTER_NAME,
    CONF_MONITOR_ALL_NAMESPACES,
    CONF_NAMESPACE,
    CONF_SCALE_COOLDOWN,
    CONF_SCALE_VERIFICATION_TIMEOUT,
    CONF_SWITCH_UPDATE_INTERVAL,
    CONF_VERIFY_SSL,
    DEFAULT_CLUSTER_NAME,
    DEFAULT_MONITOR_ALL_NAMESPACES,
    DEFAULT_NAMESPACE,
    DEFAULT_PORT,
    DEFAULT_SCALE_COOLDOWN,
    DEFAULT_SCALE_VERIFICATION_TIMEOUT,
    DEFAULT_SWITCH_UPDATE_INTERVAL,
    DEFAULT_VERIFY_SSL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


def _ensure_kubernetes_imported() -> bool:
    """Ensure kubernetes package is imported."""
    global KUBERNETES_AVAILABLE, client, ApiException

    if KUBERNETES_AVAILABLE is None:
        try:
            # Try to import the same way as kubernetes_client.py
            import kubernetes.client as k8s_client
            from kubernetes.client.rest import ApiException as K8sApiException

            # Set global variables
            client = k8s_client
            ApiException = K8sApiException
            KUBERNETES_AVAILABLE = True
            _LOGGER.info("Kubernetes package imported successfully")

        except ImportError as e:
            KUBERNETES_AVAILABLE = False
            _LOGGER.error("Kubernetes package not available: %s", e)
            _LOGGER.debug("Python path (first 5 entries): %s", sys.path[:5])

        except Exception as e:
            KUBERNETES_AVAILABLE = False
            _LOGGER.error("Unexpected error importing kubernetes package: %s", e)

    return KUBERNETES_AVAILABLE


class KubernetesConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):  # type: ignore[call-arg]
    """Handle a config flow for Kubernetes."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        # Check if kubernetes package is available
        if not _ensure_kubernetes_imported():
            errors["base"] = "kubernetes_not_installed"
            _LOGGER.error("Kubernetes package is not installed")

        if user_input is not None and KUBERNETES_AVAILABLE:
            try:
                # Validate the connection
                await self._test_connection(user_input)

                # Add default values for missing fields
                user_input.setdefault(CONF_PORT, DEFAULT_PORT)
                user_input.setdefault(CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL)
                user_input.setdefault(CONF_CLUSTER_NAME, DEFAULT_CLUSTER_NAME)
                user_input.setdefault(
                    CONF_MONITOR_ALL_NAMESPACES, DEFAULT_MONITOR_ALL_NAMESPACES
                )
                user_input.setdefault(
                    CONF_SWITCH_UPDATE_INTERVAL, DEFAULT_SWITCH_UPDATE_INTERVAL
                )
                user_input.setdefault(
                    CONF_SCALE_VERIFICATION_TIMEOUT, DEFAULT_SCALE_VERIFICATION_TIMEOUT
                )
                user_input.setdefault(CONF_SCALE_COOLDOWN, DEFAULT_SCALE_COOLDOWN)

                # Add namespace if not monitoring all namespaces
                if not user_input.get(
                    CONF_MONITOR_ALL_NAMESPACES, DEFAULT_MONITOR_ALL_NAMESPACES
                ):
                    user_input.setdefault(CONF_NAMESPACE, DEFAULT_NAMESPACE)

                # Create unique ID for the config entry
                await self.async_set_unique_id(f"{user_input[CONF_CLUSTER_NAME]}")
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=user_input[CONF_NAME],
                    data=user_input,
                )
            except AbortFlow:
                # Re-raise AbortFlow exceptions to let them propagate
                raise
            except Exception as ex:  # pylint: disable=broad-except
                _LOGGER.error("Failed to connect to Kubernetes: %s", ex)
                errors["base"] = "cannot_connect"

        # Create schema with conditional namespace field
        schema = {
            vol.Required(CONF_NAME): str,
            vol.Required(CONF_HOST): str,
            vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
            vol.Optional(CONF_CLUSTER_NAME, default=DEFAULT_CLUSTER_NAME): str,
            vol.Optional(
                CONF_MONITOR_ALL_NAMESPACES, default=DEFAULT_MONITOR_ALL_NAMESPACES
            ): bool,
            vol.Required(CONF_API_TOKEN): str,
            vol.Optional(CONF_CA_CERT): str,
            vol.Optional(CONF_VERIFY_SSL, default=DEFAULT_VERIFY_SSL): bool,
            vol.Optional(
                CONF_SWITCH_UPDATE_INTERVAL, default=DEFAULT_SWITCH_UPDATE_INTERVAL
            ): int,
            vol.Optional(
                CONF_SCALE_VERIFICATION_TIMEOUT,
                default=DEFAULT_SCALE_VERIFICATION_TIMEOUT,
            ): int,
            vol.Optional(CONF_SCALE_COOLDOWN, default=DEFAULT_SCALE_COOLDOWN): int,
        }

        # Add namespace field only if not monitoring all namespaces
        if user_input is None or not user_input.get(
            CONF_MONITOR_ALL_NAMESPACES, DEFAULT_MONITOR_ALL_NAMESPACES
        ):
            schema[vol.Optional(CONF_NAMESPACE, default=DEFAULT_NAMESPACE)] = str

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(schema),
            errors=errors,
        )

    async def _test_connection(self, user_input: dict[str, Any]) -> None:  # noqa: C901
        """Test the connection to Kubernetes."""
        import asyncio

        # Check if kubernetes package is available
        if not _ensure_kubernetes_imported():
            raise ValueError("Kubernetes package is not installed")

        # Validate required fields
        if not user_input[CONF_HOST]:
            raise ValueError("Host is required")

        if not user_input[CONF_API_TOKEN]:
            raise ValueError("API token is required")

        # Create a test configuration
        if client is None:
            raise ValueError("Kubernetes client not available")
        configuration = client.Configuration()

        # Clean the host input - remove any protocol prefix
        host = user_input[CONF_HOST].strip()
        if host.startswith(("http://", "https://")):
            host = host.split("://", 1)[1]

        # Validate the cleaned host
        if not host:
            raise ValueError("Host cannot be empty")

        # Store the cleaned host value
        user_input[CONF_HOST] = host

        configuration.host = f"https://{host}:{user_input.get(CONF_PORT, DEFAULT_PORT)}"
        configuration.api_key = {
            "authorization": f"Bearer {user_input[CONF_API_TOKEN]}"
        }
        configuration.api_key_prefix = {"authorization": "Bearer"}
        configuration.verify_ssl = user_input.get(CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL)

        if user_input.get(CONF_CA_CERT):
            configuration.ssl_ca_cert = user_input[CONF_CA_CERT]

        # Create API client
        api_client = client.ApiClient(configuration)
        core_v1 = client.CoreV1Api(api_client)

        # Test the connection
        loop = asyncio.get_event_loop()
        try:
            await loop.run_in_executor(None, core_v1.get_api_resources)
            _LOGGER.info(
                "Successfully connected to Kubernetes API at %s", configuration.host
            )
        except ApiException as ex:  # type: ignore[misc]
            _LOGGER.error("API Exception during connection test: %s", ex)
            _LOGGER.error("Status: %s", ex.status)
            _LOGGER.error("Reason: %s", ex.reason)
            if ex.body:
                _LOGGER.error("Response body: %s", ex.body)

            # Fallback to aiohttp if kubernetes client fails
            _LOGGER.info("Trying fallback connection with aiohttp...")
            if await self._test_connection_aiohttp(user_input):
                _LOGGER.info(
                    "Successfully connected to Kubernetes API using aiohttp fallback"
                )
                return
            else:
                raise ValueError(f"Failed to connect to Kubernetes API: {ex.reason}")
        except Exception as ex:
            _LOGGER.error("Failed to test connection: %s", ex)
            # Fallback to aiohttp if kubernetes client fails
            _LOGGER.info("Trying fallback connection with aiohttp...")
            if await self._test_connection_aiohttp(user_input):
                _LOGGER.info(
                    "Successfully connected to Kubernetes API using aiohttp fallback"
                )
                return
            else:
                raise ValueError(f"Connection test failed: {str(ex)}")

    async def _test_connection_aiohttp(self, user_input: dict[str, Any]) -> bool:
        """Test the connection using aiohttp as fallback."""
        try:
            headers = {
                "Authorization": f"Bearer {user_input[CONF_API_TOKEN]}",
                "Accept": "application/json",
            }

            host = user_input[CONF_HOST]
            port = user_input.get(CONF_PORT, DEFAULT_PORT)

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://{host}:{port}/api/v1/",
                    headers=headers,
                    ssl=False,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status == 200:
                        _LOGGER.info(
                            "Successfully connected to Kubernetes API using aiohttp"
                        )
                        return True
                    else:
                        _LOGGER.error(
                            "aiohttp connection failed with status: %s", response.status
                        )
                        return False
        except Exception as ex:
            _LOGGER.error("aiohttp connection test failed: %s", ex)
            return False
