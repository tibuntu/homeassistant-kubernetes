"""Tests for the Kubernetes switch platform."""

import time
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.components.switch import SwitchDeviceClass
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_VERIFY_SSL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_registry import EntityRegistry
import pytest

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


@pytest.fixture
def mock_config_entry():
    """Create a mock config entry."""
    config_entry = MagicMock()
    config_entry.entry_id = "test_entry_id"
    config_entry.data = {
        CONF_HOST: "https://kubernetes.example.com",
        CONF_PORT: 443,
        CONF_VERIFY_SSL: True,
    }
    return config_entry


@pytest.fixture
def mock_coordinator():
    """Create a mock coordinator."""
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
    coordinator.client = MagicMock()
    return coordinator


@pytest.fixture
def mock_client():
    """Create a mock Kubernetes client."""
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
    return client


@pytest.fixture
def mock_hass():
    """Create a mock Home Assistant instance."""
    hass = MagicMock()
    hass.data = {DOMAIN: {}}
    return hass


class TestSwitchSetup:
    """Test switch setup."""

    async def test_async_setup_entry_success(
        self, mock_hass, mock_config_entry, mock_coordinator, mock_client
    ):
        """Test successful switch setup."""
        # Set up hass.data
        mock_hass.data[DOMAIN][mock_config_entry.entry_id] = {
            "coordinator": mock_coordinator,
            "client": mock_client,
        }

        # Mock async_add_entities
        mock_add_entities = MagicMock()

        # Call the setup function
        await async_setup_entry(mock_hass, mock_config_entry, mock_add_entities)

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
        self, mock_hass, mock_config_entry, mock_coordinator
    ):
        """Test switch setup with no resources."""
        # Create client with no resources
        mock_client = MagicMock()
        mock_client.get_deployments = AsyncMock(return_value=[])
        mock_client.get_statefulsets = AsyncMock(return_value=[])
        mock_client.get_cronjobs = AsyncMock(return_value=[])

        # Set up hass.data
        mock_hass.data[DOMAIN][mock_config_entry.entry_id] = {
            "coordinator": mock_coordinator,
            "client": mock_client,
        }

        # Mock async_add_entities
        mock_add_entities = MagicMock()

        # Call the setup function
        await async_setup_entry(mock_hass, mock_config_entry, mock_add_entities)

        # Verify entities were added (should be empty list)
        mock_add_entities.assert_called_once()
        added_entities = mock_add_entities.call_args[0][0]
        assert len(added_entities) == 0

    async def test_async_setup_entry_missing_domain(
        self, mock_hass, mock_config_entry, mock_client, mock_coordinator
    ):
        """Test switch setup when DOMAIN is missing from hass.data."""
        # Mock hass.data with DOMAIN but missing entry_id
        mock_hass.data = {"kubernetes": {}}

        # Mock async_add_entities
        mock_add_entities = MagicMock()

        # Call the setup function - should handle missing entry gracefully
        with pytest.raises(KeyError):
            await async_setup_entry(mock_hass, mock_config_entry, mock_add_entities)


class TestKubernetesDeploymentSwitch:
    """Test Kubernetes deployment switch."""

    def test_switch_initialization(self, mock_config_entry, mock_coordinator):
        """Test deployment switch initialization."""
        switch = KubernetesDeploymentSwitch(
            mock_coordinator, mock_config_entry, "test-deployment", "default"
        )

        assert switch.name == "test-deployment"
        assert switch.unique_id == "test_entry_id_test-deployment_deployment"
        assert switch.icon == "mdi:kubernetes"
        assert switch._attr_has_entity_name is True
        assert switch.deployment_name == "test-deployment"
        assert switch.namespace == "default"

    def test_switch_is_on_property(self, mock_config_entry, mock_coordinator):
        """Test switch is_on property."""
        switch = KubernetesDeploymentSwitch(
            mock_coordinator, mock_config_entry, "test-deployment", "default"
        )

        # Test initial state
        assert switch.is_on is False

        # Test when on
        switch._is_on = True
        assert switch.is_on is True

        # Test when off
        switch._is_on = False
        assert switch.is_on is False

    def test_switch_extra_state_attributes(self, mock_config_entry, mock_coordinator):
        """Test switch extra state attributes."""
        switch = KubernetesDeploymentSwitch(
            mock_coordinator, mock_config_entry, "test-deployment", "default"
        )

        attributes = switch.extra_state_attributes
        assert attributes["deployment_name"] == "test-deployment"
        assert attributes["namespace"] == "default"
        assert attributes["replicas"] == 0
        assert attributes[ATTR_WORKLOAD_TYPE] == WORKLOAD_TYPE_DEPLOYMENT
        assert attributes["last_scale_attempt_failed"] is False

    def test_switch_available_property(self, mock_config_entry, mock_coordinator):
        """Test switch available property."""
        switch = KubernetesDeploymentSwitch(
            mock_coordinator, mock_config_entry, "test-deployment", "default"
        )

        # Test when coordinator is successful
        mock_coordinator.last_update_success = True
        assert switch.available is True

        # Test when coordinator fails
        mock_coordinator.last_update_success = False
        assert switch.available is False

    async def test_switch_turn_on_success(self, mock_config_entry, mock_coordinator):
        """Test successful turn on."""
        switch = KubernetesDeploymentSwitch(
            mock_coordinator, mock_config_entry, "test-deployment", "default"
        )

        # Mock client method
        mock_coordinator.client.start_deployment = AsyncMock(return_value=True)

        # Mock async_write_ha_state to avoid hass context issues
        switch.async_write_ha_state = MagicMock()

        # Mock the _verify_scaling method to avoid the 5-second sleep delays
        switch._verify_scaling = AsyncMock()

        # Call turn on
        await switch.async_turn_on()

        # Verify client was called
        mock_coordinator.client.start_deployment.assert_called_once_with(
            "test-deployment", replicas=1, namespace="default"
        )

        # Verify optimistic state update
        assert switch._is_on is True
        assert switch._replicas == 1
        assert switch._last_scale_attempt_failed is False

        # Verify that _verify_scaling was called
        switch._verify_scaling.assert_called_once_with(1)

    async def test_switch_turn_on_failure(self, mock_config_entry, mock_coordinator):
        """Test failed turn on."""
        switch = KubernetesDeploymentSwitch(
            mock_coordinator, mock_config_entry, "test-deployment", "default"
        )

        # Mock client method to fail
        mock_coordinator.client.start_deployment = AsyncMock(return_value=False)

        # Mock async_write_ha_state to avoid hass context issues
        switch.async_write_ha_state = MagicMock()

        # Mock the _verify_scaling method to avoid the 5-second sleep delays
        switch._verify_scaling = AsyncMock()

        # Mock coordinator async_request_refresh
        mock_coordinator.async_request_refresh = AsyncMock()

        # Call turn on
        await switch.async_turn_on()

        # Verify client was called
        mock_coordinator.client.start_deployment.assert_called_once()

        # Verify failure state
        assert switch._last_scale_attempt_failed is True

        # Verify that _verify_scaling was NOT called (only called on success)
        switch._verify_scaling.assert_not_called()

    async def test_switch_turn_off_success(self, mock_config_entry, mock_coordinator):
        """Test successful turn off."""
        switch = KubernetesDeploymentSwitch(
            mock_coordinator, mock_config_entry, "test-deployment", "default"
        )

        # Mock client method
        mock_coordinator.client.stop_deployment = AsyncMock(return_value=True)

        # Mock async_write_ha_state to avoid hass context issues
        switch.async_write_ha_state = MagicMock()

        # Mock the _verify_scaling method to avoid the 5-second sleep delays
        switch._verify_scaling = AsyncMock()

        # Call turn off
        await switch.async_turn_off()

        # Verify client was called
        mock_coordinator.client.stop_deployment.assert_called_once_with(
            "test-deployment", namespace="default"
        )

        # Verify optimistic state update
        assert switch._is_on is False
        assert switch._replicas == 0
        assert switch._last_scale_attempt_failed is False

        # Verify that _verify_scaling was called
        switch._verify_scaling.assert_called_once_with(0)

    async def test_switch_turn_off_failure(self, mock_config_entry, mock_coordinator):
        """Test failed turn off."""
        switch = KubernetesDeploymentSwitch(
            mock_coordinator, mock_config_entry, "test-deployment", "default"
        )

        # Mock client method to fail
        mock_coordinator.client.stop_deployment = AsyncMock(return_value=False)

        # Mock async_write_ha_state to avoid hass context issues
        switch.async_write_ha_state = MagicMock()

        # Mock the _verify_scaling method to avoid the 5-second sleep delays
        switch._verify_scaling = AsyncMock()

        # Mock coordinator async_request_refresh
        mock_coordinator.async_request_refresh = AsyncMock()

        # Call turn off
        await switch.async_turn_off()

        # Verify client was called
        mock_coordinator.client.stop_deployment.assert_called_once()

        # Verify failure state
        assert switch._last_scale_attempt_failed is True

        # Verify that _verify_scaling was NOT called (only called on success)
        switch._verify_scaling.assert_not_called()

    async def test_switch_update_success(self, mock_config_entry, mock_coordinator):
        """Test successful switch update."""
        switch = KubernetesDeploymentSwitch(
            mock_coordinator, mock_config_entry, "test-deployment", "default"
        )

        # Mock coordinator method
        mock_coordinator.get_deployment_data.return_value = {
            "replicas": 2,
            "is_running": True,
        }

        # Call update
        await switch.async_update()

        # Verify state was updated
        assert switch._replicas == 2
        assert switch._is_on is True

    async def test_switch_update_not_found(self, mock_config_entry, mock_coordinator):
        """Test switch update when deployment not found."""
        switch = KubernetesDeploymentSwitch(
            mock_coordinator, mock_config_entry, "test-deployment", "default"
        )

        # Mock coordinator method to return None
        mock_coordinator.get_deployment_data.return_value = None

        # Call update
        await switch.async_update()

        # Verify state remains unchanged
        assert switch._replicas == 0
        assert switch._is_on is False

    async def test_switch_update_cooldown(self, mock_config_entry, mock_coordinator):
        """Test switch update during cooldown period."""
        switch = KubernetesDeploymentSwitch(
            mock_coordinator, mock_config_entry, "test-deployment", "default"
        )

        # Set recent scale time
        switch._last_scale_time = time.time()

        # Mock coordinator method
        mock_coordinator.get_deployment_data.return_value = {
            "replicas": 2,
            "is_running": True,
        }

        # Call update
        await switch.async_update()

        # Verify coordinator method was not called due to cooldown
        mock_coordinator.get_deployment_data.assert_not_called()


class TestKubernetesStatefulSetSwitch:
    """Test Kubernetes StatefulSet switch."""

    def test_switch_initialization(self, mock_config_entry, mock_coordinator):
        """Test StatefulSet switch initialization."""
        switch = KubernetesStatefulSetSwitch(
            mock_coordinator, mock_config_entry, "test-statefulset", "default"
        )

        assert switch.name == "test-statefulset"
        assert switch.unique_id == "test_entry_id_test-statefulset_statefulset"
        assert switch.icon == "mdi:kubernetes"
        assert switch._attr_has_entity_name is True
        assert switch.statefulset_name == "test-statefulset"
        assert switch.namespace == "default"

    def test_switch_extra_state_attributes(self, mock_config_entry, mock_coordinator):
        """Test StatefulSet switch extra state attributes."""
        switch = KubernetesStatefulSetSwitch(
            mock_coordinator, mock_config_entry, "test-statefulset", "default"
        )

        attributes = switch.extra_state_attributes
        assert attributes["statefulset_name"] == "test-statefulset"
        assert attributes["namespace"] == "default"
        assert attributes["replicas"] == 0
        assert attributes[ATTR_WORKLOAD_TYPE] == WORKLOAD_TYPE_STATEFULSET
        assert attributes["last_scale_attempt_failed"] is False

    async def test_switch_turn_on_success(self, mock_config_entry, mock_coordinator):
        """Test successful StatefulSet turn on."""
        switch = KubernetesStatefulSetSwitch(
            mock_coordinator, mock_config_entry, "test-statefulset", "default"
        )

        # Mock client method
        mock_coordinator.client.start_statefulset = AsyncMock(return_value=True)

        # Mock async_write_ha_state to avoid hass context issues
        switch.async_write_ha_state = MagicMock()

        # Mock the _verify_scaling method to avoid the 5-second sleep delays
        switch._verify_scaling = AsyncMock()

        # Call turn on
        await switch.async_turn_on()

        # Verify client was called
        mock_coordinator.client.start_statefulset.assert_called_once_with(
            "test-statefulset", replicas=1, namespace="default"
        )

        # Verify that _verify_scaling was called
        switch._verify_scaling.assert_called_once_with(1)

    async def test_switch_turn_off_success(self, mock_config_entry, mock_coordinator):
        """Test successful StatefulSet turn off."""
        switch = KubernetesStatefulSetSwitch(
            mock_coordinator, mock_config_entry, "test-statefulset", "default"
        )

        # Mock client method
        mock_coordinator.client.stop_statefulset = AsyncMock(return_value=True)

        # Mock async_write_ha_state to avoid hass context issues
        switch.async_write_ha_state = MagicMock()

        # Mock the _verify_scaling method to avoid the 5-second sleep delays
        switch._verify_scaling = AsyncMock()

        # Call turn off
        await switch.async_turn_off()

        # Verify client was called
        mock_coordinator.client.stop_statefulset.assert_called_once_with(
            "test-statefulset", namespace="default"
        )

        # Verify that _verify_scaling was called
        switch._verify_scaling.assert_called_once_with(0)


class TestKubernetesCronJobSwitch:
    """Test Kubernetes CronJob switch."""

    def test_switch_initialization(self, mock_config_entry, mock_coordinator):
        """Test CronJob switch initialization."""
        switch = KubernetesCronJobSwitch(
            mock_coordinator, mock_config_entry, "test-cronjob", "default"
        )

        assert switch.name == "test-cronjob"
        assert switch.unique_id == "test_entry_id_default_test-cronjob_cronjob"
        assert switch.icon == "mdi:clock-outline"
        assert switch._attr_has_entity_name is True
        assert switch.cronjob_name == "test-cronjob"
        assert switch.namespace == "default"

    def test_switch_extra_state_attributes(self, mock_config_entry, mock_coordinator):
        """Test CronJob switch extra state attributes."""
        switch = KubernetesCronJobSwitch(
            mock_coordinator, mock_config_entry, "test-cronjob", "default"
        )

        attributes = switch.extra_state_attributes
        assert attributes["cronjob_name"] == "test-cronjob"
        assert attributes["namespace"] == "default"
        assert attributes[ATTR_WORKLOAD_TYPE] == WORKLOAD_TYPE_CRONJOB

    async def test_switch_turn_on_success(self, mock_config_entry, mock_coordinator):
        """Test successful CronJob turn on."""
        switch = KubernetesCronJobSwitch(
            mock_coordinator, mock_config_entry, "test-cronjob", "default"
        )

        # Mock hass context
        switch.hass = MagicMock()
        switch.hass.data = {
            DOMAIN: {mock_config_entry.entry_id: {"client": mock_coordinator.client}}
        }

        # Mock client method
        mock_coordinator.client.resume_cronjob = AsyncMock(
            return_value={"success": True}
        )

        # Call turn on
        await switch.async_turn_on()

        # Verify client was called
        mock_coordinator.client.resume_cronjob.assert_called_once_with(
            "test-cronjob", "default"
        )

    async def test_switch_turn_off_success(self, mock_config_entry, mock_coordinator):
        """Test successful CronJob turn off."""
        switch = KubernetesCronJobSwitch(
            mock_coordinator, mock_config_entry, "test-cronjob", "default"
        )

        # Mock hass context
        switch.hass = MagicMock()
        switch.hass.data = {
            DOMAIN: {mock_config_entry.entry_id: {"client": mock_coordinator.client}}
        }

        # Mock client method
        mock_coordinator.client.suspend_cronjob = AsyncMock(
            return_value={"success": True}
        )

        # Call turn off
        await switch.async_turn_off()

        # Verify client was called
        mock_coordinator.client.suspend_cronjob.assert_called_once_with(
            "test-cronjob", "default"
        )


class TestDynamicEntityDiscovery:
    """Test dynamic entity discovery."""

    async def test_discover_new_entities_success(
        self, mock_hass, mock_config_entry, mock_coordinator, mock_client
    ):
        """Test successful discovery of new entities."""
        # Set up hass.data
        mock_hass.data[DOMAIN] = {
            "switch_add_entities": MagicMock(),
        }

        # Mock entity registry
        mock_entity_registry = MagicMock()
        mock_entity_registry.entities.get_entries_for_config_entry_id.return_value = []

        with patch(
            "custom_components.kubernetes.switch.async_get_entity_registry",
            return_value=mock_entity_registry,
        ):
            await _async_discover_and_add_new_entities(
                mock_hass, mock_config_entry, mock_coordinator, mock_client
            )

        # Verify add_entities was called
        mock_hass.data[DOMAIN]["switch_add_entities"].assert_called_once()

    async def test_discover_new_entities_no_callback(
        self, mock_hass, mock_config_entry, mock_coordinator, mock_client
    ):
        """Test discovery when no add_entities callback is available."""
        # Set up hass.data without callback
        mock_hass.data[DOMAIN] = {}

        # Mock entity registry
        mock_entity_registry = MagicMock()
        mock_entity_registry.entities.get_entries_for_config_entry_id.return_value = []

        with patch(
            "custom_components.kubernetes.switch.async_get_entity_registry",
            return_value=mock_entity_registry,
        ):
            # Should not raise exception
            await _async_discover_and_add_new_entities(
                mock_hass, mock_config_entry, mock_coordinator, mock_client
            )

    async def test_discover_new_entities_exception(
        self, mock_hass, mock_config_entry, mock_coordinator, mock_client
    ):
        """Test discovery when an exception occurs."""
        # Set up hass.data
        mock_hass.data[DOMAIN] = {
            "switch_add_entities": MagicMock(),
        }

        # Mock entity registry to raise exception
        mock_entity_registry = MagicMock()
        mock_entity_registry.entities.get_entries_for_config_entry_id.side_effect = (
            Exception("Test error")
        )

        with patch(
            "custom_components.kubernetes.switch.async_get_entity_registry",
            return_value=mock_entity_registry,
        ):
            # Should not raise exception
            await _async_discover_and_add_new_entities(
                mock_hass, mock_config_entry, mock_coordinator, mock_client
            )
