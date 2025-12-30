"""Tests for the Kubernetes services."""

import os
from unittest.mock import ANY, AsyncMock, MagicMock, patch

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
import pytest
import voluptuous as vol
import yaml

from custom_components.kubernetes.const import (
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
from custom_components.kubernetes.services import (
    _validate_entity_workload_type,
    async_setup_services,
    async_unload_services,
)


@pytest.fixture
def mock_hass():
    """Mock Home Assistant instance."""
    hass = MagicMock(spec=HomeAssistant)
    hass.services = MagicMock()
    hass.states = MagicMock()
    hass.data = {
        DOMAIN: {
            "test-entry-id": {
                "config": {
                    "host": "test-cluster.example.com",
                    "port": 6443,
                    "api_token": "test-token",
                    "namespace": "default",
                    "verify_ssl": True,
                }
            }
        }
    }
    return hass


@pytest.fixture
def mock_client():
    """Mock Kubernetes client."""
    client = MagicMock()
    client.scale_deployment = AsyncMock(return_value=True)
    client.scale_statefulset = AsyncMock(return_value=True)
    client.stop_deployment = AsyncMock(return_value=True)
    client.stop_statefulset = AsyncMock(return_value=True)
    client.start_deployment = AsyncMock(return_value=True)
    client.start_statefulset = AsyncMock(return_value=True)
    client.trigger_cronjob = AsyncMock(
        return_value={"success": True, "job_name": "test-job-123"}
    )
    client.suspend_cronjob = AsyncMock(return_value={"success": True})
    client.resume_cronjob = AsyncMock(return_value={"success": True})
    return client


class TestServiceRegistration:
    """Test service registration and unregistration."""

    async def test_async_setup_services(self, mock_hass):
        """Test that all services are registered."""
        with patch(
            "custom_components.kubernetes.kubernetes_client.KubernetesClient"
        ) as mock_client_class:
            mock_client_class.return_value = MagicMock()
            await async_setup_services(mock_hass)

        # Verify all services are registered
        registered_services = [
            SERVICE_SCALE_WORKLOAD,
            SERVICE_START_WORKLOAD,
            SERVICE_STOP_WORKLOAD,
        ]

        for service in registered_services:
            mock_hass.services.async_register.assert_any_call(
                DOMAIN, service, ANY, schema=ANY
            )

    async def test_async_unload_services(self, mock_hass):
        """Test that all services are unregistered."""
        await async_unload_services(mock_hass)

        # Verify all services are unregistered
        unregistered_services = [
            SERVICE_SCALE_WORKLOAD,
            SERVICE_START_WORKLOAD,
            SERVICE_STOP_WORKLOAD,
        ]

        for service in unregistered_services:
            mock_hass.services.async_remove.assert_any_call(DOMAIN, service)


class TestGenericWorkloadServices:
    """Test generic workload services (scale_workload, start_workload, stop_workload)."""

    async def test_scale_workload_deployment(self, mock_hass, mock_client):
        """Test scaling a deployment using the generic scale_workload service."""
        with patch(
            "custom_components.kubernetes.kubernetes_client.KubernetesClient"
        ) as mock_client_class:
            mock_client_class.return_value = mock_client

            await async_setup_services(mock_hass)

            # Find the scale_workload service function
            service_func = None
            for call_args in mock_hass.services.async_register.call_args_list:
                if call_args[0][1] == SERVICE_SCALE_WORKLOAD:
                    service_func = call_args[0][2]
                    break

            assert service_func is not None, "Service function not found"

            # Mock entity state
            mock_hass.states.get.return_value = MagicMock(
                attributes={
                    ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_DEPLOYMENT,
                    "namespace": "default",
                    "deployment_name": "test-deployment",
                }
            )

            # Create a mock call object
            mock_call = MagicMock()
            mock_call.data = {
                ATTR_WORKLOAD_NAME: "switch.test_deployment",
                ATTR_REPLICAS: 3,
                ATTR_NAMESPACE: "default",
            }

            # Execute service
            await service_func(mock_call)

            # Verify
            mock_client.scale_deployment.assert_called_once_with(
                "test-deployment", 3, "default"
            )

    async def test_start_workload_cronjob(self, mock_hass, mock_client):
        """Test starting a CronJob using the generic start_workload service."""
        with patch(
            "custom_components.kubernetes.kubernetes_client.KubernetesClient"
        ) as mock_client_class:
            mock_client_class.return_value = mock_client
            mock_client.trigger_cronjob.return_value = {
                "success": True,
                "job_name": "test-job-123",
            }

            await async_setup_services(mock_hass)

            # Find the start_workload service function
            service_func = None
            for call_args in mock_hass.services.async_register.call_args_list:
                if call_args[0][1] == SERVICE_START_WORKLOAD:
                    service_func = call_args[0][2]
                    break

            assert service_func is not None, "Service function not found"

            # Mock entity state
            mock_hass.states.get.return_value = MagicMock(
                attributes={
                    ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_CRONJOB,
                    "namespace": "default",
                    "cronjob_name": "test-cronjob",
                }
            )

            # Create a mock call object
            mock_call = MagicMock()
            mock_call.data = {
                ATTR_WORKLOAD_NAME: "switch.test_cronjob",
                ATTR_NAMESPACE: "default",
            }

            # Execute service
            await service_func(mock_call)

            # Verify
            mock_client.trigger_cronjob.assert_called_once_with(
                "test-cronjob", "default"
            )

    async def test_stop_workload_statefulset(self, mock_hass, mock_client):
        """Test stopping a StatefulSet using the generic stop_workload service."""
        with patch(
            "custom_components.kubernetes.kubernetes_client.KubernetesClient"
        ) as mock_client_class:
            mock_client_class.return_value = mock_client

            await async_setup_services(mock_hass)

            # Find the stop_workload service function
            service_func = None
            for call_args in mock_hass.services.async_register.call_args_list:
                if call_args[0][1] == SERVICE_STOP_WORKLOAD:
                    service_func = call_args[0][2]
                    break

            assert service_func is not None, "Service function not found"

            # Mock entity state
            mock_hass.states.get.return_value = MagicMock(
                attributes={
                    ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_STATEFULSET,
                    "namespace": "default",
                    "statefulset_name": "test-statefulset",
                }
            )

            # Create a mock call object
            mock_call = MagicMock()
            mock_call.data = {
                ATTR_WORKLOAD_NAME: "switch.test_statefulset",
                ATTR_NAMESPACE: "default",
            }

            # Execute service
            await service_func(mock_call)

            # Verify
            mock_client.stop_statefulset.assert_called_once_with(
                "test-statefulset", "default"
            )

    async def test_stop_workload_cronjob_ignored(self, mock_hass, mock_client):
        """Test that stop_workload ignores CronJobs."""
        with patch(
            "custom_components.kubernetes.kubernetes_client.KubernetesClient"
        ) as mock_client_class:
            mock_client_class.return_value = mock_client

            await async_setup_services(mock_hass)

            # Find the stop_workload service function
            service_func = None
            for call_args in mock_hass.services.async_register.call_args_list:
                if call_args[0][1] == SERVICE_STOP_WORKLOAD:
                    service_func = call_args[0][2]
                    break

            assert service_func is not None, "Service function not found"

            # Mock entity state for CronJob
            mock_hass.states.get.return_value = MagicMock(
                attributes={
                    ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_CRONJOB,
                    "namespace": "default",
                    "cronjob_name": "test-cronjob",
                }
            )

            # Create a mock call object
            mock_call = MagicMock()
            mock_call.data = {
                ATTR_WORKLOAD_NAME: "switch.test_cronjob",
                ATTR_NAMESPACE: "default",
            }

            # Execute service
            await service_func(mock_call)

            # Verify that suspend_cronjob was NOT called
            mock_client.suspend_cronjob.assert_not_called()


class TestServiceSelectorConfiguration:
    """Test that service selectors are correctly configured."""

    def test_services_yaml_selector_structure(self):
        """Test that all entity selectors have the correct structure."""
        services_yaml_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "custom_components",
            "kubernetes",
            "services.yaml",
        )

        with open(services_yaml_path) as f:
            services_config = yaml.safe_load(f)

        # Check that all services with entity selectors have the correct structure
        for service_name, service_config in services_config.items():
            fields = service_config.get("fields", {})
            for field_name, field_config in fields.items():
                selector_config = field_config.get("selector", {})

                # Check entity selector
                if "entity" in selector_config:
                    entity_selector = selector_config["entity"]
                    assert (
                        "domain" in entity_selector
                    ), f"{service_name}.{field_name} entity selector missing domain"
                    assert (
                        entity_selector["domain"] == "switch"
                    ), f"{service_name}.{field_name} entity selector has wrong domain"
                    assert (
                        "integration" in entity_selector
                    ), f"{service_name}.{field_name} entity selector missing integration"
                    assert (
                        entity_selector["integration"] == DOMAIN
                    ), f"{service_name}.{field_name} entity selector has wrong integration"

                # Check target selector (for multi-select fields)
                if "target" in selector_config:
                    target_selector = selector_config["target"]
                    assert (
                        "entity" in target_selector
                    ), f"{service_name}.{field_name} target selector missing entity"
                    entity_selector = target_selector["entity"]
                    assert (
                        "domain" in entity_selector
                    ), f"{service_name}.{field_name} target entity selector missing domain"
                    assert (
                        entity_selector["domain"] == "switch"
                    ), f"{service_name}.{field_name} target entity selector has wrong domain"
                    assert (
                        "integration" in entity_selector
                    ), f"{service_name}.{field_name} target entity selector missing integration"
                    assert (
                        entity_selector["integration"] == DOMAIN
                    ), f"{service_name}.{field_name} target entity selector has wrong integration"
