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


from homeassistant.core import HomeAssistant
import pytest

from custom_components.kubernetes import (
    DOMAIN,
    PLATFORMS,
    async_setup,
    async_setup_entry,
    async_unload_entry,
)


@pytest.fixture
def mock_hass():
    """Mock Home Assistant instance."""
    hass = MagicMock(spec=HomeAssistant)
    hass.data = {}
    hass.config_entries = MagicMock()
    hass.config_entries.async_forward_entry_setups = AsyncMock(return_value=True)
    hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)
    hass.services = MagicMock()
    hass.services.async_register = AsyncMock()
    hass.services.async_remove = AsyncMock()
    hass.state = MagicMock()
    return hass


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
    entry.state = MagicMock()
    return entry


async def test_async_setup():
    """Test async_setup function."""
    result = await async_setup(MagicMock(), {})
    assert result is True


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
        patch("homeassistant.helpers.frame.report_usage"),
    ):
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
        patch("homeassistant.helpers.frame.report_usage"),
    ):
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


async def test_async_unload_entry_success(mock_hass, mock_config_entry):
    """Test successful async_unload_entry."""
    # Set up data structure
    mock_hass.data[DOMAIN] = {mock_config_entry.entry_id: {}}

    with patch(
        "custom_components.kubernetes.async_unload_services"
    ) as mock_unload_services:
        result = await async_unload_entry(mock_hass, mock_config_entry)

        assert result is True
        assert mock_config_entry.entry_id not in mock_hass.data[DOMAIN]
        # Services should be unloaded when last entry is removed
        mock_unload_services.assert_called_once_with(mock_hass)


async def test_async_unload_entry_multiple_entries(mock_hass, mock_config_entry):
    """Test async_unload_entry when multiple entries exist."""
    # Set up data structure with multiple entries
    mock_hass.data[DOMAIN] = {
        mock_config_entry.entry_id: {},
        "another_entry": {},
    }

    with patch(
        "custom_components.kubernetes.async_unload_services"
    ) as mock_unload_services:
        result = await async_unload_entry(mock_hass, mock_config_entry)

        assert result is True
        assert mock_config_entry.entry_id not in mock_hass.data[DOMAIN]
        assert "another_entry" in mock_hass.data[DOMAIN]
        # Services should not be unloaded when other entries remain
        mock_unload_services.assert_not_called()


async def test_async_unload_entry_platform_unload_fails(mock_hass, mock_config_entry):
    """Test async_unload_entry when platform unload fails."""
    # Set up data structure
    mock_hass.data[DOMAIN] = {mock_config_entry.entry_id: {}}

    # Mock platform unload to fail
    mock_hass.config_entries.async_unload_platforms.return_value = False

    with patch(
        "custom_components.kubernetes.async_unload_services"
    ) as mock_unload_services:
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
