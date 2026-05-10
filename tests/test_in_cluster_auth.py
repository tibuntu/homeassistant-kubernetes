"""Tests for in-cluster ServiceAccount detection and runtime use."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, mock_open, patch

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.loader import DATA_COMPONENTS
import pytest

from custom_components.kubernetes.config_flow import (
    SERVICE_ACCOUNT_CA_FILE,
    KubernetesConfigFlow,
    _read_in_cluster_config_sync,
    async_detect_in_cluster_config,
)
from custom_components.kubernetes.const import (
    CONF_API_TOKEN,
    CONF_CA_CERT,
    CONF_HOST,
    CONF_PORT,
    CONF_USE_IN_CLUSTER,
    DOMAIN,
)
from custom_components.kubernetes.kubernetes_client import (
    IN_CLUSTER_TOKEN_CACHE_TTL,
    IN_CLUSTER_TOKEN_PATH,
    KubernetesClient,
)


@pytest.fixture(autouse=True)
def register_config_flow(hass: HomeAssistant):
    """Register the config flow handler so flow.async_init works."""
    hass.data.setdefault(DATA_COMPONENTS, {})[f"{DOMAIN}.config_flow"] = (
        KubernetesConfigFlow
    )
    config_entries.HANDLERS[DOMAIN] = KubernetesConfigFlow
    yield
    config_entries.HANDLERS.pop(DOMAIN, None)
    hass.data.get(DATA_COMPONENTS, {}).pop(f"{DOMAIN}.config_flow", None)


# ---------------------------------------------------------------------------
# _read_in_cluster_config_sync (pure helper)
# ---------------------------------------------------------------------------


def test_read_returns_none_when_service_host_env_missing(monkeypatch):
    """No KUBERNETES_SERVICE_HOST env → not running in-cluster."""
    monkeypatch.delenv("KUBERNETES_SERVICE_HOST", raising=False)
    assert _read_in_cluster_config_sync() is None


_TOKEN_EXISTS = "custom_components.kubernetes.config_flow._service_account_token_exists"
_CA_EXISTS = "custom_components.kubernetes.config_flow._service_account_ca_exists"
_READ_TOKEN = "custom_components.kubernetes.config_flow._read_service_account_token"


def test_read_returns_none_when_token_file_missing(monkeypatch):
    """Env var present but token file missing → not in-cluster."""
    monkeypatch.setenv("KUBERNETES_SERVICE_HOST", "10.0.0.1")
    with patch(_TOKEN_EXISTS, return_value=False):
        assert _read_in_cluster_config_sync() is None


def test_read_returns_full_config_when_token_and_ca_present(monkeypatch):
    """Happy path: env + token file + CA file all present."""
    monkeypatch.setenv("KUBERNETES_SERVICE_HOST", "10.0.0.1")
    monkeypatch.setenv("KUBERNETES_SERVICE_PORT_HTTPS", "6443")

    with (
        patch(_TOKEN_EXISTS, return_value=True),
        patch(_READ_TOKEN, return_value="bearer-token\n"),
        patch(_CA_EXISTS, return_value=True),
    ):
        config = _read_in_cluster_config_sync()

    assert config == {
        "host": "10.0.0.1",
        "port": 6443,
        "api_token": "bearer-token",
        "ca_cert": str(SERVICE_ACCOUNT_CA_FILE),
    }


def test_read_omits_ca_cert_when_ca_file_missing(monkeypatch):
    """CA cert key is omitted when ca.crt isn't mounted."""
    monkeypatch.setenv("KUBERNETES_SERVICE_HOST", "10.0.0.1")
    monkeypatch.setenv("KUBERNETES_SERVICE_PORT", "443")
    monkeypatch.delenv("KUBERNETES_SERVICE_PORT_HTTPS", raising=False)

    with (
        patch(_TOKEN_EXISTS, return_value=True),
        patch(_READ_TOKEN, return_value="t"),
        patch(_CA_EXISTS, return_value=False),
    ):
        config = _read_in_cluster_config_sync()

    assert config == {"host": "10.0.0.1", "port": 443, "api_token": "t"}


def test_read_falls_back_to_https_port_then_default(monkeypatch):
    """Port resolution: PORT_HTTPS → PORT → 443."""
    monkeypatch.setenv("KUBERNETES_SERVICE_HOST", "10.0.0.1")
    monkeypatch.delenv("KUBERNETES_SERVICE_PORT_HTTPS", raising=False)
    monkeypatch.delenv("KUBERNETES_SERVICE_PORT", raising=False)

    with (
        patch(_TOKEN_EXISTS, return_value=True),
        patch(_READ_TOKEN, return_value="t"),
        patch(_CA_EXISTS, return_value=False),
    ):
        config = _read_in_cluster_config_sync()

    assert config is not None
    assert config["port"] == 443


def test_read_returns_none_when_token_unreadable(monkeypatch):
    """OSError on read → degrades to not-in-cluster rather than crashing."""
    monkeypatch.setenv("KUBERNETES_SERVICE_HOST", "10.0.0.1")

    with (
        patch(_TOKEN_EXISTS, return_value=True),
        patch(_READ_TOKEN, side_effect=OSError("permission denied")),
    ):
        assert _read_in_cluster_config_sync() is None


def test_read_returns_none_when_token_empty(monkeypatch):
    """Empty token file → treated as missing."""
    monkeypatch.setenv("KUBERNETES_SERVICE_HOST", "10.0.0.1")

    with (
        patch(_TOKEN_EXISTS, return_value=True),
        patch(_READ_TOKEN, return_value="  \n"),
    ):
        assert _read_in_cluster_config_sync() is None


# ---------------------------------------------------------------------------
# async_detect_in_cluster_config (executor wrapper)
# ---------------------------------------------------------------------------


async def test_async_detect_runs_off_event_loop(hass: HomeAssistant):
    """Verify the async wrapper delegates to the executor and returns the dict."""
    with patch(
        "custom_components.kubernetes.config_flow._read_in_cluster_config_sync",
        return_value={"host": "h", "port": 443, "api_token": "t"},
    ):
        result = await async_detect_in_cluster_config(hass)
    assert result == {"host": "h", "port": 443, "api_token": "t"}


# ---------------------------------------------------------------------------
# async_step_user pre-fill behaviour
# ---------------------------------------------------------------------------


def _suggested_values(schema) -> dict[str, Any]:
    """Pull out per-field suggested_value from a voluptuous schema."""
    suggestions: dict[str, Any] = {}
    for marker in schema.schema:
        description = getattr(marker, "description", None)
        if isinstance(description, dict) and "suggested_value" in description:
            suggestions[str(marker)] = description["suggested_value"]
    return suggestions


async def test_user_step_prefills_when_in_cluster_detected(hass: HomeAssistant):
    """Detected in-cluster credentials populate host/api_token/ca_cert/port."""
    detected = {
        "host": "10.0.0.1",
        "port": 6443,
        "api_token": "in-cluster-token",
        "ca_cert": "/var/run/secrets/kubernetes.io/serviceaccount/ca.crt",
    }
    with (
        patch(
            "custom_components.kubernetes.config_flow._ensure_kubernetes_imported",
            return_value=True,
        ),
        patch(
            "custom_components.kubernetes.config_flow.async_detect_in_cluster_config",
            new_callable=AsyncMock,
            return_value=detected,
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    suggestions = _suggested_values(result["data_schema"])
    assert suggestions[CONF_HOST] == "10.0.0.1"
    assert suggestions[CONF_API_TOKEN] == "in-cluster-token"
    assert suggestions[CONF_CA_CERT] == detected["ca_cert"]
    # Port uses default=, not suggested_value, so it isn't in suggestions.
    # The default is set to the detected port — verified indirectly via the
    # absence of CONF_PORT in suggestions and presence in the schema below.
    schema_defaults = {
        str(m): m.default()
        for m in result["data_schema"].schema
        if hasattr(m, "default") and callable(m.default)
    }
    assert schema_defaults[CONF_PORT] == 6443


async def test_user_step_no_prefill_when_not_in_cluster(hass: HomeAssistant):
    """Without in-cluster credentials, no fields carry suggested_value."""
    with (
        patch(
            "custom_components.kubernetes.config_flow._ensure_kubernetes_imported",
            return_value=True,
        ),
        patch(
            "custom_components.kubernetes.config_flow.async_detect_in_cluster_config",
            new_callable=AsyncMock,
            return_value=None,
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

    assert result["type"] is FlowResultType.FORM
    suggestions = _suggested_values(result["data_schema"])
    # No connection fields should be pre-filled.
    assert CONF_HOST not in suggestions
    assert CONF_API_TOKEN not in suggestions
    assert CONF_CA_CERT not in suggestions


async def test_user_step_use_in_cluster_default_true_when_detected(
    hass: HomeAssistant,
):
    """The use_in_cluster checkbox defaults to True only when detection succeeds."""
    detected = {"host": "10.0.0.1", "port": 6443, "api_token": "t"}
    with (
        patch(
            "custom_components.kubernetes.config_flow._ensure_kubernetes_imported",
            return_value=True,
        ),
        patch(
            "custom_components.kubernetes.config_flow.async_detect_in_cluster_config",
            new_callable=AsyncMock,
            return_value=detected,
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

    defaults = {
        str(m): m.default()
        for m in result["data_schema"].schema
        if hasattr(m, "default") and callable(m.default)
    }
    assert defaults[CONF_USE_IN_CLUSTER] is True


async def test_user_step_use_in_cluster_default_false_outside(hass: HomeAssistant):
    """Outside the cluster the checkbox defaults to False so behaviour is unchanged."""
    with (
        patch(
            "custom_components.kubernetes.config_flow._ensure_kubernetes_imported",
            return_value=True,
        ),
        patch(
            "custom_components.kubernetes.config_flow.async_detect_in_cluster_config",
            new_callable=AsyncMock,
            return_value=None,
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

    defaults = {
        str(m): m.default()
        for m in result["data_schema"].schema
        if hasattr(m, "default") and callable(m.default)
    }
    assert defaults[CONF_USE_IN_CLUSTER] is False


# ---------------------------------------------------------------------------
# KubernetesClient.api_token runtime behaviour
# ---------------------------------------------------------------------------


def _make_client(
    *, use_in_cluster: bool = True, static_token: str = "fallback-token"
) -> KubernetesClient:
    """Build a real KubernetesClient with the official-client setup short-circuited."""
    config = {
        CONF_HOST: "10.0.0.1",
        CONF_PORT: 6443,
        CONF_API_TOKEN: static_token,
        CONF_USE_IN_CLUSTER: use_in_cluster,
    }
    with patch.object(KubernetesClient, "_setup_kubernetes_client"):
        return KubernetesClient(config)


def test_api_token_returns_static_when_use_in_cluster_disabled():
    """With the runtime toggle off, the configured static token is returned verbatim."""
    client = _make_client(use_in_cluster=False, static_token="config-token")
    assert client.api_token == "config-token"


def test_api_token_reads_file_when_use_in_cluster_enabled():
    """With the toggle on, the property reads the projected SA token file."""
    client = _make_client(use_in_cluster=True)
    with patch(
        "custom_components.kubernetes.kubernetes_client.open",
        mock_open(read_data="fresh-pod-token\n"),
    ) as opener:
        token = client.api_token

    assert token == "fresh-pod-token"
    opener.assert_called_once_with(IN_CLUSTER_TOKEN_PATH, encoding="utf-8")


def test_api_token_uses_cache_within_ttl(monkeypatch):
    """A second read inside the TTL window must not touch the file again."""
    client = _make_client(use_in_cluster=True)

    monkeypatch.setattr(
        "custom_components.kubernetes.kubernetes_client.time.time",
        lambda: 1000.0,
    )
    with patch(
        "custom_components.kubernetes.kubernetes_client.open",
        mock_open(read_data="t1"),
    ) as opener:
        first = client.api_token
        # Inside TTL: same call again must hit the cache.
        monkeypatch.setattr(
            "custom_components.kubernetes.kubernetes_client.time.time",
            lambda: 1000.0 + IN_CLUSTER_TOKEN_CACHE_TTL - 1,
        )
        second = client.api_token

    assert first == "t1"
    assert second == "t1"
    assert opener.call_count == 1


def test_api_token_refreshes_after_ttl(monkeypatch):
    """Once the TTL elapses the file is re-read and a rotated token is returned."""
    client = _make_client(use_in_cluster=True)
    # Pre-populate the cache as if it was set at t=0.
    client._token_cache = "old-token"
    client._token_cache_time = 0.0

    monkeypatch.setattr(
        "custom_components.kubernetes.kubernetes_client.time.time",
        lambda: IN_CLUSTER_TOKEN_CACHE_TTL + 1,
    )
    with patch(
        "custom_components.kubernetes.kubernetes_client.open",
        mock_open(read_data="rotated-token"),
    ):
        token = client.api_token

    assert token == "rotated-token"


def test_api_token_falls_back_to_static_on_read_error():
    """OSError while reading the projected token returns the configured fallback."""
    client = _make_client(use_in_cluster=True, static_token="static-fallback")
    with patch(
        "custom_components.kubernetes.kubernetes_client.open",
        side_effect=OSError("denied"),
    ):
        assert client.api_token == "static-fallback"


def test_invalidate_token_cache_forces_reread(monkeypatch):
    """invalidate_token_cache makes the next access re-read regardless of TTL."""
    client = _make_client(use_in_cluster=True)
    # Cache freshly populated within TTL — without invalidation no read happens.
    client._token_cache = "original"
    client._token_cache_time = 1_000_000.0

    monkeypatch.setattr(
        "custom_components.kubernetes.kubernetes_client.time.time",
        lambda: 1_000_000.0 + 5,  # well within TTL
    )

    with patch(
        "custom_components.kubernetes.kubernetes_client.open",
        mock_open(read_data="rotated"),
    ):
        client.invalidate_token_cache()
        token = client.api_token

    assert token == "rotated"


def test_refresh_api_key_hook_updates_configuration():
    """The hook installed on the official-client Configuration receives the live token."""
    client = _make_client(use_in_cluster=True)

    class _Cfg:
        api_key: dict[str, str] = {}

    cfg = _Cfg()
    cfg.api_key = {"authorization": "Bearer stale"}

    with patch(
        "custom_components.kubernetes.kubernetes_client.open",
        mock_open(read_data="rotated-token"),
    ):
        client._refresh_api_key_hook(cfg)

    assert cfg.api_key["authorization"] == "Bearer rotated-token"


def test_log_error_invalidates_token_cache_on_401():
    """A 401 ApiException must drop the cached SA token so the next call re-reads."""
    from kubernetes.client.rest import ApiException

    client = _make_client(use_in_cluster=True)
    # Seed a fresh-looking cache.
    client._token_cache = "stale-token"
    client._token_cache_time = 1_000_000.0

    err = ApiException(status=401, reason="Unauthorized")
    client._log_error("get_pods", err)

    assert client._token_cache_time == 0.0


def test_log_error_does_not_invalidate_cache_when_not_in_cluster():
    """Static-token mode must not touch the cache state on 401."""
    from kubernetes.client.rest import ApiException

    client = _make_client(use_in_cluster=False)
    client._token_cache_time = 1_000_000.0

    err = ApiException(status=401, reason="Unauthorized")
    client._log_error("get_pods", err)

    assert client._token_cache_time == 1_000_000.0


def test_setup_kubernetes_client_wires_hook_when_in_cluster():
    """_setup_kubernetes_client installs the refresh hook only when use_in_cluster=True."""
    config = {
        CONF_HOST: "10.0.0.1",
        CONF_PORT: 6443,
        CONF_API_TOKEN: "static",
        CONF_USE_IN_CLUSTER: True,
    }
    fake_cfg = MagicMock()
    fake_cfg.api_key = {}

    with (
        patch(
            "custom_components.kubernetes.kubernetes_client.k8s_client.Configuration",
            return_value=fake_cfg,
        ),
        patch("custom_components.kubernetes.kubernetes_client.k8s_client.ApiClient"),
        patch("custom_components.kubernetes.kubernetes_client.k8s_client.CoreV1Api"),
        patch("custom_components.kubernetes.kubernetes_client.k8s_client.AppsV1Api"),
        patch("custom_components.kubernetes.kubernetes_client.k8s_client.BatchV1Api"),
    ):
        client = KubernetesClient(config)

    # The hook must be the bound method, and the initial api_key must use the
    # static token (not trigger a file read on the event loop).
    assert fake_cfg.refresh_api_key_hook == client._refresh_api_key_hook
    assert fake_cfg.api_key == {"authorization": "Bearer static"}


def test_api_token_setter_updates_static_and_clears_cache():
    """The setter rewrites the static fallback and drops any cached SA token."""
    client = _make_client(use_in_cluster=True, static_token="initial")
    client._token_cache = "cached-from-file"
    client._token_cache_time = 1_000_000.0

    client.api_token = "rotated-static"

    assert client._static_api_token == "rotated-static"
    assert client._token_cache == ""
    assert client._token_cache_time == 0.0


def test_api_token_returns_fallback_when_file_yields_empty(monkeypatch):
    """A whitespace-only token file is treated as a read failure (use static fallback)."""
    client = _make_client(use_in_cluster=True, static_token="static-fallback")
    with patch(
        "custom_components.kubernetes.kubernetes_client.open",
        mock_open(read_data="   \n"),
    ):
        token = client.api_token

    assert token == "static-fallback"
    # Empty tokens are never cached.
    assert client._token_cache == ""


# ---------------------------------------------------------------------------
# config_flow.py SA file-op helper coverage
# ---------------------------------------------------------------------------


def test_service_account_token_exists_helper_reflects_path_state():
    """_service_account_token_exists is a thin wrapper over Path.is_file."""
    from custom_components.kubernetes.config_flow import (
        _service_account_token_exists,
    )

    with patch("pathlib.Path.is_file", return_value=True):
        assert _service_account_token_exists() is True
    with patch("pathlib.Path.is_file", return_value=False):
        assert _service_account_token_exists() is False


def test_service_account_ca_exists_helper_reflects_path_state():
    """_service_account_ca_exists is a thin wrapper over Path.is_file."""
    from custom_components.kubernetes.config_flow import (
        _service_account_ca_exists,
    )

    with patch("pathlib.Path.is_file", return_value=True):
        assert _service_account_ca_exists() is True
    with patch("pathlib.Path.is_file", return_value=False):
        assert _service_account_ca_exists() is False


def test_read_service_account_token_helper_returns_file_contents():
    """_read_service_account_token returns the file contents verbatim."""
    from custom_components.kubernetes.config_flow import (
        _read_service_account_token,
    )

    with patch("pathlib.Path.read_text", return_value="raw-token\n"):
        assert _read_service_account_token() == "raw-token\n"


def test_setup_kubernetes_client_skips_hook_for_static_mode():
    """Static-token mode leaves Configuration.refresh_api_key_hook untouched."""
    config = {
        CONF_HOST: "10.0.0.1",
        CONF_PORT: 6443,
        CONF_API_TOKEN: "static",
        CONF_USE_IN_CLUSTER: False,
    }
    fake_cfg = MagicMock(spec_set=["host", "api_key", "api_key_prefix", "verify_ssl"])
    fake_cfg.api_key = {}

    with (
        patch(
            "custom_components.kubernetes.kubernetes_client.k8s_client.Configuration",
            return_value=fake_cfg,
        ),
        patch("custom_components.kubernetes.kubernetes_client.k8s_client.ApiClient"),
        patch("custom_components.kubernetes.kubernetes_client.k8s_client.CoreV1Api"),
        patch("custom_components.kubernetes.kubernetes_client.k8s_client.AppsV1Api"),
        patch("custom_components.kubernetes.kubernetes_client.k8s_client.BatchV1Api"),
    ):
        # spec_set without refresh_api_key_hook means an attempt to set it
        # would AttributeError — proving the production code didn't try.
        KubernetesClient(config)
