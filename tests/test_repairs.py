"""Tests for repair issues raised by the Kubernetes integration."""

from __future__ import annotations

import builtins
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.kubernetes import (
    DOMAIN,
    ISSUE_KUBERNETES_PACKAGE_MISSING,
    async_remove_entry,
    async_setup_entry,
)
from custom_components.kubernetes.const import (
    CONF_DISABLED_RESOURCES,
    CONF_ENABLE_EVENTS,
    CONF_ENABLE_WATCH,
)
from custom_components.kubernetes.coordinator import (
    ISSUE_METRICS_SERVER_UNAVAILABLE,
    ISSUE_WATCH_CONNECTION_FAILING,
    METRICS_SERVER_LEARN_MORE_URL,
    KubernetesDataCoordinator,
)


@pytest.fixture
def mock_entry(hass: HomeAssistant) -> MockConfigEntry:
    """Config entry usable for both setup and direct coordinator construction."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        entry_id="repair_entry",
        data={
            "host": "test-cluster.example.com",
            "port": 6443,
            "api_token": "tok",
            "namespace": "default",
            "verify_ssl": True,
        },
        options={},
    )
    entry.add_to_hass(hass)
    return entry


def _make_client(*, cluster_name: str = "test-cluster") -> MagicMock:
    client = MagicMock()
    client.cluster_name = cluster_name
    return client


def _make_coordinator(
    hass: HomeAssistant, entry: MockConfigEntry
) -> KubernetesDataCoordinator:
    return KubernetesDataCoordinator(hass, entry, _make_client())


# ---------------------------------------------------------------------------
# Package-missing issue (raised from __init__.py:async_setup_entry)
# ---------------------------------------------------------------------------


async def test_setup_entry_creates_issue_on_import_error(
    hass: HomeAssistant, mock_entry: MockConfigEntry
):
    """ImportError on kubernetes.client surfaces as a repair issue."""
    original_import = builtins.__import__

    def _raise(name, *args, **kwargs):
        if name == "kubernetes.client":
            raise ImportError("No module named 'kubernetes'")
        return original_import(name, *args, **kwargs)

    with patch.object(builtins, "__import__", side_effect=_raise):
        result = await async_setup_entry(hass, mock_entry)

    assert result is False
    issue = ir.async_get(hass).async_get_issue(DOMAIN, ISSUE_KUBERNETES_PACKAGE_MISSING)
    assert issue is not None
    assert issue.severity == ir.IssueSeverity.ERROR
    assert issue.is_fixable is False
    assert issue.translation_key == ISSUE_KUBERNETES_PACKAGE_MISSING


async def test_setup_entry_clears_issue_on_success(
    hass: HomeAssistant, mock_entry: MockConfigEntry
):
    """A successful setup removes a stale package-missing issue."""
    ir.async_create_issue(
        hass,
        DOMAIN,
        ISSUE_KUBERNETES_PACKAGE_MISSING,
        is_fixable=False,
        severity=ir.IssueSeverity.ERROR,
        translation_key=ISSUE_KUBERNETES_PACKAGE_MISSING,
    )
    assert ir.async_get(hass).async_get_issue(DOMAIN, ISSUE_KUBERNETES_PACKAGE_MISSING)

    with (
        patch("custom_components.kubernetes.kubernetes_client.k8s_client"),
        patch("custom_components.kubernetes.KubernetesClient"),
        patch(
            "custom_components.kubernetes.KubernetesDataCoordinator"
        ) as mock_coord_class,
        patch("custom_components.kubernetes._async_sync_panel"),
        patch.object(
            hass.config_entries,
            "async_forward_entry_setups",
            new_callable=AsyncMock,
        ),
    ):
        mock_coord = MagicMock()
        mock_coord.async_config_entry_first_refresh = AsyncMock()
        mock_coord.async_start_watch_tasks = AsyncMock()
        mock_coord_class.return_value = mock_coord

        await async_setup_entry(hass, mock_entry)

    assert (
        ir.async_get(hass).async_get_issue(DOMAIN, ISSUE_KUBERNETES_PACKAGE_MISSING)
        is None
    )


async def test_async_remove_entry_clears_package_missing_issue(
    hass: HomeAssistant, mock_entry: MockConfigEntry
):
    """Removing a (failed) entry clears the package-missing issue.

    async_unload_entry is skipped when async_setup_entry returned False,
    so async_remove_entry is the only path that can clean this up.
    """
    ir.async_create_issue(
        hass,
        DOMAIN,
        ISSUE_KUBERNETES_PACKAGE_MISSING,
        is_fixable=False,
        severity=ir.IssueSeverity.ERROR,
        translation_key=ISSUE_KUBERNETES_PACKAGE_MISSING,
    )

    await async_remove_entry(hass, mock_entry)

    assert (
        ir.async_get(hass).async_get_issue(DOMAIN, ISSUE_KUBERNETES_PACKAGE_MISSING)
        is None
    )


# ---------------------------------------------------------------------------
# Metrics-server-unavailable issue (raised from coordinator)
# ---------------------------------------------------------------------------


def _expected_metrics_issue_id(entry: MockConfigEntry) -> str:
    return f"{ISSUE_METRICS_SERVER_UNAVAILABLE}_{entry.entry_id}"


async def test_metrics_issue_created_when_nodes_have_no_metrics(
    hass: HomeAssistant, mock_entry: MockConfigEntry
):
    """Nodes present + empty metrics dict → repair issue is raised."""
    coordinator = _make_coordinator(hass, mock_entry)

    coordinator._sync_metrics_repair_issue(
        nodes=[{"name": "n1"}, {"name": "n2"}],
        node_metrics={},
    )

    issue = ir.async_get(hass).async_get_issue(
        DOMAIN, _expected_metrics_issue_id(mock_entry)
    )
    assert issue is not None
    assert issue.severity == ir.IssueSeverity.WARNING
    assert issue.is_fixable is False
    assert issue.translation_key == ISSUE_METRICS_SERVER_UNAVAILABLE
    assert issue.translation_placeholders == {"cluster": "test-cluster"}
    assert issue.learn_more_url == METRICS_SERVER_LEARN_MORE_URL
    assert coordinator._metrics_issue_active is True


async def test_metrics_issue_dismissed_when_metrics_return(
    hass: HomeAssistant, mock_entry: MockConfigEntry
):
    """Issue is removed once metrics start returning again."""
    coordinator = _make_coordinator(hass, mock_entry)

    coordinator._sync_metrics_repair_issue([{"name": "n1"}], {})
    assert coordinator._metrics_issue_active is True

    coordinator._sync_metrics_repair_issue(
        [{"name": "n1"}], {"n1": {"cpu": 100, "memory": 256}}
    )

    assert coordinator._metrics_issue_active is False
    assert (
        ir.async_get(hass).async_get_issue(
            DOMAIN, _expected_metrics_issue_id(mock_entry)
        )
        is None
    )


async def test_metrics_issue_not_created_for_empty_cluster(
    hass: HomeAssistant, mock_entry: MockConfigEntry
):
    """A cluster with no nodes should not surface the metrics issue."""
    coordinator = _make_coordinator(hass, mock_entry)

    coordinator._sync_metrics_repair_issue(nodes=[], node_metrics={})

    assert coordinator._metrics_issue_active is False
    assert (
        ir.async_get(hass).async_get_issue(
            DOMAIN, _expected_metrics_issue_id(mock_entry)
        )
        is None
    )


async def test_metrics_issue_idempotent_on_repeat(
    hass: HomeAssistant, mock_entry: MockConfigEntry
):
    """Repeated calls in the unavailable state must not flap the issue registry."""
    coordinator = _make_coordinator(hass, mock_entry)

    coordinator._sync_metrics_repair_issue([{"name": "n1"}], {})
    with patch.object(ir, "async_create_issue") as create_again:
        coordinator._sync_metrics_repair_issue([{"name": "n1"}], {})
        coordinator._sync_metrics_repair_issue([{"name": "n1"}], {})
        create_again.assert_not_called()


async def test_async_clear_repair_issues_on_unload(
    hass: HomeAssistant, mock_entry: MockConfigEntry
):
    """Coordinator cleanup removes any active metrics issue and resets state."""
    coordinator = _make_coordinator(hass, mock_entry)
    coordinator._sync_metrics_repair_issue([{"name": "n1"}], {})
    assert coordinator._metrics_issue_active is True

    coordinator.async_clear_repair_issues()

    assert coordinator._metrics_issue_active is False
    assert (
        ir.async_get(hass).async_get_issue(
            DOMAIN, _expected_metrics_issue_id(mock_entry)
        )
        is None
    )


async def test_async_clear_repair_issues_removes_orphaned_issue(
    hass: HomeAssistant, mock_entry: MockConfigEntry
):
    """Cleanup deletes issues this coordinator instance did not create.

    An issue can be inherited from an earlier setup that never unloaded
    cleanly; the in-memory ``*_issue_active`` flags are False then, but the
    registry entry must still be removed (issue #349).
    """
    coordinator = _make_coordinator(hass, mock_entry)
    _create_orphaned_watch_issue(hass, mock_entry)
    assert coordinator._watch_issue_active is False

    coordinator.async_clear_repair_issues()

    assert (
        ir.async_get(hass).async_get_issue(DOMAIN, _expected_watch_issue_id(mock_entry))
        is None
    )


async def test_async_clear_repair_issues_safe_when_no_issue_exists(
    hass: HomeAssistant, mock_entry: MockConfigEntry
):
    """Cleanup is safe to call when no issue was ever raised."""
    coordinator = _make_coordinator(hass, mock_entry)

    coordinator.async_clear_repair_issues()

    assert coordinator._metrics_issue_active is False
    assert coordinator._watch_issue_active is False


# ---------------------------------------------------------------------------
# Stale-issue cleanup at setup (async_cleanup_stale_repair_issues, issue #349)
# ---------------------------------------------------------------------------


def _expected_watch_issue_id(entry: MockConfigEntry) -> str:
    return f"{ISSUE_WATCH_CONNECTION_FAILING}_{entry.entry_id}"


def _create_orphaned_watch_issue(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    ir.async_create_issue(
        hass,
        DOMAIN,
        _expected_watch_issue_id(entry),
        is_fixable=False,
        severity=ir.IssueSeverity.WARNING,
        translation_key=ISSUE_WATCH_CONNECTION_FAILING,
    )


def _options_entry(hass: HomeAssistant, options: dict) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "host": "test-cluster.example.com",
            "port": 6443,
            "api_token": "tok",
            "namespace": "default",
            "verify_ssl": True,
        },
        options=options,
    )
    entry.add_to_hass(hass)
    return entry


async def test_stale_watch_issue_removed_when_watch_and_events_disabled(
    hass: HomeAssistant,
):
    """Switching back to polling mode removes a leftover watch issue."""
    entry = _options_entry(hass, {CONF_ENABLE_WATCH: False})
    _create_orphaned_watch_issue(hass, entry)
    coordinator = _make_coordinator(hass, entry)

    coordinator.async_cleanup_stale_repair_issues()

    assert (
        ir.async_get(hass).async_get_issue(DOMAIN, _expected_watch_issue_id(entry))
        is None
    )


@pytest.mark.parametrize(
    "options",
    [
        {},  # watch defaults to enabled
        {CONF_ENABLE_WATCH: True},
        {CONF_ENABLE_WATCH: False, CONF_ENABLE_EVENTS: True},
    ],
)
async def test_watch_issue_kept_while_a_watch_feature_is_enabled(
    hass: HomeAssistant, options: dict
):
    """The watch/event loops own the issue while either feature is on."""
    entry = _options_entry(hass, options)
    _create_orphaned_watch_issue(hass, entry)
    coordinator = _make_coordinator(hass, entry)

    coordinator.async_cleanup_stale_repair_issues()

    assert (
        ir.async_get(hass).async_get_issue(DOMAIN, _expected_watch_issue_id(entry))
        is not None
    )


async def test_stale_metrics_issue_removed_when_metrics_disabled(
    hass: HomeAssistant,
):
    """Opting out of metrics collection removes a leftover metrics issue."""
    entry = _options_entry(hass, {CONF_DISABLED_RESOURCES: ["metrics"]})
    ir.async_create_issue(
        hass,
        DOMAIN,
        _expected_metrics_issue_id(entry),
        is_fixable=False,
        severity=ir.IssueSeverity.WARNING,
        translation_key=ISSUE_METRICS_SERVER_UNAVAILABLE,
    )
    coordinator = _make_coordinator(hass, entry)

    coordinator.async_cleanup_stale_repair_issues()

    assert (
        ir.async_get(hass).async_get_issue(DOMAIN, _expected_metrics_issue_id(entry))
        is None
    )


async def test_metrics_issue_kept_when_metrics_enabled(
    hass: HomeAssistant, mock_entry: MockConfigEntry
):
    """The metrics sync owns the issue while metrics collection is on."""
    coordinator = _make_coordinator(hass, mock_entry)
    coordinator._sync_metrics_repair_issue([{"name": "n1"}], {})

    coordinator.async_cleanup_stale_repair_issues()

    assert (
        ir.async_get(hass).async_get_issue(
            DOMAIN, _expected_metrics_issue_id(mock_entry)
        )
        is not None
    )
