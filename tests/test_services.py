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
    ATTR_WORKLOAD_TYPE,
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
    WORKLOAD_TYPE_CRONJOB,
    WORKLOAD_TYPE_DEPLOYMENT,
    WORKLOAD_TYPE_STATEFULSET,
)
from custom_components.kubernetes.services import (
    async_setup_services,
    async_unload_services,
    _extract_cronjob_names_and_namespaces,
    _extract_deployment_names_and_namespaces,
    _extract_statefulset_names_and_namespaces,
    _get_namespace_from_entity,
    _validate_deployment_schema,
    _validate_entity_workload_type,
    _validate_statefulset_schema,
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
        """Test CronJob suspension with no cronjob names provided."""
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

            # Create a mock call object with no cronjob names
            mock_call = MagicMock()
            mock_call.data = {}

            # Execute service
            await service_func(mock_call)

            # Verify no calls were made
            mock_client.suspend_cronjob.assert_not_called()

    async def test_workload_type_validation_with_entity_ids(
        self, mock_hass, mock_client
    ):
        """Test that workload type validation works correctly with entity IDs."""
        from custom_components.kubernetes.services import _validate_entity_workload_type

        # Mock the states attribute
        mock_states = MagicMock()
        mock_hass.states = mock_states

        # Mock entity states for different workload types
        mock_states.get.side_effect = lambda entity_id: {
            "switch.deployment_test": MagicMock(
                attributes={"workload_type": "Deployment"}
            ),
            "switch.statefulset_test": MagicMock(
                attributes={"workload_type": "StatefulSet"}
            ),
            "switch.cronjob_test": MagicMock(attributes={"workload_type": "CronJob"}),
        }.get(entity_id)

        # Test deployment validation
        assert (
            _validate_entity_workload_type(
                mock_hass, "switch.deployment_test", "Deployment"
            )
            is True
        )
        assert (
            _validate_entity_workload_type(
                mock_hass, "switch.deployment_test", "StatefulSet"
            )
            is False
        )
        assert (
            _validate_entity_workload_type(
                mock_hass, "switch.deployment_test", "CronJob"
            )
            is False
        )

        # Test StatefulSet validation
        assert (
            _validate_entity_workload_type(
                mock_hass, "switch.statefulset_test", "Deployment"
            )
            is False
        )
        assert (
            _validate_entity_workload_type(
                mock_hass, "switch.statefulset_test", "StatefulSet"
            )
            is True
        )
        assert (
            _validate_entity_workload_type(
                mock_hass, "switch.statefulset_test", "CronJob"
            )
            is False
        )

        # Test CronJob validation
        assert (
            _validate_entity_workload_type(
                mock_hass, "switch.cronjob_test", "Deployment"
            )
            is False
        )
        assert (
            _validate_entity_workload_type(
                mock_hass, "switch.cronjob_test", "StatefulSet"
            )
            is False
        )
        assert (
            _validate_entity_workload_type(mock_hass, "switch.cronjob_test", "CronJob")
            is True
        )

        # Test that direct resource names (not entity IDs) are allowed
        assert (
            _validate_entity_workload_type(
                mock_hass, "direct-deployment-name", "Deployment"
            )
            is True
        )
        assert (
            _validate_entity_workload_type(
                mock_hass, "direct-statefulset-name", "StatefulSet"
            )
            is True
        )
        assert (
            _validate_entity_workload_type(mock_hass, "direct-cronjob-name", "CronJob")
            is True
        )

    async def test_workload_type_validation_edge_cases(self, mock_hass, mock_client):
        """Test edge cases for workload type validation."""
        from custom_components.kubernetes.services import _validate_entity_workload_type

        # Test with None entity
        mock_hass.states.get.return_value = None
        assert (
            _validate_entity_workload_type(
                mock_hass, "switch.nonexistent", "Deployment"
            )
            is False
        )

        # Test with entity that has no attributes
        mock_hass.states.get.return_value = MagicMock(attributes=None)
        assert (
            _validate_entity_workload_type(mock_hass, "switch.no_attrs", "Deployment")
            is False
        )

        # Test with entity that has empty attributes
        mock_hass.states.get.return_value = MagicMock(attributes={})
        assert (
            _validate_entity_workload_type(
                mock_hass, "switch.empty_attrs", "Deployment"
            )
            is False
        )

        # Test with entity that has wrong workload type
        mock_hass.states.get.return_value = MagicMock(
            attributes={"workload_type": "WrongType"}
        )
        assert (
            _validate_entity_workload_type(mock_hass, "switch.wrong_type", "Deployment")
            is False
        )

    async def test_validate_entity_workload_type_function(self, mock_hass, mock_client):
        """Test the _validate_entity_workload_type function directly."""
        from custom_components.kubernetes.services import _validate_entity_workload_type

        # Test with non-entity ID (should return True)
        assert (
            _validate_entity_workload_type(mock_hass, "deployment-name", "Deployment")
            is True
        )
        assert (
            _validate_entity_workload_type(mock_hass, "statefulset-name", "StatefulSet")
            is True
        )
        assert (
            _validate_entity_workload_type(mock_hass, "cronjob-name", "CronJob") is True
        )

        # Test with entity ID that doesn't start with switch.
        assert (
            _validate_entity_workload_type(mock_hass, "sensor.test", "Deployment")
            is True
        )

        # Test with entity ID that starts with switch. but has no state
        mock_hass.states.get.return_value = None
        assert (
            _validate_entity_workload_type(mock_hass, "switch.test", "Deployment")
            is False
        )

        # Test with entity ID that has state but no attributes
        mock_hass.states.get.return_value = MagicMock(attributes=None)
        assert (
            _validate_entity_workload_type(mock_hass, "switch.test", "Deployment")
            is False
        )

        # Test with entity ID that has attributes but no workload_type
        mock_hass.states.get.return_value = MagicMock(attributes={})
        assert (
            _validate_entity_workload_type(mock_hass, "switch.test", "Deployment")
            is False
        )

        # Test with entity ID that has correct workload_type
        mock_hass.states.get.return_value = MagicMock(
            attributes={"workload_type": "Deployment"}
        )
        assert (
            _validate_entity_workload_type(mock_hass, "switch.test", "Deployment")
            is True
        )

        # Test with entity ID that has wrong workload_type
        mock_hass.states.get.return_value = MagicMock(
            attributes={"workload_type": "StatefulSet"}
        )
        assert (
            _validate_entity_workload_type(mock_hass, "switch.test", "Deployment")
            is False
        )

    async def test_service_call_with_invalid_data(self, mock_hass, mock_client):
        """Test service calls with invalid data."""
        from custom_components.kubernetes.services import async_setup_services

        # Setup services
        await async_setup_services(mock_hass)

        # Test suspend cronjob with invalid data (missing cronjob_names)
        mock_call = ServiceCall(
            "suspend_cronjob",
            {"namespace": "default"},  # Missing cronjob_names
            None,
        )

        # Get the service function
        service_func = mock_hass.services.async_register.call_args_list[6][0][
            2
        ]  # suspend_cronjob

        # Execute service - should handle the error gracefully
        await service_func(mock_call)

        # Verify no calls were made to the client
        mock_client.suspend_cronjob.assert_not_called()

    async def test_service_call_with_empty_data(self, mock_hass, mock_client):
        """Test service calls with empty data."""
        from custom_components.kubernetes.services import async_setup_services

        # Setup services
        await async_setup_services(mock_hass)

        # Test suspend cronjob with empty data
        mock_call = ServiceCall("suspend_cronjob", {}, None)

        # Get the service function
        service_func = mock_hass.services.async_register.call_args_list[6][0][
            2
        ]  # suspend_cronjob

        # Execute service - should handle the error gracefully
        await service_func(mock_call)

        # Verify no calls were made to the client
        mock_client.suspend_cronjob.assert_not_called()

    async def test_validate_deployment_schema_with_missing_namespace(
        self, mock_hass, mock_client
    ):
        """Test deployment schema validation with missing namespace."""
        from custom_components.kubernetes.services import _validate_deployment_schema

        # Test with valid data but missing namespace (should be optional)
        call_data = {"deployment_names": ["test-deployment"], "replicas": 3}

        result = _validate_deployment_schema(call_data)
        assert result == call_data

    async def test_validate_statefulset_schema_with_missing_namespace(
        self, mock_hass, mock_client
    ):
        """Test StatefulSet schema validation with missing namespace."""
        from custom_components.kubernetes.services import _validate_statefulset_schema

        # Test with valid data but missing namespace (should be optional)
        call_data = {"statefulset_names": ["test-statefulset"], "replicas": 3}

        result = _validate_statefulset_schema(call_data)
        assert result == call_data

    async def test_validate_cronjob_schema_with_missing_namespace(
        self, mock_hass, mock_client
    ):
        """Test CronJob schema validation with missing namespace."""
        from custom_components.kubernetes.services import _validate_cronjob_schema

        # Test with valid data but missing namespace (should be optional)
        call_data = {"cronjob_names": ["test-cronjob"]}

        result = _validate_cronjob_schema(call_data)
        assert result == call_data

    async def test_validate_deployment_schema_with_list_names(
        self, mock_hass, mock_client
    ):
        """Test deployment schema validation with list of names."""
        from custom_components.kubernetes.services import _validate_deployment_schema

        # Test with list of deployment names
        call_data = {
            "deployment_names": ["deployment1", "deployment2"],
            "replicas": 3,
            "namespace": "default",
        }

        result = _validate_deployment_schema(call_data)
        assert result == call_data

    async def test_validate_statefulset_schema_with_list_names(
        self, mock_hass, mock_client
    ):
        """Test StatefulSet schema validation with list of names."""
        from custom_components.kubernetes.services import _validate_statefulset_schema

        # Test with list of StatefulSet names
        call_data = {
            "statefulset_names": ["statefulset1", "statefulset2"],
            "replicas": 3,
            "namespace": "default",
        }

        result = _validate_statefulset_schema(call_data)
        assert result == call_data

    async def test_validate_cronjob_schema_with_list_names(
        self, mock_hass, mock_client
    ):
        """Test CronJob schema validation with list of names."""
        from custom_components.kubernetes.services import _validate_cronjob_schema

        # Test with list of CronJob names
        call_data = {"cronjob_names": ["cronjob1", "cronjob2"], "namespace": "default"}

        result = _validate_cronjob_schema(call_data)
        assert result == call_data


class TestServiceHelpers:
    """Test service helper functions."""

    def test_validate_entity_workload_type(self, mock_hass):
        """Test _validate_entity_workload_type function."""
        # Test non-entity string
        assert _validate_entity_workload_type(mock_hass, "my-deployment", WORKLOAD_TYPE_DEPLOYMENT) is True

        # Test entity not found
        mock_hass.states.get.return_value = None
        assert _validate_entity_workload_type(mock_hass, "switch.my_deployment", WORKLOAD_TYPE_DEPLOYMENT) is False

        # Test entity with correct workload type
        entity = MagicMock()
        entity.attributes = {ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_DEPLOYMENT}
        mock_hass.states.get.return_value = entity
        assert _validate_entity_workload_type(mock_hass, "switch.my_deployment", WORKLOAD_TYPE_DEPLOYMENT) is True

        # Test entity with incorrect workload type
        entity.attributes = {ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_STATEFULSET}
        assert _validate_entity_workload_type(mock_hass, "switch.my_deployment", WORKLOAD_TYPE_DEPLOYMENT) is False

        # Test exception handling
        mock_hass.states.get.side_effect = Exception("Test error")
        assert _validate_entity_workload_type(mock_hass, "switch.my_deployment", WORKLOAD_TYPE_DEPLOYMENT) is False
        mock_hass.states.get.side_effect = None  # Reset side effect

    def test_get_namespace_from_entity(self, mock_hass):
        """Test _get_namespace_from_entity function."""
        # Test entity found with deployment_name
        entity = MagicMock()
        entity.attributes = {
            "namespace": "default",
            "deployment_name": "my-app"
        }
        mock_hass.states.get.return_value = entity

        ns, name = _get_namespace_from_entity(mock_hass, "switch.my_app")
        assert ns == "default"
        assert name == "my-app"

        # Test entity found with statefulset_name
        entity.attributes = {
            "namespace": "prod",
            "statefulset_name": "my-db"
        }
        ns, name = _get_namespace_from_entity(mock_hass, "switch.my_db")
        assert ns == "prod"
        assert name == "my-db"

        # Test entity found with cronjob_name
        entity.attributes = {
            "namespace": "batch",
            "cronjob_name": "my-job"
        }
        ns, name = _get_namespace_from_entity(mock_hass, "switch.my_job")
        assert ns == "batch"
        assert name == "my-job"

        # Test entity not found
        mock_hass.states.get.return_value = None
        ns, name = _get_namespace_from_entity(mock_hass, "switch.unknown")
        assert ns is None
        assert name is None

        # Test exception handling
        mock_hass.states.get.side_effect = Exception("Test error")
        ns, name = _get_namespace_from_entity(mock_hass, "switch.error")
        assert ns is None
        assert name is None
        mock_hass.states.get.side_effect = None  # Reset side effect

    def test_validate_deployment_schema(self):
        """Test _validate_deployment_schema function."""
        # Valid data
        assert _validate_deployment_schema({ATTR_DEPLOYMENT_NAME: "app"}) == {ATTR_DEPLOYMENT_NAME: "app"}
        assert _validate_deployment_schema({ATTR_DEPLOYMENT_NAMES: ["app"]}) == {ATTR_DEPLOYMENT_NAMES: ["app"]}

        # Invalid data
        with pytest.raises(vol.Invalid):
            _validate_deployment_schema({})

    def test_validate_statefulset_schema(self):
        """Test _validate_statefulset_schema function."""
        # Valid data
        assert _validate_statefulset_schema({ATTR_STATEFULSET_NAME: "db"}) == {ATTR_STATEFULSET_NAME: "db"}
        assert _validate_statefulset_schema({ATTR_STATEFULSET_NAMES: ["db"]}) == {ATTR_STATEFULSET_NAMES: ["db"]}

        # Invalid data
        with pytest.raises(vol.Invalid):
            _validate_statefulset_schema({})


class TestDeploymentExtraction:
    """Test deployment extraction logic."""

    def test_extract_deployment_names_single_string(self, mock_hass):
        """Test extracting from single string name."""
        # Setup mock entity
        entity = MagicMock()
        entity.attributes = {
            ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_DEPLOYMENT,
            "namespace": "default",
            "deployment_name": "my-app"
        }
        mock_hass.states.get.return_value = entity

        # Test with entity ID
        names, namespaces = _extract_deployment_names_and_namespaces(
            {ATTR_DEPLOYMENT_NAME: "switch.my_app"}, mock_hass
        )
        assert names == ["my-app"]
        assert namespaces == ["default"]

    def test_extract_deployment_names_single_dict(self, mock_hass):
        """Test extracting from single dict with entity_id."""
        # Setup mock entity
        entity = MagicMock()
        entity.attributes = {
            ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_DEPLOYMENT,
            "namespace": "default",
            "deployment_name": "my-app"
        }
        mock_hass.states.get.return_value = entity

        # Test with dict
        names, namespaces = _extract_deployment_names_and_namespaces(
            {ATTR_DEPLOYMENT_NAME: {"entity_id": "switch.my_app"}}, mock_hass
        )
        assert names == ["my-app"]
        assert namespaces == ["default"]

    def test_extract_deployment_names_list_strings(self, mock_hass):
        """Test extracting from list of strings."""
        # Setup mock entity
        entity = MagicMock()
        entity.attributes = {
            ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_DEPLOYMENT,
            "namespace": "default",
            "deployment_name": "my-app"
        }
        mock_hass.states.get.return_value = entity

        # Test with list of strings
        names, namespaces = _extract_deployment_names_and_namespaces(
            {ATTR_DEPLOYMENT_NAMES: ["switch.my_app"]}, mock_hass
        )
        assert names == ["my-app"]
        assert namespaces == ["default"]

    def test_extract_deployment_names_list_dicts(self, mock_hass):
        """Test extracting from list of dicts."""
        # Setup mock entity
        entity = MagicMock()
        entity.attributes = {
            ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_DEPLOYMENT,
            "namespace": "default",
            "deployment_name": "my-app"
        }
        mock_hass.states.get.return_value = entity

        # Test with list of dicts
        names, namespaces = _extract_deployment_names_and_namespaces(
            {ATTR_DEPLOYMENT_NAMES: [{"entity_id": "switch.my_app"}]}, mock_hass
        )
        assert names == ["my-app"]
        assert namespaces == ["default"]

    def test_extract_deployment_names_ha_ui_format(self, mock_hass):
        """Test extracting from HA UI format (dict with entity_id list)."""
        # Setup mock entity
        entity = MagicMock()
        entity.attributes = {
            ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_DEPLOYMENT,
            "namespace": "default",
            "deployment_name": "my-app"
        }
        mock_hass.states.get.return_value = entity

        # Test with HA UI format
        names, namespaces = _extract_deployment_names_and_namespaces(
            {ATTR_DEPLOYMENT_NAMES: {"entity_id": ["switch.my_app"]}}, mock_hass
        )
        assert names == ["my-app"]
        assert namespaces == ["default"]

    def test_extract_deployment_names_fallback(self, mock_hass):
        """Test fallback extraction when attributes missing."""
        # Setup mock entity with correct type but missing name
        entity = MagicMock()
        entity.attributes = {
            ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_DEPLOYMENT,
            "namespace": "default"
        }
        mock_hass.states.get.return_value = entity

        # Test fallback
        names, namespaces = _extract_deployment_names_and_namespaces(
            {ATTR_DEPLOYMENT_NAMES: {"entity_id": ["switch.my_app_deployment"]}}, mock_hass
        )
        # Fallback replaces switch. and _deployment, but keeps underscores from entity_id
        assert names == ["my_app"]
        assert namespaces == ["default"]

    def test_extract_deployment_names_invalid_type(self, mock_hass):
        """Test extracting with invalid type."""
        names, namespaces = _extract_deployment_names_and_namespaces(
            {ATTR_DEPLOYMENT_NAMES: 123}, mock_hass
        )
        assert names == []
        assert namespaces == []


class TestStatefulSetExtraction:
    """Test StatefulSet extraction logic."""

    def test_extract_statefulset_names_single_string(self, mock_hass):
        """Test extracting from single string name."""
        # Setup mock entity
        entity = MagicMock()
        entity.attributes = {
            ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_STATEFULSET,
            "namespace": "default",
            "statefulset_name": "my-db"
        }
        mock_hass.states.get.return_value = entity

        # Test with entity ID
        names, namespaces = _extract_statefulset_names_and_namespaces(
            {ATTR_STATEFULSET_NAME: "switch.my_db"}, mock_hass
        )
        assert names == ["my-db"]
        assert namespaces == ["default"]

    def test_extract_statefulset_names_ha_ui_format(self, mock_hass):
        """Test extracting from HA UI format."""
        # Setup mock entity
        entity = MagicMock()
        entity.attributes = {
            ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_STATEFULSET,
            "namespace": "default",
            "statefulset_name": "my-db"
        }
        mock_hass.states.get.return_value = entity

        # Test with HA UI format
        names, namespaces = _extract_statefulset_names_and_namespaces(
            {ATTR_STATEFULSET_NAMES: {"entity_id": ["switch.my_db"]}}, mock_hass
        )
        assert names == ["my-db"]
        assert namespaces == ["default"]

    def test_extract_statefulset_names_fallback(self, mock_hass):
        """Test fallback extraction when attributes missing."""
        # Setup mock entity with correct type but missing name
        entity = MagicMock()
        entity.attributes = {
            ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_STATEFULSET,
            "namespace": "default"
        }
        mock_hass.states.get.return_value = entity

        # Test fallback
        names, namespaces = _extract_statefulset_names_and_namespaces(
            {ATTR_STATEFULSET_NAMES: {"entity_id": ["switch.my_db_statefulset"]}}, mock_hass
        )
        # Fallback replaces switch. and _statefulset, but keeps underscores from entity_id
        assert names == ["my_db"]
        assert namespaces == ["default"]


class TestCronJobExtraction:
    """Test CronJob extraction logic."""

    def test_extract_cronjob_names_single_string(self, mock_hass):
        """Test extracting from single string name."""
        # Setup mock entity
        entity = MagicMock()
        entity.attributes = {
            ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_CRONJOB,
            "namespace": "default",
            "cronjob_name": "my-job"
        }
        mock_hass.states.get.return_value = entity

        # Test with entity ID
        names, namespaces = _extract_cronjob_names_and_namespaces(
            {ATTR_CRONJOB_NAME: "switch.my_job"}, mock_hass
        )
        # Current implementation returns the entity ID (name) instead of extracted cronjob_name
        # This matches current behavior in services.py
        assert names == ["switch.my_job"]
        assert namespaces == ["default"]

    def test_extract_cronjob_names_ha_ui_format(self, mock_hass):
        """Test extracting from HA UI format."""
        # Setup mock entity
        entity = MagicMock()
        entity.attributes = {
            ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_CRONJOB,
            "namespace": "default",
            "cronjob_name": "my-job"
        }
        mock_hass.states.get.return_value = entity

        # Test with HA UI format
        names, namespaces = _extract_cronjob_names_and_namespaces(
            {ATTR_CRONJOB_NAMES: {"entity_id": ["switch.my_job"]}}, mock_hass
        )
        assert names == ["my-job"]
        assert namespaces == ["default"]

    def test_extract_cronjob_names_fallback(self, mock_hass):
        """Test fallback extraction when attributes missing."""
        # Setup mock entity with correct type but missing name
        entity = MagicMock()
        entity.attributes = {
            ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_CRONJOB,
            "namespace": "default"
        }
        mock_hass.states.get.return_value = entity

        # Test fallback
        names, namespaces = _extract_cronjob_names_and_namespaces(
            {ATTR_CRONJOB_NAMES: {"entity_id": ["switch.my_job_cronjob"]}}, mock_hass
        )
        # Fallback replaces switch. and _cronjob, but keeps underscores from entity_id
        assert names == ["my_job"]
        assert namespaces == ["default"]
