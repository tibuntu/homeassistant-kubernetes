"""Tests for the Kubernetes integration __init__.py module."""

from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.kubernetes import (
    DOMAIN,
    PLATFORMS,
    _any_entry_wants_panel,
    _async_register_panel,
    _async_remove_panel,
    _count_config_entries,
    async_setup,
    async_setup_entry,
    async_unload_entry,
)


@pytest.fixture
def mock_config_entry(hass: HomeAssistant) -> MockConfigEntry:
    """Create a mock config entry and add it to hass."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        entry_id="test_entry_id",
        data={
            "host": "test-cluster.example.com",
            "port": 6443,
            "api_token": "test-token",
            "namespace": "default",
            "verify_ssl": True,
        },
        options={},
    )
    entry.add_to_hass(hass)
    return entry


async def test_async_setup(hass: HomeAssistant):
    """Test async_setup function."""
    with patch(
        "custom_components.kubernetes.async_register_websocket_commands"
    ) as mock_ws:
        result = await async_setup(hass, {})
        assert result is True
        mock_ws.assert_called_once_with(hass)


async def test_async_setup_entry_success(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
):
    """Test successful async_setup_entry."""
    with (
        patch("custom_components.kubernetes.kubernetes_client.k8s_client"),
        patch("custom_components.kubernetes.KubernetesClient") as mock_client_class,
        patch(
            "custom_components.kubernetes.KubernetesDataCoordinator"
        ) as mock_coordinator_class,
        patch(
            "custom_components.kubernetes.async_setup_services"
        ) as mock_setup_services,
        patch("custom_components.kubernetes._async_sync_panel") as mock_sync_panel,
        patch.object(
            hass.config_entries, "async_forward_entry_setups", new_callable=AsyncMock
        ) as mock_forward,
    ):
        mock_sync_panel.return_value = None

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_coordinator = MagicMock()
        mock_coordinator.async_config_entry_first_refresh = AsyncMock()
        mock_coordinator_class.return_value = mock_coordinator

        result = await async_setup_entry(hass, mock_config_entry)

        assert result is True
        assert DOMAIN in hass.data
        assert mock_config_entry.entry_id in hass.data[DOMAIN]
        assert (
            hass.data[DOMAIN][mock_config_entry.entry_id]["config"]
            == mock_config_entry.data
        )
        assert hass.data[DOMAIN][mock_config_entry.entry_id]["client"] == mock_client
        assert (
            hass.data[DOMAIN][mock_config_entry.entry_id]["coordinator"]
            == mock_coordinator
        )

        # Verify services were set up for first entry
        mock_setup_services.assert_called_once_with(hass)

        # Verify panel sync was called
        mock_sync_panel.assert_called_once_with(hass, mock_config_entry)

        # Verify coordinator was started
        mock_coordinator.async_config_entry_first_refresh.assert_called_once()

        # Verify platforms were forwarded
        mock_forward.assert_called_once_with(mock_config_entry, PLATFORMS)


async def test_async_setup_entry_kubernetes_not_available(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
):
    """Test async_setup_entry when kubernetes package is not available."""
    import builtins

    original_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if name == "kubernetes.client":
            raise ImportError("No module named 'kubernetes'")
        return original_import(name, *args, **kwargs)

    with patch.object(builtins, "__import__", side_effect=mock_import):
        result = await async_setup_entry(hass, mock_config_entry)

        assert result is False
        assert mock_config_entry.entry_id not in hass.data.get(DOMAIN, {})


async def test_async_setup_entry_second_entry(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
):
    """Test async_setup_entry for second config entry (should not set up services again)."""
    # Pre-populate with an existing entry
    hass.data[DOMAIN] = {"existing_entry": {}}

    with (
        patch("custom_components.kubernetes.kubernetes_client.k8s_client"),
        patch("custom_components.kubernetes.KubernetesClient") as mock_client_class,
        patch(
            "custom_components.kubernetes.KubernetesDataCoordinator"
        ) as mock_coordinator_class,
        patch(
            "custom_components.kubernetes.async_setup_services"
        ) as mock_setup_services,
        patch("custom_components.kubernetes._async_sync_panel") as mock_sync_panel,
        patch.object(
            hass.config_entries, "async_forward_entry_setups", new_callable=AsyncMock
        ),
    ):
        mock_sync_panel.return_value = None

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_coordinator = MagicMock()
        mock_coordinator.async_config_entry_first_refresh = AsyncMock()
        mock_coordinator_class.return_value = mock_coordinator

        result = await async_setup_entry(hass, mock_config_entry)

        assert result is True
        # Services should not be set up again for second entry
        mock_setup_services.assert_not_called()
        # Panel sync is still called (it handles idempotency internally)
        mock_sync_panel.assert_called_once_with(hass, mock_config_entry)


async def test_async_unload_entry_success(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
):
    """Test successful async_unload_entry."""
    mock_coordinator = MagicMock()
    mock_coordinator.async_stop_watch_tasks = AsyncMock()
    hass.data[DOMAIN] = {mock_config_entry.entry_id: {"coordinator": mock_coordinator}}

    with (
        patch(
            "custom_components.kubernetes.async_unload_services"
        ) as mock_unload_services,
        patch("custom_components.kubernetes.async_remove_panel"),
        patch.object(
            hass.config_entries,
            "async_unload_platforms",
            new_callable=AsyncMock,
            return_value=True,
        ),
    ):
        result = await async_unload_entry(hass, mock_config_entry)

        assert result is True
        # Domain data should be fully cleaned up when last entry is removed
        assert DOMAIN not in hass.data
        mock_unload_services.assert_called_once_with(hass)


async def test_async_unload_entry_removes_panel(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
):
    """Test that panel is removed when last config entry unloads."""
    mock_coordinator = MagicMock()
    mock_coordinator.async_stop_watch_tasks = AsyncMock()
    hass.data[DOMAIN] = {
        mock_config_entry.entry_id: {"coordinator": mock_coordinator},
        "panel_registered": True,
    }

    with (
        patch(
            "custom_components.kubernetes.async_unload_services"
        ) as mock_unload_services,
        patch("custom_components.kubernetes.async_remove_panel") as mock_remove_panel,
        patch.object(
            hass.config_entries,
            "async_unload_platforms",
            new_callable=AsyncMock,
            return_value=True,
        ),
    ):
        result = await async_unload_entry(hass, mock_config_entry)

        assert result is True
        mock_remove_panel.assert_called_once_with(hass, DOMAIN)
        mock_unload_services.assert_called_once_with(hass)


async def test_async_unload_entry_multiple_entries(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
):
    """Test async_unload_entry when multiple entries exist."""
    mock_coordinator = MagicMock()
    mock_coordinator.async_stop_watch_tasks = AsyncMock()
    hass.data[DOMAIN] = {
        mock_config_entry.entry_id: {"coordinator": mock_coordinator},
        "another_entry": {},
    }

    with (
        patch(
            "custom_components.kubernetes.async_unload_services"
        ) as mock_unload_services,
        patch("custom_components.kubernetes.async_remove_panel"),
        patch.object(
            hass.config_entries,
            "async_unload_platforms",
            new_callable=AsyncMock,
            return_value=True,
        ),
    ):
        result = await async_unload_entry(hass, mock_config_entry)

        assert result is True
        assert mock_config_entry.entry_id not in hass.data[DOMAIN]
        assert "another_entry" in hass.data[DOMAIN]
        # Services should not be unloaded when other entries remain
        mock_unload_services.assert_not_called()


async def test_async_unload_entry_platform_unload_fails(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
):
    """Test async_unload_entry when platform unload fails."""
    mock_coordinator = MagicMock()
    mock_coordinator.async_stop_watch_tasks = AsyncMock()
    hass.data[DOMAIN] = {mock_config_entry.entry_id: {"coordinator": mock_coordinator}}

    with (
        patch(
            "custom_components.kubernetes.async_unload_services"
        ) as mock_unload_services,
        patch("custom_components.kubernetes.async_remove_panel"),
        patch.object(
            hass.config_entries,
            "async_unload_platforms",
            new_callable=AsyncMock,
            return_value=False,
        ),
    ):
        result = await async_unload_entry(hass, mock_config_entry)

        assert result is False
        # Data should not be cleaned up if platform unload fails
        assert mock_config_entry.entry_id in hass.data[DOMAIN]
        mock_unload_services.assert_not_called()


def test_constants():
    """Test that constants are properly defined."""
    assert DOMAIN == "kubernetes"
    assert Platform.SENSOR in PLATFORMS
    assert Platform.BINARY_SENSOR in PLATFORMS
    assert Platform.SWITCH in PLATFORMS
    assert len(PLATFORMS) == 3


class TestCountConfigEntries:
    """Tests for _count_config_entries helper."""

    def test_empty_domain(self, hass: HomeAssistant):
        """Test with no domain data."""
        assert _count_config_entries(hass) == 0

    def test_with_entries_only(self, hass: HomeAssistant):
        """Test counting real config entries."""
        hass.data[DOMAIN] = {"entry_1": {}, "entry_2": {}}
        assert _count_config_entries(hass) == 2

    def test_excludes_metadata_keys(self, hass: HomeAssistant):
        """Test metadata keys are excluded from count."""
        hass.data[DOMAIN] = {
            "entry_1": {},
            "panel_registered": True,
            "switch_add_entities": MagicMock(),
        }
        assert _count_config_entries(hass) == 1

    def test_only_metadata_keys(self, hass: HomeAssistant):
        """Test returns 0 when only metadata keys exist."""
        hass.data[DOMAIN] = {
            "panel_registered": True,
        }
        assert _count_config_entries(hass) == 0


class TestPanelRegistration:
    """Tests for _async_register_panel."""

    async def test_panel_registered_successfully(self, hass: HomeAssistant):
        """Test panel is registered when JS file exists."""
        hass.data[DOMAIN] = {}
        hass.http = MagicMock()
        mock_static = AsyncMock()
        hass.http.async_register_static_paths = mock_static

        with (
            patch("custom_components.kubernetes.Path") as mock_path_cls,
            patch(
                "custom_components.kubernetes.async_register_built_in_panel"
            ) as mock_register,
        ):
            mock_panel_dir = MagicMock()
            mock_panel_js = MagicMock()
            mock_panel_js.is_file.return_value = True
            mock_path_cls.return_value.parent.__truediv__ = MagicMock(
                return_value=mock_panel_dir
            )
            mock_panel_dir.__truediv__ = MagicMock(return_value=mock_panel_js)

            await _async_register_panel(hass)

            mock_static.assert_called_once()
            mock_register.assert_called_once()
            assert hass.data[DOMAIN]["panel_registered"] is True

    async def test_panel_not_registered_twice(self, hass: HomeAssistant):
        """Test panel registration is idempotent."""
        hass.data[DOMAIN] = {"panel_registered": True}

        with patch(
            "custom_components.kubernetes.async_register_built_in_panel"
        ) as mock_register:
            await _async_register_panel(hass)
            mock_register.assert_not_called()

    async def test_panel_skipped_when_js_missing(self, hass: HomeAssistant):
        """Test panel registration skipped when JS file not found."""
        hass.data[DOMAIN] = {}

        with (
            patch("custom_components.kubernetes.Path") as mock_path_cls,
            patch(
                "custom_components.kubernetes.async_register_built_in_panel"
            ) as mock_register,
        ):
            mock_panel_dir = MagicMock()
            mock_panel_js = MagicMock()
            mock_panel_js.is_file.return_value = False
            mock_path_cls.return_value.parent.__truediv__ = MagicMock(
                return_value=mock_panel_dir
            )
            mock_panel_dir.__truediv__ = MagicMock(return_value=mock_panel_js)

            await _async_register_panel(hass)

            mock_register.assert_not_called()
            assert hass.data[DOMAIN].get("panel_registered") is not True


class TestAnyEntryWantsPanel:
    """Tests for _any_entry_wants_panel helper."""

    def test_returns_true_when_entry_has_panel_enabled(self, hass: HomeAssistant):
        """Test returns True when an entry has enable_panel=True."""
        coordinator = MagicMock()
        coordinator.config_entry.options = {"enable_panel": True}
        hass.data[DOMAIN] = {
            "entry_1": {"coordinator": coordinator},
        }
        assert _any_entry_wants_panel(hass) is True

    def test_returns_true_with_default_options(self, hass: HomeAssistant):
        """Test returns True when entry has no panel option (defaults to True)."""
        coordinator = MagicMock()
        coordinator.config_entry.options = {}
        hass.data[DOMAIN] = {
            "entry_1": {"coordinator": coordinator},
        }
        assert _any_entry_wants_panel(hass) is True

    def test_returns_false_when_all_disabled(self, hass: HomeAssistant):
        """Test returns False when all entries have enable_panel=False."""
        coordinator = MagicMock()
        coordinator.config_entry.options = {"enable_panel": False}
        hass.data[DOMAIN] = {
            "entry_1": {"coordinator": coordinator},
        }
        assert _any_entry_wants_panel(hass) is False

    def test_excludes_entry_id(self, hass: HomeAssistant):
        """Test excludes the specified entry_id from the check."""
        coordinator = MagicMock()
        coordinator.config_entry.options = {"enable_panel": True}
        hass.data[DOMAIN] = {
            "entry_1": {"coordinator": coordinator},
        }
        assert _any_entry_wants_panel(hass, exclude_entry_id="entry_1") is False

    def test_skips_metadata_keys(self, hass: HomeAssistant):
        """Test skips metadata keys."""
        hass.data[DOMAIN] = {
            "panel_registered": True,
        }
        assert _any_entry_wants_panel(hass) is False

    def test_skips_entries_without_coordinator(self, hass: HomeAssistant):
        """Test skips entries without a coordinator."""
        hass.data[DOMAIN] = {
            "entry_1": {"config": {}},
        }
        assert _any_entry_wants_panel(hass) is False


class TestAsyncRemovePanel:
    """Tests for _async_remove_panel helper."""

    def test_removes_panel_when_registered(self, hass: HomeAssistant):
        """Test removes panel when it was registered."""
        hass.data[DOMAIN] = {"panel_registered": True}
        with patch("custom_components.kubernetes.async_remove_panel") as mock_remove:
            _async_remove_panel(hass)
            mock_remove.assert_called_once_with(hass, DOMAIN)
            assert hass.data[DOMAIN]["panel_registered"] is False

    def test_noop_when_not_registered(self, hass: HomeAssistant):
        """Test does nothing when panel was not registered."""
        hass.data[DOMAIN] = {}
        with patch("custom_components.kubernetes.async_remove_panel") as mock_remove:
            _async_remove_panel(hass)
            mock_remove.assert_not_called()

    def test_noop_when_domain_missing(self, hass: HomeAssistant):
        """Test does nothing when DOMAIN not in hass.data at all."""
        with patch("custom_components.kubernetes.async_remove_panel") as mock_remove:
            _async_remove_panel(hass)
            mock_remove.assert_not_called()


class TestAsyncUpdateOptions:
    """Tests for _async_update_options."""

    async def test_reloads_config_entry(self, hass: HomeAssistant):
        """Test that _async_update_options calls async_reload with entry_id."""
        from custom_components.kubernetes import _async_update_options

        entry = MockConfigEntry(
            domain=DOMAIN,
            entry_id="test_reload_entry",
            data={"host": "test"},
            options={},
        )
        entry.add_to_hass(hass)

        with patch.object(
            hass.config_entries,
            "async_reload",
            new_callable=AsyncMock,
        ) as mock_reload:
            await _async_update_options(hass, entry)
            mock_reload.assert_called_once_with("test_reload_entry")


class TestAsyncSyncPanel:
    """Tests for _async_sync_panel."""

    async def test_registers_panel_when_wanted_and_not_registered(
        self, hass: HomeAssistant
    ):
        """Test panel is registered when wanted but not yet registered."""
        from custom_components.kubernetes import _async_sync_panel

        entry = MockConfigEntry(
            domain=DOMAIN,
            entry_id="test_panel_entry",
            data={"host": "test"},
            options={"enable_panel": True},
        )
        entry.add_to_hass(hass)
        hass.data[DOMAIN] = {}

        with patch(
            "custom_components.kubernetes._async_register_panel", new_callable=AsyncMock
        ) as mock_register:
            await _async_sync_panel(hass, entry)
            mock_register.assert_called_once_with(hass)

    async def test_does_not_register_when_already_registered(self, hass: HomeAssistant):
        """Test panel is not re-registered when already registered."""
        from custom_components.kubernetes import _async_sync_panel

        entry = MockConfigEntry(
            domain=DOMAIN,
            entry_id="test_panel_entry",
            data={"host": "test"},
            options={"enable_panel": True},
        )
        entry.add_to_hass(hass)
        hass.data[DOMAIN] = {"panel_registered": True}

        with patch(
            "custom_components.kubernetes._async_register_panel", new_callable=AsyncMock
        ) as mock_register:
            await _async_sync_panel(hass, entry)
            mock_register.assert_not_called()

    async def test_removes_panel_when_not_wanted_and_registered(
        self, hass: HomeAssistant
    ):
        """Test panel is removed when not wanted but currently registered."""
        from custom_components.kubernetes import _async_sync_panel

        entry = MockConfigEntry(
            domain=DOMAIN,
            entry_id="test_panel_entry",
            data={"host": "test"},
            options={"enable_panel": False},
        )
        entry.add_to_hass(hass)
        hass.data[DOMAIN] = {"panel_registered": True}

        with (
            patch(
                "custom_components.kubernetes._any_entry_wants_panel",
                return_value=False,
            ),
            patch("custom_components.kubernetes._async_remove_panel") as mock_remove,
        ):
            await _async_sync_panel(hass, entry)
            mock_remove.assert_called_once_with(hass)

    async def test_does_not_remove_panel_when_other_entry_wants_it(
        self, hass: HomeAssistant
    ):
        """Test panel is not removed when another entry still wants it."""
        from custom_components.kubernetes import _async_sync_panel

        entry = MockConfigEntry(
            domain=DOMAIN,
            entry_id="test_panel_entry",
            data={"host": "test"},
            options={"enable_panel": False},
        )
        entry.add_to_hass(hass)
        hass.data[DOMAIN] = {"panel_registered": True}

        with (
            patch(
                "custom_components.kubernetes._any_entry_wants_panel", return_value=True
            ),
            patch("custom_components.kubernetes._async_remove_panel") as mock_remove,
        ):
            await _async_sync_panel(hass, entry)
            mock_remove.assert_not_called()

    async def test_noop_when_not_wanted_and_not_registered(self, hass: HomeAssistant):
        """Test nothing happens when panel is neither wanted nor registered."""
        from custom_components.kubernetes import _async_sync_panel

        entry = MockConfigEntry(
            domain=DOMAIN,
            entry_id="test_panel_entry",
            data={"host": "test"},
            options={"enable_panel": False},
        )
        entry.add_to_hass(hass)
        hass.data[DOMAIN] = {}

        with (
            patch(
                "custom_components.kubernetes._async_register_panel",
                new_callable=AsyncMock,
            ) as mock_register,
            patch("custom_components.kubernetes._async_remove_panel") as mock_remove,
        ):
            await _async_sync_panel(hass, entry)
            mock_register.assert_not_called()
            mock_remove.assert_not_called()

    async def test_defaults_to_panel_enabled(self, hass: HomeAssistant):
        """Test that panel defaults to enabled when option not set."""
        from custom_components.kubernetes import _async_sync_panel

        entry = MockConfigEntry(
            domain=DOMAIN,
            entry_id="test_panel_entry",
            data={"host": "test"},
            options={},
        )
        entry.add_to_hass(hass)
        hass.data[DOMAIN] = {}

        with patch(
            "custom_components.kubernetes._async_register_panel", new_callable=AsyncMock
        ) as mock_register:
            await _async_sync_panel(hass, entry)
            mock_register.assert_called_once_with(hass)


class TestAsyncRegisterPanelStaticPathError:
    """Tests for _async_register_panel error handling."""

    async def test_static_path_error_does_not_prevent_registration(
        self, hass: HomeAssistant
    ):
        """Test that a static path registration error is caught and panel still registers."""
        hass.data[DOMAIN] = {}
        hass.http = MagicMock()
        mock_static = AsyncMock(side_effect=RuntimeError("already registered"))
        hass.http.async_register_static_paths = mock_static

        with (
            patch("custom_components.kubernetes.Path") as mock_path_cls,
            patch(
                "custom_components.kubernetes.async_register_built_in_panel"
            ) as mock_register,
        ):
            mock_panel_dir = MagicMock()
            mock_panel_js = MagicMock()
            mock_panel_js.is_file.return_value = True
            mock_path_cls.return_value.parent.__truediv__ = MagicMock(
                return_value=mock_panel_dir
            )
            mock_panel_dir.__truediv__ = MagicMock(return_value=mock_panel_js)

            await _async_register_panel(hass)

            # Static path raised but panel should still be registered
            mock_static.assert_called_once()
            mock_register.assert_called_once()
            assert hass.data[DOMAIN]["panel_registered"] is True


class TestAsyncSetupEntryWatchEnabled:
    """Tests for async_setup_entry with watch tasks enabled."""

    async def test_watch_tasks_started_when_enabled(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ):
        """Test that watch tasks are started when enable_watch is True."""
        hass.config_entries.async_update_entry(
            mock_config_entry, options={"enable_watch": True}
        )

        with (
            patch("custom_components.kubernetes.kubernetes_client.k8s_client"),
            patch("custom_components.kubernetes.KubernetesClient") as mock_client_class,
            patch(
                "custom_components.kubernetes.KubernetesDataCoordinator"
            ) as mock_coordinator_class,
            patch(
                "custom_components.kubernetes.async_setup_services",
                new_callable=AsyncMock,
            ),
            patch(
                "custom_components.kubernetes._async_sync_panel", new_callable=AsyncMock
            ),
            patch.object(
                hass.config_entries,
                "async_forward_entry_setups",
                new_callable=AsyncMock,
            ),
        ):
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client

            mock_coordinator = MagicMock()
            mock_coordinator.async_config_entry_first_refresh = AsyncMock()
            mock_coordinator.async_start_watch_tasks = AsyncMock()
            mock_coordinator_class.return_value = mock_coordinator

            result = await async_setup_entry(hass, mock_config_entry)

            assert result is True
            mock_coordinator.async_start_watch_tasks.assert_called_once()

    async def test_watch_tasks_not_started_when_disabled(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ):
        """Test that watch tasks are not started when enable_watch is False."""
        hass.config_entries.async_update_entry(
            mock_config_entry, options={"enable_watch": False}
        )

        with (
            patch("custom_components.kubernetes.kubernetes_client.k8s_client"),
            patch("custom_components.kubernetes.KubernetesClient") as mock_client_class,
            patch(
                "custom_components.kubernetes.KubernetesDataCoordinator"
            ) as mock_coordinator_class,
            patch(
                "custom_components.kubernetes.async_setup_services",
                new_callable=AsyncMock,
            ),
            patch(
                "custom_components.kubernetes._async_sync_panel", new_callable=AsyncMock
            ),
            patch.object(
                hass.config_entries,
                "async_forward_entry_setups",
                new_callable=AsyncMock,
            ),
        ):
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client

            mock_coordinator = MagicMock()
            mock_coordinator.async_config_entry_first_refresh = AsyncMock()
            mock_coordinator.async_start_watch_tasks = AsyncMock()
            mock_coordinator_class.return_value = mock_coordinator

            result = await async_setup_entry(hass, mock_config_entry)

            assert result is True
            mock_coordinator.async_start_watch_tasks.assert_not_called()

    async def test_watch_tasks_not_started_by_default(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ):
        """Test that watch tasks default to disabled (DEFAULT_ENABLE_WATCH=False)."""
        # mock_config_entry has options={}, so enable_watch defaults to False
        with (
            patch("custom_components.kubernetes.kubernetes_client.k8s_client"),
            patch("custom_components.kubernetes.KubernetesClient") as mock_client_class,
            patch(
                "custom_components.kubernetes.KubernetesDataCoordinator"
            ) as mock_coordinator_class,
            patch(
                "custom_components.kubernetes.async_setup_services",
                new_callable=AsyncMock,
            ),
            patch(
                "custom_components.kubernetes._async_sync_panel", new_callable=AsyncMock
            ),
            patch.object(
                hass.config_entries,
                "async_forward_entry_setups",
                new_callable=AsyncMock,
            ),
        ):
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client

            mock_coordinator = MagicMock()
            mock_coordinator.async_config_entry_first_refresh = AsyncMock()
            mock_coordinator.async_start_watch_tasks = AsyncMock()
            mock_coordinator_class.return_value = mock_coordinator

            result = await async_setup_entry(hass, mock_config_entry)

            assert result is True
            mock_coordinator.async_start_watch_tasks.assert_not_called()


class TestAsyncUnloadEntryWatchCleanup:
    """Tests for async_unload_entry watch task cleanup."""

    async def test_watch_tasks_stopped_on_unload(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ):
        """Test that watch tasks are stopped during unload."""
        mock_coordinator = MagicMock()
        mock_coordinator.async_stop_watch_tasks = AsyncMock()
        hass.data[DOMAIN] = {
            mock_config_entry.entry_id: {"coordinator": mock_coordinator}
        }

        with (
            patch(
                "custom_components.kubernetes.async_unload_services",
                new_callable=AsyncMock,
            ),
            patch("custom_components.kubernetes.async_remove_panel"),
            patch.object(
                hass.config_entries,
                "async_unload_platforms",
                new_callable=AsyncMock,
                return_value=True,
            ),
        ):
            result = await async_unload_entry(hass, mock_config_entry)

            assert result is True
            mock_coordinator.async_stop_watch_tasks.assert_called_once()

    async def test_watch_tasks_stopped_even_when_platform_unload_fails(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ):
        """Test that watch tasks are always stopped, even if platform unload fails."""
        mock_coordinator = MagicMock()
        mock_coordinator.async_stop_watch_tasks = AsyncMock()
        hass.data[DOMAIN] = {
            mock_config_entry.entry_id: {"coordinator": mock_coordinator}
        }

        with (
            patch(
                "custom_components.kubernetes.async_unload_services",
                new_callable=AsyncMock,
            ),
            patch("custom_components.kubernetes.async_remove_panel"),
            patch.object(
                hass.config_entries,
                "async_unload_platforms",
                new_callable=AsyncMock,
                return_value=False,
            ),
        ):
            result = await async_unload_entry(hass, mock_config_entry)

            assert result is False
            # Watch tasks should still be stopped regardless
            mock_coordinator.async_stop_watch_tasks.assert_called_once()


class TestAsyncUnloadEntryPanelRemovalWithRemainingEntries:
    """Tests for panel removal logic when other entries remain."""

    async def test_panel_removed_when_no_remaining_entry_wants_it(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ):
        """Test panel is removed when remaining entries don't want it."""
        mock_coordinator = MagicMock()
        mock_coordinator.async_stop_watch_tasks = AsyncMock()

        # Another entry exists that does not want the panel
        other_coordinator = MagicMock()
        other_coordinator.config_entry.options = {"enable_panel": False}

        hass.data[DOMAIN] = {
            mock_config_entry.entry_id: {"coordinator": mock_coordinator},
            "other_entry": {"coordinator": other_coordinator},
            "panel_registered": True,
        }

        with (
            patch(
                "custom_components.kubernetes.async_unload_services",
                new_callable=AsyncMock,
            ),
            patch(
                "custom_components.kubernetes.async_remove_panel"
            ) as mock_remove_panel,
            patch.object(
                hass.config_entries,
                "async_unload_platforms",
                new_callable=AsyncMock,
                return_value=True,
            ),
        ):
            result = await async_unload_entry(hass, mock_config_entry)

            assert result is True
            # Panel should be removed since the remaining entry doesn't want it
            mock_remove_panel.assert_called_once_with(hass, DOMAIN)

    async def test_panel_not_removed_when_remaining_entry_wants_it(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ):
        """Test panel is kept when a remaining entry still wants it."""
        mock_coordinator = MagicMock()
        mock_coordinator.async_stop_watch_tasks = AsyncMock()

        # Another entry exists that wants the panel
        other_coordinator = MagicMock()
        other_coordinator.config_entry.options = {"enable_panel": True}

        hass.data[DOMAIN] = {
            mock_config_entry.entry_id: {"coordinator": mock_coordinator},
            "other_entry": {"coordinator": other_coordinator},
            "panel_registered": True,
        }

        with (
            patch(
                "custom_components.kubernetes.async_unload_services",
                new_callable=AsyncMock,
            ),
            patch(
                "custom_components.kubernetes.async_remove_panel"
            ) as mock_remove_panel,
            patch.object(
                hass.config_entries,
                "async_unload_platforms",
                new_callable=AsyncMock,
                return_value=True,
            ),
        ):
            result = await async_unload_entry(hass, mock_config_entry)

            assert result is True
            # Panel should NOT be removed since other entry wants it
            mock_remove_panel.assert_not_called()


class TestAsyncSetupEntryUpdateListener:
    """Tests for the options update listener registration."""

    async def test_update_listener_registered(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ):
        """Test that an update listener is registered during setup."""
        with (
            patch("custom_components.kubernetes.kubernetes_client.k8s_client"),
            patch("custom_components.kubernetes.KubernetesClient") as mock_client_class,
            patch(
                "custom_components.kubernetes.KubernetesDataCoordinator"
            ) as mock_coordinator_class,
            patch(
                "custom_components.kubernetes.async_setup_services",
                new_callable=AsyncMock,
            ),
            patch(
                "custom_components.kubernetes._async_sync_panel", new_callable=AsyncMock
            ),
            patch.object(
                hass.config_entries,
                "async_forward_entry_setups",
                new_callable=AsyncMock,
            ),
        ):
            mock_client_class.return_value = MagicMock()

            mock_coordinator = MagicMock()
            mock_coordinator.async_config_entry_first_refresh = AsyncMock()
            mock_coordinator_class.return_value = mock_coordinator

            result = await async_setup_entry(hass, mock_config_entry)
            assert result is True

            # Verify that the entry has update listeners registered
            assert len(mock_config_entry.update_listeners) > 0
