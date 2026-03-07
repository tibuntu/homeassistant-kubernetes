"""Tests for the Kubernetes integration __init__.py module."""

from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.config_entries import ConfigEntry

try:
    from homeassistant.const import Platform
except ImportError:
    # Fallback for older HomeAssistant versions
    from enum import Enum

    class Platform(Enum):
        SENSOR = "sensor"
        BINARY_SENSOR = "binary_sensor"
        SWITCH = "switch"


import pytest

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
def mock_config_entry():
    """Mock config entry."""
    entry = MagicMock(spec=ConfigEntry)
    entry.entry_id = "test_entry_id"
    entry.data = {
        "host": "test-cluster.example.com",
        "port": 6443,
        "api_token": "test-token",
        "namespace": "default",
        "verify_ssl": True,
    }
    entry.options = {}
    entry.state = MagicMock()
    return entry


async def test_async_setup():
    """Test async_setup function."""
    hass = MagicMock()
    with patch(
        "custom_components.kubernetes.async_register_websocket_commands"
    ) as mock_ws:
        result = await async_setup(hass, {})
        assert result is True
        mock_ws.assert_called_once_with(hass)


async def test_async_setup_entry_success(mock_hass, mock_config_entry):
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
        patch("homeassistant.helpers.frame.report_usage"),
    ):
        mock_sync_panel.return_value = None

        # Mock the client and coordinator
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_coordinator = MagicMock()
        mock_coordinator.async_config_entry_first_refresh = AsyncMock()
        mock_coordinator_class.return_value = mock_coordinator

        result = await async_setup_entry(mock_hass, mock_config_entry)

        assert result is True
        assert DOMAIN in mock_hass.data
        assert mock_config_entry.entry_id in mock_hass.data[DOMAIN]
        assert (
            mock_hass.data[DOMAIN][mock_config_entry.entry_id]["config"]
            == mock_config_entry.data
        )
        assert (
            mock_hass.data[DOMAIN][mock_config_entry.entry_id]["client"] == mock_client
        )
        assert (
            mock_hass.data[DOMAIN][mock_config_entry.entry_id]["coordinator"]
            == mock_coordinator
        )

        # Verify services were set up for first entry
        mock_setup_services.assert_called_once_with(mock_hass)

        # Verify panel sync was called
        mock_sync_panel.assert_called_once_with(mock_hass, mock_config_entry)

        # Verify coordinator was started
        mock_coordinator.async_config_entry_first_refresh.assert_called_once()

        # Verify platforms were set up
        mock_hass.config_entries.async_forward_entry_setups.assert_called_once_with(
            mock_config_entry, PLATFORMS
        )


async def test_async_setup_entry_kubernetes_not_available(mock_hass, mock_config_entry):
    """Test async_setup_entry when kubernetes package is not available."""
    import builtins

    # Mock the import to raise an ImportError
    original_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if name == "kubernetes.client":
            raise ImportError("No module named 'kubernetes'")
        return original_import(name, *args, **kwargs)

    with (
        patch.object(builtins, "__import__", side_effect=mock_import),
        patch("homeassistant.helpers.frame.report_usage"),
    ):
        result = await async_setup_entry(mock_hass, mock_config_entry)

        assert result is False
        # The domain is added to hass.data at the beginning, but no entry data should be added
        assert mock_config_entry.entry_id not in mock_hass.data.get(DOMAIN, {})


async def test_async_setup_entry_second_entry(mock_hass, mock_config_entry):
    """Test async_setup_entry for second config entry (should not set up services again)."""
    # Set up first entry
    mock_hass.data[DOMAIN] = {"existing_entry": {}}

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
        patch("homeassistant.helpers.frame.report_usage"),
    ):
        mock_sync_panel.return_value = None

        # Mock the client and coordinator
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_coordinator = MagicMock()
        mock_coordinator.async_config_entry_first_refresh = AsyncMock()
        mock_coordinator_class.return_value = mock_coordinator

        result = await async_setup_entry(mock_hass, mock_config_entry)

        assert result is True
        # Services should not be set up again for second entry
        mock_setup_services.assert_not_called()
        # Panel sync is still called (it handles idempotency internally)
        mock_sync_panel.assert_called_once_with(mock_hass, mock_config_entry)


async def test_async_unload_entry_success(mock_hass, mock_config_entry):
    """Test successful async_unload_entry."""
    # Set up data structure with coordinator for watch task cleanup
    mock_coordinator = MagicMock()
    mock_coordinator.async_stop_watch_tasks = AsyncMock()
    mock_hass.data[DOMAIN] = {
        mock_config_entry.entry_id: {"coordinator": mock_coordinator}
    }

    with (
        patch(
            "custom_components.kubernetes.async_unload_services"
        ) as mock_unload_services,
        patch("custom_components.kubernetes.async_remove_panel"),
    ):
        result = await async_unload_entry(mock_hass, mock_config_entry)

        assert result is True
        # Domain data should be fully cleaned up when last entry is removed
        assert DOMAIN not in mock_hass.data
        mock_unload_services.assert_called_once_with(mock_hass)


async def test_async_unload_entry_removes_panel(mock_hass, mock_config_entry):
    """Test that panel is removed when last config entry unloads."""
    mock_coordinator = MagicMock()
    mock_coordinator.async_stop_watch_tasks = AsyncMock()
    mock_hass.data[DOMAIN] = {
        mock_config_entry.entry_id: {"coordinator": mock_coordinator},
        "panel_registered": True,
    }

    with (
        patch(
            "custom_components.kubernetes.async_unload_services"
        ) as mock_unload_services,
        patch("custom_components.kubernetes.async_remove_panel") as mock_remove_panel,
    ):
        result = await async_unload_entry(mock_hass, mock_config_entry)

        assert result is True
        # _async_remove_panel calls async_remove_panel internally
        mock_remove_panel.assert_called_once_with(mock_hass, DOMAIN)
        mock_unload_services.assert_called_once_with(mock_hass)


async def test_async_unload_entry_multiple_entries(mock_hass, mock_config_entry):
    """Test async_unload_entry when multiple entries exist."""
    # Set up data structure with multiple entries (coordinator needed for watch task cleanup)
    mock_coordinator = MagicMock()
    mock_coordinator.async_stop_watch_tasks = AsyncMock()
    mock_hass.data[DOMAIN] = {
        mock_config_entry.entry_id: {"coordinator": mock_coordinator},
        "another_entry": {},
    }

    with (
        patch(
            "custom_components.kubernetes.async_unload_services"
        ) as mock_unload_services,
        patch("custom_components.kubernetes.async_remove_panel"),
    ):
        result = await async_unload_entry(mock_hass, mock_config_entry)

        assert result is True
        assert mock_config_entry.entry_id not in mock_hass.data[DOMAIN]
        assert "another_entry" in mock_hass.data[DOMAIN]
        # Services should not be unloaded when other entries remain
        mock_unload_services.assert_not_called()


async def test_async_unload_entry_platform_unload_fails(mock_hass, mock_config_entry):
    """Test async_unload_entry when platform unload fails."""
    # Set up data structure with coordinator for watch task cleanup
    mock_coordinator = MagicMock()
    mock_coordinator.async_stop_watch_tasks = AsyncMock()
    mock_hass.data[DOMAIN] = {
        mock_config_entry.entry_id: {"coordinator": mock_coordinator}
    }

    # Mock platform unload to fail
    mock_hass.config_entries.async_unload_platforms.return_value = False

    with (
        patch(
            "custom_components.kubernetes.async_unload_services"
        ) as mock_unload_services,
        patch("custom_components.kubernetes.async_remove_panel"),
    ):
        result = await async_unload_entry(mock_hass, mock_config_entry)

        assert result is False
        # Data should not be cleaned up if platform unload fails
        assert mock_config_entry.entry_id in mock_hass.data[DOMAIN]
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

    def test_empty_domain(self, mock_hass):
        """Test with no domain data."""
        assert _count_config_entries(mock_hass) == 0

    def test_with_entries_only(self, mock_hass):
        """Test counting real config entries."""
        mock_hass.data[DOMAIN] = {"entry_1": {}, "entry_2": {}}
        assert _count_config_entries(mock_hass) == 2

    def test_excludes_metadata_keys(self, mock_hass):
        """Test metadata keys are excluded from count."""
        mock_hass.data[DOMAIN] = {
            "entry_1": {},
            "panel_registered": True,
            "switch_add_entities": MagicMock(),
        }
        assert _count_config_entries(mock_hass) == 1

    def test_only_metadata_keys(self, mock_hass):
        """Test returns 0 when only metadata keys exist."""
        mock_hass.data[DOMAIN] = {
            "panel_registered": True,
        }
        assert _count_config_entries(mock_hass) == 0


class TestPanelRegistration:
    """Tests for _async_register_panel."""

    async def test_panel_registered_successfully(self, mock_hass):
        """Test panel is registered when JS file exists."""
        mock_hass.data[DOMAIN] = {}

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

            await _async_register_panel(mock_hass)

            mock_hass.http.async_register_static_paths.assert_called_once()
            mock_register.assert_called_once()
            assert mock_hass.data[DOMAIN]["panel_registered"] is True

    async def test_panel_not_registered_twice(self, mock_hass):
        """Test panel registration is idempotent."""
        mock_hass.data[DOMAIN] = {"panel_registered": True}

        with patch(
            "custom_components.kubernetes.async_register_built_in_panel"
        ) as mock_register:
            await _async_register_panel(mock_hass)
            mock_register.assert_not_called()

    async def test_panel_skipped_when_js_missing(self, mock_hass):
        """Test panel registration skipped when JS file not found."""
        mock_hass.data[DOMAIN] = {}

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

            await _async_register_panel(mock_hass)

            mock_register.assert_not_called()
            assert mock_hass.data[DOMAIN].get("panel_registered") is not True


class TestAnyEntryWantsPanel:
    """Tests for _any_entry_wants_panel helper."""

    def test_returns_true_when_entry_has_panel_enabled(self, mock_hass):
        """Test returns True when an entry has enable_panel=True."""
        coordinator = MagicMock()
        coordinator.config_entry.options = {"enable_panel": True}
        mock_hass.data[DOMAIN] = {
            "entry_1": {"coordinator": coordinator},
        }
        assert _any_entry_wants_panel(mock_hass) is True

    def test_returns_true_with_default_options(self, mock_hass):
        """Test returns True when entry has no panel option (defaults to True)."""
        coordinator = MagicMock()
        coordinator.config_entry.options = {}
        mock_hass.data[DOMAIN] = {
            "entry_1": {"coordinator": coordinator},
        }
        assert _any_entry_wants_panel(mock_hass) is True

    def test_returns_false_when_all_disabled(self, mock_hass):
        """Test returns False when all entries have enable_panel=False."""
        coordinator = MagicMock()
        coordinator.config_entry.options = {"enable_panel": False}
        mock_hass.data[DOMAIN] = {
            "entry_1": {"coordinator": coordinator},
        }
        assert _any_entry_wants_panel(mock_hass) is False

    def test_excludes_entry_id(self, mock_hass):
        """Test excludes the specified entry_id from the check."""
        coordinator = MagicMock()
        coordinator.config_entry.options = {"enable_panel": True}
        mock_hass.data[DOMAIN] = {
            "entry_1": {"coordinator": coordinator},
        }
        assert _any_entry_wants_panel(mock_hass, exclude_entry_id="entry_1") is False

    def test_skips_metadata_keys(self, mock_hass):
        """Test skips metadata keys."""
        mock_hass.data[DOMAIN] = {
            "panel_registered": True,
        }
        assert _any_entry_wants_panel(mock_hass) is False

    def test_skips_entries_without_coordinator(self, mock_hass):
        """Test skips entries without a coordinator."""
        mock_hass.data[DOMAIN] = {
            "entry_1": {"config": {}},
        }
        assert _any_entry_wants_panel(mock_hass) is False


class TestAsyncRemovePanel:
    """Tests for _async_remove_panel helper."""

    def test_removes_panel_when_registered(self, mock_hass):
        """Test removes panel when it was registered."""
        mock_hass.data[DOMAIN] = {"panel_registered": True}
        with patch("custom_components.kubernetes.async_remove_panel") as mock_remove:
            _async_remove_panel(mock_hass)
            mock_remove.assert_called_once_with(mock_hass, DOMAIN)
            assert mock_hass.data[DOMAIN]["panel_registered"] is False

    def test_noop_when_not_registered(self, mock_hass):
        """Test does nothing when panel was not registered."""
        mock_hass.data[DOMAIN] = {}
        with patch("custom_components.kubernetes.async_remove_panel") as mock_remove:
            _async_remove_panel(mock_hass)
            mock_remove.assert_not_called()
