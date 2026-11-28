"""Tests for the Kubernetes integration config flow."""

from contextlib import contextmanager
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import AbortFlow, FlowResultType, InvalidData
from homeassistant.helpers import selector
import pytest
from pytest_homeassistant.common import MockConfigEntry
import voluptuous as vol

from custom_components.kubernetes.config_flow import (
    KubernetesConfigFlow,
    KubernetesOptionsFlow,
    TokenRequired,
)
from custom_components.kubernetes.const import (
    CONF_API_TOKEN,
    CONF_CA_CERT,
    CONF_CLUSTER_NAME,
    CONF_DEVICE_GROUPING_MODE,
    CONF_DISABLED_RESOURCES,
    CONF_ENABLE_EVENTS,
    CONF_ENABLE_PANEL,
    CONF_ENABLE_POD_LOGS,
    CONF_ENABLE_WATCH,
    CONF_EVENT_TYPES,
    CONF_EXCLUDE_JOB_PODS,
    CONF_MONITOR_ALL_NAMESPACES,
    CONF_NAMESPACE,
    CONF_PANEL_ADMIN_ONLY,
    CONF_SCALE_COOLDOWN,
    CONF_SWITCH_UPDATE_INTERVAL,
    CONF_USE_IN_CLUSTER,
    CONF_VERIFY_SSL,
    DEFAULT_DEVICE_GROUPING_MODE,
    DEFAULT_ENABLE_EVENTS,
    DEFAULT_ENABLE_PANEL,
    DEFAULT_ENABLE_WATCH,
    DEFAULT_EVENT_TYPES,
    DEFAULT_EXCLUDE_JOB_PODS,
    DEFAULT_PORT,
    DEFAULT_SCALE_COOLDOWN,
    DEFAULT_SWITCH_UPDATE_INTERVAL,
    DEFAULT_VERIFY_SSL,
    DOMAIN,
    EVENT_TYPES_ALL,
    EVENT_TYPES_WARNING,
)

# The flow's aiohttp calls go through Home Assistant's shared session.
_SESSION = "custom_components.kubernetes.config_flow.async_get_clientsession"


@contextmanager
def patched_connection(result=None, side_effect=None):
    """Patch KubernetesConfigFlow._test_connection for the duration of a test."""
    with patch.object(
        KubernetesConfigFlow,
        "_test_connection",
        new_callable=AsyncMock,
        return_value=result,
        side_effect=side_effect,
    ) as mock:
        yield mock


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


# ---------------------------------------------------------------------------
# User step tests (real flow manager)
# ---------------------------------------------------------------------------


async def test_async_step_user_initial_step(hass: HomeAssistant):
    """Test initial user step."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"


async def test_async_step_user_with_valid_input(hass: HomeAssistant):
    """Test user step with valid input."""
    with patched_connection():
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
    with patched_connection(side_effect=Exception("Connection failed")):
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


async def test_async_step_user_token_required(hass: HomeAssistant):
    """A missing token surfaces as token_required, not cannot_connect."""
    with patched_connection(side_effect=TokenRequired("API token is required")):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_CLUSTER_NAME: "test-cluster",
                CONF_HOST: "kubernetes.example.com",
            },
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"]["base"] == "token_required"


async def test_async_step_user_in_cluster_without_token_stores_sa_token(
    hass: HomeAssistant,
):
    """Submitting no token in in-cluster mode stores the mounted SA token."""
    with (
        patch(
            "custom_components.kubernetes.config_flow.async_detect_in_cluster_config",
            return_value={"host": "10.0.0.1", "port": 443, "api_token": "sa-token"},
        ),
        # The real _test_connection runs; only the network probe is stubbed.
        patch.object(
            KubernetesConfigFlow,
            "_test_connection_aiohttp",
            new_callable=AsyncMock,
            return_value=True,
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_CLUSTER_NAME: "test-cluster",
                CONF_HOST: "10.0.0.1",
                CONF_USE_IN_CLUSTER: True,
                CONF_MONITOR_ALL_NAMESPACES: True,
            },
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_API_TOKEN] == "sa-token"


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
        patched_connection(),
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


async def test_duplicate_cluster_name_aborts_before_namespace_step(
    hass: HomeAssistant,
):
    """Test a duplicate cluster name aborts in the user step.

    With selected namespaces the check used to run only after the namespace
    form was submitted.
    """
    existing = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_CLUSTER_NAME: "test-cluster", CONF_HOST: "old-host"},
        unique_id="test-cluster",
    )
    existing.add_to_hass(hass)

    mock_integration = MagicMock()
    mock_integration.single_config_entry = False

    with (
        patched_connection(),
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
                CONF_MONITOR_ALL_NAMESPACES: False,
            },
        )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_async_step_user_with_defaults(hass: HomeAssistant):
    """Test user step with default values."""
    with patched_connection():
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
        patched_connection(),
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
        patched_connection(),
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
        patched_connection(),
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


async def test_async_step_namespaces_no_namespaces_fetched(hass: HomeAssistant):
    """Test namespace step shows error when no namespaces fetched."""
    with (
        patched_connection(),
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


# ---------------------------------------------------------------------------
# Internal method tests (_test_connection, _test_connection_aiohttp,
# _fetch_namespaces)
# These test private methods directly and keep direct flow instantiation.
# ---------------------------------------------------------------------------


def _patch_probe(result: bool = True):
    """Stub the aiohttp probe so _test_connection runs without network access."""
    return patch.object(
        KubernetesConfigFlow,
        "_test_connection_aiohttp",
        new_callable=AsyncMock,
        return_value=result,
    )


async def test_test_connection_success(hass: HomeAssistant):
    """A successful probe lets _test_connection return without raising."""
    flow = KubernetesConfigFlow()
    flow.hass = hass
    user_input = {
        CONF_HOST: "test-host",
        CONF_PORT: 6443,
        CONF_API_TOKEN: "test-token",
        CONF_VERIFY_SSL: False,
    }

    with _patch_probe(True) as probe:
        await flow._test_connection(user_input)

    probe.assert_awaited_once_with(user_input)


async def test_test_connection_brackets_ipv6_host(hass: HomeAssistant):
    """A bare IPv6 host is bracketed before the probe builds its URL (issue #264)."""
    flow = KubernetesConfigFlow()
    flow.hass = hass

    user_input = {
        CONF_HOST: "aaaa:bbbb:cccc::1",
        CONF_PORT: 443,
        CONF_API_TOKEN: "test-token",
        CONF_VERIFY_SSL: False,
    }

    with _patch_probe(True) as probe:
        await flow._test_connection(user_input)

    # The persisted host is bracketed, and the probe saw the bracketed value.
    assert user_input[CONF_HOST] == "[aaaa:bbbb:cccc::1]"
    assert probe.await_args.args[0][CONF_HOST] == "[aaaa:bbbb:cccc::1]"


async def test_test_connection_failure(hass: HomeAssistant):
    """A failed probe raises ValueError, which the steps map to cannot_connect."""
    flow = KubernetesConfigFlow()
    flow.hass = hass

    with (
        _patch_probe(False),
        pytest.raises(ValueError, match="Failed to connect to Kubernetes API"),
    ):
        await flow._test_connection(
            {
                CONF_HOST: "test-host",
                CONF_PORT: 6443,
                CONF_API_TOKEN: "test-token",
                CONF_VERIFY_SSL: False,
            }
        )


def test_config_flow_constants():
    """Test config flow constants."""
    assert KubernetesConfigFlow.VERSION == 1


async def test_test_connection_empty_host(hass: HomeAssistant):
    """Test _test_connection raises when host is empty."""
    flow = KubernetesConfigFlow()
    flow.hass = hass

    with _patch_probe() as probe, pytest.raises(ValueError, match="Host is required"):
        await flow._test_connection(
            {
                CONF_HOST: "",
                CONF_API_TOKEN: "test-token",
            }
        )

    probe.assert_not_awaited()


async def test_test_connection_empty_token(hass: HomeAssistant):
    """Test _test_connection raises TokenRequired when API token is empty."""
    flow = KubernetesConfigFlow()
    flow.hass = hass

    with (
        _patch_probe() as probe,
        pytest.raises(TokenRequired, match="API token is required"),
    ):
        await flow._test_connection(
            {
                CONF_HOST: "test-host",
                CONF_API_TOKEN: "",
            }
        )

    probe.assert_not_awaited()


async def test_test_connection_empty_token_uses_in_cluster_token(hass: HomeAssistant):
    """With in-cluster mode on, an empty token is filled from the ServiceAccount."""
    flow = KubernetesConfigFlow()
    flow.hass = hass
    user_input = {
        CONF_HOST: "test-host",
        CONF_USE_IN_CLUSTER: True,
        CONF_VERIFY_SSL: False,
    }

    with (
        patch(
            "custom_components.kubernetes.config_flow.async_detect_in_cluster_config",
            return_value={"host": "10.0.0.1", "port": 443, "api_token": "sa-token"},
        ),
        _patch_probe(True) as probe,
    ):
        await flow._test_connection(user_input)

    assert user_input[CONF_API_TOKEN] == "sa-token"
    # The probe validates with the same token that gets stored.
    assert probe.await_args.args[0][CONF_API_TOKEN] == "sa-token"


async def test_test_connection_empty_token_in_cluster_not_detected(
    hass: HomeAssistant,
):
    """In-cluster mode without a mounted ServiceAccount still requires a token."""
    flow = KubernetesConfigFlow()
    flow.hass = hass

    with (
        patch(
            "custom_components.kubernetes.config_flow.async_detect_in_cluster_config",
            return_value=None,
        ),
        pytest.raises(ValueError, match="API token is required"),
    ):
        await flow._test_connection(
            {CONF_HOST: "test-host", CONF_USE_IN_CLUSTER: True, CONF_API_TOKEN: ""}
        )


async def test_test_connection_aiohttp_success(hass: HomeAssistant):
    """Test _test_connection_aiohttp returns True on 200 response."""
    flow = KubernetesConfigFlow()
    flow.hass = hass

    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)

    mock_session = MagicMock()
    mock_session.get = MagicMock(return_value=mock_response)

    with patch(_SESSION, return_value=mock_session):
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
    mock_session.get = MagicMock(return_value=mock_response)

    with patch(_SESSION, return_value=mock_session):
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
    mock_session.get = MagicMock(side_effect=Exception("Network error"))

    with patch(_SESSION, return_value=mock_session):
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
    mock_session.get = MagicMock(return_value=mock_response)

    with patch(_SESSION, return_value=mock_session):
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
    mock_session.get = MagicMock(return_value=mock_response)

    with patch(_SESSION, return_value=mock_session):
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
    mock_session.get = MagicMock(
        side_effect=aiohttp_mod.ClientConnectionError("Connection refused")
    )

    with patch(_SESSION, return_value=mock_session):
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
    mock_session.get = MagicMock(side_effect=Exception("Unexpected error"))

    with patch(_SESSION, return_value=mock_session):
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

    async def test_options_flow_includes_enable_watch(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ):
        """Options form should include the enable_watch field."""
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

    async def test_options_flow_reloads_entry_on_change(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ):
        """Changed options reload the entry (there is no update listener)."""
        result = await hass.config_entries.options.async_init(
            mock_config_entry.entry_id
        )
        with patch.object(hass.config_entries, "async_schedule_reload") as mock_reload:
            await hass.config_entries.options.async_configure(
                result["flow_id"],
                user_input={CONF_ENABLE_WATCH: False},
            )
        mock_reload.assert_called_once_with(mock_config_entry.entry_id)

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

    async def test_options_flow_offers_disabled_resources(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ):
        """The init form should contain the disabled_resources multi-select."""
        result = await hass.config_entries.options.async_init(
            mock_config_entry.entry_id
        )
        schema_keys = [str(k) for k in result["data_schema"].schema]
        assert any(CONF_DISABLED_RESOURCES in k for k in schema_keys)

    async def test_options_flow_saves_disabled_resources(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ):
        """Submitting a disabled_resources selection should be saved."""
        result = await hass.config_entries.options.async_init(
            mock_config_entry.entry_id
        )
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={CONF_DISABLED_RESOURCES: ["pods", "metrics"]},
        )
        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["data"][CONF_DISABLED_RESOURCES] == ["pods", "metrics"]

    async def test_options_flow_preserves_existing_disabled_resources(
        self, hass: HomeAssistant
    ):
        """The form should render with previously saved disabled resources."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_CLUSTER_NAME: "test-cluster",
                CONF_HOST: "host.example.com",
                CONF_API_TOKEN: "token",
            },
            options={CONF_DISABLED_RESOURCES: ["jobs"]},
        )
        entry.add_to_hass(hass)

        result = await hass.config_entries.options.async_init(entry.entry_id)
        assert result["type"] is FlowResultType.FORM

    def test_async_get_options_flow(self):
        """KubernetesConfigFlow.async_get_options_flow should return a KubernetesOptionsFlow."""
        config_entry = MagicMock()
        options_flow = KubernetesConfigFlow.async_get_options_flow(config_entry)
        assert isinstance(options_flow, KubernetesOptionsFlow)

    def test_default_enable_watch_is_true(self):
        """DEFAULT_ENABLE_WATCH constant should be True (watch is the default)."""
        assert DEFAULT_ENABLE_WATCH is True

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

    async def test_options_flow_saves_panel_admin_only(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ):
        """The panel_admin_only option defaults to off and can be turned on."""
        result = await hass.config_entries.options.async_init(
            mock_config_entry.entry_id
        )
        defaults = {
            str(k): k.default() for k in result["data_schema"].schema if k.default
        }
        assert defaults[CONF_PANEL_ADMIN_ONLY] is False

        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={CONF_PANEL_ADMIN_ONLY: True, CONF_ENABLE_WATCH: False},
        )
        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["data"][CONF_PANEL_ADMIN_ONLY] is True

    async def test_options_flow_includes_enable_events(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ):
        """Options form should include the enable_events and event_types fields."""
        result = await hass.config_entries.options.async_init(
            mock_config_entry.entry_id
        )
        assert result["type"] is FlowResultType.FORM
        schema_keys = [str(k) for k in result["data_schema"].schema]
        assert any(CONF_ENABLE_EVENTS in k for k in schema_keys)
        assert any(CONF_EVENT_TYPES in k for k in schema_keys)

    async def test_options_flow_pod_logs_defaults_off(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ):
        """enable_pod_logs is offered and is off unless the user opts in."""
        result = await hass.config_entries.options.async_init(
            mock_config_entry.entry_id
        )
        key = next(k for k in result["data_schema"].schema if k == CONF_ENABLE_POD_LOGS)
        assert key.default() is False

    def test_options_flow_defaults_events_disabled(self):
        """Default value for enable_events should be False."""
        assert DEFAULT_ENABLE_EVENTS is False

    def test_options_flow_defaults_event_types_warning(self):
        """Default value for event_types should be 'warning'."""
        assert DEFAULT_EVENT_TYPES == EVENT_TYPES_WARNING

    async def test_options_flow_event_types_selector_is_translated(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ):
        """event_types offers plain-string options labelled via translations."""
        result = await hass.config_entries.options.async_init(
            mock_config_entry.entry_id
        )
        schema = result["data_schema"].schema
        config = schema[next(k for k in schema if k == CONF_EVENT_TYPES)].config
        assert config["options"] == [EVENT_TYPES_WARNING, EVENT_TYPES_ALL]
        assert config["translation_key"] == CONF_EVENT_TYPES

    async def test_user_flow_grouping_selector_is_translated(self, hass: HomeAssistant):
        """The grouping selector offers plain-string options labelled via translations."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        schema = result["data_schema"].schema
        config = schema[
            next(k for k in schema if k == CONF_DEVICE_GROUPING_MODE)
        ].config
        assert config["options"] == ["namespace", "cluster"]
        assert config["translation_key"] == "device_grouping_mode"

    async def test_options_flow_saves_enable_events_true_and_event_types_all(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ):
        """Submitting enable_events=True and event_types='all' saves those values."""
        result = await hass.config_entries.options.async_init(
            mock_config_entry.entry_id
        )
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_ENABLE_PANEL: True,
                CONF_ENABLE_WATCH: False,
                CONF_ENABLE_EVENTS: True,
                CONF_EVENT_TYPES: EVENT_TYPES_ALL,
            },
        )
        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["data"][CONF_ENABLE_EVENTS] is True
        assert result["data"][CONF_EVENT_TYPES] == EVENT_TYPES_ALL

    async def test_options_flow_shows_exclude_job_pods_after_event_types(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ):
        """exclude_job_pods defaults on and sits after the two event fields."""
        result = await hass.config_entries.options.async_init(
            mock_config_entry.entry_id
        )
        assert result["type"] is FlowResultType.FORM
        keys = [str(k) for k in result["data_schema"].schema]
        assert keys.index(CONF_EXCLUDE_JOB_PODS) > keys.index(CONF_EVENT_TYPES)
        defaults = {str(k): k.default() for k in result["data_schema"].schema}
        assert defaults[CONF_EXCLUDE_JOB_PODS] is DEFAULT_EXCLUDE_JOB_PODS is True

    async def test_options_flow_exclude_job_pods_round_trip(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ):
        """Submitting exclude_job_pods=False persists it and pre-fills the form."""
        result = await hass.config_entries.options.async_init(
            mock_config_entry.entry_id
        )
        result = await hass.config_entries.options.async_configure(
            result["flow_id"], user_input={CONF_EXCLUDE_JOB_PODS: False}
        )
        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["data"][CONF_EXCLUDE_JOB_PODS] is False

        result = await hass.config_entries.options.async_init(
            mock_config_entry.entry_id
        )
        defaults = {str(k): k.default() for k in result["data_schema"].schema}
        assert defaults[CONF_EXCLUDE_JOB_PODS] is False


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
        result = await self._init_reconfigure(hass, mock_config_entry)

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "reconfigure"
        schema_keys = [str(k) for k in result["data_schema"].schema]
        assert not any(CONF_CLUSTER_NAME in k for k in schema_keys)
        assert any(CONF_HOST in k for k in schema_keys)

    async def test_reconfigure_successful_monitor_all_namespaces(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ):
        """Test successful reconfigure with monitor_all_namespaces=True."""
        with patched_connection():
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

    async def test_reconfigure_stores_cluster_grouping_unchanged(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ):
        """A submitted "cluster" grouping mode is stored as-is."""
        with patched_connection():
            result = await self._init_reconfigure(hass, mock_config_entry)
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                user_input={
                    CONF_HOST: "new-host.example.com",
                    CONF_PORT: 6443,
                    CONF_API_TOKEN: "new-token",
                    CONF_MONITOR_ALL_NAMESPACES: True,
                    CONF_DEVICE_GROUPING_MODE: "cluster",
                },
            )

        assert result["reason"] == "reconfigure_successful"
        assert mock_config_entry.data[CONF_DEVICE_GROUPING_MODE] == "cluster"

    async def test_reconfigure_proceeds_to_namespace_step(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ):
        """Test reconfigure proceeds to namespace step when monitor_all=False."""
        with (
            patched_connection(),
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
        with patched_connection(side_effect=Exception("Connection refused")):
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

    async def test_reconfigure_token_required(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ):
        """Reconfigure reports a missing token as token_required."""
        with patched_connection(side_effect=TokenRequired("API token is required")):
            result = await self._init_reconfigure(hass, mock_config_entry)

            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                user_input={CONF_HOST: "host.example.com", CONF_PORT: 6443},
            )

        assert result["type"] is FlowResultType.FORM
        assert result["errors"]["base"] == "token_required"

    async def test_reconfigure_abort_flow_propagates(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ):
        """Test AbortFlow is re-raised instead of becoming a cannot_connect error."""
        with patched_connection(side_effect=AbortFlow("already_configured")):
            result = await self._init_reconfigure(hass, mock_config_entry)

            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                user_input={
                    CONF_HOST: "new-host.example.com",
                    CONF_PORT: 6443,
                    CONF_API_TOKEN: "new-token",
                    CONF_MONITOR_ALL_NAMESPACES: True,
                },
            )

        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == "already_configured"

    async def test_reconfigure_preserves_cluster_name(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ):
        """Test that cluster_name is always injected from existing entry."""
        with patched_connection():
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
        with patched_connection():
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
                CONF_SCALE_COOLDOWN: DEFAULT_SCALE_COOLDOWN,
            },
            unique_id="test-cluster",
        )
        entry.add_to_hass(hass)

        with patched_connection():
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
        with patched_connection():
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
            patched_connection(),
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


# ---------------------------------------------------------------------------
# Additional coverage: _test_connection edge cases
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("raw_host", "expected"),
    [
        ("https://my-cluster.example.com", "my-cluster.example.com"),
        ("http://my-cluster.example.com", "my-cluster.example.com"),
        ("  my-cluster.example.com  ", "my-cluster.example.com"),
    ],
)
async def test_test_connection_cleans_host(
    hass: HomeAssistant, raw_host: str, expected: str
):
    """_test_connection strips the scheme and whitespace from the host."""
    flow = KubernetesConfigFlow()
    flow.hass = hass
    user_input = {
        CONF_HOST: raw_host,
        CONF_API_TOKEN: "test-token",
        CONF_VERIFY_SSL: False,
    }

    with _patch_probe(True):
        await flow._test_connection(user_input)

    assert user_input[CONF_HOST] == expected


async def test_test_connection_empty_host_after_strip(hass: HomeAssistant):
    """Test _test_connection raises when host is empty after stripping protocol."""
    flow = KubernetesConfigFlow()
    flow.hass = hass

    with (
        _patch_probe() as probe,
        pytest.raises(ValueError, match="Host cannot be empty"),
    ):
        await flow._test_connection(
            {
                CONF_HOST: "https://",
                CONF_API_TOKEN: "test-token",
            }
        )

    probe.assert_not_awaited()


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
    mock_session.get = MagicMock(return_value=mock_response)

    with patch(_SESSION, return_value=mock_session):
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
    mock_session.get = MagicMock(return_value=mock_response)

    with patch(_SESSION, return_value=mock_session):
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
    mock_session.get = MagicMock(return_value=mock_response)

    with patch(_SESSION, return_value=mock_session):
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
    mock_session.get = MagicMock(side_effect=TimeoutError())

    with patch(_SESSION, return_value=mock_session):
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
    mock_session.get = MagicMock(return_value=mock_response)

    with patch(_SESSION, return_value=mock_session):
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
    mock_session.get = MagicMock(return_value=mock_response)

    with patch(_SESSION, return_value=mock_session):
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
    mock_session.get = MagicMock(
        side_effect=aiohttp_mod.ServerTimeoutError("Request timed out")
    )

    with patch(_SESSION, return_value=mock_session):
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
    mock_session.get = MagicMock(return_value=mock_response)

    with patch(_SESSION, return_value=mock_session):
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
    mock_session.get = MagicMock(
        side_effect=aiohttp_mod.ClientConnectionError("Connection refused")
    )

    with patch(_SESSION, return_value=mock_session):
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
        with patched_connection():
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
        with patched_connection():
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
        assert mock_config_entry.data[CONF_SCALE_COOLDOWN] == DEFAULT_SCALE_COOLDOWN
        assert (
            mock_config_entry.data[CONF_DEVICE_GROUPING_MODE]
            == DEFAULT_DEVICE_GROUPING_MODE
        )

    async def test_reconfigure_with_legacy_scale_verification_timeout(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ):
        """An entry that still stores the removed option reconfigures fine."""
        legacy_key = "scale_verification_timeout"
        hass.config_entries.async_update_entry(
            mock_config_entry,
            data={**mock_config_entry.data, legacy_key: 30},
        )
        with patched_connection():
            result = await self._init_reconfigure(hass, mock_config_entry)
            assert result["type"] is FlowResultType.FORM
            assert legacy_key not in [str(k) for k in result["data_schema"].schema]

            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                user_input={
                    CONF_HOST: "host.example.com",
                    CONF_API_TOKEN: "test-token",
                    CONF_MONITOR_ALL_NAMESPACES: True,
                },
            )

        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == "reconfigure_successful"


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
            patched_connection(),
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
# Additional coverage: in-cluster port parsing
# ---------------------------------------------------------------------------


def test_read_in_cluster_config_non_numeric_port_falls_back_to_443(monkeypatch):
    """Test a non-numeric KUBERNETES_SERVICE_PORT_HTTPS falls back to 443."""
    import custom_components.kubernetes.config_flow as cf_module

    monkeypatch.setenv("KUBERNETES_SERVICE_HOST", "10.0.0.1")
    monkeypatch.setenv("KUBERNETES_SERVICE_PORT_HTTPS", "not-a-number")

    with (
        patch.object(cf_module, "_service_account_token_exists", return_value=True),
        patch.object(cf_module, "_read_service_account_token", return_value="t"),
        patch.object(cf_module, "_service_account_ca_exists", return_value=False),
    ):
        config = cf_module._read_in_cluster_config_sync()

    assert config == {"host": "10.0.0.1", "port": 443, "api_token": "t"}


# ---------------------------------------------------------------------------
# Additional coverage: user step with namespace removal
# ---------------------------------------------------------------------------


async def test_async_step_user_monitor_all_creates_entry_without_namespace(
    hass: HomeAssistant,
):
    """Test that user step creates entry without CONF_NAMESPACE when monitoring all."""
    with patched_connection():
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
    with patched_connection():
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
    mock_session.get = MagicMock(return_value=mock_response)

    with patch(_SESSION, return_value=mock_session):
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
    mock_session.get = MagicMock(return_value=mock_response)

    with patch(_SESSION, return_value=mock_session):
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
    mock_session.get = MagicMock(side_effect=TimeoutError())

    with patch(_SESSION, return_value=mock_session):
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
    mock_session.get = MagicMock(return_value=mock_response)

    with patch(_SESSION, return_value=mock_session):
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
    mock_session.get = MagicMock(return_value=mock_response)

    with patch(_SESSION, return_value=mock_session):
        # Should not raise, just return empty list
        result = await flow._fetch_namespaces(
            {
                CONF_HOST: "test-host",
                CONF_API_TOKEN: "test-token",
            }
        )

    assert result == []


# ---------------------------------------------------------------------------
# Reauthentication flow tests (real flow manager)
# ---------------------------------------------------------------------------


class TestReauthFlow:
    """Tests for the Kubernetes integration reauthentication flow."""

    @pytest.fixture
    def mock_config_entry(self, hass: HomeAssistant) -> MockConfigEntry:
        """Return a config entry added to hass for reauth tests."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="test-cluster",
            data={
                CONF_CLUSTER_NAME: "test-cluster",
                CONF_HOST: "cluster.example.com",
                CONF_PORT: 6443,
                CONF_API_TOKEN: "expired-token",
                CONF_CA_CERT: "/etc/ca.crt",
                CONF_VERIFY_SSL: False,
                CONF_USE_IN_CLUSTER: False,
                CONF_MONITOR_ALL_NAMESPACES: True,
            },
            unique_id="test-cluster",
        )
        entry.add_to_hass(hass)
        return entry

    async def _init_reauth(self, hass: HomeAssistant, entry: MockConfigEntry):
        """Helper to start a reauth flow."""
        return await hass.config_entries.flow.async_init(
            DOMAIN,
            context={
                "source": config_entries.SOURCE_REAUTH,
                "entry_id": entry.entry_id,
            },
            data=entry.data,
        )

    async def test_reauth_shows_token_only_form(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ):
        """Test reauth asks only for a new token and names the cluster."""
        result = await self._init_reauth(hass, mock_config_entry)

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "reauth_confirm"
        assert result["errors"] == {}
        assert result["description_placeholders"]["cluster_name"] == "test-cluster"
        assert result["description_placeholders"]["host"] == "cluster.example.com"
        schema_keys = [str(k) for k in result["data_schema"].schema]
        assert schema_keys == [CONF_API_TOKEN]

    async def test_reauth_successful_updates_only_the_token(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ):
        """Test a valid token is stored, the entry reloaded and the flow aborted."""
        with patched_connection() as mock_test_connection:
            result = await self._init_reauth(hass, mock_config_entry)
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                user_input={CONF_API_TOKEN: "fresh-token"},
            )

        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == "reauth_successful"
        assert mock_config_entry.data[CONF_API_TOKEN] == "fresh-token"
        # Everything except the token is untouched.
        assert mock_config_entry.data[CONF_HOST] == "cluster.example.com"
        assert mock_config_entry.data[CONF_CA_CERT] == "/etc/ca.crt"
        assert mock_config_entry.data[CONF_CLUSTER_NAME] == "test-cluster"
        # Already static: the in-cluster flag is left exactly as it was.
        assert mock_config_entry.data[CONF_USE_IN_CLUSTER] is False

        # The candidate validated is the entry's settings plus the new token.
        validated = mock_test_connection.call_args[0][0]
        assert validated[CONF_API_TOKEN] == "fresh-token"
        assert validated[CONF_HOST] == "cluster.example.com"
        assert validated[CONF_PORT] == 6443

    async def test_reauth_in_cluster_entry_switches_to_the_pasted_token(
        self, hass: HomeAssistant
    ):
        """Test reauth turns off in-cluster mode so the pasted token is used.

        An in-cluster entry only reaches reauth once the projected token is
        persistently rejected, so leaving the flag on would keep the pasted
        token inert and re-prompt forever.
        """
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="in-cluster",
            data={
                CONF_CLUSTER_NAME: "in-cluster",
                CONF_HOST: "kubernetes.default.svc",
                CONF_PORT: 443,
                CONF_API_TOKEN: "stale-fallback-token",
                CONF_USE_IN_CLUSTER: True,
                CONF_MONITOR_ALL_NAMESPACES: True,
            },
            unique_id="in-cluster",
        )
        entry.add_to_hass(hass)

        with patched_connection() as mock_test_connection:
            result = await self._init_reauth(hass, entry)
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                user_input={CONF_API_TOKEN: "pasted-token"},
            )

        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == "reauth_successful"
        assert entry.data[CONF_API_TOKEN] == "pasted-token"
        assert entry.data[CONF_USE_IN_CLUSTER] is False
        assert entry.data[CONF_HOST] == "kubernetes.default.svc"
        # The candidate mirrors what is stored: in-cluster mode off.
        assert mock_test_connection.call_args[0][0][CONF_USE_IN_CLUSTER] is False

    async def test_reauth_in_cluster_entry_rejects_an_empty_token(
        self, hass: HomeAssistant
    ):
        """Test an empty token is not filled from the pod's ServiceAccount.

        The entry would be saved with an empty token and in-cluster mode off,
        so validation must run with in-cluster mode off.
        """
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="in-cluster",
            data={
                CONF_CLUSTER_NAME: "in-cluster",
                CONF_HOST: "kubernetes.default.svc",
                CONF_PORT: 443,
                CONF_API_TOKEN: "stale-fallback-token",
                CONF_USE_IN_CLUSTER: True,
                CONF_MONITOR_ALL_NAMESPACES: True,
            },
            unique_id="in-cluster",
        )
        entry.add_to_hass(hass)

        probe = AsyncMock(return_value=True)
        with (
            patch(
                "custom_components.kubernetes.config_flow.async_detect_in_cluster_config",
                AsyncMock(return_value={"api_token": "pod-token"}),
            ),
            patch.object(KubernetesConfigFlow, "_test_connection_aiohttp", probe),
        ):
            result = await self._init_reauth(hass, entry)
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                user_input={CONF_API_TOKEN: ""},
            )

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "reauth_confirm"
        assert result["errors"] == {"base": "invalid_auth"}
        assert entry.data[CONF_API_TOKEN] == "stale-fallback-token"
        assert entry.data[CONF_USE_IN_CLUSTER] is True
        probe.assert_not_awaited()

    async def test_reauth_invalid_token_reshows_form_then_succeeds(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ):
        """Test a rejected token re-shows the form; a later valid token is stored."""
        with patched_connection(
            side_effect=[ValueError("Failed to connect: Unauthorized"), None]
        ):
            result = await self._init_reauth(hass, mock_config_entry)
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                user_input={CONF_API_TOKEN: "still-bad-token"},
            )

            assert result["type"] is FlowResultType.FORM
            assert result["step_id"] == "reauth_confirm"
            assert result["errors"]["base"] == "invalid_auth"
            assert mock_config_entry.data[CONF_API_TOKEN] == "expired-token"

            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                user_input={CONF_API_TOKEN: "good-token"},
            )

        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == "reauth_successful"
        assert mock_config_entry.data[CONF_API_TOKEN] == "good-token"


# ---------------------------------------------------------------------------
# The aiohttp calls made by the flow honor verify_ssl / ca_cert
# ---------------------------------------------------------------------------


def _mock_session(status: int = 200, json_body: dict | None = None) -> MagicMock:
    """Build a session mock whose GET returns ``status``."""
    mock_response = MagicMock()
    mock_response.status = status
    mock_response.json = AsyncMock(return_value=json_body or {"items": []})
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)

    mock_session = MagicMock()
    mock_session.get = MagicMock(return_value=mock_response)
    return mock_session


class TestFlowHonorsTls:
    """Both aiohttp call sites must pass the same ssl= value the runtime client uses.

    Before this, both hardcoded ``ssl=False``, so a certificate error passed
    validation and the entry then broke at runtime.
    """

    @pytest.mark.parametrize(
        "method", ["_test_connection_aiohttp", "_fetch_namespaces"]
    )
    async def test_passes_built_ssl_param(self, hass: HomeAssistant, method: str):
        """verify_ssl on + ca_cert -> the helper's return value reaches session.get."""
        flow = KubernetesConfigFlow()
        flow.hass = hass
        sentinel = object()
        mock_session = _mock_session()

        with (
            patch(_SESSION, return_value=mock_session),
            patch(
                "custom_components.kubernetes.config_flow.build_ssl_param",
                new_callable=AsyncMock,
                return_value=sentinel,
            ) as mock_build,
        ):
            await getattr(flow, method)(
                {
                    CONF_HOST: "test-host",
                    CONF_API_TOKEN: "test-token",
                    CONF_VERIFY_SSL: True,
                    CONF_CA_CERT: "/path/ca.crt",
                }
            )

        mock_build.assert_awaited_once_with(True, "/path/ca.crt")
        assert mock_session.get.call_args.kwargs["ssl"] is sentinel

    @pytest.mark.parametrize(
        "method", ["_test_connection_aiohttp", "_fetch_namespaces"]
    )
    async def test_verify_ssl_off_disables_verification(
        self, hass: HomeAssistant, method: str
    ):
        """verify_ssl off -> ssl=False, end to end through the real helper."""
        flow = KubernetesConfigFlow()
        flow.hass = hass
        mock_session = _mock_session()

        with patch(_SESSION, return_value=mock_session):
            await getattr(flow, method)(
                {
                    CONF_HOST: "test-host",
                    CONF_API_TOKEN: "test-token",
                    CONF_VERIFY_SSL: False,
                }
            )

        assert mock_session.get.call_args.kwargs["ssl"] is False

    async def test_unreadable_ca_cert_fails_connection_test(self, hass: HomeAssistant):
        """A CA path that cannot be loaded makes the probe fail instead of bypassing TLS."""
        flow = KubernetesConfigFlow()
        flow.hass = hass
        mock_session = _mock_session()

        with patch(_SESSION, return_value=mock_session):
            result = await flow._test_connection_aiohttp(
                {
                    CONF_HOST: "test-host",
                    CONF_API_TOKEN: "test-token",
                    CONF_VERIFY_SSL: True,
                    CONF_CA_CERT: "/nonexistent/ca.crt",
                }
            )

        assert result is False
        mock_session.get.assert_not_called()


# ---------------------------------------------------------------------------
# Field types and number ranges (D16, D17)
# ---------------------------------------------------------------------------


def _schema_field(schema, name):
    """Return the (key, validator) pair of a voluptuous schema field by name."""
    key = next(k for k in schema if k == name)
    return key, schema[key]


def _assert_password_selector(validator):
    assert isinstance(validator, selector.TextSelector)
    assert validator.config["type"] == selector.TextSelectorType.PASSWORD


class TestConfigFlowFieldValidation:
    """API tokens are masked and numeric fields reject out-of-range values."""

    async def _user_form_schema(self, hass: HomeAssistant):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        return result["data_schema"].schema

    async def test_user_api_token_is_password_selector(self, hass: HomeAssistant):
        """The user step masks the API token."""
        schema = await self._user_form_schema(hass)

        _, validator = _schema_field(schema, CONF_API_TOKEN)
        _assert_password_selector(validator)

    async def test_user_number_fields_are_ranged(self, hass: HomeAssistant):
        """Port, poll interval and cooldown carry their minimums."""
        schema = await self._user_form_schema(hass)

        _, port = _schema_field(schema, CONF_PORT)
        assert port(1) == 1
        assert port(65535) == 65535
        with pytest.raises(vol.Invalid):
            port(0)
        with pytest.raises(vol.Invalid):
            port(65536)

        _, interval = _schema_field(schema, CONF_SWITCH_UPDATE_INTERVAL)
        assert interval(1) == 1
        with pytest.raises(vol.Invalid):
            interval(0)

        _, cooldown = _schema_field(schema, CONF_SCALE_COOLDOWN)
        assert cooldown(0) == 0
        with pytest.raises(vol.Invalid):
            cooldown(-1)

    @pytest.mark.parametrize(
        ("field", "value"),
        [
            (CONF_PORT, 0),
            (CONF_SWITCH_UPDATE_INTERVAL, 0),
            (CONF_SCALE_COOLDOWN, -1),
        ],
    )
    async def test_user_rejects_invalid_number(
        self, hass: HomeAssistant, field: str, value: int
    ):
        """The flow manager rejects out-of-range numbers in the user step."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        with pytest.raises(InvalidData):
            await hass.config_entries.flow.async_configure(
                result["flow_id"],
                user_input={
                    CONF_CLUSTER_NAME: "test-cluster",
                    CONF_HOST: "kubernetes.example.com",
                    field: value,
                },
            )

    async def test_reconfigure_api_token_is_password_selector(
        self, hass: HomeAssistant
    ):
        """The reconfigure step masks the token and keeps its suggested value."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_CLUSTER_NAME: "test-cluster",
                CONF_HOST: "cluster.example.com",
                CONF_PORT: 6443,
                CONF_API_TOKEN: "stored-token",
            },
            unique_id="test-cluster",
        )
        entry.add_to_hass(hass)
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={
                "source": config_entries.SOURCE_RECONFIGURE,
                "entry_id": entry.entry_id,
            },
        )

        schema = result["data_schema"].schema
        key, validator = _schema_field(schema, CONF_API_TOKEN)
        _assert_password_selector(validator)
        assert key.description == {"suggested_value": "stored-token"}

    @pytest.mark.parametrize(
        ("field", "value"),
        [
            (CONF_PORT, 0),
            (CONF_SWITCH_UPDATE_INTERVAL, 0),
            (CONF_SCALE_COOLDOWN, -1),
        ],
    )
    async def test_reconfigure_rejects_invalid_number(
        self, hass: HomeAssistant, field: str, value: int
    ):
        """The flow manager rejects out-of-range numbers in the reconfigure step."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_CLUSTER_NAME: "test-cluster",
                CONF_HOST: "cluster.example.com",
                CONF_PORT: 6443,
                CONF_API_TOKEN: "stored-token",
            },
            unique_id="test-cluster",
        )
        entry.add_to_hass(hass)
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={
                "source": config_entries.SOURCE_RECONFIGURE,
                "entry_id": entry.entry_id,
            },
        )

        with pytest.raises(InvalidData):
            await hass.config_entries.flow.async_configure(
                result["flow_id"],
                user_input={CONF_HOST: "cluster.example.com", field: value},
            )

    async def test_reauth_api_token_is_password_selector(self, hass: HomeAssistant):
        """The reauth step masks the new token."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="test-cluster",
            data={
                CONF_CLUSTER_NAME: "test-cluster",
                CONF_HOST: "cluster.example.com",
                CONF_PORT: 6443,
                CONF_API_TOKEN: "expired-token",
            },
            unique_id="test-cluster",
        )
        entry.add_to_hass(hass)
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={
                "source": config_entries.SOURCE_REAUTH,
                "entry_id": entry.entry_id,
            },
            data=entry.data,
        )

        _, validator = _schema_field(result["data_schema"].schema, CONF_API_TOKEN)
        _assert_password_selector(validator)
