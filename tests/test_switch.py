"""Tests for the Kubernetes switch platform."""

import time
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.const import CONF_HOST, CONF_PORT, CONF_VERIFY_SSL
from homeassistant.core import HomeAssistant
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.kubernetes.const import (
    ATTR_WORKLOAD_TYPE,
    DOMAIN,
    WORKLOAD_TYPE_CRONJOB,
    WORKLOAD_TYPE_DEPLOYMENT,
    WORKLOAD_TYPE_STATEFULSET,
)
from custom_components.kubernetes.switch import (
    KubernetesCronJobSwitch,
    KubernetesDeploymentSwitch,
    KubernetesStatefulSetSwitch,
    _async_discover_and_add_new_entities,
    async_setup_entry,
)

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_config_entry(hass: HomeAssistant) -> MockConfigEntry:
    """Create a MockConfigEntry and add it to hass."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        entry_id="test_entry_id",
        data={
            CONF_HOST: "https://kubernetes.example.com",
            CONF_PORT: 443,
            CONF_VERIFY_SSL: True,
            "cluster_name": "test-cluster",
        },
    )
    entry.add_to_hass(hass)
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
def cronjob_switch(mock_config_entry, mock_coordinator):
    """Create a CronJob switch instance."""
    return KubernetesCronJobSwitch(
        mock_coordinator, mock_config_entry, "test-cronjob", "default"
    )


# ---------------------------------------------------------------------------
# Platform setup tests (merged from test_switch_platform.py)
# ---------------------------------------------------------------------------


class TestSwitchSetup:
    """Test switch platform setup."""

    async def test_async_setup_entry_success(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test successful switch setup."""
        client = MagicMock()
        client.get_deployments = AsyncMock(
            return_value=[{"name": "test-deployment", "namespace": "default"}]
        )
        client.get_statefulsets = AsyncMock(
            return_value=[{"name": "test-statefulset", "namespace": "default"}]
        )
        client.get_cronjobs = AsyncMock(
            return_value=[{"name": "test-cronjob", "namespace": "default"}]
        )

        coordinator = MagicMock()
        coordinator.last_update_success = True
        coordinator.data = {
            "deployments": {
                "test-deployment": {
                    "name": "test-deployment",
                    "namespace": "default",
                    "replicas": 1,
                    "is_running": True,
                }
            },
            "statefulsets": {
                "test-statefulset": {
                    "name": "test-statefulset",
                    "namespace": "default",
                    "replicas": 1,
                    "is_running": True,
                }
            },
            "cronjobs": {
                "test-cronjob": {
                    "name": "test-cronjob",
                    "namespace": "default",
                    "suspend": False,
                }
            },
        }
        coordinator.client = client

        # Populate hass.data
        hass.data.setdefault(DOMAIN, {})[mock_config_entry.entry_id] = {
            "coordinator": coordinator,
            "client": client,
        }

        mock_add_entities = MagicMock()

        await async_setup_entry(hass, mock_config_entry, mock_add_entities)

        # Verify entities were added
        mock_add_entities.assert_called_once()
        added_entities = mock_add_entities.call_args[0][0]
        assert len(added_entities) == 3  # deployment, statefulset, cronjob

        # Verify entity types
        entity_types = [type(entity) for entity in added_entities]
        assert KubernetesDeploymentSwitch in entity_types
        assert KubernetesStatefulSetSwitch in entity_types
        assert KubernetesCronJobSwitch in entity_types

    async def test_async_setup_entry_empty_resources(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test switch setup with no resources."""
        client = MagicMock()
        client.get_deployments = AsyncMock(return_value=[])
        client.get_statefulsets = AsyncMock(return_value=[])
        client.get_cronjobs = AsyncMock(return_value=[])

        coordinator = MagicMock()
        coordinator.last_update_success = True
        coordinator.data = {
            "deployments": {},
            "statefulsets": {},
            "cronjobs": {},
        }

        # Populate hass.data
        hass.data.setdefault(DOMAIN, {})[mock_config_entry.entry_id] = {
            "coordinator": coordinator,
            "client": client,
        }

        mock_add_entities = MagicMock()

        await async_setup_entry(hass, mock_config_entry, mock_add_entities)

        # Verify entities were added (should be empty list)
        mock_add_entities.assert_called_once()
        added_entities = mock_add_entities.call_args[0][0]
        assert len(added_entities) == 0


# ---------------------------------------------------------------------------
# KubernetesCronJobSwitch tests
# ---------------------------------------------------------------------------


class TestKubernetesCronJobSwitch:
    """Test Kubernetes CronJob switch."""

    def test_initialization(self, cronjob_switch):
        """Test switch initialization."""
        assert cronjob_switch.cronjob_name == "test-cronjob"
        assert cronjob_switch.namespace == "default"
        assert cronjob_switch._attr_name == "test-cronjob"
        assert (
            cronjob_switch._attr_unique_id
            == "test_entry_id_default_test-cronjob_cronjob"
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
        self, cronjob_switch, mock_config_entry, mock_client
    ):
        """Test successful turn on (resume CronJob)."""
        # Setup
        cronjob_switch.hass = MagicMock()
        cronjob_switch.hass.data = {
            DOMAIN: {mock_config_entry.entry_id: {"client": mock_client}}
        }
        cronjob_switch.config_entry = mock_config_entry
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
        self, cronjob_switch, mock_config_entry, mock_client
    ):
        """Test failed turn on (resume CronJob)."""
        # Setup
        cronjob_switch.hass = MagicMock()
        cronjob_switch.hass.data = {
            DOMAIN: {mock_config_entry.entry_id: {"client": mock_client}}
        }
        cronjob_switch.config_entry = mock_config_entry
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
        self, cronjob_switch, mock_config_entry, mock_client
    ):
        """Test successful turn off (suspend CronJob)."""
        # Setup
        cronjob_switch.hass = MagicMock()
        cronjob_switch.hass.data = {
            DOMAIN: {mock_config_entry.entry_id: {"client": mock_client}}
        }
        cronjob_switch.config_entry = mock_config_entry
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
        self, cronjob_switch, mock_config_entry, mock_client
    ):
        """Test failed turn off (suspend CronJob)."""
        # Setup
        cronjob_switch.hass = MagicMock()
        cronjob_switch.hass.data = {
            DOMAIN: {mock_config_entry.entry_id: {"client": mock_client}}
        }
        cronjob_switch.config_entry = mock_config_entry
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


# ---------------------------------------------------------------------------
# KubernetesDeploymentSwitch tests
# ---------------------------------------------------------------------------


@pytest.fixture
def deployment_coordinator():
    """Mock coordinator for deployment tests."""
    coordinator = MagicMock()
    coordinator.last_update_success = True
    coordinator.data = {
        "deployments": {
            "nginx": {
                "name": "nginx",
                "namespace": "default",
                "replicas": 2,
                "is_running": True,
                "cpu_usage": 50.0,
                "memory_usage": 128.0,
            }
        }
    }
    coordinator.async_add_listener = MagicMock(return_value=lambda: None)
    coordinator.async_request_refresh = AsyncMock()
    coordinator.get_deployment_data = MagicMock(
        return_value={
            "name": "nginx",
            "namespace": "default",
            "replicas": 2,
            "is_running": True,
            "cpu_usage": 50.0,
            "memory_usage": 128.0,
        }
    )
    coordinator.client = MagicMock()
    coordinator.client.start_deployment = AsyncMock(return_value=True)
    coordinator.client.stop_deployment = AsyncMock(return_value=True)
    return coordinator


@pytest.fixture
def deployment_switch(deployment_coordinator, mock_config_entry):
    """Create a Deployment switch instance."""
    return KubernetesDeploymentSwitch(
        deployment_coordinator, mock_config_entry, "nginx", "default"
    )


class TestKubernetesDeploymentSwitch:
    """Test Kubernetes Deployment switch."""

    def test_initialization(self, deployment_switch):
        """Test deployment switch initialization."""
        assert deployment_switch.deployment_name == "nginx"
        assert deployment_switch.namespace == "default"
        assert deployment_switch._attr_name == "nginx"
        assert "nginx_deployment" in deployment_switch._attr_unique_id
        assert deployment_switch._attr_icon == "mdi:kubernetes"
        assert deployment_switch._is_on is False
        assert deployment_switch._replicas == 0

    def test_is_on(self, deployment_switch):
        """Test is_on property."""
        deployment_switch._is_on = True
        assert deployment_switch.is_on is True
        deployment_switch._is_on = False
        assert deployment_switch.is_on is False

    def test_available(self, deployment_switch, deployment_coordinator):
        """Test availability based on coordinator success."""
        deployment_coordinator.last_update_success = True
        assert deployment_switch.available is True
        deployment_coordinator.last_update_success = False
        assert deployment_switch.available is False

    def test_extra_state_attributes(self, deployment_switch):
        """Test extra state attributes."""
        deployment_switch._replicas = 3
        deployment_switch._cpu_usage = 100.0
        deployment_switch._memory_usage = 256.0
        attrs = deployment_switch.extra_state_attributes
        assert attrs["deployment_name"] == "nginx"
        assert attrs["namespace"] == "default"
        assert attrs["replicas"] == 3
        assert attrs[ATTR_WORKLOAD_TYPE] == WORKLOAD_TYPE_DEPLOYMENT

    def test_extra_state_attributes_with_metrics(self, mock_config_entry):
        """Test extra state attributes include CPU and memory metrics."""
        coordinator = MagicMock()
        coordinator.last_update_success = True
        switch = KubernetesDeploymentSwitch(
            coordinator, mock_config_entry, "test-deployment", "default"
        )
        switch._cpu_usage = 500.0
        switch._memory_usage = 256.0

        attributes = switch.extra_state_attributes
        assert attributes["deployment_name"] == "test-deployment"
        assert attributes["namespace"] == "default"
        assert attributes["replicas"] == 0
        assert attributes[ATTR_WORKLOAD_TYPE] == WORKLOAD_TYPE_DEPLOYMENT
        assert attributes["last_scale_attempt_failed"] is False
        assert attributes["cpu_usage_(millicores)"] == "500"
        assert attributes["memory_usage_(MiB)"] == "256"

    def test_device_info(self, mock_config_entry):
        """Test deployment switch device info."""
        coordinator = MagicMock()
        coordinator.last_update_success = True
        switch = KubernetesDeploymentSwitch(
            coordinator, mock_config_entry, "test-deployment", "default"
        )
        device_info = switch.device_info
        assert device_info["identifiers"] == {
            ("kubernetes", "test_entry_id_namespace_default")
        }
        assert device_info["name"] == "test-cluster: default"

    async def test_async_added_to_hass(self, deployment_switch, deployment_coordinator):
        """Test async_added_to_hass registers listener."""
        deployment_switch.async_on_remove = MagicMock()
        await deployment_switch.async_added_to_hass()
        deployment_switch.async_on_remove.assert_called_once()
        deployment_coordinator.async_add_listener.assert_called_once_with(
            deployment_switch._handle_coordinator_update
        )

    def test_handle_coordinator_update_with_data(
        self, deployment_switch, deployment_coordinator
    ):
        """Test _handle_coordinator_update when data is present."""
        deployment_switch.async_write_ha_state = MagicMock()
        deployment_coordinator.get_deployment_data.return_value = {
            "replicas": 3,
            "is_running": True,
            "cpu_usage": 200.0,
            "memory_usage": 512.0,
        }
        deployment_switch._handle_coordinator_update()
        assert deployment_switch._replicas == 3
        assert deployment_switch._is_on is True
        deployment_switch.async_write_ha_state.assert_called_once()

    def test_handle_coordinator_update_no_data(
        self, deployment_switch, deployment_coordinator
    ):
        """Test _handle_coordinator_update when deployment not found."""
        deployment_switch.async_write_ha_state = MagicMock()
        deployment_coordinator.get_deployment_data.return_value = None
        deployment_switch._handle_coordinator_update()
        # Should still call async_write_ha_state
        deployment_switch.async_write_ha_state.assert_called_once()

    def test_handle_coordinator_update_metrics_change(
        self, deployment_switch, deployment_coordinator
    ):
        """Test _handle_coordinator_update logs when metrics change."""
        deployment_switch.async_write_ha_state = MagicMock()
        deployment_switch._cpu_usage = 10.0
        deployment_switch._memory_usage = 64.0
        deployment_coordinator.get_deployment_data.return_value = {
            "replicas": 1,
            "is_running": True,
            "cpu_usage": 200.0,
            "memory_usage": 512.0,
        }
        deployment_switch._handle_coordinator_update()
        assert deployment_switch._cpu_usage == 200.0
        assert deployment_switch._memory_usage == 512.0

    async def test_async_turn_on_success(
        self, deployment_switch, deployment_coordinator
    ):
        """Test turn on success path."""
        deployment_switch.async_write_ha_state = MagicMock()
        deployment_switch._verify_scaling = AsyncMock()
        deployment_coordinator.client.start_deployment = AsyncMock(return_value=True)

        await deployment_switch.async_turn_on()

        deployment_coordinator.client.start_deployment.assert_called_once_with(
            "nginx", replicas=1, namespace="default"
        )
        assert deployment_switch._is_on is True
        assert deployment_switch._replicas == 1
        assert deployment_switch._last_scale_attempt_failed is False

    async def test_async_turn_on_failure(
        self, deployment_switch, deployment_coordinator
    ):
        """Test turn on failure path."""
        deployment_switch.async_write_ha_state = MagicMock()
        deployment_coordinator.client.start_deployment = AsyncMock(return_value=False)

        await deployment_switch.async_turn_on()

        assert deployment_switch._last_scale_attempt_failed is True
        deployment_coordinator.async_request_refresh.assert_called_once()

    async def test_async_turn_off_success(
        self, deployment_switch, deployment_coordinator
    ):
        """Test turn off success path."""
        deployment_switch.async_write_ha_state = MagicMock()
        deployment_switch._verify_scaling = AsyncMock()
        deployment_coordinator.client.stop_deployment = AsyncMock(return_value=True)

        await deployment_switch.async_turn_off()

        deployment_coordinator.client.stop_deployment.assert_called_once_with(
            "nginx", namespace="default"
        )
        assert deployment_switch._is_on is False
        assert deployment_switch._replicas == 0

    async def test_async_turn_off_failure(
        self, deployment_switch, deployment_coordinator
    ):
        """Test turn off failure path."""
        deployment_switch.async_write_ha_state = MagicMock()
        deployment_coordinator.client.stop_deployment = AsyncMock(return_value=False)

        await deployment_switch.async_turn_off()

        assert deployment_switch._last_scale_attempt_failed is True
        deployment_coordinator.async_request_refresh.assert_called_once()

    async def test_async_update_with_data(
        self, deployment_switch, deployment_coordinator
    ):
        """Test async_update with coordinator data."""
        deployment_switch._last_scale_time = 0.0
        deployment_coordinator.get_deployment_data.return_value = {
            "replicas": 3,
            "is_running": True,
            "cpu_usage": 100.0,
            "memory_usage": 256.0,
        }
        await deployment_switch.async_update()
        assert deployment_switch._replicas == 3
        assert deployment_switch._is_on is True

    async def test_async_update_no_data(
        self, deployment_switch, deployment_coordinator
    ):
        """Test async_update when deployment not found in coordinator."""
        deployment_switch._last_scale_time = 0.0
        deployment_coordinator.get_deployment_data.return_value = None
        # Should return early without exception
        await deployment_switch.async_update()

    async def test_async_update_in_cooldown(
        self, deployment_switch, deployment_coordinator
    ):
        """Test async_update skips during cooldown period."""
        deployment_switch._last_scale_time = time.time()
        deployment_switch._scale_cooldown = 100
        await deployment_switch.async_update()
        # Should not call get_deployment_data during cooldown
        deployment_coordinator.get_deployment_data.assert_not_called()

    async def test_async_update_replica_change_logged(
        self, deployment_switch, deployment_coordinator
    ):
        """Test async_update logs replica changes."""
        deployment_switch._last_scale_time = 0.0
        deployment_switch._replicas = 1
        deployment_switch._is_on = True
        deployment_coordinator.get_deployment_data.return_value = {
            "replicas": 3,
            "is_running": True,
            "cpu_usage": 0.0,
            "memory_usage": 0.0,
        }
        await deployment_switch.async_update()
        assert deployment_switch._replicas == 3

    async def test_async_update_state_change_logged(
        self, deployment_switch, deployment_coordinator
    ):
        """Test async_update logs state changes."""
        deployment_switch._last_scale_time = 0.0
        deployment_switch._is_on = False
        deployment_coordinator.get_deployment_data.return_value = {
            "replicas": 1,
            "is_running": True,
            "cpu_usage": 0.0,
            "memory_usage": 0.0,
        }
        await deployment_switch.async_update()
        assert deployment_switch._is_on is True

    async def test_async_update_unchanged_state(
        self, deployment_switch, deployment_coordinator
    ):
        """Test async_update when state unchanged (covers debug log path)."""
        deployment_switch._last_scale_time = 0.0
        deployment_switch._replicas = 2
        deployment_switch._is_on = True
        deployment_coordinator.get_deployment_data.return_value = {
            "replicas": 2,
            "is_running": True,
            "cpu_usage": 0.0,
            "memory_usage": 0.0,
        }
        await deployment_switch.async_update()
        assert deployment_switch._replicas == 2
        assert deployment_switch._is_on is True

    async def test_verify_scaling_success(
        self, deployment_switch, deployment_coordinator
    ):
        """Test _verify_scaling succeeds when target replicas reached."""
        deployment_switch._scale_verification_timeout = 10
        deployment_coordinator.async_request_refresh = AsyncMock()
        deployment_coordinator.get_deployment_data.return_value = {
            "replicas": 1,
            "is_running": True,
        }
        with patch("asyncio.sleep", new_callable=AsyncMock):
            await deployment_switch._verify_scaling(1)
        deployment_coordinator.async_request_refresh.assert_called()

    async def test_verify_scaling_not_found(
        self, deployment_switch, deployment_coordinator
    ):
        """Test _verify_scaling when deployment not found during verification."""
        deployment_switch._scale_verification_timeout = 10
        deployment_coordinator.async_request_refresh = AsyncMock()
        deployment_coordinator.get_deployment_data.return_value = None
        with patch("asyncio.sleep", new_callable=AsyncMock):
            await deployment_switch._verify_scaling(1)

    async def test_verify_scaling_still_scaling(
        self, deployment_switch, deployment_coordinator
    ):
        """Test _verify_scaling logs debug when still scaling."""
        deployment_switch._scale_verification_timeout = 10
        deployment_coordinator.async_request_refresh = AsyncMock()
        deployment_coordinator.get_deployment_data.return_value = {
            "replicas": 0,
            "is_running": False,
        }
        with patch("asyncio.sleep", new_callable=AsyncMock):
            await deployment_switch._verify_scaling(1)

    async def test_verify_scaling_exception(
        self, deployment_switch, deployment_coordinator
    ):
        """Test _verify_scaling handles exceptions gracefully."""
        deployment_switch._scale_verification_timeout = 10
        deployment_coordinator.async_request_refresh = AsyncMock(
            side_effect=Exception("Refresh failed")
        )
        with patch("asyncio.sleep", new_callable=AsyncMock):
            await deployment_switch._verify_scaling(1)

    async def test_verify_scaling_timeout(
        self, deployment_switch, deployment_coordinator
    ):
        """Test _verify_scaling times out when target never reached."""
        deployment_switch._scale_verification_timeout = 15
        deployment_coordinator.async_request_refresh = AsyncMock()
        deployment_coordinator.get_deployment_data.return_value = {
            "replicas": 0,
            "is_running": False,
        }
        with patch("asyncio.sleep", new_callable=AsyncMock):
            await deployment_switch._verify_scaling(1)
        # Should complete without error even after timeout


# ---------------------------------------------------------------------------
# KubernetesStatefulSetSwitch tests
# ---------------------------------------------------------------------------


@pytest.fixture
def statefulset_coordinator():
    """Mock coordinator for statefulset tests."""
    coordinator = MagicMock()
    coordinator.last_update_success = True
    coordinator.data = {
        "statefulsets": {
            "redis": {
                "name": "redis",
                "namespace": "default",
                "replicas": 1,
                "is_running": True,
                "cpu_usage": 20.0,
                "memory_usage": 64.0,
            }
        }
    }
    coordinator.async_add_listener = MagicMock(return_value=lambda: None)
    coordinator.async_request_refresh = AsyncMock()
    coordinator.get_statefulset_data = MagicMock(
        return_value={
            "name": "redis",
            "namespace": "default",
            "replicas": 1,
            "is_running": True,
            "cpu_usage": 20.0,
            "memory_usage": 64.0,
        }
    )
    coordinator.client = MagicMock()
    coordinator.client.start_statefulset = AsyncMock(return_value=True)
    coordinator.client.stop_statefulset = AsyncMock(return_value=True)
    return coordinator


@pytest.fixture
def statefulset_switch(statefulset_coordinator, mock_config_entry):
    """Create a StatefulSet switch instance."""
    return KubernetesStatefulSetSwitch(
        statefulset_coordinator, mock_config_entry, "redis", "default"
    )


class TestKubernetesStatefulSetSwitch:
    """Test Kubernetes StatefulSet switch."""

    def test_initialization(self, statefulset_switch):
        """Test statefulset switch initialization."""
        assert statefulset_switch.statefulset_name == "redis"
        assert statefulset_switch.namespace == "default"
        assert statefulset_switch._attr_name == "redis"
        assert "redis_statefulset" in statefulset_switch._attr_unique_id
        assert statefulset_switch._attr_icon == "mdi:kubernetes"
        assert statefulset_switch._is_on is False
        assert statefulset_switch._replicas == 0

    def test_is_on(self, statefulset_switch):
        """Test is_on property."""
        statefulset_switch._is_on = True
        assert statefulset_switch.is_on is True

    def test_available(self, statefulset_switch, statefulset_coordinator):
        """Test availability based on coordinator success."""
        statefulset_coordinator.last_update_success = True
        assert statefulset_switch.available is True
        statefulset_coordinator.last_update_success = False
        assert statefulset_switch.available is False

    def test_extra_state_attributes(self, statefulset_switch):
        """Test extra state attributes."""
        statefulset_switch._replicas = 2
        attrs = statefulset_switch.extra_state_attributes
        assert attrs["statefulset_name"] == "redis"
        assert attrs["namespace"] == "default"
        assert attrs["replicas"] == 2
        assert attrs[ATTR_WORKLOAD_TYPE] == WORKLOAD_TYPE_STATEFULSET

    def test_extra_state_attributes_with_metrics(self, mock_config_entry):
        """Test extra state attributes include CPU and memory metrics."""
        coordinator = MagicMock()
        coordinator.last_update_success = True
        switch = KubernetesStatefulSetSwitch(
            coordinator, mock_config_entry, "test-statefulset", "default"
        )
        switch._cpu_usage = 500.0
        switch._memory_usage = 256.0

        attributes = switch.extra_state_attributes
        assert attributes["statefulset_name"] == "test-statefulset"
        assert attributes["namespace"] == "default"
        assert attributes["replicas"] == 0
        assert attributes[ATTR_WORKLOAD_TYPE] == WORKLOAD_TYPE_STATEFULSET
        assert attributes["last_scale_attempt_failed"] is False
        assert attributes["cpu_usage_(millicores)"] == "500"
        assert attributes["memory_usage_(MiB)"] == "256"

    def test_device_info(self, mock_config_entry):
        """Test StatefulSet switch device info."""
        coordinator = MagicMock()
        coordinator.last_update_success = True
        switch = KubernetesStatefulSetSwitch(
            coordinator, mock_config_entry, "test-statefulset", "default"
        )
        device_info = switch.device_info
        assert device_info["identifiers"] == {
            ("kubernetes", "test_entry_id_namespace_default")
        }
        assert device_info["name"] == "test-cluster: default"

    async def test_async_added_to_hass(
        self, statefulset_switch, statefulset_coordinator
    ):
        """Test async_added_to_hass registers listener."""
        statefulset_switch.async_on_remove = MagicMock()
        await statefulset_switch.async_added_to_hass()
        statefulset_switch.async_on_remove.assert_called_once()
        statefulset_coordinator.async_add_listener.assert_called_once_with(
            statefulset_switch._handle_coordinator_update
        )

    def test_handle_coordinator_update_with_data(
        self, statefulset_switch, statefulset_coordinator
    ):
        """Test _handle_coordinator_update when data is present."""
        statefulset_switch.async_write_ha_state = MagicMock()
        statefulset_coordinator.get_statefulset_data.return_value = {
            "replicas": 2,
            "is_running": True,
            "cpu_usage": 100.0,
            "memory_usage": 256.0,
        }
        statefulset_switch._handle_coordinator_update()
        assert statefulset_switch._replicas == 2
        assert statefulset_switch._is_on is True
        statefulset_switch.async_write_ha_state.assert_called_once()

    def test_handle_coordinator_update_no_data(
        self, statefulset_switch, statefulset_coordinator
    ):
        """Test _handle_coordinator_update when statefulset not found."""
        statefulset_switch.async_write_ha_state = MagicMock()
        statefulset_coordinator.get_statefulset_data.return_value = None
        statefulset_switch._handle_coordinator_update()
        statefulset_switch.async_write_ha_state.assert_called_once()

    def test_handle_coordinator_update_metrics_change(
        self, statefulset_switch, statefulset_coordinator
    ):
        """Test _handle_coordinator_update logs when metrics change."""
        statefulset_switch.async_write_ha_state = MagicMock()
        statefulset_switch._cpu_usage = 5.0
        statefulset_switch._memory_usage = 32.0
        statefulset_coordinator.get_statefulset_data.return_value = {
            "replicas": 1,
            "is_running": True,
            "cpu_usage": 150.0,
            "memory_usage": 512.0,
        }
        statefulset_switch._handle_coordinator_update()
        assert statefulset_switch._cpu_usage == 150.0

    async def test_async_turn_on_success(
        self, statefulset_switch, statefulset_coordinator
    ):
        """Test turn on success path."""
        statefulset_switch.async_write_ha_state = MagicMock()
        statefulset_switch._verify_scaling = AsyncMock()
        statefulset_coordinator.client.start_statefulset = AsyncMock(return_value=True)

        await statefulset_switch.async_turn_on()

        statefulset_coordinator.client.start_statefulset.assert_called_once_with(
            "redis", replicas=1, namespace="default"
        )
        assert statefulset_switch._is_on is True
        assert statefulset_switch._replicas == 1
        assert statefulset_switch._last_scale_attempt_failed is False

    async def test_async_turn_on_failure(
        self, statefulset_switch, statefulset_coordinator
    ):
        """Test turn on failure path."""
        statefulset_switch.async_write_ha_state = MagicMock()
        statefulset_coordinator.client.start_statefulset = AsyncMock(return_value=False)

        await statefulset_switch.async_turn_on()

        assert statefulset_switch._last_scale_attempt_failed is True
        statefulset_coordinator.async_request_refresh.assert_called_once()

    async def test_async_turn_off_success(
        self, statefulset_switch, statefulset_coordinator
    ):
        """Test turn off success path."""
        statefulset_switch.async_write_ha_state = MagicMock()
        statefulset_switch._verify_scaling = AsyncMock()
        statefulset_coordinator.client.stop_statefulset = AsyncMock(return_value=True)

        await statefulset_switch.async_turn_off()

        statefulset_coordinator.client.stop_statefulset.assert_called_once_with(
            "redis", namespace="default"
        )
        assert statefulset_switch._is_on is False
        assert statefulset_switch._replicas == 0

    async def test_async_turn_off_failure(
        self, statefulset_switch, statefulset_coordinator
    ):
        """Test turn off failure path."""
        statefulset_switch.async_write_ha_state = MagicMock()
        statefulset_coordinator.client.stop_statefulset = AsyncMock(return_value=False)

        await statefulset_switch.async_turn_off()

        assert statefulset_switch._last_scale_attempt_failed is True
        statefulset_coordinator.async_request_refresh.assert_called_once()

    async def test_async_update_with_data(
        self, statefulset_switch, statefulset_coordinator
    ):
        """Test async_update with coordinator data."""
        statefulset_switch._last_scale_time = 0.0
        statefulset_coordinator.get_statefulset_data.return_value = {
            "replicas": 2,
            "is_running": True,
            "cpu_usage": 50.0,
            "memory_usage": 128.0,
        }
        await statefulset_switch.async_update()
        assert statefulset_switch._replicas == 2
        assert statefulset_switch._is_on is True

    async def test_async_update_no_data(
        self, statefulset_switch, statefulset_coordinator
    ):
        """Test async_update when statefulset not found in coordinator."""
        statefulset_switch._last_scale_time = 0.0
        statefulset_coordinator.get_statefulset_data.return_value = None
        await statefulset_switch.async_update()

    async def test_async_update_in_cooldown(
        self, statefulset_switch, statefulset_coordinator
    ):
        """Test async_update skips during cooldown period."""
        statefulset_switch._last_scale_time = time.time()
        statefulset_switch._scale_cooldown = 100
        await statefulset_switch.async_update()
        statefulset_coordinator.get_statefulset_data.assert_not_called()

    async def test_async_update_replica_change(
        self, statefulset_switch, statefulset_coordinator
    ):
        """Test async_update logs replica changes."""
        statefulset_switch._last_scale_time = 0.0
        statefulset_switch._replicas = 1
        statefulset_switch._is_on = True
        statefulset_coordinator.get_statefulset_data.return_value = {
            "replicas": 3,
            "is_running": True,
            "cpu_usage": 0.0,
            "memory_usage": 0.0,
        }
        await statefulset_switch.async_update()
        assert statefulset_switch._replicas == 3

    async def test_async_update_state_change(
        self, statefulset_switch, statefulset_coordinator
    ):
        """Test async_update logs state changes."""
        statefulset_switch._last_scale_time = 0.0
        statefulset_switch._is_on = False
        statefulset_coordinator.get_statefulset_data.return_value = {
            "replicas": 1,
            "is_running": True,
            "cpu_usage": 0.0,
            "memory_usage": 0.0,
        }
        await statefulset_switch.async_update()
        assert statefulset_switch._is_on is True

    async def test_async_update_unchanged_state(
        self, statefulset_switch, statefulset_coordinator
    ):
        """Test async_update covers debug log path for unchanged state."""
        statefulset_switch._last_scale_time = 0.0
        statefulset_switch._replicas = 1
        statefulset_switch._is_on = True
        statefulset_coordinator.get_statefulset_data.return_value = {
            "replicas": 1,
            "is_running": True,
            "cpu_usage": 0.0,
            "memory_usage": 0.0,
        }
        await statefulset_switch.async_update()
        assert statefulset_switch._replicas == 1
        assert statefulset_switch._is_on is True

    async def test_verify_scaling_success(
        self, statefulset_switch, statefulset_coordinator
    ):
        """Test _verify_scaling succeeds when target replicas reached."""
        statefulset_switch._scale_verification_timeout = 10
        statefulset_coordinator.async_request_refresh = AsyncMock()
        statefulset_coordinator.get_statefulset_data.return_value = {
            "replicas": 1,
            "is_running": True,
        }
        with patch("asyncio.sleep", new_callable=AsyncMock):
            await statefulset_switch._verify_scaling(1)
        statefulset_coordinator.async_request_refresh.assert_called()

    async def test_verify_scaling_not_found(
        self, statefulset_switch, statefulset_coordinator
    ):
        """Test _verify_scaling when statefulset not found during verification."""
        statefulset_switch._scale_verification_timeout = 10
        statefulset_coordinator.async_request_refresh = AsyncMock()
        statefulset_coordinator.get_statefulset_data.return_value = None
        with patch("asyncio.sleep", new_callable=AsyncMock):
            await statefulset_switch._verify_scaling(1)

    async def test_verify_scaling_still_scaling(
        self, statefulset_switch, statefulset_coordinator
    ):
        """Test _verify_scaling logs debug when still scaling."""
        statefulset_switch._scale_verification_timeout = 10
        statefulset_coordinator.async_request_refresh = AsyncMock()
        statefulset_coordinator.get_statefulset_data.return_value = {
            "replicas": 0,
            "is_running": False,
        }
        with patch("asyncio.sleep", new_callable=AsyncMock):
            await statefulset_switch._verify_scaling(1)

    async def test_verify_scaling_exception(
        self, statefulset_switch, statefulset_coordinator
    ):
        """Test _verify_scaling handles exceptions gracefully."""
        statefulset_switch._scale_verification_timeout = 10
        statefulset_coordinator.async_request_refresh = AsyncMock(
            side_effect=Exception("Refresh failed")
        )
        with patch("asyncio.sleep", new_callable=AsyncMock):
            await statefulset_switch._verify_scaling(1)

    async def test_verify_scaling_timeout(
        self, statefulset_switch, statefulset_coordinator
    ):
        """Test _verify_scaling times out gracefully."""
        statefulset_switch._scale_verification_timeout = 15
        statefulset_coordinator.async_request_refresh = AsyncMock()
        statefulset_coordinator.get_statefulset_data.return_value = {
            "replicas": 0,
            "is_running": False,
        }
        with patch("asyncio.sleep", new_callable=AsyncMock):
            await statefulset_switch._verify_scaling(1)


# ---------------------------------------------------------------------------
# _async_discover_and_add_new_entities tests
# ---------------------------------------------------------------------------


class TestDiscoverAndAddNewEntities:
    """Test _async_discover_and_add_new_entities helper function."""

    async def test_no_add_entities_callback(self, mock_config_entry):
        """Test function returns early when no callback stored."""
        hass = MagicMock()
        hass.data = {DOMAIN: {}}  # No 'switch_add_entities' key

        coordinator = MagicMock()
        coordinator.data = {}
        client = MagicMock()

        entity_registry = MagicMock()
        entity_registry.entities.get_entries_for_config_entry_id.return_value = []

        with patch(
            "custom_components.kubernetes.switch.async_get_entity_registry",
            return_value=entity_registry,
        ):
            # Should return early without error
            await _async_discover_and_add_new_entities(
                hass, mock_config_entry, coordinator, client
            )

    async def test_discovers_new_deployment(self, mock_config_entry):
        """Test discovering and adding a new deployment entity."""
        add_entities_callback = MagicMock()
        hass = MagicMock()
        hass.data = {DOMAIN: {"switch_add_entities": add_entities_callback}}

        coordinator = MagicMock()
        coordinator.data = {
            "deployments": {
                "new-deploy": {
                    "name": "new-deploy",
                    "namespace": "default",
                    "replicas": 1,
                    "is_running": True,
                }
            },
            "statefulsets": {},
            "cronjobs": {},
        }

        entity_registry = MagicMock()
        entity_registry.entities.get_entries_for_config_entry_id.return_value = []

        with (
            patch(
                "custom_components.kubernetes.switch.async_get_entity_registry",
                return_value=entity_registry,
            ),
            patch(
                "custom_components.kubernetes.device.get_or_create_namespace_device",
                new_callable=AsyncMock,
            ),
        ):
            await _async_discover_and_add_new_entities(
                hass, mock_config_entry, coordinator, MagicMock()
            )

        add_entities_callback.assert_called_once()
        new_entities = add_entities_callback.call_args[0][0]
        assert len(new_entities) == 1
        assert isinstance(new_entities[0], KubernetesDeploymentSwitch)

    async def test_discovers_new_statefulset(self, mock_config_entry):
        """Test discovering and adding a new statefulset entity."""
        add_entities_callback = MagicMock()
        hass = MagicMock()
        hass.data = {DOMAIN: {"switch_add_entities": add_entities_callback}}

        coordinator = MagicMock()
        coordinator.data = {
            "deployments": {},
            "statefulsets": {
                "new-sts": {
                    "name": "new-sts",
                    "namespace": "default",
                    "replicas": 1,
                    "is_running": True,
                }
            },
            "cronjobs": {},
        }

        entity_registry = MagicMock()
        entity_registry.entities.get_entries_for_config_entry_id.return_value = []

        with (
            patch(
                "custom_components.kubernetes.switch.async_get_entity_registry",
                return_value=entity_registry,
            ),
            patch(
                "custom_components.kubernetes.device.get_or_create_namespace_device",
                new_callable=AsyncMock,
            ),
        ):
            await _async_discover_and_add_new_entities(
                hass, mock_config_entry, coordinator, MagicMock()
            )

        add_entities_callback.assert_called_once()
        new_entities = add_entities_callback.call_args[0][0]
        assert len(new_entities) == 1
        assert isinstance(new_entities[0], KubernetesStatefulSetSwitch)

    async def test_discovers_new_cronjob(self, mock_config_entry):
        """Test discovering and adding a new cronjob entity."""
        add_entities_callback = MagicMock()
        hass = MagicMock()
        hass.data = {DOMAIN: {"switch_add_entities": add_entities_callback}}

        coordinator = MagicMock()
        coordinator.data = {
            "deployments": {},
            "statefulsets": {},
            "cronjobs": {
                "new-cron": {
                    "name": "new-cron",
                    "namespace": "default",
                    "schedule": "0 1 * * *",
                    "suspend": False,
                }
            },
        }

        entity_registry = MagicMock()
        entity_registry.entities.get_entries_for_config_entry_id.return_value = []

        with (
            patch(
                "custom_components.kubernetes.switch.async_get_entity_registry",
                return_value=entity_registry,
            ),
            patch(
                "custom_components.kubernetes.device.get_or_create_namespace_device",
                new_callable=AsyncMock,
            ),
        ):
            await _async_discover_and_add_new_entities(
                hass, mock_config_entry, coordinator, MagicMock()
            )

        add_entities_callback.assert_called_once()
        new_entities = add_entities_callback.call_args[0][0]
        assert len(new_entities) == 1
        assert isinstance(new_entities[0], KubernetesCronJobSwitch)

    async def test_skips_existing_deployment(self, mock_config_entry):
        """Test that already-registered deployments are skipped."""
        add_entities_callback = MagicMock()
        hass = MagicMock()
        hass.data = {DOMAIN: {"switch_add_entities": add_entities_callback}}

        coordinator = MagicMock()
        coordinator.data = {
            "deployments": {
                "existing-deploy": {
                    "name": "existing-deploy",
                    "namespace": "default",
                }
            },
            "statefulsets": {},
            "cronjobs": {},
        }

        # Simulate existing entity with the same unique_id
        existing_entity = MagicMock()
        existing_entity.unique_id = (
            f"{mock_config_entry.entry_id}_existing-deploy_deployment"
        )

        entity_registry = MagicMock()
        entity_registry.entities.get_entries_for_config_entry_id.return_value = [
            existing_entity
        ]

        with (
            patch(
                "custom_components.kubernetes.switch.async_get_entity_registry",
                return_value=entity_registry,
            ),
            patch(
                "custom_components.kubernetes.device.get_or_create_namespace_device",
                new_callable=AsyncMock,
            ),
        ):
            await _async_discover_and_add_new_entities(
                hass, mock_config_entry, coordinator, MagicMock()
            )

        # No new entities should be added
        add_entities_callback.assert_not_called()

    async def test_no_new_entities_debug_path(self, mock_config_entry):
        """Test that no-new-entities path hits the debug log branch."""
        add_entities_callback = MagicMock()
        hass = MagicMock()
        hass.data = {DOMAIN: {"switch_add_entities": add_entities_callback}}

        coordinator = MagicMock()
        coordinator.data = {}  # No deployments/statefulsets/cronjobs

        entity_registry = MagicMock()
        entity_registry.entities.get_entries_for_config_entry_id.return_value = []

        with patch(
            "custom_components.kubernetes.switch.async_get_entity_registry",
            return_value=entity_registry,
        ):
            await _async_discover_and_add_new_entities(
                hass, mock_config_entry, coordinator, MagicMock()
            )

        add_entities_callback.assert_not_called()

    async def test_exception_handled_gracefully(self, mock_config_entry):
        """Test that exceptions in the function are caught and logged."""
        hass = MagicMock()
        hass.data = {DOMAIN: {"switch_add_entities": MagicMock()}}

        coordinator = MagicMock()
        coordinator.data = None

        with patch(
            "custom_components.kubernetes.switch.async_get_entity_registry",
            side_effect=Exception("Registry error"),
        ):
            # Should not raise
            await _async_discover_and_add_new_entities(
                hass, mock_config_entry, coordinator, MagicMock()
            )

    async def test_does_not_readd_pending_entities(self, mock_config_entry):
        """Test that entities added in a previous cycle are not re-added."""
        add_entities_callback = MagicMock()
        pending_ids: set[str] = set()
        hass = MagicMock()
        hass.data = {
            DOMAIN: {
                "switch_add_entities": add_entities_callback,
                mock_config_entry.entry_id: {
                    "switch_pending_unique_ids": pending_ids,
                },
            }
        }

        coordinator = MagicMock()
        coordinator.data = {
            "deployments": {
                "my-deploy": {
                    "name": "my-deploy",
                    "namespace": "default",
                    "replicas": 1,
                    "is_running": True,
                }
            },
            "statefulsets": {},
            "cronjobs": {},
        }

        entity_registry = MagicMock()
        entity_registry.entities.get_entries_for_config_entry_id.return_value = []

        with (
            patch(
                "custom_components.kubernetes.switch.async_get_entity_registry",
                return_value=entity_registry,
            ),
            patch(
                "custom_components.kubernetes.device.get_or_create_namespace_device",
                new_callable=AsyncMock,
            ),
        ):
            # First call: discovers the deployment
            await _async_discover_and_add_new_entities(
                hass, mock_config_entry, coordinator, MagicMock()
            )

        add_entities_callback.assert_called_once()
        assert len(pending_ids) == 1

        add_entities_callback.reset_mock()

        with (
            patch(
                "custom_components.kubernetes.switch.async_get_entity_registry",
                return_value=entity_registry,
            ),
            patch(
                "custom_components.kubernetes.device.get_or_create_namespace_device",
                new_callable=AsyncMock,
            ),
        ):
            # Second call: entity registry still empty, but pending_ids prevents re-add
            await _async_discover_and_add_new_entities(
                hass, mock_config_entry, coordinator, MagicMock()
            )

        add_entities_callback.assert_not_called()
