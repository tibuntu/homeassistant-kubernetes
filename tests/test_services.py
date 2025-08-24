"""Tests for the Kubernetes services."""

from unittest.mock import ANY, AsyncMock, MagicMock, patch

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
import pytest
import voluptuous as vol

from custom_components.kubernetes.const import (
    ATTR_CRONJOB_NAME,
    ATTR_CRONJOB_NAMES,
    ATTR_DEPLOYMENT_NAME,
    ATTR_DEPLOYMENT_NAMES,
    ATTR_NAMESPACE,
    ATTR_REPLICAS,
    ATTR_STATEFULSET_NAME,
    ATTR_STATEFULSET_NAMES,
    DOMAIN,
    SERVICE_CREATE_CRONJOB_JOB,
    SERVICE_RESUME_CRONJOB,
    SERVICE_SCALE_DEPLOYMENT,
    SERVICE_SCALE_STATEFULSET,
    SERVICE_START_DEPLOYMENT,
    SERVICE_START_STATEFULSET,
    SERVICE_STOP_DEPLOYMENT,
    SERVICE_STOP_STATEFULSET,
    SERVICE_SUSPEND_CRONJOB,
    SERVICE_TRIGGER_CRONJOB,
)
from custom_components.kubernetes.services import (
    async_setup_services,
    async_unload_services,
)


@pytest.fixture
def mock_hass():
    """Mock Home Assistant instance."""
    hass = MagicMock(spec=HomeAssistant)
    hass.services = MagicMock()
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
            SERVICE_SCALE_DEPLOYMENT,
            SERVICE_START_DEPLOYMENT,
            SERVICE_STOP_DEPLOYMENT,
            SERVICE_SCALE_STATEFULSET,
            SERVICE_START_STATEFULSET,
            SERVICE_STOP_STATEFULSET,
            SERVICE_TRIGGER_CRONJOB,
            SERVICE_SUSPEND_CRONJOB,
            SERVICE_RESUME_CRONJOB,
            SERVICE_CREATE_CRONJOB_JOB,
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
            SERVICE_SCALE_DEPLOYMENT,
            SERVICE_START_DEPLOYMENT,
            SERVICE_STOP_DEPLOYMENT,
            SERVICE_SCALE_STATEFULSET,
            SERVICE_START_STATEFULSET,
            SERVICE_STOP_STATEFULSET,
            SERVICE_TRIGGER_CRONJOB,
            SERVICE_SUSPEND_CRONJOB,
            SERVICE_RESUME_CRONJOB,
            SERVICE_CREATE_CRONJOB_JOB,
        ]

        for service in unregistered_services:
            mock_hass.services.async_remove.assert_any_call(DOMAIN, service)


class TestCronJobServices:
    """Test CronJob service functions."""

    async def test_suspend_cronjob_success(self, mock_hass, mock_client):
        """Test successful CronJob suspension."""
        with patch(
            "custom_components.kubernetes.kubernetes_client.KubernetesClient"
        ) as mock_client_class:
            mock_client_class.return_value = mock_client

            # Get the service function
            await async_setup_services(mock_hass)

            # Find the suspend_cronjob service function
            service_func = None
            for call_args in mock_hass.services.async_register.call_args_list:
                if call_args[0][1] == SERVICE_SUSPEND_CRONJOB:
                    service_func = call_args[0][2]
                    break

            assert service_func is not None, "Service function not found"

            # Create a mock call object
            mock_call = MagicMock()
            mock_call.data = {
                ATTR_CRONJOB_NAME: "test-cronjob",
                ATTR_NAMESPACE: "default",
            }

            # Execute service
            await service_func(mock_call)

            # Verify
            mock_client.suspend_cronjob.assert_called_once_with(
                "test-cronjob", "default"
            )

    async def test_suspend_cronjob_failure(self, mock_hass, mock_client):
        """Test failed CronJob suspension."""
        mock_client.suspend_cronjob.return_value = {
            "success": False,
            "error": "CronJob not found",
        }

        with patch(
            "custom_components.kubernetes.kubernetes_client.KubernetesClient"
        ) as mock_client_class:
            mock_client_class.return_value = mock_client

            # Get the service function
            await async_setup_services(mock_hass)
            service_func = None
            for call_args in mock_hass.services.async_register.call_args_list:
                if call_args[0][1] == SERVICE_SUSPEND_CRONJOB:
                    service_func = call_args[0][2]
                    break

            assert service_func is not None, "Service function not found"

            # Create a mock call object
            mock_call = MagicMock()
            mock_call.data = {
                ATTR_CRONJOB_NAME: "test-cronjob",
                ATTR_NAMESPACE: "default",
            }

            # Execute service
            await service_func(mock_call)

            # Verify
            mock_client.suspend_cronjob.assert_called_once_with(
                "test-cronjob", "default"
            )

    async def test_resume_cronjob_success(self, mock_hass, mock_client):
        """Test successful CronJob resume."""
        with patch(
            "custom_components.kubernetes.kubernetes_client.KubernetesClient"
        ) as mock_client_class:
            mock_client_class.return_value = mock_client

            # Get the service function
            await async_setup_services(mock_hass)
            service_func = None
            for call_args in mock_hass.services.async_register.call_args_list:
                if call_args[0][1] == SERVICE_RESUME_CRONJOB:
                    service_func = call_args[0][2]
                    break

            assert service_func is not None, "Service function not found"

            # Create a mock call object
            mock_call = MagicMock()
            mock_call.data = {
                ATTR_CRONJOB_NAME: "test-cronjob",
                ATTR_NAMESPACE: "default",
            }

            # Execute service
            await service_func(mock_call)

            # Verify
            mock_client.resume_cronjob.assert_called_once_with(
                "test-cronjob", "default"
            )

    async def test_resume_cronjob_failure(self, mock_hass, mock_client):
        """Test failed CronJob resume."""
        mock_client.resume_cronjob.return_value = {
            "success": False,
            "error": "Permission denied",
        }

        with patch(
            "custom_components.kubernetes.kubernetes_client.KubernetesClient"
        ) as mock_client_class:
            mock_client_class.return_value = mock_client

            # Get the service function
            await async_setup_services(mock_hass)
            service_func = None
            for call_args in mock_hass.services.async_register.call_args_list:
                if call_args[0][1] == SERVICE_RESUME_CRONJOB:
                    service_func = call_args[0][2]
                    break

            assert service_func is not None, "Service function not found"

            # Create a mock call object
            mock_call = MagicMock()
            mock_call.data = {
                ATTR_CRONJOB_NAME: "test-cronjob",
                ATTR_NAMESPACE: "default",
            }

            # Execute service
            await service_func(mock_call)

            # Verify
            mock_client.resume_cronjob.assert_called_once_with(
                "test-cronjob", "default"
            )

    async def test_create_cronjob_job_success(self, mock_hass, mock_client):
        """Test successful CronJob job creation."""
        with patch(
            "custom_components.kubernetes.kubernetes_client.KubernetesClient"
        ) as mock_client_class:
            mock_client_class.return_value = mock_client

            # Get the service function
            await async_setup_services(mock_hass)
            service_func = None
            for call_args in mock_hass.services.async_register.call_args_list:
                if call_args[0][1] == SERVICE_CREATE_CRONJOB_JOB:
                    service_func = call_args[0][2]
                    break

            assert service_func is not None, "Service function not found"

            # Create a mock call object
            mock_call = MagicMock()
            mock_call.data = {
                ATTR_CRONJOB_NAME: "test-cronjob",
                ATTR_NAMESPACE: "default",
            }

            # Execute service
            await service_func(mock_call)

            # Verify
            mock_client.trigger_cronjob.assert_called_once_with(
                "test-cronjob", "default"
            )

    async def test_create_cronjob_job_failure(self, mock_hass, mock_client):
        """Test failed CronJob job creation."""
        mock_client.trigger_cronjob.return_value = {
            "success": False,
            "error": "CronJob not found",
        }

        with patch(
            "custom_components.kubernetes.kubernetes_client.KubernetesClient"
        ) as mock_client_class:
            mock_client_class.return_value = mock_client

            # Get the service function
            await async_setup_services(mock_hass)
            service_func = None
            for call_args in mock_hass.services.async_register.call_args_list:
                if call_args[0][1] == SERVICE_CREATE_CRONJOB_JOB:
                    service_func = call_args[0][2]
                    break

            assert service_func is not None, "Service function not found"

            # Create a mock call object
            mock_call = MagicMock()
            mock_call.data = {
                ATTR_CRONJOB_NAME: "test-cronjob",
                ATTR_NAMESPACE: "default",
            }

            # Execute service
            await service_func(mock_call)

            # Verify
            mock_client.trigger_cronjob.assert_called_once_with(
                "test-cronjob", "default"
            )

    async def test_suspend_cronjob_multiple(self, mock_hass, mock_client):
        """Test suspending multiple CronJobs."""
        with patch(
            "custom_components.kubernetes.kubernetes_client.KubernetesClient"
        ) as mock_client_class:
            mock_client_class.return_value = mock_client

            # Get the service function
            await async_setup_services(mock_hass)
            service_func = None
            for call_args in mock_hass.services.async_register.call_args_list:
                if call_args[0][1] == SERVICE_SUSPEND_CRONJOB:
                    service_func = call_args[0][2]
                    break

            assert service_func is not None, "Service function not found"

            # Create a mock call object
            mock_call = MagicMock()
            mock_call.data = {
                ATTR_CRONJOB_NAMES: ["cronjob1", "cronjob2"],
                ATTR_NAMESPACE: "default",
            }

            # Execute service
            await service_func(mock_call)

            # Verify both CronJobs were suspended
            assert mock_client.suspend_cronjob.call_count == 2
            mock_client.suspend_cronjob.assert_any_call("cronjob1", "default")
            mock_client.suspend_cronjob.assert_any_call("cronjob2", "default")

    async def test_resume_cronjob_multiple(self, mock_hass, mock_client):
        """Test resuming multiple CronJobs."""
        with patch(
            "custom_components.kubernetes.kubernetes_client.KubernetesClient"
        ) as mock_client_class:
            mock_client_class.return_value = mock_client

            # Get the service function
            await async_setup_services(mock_hass)
            service_func = None
            for call_args in mock_hass.services.async_register.call_args_list:
                if call_args[0][1] == SERVICE_RESUME_CRONJOB:
                    service_func = call_args[0][2]
                    break

            assert service_func is not None, "Service function not found"

            # Create a mock call object
            mock_call = MagicMock()
            mock_call.data = {
                ATTR_CRONJOB_NAMES: ["cronjob1", "cronjob2"],
                ATTR_NAMESPACE: "default",
            }

            # Execute service
            await service_func(mock_call)

            # Verify both CronJobs were resumed
            assert mock_client.resume_cronjob.call_count == 2
            mock_client.resume_cronjob.assert_any_call("cronjob1", "default")
            mock_client.resume_cronjob.assert_any_call("cronjob2", "default")

    async def test_create_cronjob_job_multiple(self, mock_hass, mock_client):
        """Test creating jobs from multiple CronJobs."""
        with patch(
            "custom_components.kubernetes.kubernetes_client.KubernetesClient"
        ) as mock_client_class:
            mock_client_class.return_value = mock_client

            # Get the service function
            await async_setup_services(mock_hass)
            service_func = None
            for call_args in mock_hass.services.async_register.call_args_list:
                if call_args[0][1] == SERVICE_CREATE_CRONJOB_JOB:
                    service_func = call_args[0][2]
                    break

            assert service_func is not None, "Service function not found"

            # Create a mock call object
            mock_call = MagicMock()
            mock_call.data = {
                ATTR_CRONJOB_NAMES: ["cronjob1", "cronjob2"],
                ATTR_NAMESPACE: "default",
            }

            # Execute service
            await service_func(mock_call)

            # Verify jobs were created from both CronJobs
            assert mock_client.trigger_cronjob.call_count == 2
            mock_client.trigger_cronjob.assert_any_call("cronjob1", "default")
            mock_client.trigger_cronjob.assert_any_call("cronjob2", "default")

    async def test_suspend_cronjob_no_kubernetes_data(self, mock_hass):
        """Test CronJob suspension when no Kubernetes data is available."""
        # Setup mock_hass without Kubernetes data
        mock_hass.data = {}

        with patch(
            "custom_components.kubernetes.kubernetes_client.KubernetesClient"
        ) as mock_client_class:
            mock_client_class.return_value = MagicMock()

            # Get the service function
            await async_setup_services(mock_hass)
            service_func = None
            for call_args in mock_hass.services.async_register.call_args_list:
                if call_args[0][1] == SERVICE_SUSPEND_CRONJOB:
                    service_func = call_args[0][2]
                    break

            assert service_func is not None, "Service function not found"

            # Create a mock call object
            mock_call = MagicMock()
            mock_call.data = {
                ATTR_CRONJOB_NAME: "test-cronjob",
                ATTR_NAMESPACE: "default",
            }

            # Execute service
            await service_func(mock_call)

            # Verify no client calls were made
            mock_client_class.assert_not_called()

    async def test_suspend_cronjob_no_cronjob_names(self, mock_hass, mock_client):
        """Test CronJob suspension with no valid CronJob names."""
        with patch(
            "custom_components.kubernetes.kubernetes_client.KubernetesClient"
        ) as mock_client_class:
            mock_client_class.return_value = mock_client

            # Get the service function
            await async_setup_services(mock_hass)
            service_func = None
            for call_args in mock_hass.services.async_register.call_args_list:
                if call_args[0][1] == SERVICE_SUSPEND_CRONJOB:
                    service_func = call_args[0][2]
                    break

            assert service_func is not None, "Service function not found"

            # Create a mock call object
            mock_call = MagicMock()
            mock_call.data = {
                ATTR_NAMESPACE: "default",
            }

            # Execute service
            await service_func(mock_call)

            # Verify no client calls were made
            mock_client.suspend_cronjob.assert_not_called()
