"""Config flow for Kubernetes integration."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol
from kubernetes import client, config
from kubernetes.client.rest import ApiException

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_API_TOKEN,
    CONF_CA_CERT,
    CONF_CLUSTER_NAME,
    CONF_MONITOR_ALL_NAMESPACES,
    CONF_NAMESPACE,
    CONF_VERIFY_SSL,
    CONF_SWITCH_UPDATE_INTERVAL,
    CONF_SCALE_VERIFICATION_TIMEOUT,
    CONF_SCALE_COOLDOWN,
    DEFAULT_CLUSTER_NAME,
    DEFAULT_MONITOR_ALL_NAMESPACES,
    DEFAULT_NAMESPACE,
    DEFAULT_PORT,
    DEFAULT_VERIFY_SSL,
    DEFAULT_SWITCH_UPDATE_INTERVAL,
    DEFAULT_SCALE_VERIFICATION_TIMEOUT,
    DEFAULT_SCALE_COOLDOWN,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class KubernetesConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Kubernetes."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            try:
                # Validate the connection
                await self._test_connection(user_input)

                # Create unique ID for the config entry
                await self.async_set_unique_id(f"{user_input[CONF_CLUSTER_NAME]}")
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=user_input[CONF_NAME],
                    data=user_input,
                )
            except Exception as ex:  # pylint: disable=broad-except
                _LOGGER.error("Failed to connect to Kubernetes: %s", ex)
                errors["base"] = "cannot_connect"

        # Create schema with conditional namespace field
        schema = {
            vol.Required(CONF_NAME): str,
            vol.Required(CONF_HOST): str,
            vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
            vol.Optional(CONF_CLUSTER_NAME, default=DEFAULT_CLUSTER_NAME): str,
            vol.Optional(CONF_MONITOR_ALL_NAMESPACES, default=DEFAULT_MONITOR_ALL_NAMESPACES): bool,
            vol.Required(CONF_API_TOKEN): str,
            vol.Optional(CONF_CA_CERT): str,
            vol.Optional(CONF_VERIFY_SSL, default=DEFAULT_VERIFY_SSL): bool,
            vol.Optional(CONF_SWITCH_UPDATE_INTERVAL, default=DEFAULT_SWITCH_UPDATE_INTERVAL): int,
            vol.Optional(CONF_SCALE_VERIFICATION_TIMEOUT, default=DEFAULT_SCALE_VERIFICATION_TIMEOUT): int,
            vol.Optional(CONF_SCALE_COOLDOWN, default=DEFAULT_SCALE_COOLDOWN): int,
        }

        # Add namespace field only if not monitoring all namespaces
        if user_input is None or not user_input.get(CONF_MONITOR_ALL_NAMESPACES, DEFAULT_MONITOR_ALL_NAMESPACES):
            schema[vol.Optional(CONF_NAMESPACE, default=DEFAULT_NAMESPACE)] = str

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(schema),
            errors=errors,
        )

    async def _test_connection(self, user_input: dict[str, Any]) -> None:
        """Test the connection to Kubernetes."""
        import asyncio

        # Validate required fields
        if not user_input[CONF_HOST]:
            raise ValueError("Host is required")

        if not user_input[CONF_API_TOKEN]:
            raise ValueError("API token is required")

        # Create a test configuration
        configuration = client.Configuration()

        # Clean the host input - remove any protocol prefix
        host = user_input[CONF_HOST].strip()
        if host.startswith(('http://', 'https://')):
            host = host.split('://', 1)[1]

        # Validate the cleaned host
        if not host:
            raise ValueError("Host cannot be empty")

        # Store the cleaned host value
        user_input[CONF_HOST] = host

        configuration.host = f"https://{host}:{user_input.get(CONF_PORT, DEFAULT_PORT)}"
        configuration.api_key = {"authorization": f"Bearer {user_input[CONF_API_TOKEN]}"}
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
            _LOGGER.info("Successfully connected to Kubernetes API at %s", configuration.host)
        except ApiException as ex:
            _LOGGER.error("API Exception during connection test: %s", ex)
            _LOGGER.error("Status: %s", ex.status)
            _LOGGER.error("Reason: %s", ex.reason)
            if ex.body:
                _LOGGER.error("Response body: %s", ex.body)

            # Fallback to aiohttp if kubernetes client fails
            _LOGGER.info("Trying fallback connection with aiohttp...")
            if await self._test_connection_aiohttp(user_input):
                _LOGGER.info("Successfully connected to Kubernetes API using aiohttp fallback")
                return
            else:
                raise ValueError(f"Failed to connect to Kubernetes API: {ex.reason}")
        except Exception as ex:
            _LOGGER.error("Failed to test connection: %s", ex)
            # Fallback to aiohttp if kubernetes client fails
            _LOGGER.info("Trying fallback connection with aiohttp...")
            if await self._test_connection_aiohttp(user_input):
                _LOGGER.info("Successfully connected to Kubernetes API using aiohttp fallback")
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
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        _LOGGER.info("Successfully connected to Kubernetes API using aiohttp")
                        return True
                    else:
                        _LOGGER.error("aiohttp connection failed with status: %s", response.status)
                        return False
        except Exception as ex:
            _LOGGER.error("aiohttp connection test failed: %s", ex)
            return False
