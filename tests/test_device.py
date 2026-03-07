"""Tests for the Kubernetes integration device management."""

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.kubernetes.const import DOMAIN
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
def mock_config_entry(hass: HomeAssistant) -> MockConfigEntry:
    """Create a mock config entry and add it to hass."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"cluster_name": "test-cluster"},
        entry_id="test_entry_id",
    )
    entry.add_to_hass(hass)
    return entry


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

    async def test_get_or_create_cluster_device_new(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test creating a new cluster device."""
        device = await get_or_create_cluster_device(hass, mock_config_entry)

        assert device is not None
        assert device.name == "test-cluster"
        assert (DOMAIN, "test_entry_id_cluster") in device.identifiers

    async def test_get_or_create_cluster_device_existing(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test retrieving an existing cluster device."""
        device1 = await get_or_create_cluster_device(hass, mock_config_entry)
        device2 = await get_or_create_cluster_device(hass, mock_config_entry)

        assert device1.id == device2.id

    async def test_get_or_create_namespace_device_new(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test creating a new namespace device."""
        device = await get_or_create_namespace_device(
            hass, mock_config_entry, "default"
        )

        assert device is not None
        assert device.name == "test-cluster: default"
        assert (DOMAIN, "test_entry_id_namespace_default") in device.identifiers

        # Verify the via_device relationship — cluster device should exist
        registry = dr.async_get(hass)
        cluster_device = registry.async_get_device(
            identifiers={(DOMAIN, "test_entry_id_cluster")}
        )
        assert cluster_device is not None


class TestDeviceCleanup:
    """Test device cleanup functions."""

    async def test_cleanup_orphaned_namespace_devices(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test cleaning up orphaned namespace devices."""
        registry = dr.async_get(hass)

        # Create cluster device (parent)
        await get_or_create_cluster_device(hass, mock_config_entry)

        # Create namespace devices
        registry.async_get_or_create(
            config_entry_id=mock_config_entry.entry_id,
            identifiers={(DOMAIN, "test_entry_id_namespace_old-namespace")},
            name="test-cluster: old-namespace",
        )
        registry.async_get_or_create(
            config_entry_id=mock_config_entry.entry_id,
            identifiers={(DOMAIN, "test_entry_id_namespace_default")},
            name="test-cluster: default",
        )

        current_namespaces = {"default"}
        await cleanup_orphaned_namespace_devices(
            hass, mock_config_entry, current_namespaces
        )

        # Orphaned device should be removed
        assert (
            registry.async_get_device(
                identifiers={(DOMAIN, "test_entry_id_namespace_old-namespace")}
            )
            is None
        )
        # Current device should still exist
        assert (
            registry.async_get_device(
                identifiers={(DOMAIN, "test_entry_id_namespace_default")}
            )
            is not None
        )

    async def test_cleanup_no_orphaned_devices(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test cleanup when no orphaned devices exist."""
        registry = dr.async_get(hass)

        # Create cluster device and one current namespace device
        await get_or_create_cluster_device(hass, mock_config_entry)
        registry.async_get_or_create(
            config_entry_id=mock_config_entry.entry_id,
            identifiers={(DOMAIN, "test_entry_id_namespace_default")},
            name="test-cluster: default",
        )

        current_namespaces = {"default"}
        await cleanup_orphaned_namespace_devices(
            hass, mock_config_entry, current_namespaces
        )

        # Device should still exist
        assert (
            registry.async_get_device(
                identifiers={(DOMAIN, "test_entry_id_namespace_default")}
            )
            is not None
        )
