"""Tests for the Kubernetes integration services."""

from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.core import HomeAssistant

try:
    from homeassistant.core import ServiceCall
except ImportError:
    # Fallback for older HomeAssistant versions
    ServiceCall = MagicMock
import pytest

from custom_components.kubernetes.const import (
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
from custom_components.kubernetes.services import (
    _extract_deployment_names_and_namespaces,
    _extract_statefulset_names_and_namespaces,
    _get_namespace_from_entity,
    async_setup_services,
    async_unload_services,
)


@pytest.fixture
def mock_hass():
    """Mock Home Assistant instance."""
    hass = MagicMock(spec=HomeAssistant)
    hass.data = {
        DOMAIN: {
            "entry1": {
                "config": {
                    "host": "https://kubernetes.example.com",
                    "token": "test-token",
                    "verify_ssl": True,
                }
            }
        }
    }
    # Add required attributes
    hass.services = MagicMock()
    hass.states = MagicMock()
    return hass


@pytest.fixture
def mock_service_call():
    """Mock service call."""
    call = MagicMock(spec=ServiceCall)
    call.data = {}
    return call


async def test_async_setup_services(mock_hass):
    """Test setting up services."""
    # The services module directly calls hass.services.async_register
    # So we need to patch the mock_hass.services.async_register
    await async_setup_services(mock_hass)

    # Verify all services were registered
    assert mock_hass.services.async_register.call_count == 6

    # Check that the correct services were registered
    registered_services = [
        call[0][1] for call in mock_hass.services.async_register.call_args_list
    ]
    assert SERVICE_SCALE_DEPLOYMENT in registered_services
    assert SERVICE_START_DEPLOYMENT in registered_services
    assert SERVICE_STOP_DEPLOYMENT in registered_services
    assert SERVICE_SCALE_STATEFULSET in registered_services
    assert SERVICE_START_STATEFULSET in registered_services
    assert SERVICE_STOP_STATEFULSET in registered_services


async def test_async_unload_services(mock_hass):
    """Test unloading services."""
    # The services module directly calls hass.services.async_remove
    # So we need to patch the mock_hass.services.async_remove
    await async_unload_services(mock_hass)

    # Verify all services were unregistered
    assert mock_hass.services.async_remove.call_count == 6

    # Check that the correct services were unregistered
    unregistered_services = [
        call[0][1] for call in mock_hass.services.async_remove.call_args_list
    ]
    assert SERVICE_SCALE_DEPLOYMENT in unregistered_services
    assert SERVICE_START_DEPLOYMENT in unregistered_services
    assert SERVICE_STOP_DEPLOYMENT in unregistered_services
    assert SERVICE_SCALE_STATEFULSET in unregistered_services
    assert SERVICE_START_STATEFULSET in unregistered_services
    assert SERVICE_STOP_STATEFULSET in unregistered_services


def test_extract_deployment_names_and_namespaces_single_string(mock_hass):
    """Test extracting deployment names and namespaces from single string."""
    call_data = {ATTR_DEPLOYMENT_NAMES: "nginx-deployment"}

    with patch(
        "custom_components.kubernetes.services._get_namespace_from_entity",
        return_value=("default", "nginx-deployment"),
    ):
        names, namespaces = _extract_deployment_names_and_namespaces(
            call_data, mock_hass
        )

        assert names == ["nginx-deployment"]
        assert namespaces == ["default"]


def test_extract_deployment_names_and_namespaces_entity_id_format(mock_hass):
    """Test extracting deployment names and namespaces from entity_id format."""
    call_data = {
        ATTR_DEPLOYMENT_NAMES: {"entity_id": ["switch.nginx-deployment_deployment"]}
    }

    with patch(
        "custom_components.kubernetes.services._get_namespace_from_entity",
        return_value=("default", "nginx-deployment"),
    ):
        names, namespaces = _extract_deployment_names_and_namespaces(
            call_data, mock_hass
        )

        assert names == ["nginx-deployment"]
        assert namespaces == ["default"]


def test_extract_deployment_names_and_namespaces_list_format(mock_hass):
    """Test extracting deployment names and namespaces from list format."""
    call_data = {ATTR_DEPLOYMENT_NAMES: ["nginx-deployment", "api-deployment"]}

    with patch(
        "custom_components.kubernetes.services._get_namespace_from_entity",
        return_value=("default", "nginx-deployment"),
    ):
        names, namespaces = _extract_deployment_names_and_namespaces(
            call_data, mock_hass
        )

        assert names == ["nginx-deployment", "api-deployment"]
        assert namespaces == ["default", "default"]


def test_extract_statefulset_names_and_namespaces_single_string(mock_hass):
    """Test extracting statefulset names and namespaces from single string."""
    call_data = {ATTR_STATEFULSET_NAMES: "redis-statefulset"}

    with patch(
        "custom_components.kubernetes.services._get_namespace_from_entity",
        return_value=("default", "redis-statefulset"),
    ):
        names, namespaces = _extract_statefulset_names_and_namespaces(
            call_data, mock_hass
        )

        assert names == ["redis-statefulset"]
        assert namespaces == ["default"]


def test_extract_statefulset_names_and_namespaces_entity_id_format(mock_hass):
    """Test extracting statefulset names and namespaces from entity_id format."""
    call_data = {
        ATTR_STATEFULSET_NAMES: {"entity_id": ["switch.redis-statefulset_statefulset"]}
    }

    with patch(
        "custom_components.kubernetes.services._get_namespace_from_entity",
        return_value=("default", "redis-statefulset"),
    ):
        names, namespaces = _extract_statefulset_names_and_namespaces(
            call_data, mock_hass
        )

        assert names == ["redis-statefulset"]
        assert namespaces == ["default"]


def test_get_namespace_from_entity_found(mock_hass):
    """Test getting namespace from entity when entity is found."""
    mock_entity = MagicMock()
    mock_entity.attributes = {
        "namespace": "default",
        "deployment_name": "nginx-deployment",
    }

    with patch.object(mock_hass.states, "get", return_value=mock_entity):
        namespace, name = _get_namespace_from_entity(
            mock_hass, "switch.nginx-deployment_deployment"
        )

        assert namespace == "default"
        assert name == "nginx-deployment"


def test_get_namespace_from_entity_not_found(mock_hass):
    """Test getting namespace from entity when entity is not found."""
    with patch.object(mock_hass.states, "get", return_value=None):
        namespace, name = _get_namespace_from_entity(
            mock_hass, "switch.nginx-deployment_deployment"
        )

        assert namespace is None
        assert name is None
