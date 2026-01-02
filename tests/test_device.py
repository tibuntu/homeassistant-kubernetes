"""Tests for the Kubernetes integration device management."""

from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
import pytest

from custom_components.kubernetes.device import (
    cleanup_orphaned_namespace_devices,
    get_all_namespaces,
    get_cluster_device_identifier,
    get_cluster_device_info,
    get_namespace_device_identifier,
    get_namespace_device_info,
    get_or_create_cluster_device,
    get_or_create_namespace_device,
)


@pytest.fixture
def mock_config_entry():
    """Mock config entry."""
    entry = MagicMock(spec=ConfigEntry)
    entry.entry_id = "test_entry_id"
    entry.data = {
        "cluster_name": "test-cluster",
    }
    return entry


@pytest.fixture
def mock_hass():
    """Mock Home Assistant instance."""
    hass = MagicMock(spec=HomeAssistant)
    return hass


@pytest.fixture
def mock_device_registry():
    """Mock device registry."""
    registry = MagicMock(spec=dr.DeviceRegistry)
    registry.async_get_device = MagicMock(return_value=None)
    registry.async_get_or_create = MagicMock()
    registry.async_remove_device = MagicMock()
    return registry


class TestDeviceIdentifiers:
    """Test device identifier functions."""

    def test_get_cluster_device_identifier(self, mock_config_entry):
        """Test cluster device identifier generation."""
        identifier = get_cluster_device_identifier(mock_config_entry)
        assert identifier == "test_entry_id_cluster"

    def test_get_namespace_device_identifier(self, mock_config_entry):
        """Test namespace device identifier generation."""
        identifier = get_namespace_device_identifier(mock_config_entry, "default")
        assert identifier == "test_entry_id_namespace_default"


class TestDeviceInfo:
    """Test device info functions."""

    def test_get_cluster_device_info(self, mock_config_entry):
        """Test cluster device info."""
        device_info = get_cluster_device_info(mock_config_entry)
        assert device_info["identifiers"] == {("kubernetes", "test_entry_id_cluster")}
        assert device_info["name"] == "test-cluster"
        assert device_info["manufacturer"] == "Kubernetes"
        assert device_info["model"] == "Cluster"

    def test_get_namespace_device_info(self, mock_config_entry):
        """Test namespace device info."""
        device_info = get_namespace_device_info(mock_config_entry, "default")
        assert device_info["identifiers"] == {
            ("kubernetes", "test_entry_id_namespace_default")
        }
        assert device_info["name"] == "test-cluster: default"
        assert device_info["manufacturer"] == "Kubernetes"
        assert device_info["model"] == "Namespace"
        assert device_info["via_device"] == ("kubernetes", "test_entry_id_cluster")


class TestGetAllNamespaces:
    """Test namespace discovery."""

    def test_get_all_namespaces_empty(self):
        """Test getting namespaces from empty data."""
        namespaces = get_all_namespaces(None)
        assert namespaces == set()

    def test_get_all_namespaces_from_pods(self):
        """Test extracting namespaces from pods."""
        data = {
            "pods": {
                "default_pod1": {"namespace": "default", "name": "pod1"},
                "kube-system_pod2": {"namespace": "kube-system", "name": "pod2"},
                "default_pod3": {"namespace": "default", "name": "pod3"},
            }
        }
        namespaces = get_all_namespaces(data)
        assert namespaces == {"default", "kube-system"}

    def test_get_all_namespaces_from_deployments(self):
        """Test extracting namespaces from deployments."""
        data = {
            "deployments": {
                "deployment1": {"namespace": "default", "name": "deployment1"},
                "deployment2": {"namespace": "production", "name": "deployment2"},
            }
        }
        namespaces = get_all_namespaces(data)
        assert namespaces == {"default", "production"}

    def test_get_all_namespaces_from_all_resources(self):
        """Test extracting namespaces from all resource types."""
        data = {
            "pods": {
                "default_pod1": {"namespace": "default", "name": "pod1"},
            },
            "deployments": {
                "deployment1": {"namespace": "default", "name": "deployment1"},
            },
            "statefulsets": {
                "statefulset1": {"namespace": "production", "name": "statefulset1"},
            },
            "cronjobs": {
                "cronjob1": {"namespace": "kube-system", "name": "cronjob1"},
            },
            "daemonsets": {
                "daemonset1": {"namespace": "default", "name": "daemonset1"},
            },
        }
        namespaces = get_all_namespaces(data)
        assert namespaces == {"default", "production", "kube-system"}


class TestDeviceCreation:
    """Test device creation functions."""

    @pytest.mark.asyncio
    async def test_get_or_create_cluster_device_new(self, mock_hass, mock_config_entry):
        """Test creating a new cluster device."""
        with patch(
            "custom_components.kubernetes.device.dr.async_get"
        ) as mock_get_registry:
            mock_registry = MagicMock()
            mock_registry.async_get_device = MagicMock(return_value=None)
            mock_device = MagicMock()
            mock_device.name = "test-cluster"
            mock_registry.async_get_or_create = MagicMock(return_value=mock_device)
            mock_get_registry.return_value = mock_registry

            device = await get_or_create_cluster_device(mock_hass, mock_config_entry)

            assert device == mock_device
            mock_registry.async_get_or_create.assert_called_once()
            call_kwargs = mock_registry.async_get_or_create.call_args[1]
            assert call_kwargs["identifiers"] == {
                ("kubernetes", "test_entry_id_cluster")
            }
            assert call_kwargs["name"] == "test-cluster"

    @pytest.mark.asyncio
    async def test_get_or_create_cluster_device_existing(
        self, mock_hass, mock_config_entry
    ):
        """Test retrieving an existing cluster device."""
        with patch(
            "custom_components.kubernetes.device.dr.async_get"
        ) as mock_get_registry:
            mock_registry = MagicMock()
            existing_device = MagicMock()
            existing_device.name = "test-cluster"
            mock_registry.async_get_device = MagicMock(return_value=existing_device)
            mock_get_registry.return_value = mock_registry

            device = await get_or_create_cluster_device(mock_hass, mock_config_entry)

            assert device == existing_device
            mock_registry.async_get_or_create.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_or_create_namespace_device_new(
        self, mock_hass, mock_config_entry
    ):
        """Test creating a new namespace device."""
        with patch(
            "custom_components.kubernetes.device.dr.async_get"
        ) as mock_get_registry:
            with patch(
                "custom_components.kubernetes.device.get_or_create_cluster_device"
            ) as mock_get_cluster:
                mock_registry = MagicMock()
                mock_registry.async_get_device = MagicMock(return_value=None)
                mock_cluster_device = MagicMock()
                mock_cluster_device.name = "test-cluster"
                mock_get_cluster.return_value = mock_cluster_device
                mock_namespace_device = MagicMock()
                mock_namespace_device.name = "test-cluster: default"
                mock_registry.async_get_or_create = MagicMock(
                    return_value=mock_namespace_device
                )
                mock_get_registry.return_value = mock_registry

                device = await get_or_create_namespace_device(
                    mock_hass, mock_config_entry, "default"
                )

                assert device == mock_namespace_device
                mock_registry.async_get_or_create.assert_called_once()
                call_kwargs = mock_registry.async_get_or_create.call_args[1]
                assert call_kwargs["identifiers"] == {
                    ("kubernetes", "test_entry_id_namespace_default")
                }
                assert call_kwargs["name"] == "test-cluster: default"
                assert call_kwargs["via_device"] == (
                    "kubernetes",
                    "test_entry_id_cluster",
                )


class TestDeviceCleanup:
    """Test device cleanup functions."""

    @pytest.mark.asyncio
    async def test_cleanup_orphaned_namespace_devices(
        self, mock_hass, mock_config_entry
    ):
        """Test cleaning up orphaned namespace devices."""
        with patch(
            "custom_components.kubernetes.device.dr.async_get"
        ) as mock_get_registry:
            with patch(
                "custom_components.kubernetes.device.dr.async_entries_for_config_entry"
            ) as mock_get_entries:
                mock_registry = MagicMock()
                mock_get_registry.return_value = mock_registry

                # Create mock devices
                orphaned_device = MagicMock()
                orphaned_device.id = "device1"
                orphaned_device.name = "test-cluster: old-namespace"
                orphaned_device.identifiers = {
                    ("kubernetes", "test_entry_id_namespace_old-namespace")
                }

                current_device = MagicMock()
                current_device.id = "device2"
                current_device.name = "test-cluster: default"
                current_device.identifiers = {
                    ("kubernetes", "test_entry_id_namespace_default")
                }

                mock_get_entries.return_value = [orphaned_device, current_device]

                current_namespaces = {"default"}

                await cleanup_orphaned_namespace_devices(
                    mock_hass, mock_config_entry, current_namespaces
                )

                # Should remove the orphaned device
                mock_registry.async_remove_device.assert_called_once_with("device1")

    @pytest.mark.asyncio
    async def test_cleanup_no_orphaned_devices(self, mock_hass, mock_config_entry):
        """Test cleanup when no orphaned devices exist."""
        with patch(
            "custom_components.kubernetes.device.dr.async_get"
        ) as mock_get_registry:
            with patch(
                "custom_components.kubernetes.device.dr.async_entries_for_config_entry"
            ) as mock_get_entries:
                mock_registry = MagicMock()
                mock_get_registry.return_value = mock_registry

                current_device = MagicMock()
                current_device.id = "device1"
                current_device.name = "test-cluster: default"
                current_device.identifiers = {
                    ("kubernetes", "test_entry_id_namespace_default")
                }

                mock_get_entries.return_value = [current_device]

                current_namespaces = {"default"}

                await cleanup_orphaned_namespace_devices(
                    mock_hass, mock_config_entry, current_namespaces
                )

                # Should not remove any devices
                mock_registry.async_remove_device.assert_not_called()
