"""Tests for the Kubernetes integration device management."""

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

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
    update_cluster_device_version,
)

# `mock_config_entry` (cluster_name="test-cluster", entry_id="test_entry_id")
# comes from tests/conftest.py's `mock_config_entry` fixture.


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

    async def test_get_namespace_device_info(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test namespace device info."""
        cluster_device = await get_or_create_cluster_device(hass, mock_config_entry)
        device_info = get_namespace_device_info(hass, mock_config_entry, "default")
        assert device_info["identifiers"] == {
            ("kubernetes", "test_entry_id_namespace_default")
        }
        assert device_info["name"] == "test-cluster: default"
        assert device_info["manufacturer"] == "Kubernetes"
        assert device_info["model"] == "Namespace"
        assert device_info["via_device_id"] == cluster_device.id

    def test_get_namespace_device_info_no_cluster_device(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test namespace device info when cluster device does not exist yet."""
        device_info = get_namespace_device_info(hass, mock_config_entry, "default")
        assert device_info["identifiers"] == {
            ("kubernetes", "test_entry_id_namespace_default")
        }
        assert device_info["via_device_id"] is None


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

        # Verify the via_device_id relationship — cluster device should exist
        registry = dr.async_get(hass)
        cluster_device = registry.async_get_device_by_identifier(
            (DOMAIN, "test_entry_id_cluster"), mock_config_entry.entry_id
        )
        assert cluster_device is not None
        assert device.via_device_id == cluster_device.id


class TestUpdateClusterDeviceVersion:
    """Test mirroring the API server version onto the cluster device."""

    async def test_sets_and_updates_sw_version(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """The version is written, then replaced on upgrade."""
        device = await get_or_create_cluster_device(hass, mock_config_entry)
        registry = dr.async_get(hass)

        update_cluster_device_version(hass, mock_config_entry, "v1.36.2-eks-1552ad0")
        assert registry.async_get(device.id).sw_version == "v1.36.2-eks-1552ad0"

        update_cluster_device_version(hass, mock_config_entry, "v1.37.0-eks-0000000")
        assert registry.async_get(device.id).sw_version == "v1.37.0-eks-0000000"

    async def test_unknown_version_keeps_last_known(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """A failed /version fetch must not blank the stored version."""
        device = await get_or_create_cluster_device(hass, mock_config_entry)
        update_cluster_device_version(hass, mock_config_entry, "v1.36.2")

        update_cluster_device_version(hass, mock_config_entry, None)
        # Re-running device creation (platform setup) must not clear it either.
        await get_or_create_cluster_device(hass, mock_config_entry)

        assert dr.async_get(hass).async_get(device.id).sw_version == "v1.36.2"

    async def test_no_device_yet_is_noop(self, hass: HomeAssistant, mock_config_entry):
        """Before the platforms create the device there is nothing to update."""
        update_cluster_device_version(hass, mock_config_entry, "v1.36.2")

        assert not dr.async_entries_for_config_entry(
            dr.async_get(hass), mock_config_entry.entry_id
        )


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
            registry.async_get_device_by_identifier(
                (DOMAIN, "test_entry_id_namespace_old-namespace"),
                mock_config_entry.entry_id,
            )
            is None
        )
        # Current device should still exist
        assert (
            registry.async_get_device_by_identifier(
                (DOMAIN, "test_entry_id_namespace_default"),
                mock_config_entry.entry_id,
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
            registry.async_get_device_by_identifier(
                (DOMAIN, "test_entry_id_namespace_default"),
                mock_config_entry.entry_id,
            )
            is not None
        )
