"""Tests for the Kubernetes binary sensor platform."""

from unittest.mock import AsyncMock, MagicMock

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_VERIFY_SSL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
import pytest

from custom_components.kubernetes.binary_sensor import (
    KubernetesBaseBinarySensor,
    KubernetesClusterHealthSensor,
    async_setup_entry,
)
from custom_components.kubernetes.const import DOMAIN


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
def mock_client():
    """Create a mock Kubernetes client."""
    client = MagicMock()
    client.is_cluster_healthy = AsyncMock(return_value=True)
    return client


@pytest.fixture
def mock_hass():
    """Create a mock Home Assistant instance."""
    hass = MagicMock()
    hass.data = {DOMAIN: {}}
    return hass


class TestKubernetesBinarySensorSetup:
    """Test binary sensor setup."""

    async def test_async_setup_entry_success(
        self, mock_hass, mock_config_entry, mock_client
    ):
        """Test successful binary sensor setup."""
        # Set up hass.data
        mock_hass.data[DOMAIN][mock_config_entry.entry_id] = {"client": mock_client}

        # Mock async_add_entities
        mock_add_entities = MagicMock()

        # Call the setup function
        await async_setup_entry(mock_hass, mock_config_entry, mock_add_entities)

        # Verify entities were added
        mock_add_entities.assert_called_once()
        added_entities = mock_add_entities.call_args[0][0]
        assert len(added_entities) == 1
        assert isinstance(added_entities[0], KubernetesClusterHealthSensor)

    async def test_async_setup_entry_missing_client(self, mock_hass, mock_config_entry):
        """Test binary sensor setup when client is missing."""
        # Set up hass.data without client - this should raise KeyError
        mock_hass.data[DOMAIN][mock_config_entry.entry_id] = {}

        # Mock async_add_entities
        mock_add_entities = MagicMock()

        # Call the setup function - should raise KeyError
        with pytest.raises(KeyError, match="'client'"):
            await async_setup_entry(mock_hass, mock_config_entry, mock_add_entities)


class TestKubernetesBaseBinarySensor:
    """Test base binary sensor class."""

    def test_base_binary_sensor_initialization(self, mock_config_entry, mock_client):
        """Test base binary sensor initialization."""
        sensor = KubernetesBaseBinarySensor(mock_client, mock_config_entry)

        assert sensor.client == mock_client
        assert sensor.config_entry == mock_config_entry
        assert sensor._attr_has_entity_name is True


class TestKubernetesClusterHealthSensor:
    """Test Kubernetes cluster health binary sensor."""

    def test_sensor_initialization(self, mock_config_entry, mock_client):
        """Test cluster health sensor initialization."""
        sensor = KubernetesClusterHealthSensor(mock_client, mock_config_entry)

        assert sensor.name == "Cluster Health"
        assert sensor.unique_id == "test_entry_id_cluster_health"
        assert sensor.device_class == BinarySensorDeviceClass.CONNECTIVITY
        assert sensor._attr_has_entity_name is True

    async def test_sensor_update_success(self, mock_config_entry, mock_client):
        """Test successful sensor update."""
        mock_client.is_cluster_healthy.return_value = True

        sensor = KubernetesClusterHealthSensor(mock_client, mock_config_entry)

        await sensor.async_update()

        assert sensor.is_on is True
        mock_client.is_cluster_healthy.assert_called_once()

    async def test_sensor_update_cluster_unhealthy(
        self, mock_config_entry, mock_client
    ):
        """Test sensor update when cluster is unhealthy."""
        mock_client.is_cluster_healthy.return_value = False

        sensor = KubernetesClusterHealthSensor(mock_client, mock_config_entry)

        await sensor.async_update()

        assert sensor.is_on is False
        mock_client.is_cluster_healthy.assert_called_once()

    async def test_sensor_update_exception(self, mock_config_entry, mock_client):
        """Test sensor update when client call fails."""
        mock_client.is_cluster_healthy.side_effect = Exception("API Error")

        sensor = KubernetesClusterHealthSensor(mock_client, mock_config_entry)

        await sensor.async_update()

        # Should handle exception gracefully and set to False
        assert sensor.is_on is False
        mock_client.is_cluster_healthy.assert_called_once()

    async def test_sensor_update_connection_error(self, mock_config_entry, mock_client):
        """Test sensor update with connection error."""
        mock_client.is_cluster_healthy.side_effect = ConnectionError(
            "Connection failed"
        )

        sensor = KubernetesClusterHealthSensor(mock_client, mock_config_entry)

        await sensor.async_update()

        # Should handle connection error gracefully
        assert sensor.is_on is False
        mock_client.is_cluster_healthy.assert_called_once()

    def test_sensor_properties(self, mock_config_entry, mock_client):
        """Test sensor properties."""
        sensor = KubernetesClusterHealthSensor(mock_client, mock_config_entry)

        # Test initial state
        assert sensor.is_on is None

        # Test after setting state
        sensor._attr_is_on = True
        assert sensor.is_on is True

        sensor._attr_is_on = False
        assert sensor.is_on is False

    def test_sensor_unique_id_format(self, mock_config_entry, mock_client):
        """Test sensor unique ID format."""
        sensor = KubernetesClusterHealthSensor(mock_client, mock_config_entry)

        expected_unique_id = f"{mock_config_entry.entry_id}_cluster_health"
        assert sensor.unique_id == expected_unique_id

    def test_sensor_device_class(self, mock_config_entry, mock_client):
        """Test sensor device class."""
        sensor = KubernetesClusterHealthSensor(mock_client, mock_config_entry)

        assert sensor.device_class == BinarySensorDeviceClass.CONNECTIVITY

    async def test_sensor_multiple_updates(self, mock_config_entry, mock_client):
        """Test multiple sensor updates."""
        # First update - healthy
        mock_client.is_cluster_healthy.return_value = True
        sensor = KubernetesClusterHealthSensor(mock_client, mock_config_entry)

        await sensor.async_update()
        assert sensor.is_on is True

        # Second update - unhealthy
        mock_client.is_cluster_healthy.return_value = False
        await sensor.async_update()
        assert sensor.is_on is False

        # Verify client was called twice
        assert mock_client.is_cluster_healthy.call_count == 2

    async def test_sensor_update_with_none_client(self, mock_config_entry):
        """Test sensor update with None client."""
        sensor = KubernetesClusterHealthSensor(None, mock_config_entry)

        # Should handle None client gracefully
        await sensor.async_update()
        assert sensor.is_on is False

    def test_sensor_entity_attributes(self, mock_config_entry, mock_client):
        """Test sensor entity attributes."""
        sensor = KubernetesClusterHealthSensor(mock_client, mock_config_entry)

        # Test that the sensor has the expected attributes
        assert hasattr(sensor, "_attr_name")
        assert hasattr(sensor, "_attr_unique_id")
        assert hasattr(sensor, "_attr_device_class")
        assert hasattr(sensor, "_attr_has_entity_name")
        assert hasattr(sensor, "_attr_is_on")

        assert sensor._attr_name == "Cluster Health"
        assert sensor._attr_unique_id == "test_entry_id_cluster_health"
        assert sensor._attr_device_class == BinarySensorDeviceClass.CONNECTIVITY
        assert sensor._attr_has_entity_name is True
