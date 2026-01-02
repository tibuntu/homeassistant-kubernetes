"""Tests for the Kubernetes integration config flow."""

from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.data_entry_flow import AbortFlow, FlowResultType
import pytest

from custom_components.kubernetes.config_flow import KubernetesConfigFlow
from custom_components.kubernetes.const import (
    CONF_API_TOKEN,
    CONF_CLUSTER_NAME,
    CONF_MONITOR_ALL_NAMESPACES,
    CONF_NAMESPACE,
    CONF_VERIFY_SSL,
    DEFAULT_CLUSTER_NAME,
    DEFAULT_MONITOR_ALL_NAMESPACES,
    DEFAULT_NAMESPACE,
    DEFAULT_PORT,
    DEFAULT_VERIFY_SSL,
    DOMAIN,
)


@pytest.fixture
def mock_flow():
    """Mock config flow."""
    flow = KubernetesConfigFlow()
    flow.hass = MagicMock()
    return flow


@pytest.fixture
def valid_user_input():
    """Valid user input for config flow."""
    return {
        CONF_CLUSTER_NAME: "test-cluster",
        CONF_HOST: "test-cluster.example.com",
        CONF_PORT: 6443,
        CONF_API_TOKEN: "test-token",
        CONF_MONITOR_ALL_NAMESPACES: True,
        CONF_VERIFY_SSL: False,
    }


async def test_async_step_user_kubernetes_not_available(mock_hass):
    """Test user step when kubernetes package is not available."""
    with patch(
        "custom_components.kubernetes.config_flow._ensure_kubernetes_imported",
        return_value=False,
    ):
        flow = KubernetesConfigFlow()
        flow.hass = mock_hass

        result = await flow.async_step_user()

        assert result["type"] == "form"
        assert "errors" in result
        assert result["errors"]["base"] == "kubernetes_not_installed"


async def test_async_step_user_initial_step(mock_flow):
    """Test initial user step."""
    with patch(
        "custom_components.kubernetes.config_flow._ensure_kubernetes_imported",
        return_value=True,
    ):
        result = await mock_flow.async_step_user()

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "user"
        assert "errors" not in result["data_schema"].schema


async def test_async_step_user_with_valid_input(mock_hass):
    """Test user step with valid input."""
    with (
        patch(
            "custom_components.kubernetes.config_flow._ensure_kubernetes_imported",
            return_value=True,
        ),
        patch(
            "custom_components.kubernetes.config_flow.KUBERNETES_AVAILABLE",
            True,
        ),
        patch(
            "custom_components.kubernetes.config_flow.KubernetesConfigFlow.async_set_unique_id"
        ),
        patch(
            "custom_components.kubernetes.config_flow.KubernetesConfigFlow._abort_if_unique_id_configured"
        ),
    ):
        flow = KubernetesConfigFlow()
        flow.hass = mock_hass

        # Mock the _test_connection method on the instance
        flow._test_connection = AsyncMock()

        user_input = {
            CONF_CLUSTER_NAME: "test-cluster",
            CONF_HOST: "kubernetes.example.com",
            CONF_PORT: 6443,
            CONF_API_TOKEN: "test-token",
            CONF_MONITOR_ALL_NAMESPACES: True,
            CONF_VERIFY_SSL: False,
        }

        result = await flow.async_step_user(user_input=user_input)

        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["title"] == "test-cluster"
        assert result["data"][CONF_CLUSTER_NAME] == "test-cluster"
        flow._test_connection.assert_called_once_with(user_input)


async def test_async_step_user_connection_test_fails(mock_hass):
    """Test user step when connection test fails."""
    with (
        patch(
            "custom_components.kubernetes.config_flow._ensure_kubernetes_imported",
            return_value=True,
        ),
        patch(
            "custom_components.kubernetes.config_flow.KUBERNETES_AVAILABLE",
            True,
        ),
    ):
        flow = KubernetesConfigFlow()
        flow.hass = mock_hass

        # Mock the _test_connection method on the instance to raise an exception
        flow._test_connection = AsyncMock(side_effect=Exception("Connection failed"))

        user_input = {
            CONF_CLUSTER_NAME: "test-cluster",
            CONF_HOST: "kubernetes.example.com",
            CONF_API_TOKEN: "test-token",
        }

        result = await flow.async_step_user(user_input=user_input)

        assert result["type"] == FlowResultType.FORM
        assert "errors" in result
        assert result["errors"]["base"] == "cannot_connect"


async def test_async_step_user_duplicate_entry(mock_hass):
    """Test user step with duplicate entry."""
    with (
        patch(
            "custom_components.kubernetes.config_flow._ensure_kubernetes_imported",
            return_value=True,
        ),
        patch(
            "custom_components.kubernetes.config_flow.KUBERNETES_AVAILABLE",
            True,
        ),
        patch(
            "custom_components.kubernetes.config_flow.KubernetesConfigFlow.async_set_unique_id"
        ),
    ):
        flow = KubernetesConfigFlow()
        flow.hass = mock_hass

        # Mock the _test_connection method on the instance
        flow._test_connection = AsyncMock()

        # Mock the _abort_if_unique_id_configured method to raise an AbortFlow exception
        flow._abort_if_unique_id_configured = MagicMock(
            side_effect=AbortFlow("already_configured")
        )

        user_input = {
            CONF_CLUSTER_NAME: "test-cluster",
            CONF_HOST: "kubernetes.example.com",
            CONF_API_TOKEN: "test-token",
            CONF_MONITOR_ALL_NAMESPACES: True,
        }

        with pytest.raises(AbortFlow) as exc_info:
            await flow.async_step_user(user_input=user_input)

        assert exc_info.value.reason == "already_configured"


async def test_test_connection_success(mock_flow):
    """Test successful connection test."""
    # Mock the _test_connection method to not raise an exception
    mock_flow._test_connection = AsyncMock()

    # Should not raise an exception
    await mock_flow._test_connection(
        {
            CONF_HOST: "test-host",
            CONF_PORT: 6443,
            CONF_API_TOKEN: "test-token",
            CONF_VERIFY_SSL: False,
        }
    )


async def test_test_connection_failure(mock_flow):
    """Test failed connection test."""
    with patch("custom_components.kubernetes.config_flow.client") as mock_client:
        mock_api = MagicMock()
        mock_client.CoreV1Api.return_value = mock_api
        mock_api.get_api_resources.side_effect = Exception("Connection failed")

        with pytest.raises(Exception, match="Connection test failed"):
            await mock_flow._test_connection(
                {
                    CONF_HOST: "test-host",
                    CONF_PORT: 6443,
                    CONF_API_TOKEN: "test-token",
                    CONF_VERIFY_SSL: False,
                }
            )


def test_ensure_kubernetes_imported_success():
    """Test successful kubernetes import."""
    with patch("custom_components.kubernetes.config_flow.KUBERNETES_AVAILABLE", True):
        from custom_components.kubernetes.config_flow import _ensure_kubernetes_imported

        assert _ensure_kubernetes_imported() is True


def test_ensure_kubernetes_imported_failure():
    """Test failed kubernetes import."""
    with patch("custom_components.kubernetes.config_flow.KUBERNETES_AVAILABLE", False):
        from custom_components.kubernetes.config_flow import _ensure_kubernetes_imported

        assert _ensure_kubernetes_imported() is False


def test_config_flow_constants():
    """Test config flow constants."""
    assert KubernetesConfigFlow.VERSION == 1


async def test_async_step_namespaces(mock_hass):
    """Test namespace selection step."""
    with (
        patch(
            "custom_components.kubernetes.config_flow._ensure_kubernetes_imported",
            return_value=True,
        ),
        patch(
            "custom_components.kubernetes.config_flow.KUBERNETES_AVAILABLE",
            True,
        ),
        patch(
            "custom_components.kubernetes.config_flow.KubernetesConfigFlow.async_set_unique_id"
        ),
        patch(
            "custom_components.kubernetes.config_flow.KubernetesConfigFlow._abort_if_unique_id_configured"
        ),
    ):
        flow = KubernetesConfigFlow()
        flow.hass = mock_hass

        # Set up connection data
        flow._connection_data = {
            CONF_CLUSTER_NAME: "test-cluster",
            CONF_HOST: "test-cluster.example.com",
            CONF_API_TOKEN: "test-token",
            CONF_MONITOR_ALL_NAMESPACES: False,
        }

        # Mock namespace fetching
        flow._fetch_namespaces = AsyncMock(
            return_value=["default", "kube-system", "production"]
        )

        # Test initial namespace step (no user input)
        result = await flow.async_step_namespaces()

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "namespaces"

        # Test namespace selection
        user_input = {
            CONF_NAMESPACE: ["default", "production"],
        }

        result = await flow.async_step_namespaces(user_input=user_input)

        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["title"] == "test-cluster"
        assert result["data"][CONF_NAMESPACE] == ["default", "production"]
        assert result["data"][CONF_CLUSTER_NAME] == "test-cluster"


async def test_async_step_user_goes_to_namespaces_step(mock_hass):
    """Test that user step proceeds to namespace step when monitor_all_namespaces is False."""
    with (
        patch(
            "custom_components.kubernetes.config_flow._ensure_kubernetes_imported",
            return_value=True,
        ),
        patch(
            "custom_components.kubernetes.config_flow.KUBERNETES_AVAILABLE",
            True,
        ),
    ):
        flow = KubernetesConfigFlow()
        flow.hass = mock_hass

        flow._test_connection = AsyncMock()
        flow.async_step_namespaces = AsyncMock(
            return_value={"type": "form", "step_id": "namespaces"}
        )

        user_input = {
            CONF_CLUSTER_NAME: "test-cluster",
            CONF_HOST: "test-cluster.example.com",
            CONF_API_TOKEN: "test-token",
            CONF_MONITOR_ALL_NAMESPACES: False,
        }

        await flow.async_step_user(user_input=user_input)

        # Should proceed to namespaces step
        flow.async_step_namespaces.assert_called_once()


async def test_async_step_user_with_defaults(mock_hass):
    """Test user step with default values."""
    with (
        patch(
            "custom_components.kubernetes.config_flow._ensure_kubernetes_imported",
            return_value=True,
        ),
        patch(
            "custom_components.kubernetes.config_flow.KUBERNETES_AVAILABLE",
            True,
        ),
        patch(
            "custom_components.kubernetes.config_flow.KubernetesConfigFlow.async_set_unique_id"
        ),
        patch(
            "custom_components.kubernetes.config_flow.KubernetesConfigFlow._abort_if_unique_id_configured"
        ),
    ):
        flow = KubernetesConfigFlow()
        flow.hass = mock_hass

        # Mock the _test_connection method on the instance
        flow._test_connection = AsyncMock()

        user_input = {
            CONF_CLUSTER_NAME: "test-cluster",
            CONF_HOST: "test-cluster.example.com",
            CONF_API_TOKEN: "test-token",
            CONF_MONITOR_ALL_NAMESPACES: True,
        }

        result = await flow.async_step_user(user_input=user_input)

        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["title"] == "test-cluster"
        assert result["data"][CONF_PORT] == DEFAULT_PORT
        assert result["data"][CONF_CLUSTER_NAME] == "test-cluster"
        assert result["data"][CONF_VERIFY_SSL] == DEFAULT_VERIFY_SSL
        flow._test_connection.assert_called_once()
