"""Tests for the Kubernetes switch platform."""

import time
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry
import pytest

from custom_components.kubernetes.const import (
    ATTR_NAMESPACE,
    ATTR_WORKLOAD_TYPE,
    DOMAIN,
    WORKLOAD_TYPE_CRONJOB,
)
from custom_components.kubernetes.switch import KubernetesCronJobSwitch


@pytest.fixture
def mock_hass():
    """Mock Home Assistant instance."""
    return MagicMock(spec=HomeAssistant)


@pytest.fixture
def mock_config_entry():
    """Mock config entry."""
    entry = MagicMock(spec=ConfigEntry)
    entry.entry_id = "test-entry-id"
    entry.data = {
        CONF_NAME: "Test Cluster",
        "host": "test-cluster.example.com",
        "port": 6443,
        "api_token": "test-token",
        "namespace": "default",
        "verify_ssl": True,
    }
    return entry


@pytest.fixture
def mock_coordinator():
    """Mock coordinator."""
    coordinator = MagicMock()
    coordinator.last_update_success = True
    coordinator.data = {
        "cronjobs": {
            "test-cronjob": {
                "name": "test-cronjob",
                "namespace": "default",
                "schedule": "0 2 * * *",
                "suspend": False,
                "active_jobs_count": 0,
                "last_schedule_time": None,
                "next_schedule_time": None,
            }
        }
    }
    return coordinator


@pytest.fixture
def mock_client():
    """Mock Kubernetes client."""
    client = MagicMock()
    client.suspend_cronjob = AsyncMock(return_value={"success": True})
    client.resume_cronjob = AsyncMock(return_value={"success": True})
    return client


@pytest.fixture
def cronjob_switch(mock_hass, mock_config_entry, mock_coordinator):
    """Create a CronJob switch instance."""
    return KubernetesCronJobSwitch(
        mock_coordinator, mock_config_entry, "test-cronjob", "default"
    )


class TestKubernetesCronJobSwitch:
    """Test Kubernetes CronJob switch."""

    def test_initialization(self, cronjob_switch):
        """Test switch initialization."""
        assert cronjob_switch.cronjob_name == "test-cronjob"
        assert cronjob_switch.namespace == "default"
        assert cronjob_switch._attr_name == "test-cronjob"
        assert (
            cronjob_switch._attr_unique_id
            == "test-entry-id_default_test-cronjob_cronjob"
        )
        assert cronjob_switch._attr_icon == "mdi:clock-outline"
        assert cronjob_switch._is_on is False
        assert cronjob_switch._suspend is False

    def test_available(self, cronjob_switch, mock_coordinator):
        """Test switch availability."""
        # Test when coordinator is successful
        mock_coordinator.last_update_success = True
        assert cronjob_switch.available is True

        # Test when coordinator fails
        mock_coordinator.last_update_success = False
        assert cronjob_switch.available is False

    def test_is_on_when_enabled(self, cronjob_switch):
        """Test is_on when CronJob is enabled (not suspended)."""
        cronjob_switch._suspend = False
        cronjob_switch._is_on = True
        assert cronjob_switch.is_on is True

    def test_is_on_when_suspended(self, cronjob_switch):
        """Test is_on when CronJob is suspended."""
        cronjob_switch._suspend = True
        cronjob_switch._is_on = False
        assert cronjob_switch.is_on is False

    def test_extra_state_attributes(self, cronjob_switch):
        """Test extra state attributes."""
        cronjob_switch._schedule = "0 2 * * *"
        cronjob_switch._suspend = False
        cronjob_switch._active_jobs_count = 1
        cronjob_switch._last_schedule_time = "2023-01-01T02:00:00Z"
        cronjob_switch._next_schedule_time = "2023-01-02T02:00:00Z"
        cronjob_switch._last_suspend_time = 1234567890.0
        cronjob_switch._last_resume_time = 1234567891.0

        attributes = cronjob_switch.extra_state_attributes

        assert attributes["namespace"] == "default"
        assert attributes["schedule"] == "0 2 * * *"
        assert attributes["suspend"] is False
        assert attributes["suspended"] is False
        assert attributes["active_jobs_count"] == 1
        assert attributes["last_schedule_time"] == "2023-01-01T02:00:00Z"
        assert attributes["next_schedule_time"] == "2023-01-02T02:00:00Z"
        assert attributes["last_suspend_time"] == 1234567890.0
        assert attributes["last_resume_time"] == 1234567891.0
        assert attributes[ATTR_WORKLOAD_TYPE] == WORKLOAD_TYPE_CRONJOB

    async def test_async_turn_on_success(
        self, cronjob_switch, mock_hass, mock_config_entry, mock_client
    ):
        """Test successful turn on (resume CronJob)."""
        # Setup
        cronjob_switch.hass = mock_hass
        cronjob_switch.config_entry = mock_config_entry
        mock_hass.data = {DOMAIN: {mock_config_entry.entry_id: {"client": mock_client}}}
        cronjob_switch._is_on = False
        cronjob_switch._suspend = True

        # Execute
        await cronjob_switch.async_turn_on()

        # Verify
        mock_client.resume_cronjob.assert_called_once_with("test-cronjob", "default")
        assert cronjob_switch._is_on is True
        assert cronjob_switch._suspend is False
        assert cronjob_switch._last_resume_time is not None

    async def test_async_turn_on_failure(
        self, cronjob_switch, mock_hass, mock_config_entry, mock_client
    ):
        """Test failed turn on (resume CronJob)."""
        # Setup
        cronjob_switch.hass = mock_hass
        cronjob_switch.config_entry = mock_config_entry
        mock_hass.data = {DOMAIN: {mock_config_entry.entry_id: {"client": mock_client}}}
        mock_client.resume_cronjob.return_value = {
            "success": False,
            "error": "Permission denied",
        }
        cronjob_switch._is_on = False
        cronjob_switch._suspend = True

        # Execute and verify exception
        with pytest.raises(Exception, match="Permission denied"):
            await cronjob_switch.async_turn_on()

        # Verify state unchanged
        assert cronjob_switch._is_on is False
        assert cronjob_switch._suspend is True

    async def test_async_turn_off_success(
        self, cronjob_switch, mock_hass, mock_config_entry, mock_client
    ):
        """Test successful turn off (suspend CronJob)."""
        # Setup
        cronjob_switch.hass = mock_hass
        cronjob_switch.config_entry = mock_config_entry
        mock_hass.data = {DOMAIN: {mock_config_entry.entry_id: {"client": mock_client}}}
        cronjob_switch._is_on = True
        cronjob_switch._suspend = False

        # Execute
        await cronjob_switch.async_turn_off()

        # Verify
        mock_client.suspend_cronjob.assert_called_once_with("test-cronjob", "default")
        assert cronjob_switch._is_on is False
        assert cronjob_switch._suspend is True
        assert cronjob_switch._last_suspend_time is not None

    async def test_async_turn_off_failure(
        self, cronjob_switch, mock_hass, mock_config_entry, mock_client
    ):
        """Test failed turn off (suspend CronJob)."""
        # Setup
        cronjob_switch.hass = mock_hass
        cronjob_switch.config_entry = mock_config_entry
        mock_hass.data = {DOMAIN: {mock_config_entry.entry_id: {"client": mock_client}}}
        mock_client.suspend_cronjob.return_value = {
            "success": False,
            "error": "CronJob not found",
        }
        cronjob_switch._is_on = True
        cronjob_switch._suspend = False

        # Execute and verify exception
        with pytest.raises(Exception, match="CronJob not found"):
            await cronjob_switch.async_turn_off()

        # Verify state unchanged
        assert cronjob_switch._is_on is True
        assert cronjob_switch._suspend is False

    async def test_async_update_enabled_cronjob(self, cronjob_switch, mock_coordinator):
        """Test async_update with enabled CronJob."""
        # Setup coordinator data for enabled CronJob
        mock_coordinator.data = {
            "cronjobs": {
                "test-cronjob": {
                    "name": "test-cronjob",
                    "namespace": "default",
                    "schedule": "0 2 * * *",
                    "suspend": False,
                    "active_jobs_count": 2,
                    "last_schedule_time": "2023-01-01T02:00:00Z",
                    "next_schedule_time": "2023-01-02T02:00:00Z",
                }
            }
        }

        # Mock the get_cronjob_data method
        mock_coordinator.get_cronjob_data = MagicMock(
            return_value=mock_coordinator.data["cronjobs"]["test-cronjob"]
        )

        # Execute
        await cronjob_switch.async_update()

        # Verify
        assert cronjob_switch._is_on is True
        assert cronjob_switch._suspend is False
        assert cronjob_switch._active_jobs_count == 2
        assert cronjob_switch._schedule == "0 2 * * *"
        assert cronjob_switch._last_schedule_time == "2023-01-01T02:00:00Z"
        assert cronjob_switch._next_schedule_time == "2023-01-02T02:00:00Z"

    async def test_async_update_suspended_cronjob(
        self, cronjob_switch, mock_coordinator
    ):
        """Test async_update with suspended CronJob."""
        # Setup coordinator data for suspended CronJob
        mock_coordinator.data = {
            "cronjobs": {
                "test-cronjob": {
                    "name": "test-cronjob",
                    "namespace": "default",
                    "schedule": "0 2 * * *",
                    "suspend": True,
                    "active_jobs_count": 0,
                    "last_schedule_time": None,
                    "next_schedule_time": None,
                }
            }
        }

        # Mock the get_cronjob_data method
        mock_coordinator.get_cronjob_data = MagicMock(
            return_value=mock_coordinator.data["cronjobs"]["test-cronjob"]
        )

        # Execute
        await cronjob_switch.async_update()

        # Verify
        assert cronjob_switch._is_on is False
        assert cronjob_switch._suspend is True
        assert cronjob_switch._active_jobs_count == 0

    async def test_async_update_cronjob_not_found(
        self, cronjob_switch, mock_coordinator
    ):
        """Test async_update when CronJob is not found in coordinator data."""
        # Setup empty coordinator data
        mock_coordinator.data = {"cronjobs": {}}

        # Mock the get_cronjob_data method to return None
        mock_coordinator.get_cronjob_data = MagicMock(return_value=None)

        # Execute
        await cronjob_switch.async_update()

        # Verify - should not raise exception and should log warning
        # State should remain unchanged

    async def test_async_update_with_string_suspend_value(
        self, cronjob_switch, mock_coordinator
    ):
        """Test async_update with string suspend value."""
        # Setup coordinator data with string suspend value
        mock_coordinator.data = {
            "cronjobs": {
                "test-cronjob": {
                    "name": "test-cronjob",
                    "namespace": "default",
                    "schedule": "0 2 * * *",
                    "suspend": "true",  # String value
                    "active_jobs_count": 0,
                    "last_schedule_time": None,
                    "next_schedule_time": None,
                }
            }
        }

        # Mock the get_cronjob_data method
        mock_coordinator.get_cronjob_data = MagicMock(
            return_value=mock_coordinator.data["cronjobs"]["test-cronjob"]
        )

        # Execute
        await cronjob_switch.async_update()

        # Verify
        assert cronjob_switch._is_on is False
        assert cronjob_switch._suspend is True

    async def test_async_update_with_none_suspend_value(
        self, cronjob_switch, mock_coordinator
    ):
        """Test async_update with None suspend value."""
        # Setup coordinator data with None suspend value
        mock_coordinator.data = {
            "cronjobs": {
                "test-cronjob": {
                    "name": "test-cronjob",
                    "namespace": "default",
                    "schedule": "0 2 * * *",
                    "suspend": None,  # None value
                    "active_jobs_count": 0,
                    "last_schedule_time": None,
                    "next_schedule_time": None,
                }
            }
        }

        # Mock the get_cronjob_data method
        mock_coordinator.get_cronjob_data = MagicMock(
            return_value=mock_coordinator.data["cronjobs"]["test-cronjob"]
        )

        # Execute
        await cronjob_switch.async_update()

        # Verify
        assert cronjob_switch._is_on is True
        assert cronjob_switch._suspend is False

    async def test_async_added_to_hass(self, cronjob_switch, mock_coordinator):
        """Test async_added_to_hass."""
        # Setup
        cronjob_switch.hass = MagicMock()
        cronjob_switch.async_on_remove = MagicMock()

        # Execute
        await cronjob_switch.async_added_to_hass()

        # Verify
        cronjob_switch.async_on_remove.assert_called_once()

    @callback
    def test_handle_coordinator_update(self, cronjob_switch):
        """Test _handle_coordinator_update callback."""
        # Setup
        cronjob_switch.async_write_ha_state = MagicMock()

        # Execute
        cronjob_switch._handle_coordinator_update()

        # Verify
        cronjob_switch.async_write_ha_state.assert_called_once()

    async def test_switch_available_when_coordinator_last_update_success_is_true(
        self, mock_coordinator, mock_config_entry
    ):
        """Test switch available property when coordinator last_update_success is True."""
        switch = KubernetesCronJobSwitch(
            mock_coordinator, mock_config_entry, "test-cronjob", "default"
        )

        # Set coordinator last_update_success to True
        mock_coordinator.last_update_success = True

        # Verify available is True when last_update_success is True
        assert switch.available is True
