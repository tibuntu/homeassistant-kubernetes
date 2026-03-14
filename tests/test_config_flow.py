"""Tests for the Kubernetes integration config flow."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.kubernetes.config_flow import (
    KubernetesConfigFlow,
    KubernetesOptionsFlow,
)
from custom_components.kubernetes.const import (
    CONF_API_TOKEN,
    CONF_CA_CERT,
    CONF_CLUSTER_NAME,
    CONF_DEVICE_GROUPING_MODE,
    CONF_ENABLE_PANEL,
    CONF_ENABLE_WATCH,
    CONF_MONITOR_ALL_NAMESPACES,
    CONF_NAMESPACE,
    CONF_SCALE_COOLDOWN,
    CONF_SCALE_VERIFICATION_TIMEOUT,
    CONF_SWITCH_UPDATE_INTERVAL,
    CONF_VERIFY_SSL,
    DEFAULT_DEVICE_GROUPING_MODE,
    DEFAULT_ENABLE_PANEL,
    DEFAULT_ENABLE_WATCH,
    DEFAULT_PORT,
    DEFAULT_SCALE_COOLDOWN,
    DEFAULT_SCALE_VERIFICATION_TIMEOUT,
    DEFAULT_SWITCH_UPDATE_INTERVAL,
    DEFAULT_VERIFY_SSL,
    DOMAIN,
)


@pytest.fixture(autouse=True)
def register_config_flow(hass: HomeAssistant):
    """Register the kubernetes config flow handler with HA's flow manager.

    HA's _async_get_flow_handler checks two things:
    1. The config_flow module is marked as loaded in hass.data
    2. The handler class is in the HANDLERS registry
    Both are needed to avoid UnknownHandler / IntegrationNotFound.
    """
    from homeassistant.loader import DATA_COMPONENTS

    hass.data.setdefault(DATA_COMPONENTS, {})[f"{DOMAIN}.config_flow"] = (
        KubernetesConfigFlow
    )
    config_entries.HANDLERS[DOMAIN] = KubernetesConfigFlow
    yield
    config_entries.HANDLERS.pop(DOMAIN, None)
    hass.data.get(DATA_COMPONENTS, {}).pop(f"{DOMAIN}.config_flow", None)


@pytest.fixture(autouse=True)
def mock_setup_entry():
    """Prevent actual integration setup during config flow tests."""
    with patch(
        "custom_components.kubernetes.async_setup_entry",
        return_value=True,
    ):
        yield


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


# ---------------------------------------------------------------------------
# User step tests (real flow manager)
# ---------------------------------------------------------------------------


async def test_async_step_user_kubernetes_not_available(hass: HomeAssistant):
    """Test user step when kubernetes package is not available."""
    with patch(
        "custom_components.kubernetes.config_flow._ensure_kubernetes_imported",
        return_value=False,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"]["base"] == "kubernetes_not_installed"


async def test_async_step_user_initial_step(hass: HomeAssistant):
    """Test initial user step."""
    with patch(
        "custom_components.kubernetes.config_flow._ensure_kubernetes_imported",
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"


async def test_async_step_user_with_valid_input(hass: HomeAssistant):
    """Test user step with valid input."""
    with (
        patch(
            "custom_components.kubernetes.config_flow._ensure_kubernetes_imported",
            return_value=True,
        ),
        patch("custom_components.kubernetes.config_flow.KUBERNETES_AVAILABLE", True),
        patch.object(KubernetesConfigFlow, "_test_connection", new_callable=AsyncMock),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_CLUSTER_NAME: "test-cluster",
                CONF_HOST: "kubernetes.example.com",
                CONF_PORT: 6443,
                CONF_API_TOKEN: "test-token",
                CONF_MONITOR_ALL_NAMESPACES: True,
                CONF_VERIFY_SSL: False,
            },
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "test-cluster"
    assert result["data"][CONF_CLUSTER_NAME] == "test-cluster"


async def test_async_step_user_connection_test_fails(hass: HomeAssistant):
    """Test user step when connection test fails."""
    with (
        patch(
            "custom_components.kubernetes.config_flow._ensure_kubernetes_imported",
            return_value=True,
        ),
        patch("custom_components.kubernetes.config_flow.KUBERNETES_AVAILABLE", True),
        patch.object(
            KubernetesConfigFlow,
            "_test_connection",
            new_callable=AsyncMock,
            side_effect=Exception("Connection failed"),
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_CLUSTER_NAME: "test-cluster",
                CONF_HOST: "kubernetes.example.com",
                CONF_API_TOKEN: "test-token",
            },
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"]["base"] == "cannot_connect"


async def test_async_step_user_duplicate_entry(hass: HomeAssistant):
    """Test user step with duplicate entry."""
    existing = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_CLUSTER_NAME: "test-cluster", CONF_HOST: "old-host"},
        unique_id="test-cluster",
    )
    existing.add_to_hass(hass)

    mock_integration = MagicMock()
    mock_integration.single_config_entry = False

    with (
        patch(
            "custom_components.kubernetes.config_flow._ensure_kubernetes_imported",
            return_value=True,
        ),
        patch("custom_components.kubernetes.config_flow.KUBERNETES_AVAILABLE", True),
        patch.object(KubernetesConfigFlow, "_test_connection", new_callable=AsyncMock),
        patch(
            "homeassistant.config_entries.loader.async_get_integration",
            return_value=mock_integration,
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_CLUSTER_NAME: "test-cluster",
                CONF_HOST: "kubernetes.example.com",
                CONF_API_TOKEN: "test-token",
                CONF_MONITOR_ALL_NAMESPACES: True,
            },
        )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_async_step_user_with_defaults(hass: HomeAssistant):
    """Test user step with default values."""
    with (
        patch(
            "custom_components.kubernetes.config_flow._ensure_kubernetes_imported",
            return_value=True,
        ),
        patch("custom_components.kubernetes.config_flow.KUBERNETES_AVAILABLE", True),
        patch.object(KubernetesConfigFlow, "_test_connection", new_callable=AsyncMock),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_CLUSTER_NAME: "test-cluster",
                CONF_HOST: "test-cluster.example.com",
                CONF_API_TOKEN: "test-token",
                CONF_MONITOR_ALL_NAMESPACES: True,
            },
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "test-cluster"
    assert result["data"][CONF_PORT] == DEFAULT_PORT
    assert result["data"][CONF_CLUSTER_NAME] == "test-cluster"
    assert result["data"][CONF_VERIFY_SSL] == DEFAULT_VERIFY_SSL


# ---------------------------------------------------------------------------
# Namespace step tests (real flow manager, multi-step)
# ---------------------------------------------------------------------------


async def test_async_step_user_goes_to_namespaces_step(hass: HomeAssistant):
    """Test that user step proceeds to namespace step when monitor_all_namespaces is False."""
    with (
        patch(
            "custom_components.kubernetes.config_flow._ensure_kubernetes_imported",
            return_value=True,
        ),
        patch("custom_components.kubernetes.config_flow.KUBERNETES_AVAILABLE", True),
        patch.object(KubernetesConfigFlow, "_test_connection", new_callable=AsyncMock),
        patch.object(
            KubernetesConfigFlow,
            "_fetch_namespaces",
            new_callable=AsyncMock,
            return_value=["default", "kube-system", "production"],
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_CLUSTER_NAME: "test-cluster",
                CONF_HOST: "test-cluster.example.com",
                CONF_API_TOKEN: "test-token",
                CONF_MONITOR_ALL_NAMESPACES: False,
            },
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "namespaces"


async def test_async_step_namespaces(hass: HomeAssistant):
    """Test namespace selection step."""
    with (
        patch(
            "custom_components.kubernetes.config_flow._ensure_kubernetes_imported",
            return_value=True,
        ),
        patch("custom_components.kubernetes.config_flow.KUBERNETES_AVAILABLE", True),
        patch.object(KubernetesConfigFlow, "_test_connection", new_callable=AsyncMock),
        patch.object(
            KubernetesConfigFlow,
            "_fetch_namespaces",
            new_callable=AsyncMock,
            return_value=["default", "kube-system", "production"],
        ),
    ):
        # Step 1: User input with monitor_all=False
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_CLUSTER_NAME: "test-cluster",
                CONF_HOST: "test-cluster.example.com",
                CONF_API_TOKEN: "test-token",
                CONF_MONITOR_ALL_NAMESPACES: False,
            },
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "namespaces"

        # Step 2: Namespace selection
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_NAMESPACE: ["default", "production"]},
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "test-cluster"
    assert result["data"][CONF_NAMESPACE] == ["default", "production"]
    assert result["data"][CONF_CLUSTER_NAME] == "test-cluster"


async def test_async_step_namespaces_empty_namespace_error(hass: HomeAssistant):
    """Test namespace step returns error when no namespace selected."""
    with (
        patch(
            "custom_components.kubernetes.config_flow._ensure_kubernetes_imported",
            return_value=True,
        ),
        patch("custom_components.kubernetes.config_flow.KUBERNETES_AVAILABLE", True),
        patch.object(KubernetesConfigFlow, "_test_connection", new_callable=AsyncMock),
        patch.object(
            KubernetesConfigFlow,
            "_fetch_namespaces",
            new_callable=AsyncMock,
            return_value=["default", "kube-system"],
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_CLUSTER_NAME: "test-cluster",
                CONF_HOST: "test-host",
                CONF_API_TOKEN: "test-token",
                CONF_MONITOR_ALL_NAMESPACES: False,
            },
        )
        assert result["step_id"] == "namespaces"

        # Pass empty namespace list
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_NAMESPACE: []},
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "namespaces"
    assert CONF_NAMESPACE in result["errors"]


async def test_async_step_namespaces_string_namespace_conversion(
    hass: HomeAssistant,
):
    """Test namespace step converts comma-separated string input to list.

    The real flow manager validates input against the schema, so a raw string
    can only arrive via the text-input fallback (when namespace fetch fails)
    or from non-UI callers. Test the conversion logic via direct method call.
    """
    flow = KubernetesConfigFlow()
    flow.hass = hass
    flow.context = {"source": config_entries.SOURCE_USER}
    flow._connection_data = {
        CONF_CLUSTER_NAME: "test-cluster",
        CONF_HOST: "test-host",
        CONF_PORT: 6443,
        CONF_API_TOKEN: "test-token",
    }

    result = await flow.async_step_namespaces({CONF_NAMESPACE: "default, production"})

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert "default" in result["data"][CONF_NAMESPACE]
    assert "production" in result["data"][CONF_NAMESPACE]


async def test_async_step_namespaces_non_list_namespace(hass: HomeAssistant):
    """Test namespace step converts non-list/non-string namespace to default.

    The real flow manager validates input against the schema, so a non-list
    value can only arrive from non-UI callers. Test the conversion logic
    via direct method call.
    """
    flow = KubernetesConfigFlow()
    flow.hass = hass
    flow.context = {"source": config_entries.SOURCE_USER}
    flow._connection_data = {
        CONF_CLUSTER_NAME: "test-cluster",
        CONF_HOST: "test-host",
        CONF_PORT: 6443,
        CONF_API_TOKEN: "test-token",
    }

    result = await flow.async_step_namespaces({CONF_NAMESPACE: 12345})

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_NAMESPACE] == ["default"]


async def test_async_step_namespaces_no_namespaces_fetched(hass: HomeAssistant):
    """Test namespace step shows error when no namespaces fetched."""
    with (
        patch(
            "custom_components.kubernetes.config_flow._ensure_kubernetes_imported",
            return_value=True,
        ),
        patch("custom_components.kubernetes.config_flow.KUBERNETES_AVAILABLE", True),
        patch.object(KubernetesConfigFlow, "_test_connection", new_callable=AsyncMock),
        patch.object(
            KubernetesConfigFlow,
            "_fetch_namespaces",
            new_callable=AsyncMock,
            return_value=[],
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_CLUSTER_NAME: "test-cluster",
                CONF_HOST: "test-host",
                CONF_API_TOKEN: "test-token",
                CONF_MONITOR_ALL_NAMESPACES: False,
            },
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"].get("base") == "cannot_fetch_namespaces"


async def test_async_step_namespaces_fetch_exception(hass: HomeAssistant):
    """Test namespace step handles fetch exception."""
    with (
        patch(
            "custom_components.kubernetes.config_flow._ensure_kubernetes_imported",
            return_value=True,
        ),
        patch("custom_components.kubernetes.config_flow.KUBERNETES_AVAILABLE", True),
        patch.object(KubernetesConfigFlow, "_test_connection", new_callable=AsyncMock),
        patch.object(
            KubernetesConfigFlow,
            "_fetch_namespaces",
            new_callable=AsyncMock,
            side_effect=Exception("Network error"),
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_CLUSTER_NAME: "test-cluster",
                CONF_HOST: "test-host",
                CONF_API_TOKEN: "test-token",
                CONF_MONITOR_ALL_NAMESPACES: False,
            },
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"].get("base") == "cannot_fetch_namespaces"


# ---------------------------------------------------------------------------
# Internal method tests (_test_connection, _test_connection_aiohttp,
# _fetch_namespaces, _ensure_kubernetes_imported)
# These test private methods directly and keep direct flow instantiation.
# ---------------------------------------------------------------------------


async def test_test_connection_success(hass: HomeAssistant):
    """Test successful connection test."""
    flow = KubernetesConfigFlow()
    flow.hass = hass

    with (
        patch(
            "custom_components.kubernetes.config_flow._ensure_kubernetes_imported",
            return_value=True,
        ),
        patch("custom_components.kubernetes.config_flow.client") as mock_client,
    ):
        mock_api = MagicMock()
        mock_client.Configuration.return_value = MagicMock()
        mock_client.CoreV1Api.return_value = mock_api
        mock_client.ApiClient.return_value = MagicMock()

        loop = asyncio.get_running_loop()
        with patch.object(loop, "run_in_executor", new_callable=AsyncMock):
            await flow._test_connection(
                {
                    CONF_HOST: "test-host",
                    CONF_PORT: 6443,
                    CONF_API_TOKEN: "test-token",
                    CONF_VERIFY_SSL: False,
                }
            )


async def test_test_connection_failure(hass: HomeAssistant):
    """Test failed connection test."""
    flow = KubernetesConfigFlow()
    flow.hass = hass

    with patch("custom_components.kubernetes.config_flow.client") as mock_client:
        mock_api = MagicMock()
        mock_client.CoreV1Api.return_value = mock_api
        mock_api.get_api_resources.side_effect = Exception("Connection failed")

        with pytest.raises(Exception, match="Connection test failed"):
            await flow._test_connection(
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


async def test_test_connection_kubernetes_not_available(hass: HomeAssistant):
    """Test _test_connection raises when kubernetes not available."""
    with patch(
        "custom_components.kubernetes.config_flow._ensure_kubernetes_imported",
        return_value=False,
    ):
        flow = KubernetesConfigFlow()
        flow.hass = hass

        with pytest.raises(ValueError, match="Kubernetes package is not installed"):
            await flow._test_connection(
                {
                    CONF_HOST: "test-host",
                    CONF_API_TOKEN: "test-token",
                }
            )


async def test_test_connection_empty_host(hass: HomeAssistant):
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
            flow.hass = hass

            with pytest.raises(ValueError, match="Host is required"):
                await flow._test_connection(
                    {
                        CONF_HOST: "",
                        CONF_API_TOKEN: "test-token",
                    }
                )
    finally:
        cf_module.KUBERNETES_AVAILABLE = original


async def test_test_connection_empty_token(hass: HomeAssistant):
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
            flow.hass = hass

            with pytest.raises(ValueError, match="API token is required"):
                await flow._test_connection(
                    {
                        CONF_HOST: "test-host",
                        CONF_API_TOKEN: "",
                    }
                )
    finally:
        cf_module.KUBERNETES_AVAILABLE = original


async def test_test_connection_with_ca_cert(hass: HomeAssistant):
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
            flow.hass = hass

            import asyncio

            loop = asyncio.get_running_loop()

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

            assert mock_config.ssl_ca_cert == "/path/to/ca.crt"
    finally:
        cf_module.KUBERNETES_AVAILABLE = original_available
        cf_module.client = original_client


async def test_test_connection_api_exception_aiohttp_success(hass: HomeAssistant):
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
            flow.hass = hass
            flow._test_connection_aiohttp = AsyncMock(return_value=True)

            import asyncio

            loop = asyncio.get_running_loop()

            with patch.object(
                loop,
                "run_in_executor",
                new=AsyncMock(side_effect=FakeApiException()),
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
        cf_module.ApiException = original_api_exc


async def test_test_connection_api_exception_aiohttp_failure(hass: HomeAssistant):
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
            flow.hass = hass
            flow._test_connection_aiohttp = AsyncMock(return_value=False)

            import asyncio

            loop = asyncio.get_running_loop()

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


async def test_test_connection_generic_exception_aiohttp_success(
    hass: HomeAssistant,
):
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
            flow.hass = hass
            flow._test_connection_aiohttp = AsyncMock(return_value=True)

            import asyncio

            loop = asyncio.get_running_loop()

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


async def test_test_connection_generic_exception_aiohttp_failure(
    hass: HomeAssistant,
):
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
            flow.hass = hass
            flow._test_connection_aiohttp = AsyncMock(return_value=False)

            import asyncio

            loop = asyncio.get_running_loop()

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


async def test_test_connection_aiohttp_success(hass: HomeAssistant):
    """Test _test_connection_aiohttp returns True on 200 response."""
    flow = KubernetesConfigFlow()
    flow.hass = hass

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


async def test_test_connection_aiohttp_error_status(hass: HomeAssistant):
    """Test _test_connection_aiohttp returns False on non-200 response."""
    flow = KubernetesConfigFlow()
    flow.hass = hass

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


async def test_test_connection_aiohttp_exception(hass: HomeAssistant):
    """Test _test_connection_aiohttp returns False on exception."""
    flow = KubernetesConfigFlow()
    flow.hass = hass

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


async def test_fetch_namespaces_success(hass: HomeAssistant):
    """Test _fetch_namespaces returns sorted namespace list on success."""
    flow = KubernetesConfigFlow()
    flow.hass = hass

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


async def test_fetch_namespaces_error_status(hass: HomeAssistant):
    """Test _fetch_namespaces returns empty list on non-200 response."""
    flow = KubernetesConfigFlow()
    flow.hass = hass

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


async def test_fetch_namespaces_client_error(hass: HomeAssistant):
    """Test _fetch_namespaces returns empty list on aiohttp.ClientError."""
    import aiohttp as aiohttp_mod

    flow = KubernetesConfigFlow()
    flow.hass = hass

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


async def test_fetch_namespaces_generic_exception(hass: HomeAssistant):
    """Test _fetch_namespaces returns empty list on generic exception."""
    flow = KubernetesConfigFlow()
    flow.hass = hass

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


# ---------------------------------------------------------------------------
# Options flow tests (real options flow manager)
# ---------------------------------------------------------------------------


class TestKubernetesOptionsFlow:
    """Tests for the Kubernetes integration options flow."""

    @pytest.fixture
    def mock_config_entry(self, hass: HomeAssistant) -> MockConfigEntry:
        """Return a mock config entry added to hass."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_CLUSTER_NAME: "test-cluster",
                CONF_HOST: "host.example.com",
                CONF_API_TOKEN: "token",
            },
            options={},
        )
        entry.add_to_hass(hass)
        return entry

    async def test_options_flow_returns_form(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ):
        """Calling the flow with no input should return the init form."""
        result = await hass.config_entries.options.async_init(
            mock_config_entry.entry_id
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "init"

    async def test_options_flow_defaults_to_watch_disabled(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ):
        """Default value for enable_watch should be False."""
        result = await hass.config_entries.options.async_init(
            mock_config_entry.entry_id
        )
        schema_keys = [str(k) for k in result["data_schema"].schema]
        assert any(CONF_ENABLE_WATCH in k for k in schema_keys)

    async def test_options_flow_saves_enable_watch_true(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ):
        """Submitting enable_watch=True should create an entry with that value."""
        result = await hass.config_entries.options.async_init(
            mock_config_entry.entry_id
        )
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={CONF_ENABLE_WATCH: True},
        )
        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["data"][CONF_ENABLE_WATCH] is True

    async def test_options_flow_saves_enable_watch_false(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ):
        """Submitting enable_watch=False should create an entry with that value."""
        result = await hass.config_entries.options.async_init(
            mock_config_entry.entry_id
        )
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={CONF_ENABLE_WATCH: False},
        )
        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["data"][CONF_ENABLE_WATCH] is False

    async def test_options_flow_uses_existing_options(self, hass: HomeAssistant):
        """When options already have enable_watch=True, the form should still render."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_CLUSTER_NAME: "test-cluster",
                CONF_HOST: "host.example.com",
                CONF_API_TOKEN: "token",
            },
            options={CONF_ENABLE_WATCH: True},
        )
        entry.add_to_hass(hass)

        result = await hass.config_entries.options.async_init(entry.entry_id)
        assert result["type"] is FlowResultType.FORM

    def test_async_get_options_flow(self):
        """KubernetesConfigFlow.async_get_options_flow should return a KubernetesOptionsFlow."""
        config_entry = MagicMock()
        options_flow = KubernetesConfigFlow.async_get_options_flow(config_entry)
        assert isinstance(options_flow, KubernetesOptionsFlow)

    def test_default_enable_watch_is_false(self):
        """DEFAULT_ENABLE_WATCH constant should be False."""
        assert DEFAULT_ENABLE_WATCH is False

    async def test_options_flow_includes_enable_panel(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ):
        """Options form should include the enable_panel field."""
        result = await hass.config_entries.options.async_init(
            mock_config_entry.entry_id
        )
        schema_keys = [str(k) for k in result["data_schema"].schema]
        assert any(CONF_ENABLE_PANEL in k for k in schema_keys)

    def test_options_flow_defaults_panel_enabled(self):
        """Default value for enable_panel should be True."""
        assert DEFAULT_ENABLE_PANEL is True

    async def test_options_flow_saves_panel_disabled(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ):
        """Submitting enable_panel=False should create an entry with that value."""
        result = await hass.config_entries.options.async_init(
            mock_config_entry.entry_id
        )
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={CONF_ENABLE_PANEL: False, CONF_ENABLE_WATCH: False},
        )
        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["data"][CONF_ENABLE_PANEL] is False


# ---------------------------------------------------------------------------
# Reconfigure flow tests (real flow manager)
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
    def mock_config_entry(
        self, hass: HomeAssistant, existing_entry_data
    ) -> MockConfigEntry:
        """Return a config entry added to hass for reconfigure tests."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data=existing_entry_data,
            unique_id="test-cluster",
        )
        entry.add_to_hass(hass)
        return entry

    async def _init_reconfigure(self, hass, entry):
        """Helper to start a reconfigure flow."""
        return await hass.config_entries.flow.async_init(
            DOMAIN,
            context={
                "source": config_entries.SOURCE_RECONFIGURE,
                "entry_id": entry.entry_id,
            },
        )

    async def test_reconfigure_shows_form_with_current_values(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ):
        """Test reconfigure step shows form pre-filled with current entry data."""
        with patch(
            "custom_components.kubernetes.config_flow._ensure_kubernetes_imported",
            return_value=True,
        ):
            result = await self._init_reconfigure(hass, mock_config_entry)

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "reconfigure"
        schema_keys = [str(k) for k in result["data_schema"].schema]
        assert not any(CONF_CLUSTER_NAME in k for k in schema_keys)
        assert any(CONF_HOST in k for k in schema_keys)

    async def test_reconfigure_kubernetes_not_available(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ):
        """Test reconfigure shows error when kubernetes is not available."""
        with patch(
            "custom_components.kubernetes.config_flow._ensure_kubernetes_imported",
            return_value=False,
        ):
            result = await self._init_reconfigure(hass, mock_config_entry)

        assert result["type"] is FlowResultType.FORM
        assert result["errors"]["base"] == "kubernetes_not_installed"

    async def test_reconfigure_successful_monitor_all_namespaces(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
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
            patch.object(
                KubernetesConfigFlow, "_test_connection", new_callable=AsyncMock
            ),
        ):
            result = await self._init_reconfigure(hass, mock_config_entry)

            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                user_input={
                    CONF_HOST: "new-host.example.com",
                    CONF_PORT: 6443,
                    CONF_API_TOKEN: "new-token",
                    CONF_VERIFY_SSL: True,
                    CONF_MONITOR_ALL_NAMESPACES: True,
                },
            )

        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == "reconfigure_successful"
        assert mock_config_entry.data[CONF_HOST] == "new-host.example.com"
        assert mock_config_entry.data[CONF_CLUSTER_NAME] == "test-cluster"
        assert mock_config_entry.data[CONF_NAMESPACE] == []

    async def test_reconfigure_proceeds_to_namespace_step(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ):
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
            patch.object(
                KubernetesConfigFlow, "_test_connection", new_callable=AsyncMock
            ),
            patch.object(
                KubernetesConfigFlow,
                "_fetch_namespaces",
                new_callable=AsyncMock,
                return_value=["default", "kube-system", "production"],
            ),
        ):
            result = await self._init_reconfigure(hass, mock_config_entry)

            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                user_input={
                    CONF_HOST: "new-host.example.com",
                    CONF_PORT: 6443,
                    CONF_API_TOKEN: "new-token",
                    CONF_MONITOR_ALL_NAMESPACES: False,
                },
            )

        assert result["step_id"] == "reconfigure_namespaces"

    async def test_reconfigure_connection_failure(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ):
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
            patch.object(
                KubernetesConfigFlow,
                "_test_connection",
                new_callable=AsyncMock,
                side_effect=Exception("Connection refused"),
            ),
        ):
            result = await self._init_reconfigure(hass, mock_config_entry)

            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                user_input={
                    CONF_HOST: "bad-host.example.com",
                    CONF_PORT: 6443,
                    CONF_API_TOKEN: "test-token",
                },
            )

        assert result["type"] is FlowResultType.FORM
        assert result["errors"]["base"] == "cannot_connect"

    async def test_reconfigure_preserves_cluster_name(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ):
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
            patch.object(
                KubernetesConfigFlow, "_test_connection", new_callable=AsyncMock
            ),
        ):
            result = await self._init_reconfigure(hass, mock_config_entry)

            await hass.config_entries.flow.async_configure(
                result["flow_id"],
                user_input={
                    CONF_HOST: "new-host.example.com",
                    CONF_PORT: 6443,
                    CONF_API_TOKEN: "new-token",
                    CONF_MONITOR_ALL_NAMESPACES: True,
                },
            )

        assert mock_config_entry.data[CONF_CLUSTER_NAME] == "test-cluster"

    async def test_reconfigure_updates_connection_fields(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ):
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
            patch.object(
                KubernetesConfigFlow, "_test_connection", new_callable=AsyncMock
            ),
        ):
            result = await self._init_reconfigure(hass, mock_config_entry)

            await hass.config_entries.flow.async_configure(
                result["flow_id"],
                user_input={
                    CONF_HOST: "updated-host.example.com",
                    CONF_PORT: 8443,
                    CONF_API_TOKEN: "updated-token",
                    CONF_VERIFY_SSL: True,
                    CONF_MONITOR_ALL_NAMESPACES: True,
                },
            )

        assert mock_config_entry.data[CONF_HOST] == "updated-host.example.com"
        assert mock_config_entry.data[CONF_PORT] == 8443
        assert mock_config_entry.data[CONF_API_TOKEN] == "updated-token"
        assert mock_config_entry.data[CONF_VERIFY_SSL] is True

    async def test_reconfigure_clears_namespaces_when_switching_to_all(
        self, hass: HomeAssistant
    ):
        """Test switching from specific namespaces to all clears CONF_NAMESPACE."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
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
            },
            unique_id="test-cluster",
        )
        entry.add_to_hass(hass)

        with (
            patch(
                "custom_components.kubernetes.config_flow._ensure_kubernetes_imported",
                return_value=True,
            ),
            patch(
                "custom_components.kubernetes.config_flow.KUBERNETES_AVAILABLE",
                True,
            ),
            patch.object(
                KubernetesConfigFlow, "_test_connection", new_callable=AsyncMock
            ),
        ):
            result = await self._init_reconfigure(hass, entry)

            await hass.config_entries.flow.async_configure(
                result["flow_id"],
                user_input={
                    CONF_HOST: "old-host.example.com",
                    CONF_PORT: 6443,
                    CONF_API_TOKEN: "old-token",
                    CONF_MONITOR_ALL_NAMESPACES: True,
                },
            )

        assert entry.data[CONF_NAMESPACE] == []

    async def test_reconfigure_clears_ca_cert_when_removed(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ):
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
            patch.object(
                KubernetesConfigFlow, "_test_connection", new_callable=AsyncMock
            ),
        ):
            result = await self._init_reconfigure(hass, mock_config_entry)

            await hass.config_entries.flow.async_configure(
                result["flow_id"],
                user_input={
                    CONF_HOST: "new-host.example.com",
                    CONF_PORT: 6443,
                    CONF_API_TOKEN: "new-token",
                    CONF_MONITOR_ALL_NAMESPACES: True,
                },
            )

        assert mock_config_entry.data[CONF_CA_CERT] == ""


# ---------------------------------------------------------------------------
# Reconfigure namespaces tests (real flow manager)
# ---------------------------------------------------------------------------


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
    def mock_config_entry(
        self, hass: HomeAssistant, existing_entry_data
    ) -> MockConfigEntry:
        """Return a config entry added to hass for reconfigure tests."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data=existing_entry_data,
            unique_id="test-cluster",
        )
        entry.add_to_hass(hass)
        return entry

    async def _init_reconfigure_to_namespaces(self, hass, entry, fetch_return):
        """Helper to start reconfigure and advance to namespace step."""
        with (
            patch(
                "custom_components.kubernetes.config_flow._ensure_kubernetes_imported",
                return_value=True,
            ),
            patch(
                "custom_components.kubernetes.config_flow.KUBERNETES_AVAILABLE",
                True,
            ),
            patch.object(
                KubernetesConfigFlow, "_test_connection", new_callable=AsyncMock
            ),
            patch.object(
                KubernetesConfigFlow,
                "_fetch_namespaces",
                new_callable=AsyncMock,
                return_value=fetch_return,
            ),
        ):
            result = await hass.config_entries.flow.async_init(
                DOMAIN,
                context={
                    "source": config_entries.SOURCE_RECONFIGURE,
                    "entry_id": entry.entry_id,
                },
            )
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                user_input={
                    CONF_HOST: "host.example.com",
                    CONF_PORT: 6443,
                    CONF_API_TOKEN: "test-token",
                    CONF_MONITOR_ALL_NAMESPACES: False,
                },
            )
            return result

    async def test_reconfigure_namespaces_shows_form(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ):
        """Test namespace step shows form with fetched namespaces."""
        result = await self._init_reconfigure_to_namespaces(
            hass,
            mock_config_entry,
            ["default", "kube-system", "production", "staging"],
        )

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "reconfigure_namespaces"

    async def test_reconfigure_namespaces_preselects_current(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ):
        """Test that currently configured namespaces are pre-selected."""
        result = await self._init_reconfigure_to_namespaces(
            hass,
            mock_config_entry,
            ["default", "kube-system", "production", "staging"],
        )

        for key in result["data_schema"].schema:
            if str(key) == CONF_NAMESPACE or (
                hasattr(key, "schema") and key.schema == CONF_NAMESPACE
            ):
                assert key.default() == ["production", "staging"]
                break
        else:
            pytest.fail(f"{CONF_NAMESPACE} not found in schema")

    async def test_reconfigure_namespaces_filters_stale(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ):
        """Test that stale namespaces are filtered from defaults."""
        # "staging" was configured but no longer exists on the cluster
        result = await self._init_reconfigure_to_namespaces(
            hass,
            mock_config_entry,
            ["default", "kube-system", "production"],
        )

        for key in result["data_schema"].schema:
            if str(key) == CONF_NAMESPACE or (
                hasattr(key, "schema") and key.schema == CONF_NAMESPACE
            ):
                defaults = key.default()
                assert "production" in defaults
                assert "staging" not in defaults
                break
        else:
            pytest.fail(f"{CONF_NAMESPACE} not found in schema")

    async def test_reconfigure_namespaces_all_stale_leaves_empty(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ):
        """Test that no namespace is auto-selected when all previous ones are gone."""
        result = await self._init_reconfigure_to_namespaces(
            hass,
            mock_config_entry,
            ["default", "kube-system", "new-ns"],
        )

        for key in result["data_schema"].schema:
            if str(key) == CONF_NAMESPACE or (
                hasattr(key, "schema") and key.schema == CONF_NAMESPACE
            ):
                assert key.default() == []
                break
        else:
            pytest.fail(f"{CONF_NAMESPACE} not found in schema")

    async def test_reconfigure_namespaces_successful_submission(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ):
        """Test successful namespace selection during reconfigure."""
        result = await self._init_reconfigure_to_namespaces(
            hass,
            mock_config_entry,
            ["default", "production"],
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_NAMESPACE: ["default", "production"]},
        )

        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == "reconfigure_successful"
        assert mock_config_entry.data[CONF_NAMESPACE] == ["default", "production"]
        assert mock_config_entry.data[CONF_CLUSTER_NAME] == "test-cluster"

    async def test_reconfigure_namespaces_empty_selection_error(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ):
        """Test error when no namespace selected."""
        result = await self._init_reconfigure_to_namespaces(
            hass,
            mock_config_entry,
            ["default", "production"],
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_NAMESPACE: []},
        )

        assert result["type"] is FlowResultType.FORM
        assert CONF_NAMESPACE in result["errors"]

    async def test_reconfigure_namespaces_string_conversion(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ):
        """Test that comma-separated string is converted to list.

        The real flow manager validates input against the schema, so a raw
        string can only arrive via the text-input fallback or non-UI callers.
        Test the conversion logic via direct method call.
        """
        flow = KubernetesConfigFlow()
        flow.hass = hass
        flow._connection_data = {
            CONF_CLUSTER_NAME: "test-cluster",
            CONF_HOST: "host.example.com",
            CONF_PORT: 6443,
            CONF_API_TOKEN: "test-token",
        }
        flow.handler = DOMAIN
        flow.context = {
            "source": config_entries.SOURCE_RECONFIGURE,
            "entry_id": mock_config_entry.entry_id,
        }

        result = await flow.async_step_reconfigure_namespaces(
            {CONF_NAMESPACE: "default, production"}
        )

        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == "reconfigure_successful"
        assert "default" in mock_config_entry.data[CONF_NAMESPACE]
        assert "production" in mock_config_entry.data[CONF_NAMESPACE]

    async def test_reconfigure_namespaces_fetch_failure(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ):
        """Test error and text fallback when namespace fetch returns empty."""
        result = await self._init_reconfigure_to_namespaces(hass, mock_config_entry, [])

        assert result["type"] is FlowResultType.FORM
        assert result["errors"].get("base") == "cannot_fetch_namespaces"

    async def test_reconfigure_namespaces_fetch_exception(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ):
        """Test error when namespace fetch raises an exception."""
        with (
            patch(
                "custom_components.kubernetes.config_flow._ensure_kubernetes_imported",
                return_value=True,
            ),
            patch(
                "custom_components.kubernetes.config_flow.KUBERNETES_AVAILABLE",
                True,
            ),
            patch.object(
                KubernetesConfigFlow, "_test_connection", new_callable=AsyncMock
            ),
            patch.object(
                KubernetesConfigFlow,
                "_fetch_namespaces",
                new_callable=AsyncMock,
                side_effect=Exception("connection reset"),
            ),
        ):
            result = await hass.config_entries.flow.async_init(
                DOMAIN,
                context={
                    "source": config_entries.SOURCE_RECONFIGURE,
                    "entry_id": mock_config_entry.entry_id,
                },
            )
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                user_input={
                    CONF_HOST: "host.example.com",
                    CONF_PORT: 6443,
                    CONF_API_TOKEN: "test-token",
                    CONF_MONITOR_ALL_NAMESPACES: False,
                },
            )

        assert result["type"] is FlowResultType.FORM
        assert result["errors"].get("base") == "cannot_fetch_namespaces"

    async def test_reconfigure_namespaces_non_list_default(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ):
        """Test non-list/non-string namespace input defaults to ['default'].

        The real flow manager validates input against the schema, so a non-list
        value can only arrive from non-UI callers. Test the conversion logic
        via direct method call.
        """
        flow = KubernetesConfigFlow()
        flow.hass = hass
        flow._connection_data = {
            CONF_CLUSTER_NAME: "test-cluster",
            CONF_HOST: "host.example.com",
            CONF_PORT: 6443,
            CONF_API_TOKEN: "test-token",
        }
        flow.handler = DOMAIN
        flow.context = {
            "source": config_entries.SOURCE_RECONFIGURE,
            "entry_id": mock_config_entry.entry_id,
        }

        result = await flow.async_step_reconfigure_namespaces({CONF_NAMESPACE: 12345})

        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == "reconfigure_successful"
        assert mock_config_entry.data[CONF_NAMESPACE] == ["default"]


# ---------------------------------------------------------------------------
# Additional coverage: _test_connection edge cases
# ---------------------------------------------------------------------------


async def test_test_connection_strips_https_prefix(hass: HomeAssistant):
    """Test _test_connection strips https:// prefix from host."""
    import custom_components.kubernetes.config_flow as cf_module

    original_available = cf_module.KUBERNETES_AVAILABLE
    original_client = cf_module.client
    cf_module.KUBERNETES_AVAILABLE = True

    mock_k8s_client = MagicMock()
    mock_config = MagicMock()
    mock_k8s_client.Configuration.return_value = mock_config
    mock_k8s_client.ApiClient.return_value = MagicMock()
    mock_k8s_client.CoreV1Api.return_value = MagicMock()
    cf_module.client = mock_k8s_client

    try:
        with patch(
            "custom_components.kubernetes.config_flow._ensure_kubernetes_imported",
            return_value=True,
        ):
            flow = KubernetesConfigFlow()
            flow.hass = hass

            import asyncio

            loop = asyncio.get_running_loop()
            user_input = {
                CONF_HOST: "https://my-cluster.example.com",
                CONF_API_TOKEN: "test-token",
                CONF_VERIFY_SSL: False,
            }

            with patch.object(
                loop, "run_in_executor", new=AsyncMock(return_value=None)
            ):
                await flow._test_connection(user_input)

            # The host should have the protocol stripped
            assert user_input[CONF_HOST] == "my-cluster.example.com"
    finally:
        cf_module.KUBERNETES_AVAILABLE = original_available
        cf_module.client = original_client


async def test_test_connection_strips_http_prefix(hass: HomeAssistant):
    """Test _test_connection strips http:// prefix from host."""
    import custom_components.kubernetes.config_flow as cf_module

    original_available = cf_module.KUBERNETES_AVAILABLE
    original_client = cf_module.client
    cf_module.KUBERNETES_AVAILABLE = True

    mock_k8s_client = MagicMock()
    mock_config = MagicMock()
    mock_k8s_client.Configuration.return_value = mock_config
    mock_k8s_client.ApiClient.return_value = MagicMock()
    mock_k8s_client.CoreV1Api.return_value = MagicMock()
    cf_module.client = mock_k8s_client

    try:
        with patch(
            "custom_components.kubernetes.config_flow._ensure_kubernetes_imported",
            return_value=True,
        ):
            flow = KubernetesConfigFlow()
            flow.hass = hass

            import asyncio

            loop = asyncio.get_running_loop()
            user_input = {
                CONF_HOST: "http://my-cluster.example.com",
                CONF_API_TOKEN: "test-token",
                CONF_VERIFY_SSL: False,
            }

            with patch.object(
                loop, "run_in_executor", new=AsyncMock(return_value=None)
            ):
                await flow._test_connection(user_input)

            assert user_input[CONF_HOST] == "my-cluster.example.com"
    finally:
        cf_module.KUBERNETES_AVAILABLE = original_available
        cf_module.client = original_client


async def test_test_connection_empty_host_after_strip(hass: HomeAssistant):
    """Test _test_connection raises when host is empty after stripping protocol."""
    import custom_components.kubernetes.config_flow as cf_module

    original_available = cf_module.KUBERNETES_AVAILABLE
    original_client = cf_module.client
    cf_module.KUBERNETES_AVAILABLE = True

    mock_k8s_client = MagicMock()
    mock_k8s_client.Configuration.return_value = MagicMock()
    cf_module.client = mock_k8s_client

    try:
        with patch(
            "custom_components.kubernetes.config_flow._ensure_kubernetes_imported",
            return_value=True,
        ):
            flow = KubernetesConfigFlow()
            flow.hass = hass

            with pytest.raises(ValueError, match="Host cannot be empty"):
                await flow._test_connection(
                    {
                        CONF_HOST: "https://",
                        CONF_API_TOKEN: "test-token",
                    }
                )
    finally:
        cf_module.KUBERNETES_AVAILABLE = original_available
        cf_module.client = original_client


async def test_test_connection_client_is_none(hass: HomeAssistant):
    """Test _test_connection raises when client module is None."""
    import custom_components.kubernetes.config_flow as cf_module

    original_available = cf_module.KUBERNETES_AVAILABLE
    original_client = cf_module.client
    cf_module.KUBERNETES_AVAILABLE = True
    cf_module.client = None

    try:
        with patch(
            "custom_components.kubernetes.config_flow._ensure_kubernetes_imported",
            return_value=True,
        ):
            flow = KubernetesConfigFlow()
            flow.hass = hass

            with pytest.raises(ValueError, match="Kubernetes client not available"):
                await flow._test_connection(
                    {
                        CONF_HOST: "test-host",
                        CONF_API_TOKEN: "test-token",
                    }
                )
    finally:
        cf_module.KUBERNETES_AVAILABLE = original_available
        cf_module.client = original_client


async def test_test_connection_api_exception_with_body(hass: HomeAssistant):
    """Test _test_connection logs response body when ApiException has body."""
    import custom_components.kubernetes.config_flow as cf_module

    original_available = cf_module.KUBERNETES_AVAILABLE
    original_client = cf_module.client
    original_api_exc = cf_module.ApiException
    cf_module.KUBERNETES_AVAILABLE = True

    mock_k8s_client = MagicMock()
    mock_k8s_client.Configuration.return_value = MagicMock()
    mock_k8s_client.ApiClient.return_value = MagicMock()
    mock_k8s_client.CoreV1Api.return_value = MagicMock()
    cf_module.client = mock_k8s_client

    class FakeApiException(Exception):
        def __init__(self):
            self.status = 403
            self.reason = "Forbidden"
            self.body = '{"message": "forbidden: User cannot list resources"}'

    cf_module.ApiException = FakeApiException

    try:
        with patch(
            "custom_components.kubernetes.config_flow._ensure_kubernetes_imported",
            return_value=True,
        ):
            flow = KubernetesConfigFlow()
            flow.hass = hass
            flow._test_connection_aiohttp = AsyncMock(return_value=False)

            import asyncio

            loop = asyncio.get_running_loop()

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
                            CONF_VERIFY_SSL: False,
                        }
                    )
    finally:
        cf_module.KUBERNETES_AVAILABLE = original_available
        cf_module.client = original_client
        cf_module.ApiException = original_api_exc


async def test_test_connection_api_exception_404_aiohttp_fallback(
    hass: HomeAssistant,
):
    """Test _test_connection with 404 ApiException falls back to aiohttp."""
    import custom_components.kubernetes.config_flow as cf_module

    original_available = cf_module.KUBERNETES_AVAILABLE
    original_client = cf_module.client
    original_api_exc = cf_module.ApiException
    cf_module.KUBERNETES_AVAILABLE = True

    mock_k8s_client = MagicMock()
    mock_k8s_client.Configuration.return_value = MagicMock()
    mock_k8s_client.ApiClient.return_value = MagicMock()
    mock_k8s_client.CoreV1Api.return_value = MagicMock()
    cf_module.client = mock_k8s_client

    class FakeApiException(Exception):
        def __init__(self):
            self.status = 404
            self.reason = "Not Found"
            self.body = None

    cf_module.ApiException = FakeApiException

    try:
        with patch(
            "custom_components.kubernetes.config_flow._ensure_kubernetes_imported",
            return_value=True,
        ):
            flow = KubernetesConfigFlow()
            flow.hass = hass
            flow._test_connection_aiohttp = AsyncMock(return_value=True)

            import asyncio

            loop = asyncio.get_running_loop()

            with patch.object(
                loop,
                "run_in_executor",
                new=AsyncMock(side_effect=FakeApiException()),
            ):
                # Should succeed because aiohttp fallback returns True
                await flow._test_connection(
                    {
                        CONF_HOST: "test-host",
                        CONF_API_TOKEN: "test-token",
                        CONF_VERIFY_SSL: False,
                    }
                )

            flow._test_connection_aiohttp.assert_called_once()
    finally:
        cf_module.KUBERNETES_AVAILABLE = original_available
        cf_module.client = original_client
        cf_module.ApiException = original_api_exc


async def test_test_connection_api_exception_500_aiohttp_fails(
    hass: HomeAssistant,
):
    """Test _test_connection with 500 ApiException and aiohttp also failing."""
    import custom_components.kubernetes.config_flow as cf_module

    original_available = cf_module.KUBERNETES_AVAILABLE
    original_client = cf_module.client
    original_api_exc = cf_module.ApiException
    cf_module.KUBERNETES_AVAILABLE = True

    mock_k8s_client = MagicMock()
    mock_k8s_client.Configuration.return_value = MagicMock()
    mock_k8s_client.ApiClient.return_value = MagicMock()
    mock_k8s_client.CoreV1Api.return_value = MagicMock()
    cf_module.client = mock_k8s_client

    class FakeApiException(Exception):
        def __init__(self):
            self.status = 500
            self.reason = "Internal Server Error"
            self.body = None

    cf_module.ApiException = FakeApiException

    try:
        with patch(
            "custom_components.kubernetes.config_flow._ensure_kubernetes_imported",
            return_value=True,
        ):
            flow = KubernetesConfigFlow()
            flow.hass = hass
            flow._test_connection_aiohttp = AsyncMock(return_value=False)

            import asyncio

            loop = asyncio.get_running_loop()

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
                            CONF_VERIFY_SSL: False,
                        }
                    )
    finally:
        cf_module.KUBERNETES_AVAILABLE = original_available
        cf_module.client = original_client
        cf_module.ApiException = original_api_exc


async def test_test_connection_host_with_whitespace(hass: HomeAssistant):
    """Test _test_connection strips whitespace from host."""
    import custom_components.kubernetes.config_flow as cf_module

    original_available = cf_module.KUBERNETES_AVAILABLE
    original_client = cf_module.client
    cf_module.KUBERNETES_AVAILABLE = True

    mock_k8s_client = MagicMock()
    mock_config = MagicMock()
    mock_k8s_client.Configuration.return_value = mock_config
    mock_k8s_client.ApiClient.return_value = MagicMock()
    mock_k8s_client.CoreV1Api.return_value = MagicMock()
    cf_module.client = mock_k8s_client

    try:
        with patch(
            "custom_components.kubernetes.config_flow._ensure_kubernetes_imported",
            return_value=True,
        ):
            flow = KubernetesConfigFlow()
            flow.hass = hass

            import asyncio

            loop = asyncio.get_running_loop()
            user_input = {
                CONF_HOST: "  my-cluster.example.com  ",
                CONF_API_TOKEN: "test-token",
                CONF_VERIFY_SSL: False,
            }

            with patch.object(
                loop, "run_in_executor", new=AsyncMock(return_value=None)
            ):
                await flow._test_connection(user_input)

            assert user_input[CONF_HOST] == "my-cluster.example.com"
    finally:
        cf_module.KUBERNETES_AVAILABLE = original_available
        cf_module.client = original_client


# ---------------------------------------------------------------------------
# Additional coverage: _fetch_namespaces edge cases
# ---------------------------------------------------------------------------


async def test_fetch_namespaces_empty_items(hass: HomeAssistant):
    """Test _fetch_namespaces returns empty list when items array is empty."""
    flow = KubernetesConfigFlow()
    flow.hass = hass

    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={"items": []})
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


async def test_fetch_namespaces_malformed_json_missing_metadata(
    hass: HomeAssistant,
):
    """Test _fetch_namespaces handles malformed JSON with missing metadata key."""
    flow = KubernetesConfigFlow()
    flow.hass = hass

    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(
        return_value={
            "items": [
                {"not_metadata": {"name": "default"}},
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
        # This should raise a KeyError which is caught by the generic except
        result = await flow._fetch_namespaces(
            {
                CONF_HOST: "test-host",
                CONF_API_TOKEN: "test-token",
            }
        )

    # KeyError from item["metadata"]["name"] is caught by the generic except
    assert result == []


async def test_fetch_namespaces_no_items_key(hass: HomeAssistant):
    """Test _fetch_namespaces handles response with no items key."""
    flow = KubernetesConfigFlow()
    flow.hass = hass

    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={"kind": "NamespaceList"})
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

    # data.get("items", []) returns [] when key missing
    assert result == []


async def test_fetch_namespaces_timeout(hass: HomeAssistant):
    """Test _fetch_namespaces returns empty list on asyncio.TimeoutError."""
    flow = KubernetesConfigFlow()
    flow.hass = hass

    mock_session = MagicMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mock_session.get = MagicMock(side_effect=TimeoutError())

    with patch("aiohttp.ClientSession", return_value=mock_session):
        result = await flow._fetch_namespaces(
            {
                CONF_HOST: "test-host",
                CONF_API_TOKEN: "test-token",
            }
        )

    assert result == []


async def test_fetch_namespaces_non_200_with_empty_body(hass: HomeAssistant):
    """Test _fetch_namespaces handles non-200 with empty error text."""
    flow = KubernetesConfigFlow()
    flow.hass = hass

    mock_response = MagicMock()
    mock_response.status = 500
    mock_response.text = AsyncMock(return_value="")
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


async def test_fetch_namespaces_uses_default_port(hass: HomeAssistant):
    """Test _fetch_namespaces uses DEFAULT_PORT when port not provided."""
    flow = KubernetesConfigFlow()
    flow.hass = hass

    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(
        return_value={"items": [{"metadata": {"name": "default"}}]}
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
                # No CONF_PORT provided
            }
        )

    assert result == ["default"]
    # Verify the URL used the default port
    call_args = mock_session.get.call_args
    assert f":{DEFAULT_PORT}" in call_args[0][0]


async def test_fetch_namespaces_client_timeout_error(hass: HomeAssistant):
    """Test _fetch_namespaces returns empty list on aiohttp.ServerTimeoutError."""
    import aiohttp as aiohttp_mod

    flow = KubernetesConfigFlow()
    flow.hass = hass

    mock_session = MagicMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mock_session.get = MagicMock(
        side_effect=aiohttp_mod.ServerTimeoutError("Request timed out")
    )

    with patch("aiohttp.ClientSession", return_value=mock_session):
        result = await flow._fetch_namespaces(
            {
                CONF_HOST: "test-host",
                CONF_API_TOKEN: "test-token",
            }
        )

    assert result == []


# ---------------------------------------------------------------------------
# Additional coverage: _test_connection_aiohttp edge cases
# ---------------------------------------------------------------------------


async def test_test_connection_aiohttp_uses_default_port(hass: HomeAssistant):
    """Test _test_connection_aiohttp uses DEFAULT_PORT when port not provided."""
    flow = KubernetesConfigFlow()
    flow.hass = hass

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
                # No CONF_PORT
            }
        )

    assert result is True
    call_args = mock_session.get.call_args
    assert f":{DEFAULT_PORT}" in call_args[0][0]


async def test_test_connection_aiohttp_client_error(hass: HomeAssistant):
    """Test _test_connection_aiohttp returns False on aiohttp.ClientError."""
    import aiohttp as aiohttp_mod

    flow = KubernetesConfigFlow()
    flow.hass = hass

    mock_session = MagicMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mock_session.get = MagicMock(
        side_effect=aiohttp_mod.ClientConnectionError("Connection refused")
    )

    with patch("aiohttp.ClientSession", return_value=mock_session):
        result = await flow._test_connection_aiohttp(
            {
                CONF_HOST: "test-host",
                CONF_API_TOKEN: "test-token",
            }
        )

    assert result is False


# ---------------------------------------------------------------------------
# Additional coverage: async_step_namespaces edge cases
# ---------------------------------------------------------------------------


async def test_async_step_namespaces_missing_namespace_key(hass: HomeAssistant):
    """Test namespace step returns error when CONF_NAMESPACE key is missing."""
    with (
        patch(
            "custom_components.kubernetes.config_flow._ensure_kubernetes_imported",
            return_value=True,
        ),
        patch("custom_components.kubernetes.config_flow.KUBERNETES_AVAILABLE", True),
        patch.object(KubernetesConfigFlow, "_test_connection", new_callable=AsyncMock),
        patch.object(
            KubernetesConfigFlow,
            "_fetch_namespaces",
            new_callable=AsyncMock,
            return_value=["default", "kube-system"],
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_CLUSTER_NAME: "test-cluster",
                CONF_HOST: "test-host",
                CONF_API_TOKEN: "test-token",
                CONF_MONITOR_ALL_NAMESPACES: False,
            },
        )
        assert result["step_id"] == "namespaces"

        # Submit with empty namespace list to trigger validation error
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_NAMESPACE: []},
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "namespaces"
    assert CONF_NAMESPACE in result["errors"]


async def test_async_step_namespaces_filters_empty_strings(hass: HomeAssistant):
    """Test namespace step filters out empty strings from namespace list.

    Direct method call to bypass schema validation.
    """
    flow = KubernetesConfigFlow()
    flow.hass = hass
    flow.context = {"source": config_entries.SOURCE_USER}
    flow._connection_data = {
        CONF_CLUSTER_NAME: "test-cluster",
        CONF_HOST: "test-host",
        CONF_PORT: 6443,
        CONF_API_TOKEN: "test-token",
    }

    result = await flow.async_step_namespaces(
        {CONF_NAMESPACE: ["default", "", "production", ""]}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_NAMESPACE] == ["default", "production"]


# ---------------------------------------------------------------------------
# Additional coverage: async_step_reconfigure edge cases
# ---------------------------------------------------------------------------


class TestReconfigureAdditionalCoverage:
    """Additional reconfigure flow tests for untested paths."""

    @pytest.fixture
    def mock_config_entry(self, hass: HomeAssistant) -> MockConfigEntry:
        """Return a config entry with CA cert for reconfigure tests."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_CLUSTER_NAME: "test-cluster",
                CONF_HOST: "host.example.com",
                CONF_PORT: 6443,
                CONF_API_TOKEN: "test-token",
                CONF_CA_CERT: "/path/to/ca.crt",
                CONF_VERIFY_SSL: True,
                CONF_MONITOR_ALL_NAMESPACES: True,
                CONF_DEVICE_GROUPING_MODE: DEFAULT_DEVICE_GROUPING_MODE,
                CONF_SWITCH_UPDATE_INTERVAL: DEFAULT_SWITCH_UPDATE_INTERVAL,
                CONF_SCALE_VERIFICATION_TIMEOUT: DEFAULT_SCALE_VERIFICATION_TIMEOUT,
                CONF_SCALE_COOLDOWN: DEFAULT_SCALE_COOLDOWN,
            },
            unique_id="test-cluster",
        )
        entry.add_to_hass(hass)
        return entry

    async def _init_reconfigure(self, hass, entry):
        """Helper to start a reconfigure flow."""
        return await hass.config_entries.flow.async_init(
            DOMAIN,
            context={
                "source": config_entries.SOURCE_RECONFIGURE,
                "entry_id": entry.entry_id,
            },
        )

    async def test_reconfigure_keeps_ca_cert_when_provided(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ):
        """Test that CA cert is preserved when user provides a new one."""
        with (
            patch(
                "custom_components.kubernetes.config_flow._ensure_kubernetes_imported",
                return_value=True,
            ),
            patch(
                "custom_components.kubernetes.config_flow.KUBERNETES_AVAILABLE",
                True,
            ),
            patch.object(
                KubernetesConfigFlow, "_test_connection", new_callable=AsyncMock
            ),
        ):
            result = await self._init_reconfigure(hass, mock_config_entry)

            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                user_input={
                    CONF_HOST: "host.example.com",
                    CONF_PORT: 6443,
                    CONF_API_TOKEN: "test-token",
                    CONF_CA_CERT: "/new/ca.crt",
                    CONF_VERIFY_SSL: True,
                    CONF_MONITOR_ALL_NAMESPACES: True,
                },
            )

        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == "reconfigure_successful"
        assert mock_config_entry.data[CONF_CA_CERT] == "/new/ca.crt"

    async def test_reconfigure_applies_default_values(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ):
        """Test that reconfigure applies defaults for optional fields not submitted."""
        with (
            patch(
                "custom_components.kubernetes.config_flow._ensure_kubernetes_imported",
                return_value=True,
            ),
            patch(
                "custom_components.kubernetes.config_flow.KUBERNETES_AVAILABLE",
                True,
            ),
            patch.object(
                KubernetesConfigFlow, "_test_connection", new_callable=AsyncMock
            ),
        ):
            result = await self._init_reconfigure(hass, mock_config_entry)

            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                user_input={
                    CONF_HOST: "host.example.com",
                    CONF_API_TOKEN: "test-token",
                    CONF_MONITOR_ALL_NAMESPACES: True,
                },
            )

        assert result["type"] is FlowResultType.ABORT
        assert mock_config_entry.data[CONF_PORT] == DEFAULT_PORT
        assert mock_config_entry.data[CONF_VERIFY_SSL] == DEFAULT_VERIFY_SSL
        assert (
            mock_config_entry.data[CONF_SWITCH_UPDATE_INTERVAL]
            == DEFAULT_SWITCH_UPDATE_INTERVAL
        )
        assert (
            mock_config_entry.data[CONF_SCALE_VERIFICATION_TIMEOUT]
            == DEFAULT_SCALE_VERIFICATION_TIMEOUT
        )
        assert mock_config_entry.data[CONF_SCALE_COOLDOWN] == DEFAULT_SCALE_COOLDOWN
        assert (
            mock_config_entry.data[CONF_DEVICE_GROUPING_MODE]
            == DEFAULT_DEVICE_GROUPING_MODE
        )


# ---------------------------------------------------------------------------
# Additional coverage: reconfigure_namespaces with string current_namespaces
# ---------------------------------------------------------------------------


class TestReconfigureNamespacesStringEntry:
    """Tests for reconfigure_namespaces when current namespaces is a string."""

    @pytest.fixture
    def entry_with_string_namespace(self, hass: HomeAssistant) -> MockConfigEntry:
        """Return entry where CONF_NAMESPACE is a string (legacy format)."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_CLUSTER_NAME: "test-cluster",
                CONF_HOST: "host.example.com",
                CONF_PORT: 6443,
                CONF_API_TOKEN: "test-token",
                CONF_VERIFY_SSL: False,
                CONF_MONITOR_ALL_NAMESPACES: False,
                CONF_NAMESPACE: "production",
                CONF_DEVICE_GROUPING_MODE: DEFAULT_DEVICE_GROUPING_MODE,
                CONF_SWITCH_UPDATE_INTERVAL: DEFAULT_SWITCH_UPDATE_INTERVAL,
                CONF_SCALE_VERIFICATION_TIMEOUT: DEFAULT_SCALE_VERIFICATION_TIMEOUT,
                CONF_SCALE_COOLDOWN: DEFAULT_SCALE_COOLDOWN,
            },
            unique_id="test-cluster",
        )
        entry.add_to_hass(hass)
        return entry

    async def test_reconfigure_namespaces_string_current_namespace(
        self, hass: HomeAssistant, entry_with_string_namespace: MockConfigEntry
    ):
        """Test reconfigure_namespaces converts string current_namespaces to list."""
        with (
            patch(
                "custom_components.kubernetes.config_flow._ensure_kubernetes_imported",
                return_value=True,
            ),
            patch(
                "custom_components.kubernetes.config_flow.KUBERNETES_AVAILABLE",
                True,
            ),
            patch.object(
                KubernetesConfigFlow, "_test_connection", new_callable=AsyncMock
            ),
            patch.object(
                KubernetesConfigFlow,
                "_fetch_namespaces",
                new_callable=AsyncMock,
                return_value=["default", "production", "staging"],
            ),
        ):
            result = await hass.config_entries.flow.async_init(
                DOMAIN,
                context={
                    "source": config_entries.SOURCE_RECONFIGURE,
                    "entry_id": entry_with_string_namespace.entry_id,
                },
            )
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                user_input={
                    CONF_HOST: "host.example.com",
                    CONF_PORT: 6443,
                    CONF_API_TOKEN: "test-token",
                    CONF_MONITOR_ALL_NAMESPACES: False,
                },
            )

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "reconfigure_namespaces"

        # Verify "production" is pre-selected (converted from string)
        for key in result["data_schema"].schema:
            if str(key) == CONF_NAMESPACE or (
                hasattr(key, "schema") and key.schema == CONF_NAMESPACE
            ):
                assert "production" in key.default()
                break
        else:
            pytest.fail(f"{CONF_NAMESPACE} not found in schema")

    async def test_reconfigure_namespaces_empty_selection_shows_error(
        self, hass: HomeAssistant, entry_with_string_namespace: MockConfigEntry
    ):
        """Test reconfigure_namespaces returns error when no namespace key in input."""
        flow = KubernetesConfigFlow()
        flow.hass = hass
        flow._connection_data = {
            CONF_CLUSTER_NAME: "test-cluster",
            CONF_HOST: "host.example.com",
            CONF_PORT: 6443,
            CONF_API_TOKEN: "test-token",
        }
        flow.handler = DOMAIN
        flow.context = {
            "source": config_entries.SOURCE_RECONFIGURE,
            "entry_id": entry_with_string_namespace.entry_id,
        }

        # Submit with empty dict (missing CONF_NAMESPACE)
        with patch.object(
            KubernetesConfigFlow,
            "_fetch_namespaces",
            new_callable=AsyncMock,
            return_value=["default"],
        ):
            result = await flow.async_step_reconfigure_namespaces({})

        assert result["type"] is FlowResultType.FORM
        assert CONF_NAMESPACE in result["errors"]


# ---------------------------------------------------------------------------
# Additional coverage: _ensure_kubernetes_imported double-checked locking
# ---------------------------------------------------------------------------


def test_ensure_kubernetes_imported_cached_true():
    """Test _ensure_kubernetes_imported returns cached True without re-importing."""
    import custom_components.kubernetes.config_flow as cf_module

    original = cf_module.KUBERNETES_AVAILABLE
    cf_module.KUBERNETES_AVAILABLE = True

    try:
        # Should return immediately without attempting import
        result = cf_module._ensure_kubernetes_imported()
        assert result is True
    finally:
        cf_module.KUBERNETES_AVAILABLE = original


def test_ensure_kubernetes_imported_cached_false():
    """Test _ensure_kubernetes_imported returns cached False without re-importing."""
    import custom_components.kubernetes.config_flow as cf_module

    original = cf_module.KUBERNETES_AVAILABLE
    cf_module.KUBERNETES_AVAILABLE = False

    try:
        result = cf_module._ensure_kubernetes_imported()
        assert result is False
    finally:
        cf_module.KUBERNETES_AVAILABLE = original


# ---------------------------------------------------------------------------
# Additional coverage: user step with namespace removal
# ---------------------------------------------------------------------------


async def test_async_step_user_monitor_all_creates_entry_without_namespace(
    hass: HomeAssistant,
):
    """Test that user step creates entry without CONF_NAMESPACE when monitoring all."""
    with (
        patch(
            "custom_components.kubernetes.config_flow._ensure_kubernetes_imported",
            return_value=True,
        ),
        patch("custom_components.kubernetes.config_flow.KUBERNETES_AVAILABLE", True),
        patch.object(KubernetesConfigFlow, "_test_connection", new_callable=AsyncMock),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_CLUSTER_NAME: "test-cluster",
                CONF_HOST: "test-host.example.com",
                CONF_API_TOKEN: "test-token",
                CONF_MONITOR_ALL_NAMESPACES: True,
            },
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert CONF_NAMESPACE not in result["data"]


async def test_async_step_user_sets_all_defaults(hass: HomeAssistant):
    """Test that user step sets all default values for optional fields."""
    with (
        patch(
            "custom_components.kubernetes.config_flow._ensure_kubernetes_imported",
            return_value=True,
        ),
        patch("custom_components.kubernetes.config_flow.KUBERNETES_AVAILABLE", True),
        patch.object(KubernetesConfigFlow, "_test_connection", new_callable=AsyncMock),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_CLUSTER_NAME: "test-cluster",
                CONF_HOST: "test-host.example.com",
                CONF_API_TOKEN: "test-token",
                CONF_MONITOR_ALL_NAMESPACES: True,
            },
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    data = result["data"]
    assert data[CONF_PORT] == DEFAULT_PORT
    assert data[CONF_VERIFY_SSL] == DEFAULT_VERIFY_SSL
    assert data[CONF_SWITCH_UPDATE_INTERVAL] == DEFAULT_SWITCH_UPDATE_INTERVAL
    assert data[CONF_SCALE_VERIFICATION_TIMEOUT] == DEFAULT_SCALE_VERIFICATION_TIMEOUT
    assert data[CONF_SCALE_COOLDOWN] == DEFAULT_SCALE_COOLDOWN
    assert data[CONF_DEVICE_GROUPING_MODE] == DEFAULT_DEVICE_GROUPING_MODE


# ---------------------------------------------------------------------------
# Additional coverage: _test_connection_aiohttp specific status codes
# ---------------------------------------------------------------------------


async def test_test_connection_aiohttp_forbidden(hass: HomeAssistant):
    """Test _test_connection_aiohttp returns False on 403 Forbidden."""
    flow = KubernetesConfigFlow()
    flow.hass = hass

    mock_response = MagicMock()
    mock_response.status = 403
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
                CONF_PORT: 6443,
                CONF_API_TOKEN: "test-token",
            }
        )

    assert result is False


async def test_test_connection_aiohttp_500(hass: HomeAssistant):
    """Test _test_connection_aiohttp returns False on 500 Internal Server Error."""
    flow = KubernetesConfigFlow()
    flow.hass = hass

    mock_response = MagicMock()
    mock_response.status = 500
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
                CONF_PORT: 6443,
                CONF_API_TOKEN: "test-token",
            }
        )

    assert result is False


async def test_test_connection_aiohttp_timeout(hass: HomeAssistant):
    """Test _test_connection_aiohttp returns False on timeout."""
    flow = KubernetesConfigFlow()
    flow.hass = hass

    mock_session = MagicMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mock_session.get = MagicMock(side_effect=TimeoutError())

    with patch("aiohttp.ClientSession", return_value=mock_session):
        result = await flow._test_connection_aiohttp(
            {
                CONF_HOST: "test-host",
                CONF_API_TOKEN: "test-token",
            }
        )

    assert result is False


# ---------------------------------------------------------------------------
# Additional coverage: fetch namespaces non-200 status codes
# ---------------------------------------------------------------------------


async def test_fetch_namespaces_401_unauthorized(hass: HomeAssistant):
    """Test _fetch_namespaces returns empty list on 401 Unauthorized."""
    flow = KubernetesConfigFlow()
    flow.hass = hass

    mock_response = MagicMock()
    mock_response.status = 401
    mock_response.text = AsyncMock(return_value="Unauthorized")
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
                CONF_API_TOKEN: "bad-token",
            }
        )

    assert result == []


async def test_fetch_namespaces_long_error_text_truncated(hass: HomeAssistant):
    """Test _fetch_namespaces truncates long error text in log message."""
    flow = KubernetesConfigFlow()
    flow.hass = hass

    long_error = "x" * 500
    mock_response = MagicMock()
    mock_response.status = 500
    mock_response.text = AsyncMock(return_value=long_error)
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)

    mock_session = MagicMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mock_session.get = MagicMock(return_value=mock_response)

    with patch("aiohttp.ClientSession", return_value=mock_session):
        # Should not raise, just return empty list
        result = await flow._fetch_namespaces(
            {
                CONF_HOST: "test-host",
                CONF_API_TOKEN: "test-token",
            }
        )

    assert result == []
