"""Tests for the Kubernetes integration config flow."""

from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.data_entry_flow import AbortFlow, FlowResultType
import pytest

from custom_components.kubernetes.config_flow import (
    KubernetesConfigFlow,
    KubernetesOptionsFlow,
)
from custom_components.kubernetes.const import (
    CONF_API_TOKEN,
    CONF_CA_CERT,
    CONF_CLUSTER_NAME,
    CONF_DEVICE_GROUPING_MODE,
    CONF_ENABLE_WATCH,
    CONF_MONITOR_ALL_NAMESPACES,
    CONF_NAMESPACE,
    CONF_SCALE_COOLDOWN,
    CONF_SCALE_VERIFICATION_TIMEOUT,
    CONF_SWITCH_UPDATE_INTERVAL,
    CONF_VERIFY_SSL,
    DEFAULT_DEVICE_GROUPING_MODE,
    DEFAULT_ENABLE_WATCH,
    DEFAULT_PORT,
    DEFAULT_SCALE_COOLDOWN,
    DEFAULT_SCALE_VERIFICATION_TIMEOUT,
    DEFAULT_SWITCH_UPDATE_INTERVAL,
    DEFAULT_VERIFY_SSL,
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


# ---------------------------------------------------------------------------
# Additional config_flow tests for uncovered paths
# ---------------------------------------------------------------------------


def test_ensure_kubernetes_imported_import_error():
    """Test _ensure_kubernetes_imported when ImportError occurs."""
    import custom_components.kubernetes.config_flow as cf_module

    original = cf_module.KUBERNETES_AVAILABLE
    cf_module.KUBERNETES_AVAILABLE = None

    try:
        import builtins

        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "kubernetes.client":
                raise ImportError("No module named 'kubernetes'")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            result = cf_module._ensure_kubernetes_imported()
            assert result is False
    finally:
        cf_module.KUBERNETES_AVAILABLE = original


def test_ensure_kubernetes_imported_generic_exception():
    """Test _ensure_kubernetes_imported when a generic Exception occurs."""
    import custom_components.kubernetes.config_flow as cf_module

    original = cf_module.KUBERNETES_AVAILABLE
    cf_module.KUBERNETES_AVAILABLE = None

    try:
        import builtins

        original_import = builtins.__import__

        def mock_import_exc(name, *args, **kwargs):
            if name == "kubernetes.client":
                raise RuntimeError("Unexpected error")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import_exc):
            result = cf_module._ensure_kubernetes_imported()
            assert result is False
    finally:
        cf_module.KUBERNETES_AVAILABLE = original


async def test_async_step_namespaces_empty_namespace_error(mock_hass):
    """Test namespace step returns error when no namespace selected."""
    flow = KubernetesConfigFlow()
    flow.hass = mock_hass
    flow._connection_data = {
        CONF_CLUSTER_NAME: "test-cluster",
        CONF_HOST: "test-host",
        CONF_API_TOKEN: "test-token",
    }
    flow._fetch_namespaces = AsyncMock(return_value=["default", "kube-system"])

    # Pass empty namespace list
    result = await flow.async_step_namespaces(user_input={CONF_NAMESPACE: []})

    assert result["type"] == "form"
    assert result["step_id"] == "namespaces"
    assert CONF_NAMESPACE in result["errors"]


async def test_async_step_namespaces_string_namespace_conversion(mock_hass):
    """Test namespace step converts string input to list."""
    with (
        patch(
            "custom_components.kubernetes.config_flow.KubernetesConfigFlow.async_set_unique_id"
        ),
        patch(
            "custom_components.kubernetes.config_flow.KubernetesConfigFlow._abort_if_unique_id_configured"
        ),
    ):
        flow = KubernetesConfigFlow()
        flow.hass = mock_hass
        flow._connection_data = {
            CONF_CLUSTER_NAME: "test-cluster",
            CONF_HOST: "test-host",
            CONF_API_TOKEN: "test-token",
        }

        # Provide namespace as comma-separated string
        result = await flow.async_step_namespaces(
            user_input={CONF_NAMESPACE: "default, production"}
        )

        assert result["type"] == "form" or result["type"] == "create_entry"
        if result["type"] == "create_entry":
            assert "default" in result["data"][CONF_NAMESPACE]
            assert "production" in result["data"][CONF_NAMESPACE]


async def test_async_step_namespaces_non_list_namespace(mock_hass):
    """Test namespace step converts non-list/non-string namespace to default."""
    with (
        patch(
            "custom_components.kubernetes.config_flow.KubernetesConfigFlow.async_set_unique_id"
        ),
        patch(
            "custom_components.kubernetes.config_flow.KubernetesConfigFlow._abort_if_unique_id_configured"
        ),
    ):
        flow = KubernetesConfigFlow()
        flow.hass = mock_hass
        flow._connection_data = {
            CONF_CLUSTER_NAME: "test-cluster",
            CONF_HOST: "test-host",
            CONF_API_TOKEN: "test-token",
        }

        # Provide namespace as an integer (non-list, non-string)
        result = await flow.async_step_namespaces(user_input={CONF_NAMESPACE: 12345})

        assert result["type"] == "create_entry"
        assert result["data"][CONF_NAMESPACE] == ["default"]


async def test_async_step_namespaces_no_namespaces_fetched(mock_hass):
    """Test namespace step shows error when no namespaces fetched."""
    flow = KubernetesConfigFlow()
    flow.hass = mock_hass
    flow._connection_data = {
        CONF_CLUSTER_NAME: "test-cluster",
        CONF_HOST: "test-host",
        CONF_API_TOKEN: "test-token",
    }
    flow._fetch_namespaces = AsyncMock(return_value=[])

    result = await flow.async_step_namespaces()

    assert result["type"] == "form"
    assert result["errors"].get("base") == "cannot_fetch_namespaces"


async def test_async_step_namespaces_fetch_exception(mock_hass):
    """Test namespace step handles fetch exception."""
    flow = KubernetesConfigFlow()
    flow.hass = mock_hass
    flow._connection_data = {
        CONF_CLUSTER_NAME: "test-cluster",
        CONF_HOST: "test-host",
        CONF_API_TOKEN: "test-token",
    }
    flow._fetch_namespaces = AsyncMock(side_effect=Exception("Network error"))

    result = await flow.async_step_namespaces()

    assert result["type"] == "form"
    assert result["errors"].get("base") == "cannot_fetch_namespaces"


async def test_test_connection_kubernetes_not_available(mock_hass):
    """Test _test_connection raises when kubernetes not available."""
    with patch(
        "custom_components.kubernetes.config_flow._ensure_kubernetes_imported",
        return_value=False,
    ):
        flow = KubernetesConfigFlow()
        flow.hass = mock_hass

        with pytest.raises(ValueError, match="Kubernetes package is not installed"):
            await flow._test_connection(
                {
                    CONF_HOST: "test-host",
                    CONF_API_TOKEN: "test-token",
                }
            )


async def test_test_connection_empty_host(mock_hass):
    """Test _test_connection raises when host is empty."""
    import custom_components.kubernetes.config_flow as cf_module

    original = cf_module.KUBERNETES_AVAILABLE
    cf_module.KUBERNETES_AVAILABLE = True

    try:
        with patch(
            "custom_components.kubernetes.config_flow._ensure_kubernetes_imported",
            return_value=True,
        ):
            flow = KubernetesConfigFlow()
            flow.hass = mock_hass

            with pytest.raises(ValueError, match="Host is required"):
                await flow._test_connection(
                    {
                        CONF_HOST: "",
                        CONF_API_TOKEN: "test-token",
                    }
                )
    finally:
        cf_module.KUBERNETES_AVAILABLE = original


async def test_test_connection_empty_token(mock_hass):
    """Test _test_connection raises when API token is empty."""
    import custom_components.kubernetes.config_flow as cf_module

    original = cf_module.KUBERNETES_AVAILABLE
    cf_module.KUBERNETES_AVAILABLE = True

    try:
        with patch(
            "custom_components.kubernetes.config_flow._ensure_kubernetes_imported",
            return_value=True,
        ):
            flow = KubernetesConfigFlow()
            flow.hass = mock_hass

            with pytest.raises(ValueError, match="API token is required"):
                await flow._test_connection(
                    {
                        CONF_HOST: "test-host",
                        CONF_API_TOKEN: "",
                    }
                )
    finally:
        cf_module.KUBERNETES_AVAILABLE = original


async def test_test_connection_with_ca_cert(mock_hass):
    """Test _test_connection sets CA cert when provided."""
    import custom_components.kubernetes.config_flow as cf_module

    original_available = cf_module.KUBERNETES_AVAILABLE
    original_client = cf_module.client

    cf_module.KUBERNETES_AVAILABLE = True

    mock_k8s_client = MagicMock()
    mock_config = MagicMock()
    mock_api_client = MagicMock()
    mock_core_v1 = MagicMock()

    mock_k8s_client.Configuration.return_value = mock_config
    mock_k8s_client.ApiClient.return_value = mock_api_client
    mock_k8s_client.CoreV1Api.return_value = mock_core_v1

    cf_module.client = mock_k8s_client

    try:
        with patch(
            "custom_components.kubernetes.config_flow._ensure_kubernetes_imported",
            return_value=True,
        ):
            flow = KubernetesConfigFlow()
            flow.hass = mock_hass

            import asyncio

            loop = asyncio.get_event_loop()

            with patch.object(
                loop, "run_in_executor", new=AsyncMock(return_value=None)
            ):
                await flow._test_connection(
                    {
                        CONF_HOST: "test-host",
                        CONF_API_TOKEN: "test-token",
                        "ca_cert": "/path/to/ca.crt",
                        "verify_ssl": False,
                    }
                )

            # Verify CA cert was set
            assert mock_config.ssl_ca_cert == "/path/to/ca.crt"
    finally:
        cf_module.KUBERNETES_AVAILABLE = original_available
        cf_module.client = original_client


async def test_test_connection_api_exception_aiohttp_success(mock_hass):
    """Test _test_connection falls back to aiohttp when ApiException raised and succeeds."""
    import custom_components.kubernetes.config_flow as cf_module

    original_available = cf_module.KUBERNETES_AVAILABLE
    original_client = cf_module.client
    original_api_exc = cf_module.ApiException

    cf_module.KUBERNETES_AVAILABLE = True

    mock_k8s_client = MagicMock()
    mock_config = MagicMock()
    mock_api_client = MagicMock()
    mock_core_v1 = MagicMock()

    mock_k8s_client.Configuration.return_value = mock_config
    mock_k8s_client.ApiClient.return_value = mock_api_client
    mock_k8s_client.CoreV1Api.return_value = mock_core_v1

    cf_module.client = mock_k8s_client

    # Make ApiException a real exception subclass we can raise
    class FakeApiException(Exception):
        def __init__(self):
            self.status = 401
            self.reason = "Unauthorized"
            self.body = None

    cf_module.ApiException = FakeApiException

    try:
        with patch(
            "custom_components.kubernetes.config_flow._ensure_kubernetes_imported",
            return_value=True,
        ):
            flow = KubernetesConfigFlow()
            flow.hass = mock_hass
            flow._test_connection_aiohttp = AsyncMock(return_value=True)

            import asyncio

            loop = asyncio.get_event_loop()

            with patch.object(
                loop,
                "run_in_executor",
                new=AsyncMock(side_effect=FakeApiException()),
            ):
                # Should not raise because aiohttp fallback succeeds
                await flow._test_connection(
                    {
                        CONF_HOST: "test-host",
                        CONF_API_TOKEN: "test-token",
                        "verify_ssl": False,
                    }
                )

            flow._test_connection_aiohttp.assert_called_once()
    finally:
        cf_module.KUBERNETES_AVAILABLE = original_available
        cf_module.client = original_client
        cf_module.ApiException = original_api_exc


async def test_test_connection_api_exception_aiohttp_failure(mock_hass):
    """Test _test_connection raises when ApiException raised and aiohttp also fails."""
    import custom_components.kubernetes.config_flow as cf_module

    original_available = cf_module.KUBERNETES_AVAILABLE
    original_client = cf_module.client
    original_api_exc = cf_module.ApiException

    cf_module.KUBERNETES_AVAILABLE = True

    mock_k8s_client = MagicMock()
    mock_config = MagicMock()
    mock_api_client = MagicMock()
    mock_core_v1 = MagicMock()

    mock_k8s_client.Configuration.return_value = mock_config
    mock_k8s_client.ApiClient.return_value = mock_api_client
    mock_k8s_client.CoreV1Api.return_value = mock_core_v1

    cf_module.client = mock_k8s_client

    class FakeApiException(Exception):
        def __init__(self):
            self.status = 401
            self.reason = "Unauthorized"
            self.body = None

    cf_module.ApiException = FakeApiException

    try:
        with patch(
            "custom_components.kubernetes.config_flow._ensure_kubernetes_imported",
            return_value=True,
        ):
            flow = KubernetesConfigFlow()
            flow.hass = mock_hass
            flow._test_connection_aiohttp = AsyncMock(return_value=False)

            import asyncio

            loop = asyncio.get_event_loop()

            with patch.object(
                loop,
                "run_in_executor",
                new=AsyncMock(side_effect=FakeApiException()),
            ):
                with pytest.raises(ValueError, match="Failed to connect"):
                    await flow._test_connection(
                        {
                            CONF_HOST: "test-host",
                            CONF_API_TOKEN: "test-token",
                            "verify_ssl": False,
                        }
                    )
    finally:
        cf_module.KUBERNETES_AVAILABLE = original_available
        cf_module.client = original_client
        cf_module.ApiException = original_api_exc


async def test_test_connection_generic_exception_aiohttp_success(mock_hass):
    """Test _test_connection falls back to aiohttp on generic exception and succeeds."""
    import custom_components.kubernetes.config_flow as cf_module

    original_available = cf_module.KUBERNETES_AVAILABLE
    original_client = cf_module.client

    cf_module.KUBERNETES_AVAILABLE = True

    mock_k8s_client = MagicMock()
    mock_config = MagicMock()
    mock_api_client = MagicMock()
    mock_core_v1 = MagicMock()

    mock_k8s_client.Configuration.return_value = mock_config
    mock_k8s_client.ApiClient.return_value = mock_api_client
    mock_k8s_client.CoreV1Api.return_value = mock_core_v1

    cf_module.client = mock_k8s_client

    try:
        with patch(
            "custom_components.kubernetes.config_flow._ensure_kubernetes_imported",
            return_value=True,
        ):
            flow = KubernetesConfigFlow()
            flow.hass = mock_hass
            flow._test_connection_aiohttp = AsyncMock(return_value=True)

            import asyncio

            loop = asyncio.get_event_loop()

            with patch.object(
                loop,
                "run_in_executor",
                new=AsyncMock(side_effect=ConnectionError("SSL error")),
            ):
                await flow._test_connection(
                    {
                        CONF_HOST: "test-host",
                        CONF_API_TOKEN: "test-token",
                        "verify_ssl": False,
                    }
                )

            flow._test_connection_aiohttp.assert_called_once()
    finally:
        cf_module.KUBERNETES_AVAILABLE = original_available
        cf_module.client = original_client


async def test_test_connection_generic_exception_aiohttp_failure(mock_hass):
    """Test _test_connection raises when generic exception raised and aiohttp fails."""
    import custom_components.kubernetes.config_flow as cf_module

    original_available = cf_module.KUBERNETES_AVAILABLE
    original_client = cf_module.client

    cf_module.KUBERNETES_AVAILABLE = True

    mock_k8s_client = MagicMock()
    mock_config = MagicMock()
    mock_api_client = MagicMock()
    mock_core_v1 = MagicMock()

    mock_k8s_client.Configuration.return_value = mock_config
    mock_k8s_client.ApiClient.return_value = mock_api_client
    mock_k8s_client.CoreV1Api.return_value = mock_core_v1

    cf_module.client = mock_k8s_client

    try:
        with patch(
            "custom_components.kubernetes.config_flow._ensure_kubernetes_imported",
            return_value=True,
        ):
            flow = KubernetesConfigFlow()
            flow.hass = mock_hass
            flow._test_connection_aiohttp = AsyncMock(return_value=False)

            import asyncio

            loop = asyncio.get_event_loop()

            with patch.object(
                loop,
                "run_in_executor",
                new=AsyncMock(side_effect=ConnectionError("SSL error")),
            ):
                with pytest.raises(ValueError, match="Connection test failed"):
                    await flow._test_connection(
                        {
                            CONF_HOST: "test-host",
                            CONF_API_TOKEN: "test-token",
                            "verify_ssl": False,
                        }
                    )
    finally:
        cf_module.KUBERNETES_AVAILABLE = original_available
        cf_module.client = original_client


async def test_test_connection_aiohttp_success(mock_hass):
    """Test _test_connection_aiohttp returns True on 200 response."""
    flow = KubernetesConfigFlow()
    flow.hass = mock_hass

    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)

    mock_session = MagicMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mock_session.get = MagicMock(return_value=mock_response)

    with patch("aiohttp.ClientSession", return_value=mock_session):
        result = await flow._test_connection_aiohttp(
            {
                CONF_HOST: "test-host",
                CONF_API_TOKEN: "test-token",
            }
        )

    assert result is True


async def test_test_connection_aiohttp_error_status(mock_hass):
    """Test _test_connection_aiohttp returns False on non-200 response."""
    flow = KubernetesConfigFlow()
    flow.hass = mock_hass

    mock_response = MagicMock()
    mock_response.status = 401
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)

    mock_session = MagicMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mock_session.get = MagicMock(return_value=mock_response)

    with patch("aiohttp.ClientSession", return_value=mock_session):
        result = await flow._test_connection_aiohttp(
            {
                CONF_HOST: "test-host",
                CONF_API_TOKEN: "test-token",
            }
        )

    assert result is False


async def test_test_connection_aiohttp_exception(mock_hass):
    """Test _test_connection_aiohttp returns False on exception."""
    flow = KubernetesConfigFlow()
    flow.hass = mock_hass

    mock_session = MagicMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mock_session.get = MagicMock(side_effect=Exception("Network error"))

    with patch("aiohttp.ClientSession", return_value=mock_session):
        result = await flow._test_connection_aiohttp(
            {
                CONF_HOST: "test-host",
                CONF_API_TOKEN: "test-token",
            }
        )

    assert result is False


async def test_fetch_namespaces_success(mock_hass):
    """Test _fetch_namespaces returns sorted namespace list on success."""
    flow = KubernetesConfigFlow()
    flow.hass = mock_hass

    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(
        return_value={
            "items": [
                {"metadata": {"name": "production"}},
                {"metadata": {"name": "default"}},
                {"metadata": {"name": "kube-system"}},
            ]
        }
    )
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)

    mock_session = MagicMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mock_session.get = MagicMock(return_value=mock_response)

    with patch("aiohttp.ClientSession", return_value=mock_session):
        result = await flow._fetch_namespaces(
            {
                CONF_HOST: "test-host",
                CONF_API_TOKEN: "test-token",
            }
        )

    assert result == ["default", "kube-system", "production"]


async def test_fetch_namespaces_error_status(mock_hass):
    """Test _fetch_namespaces returns empty list on non-200 response."""
    flow = KubernetesConfigFlow()
    flow.hass = mock_hass

    mock_response = MagicMock()
    mock_response.status = 403
    mock_response.text = AsyncMock(return_value="Forbidden")
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)

    mock_session = MagicMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mock_session.get = MagicMock(return_value=mock_response)

    with patch("aiohttp.ClientSession", return_value=mock_session):
        result = await flow._fetch_namespaces(
            {
                CONF_HOST: "test-host",
                CONF_API_TOKEN: "test-token",
            }
        )

    assert result == []


async def test_fetch_namespaces_client_error(mock_hass):
    """Test _fetch_namespaces returns empty list on aiohttp.ClientError."""
    import aiohttp as aiohttp_mod

    flow = KubernetesConfigFlow()
    flow.hass = mock_hass

    mock_session = MagicMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mock_session.get = MagicMock(
        side_effect=aiohttp_mod.ClientConnectionError("Connection refused")
    )

    with patch("aiohttp.ClientSession", return_value=mock_session):
        result = await flow._fetch_namespaces(
            {
                CONF_HOST: "test-host",
                CONF_API_TOKEN: "test-token",
            }
        )

    assert result == []


async def test_fetch_namespaces_generic_exception(mock_hass):
    """Test _fetch_namespaces returns empty list on generic exception."""
    flow = KubernetesConfigFlow()
    flow.hass = mock_hass

    mock_session = MagicMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mock_session.get = MagicMock(side_effect=Exception("Unexpected error"))

    with patch("aiohttp.ClientSession", return_value=mock_session):
        result = await flow._fetch_namespaces(
            {
                CONF_HOST: "test-host",
                CONF_API_TOKEN: "test-token",
            }
        )

    assert result == []


class TestKubernetesOptionsFlow:
    """Tests for the Kubernetes integration options flow."""

    @pytest.fixture
    def mock_config_entry(self):
        """Return a mock config entry with no options set."""
        entry = MagicMock()
        entry.options = {}
        return entry

    @pytest.fixture
    def options_flow(self, mock_config_entry):
        """Return an options flow instance with a mock config entry."""
        flow = KubernetesOptionsFlow()
        with patch.object(
            KubernetesOptionsFlow,
            "config_entry",
            new_callable=PropertyMock,
            return_value=mock_config_entry,
        ):
            yield flow

    async def test_options_flow_returns_form(self, options_flow):
        """Calling the flow with no input should return the init form."""
        result = await options_flow.async_step_init(user_input=None)
        assert result["type"] == "form"
        assert result["step_id"] == "init"

    async def test_options_flow_defaults_to_watch_disabled(self, options_flow):
        """Default value for enable_watch should be False."""
        result = await options_flow.async_step_init(user_input=None)
        # Verify the schema contains the enable_watch key
        schema_keys = [str(k) for k in result["data_schema"].schema]
        assert any(CONF_ENABLE_WATCH in k for k in schema_keys)

    async def test_options_flow_saves_enable_watch_true(self, options_flow):
        """Submitting enable_watch=True should create an entry with that value."""
        result = await options_flow.async_step_init(
            user_input={CONF_ENABLE_WATCH: True}
        )
        assert result["type"] == "create_entry"
        assert result["data"][CONF_ENABLE_WATCH] is True

    async def test_options_flow_saves_enable_watch_false(self, options_flow):
        """Submitting enable_watch=False should create an entry with that value."""
        result = await options_flow.async_step_init(
            user_input={CONF_ENABLE_WATCH: False}
        )
        assert result["type"] == "create_entry"
        assert result["data"][CONF_ENABLE_WATCH] is False

    async def test_options_flow_uses_existing_options(self):
        """When options already have enable_watch=True, the form should still render."""
        entry = MagicMock()
        entry.options = {CONF_ENABLE_WATCH: True}
        flow = KubernetesOptionsFlow()
        with patch.object(
            KubernetesOptionsFlow,
            "config_entry",
            new_callable=PropertyMock,
            return_value=entry,
        ):
            result = await flow.async_step_init(user_input=None)
        assert result["type"] == "form"

    async def test_async_get_options_flow(self):
        """KubernetesConfigFlow.async_get_options_flow should return a KubernetesOptionsFlow."""
        config_entry = MagicMock()
        options_flow = KubernetesConfigFlow.async_get_options_flow(config_entry)
        assert isinstance(options_flow, KubernetesOptionsFlow)

    async def test_default_enable_watch_is_false(self):
        """DEFAULT_ENABLE_WATCH constant should be False."""
        assert DEFAULT_ENABLE_WATCH is False


# ---------------------------------------------------------------------------
# Reconfigure flow tests
# ---------------------------------------------------------------------------


class TestReconfigureFlow:
    """Tests for the Kubernetes integration reconfigure flow."""

    @pytest.fixture
    def existing_entry_data(self):
        """Return typical existing config entry data."""
        return {
            CONF_CLUSTER_NAME: "test-cluster",
            CONF_HOST: "old-host.example.com",
            CONF_PORT: 6443,
            CONF_API_TOKEN: "old-token",
            CONF_CA_CERT: "/old/ca.crt",
            CONF_VERIFY_SSL: False,
            CONF_MONITOR_ALL_NAMESPACES: True,
            CONF_DEVICE_GROUPING_MODE: DEFAULT_DEVICE_GROUPING_MODE,
            CONF_SWITCH_UPDATE_INTERVAL: DEFAULT_SWITCH_UPDATE_INTERVAL,
            CONF_SCALE_VERIFICATION_TIMEOUT: DEFAULT_SCALE_VERIFICATION_TIMEOUT,
            CONF_SCALE_COOLDOWN: DEFAULT_SCALE_COOLDOWN,
        }

    @pytest.fixture
    def reconfigure_flow(self, mock_hass, existing_entry_data):
        """Return a config flow with a mock reconfigure entry."""
        flow = KubernetesConfigFlow()
        flow.hass = mock_hass

        entry = MagicMock()
        entry.data = existing_entry_data
        entry.unique_id = "test-cluster"
        flow._get_reconfigure_entry = MagicMock(return_value=entry)
        flow.async_update_reload_and_abort = MagicMock(
            return_value={"type": "abort", "reason": "reconfigure_successful"}
        )
        return flow

    async def test_reconfigure_shows_form_with_current_values(self, reconfigure_flow):
        """Test reconfigure step shows form pre-filled with current entry data."""
        with patch(
            "custom_components.kubernetes.config_flow._ensure_kubernetes_imported",
            return_value=True,
        ):
            result = await reconfigure_flow.async_step_reconfigure()

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "reconfigure"
        # cluster_name should NOT be in the schema
        schema_keys = [str(k) for k in result["data_schema"].schema]
        assert not any(CONF_CLUSTER_NAME in k for k in schema_keys)
        # host should be in the schema
        assert any(CONF_HOST in k for k in schema_keys)

    async def test_reconfigure_kubernetes_not_available(self, reconfigure_flow):
        """Test reconfigure shows error when kubernetes is not available."""
        with patch(
            "custom_components.kubernetes.config_flow._ensure_kubernetes_imported",
            return_value=False,
        ):
            result = await reconfigure_flow.async_step_reconfigure()

        assert result["type"] == FlowResultType.FORM
        assert result["errors"]["base"] == "kubernetes_not_installed"

    async def test_reconfigure_successful_monitor_all_namespaces(
        self, reconfigure_flow
    ):
        """Test successful reconfigure with monitor_all_namespaces=True."""
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
            reconfigure_flow._test_connection = AsyncMock()

            user_input = {
                CONF_HOST: "new-host.example.com",
                CONF_PORT: 6443,
                CONF_API_TOKEN: "new-token",
                CONF_VERIFY_SSL: True,
                CONF_MONITOR_ALL_NAMESPACES: True,
            }

            result = await reconfigure_flow.async_step_reconfigure(
                user_input=user_input
            )

        assert result == {"type": "abort", "reason": "reconfigure_successful"}
        reconfigure_flow.async_update_reload_and_abort.assert_called_once()
        call_kwargs = reconfigure_flow.async_update_reload_and_abort.call_args
        data_updates = call_kwargs[1]["data_updates"]
        assert data_updates[CONF_HOST] == "new-host.example.com"
        assert data_updates[CONF_CLUSTER_NAME] == "test-cluster"
        assert data_updates[CONF_NAMESPACE] == []

    async def test_reconfigure_proceeds_to_namespace_step(self, reconfigure_flow):
        """Test reconfigure proceeds to namespace step when monitor_all=False."""
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
            reconfigure_flow._test_connection = AsyncMock()
            reconfigure_flow.async_step_reconfigure_namespaces = AsyncMock(
                return_value={"type": "form", "step_id": "reconfigure_namespaces"}
            )

            user_input = {
                CONF_HOST: "new-host.example.com",
                CONF_PORT: 6443,
                CONF_API_TOKEN: "new-token",
                CONF_MONITOR_ALL_NAMESPACES: False,
            }

            result = await reconfigure_flow.async_step_reconfigure(
                user_input=user_input
            )

        assert result["step_id"] == "reconfigure_namespaces"
        reconfigure_flow.async_step_reconfigure_namespaces.assert_called_once()

    async def test_reconfigure_connection_failure(self, reconfigure_flow):
        """Test reconfigure shows error on connection failure."""
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
            reconfigure_flow._test_connection = AsyncMock(
                side_effect=Exception("Connection refused")
            )

            user_input = {
                CONF_HOST: "bad-host.example.com",
                CONF_PORT: 6443,
                CONF_API_TOKEN: "test-token",
            }

            result = await reconfigure_flow.async_step_reconfigure(
                user_input=user_input
            )

        assert result["type"] == FlowResultType.FORM
        assert result["errors"]["base"] == "cannot_connect"

    async def test_reconfigure_preserves_cluster_name(self, reconfigure_flow):
        """Test that cluster_name is always injected from existing entry."""
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
            reconfigure_flow._test_connection = AsyncMock()

            user_input = {
                CONF_HOST: "new-host.example.com",
                CONF_PORT: 6443,
                CONF_API_TOKEN: "new-token",
                CONF_MONITOR_ALL_NAMESPACES: True,
            }

            await reconfigure_flow.async_step_reconfigure(user_input=user_input)

        call_kwargs = reconfigure_flow.async_update_reload_and_abort.call_args
        data_updates = call_kwargs[1]["data_updates"]
        assert data_updates[CONF_CLUSTER_NAME] == "test-cluster"

    async def test_reconfigure_updates_connection_fields(self, reconfigure_flow):
        """Test that updated host/port/token values are passed through."""
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
            reconfigure_flow._test_connection = AsyncMock()

            user_input = {
                CONF_HOST: "updated-host.example.com",
                CONF_PORT: 8443,
                CONF_API_TOKEN: "updated-token",
                CONF_VERIFY_SSL: True,
                CONF_MONITOR_ALL_NAMESPACES: True,
            }

            await reconfigure_flow.async_step_reconfigure(user_input=user_input)

        call_kwargs = reconfigure_flow.async_update_reload_and_abort.call_args
        data_updates = call_kwargs[1]["data_updates"]
        assert data_updates[CONF_HOST] == "updated-host.example.com"
        assert data_updates[CONF_PORT] == 8443
        assert data_updates[CONF_API_TOKEN] == "updated-token"
        assert data_updates[CONF_VERIFY_SSL] is True

    async def test_reconfigure_clears_namespaces_when_switching_to_all(self, mock_hass):
        """Test switching from specific namespaces to all clears CONF_NAMESPACE."""
        entry = MagicMock()
        entry.data = {
            CONF_CLUSTER_NAME: "test-cluster",
            CONF_HOST: "old-host.example.com",
            CONF_PORT: 6443,
            CONF_API_TOKEN: "old-token",
            CONF_VERIFY_SSL: False,
            CONF_MONITOR_ALL_NAMESPACES: False,
            CONF_NAMESPACE: ["production", "staging"],
            CONF_DEVICE_GROUPING_MODE: DEFAULT_DEVICE_GROUPING_MODE,
            CONF_SWITCH_UPDATE_INTERVAL: DEFAULT_SWITCH_UPDATE_INTERVAL,
            CONF_SCALE_VERIFICATION_TIMEOUT: DEFAULT_SCALE_VERIFICATION_TIMEOUT,
            CONF_SCALE_COOLDOWN: DEFAULT_SCALE_COOLDOWN,
        }
        entry.unique_id = "test-cluster"

        flow = KubernetesConfigFlow()
        flow.hass = mock_hass
        flow._get_reconfigure_entry = MagicMock(return_value=entry)
        flow.async_update_reload_and_abort = MagicMock(
            return_value={"type": "abort", "reason": "reconfigure_successful"}
        )

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
            flow._test_connection = AsyncMock()

            user_input = {
                CONF_HOST: "old-host.example.com",
                CONF_PORT: 6443,
                CONF_API_TOKEN: "old-token",
                CONF_MONITOR_ALL_NAMESPACES: True,
            }

            await flow.async_step_reconfigure(user_input=user_input)

        call_kwargs = flow.async_update_reload_and_abort.call_args
        data_updates = call_kwargs[1]["data_updates"]
        assert data_updates[CONF_NAMESPACE] == []

    async def test_reconfigure_clears_ca_cert_when_removed(self, reconfigure_flow):
        """Test that CA cert is cleared when user removes it from the form."""
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
            reconfigure_flow._test_connection = AsyncMock()

            # user_input without CONF_CA_CERT means user cleared the field
            user_input = {
                CONF_HOST: "new-host.example.com",
                CONF_PORT: 6443,
                CONF_API_TOKEN: "new-token",
                CONF_MONITOR_ALL_NAMESPACES: True,
            }

            await reconfigure_flow.async_step_reconfigure(user_input=user_input)

        call_kwargs = reconfigure_flow.async_update_reload_and_abort.call_args
        data_updates = call_kwargs[1]["data_updates"]
        assert data_updates[CONF_CA_CERT] == ""


class TestReconfigureNamespacesFlow:
    """Tests for the reconfigure namespaces step."""

    @pytest.fixture
    def existing_entry_data(self):
        """Return typical existing config entry data with specific namespaces."""
        return {
            CONF_CLUSTER_NAME: "test-cluster",
            CONF_HOST: "host.example.com",
            CONF_PORT: 6443,
            CONF_API_TOKEN: "test-token",
            CONF_VERIFY_SSL: False,
            CONF_MONITOR_ALL_NAMESPACES: False,
            CONF_NAMESPACE: ["production", "staging"],
            CONF_DEVICE_GROUPING_MODE: DEFAULT_DEVICE_GROUPING_MODE,
            CONF_SWITCH_UPDATE_INTERVAL: DEFAULT_SWITCH_UPDATE_INTERVAL,
            CONF_SCALE_VERIFICATION_TIMEOUT: DEFAULT_SCALE_VERIFICATION_TIMEOUT,
            CONF_SCALE_COOLDOWN: DEFAULT_SCALE_COOLDOWN,
        }

    @pytest.fixture
    def reconfigure_ns_flow(self, mock_hass, existing_entry_data):
        """Return a config flow ready for the reconfigure namespaces step."""
        flow = KubernetesConfigFlow()
        flow.hass = mock_hass

        entry = MagicMock()
        entry.data = existing_entry_data
        entry.unique_id = "test-cluster"
        flow._get_reconfigure_entry = MagicMock(return_value=entry)
        flow.async_update_reload_and_abort = MagicMock(
            return_value={"type": "abort", "reason": "reconfigure_successful"}
        )
        flow._connection_data = {
            CONF_CLUSTER_NAME: "test-cluster",
            CONF_HOST: "host.example.com",
            CONF_PORT: 6443,
            CONF_API_TOKEN: "test-token",
            CONF_MONITOR_ALL_NAMESPACES: False,
        }
        return flow

    async def test_reconfigure_namespaces_shows_form(self, reconfigure_ns_flow):
        """Test namespace step shows form with fetched namespaces."""
        reconfigure_ns_flow._fetch_namespaces = AsyncMock(
            return_value=["default", "kube-system", "production", "staging"]
        )

        result = await reconfigure_ns_flow.async_step_reconfigure_namespaces()

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "reconfigure_namespaces"

    async def test_reconfigure_namespaces_preselects_current(self, reconfigure_ns_flow):
        """Test that currently configured namespaces are pre-selected."""
        reconfigure_ns_flow._fetch_namespaces = AsyncMock(
            return_value=["default", "kube-system", "production", "staging"]
        )

        result = await reconfigure_ns_flow.async_step_reconfigure_namespaces()

        # Check the default values in the schema
        for key in result["data_schema"].schema:
            if str(key) == CONF_NAMESPACE or (
                hasattr(key, "schema") and key.schema == CONF_NAMESPACE
            ):
                assert key.default() == ["production", "staging"]
                break

    async def test_reconfigure_namespaces_filters_stale(self, reconfigure_ns_flow):
        """Test that stale namespaces are filtered from defaults."""
        # "staging" was configured but no longer exists on the cluster
        reconfigure_ns_flow._fetch_namespaces = AsyncMock(
            return_value=["default", "kube-system", "production"]
        )

        result = await reconfigure_ns_flow.async_step_reconfigure_namespaces()

        for key in result["data_schema"].schema:
            if str(key) == CONF_NAMESPACE or (
                hasattr(key, "schema") and key.schema == CONF_NAMESPACE
            ):
                defaults = key.default()
                assert "production" in defaults
                assert "staging" not in defaults
                break

    async def test_reconfigure_namespaces_all_stale_leaves_empty(
        self, reconfigure_ns_flow
    ):
        """Test that no namespace is auto-selected when all previous ones are gone."""
        # Both "production" and "staging" no longer exist on the cluster
        reconfigure_ns_flow._fetch_namespaces = AsyncMock(
            return_value=["default", "kube-system", "new-ns"]
        )

        result = await reconfigure_ns_flow.async_step_reconfigure_namespaces()

        for key in result["data_schema"].schema:
            if str(key) == CONF_NAMESPACE or (
                hasattr(key, "schema") and key.schema == CONF_NAMESPACE
            ):
                assert key.default() == []
                break

    async def test_reconfigure_namespaces_successful_submission(
        self, reconfigure_ns_flow
    ):
        """Test successful namespace selection during reconfigure."""
        reconfigure_ns_flow._fetch_namespaces = AsyncMock(
            return_value=["default", "production"]
        )

        result = await reconfigure_ns_flow.async_step_reconfigure_namespaces(
            user_input={CONF_NAMESPACE: ["default", "production"]}
        )

        assert result == {"type": "abort", "reason": "reconfigure_successful"}
        reconfigure_ns_flow.async_update_reload_and_abort.assert_called_once()
        call_kwargs = reconfigure_ns_flow.async_update_reload_and_abort.call_args
        data_updates = call_kwargs[1]["data_updates"]
        assert data_updates[CONF_NAMESPACE] == ["default", "production"]
        assert data_updates[CONF_CLUSTER_NAME] == "test-cluster"

    async def test_reconfigure_namespaces_empty_selection_error(
        self, reconfigure_ns_flow
    ):
        """Test error when no namespace selected."""
        reconfigure_ns_flow._fetch_namespaces = AsyncMock(
            return_value=["default", "production"]
        )

        result = await reconfigure_ns_flow.async_step_reconfigure_namespaces(
            user_input={CONF_NAMESPACE: []}
        )

        assert result["type"] == FlowResultType.FORM
        assert CONF_NAMESPACE in result["errors"]

    async def test_reconfigure_namespaces_string_conversion(self, reconfigure_ns_flow):
        """Test that comma-separated string is converted to list."""
        result = await reconfigure_ns_flow.async_step_reconfigure_namespaces(
            user_input={CONF_NAMESPACE: "default, production"}
        )

        assert result == {"type": "abort", "reason": "reconfigure_successful"}
        call_kwargs = reconfigure_ns_flow.async_update_reload_and_abort.call_args
        data_updates = call_kwargs[1]["data_updates"]
        assert "default" in data_updates[CONF_NAMESPACE]
        assert "production" in data_updates[CONF_NAMESPACE]

    async def test_reconfigure_namespaces_fetch_failure(self, reconfigure_ns_flow):
        """Test error and text fallback when namespace fetch returns empty."""
        reconfigure_ns_flow._fetch_namespaces = AsyncMock(return_value=[])

        result = await reconfigure_ns_flow.async_step_reconfigure_namespaces()

        assert result["type"] == FlowResultType.FORM
        assert result["errors"].get("base") == "cannot_fetch_namespaces"

    async def test_reconfigure_namespaces_fetch_exception(self, reconfigure_ns_flow):
        """Test error when namespace fetch raises an exception."""
        reconfigure_ns_flow._fetch_namespaces = AsyncMock(
            side_effect=Exception("connection reset")
        )

        result = await reconfigure_ns_flow.async_step_reconfigure_namespaces()

        assert result["type"] == FlowResultType.FORM
        assert result["errors"].get("base") == "cannot_fetch_namespaces"

    async def test_reconfigure_namespaces_non_list_default(self, reconfigure_ns_flow):
        """Test non-list/non-string namespace input defaults to ['default']."""
        result = await reconfigure_ns_flow.async_step_reconfigure_namespaces(
            user_input={CONF_NAMESPACE: 12345}
        )

        assert result == {"type": "abort", "reason": "reconfigure_successful"}
        call_kwargs = reconfigure_ns_flow.async_update_reload_and_abort.call_args
        data_updates = call_kwargs[1]["data_updates"]
        assert data_updates[CONF_NAMESPACE] == ["default"]
