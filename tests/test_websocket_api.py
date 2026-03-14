"""Tests for the Kubernetes WebSocket API module."""

from unittest.mock import MagicMock, patch

import pytest

from custom_components.kubernetes.const import DOMAIN
from custom_components.kubernetes.websocket_api import (
    _build_alerts,
    _build_cluster_overview,
    _build_namespace_breakdown,
    _get_cluster_overview_data,
    _get_config_list_data,
    _get_nodes_list_data,
    _get_pods_list_data,
    _get_workloads_list_data,
    async_register_websocket_commands,
)


@pytest.fixture
def sample_coordinator_data():
    """Sample coordinator data for testing."""
    return {
        "deployments": {
            "nginx": {
                "name": "nginx",
                "namespace": "default",
                "replicas": 3,
                "available_replicas": 3,
                "ready_replicas": 3,
                "is_running": True,
            },
            "api": {
                "name": "api",
                "namespace": "production",
                "replicas": 2,
                "available_replicas": 1,
                "ready_replicas": 1,
                "is_running": True,
            },
        },
        "statefulsets": {
            "postgres": {
                "name": "postgres",
                "namespace": "default",
                "replicas": 1,
                "available_replicas": 1,
                "ready_replicas": 1,
                "is_running": True,
            },
        },
        "daemonsets": {
            "fluentd": {
                "name": "fluentd",
                "namespace": "kube-system",
                "desired_number_scheduled": 3,
                "current_number_scheduled": 3,
                "number_ready": 3,
                "number_available": 3,
                "is_running": True,
            },
        },
        "cronjobs": {
            "backup": {
                "name": "backup",
                "namespace": "default",
            },
        },
        "jobs": {
            "migration": {
                "name": "migration",
                "namespace": "production",
            },
        },
        "nodes": {
            "node-1": {
                "name": "node-1",
                "status": "Ready",
                "memory_pressure": False,
                "disk_pressure": False,
                "pid_pressure": False,
                "network_unavailable": False,
            },
            "node-2": {
                "name": "node-2",
                "status": "Ready",
                "memory_pressure": True,
                "disk_pressure": False,
                "pid_pressure": False,
                "network_unavailable": False,
            },
        },
        "pods": {
            "default_nginx-abc123": {
                "name": "nginx-abc123",
                "namespace": "default",
                "phase": "Running",
            },
            "default_nginx-def456": {
                "name": "nginx-def456",
                "namespace": "default",
                "phase": "Running",
            },
            "production_api-xyz789": {
                "name": "api-xyz789",
                "namespace": "production",
                "phase": "Failed",
            },
        },
        "pods_count": 3,
        "nodes_count": 2,
        "last_update": 1700000000.0,
    }


def _make_coordinator(data, last_update_success=True, options=None):
    """Create a mock coordinator with the given data."""
    coordinator = MagicMock()
    coordinator.data = data
    coordinator.last_update_success = last_update_success
    coordinator.config_entry = MagicMock()
    coordinator.config_entry.options = options or {}
    return coordinator


class TestAsyncRegisterWebsocketCommands:
    """Tests for WS command registration."""

    def test_registers_commands(self, mock_hass):
        """Test that WS commands are registered."""
        with patch(
            "custom_components.kubernetes.websocket_api.websocket_api"
        ) as mock_ws_api:
            async_register_websocket_commands(mock_hass)
            assert mock_ws_api.async_register_command.call_count == 5


class TestWebsocketClusterOverview:
    """Tests for the kubernetes/cluster/overview command logic."""

    def test_returns_empty_when_no_domain_data(self, mock_hass):
        """Test returns empty clusters list when no DOMAIN data."""
        mock_hass.data = {}

        result = _get_cluster_overview_data(mock_hass)

        assert result == {"clusters": []}

    def test_returns_empty_when_domain_has_only_metadata(self, mock_hass):
        """Test returns empty clusters when only metadata keys exist."""
        mock_hass.data = {DOMAIN: {"panel_registered": True}}

        result = _get_cluster_overview_data(mock_hass)

        assert result == {"clusters": []}

    def test_returns_single_cluster_data(self, mock_hass, sample_coordinator_data):
        """Test returns data for a single cluster."""
        coordinator = _make_coordinator(sample_coordinator_data)
        mock_hass.data = {
            DOMAIN: {
                "entry_1": {
                    "config": {"cluster_name": "test-cluster"},
                    "coordinator": coordinator,
                },
            }
        }

        result = _get_cluster_overview_data(mock_hass)

        assert len(result["clusters"]) == 1

        cluster = result["clusters"][0]
        assert cluster["entry_id"] == "entry_1"
        assert cluster["cluster_name"] == "test-cluster"
        assert cluster["healthy"] is True
        assert cluster["counts"]["pods"] == 3
        assert cluster["counts"]["nodes"] == 2
        assert cluster["counts"]["deployments"] == 2
        assert cluster["counts"]["statefulsets"] == 1
        assert cluster["counts"]["daemonsets"] == 1
        assert cluster["counts"]["cronjobs"] == 1
        assert cluster["counts"]["jobs"] == 1

    def test_multi_cluster_aggregation(self, mock_hass, sample_coordinator_data):
        """Test aggregates data from multiple config entries."""
        coordinator_1 = _make_coordinator(sample_coordinator_data)
        coordinator_2 = _make_coordinator(
            {
                "deployments": {},
                "statefulsets": {},
                "daemonsets": {},
                "cronjobs": {},
                "jobs": {},
                "nodes": {},
                "pods": {},
                "pods_count": 0,
                "nodes_count": 0,
                "last_update": 1700000001.0,
            }
        )
        mock_hass.data = {
            DOMAIN: {
                "entry_1": {
                    "config": {"cluster_name": "cluster-a"},
                    "coordinator": coordinator_1,
                },
                "entry_2": {
                    "config": {"cluster_name": "cluster-b"},
                    "coordinator": coordinator_2,
                },
            }
        }

        result = _get_cluster_overview_data(mock_hass)

        assert len(result["clusters"]) == 2
        names = {c["cluster_name"] for c in result["clusters"]}
        assert names == {"cluster-a", "cluster-b"}

    def test_skips_metadata_keys(self, mock_hass, sample_coordinator_data):
        """Test skips panel_registered and switch_add_entities keys."""
        coordinator = _make_coordinator(sample_coordinator_data)
        mock_hass.data = {
            DOMAIN: {
                "panel_registered": True,
                "switch_add_entities": MagicMock(),
                "entry_1": {
                    "config": {"cluster_name": "test"},
                    "coordinator": coordinator,
                },
            }
        }

        result = _get_cluster_overview_data(mock_hass)

        assert len(result["clusters"]) == 1

    def test_handles_none_coordinator_data(self, mock_hass):
        """Test handles coordinator with None data gracefully."""
        coordinator = _make_coordinator(None)
        mock_hass.data = {
            DOMAIN: {
                "entry_1": {
                    "config": {"cluster_name": "test"},
                    "coordinator": coordinator,
                },
            }
        }

        result = _get_cluster_overview_data(mock_hass)

        cluster = result["clusters"][0]
        assert cluster["healthy"] is None
        assert cluster["counts"]["pods"] == 0
        assert cluster["counts"]["nodes"] == 0
        assert cluster["namespaces"] == {}

    def test_skips_entries_without_coordinator(self, mock_hass):
        """Test skips entries that have no coordinator."""
        mock_hass.data = {
            DOMAIN: {
                "entry_1": {
                    "config": {"cluster_name": "test"},
                    # No coordinator key
                },
            }
        }

        result = _get_cluster_overview_data(mock_hass)

        assert len(result["clusters"]) == 0

    def test_watch_enabled_from_options(self, mock_hass):
        """Test watch_enabled is read from config entry options."""
        coordinator = _make_coordinator(
            {
                "deployments": {},
                "statefulsets": {},
                "daemonsets": {},
                "cronjobs": {},
                "jobs": {},
                "nodes": {},
                "pods": {},
                "pods_count": 0,
                "nodes_count": 0,
                "last_update": 0.0,
            },
            options={"enable_watch": True},
        )
        mock_hass.data = {
            DOMAIN: {
                "entry_1": {
                    "config": {"cluster_name": "test"},
                    "coordinator": coordinator,
                },
            }
        }

        result = _get_cluster_overview_data(mock_hass)

        assert result["clusters"][0]["watch_enabled"] is True


class TestBuildClusterOverview:
    """Tests for the _build_cluster_overview helper."""

    def test_with_none_data(self):
        """Test building overview when coordinator data is None."""
        coordinator = _make_coordinator(None)
        result = _build_cluster_overview(
            "entry_1", {"cluster_name": "test"}, coordinator
        )

        assert result["entry_id"] == "entry_1"
        assert result["cluster_name"] == "test"
        assert result["healthy"] is None
        assert result["counts"]["pods"] == 0

    def test_uses_default_cluster_name(self):
        """Test uses default cluster name when not in config."""
        coordinator = _make_coordinator(None)
        result = _build_cluster_overview("entry_1", {}, coordinator)

        assert result["cluster_name"] == "default"

    def test_healthy_from_last_update_success(self, sample_coordinator_data):
        """Test healthy field comes from coordinator.last_update_success."""
        coordinator = _make_coordinator(
            sample_coordinator_data, last_update_success=False
        )
        result = _build_cluster_overview(
            "entry_1", {"cluster_name": "test"}, coordinator
        )
        assert result["healthy"] is False


class TestBuildNamespaceBreakdown:
    """Tests for _build_namespace_breakdown."""

    def test_empty_data(self):
        """Test with empty data dict."""
        result = _build_namespace_breakdown({})
        assert result == {}

    def test_groups_by_namespace(self, sample_coordinator_data):
        """Test resources are grouped correctly by namespace."""
        result = _build_namespace_breakdown(sample_coordinator_data)

        assert "default" in result
        assert "production" in result
        assert "kube-system" in result

        assert result["default"]["pods"] == 2
        assert result["default"]["deployments"] == 1
        assert result["default"]["statefulsets"] == 1
        assert result["default"]["cronjobs"] == 1

        assert result["production"]["pods"] == 1
        assert result["production"]["deployments"] == 1
        assert result["production"]["jobs"] == 1

        assert result["kube-system"]["daemonsets"] == 1


class TestBuildAlerts:
    """Tests for _build_alerts."""

    def test_empty_data(self):
        """Test with empty data."""
        result = _build_alerts({})
        assert result["nodes_with_pressure"] == []
        assert result["degraded_workloads"] == []
        assert result["failed_pods"] == []

    def test_detects_node_pressure(self, sample_coordinator_data):
        """Test detects nodes with pressure conditions."""
        result = _build_alerts(sample_coordinator_data)
        assert len(result["nodes_with_pressure"]) == 1
        assert result["nodes_with_pressure"][0]["name"] == "node-2"
        assert "memory_pressure" in result["nodes_with_pressure"][0]["conditions"]

    def test_detects_degraded_deployment(self, sample_coordinator_data):
        """Test detects deployments where available < desired."""
        result = _build_alerts(sample_coordinator_data)
        degraded = result["degraded_workloads"]
        assert len(degraded) == 1
        assert degraded[0]["name"] == "api"
        assert degraded[0]["type"] == "Deployment"
        assert degraded[0]["ready"] == 1
        assert degraded[0]["desired"] == 2

    def test_detects_degraded_statefulset(self):
        """Test detects degraded statefulsets."""
        data = {
            "deployments": {},
            "statefulsets": {
                "db": {
                    "name": "db",
                    "namespace": "default",
                    "replicas": 3,
                    "ready_replicas": 1,
                },
            },
            "daemonsets": {},
            "nodes": {},
            "pods": {},
        }
        result = _build_alerts(data)
        assert len(result["degraded_workloads"]) == 1
        assert result["degraded_workloads"][0]["type"] == "StatefulSet"

    def test_detects_degraded_daemonset(self):
        """Test detects degraded daemonsets."""
        data = {
            "deployments": {},
            "statefulsets": {},
            "daemonsets": {
                "agent": {
                    "name": "agent",
                    "namespace": "kube-system",
                    "desired_number_scheduled": 3,
                    "number_available": 2,
                },
            },
            "nodes": {},
            "pods": {},
        }
        result = _build_alerts(data)
        assert len(result["degraded_workloads"]) == 1
        assert result["degraded_workloads"][0]["type"] == "DaemonSet"

    def test_detects_failed_pods(self, sample_coordinator_data):
        """Test detects pods in Failed or Unknown phase."""
        result = _build_alerts(sample_coordinator_data)
        assert len(result["failed_pods"]) == 1
        assert result["failed_pods"][0]["name"] == "api-xyz789"
        assert result["failed_pods"][0]["phase"] == "Failed"

    def test_detects_unknown_phase_pods(self):
        """Test detects pods in Unknown phase."""
        data = {
            "deployments": {},
            "statefulsets": {},
            "daemonsets": {},
            "nodes": {},
            "pods": {
                "default_stuck-pod": {
                    "name": "stuck-pod",
                    "namespace": "default",
                    "phase": "Unknown",
                },
            },
        }
        result = _build_alerts(data)
        assert len(result["failed_pods"]) == 1
        assert result["failed_pods"][0]["phase"] == "Unknown"

    def test_no_alerts_for_healthy_cluster(self):
        """Test no alerts when everything is healthy."""
        data = {
            "deployments": {
                "app": {
                    "name": "app",
                    "namespace": "default",
                    "replicas": 2,
                    "available_replicas": 2,
                },
            },
            "statefulsets": {},
            "daemonsets": {},
            "nodes": {
                "node-1": {
                    "name": "node-1",
                    "memory_pressure": False,
                    "disk_pressure": False,
                    "pid_pressure": False,
                    "network_unavailable": False,
                },
            },
            "pods": {
                "default_app-1": {
                    "name": "app-1",
                    "namespace": "default",
                    "phase": "Running",
                },
            },
        }
        result = _build_alerts(data)
        assert result["nodes_with_pressure"] == []
        assert result["degraded_workloads"] == []
        assert result["failed_pods"] == []

    def test_skips_scaled_down_deployments(self):
        """Test does not alert on intentionally scaled-down deployments."""
        data = {
            "deployments": {
                "app": {
                    "name": "app",
                    "namespace": "default",
                    "replicas": 0,
                    "available_replicas": 0,
                },
            },
            "statefulsets": {},
            "daemonsets": {},
            "nodes": {},
            "pods": {},
        }
        result = _build_alerts(data)
        assert result["degraded_workloads"] == []

    def test_multiple_node_conditions(self):
        """Test node with multiple pressure conditions."""
        data = {
            "deployments": {},
            "statefulsets": {},
            "daemonsets": {},
            "nodes": {
                "bad-node": {
                    "name": "bad-node",
                    "memory_pressure": True,
                    "disk_pressure": True,
                    "pid_pressure": False,
                    "network_unavailable": False,
                },
            },
            "pods": {},
        }
        result = _build_alerts(data)
        assert len(result["nodes_with_pressure"]) == 1
        conditions = result["nodes_with_pressure"][0]["conditions"]
        assert "memory_pressure" in conditions
        assert "disk_pressure" in conditions
        assert len(conditions) == 2


class TestWebsocketNodesList:
    """Tests for the kubernetes/nodes/list command logic."""

    def test_returns_empty_when_no_domain_data(self, mock_hass):
        """Test returns empty clusters list when no DOMAIN data."""
        mock_hass.data = {}
        result = _get_nodes_list_data(mock_hass)
        assert result == {"clusters": []}

    def test_returns_nodes_for_cluster(self, mock_hass, sample_coordinator_data):
        """Test returns all nodes for a cluster."""
        coordinator = _make_coordinator(sample_coordinator_data)
        mock_hass.data = {
            DOMAIN: {
                "entry_1": {
                    "config": {"cluster_name": "test-cluster"},
                    "coordinator": coordinator,
                },
            }
        }

        result = _get_nodes_list_data(mock_hass)

        assert len(result["clusters"]) == 1
        cluster = result["clusters"][0]
        assert cluster["entry_id"] == "entry_1"
        assert cluster["cluster_name"] == "test-cluster"
        assert len(cluster["nodes"]) == 2

        node_names = {n["name"] for n in cluster["nodes"]}
        assert node_names == {"node-1", "node-2"}

    def test_handles_none_coordinator_data(self, mock_hass):
        """Test handles coordinator with None data gracefully."""
        coordinator = _make_coordinator(None)
        mock_hass.data = {
            DOMAIN: {
                "entry_1": {
                    "config": {"cluster_name": "test"},
                    "coordinator": coordinator,
                },
            }
        }

        result = _get_nodes_list_data(mock_hass)

        cluster = result["clusters"][0]
        assert cluster["nodes"] == []

    def test_skips_metadata_keys(self, mock_hass, sample_coordinator_data):
        """Test skips panel_registered and switch_add_entities keys."""
        coordinator = _make_coordinator(sample_coordinator_data)
        mock_hass.data = {
            DOMAIN: {
                "panel_registered": True,
                "switch_add_entities": MagicMock(),
                "entry_1": {
                    "config": {"cluster_name": "test"},
                    "coordinator": coordinator,
                },
            }
        }

        result = _get_nodes_list_data(mock_hass)

        assert len(result["clusters"]) == 1

    def test_skips_entries_without_coordinator(self, mock_hass):
        """Test skips entries that have no coordinator."""
        mock_hass.data = {
            DOMAIN: {
                "entry_1": {
                    "config": {"cluster_name": "test"},
                },
            }
        }

        result = _get_nodes_list_data(mock_hass)

        assert len(result["clusters"]) == 0

    def test_multi_cluster(self, mock_hass, sample_coordinator_data):
        """Test returns nodes from multiple clusters."""
        coordinator_1 = _make_coordinator(sample_coordinator_data)
        coordinator_2 = _make_coordinator(
            {
                "nodes": {
                    "worker-1": {"name": "worker-1", "status": "Ready"},
                },
                "pods": {},
                "deployments": {},
                "statefulsets": {},
                "daemonsets": {},
                "cronjobs": {},
                "jobs": {},
                "pods_count": 0,
                "nodes_count": 1,
                "last_update": 0.0,
            }
        )
        mock_hass.data = {
            DOMAIN: {
                "entry_1": {
                    "config": {"cluster_name": "cluster-a"},
                    "coordinator": coordinator_1,
                },
                "entry_2": {
                    "config": {"cluster_name": "cluster-b"},
                    "coordinator": coordinator_2,
                },
            }
        }

        result = _get_nodes_list_data(mock_hass)

        assert len(result["clusters"]) == 2
        total_nodes = sum(len(c["nodes"]) for c in result["clusters"])
        assert total_nodes == 3


class TestWebsocketPodsList:
    """Tests for the kubernetes/pods/list command logic."""

    def test_returns_empty_when_no_domain_data(self, mock_hass):
        """Test returns empty clusters list when no DOMAIN data."""
        mock_hass.data = {}
        result = _get_pods_list_data(mock_hass)
        assert result == {"clusters": []}

    def test_returns_pods_for_cluster(self, mock_hass, sample_coordinator_data):
        """Test returns all pods for a cluster."""
        coordinator = _make_coordinator(sample_coordinator_data)
        mock_hass.data = {
            DOMAIN: {
                "entry_1": {
                    "config": {"cluster_name": "test-cluster"},
                    "coordinator": coordinator,
                },
            }
        }

        result = _get_pods_list_data(mock_hass)

        assert len(result["clusters"]) == 1
        cluster = result["clusters"][0]
        assert cluster["entry_id"] == "entry_1"
        assert cluster["cluster_name"] == "test-cluster"
        assert len(cluster["pods"]) == 3

        pod_names = {p["name"] for p in cluster["pods"]}
        assert pod_names == {"nginx-abc123", "nginx-def456", "api-xyz789"}

    def test_handles_none_coordinator_data(self, mock_hass):
        """Test handles coordinator with None data gracefully."""
        coordinator = _make_coordinator(None)
        mock_hass.data = {
            DOMAIN: {
                "entry_1": {
                    "config": {"cluster_name": "test"},
                    "coordinator": coordinator,
                },
            }
        }

        result = _get_pods_list_data(mock_hass)

        cluster = result["clusters"][0]
        assert cluster["pods"] == []

    def test_skips_metadata_keys(self, mock_hass, sample_coordinator_data):
        """Test skips panel_registered and switch_add_entities keys."""
        coordinator = _make_coordinator(sample_coordinator_data)
        mock_hass.data = {
            DOMAIN: {
                "panel_registered": True,
                "entry_1": {
                    "config": {"cluster_name": "test"},
                    "coordinator": coordinator,
                },
            }
        }

        result = _get_pods_list_data(mock_hass)

        assert len(result["clusters"]) == 1

    def test_skips_entries_without_coordinator(self, mock_hass):
        """Test skips entries that have no coordinator."""
        mock_hass.data = {
            DOMAIN: {
                "entry_1": {
                    "config": {"cluster_name": "test"},
                },
            }
        }

        result = _get_pods_list_data(mock_hass)

        assert len(result["clusters"]) == 0

    def test_multi_cluster(self, mock_hass, sample_coordinator_data):
        """Test returns pods from multiple clusters."""
        coordinator_1 = _make_coordinator(sample_coordinator_data)
        coordinator_2 = _make_coordinator(
            {
                "nodes": {},
                "pods": {
                    "staging_app-1": {
                        "name": "app-1",
                        "namespace": "staging",
                        "phase": "Running",
                    },
                },
                "deployments": {},
                "statefulsets": {},
                "daemonsets": {},
                "cronjobs": {},
                "jobs": {},
                "pods_count": 1,
                "nodes_count": 0,
                "last_update": 0.0,
            }
        )
        mock_hass.data = {
            DOMAIN: {
                "entry_1": {
                    "config": {"cluster_name": "cluster-a"},
                    "coordinator": coordinator_1,
                },
                "entry_2": {
                    "config": {"cluster_name": "cluster-b"},
                    "coordinator": coordinator_2,
                },
            }
        }

        result = _get_pods_list_data(mock_hass)

        assert len(result["clusters"]) == 2
        total_pods = sum(len(c["pods"]) for c in result["clusters"])
        assert total_pods == 4

    def test_pods_include_all_fields(self, mock_hass):
        """Test that pod data includes expected fields."""
        pod_data = {
            "name": "web-abc",
            "namespace": "prod",
            "phase": "Running",
            "ready_containers": 1,
            "total_containers": 1,
            "restart_count": 3,
            "node_name": "worker-1",
            "pod_ip": "10.0.0.5",
            "creation_timestamp": "2024-01-01T00:00:00Z",
            "owner_kind": "ReplicaSet",
            "owner_name": "web-abc123",
            "uid": "test-uid",
            "labels": {},
        }
        coordinator = _make_coordinator(
            {
                "pods": {"prod_web-abc": pod_data},
                "nodes": {},
                "deployments": {},
                "statefulsets": {},
                "daemonsets": {},
                "cronjobs": {},
                "jobs": {},
                "pods_count": 1,
                "nodes_count": 0,
                "last_update": 0.0,
            }
        )
        mock_hass.data = {
            DOMAIN: {
                "entry_1": {
                    "config": {"cluster_name": "test"},
                    "coordinator": coordinator,
                },
            }
        }

        result = _get_pods_list_data(mock_hass)
        pod = result["clusters"][0]["pods"][0]
        assert pod["name"] == "web-abc"
        assert pod["namespace"] == "prod"
        assert pod["phase"] == "Running"
        assert pod["ready_containers"] == 1
        assert pod["restart_count"] == 3
        assert pod["node_name"] == "worker-1"
        assert pod["pod_ip"] == "10.0.0.5"
        assert pod["owner_kind"] == "ReplicaSet"


class TestWebsocketWorkloadsList:
    """Tests for the kubernetes/workloads/list command logic."""

    def test_returns_empty_when_no_domain_data(self, mock_hass):
        """Test returns empty clusters list when no DOMAIN data."""
        mock_hass.data = {}
        result = _get_workloads_list_data(mock_hass)
        assert result == {"clusters": []}

    def test_returns_workloads_for_cluster(self, mock_hass, sample_coordinator_data):
        """Test returns all workload types for a cluster."""
        coordinator = _make_coordinator(sample_coordinator_data)
        mock_hass.data = {
            DOMAIN: {
                "entry_1": {
                    "config": {"cluster_name": "test-cluster"},
                    "coordinator": coordinator,
                },
            }
        }

        result = _get_workloads_list_data(mock_hass)

        assert len(result["clusters"]) == 1
        cluster = result["clusters"][0]
        assert cluster["entry_id"] == "entry_1"
        assert cluster["cluster_name"] == "test-cluster"
        assert len(cluster["deployments"]) == 2
        assert len(cluster["statefulsets"]) == 1
        assert len(cluster["daemonsets"]) == 1
        assert len(cluster["cronjobs"]) == 1
        assert len(cluster["jobs"]) == 1

    def test_handles_none_coordinator_data(self, mock_hass):
        """Test handles coordinator with None data gracefully."""
        coordinator = _make_coordinator(None)
        mock_hass.data = {
            DOMAIN: {
                "entry_1": {
                    "config": {"cluster_name": "test"},
                    "coordinator": coordinator,
                },
            }
        }

        result = _get_workloads_list_data(mock_hass)

        cluster = result["clusters"][0]
        assert cluster["deployments"] == []
        assert cluster["statefulsets"] == []
        assert cluster["daemonsets"] == []
        assert cluster["cronjobs"] == []
        assert cluster["jobs"] == []

    def test_skips_metadata_keys(self, mock_hass, sample_coordinator_data):
        """Test skips panel_registered and switch_add_entities keys."""
        coordinator = _make_coordinator(sample_coordinator_data)
        mock_hass.data = {
            DOMAIN: {
                "panel_registered": True,
                "switch_add_entities": MagicMock(),
                "entry_1": {
                    "config": {"cluster_name": "test"},
                    "coordinator": coordinator,
                },
            }
        }

        result = _get_workloads_list_data(mock_hass)

        assert len(result["clusters"]) == 1

    def test_skips_entries_without_coordinator(self, mock_hass):
        """Test skips entries that have no coordinator."""
        mock_hass.data = {
            DOMAIN: {
                "entry_1": {
                    "config": {"cluster_name": "test"},
                },
            }
        }

        result = _get_workloads_list_data(mock_hass)

        assert len(result["clusters"]) == 0

    def test_multi_cluster(self, mock_hass, sample_coordinator_data):
        """Test returns workloads from multiple clusters."""
        coordinator_1 = _make_coordinator(sample_coordinator_data)
        coordinator_2 = _make_coordinator(
            {
                "nodes": {},
                "pods": {},
                "deployments": {
                    "web": {
                        "name": "web",
                        "namespace": "staging",
                        "replicas": 1,
                        "available_replicas": 1,
                        "ready_replicas": 1,
                        "is_running": True,
                    },
                },
                "statefulsets": {},
                "daemonsets": {},
                "cronjobs": {},
                "jobs": {},
                "pods_count": 0,
                "nodes_count": 0,
                "last_update": 0.0,
            }
        )
        mock_hass.data = {
            DOMAIN: {
                "entry_1": {
                    "config": {"cluster_name": "cluster-a"},
                    "coordinator": coordinator_1,
                },
                "entry_2": {
                    "config": {"cluster_name": "cluster-b"},
                    "coordinator": coordinator_2,
                },
            }
        }

        result = _get_workloads_list_data(mock_hass)

        assert len(result["clusters"]) == 2
        total_deploys = sum(len(c["deployments"]) for c in result["clusters"])
        assert total_deploys == 3

    def test_deployment_fields(self, mock_hass, sample_coordinator_data):
        """Test that deployment data includes expected fields."""
        coordinator = _make_coordinator(sample_coordinator_data)
        mock_hass.data = {
            DOMAIN: {
                "entry_1": {
                    "config": {"cluster_name": "test"},
                    "coordinator": coordinator,
                },
            }
        }

        result = _get_workloads_list_data(mock_hass)
        deploys = result["clusters"][0]["deployments"]
        nginx = next(d for d in deploys if d["name"] == "nginx")
        assert nginx["namespace"] == "default"
        assert nginx["replicas"] == 3
        assert nginx["available_replicas"] == 3
        assert nginx["is_running"] is True

    def test_cronjob_fields(self, mock_hass):
        """Test that cronjob data includes expected fields."""
        cronjob_data = {
            "name": "nightly-backup",
            "namespace": "prod",
            "schedule": "0 2 * * *",
            "suspend": False,
            "last_schedule_time": "2024-01-01T02:00:00Z",
            "next_schedule_time": "2024-01-02T02:00:00Z",
            "active_jobs_count": 0,
            "successful_jobs_history_limit": 3,
            "failed_jobs_history_limit": 1,
            "concurrency_policy": "Forbid",
            "uid": "cj-uid",
            "creation_timestamp": "2023-01-01T00:00:00Z",
        }
        coordinator = _make_coordinator(
            {
                "pods": {},
                "nodes": {},
                "deployments": {},
                "statefulsets": {},
                "daemonsets": {},
                "cronjobs": {"nightly-backup": cronjob_data},
                "jobs": {},
                "pods_count": 0,
                "nodes_count": 0,
                "last_update": 0.0,
            }
        )
        mock_hass.data = {
            DOMAIN: {
                "entry_1": {
                    "config": {"cluster_name": "test"},
                    "coordinator": coordinator,
                },
            }
        }

        result = _get_workloads_list_data(mock_hass)
        cj = result["clusters"][0]["cronjobs"][0]
        assert cj["name"] == "nightly-backup"
        assert cj["schedule"] == "0 2 * * *"
        assert cj["suspend"] is False
        assert cj["active_jobs_count"] == 0
        assert cj["concurrency_policy"] == "Forbid"


class TestWebsocketConfigList:
    """Tests for the kubernetes/config/list command logic."""

    def test_returns_empty_when_no_domain_data(self, mock_hass):
        """Test returns empty entries list when no DOMAIN data."""
        mock_hass.data = {}
        result = _get_config_list_data(mock_hass)
        assert result == {"entries": []}

    def test_returns_config_for_entry(self, mock_hass, sample_coordinator_data):
        """Test returns sanitized config for a cluster entry."""
        coordinator = _make_coordinator(sample_coordinator_data)
        mock_hass.data = {
            DOMAIN: {
                "entry_1": {
                    "config": {
                        "cluster_name": "test-cluster",
                        "host": "192.168.1.100",
                        "port": 6443,
                        "api_token": "secret-token-should-not-appear",
                        "verify_ssl": True,
                        "monitor_all_namespaces": False,
                        "namespace": ["default", "production"],
                        "device_grouping_mode": "namespace",
                        "switch_update_interval": 60,
                        "scale_verification_timeout": 30,
                        "scale_cooldown": 10,
                    },
                    "coordinator": coordinator,
                },
            }
        }

        result = _get_config_list_data(mock_hass)

        assert len(result["entries"]) == 1
        entry = result["entries"][0]
        assert entry["entry_id"] == "entry_1"
        assert entry["cluster_name"] == "test-cluster"
        assert entry["host"] == "192.168.1.100"
        assert entry["port"] == 6443
        assert entry["verify_ssl"] is True
        assert entry["monitor_all_namespaces"] is False
        assert entry["namespaces"] == ["default", "production"]
        assert entry["device_grouping_mode"] == "namespace"
        assert entry["switch_update_interval"] == 60
        assert entry["scale_verification_timeout"] == 30
        assert entry["scale_cooldown"] == 10
        assert entry["watch_enabled"] is False
        assert entry["healthy"] is True
        # Ensure secret is NOT exposed
        assert "api_token" not in entry

    def test_watch_enabled_from_options(self, mock_hass, sample_coordinator_data):
        """Test watch_enabled reflects config entry options."""
        coordinator = _make_coordinator(
            sample_coordinator_data, options={"enable_watch": True}
        )
        mock_hass.data = {
            DOMAIN: {
                "entry_1": {
                    "config": {"cluster_name": "test"},
                    "coordinator": coordinator,
                },
            }
        }

        result = _get_config_list_data(mock_hass)
        assert result["entries"][0]["watch_enabled"] is True

    def test_namespace_string_converted_to_list(
        self, mock_hass, sample_coordinator_data
    ):
        """Test namespace string is converted to a list."""
        coordinator = _make_coordinator(sample_coordinator_data)
        mock_hass.data = {
            DOMAIN: {
                "entry_1": {
                    "config": {
                        "cluster_name": "test",
                        "namespace": "default",
                    },
                    "coordinator": coordinator,
                },
            }
        }

        result = _get_config_list_data(mock_hass)
        assert result["entries"][0]["namespaces"] == ["default"]

    def test_defaults_applied_for_missing_config(
        self, mock_hass, sample_coordinator_data
    ):
        """Test default values are used when config keys are missing."""
        coordinator = _make_coordinator(sample_coordinator_data)
        mock_hass.data = {
            DOMAIN: {
                "entry_1": {
                    "config": {},
                    "coordinator": coordinator,
                },
            }
        }

        result = _get_config_list_data(mock_hass)
        entry = result["entries"][0]
        assert entry["cluster_name"] == "default"
        assert entry["host"] == ""
        assert entry["port"] == 6443
        assert entry["verify_ssl"] is True
        assert entry["monitor_all_namespaces"] is True
        assert entry["namespaces"] == []
        assert entry["device_grouping_mode"] == "namespace"
        assert entry["switch_update_interval"] == 60
        assert entry["scale_verification_timeout"] == 30
        assert entry["scale_cooldown"] == 10

    def test_skips_metadata_keys(self, mock_hass, sample_coordinator_data):
        """Test skips panel_registered and switch_add_entities keys."""
        coordinator = _make_coordinator(sample_coordinator_data)
        mock_hass.data = {
            DOMAIN: {
                "panel_registered": True,
                "switch_add_entities": MagicMock(),
                "entry_1": {
                    "config": {"cluster_name": "test"},
                    "coordinator": coordinator,
                },
            }
        }

        result = _get_config_list_data(mock_hass)
        assert len(result["entries"]) == 1

    def test_skips_entries_without_coordinator(self, mock_hass):
        """Test skips entries that have no coordinator."""
        mock_hass.data = {
            DOMAIN: {
                "entry_1": {
                    "config": {"cluster_name": "test"},
                },
            }
        }

        result = _get_config_list_data(mock_hass)
        assert len(result["entries"]) == 0


class TestBuildNamespaceBreakdownEdgeCases:
    """Additional edge-case tests for _build_namespace_breakdown."""

    def test_missing_namespace_field_defaults_to_unknown(self):
        """Test resources without a namespace field are grouped under 'unknown'."""
        data = {
            "pods": {
                "p1": {"name": "p1"},  # no namespace key
            },
            "deployments": {
                "d1": {"name": "d1"},  # no namespace key
            },
            "statefulsets": {},
            "daemonsets": {},
            "cronjobs": {},
            "jobs": {},
        }
        result = _build_namespace_breakdown(data)
        assert "unknown" in result
        assert result["unknown"]["pods"] == 1
        assert result["unknown"]["deployments"] == 1

    def test_all_resource_types_missing_namespace(self):
        """Test all six resource types default to 'unknown' when namespace is absent."""
        data = {
            "pods": {"p1": {"name": "p1"}},
            "deployments": {"d1": {"name": "d1"}},
            "statefulsets": {"s1": {"name": "s1"}},
            "daemonsets": {"ds1": {"name": "ds1"}},
            "cronjobs": {"cj1": {"name": "cj1"}},
            "jobs": {"j1": {"name": "j1"}},
        }
        result = _build_namespace_breakdown(data)
        assert len(result) == 1
        assert result["unknown"]["pods"] == 1
        assert result["unknown"]["deployments"] == 1
        assert result["unknown"]["statefulsets"] == 1
        assert result["unknown"]["daemonsets"] == 1
        assert result["unknown"]["cronjobs"] == 1
        assert result["unknown"]["jobs"] == 1

    def test_duplicate_namespaces_across_resource_types(self):
        """Test same namespace across multiple resource types accumulates correctly."""
        data = {
            "pods": {
                "p1": {"name": "p1", "namespace": "shared"},
                "p2": {"name": "p2", "namespace": "shared"},
            },
            "deployments": {
                "d1": {"name": "d1", "namespace": "shared"},
            },
            "statefulsets": {
                "s1": {"name": "s1", "namespace": "shared"},
            },
            "daemonsets": {
                "ds1": {"name": "ds1", "namespace": "shared"},
            },
            "cronjobs": {
                "cj1": {"name": "cj1", "namespace": "shared"},
                "cj2": {"name": "cj2", "namespace": "shared"},
            },
            "jobs": {
                "j1": {"name": "j1", "namespace": "shared"},
            },
        }
        result = _build_namespace_breakdown(data)
        assert len(result) == 1
        assert result["shared"]["pods"] == 2
        assert result["shared"]["deployments"] == 1
        assert result["shared"]["statefulsets"] == 1
        assert result["shared"]["daemonsets"] == 1
        assert result["shared"]["cronjobs"] == 2
        assert result["shared"]["jobs"] == 1

    def test_only_some_resource_types_present(self):
        """Test data dict with only pods and jobs keys."""
        data = {
            "pods": {
                "p1": {"name": "p1", "namespace": "ns-a"},
            },
            "jobs": {
                "j1": {"name": "j1", "namespace": "ns-b"},
            },
        }
        result = _build_namespace_breakdown(data)
        assert result["ns-a"]["pods"] == 1
        # ns-a should have zero for other types since setdefault initializes them
        assert result["ns-a"]["deployments"] == 0
        assert result["ns-b"]["jobs"] == 1
        assert result["ns-b"]["pods"] == 0

    def test_mixed_known_and_unknown_namespaces(self):
        """Test mix of resources with and without namespace field."""
        data = {
            "pods": {
                "p1": {"name": "p1", "namespace": "real-ns"},
                "p2": {"name": "p2"},  # missing namespace
            },
            "deployments": {},
            "statefulsets": {},
            "daemonsets": {},
            "cronjobs": {},
            "jobs": {},
        }
        result = _build_namespace_breakdown(data)
        assert result["real-ns"]["pods"] == 1
        assert result["unknown"]["pods"] == 1

    def test_empty_resource_dicts(self):
        """Test all resource type dicts are present but empty."""
        data = {
            "pods": {},
            "deployments": {},
            "statefulsets": {},
            "daemonsets": {},
            "cronjobs": {},
            "jobs": {},
        }
        result = _build_namespace_breakdown(data)
        assert result == {}


class TestBuildAlertsEdgeCases:
    """Additional edge-case tests for _build_alerts."""

    def test_node_with_all_pressure_conditions_true(self):
        """Test node with all four pressure conditions set to True."""
        data = {
            "deployments": {},
            "statefulsets": {},
            "daemonsets": {},
            "nodes": {
                "critical-node": {
                    "name": "critical-node",
                    "memory_pressure": True,
                    "disk_pressure": True,
                    "pid_pressure": True,
                    "network_unavailable": True,
                },
            },
            "pods": {},
        }
        result = _build_alerts(data)
        assert len(result["nodes_with_pressure"]) == 1
        conditions = result["nodes_with_pressure"][0]["conditions"]
        assert len(conditions) == 4
        assert "memory_pressure" in conditions
        assert "disk_pressure" in conditions
        assert "pid_pressure" in conditions
        assert "network_unavailable" in conditions

    def test_node_missing_pressure_keys_entirely(self):
        """Test node dict without any pressure keys does not appear in alerts."""
        data = {
            "deployments": {},
            "statefulsets": {},
            "daemonsets": {},
            "nodes": {
                "bare-node": {
                    "name": "bare-node",
                    "status": "Ready",
                    # no pressure keys at all
                },
            },
            "pods": {},
        }
        result = _build_alerts(data)
        assert result["nodes_with_pressure"] == []

    def test_node_pressure_keys_with_none_values(self):
        """Test node pressure keys set to None are treated as falsy."""
        data = {
            "deployments": {},
            "statefulsets": {},
            "daemonsets": {},
            "nodes": {
                "none-node": {
                    "name": "none-node",
                    "memory_pressure": None,
                    "disk_pressure": None,
                    "pid_pressure": None,
                    "network_unavailable": None,
                },
            },
            "pods": {},
        }
        result = _build_alerts(data)
        assert result["nodes_with_pressure"] == []

    def test_node_pressure_keys_with_false_values(self):
        """Test node with all pressure conditions explicitly False."""
        data = {
            "deployments": {},
            "statefulsets": {},
            "daemonsets": {},
            "nodes": {
                "ok-node": {
                    "name": "ok-node",
                    "memory_pressure": False,
                    "disk_pressure": False,
                    "pid_pressure": False,
                    "network_unavailable": False,
                },
            },
            "pods": {},
        }
        result = _build_alerts(data)
        assert result["nodes_with_pressure"] == []

    def test_multiple_nodes_with_different_pressure_conditions(self):
        """Test multiple nodes each with different pressure conditions."""
        data = {
            "deployments": {},
            "statefulsets": {},
            "daemonsets": {},
            "nodes": {
                "node-a": {
                    "name": "node-a",
                    "memory_pressure": True,
                    "disk_pressure": False,
                    "pid_pressure": False,
                    "network_unavailable": False,
                },
                "node-b": {
                    "name": "node-b",
                    "memory_pressure": False,
                    "disk_pressure": True,
                    "pid_pressure": True,
                    "network_unavailable": False,
                },
                "node-c": {
                    "name": "node-c",
                    "memory_pressure": False,
                    "disk_pressure": False,
                    "pid_pressure": False,
                    "network_unavailable": False,
                },
            },
            "pods": {},
        }
        result = _build_alerts(data)
        assert len(result["nodes_with_pressure"]) == 2
        names = {n["name"] for n in result["nodes_with_pressure"]}
        assert names == {"node-a", "node-b"}

    def test_deployment_with_none_available_replicas(self):
        """Test deployment where available_replicas is None (not yet scheduled)."""
        data = {
            "deployments": {
                "new-deploy": {
                    "name": "new-deploy",
                    "namespace": "default",
                    "replicas": 3,
                    "available_replicas": None,
                },
            },
            "statefulsets": {},
            "daemonsets": {},
            "nodes": {},
            "pods": {},
        }
        result = _build_alerts(data)
        assert len(result["degraded_workloads"]) == 1
        assert result["degraded_workloads"][0]["name"] == "new-deploy"
        assert result["degraded_workloads"][0]["ready"] == 0
        assert result["degraded_workloads"][0]["desired"] == 3

    def test_statefulset_with_none_ready_replicas(self):
        """Test statefulset where ready_replicas is None."""
        data = {
            "deployments": {},
            "statefulsets": {
                "new-sts": {
                    "name": "new-sts",
                    "namespace": "default",
                    "replicas": 2,
                    "ready_replicas": None,
                },
            },
            "daemonsets": {},
            "nodes": {},
            "pods": {},
        }
        result = _build_alerts(data)
        assert len(result["degraded_workloads"]) == 1
        assert result["degraded_workloads"][0]["type"] == "StatefulSet"
        assert result["degraded_workloads"][0]["ready"] == 0
        assert result["degraded_workloads"][0]["desired"] == 2

    def test_daemonset_with_none_number_available(self):
        """Test daemonset where number_available is None."""
        data = {
            "deployments": {},
            "statefulsets": {},
            "daemonsets": {
                "new-ds": {
                    "name": "new-ds",
                    "namespace": "kube-system",
                    "desired_number_scheduled": 5,
                    "number_available": None,
                },
            },
            "nodes": {},
            "pods": {},
        }
        result = _build_alerts(data)
        assert len(result["degraded_workloads"]) == 1
        assert result["degraded_workloads"][0]["type"] == "DaemonSet"
        assert result["degraded_workloads"][0]["ready"] == 0
        assert result["degraded_workloads"][0]["desired"] == 5

    def test_deployment_missing_replicas_key(self):
        """Test deployment with missing replicas key defaults to 0 (not degraded)."""
        data = {
            "deployments": {
                "bare-deploy": {
                    "name": "bare-deploy",
                    "namespace": "default",
                    # no replicas key
                },
            },
            "statefulsets": {},
            "daemonsets": {},
            "nodes": {},
            "pods": {},
        }
        result = _build_alerts(data)
        # replicas defaults to 0, so desired=0, condition desired>0 is False
        assert result["degraded_workloads"] == []

    def test_statefulset_scaled_to_zero_not_degraded(self):
        """Test statefulset with replicas=0 is not reported as degraded."""
        data = {
            "deployments": {},
            "statefulsets": {
                "off-sts": {
                    "name": "off-sts",
                    "namespace": "default",
                    "replicas": 0,
                    "ready_replicas": 0,
                },
            },
            "daemonsets": {},
            "nodes": {},
            "pods": {},
        }
        result = _build_alerts(data)
        assert result["degraded_workloads"] == []

    def test_daemonset_scaled_to_zero_not_degraded(self):
        """Test daemonset with desired_number_scheduled=0 is not degraded."""
        data = {
            "deployments": {},
            "statefulsets": {},
            "daemonsets": {
                "off-ds": {
                    "name": "off-ds",
                    "namespace": "kube-system",
                    "desired_number_scheduled": 0,
                    "number_available": 0,
                },
            },
            "nodes": {},
            "pods": {},
        }
        result = _build_alerts(data)
        assert result["degraded_workloads"] == []

    def test_pod_with_missing_phase_not_failed(self):
        """Test pod missing the phase key is not treated as failed."""
        data = {
            "deployments": {},
            "statefulsets": {},
            "daemonsets": {},
            "nodes": {},
            "pods": {
                "p1": {
                    "name": "no-phase-pod",
                    "namespace": "default",
                    # no phase key
                },
            },
        }
        result = _build_alerts(data)
        assert result["failed_pods"] == []

    def test_pod_with_empty_string_phase_not_failed(self):
        """Test pod with empty string phase is not treated as failed."""
        data = {
            "deployments": {},
            "statefulsets": {},
            "daemonsets": {},
            "nodes": {},
            "pods": {
                "p1": {
                    "name": "empty-phase-pod",
                    "namespace": "default",
                    "phase": "",
                },
            },
        }
        result = _build_alerts(data)
        assert result["failed_pods"] == []

    def test_pod_pending_and_succeeded_not_failed(self):
        """Test pods in Pending and Succeeded phase are not reported as failed."""
        data = {
            "deployments": {},
            "statefulsets": {},
            "daemonsets": {},
            "nodes": {},
            "pods": {
                "p1": {
                    "name": "pending-pod",
                    "namespace": "default",
                    "phase": "Pending",
                },
                "p2": {
                    "name": "done-pod",
                    "namespace": "default",
                    "phase": "Succeeded",
                },
            },
        }
        result = _build_alerts(data)
        assert result["failed_pods"] == []

    def test_multiple_failed_and_unknown_pods(self):
        """Test multiple pods in Failed and Unknown phases all appear."""
        data = {
            "deployments": {},
            "statefulsets": {},
            "daemonsets": {},
            "nodes": {},
            "pods": {
                "p1": {
                    "name": "fail-1",
                    "namespace": "default",
                    "phase": "Failed",
                },
                "p2": {
                    "name": "fail-2",
                    "namespace": "prod",
                    "phase": "Failed",
                },
                "p3": {
                    "name": "unknown-1",
                    "namespace": "default",
                    "phase": "Unknown",
                },
            },
        }
        result = _build_alerts(data)
        assert len(result["failed_pods"]) == 3
        names = {p["name"] for p in result["failed_pods"]}
        assert names == {"fail-1", "fail-2", "unknown-1"}

    def test_pod_missing_name_field(self):
        """Test failed pod with missing name field defaults to empty string."""
        data = {
            "deployments": {},
            "statefulsets": {},
            "daemonsets": {},
            "nodes": {},
            "pods": {
                "p1": {
                    "namespace": "default",
                    "phase": "Failed",
                    # no name key
                },
            },
        }
        result = _build_alerts(data)
        assert len(result["failed_pods"]) == 1
        assert result["failed_pods"][0]["name"] == ""

    def test_degraded_workload_missing_namespace_defaults_to_unknown(self):
        """Test degraded workloads without namespace default to 'unknown'."""
        data = {
            "deployments": {
                "no-ns-deploy": {
                    "name": "no-ns-deploy",
                    "replicas": 2,
                    "available_replicas": 1,
                    # no namespace key
                },
            },
            "statefulsets": {
                "no-ns-sts": {
                    "name": "no-ns-sts",
                    "replicas": 3,
                    "ready_replicas": 0,
                    # no namespace key
                },
            },
            "daemonsets": {
                "no-ns-ds": {
                    "name": "no-ns-ds",
                    "desired_number_scheduled": 2,
                    "number_available": 1,
                    # no namespace key
                },
            },
            "nodes": {},
            "pods": {},
        }
        result = _build_alerts(data)
        assert len(result["degraded_workloads"]) == 3
        for workload in result["degraded_workloads"]:
            assert workload["namespace"] == "unknown"

    def test_mixed_healthy_and_degraded_workloads(self):
        """Test only degraded workloads appear, healthy ones are excluded."""
        data = {
            "deployments": {
                "healthy-deploy": {
                    "name": "healthy-deploy",
                    "namespace": "default",
                    "replicas": 2,
                    "available_replicas": 2,
                },
                "sick-deploy": {
                    "name": "sick-deploy",
                    "namespace": "default",
                    "replicas": 3,
                    "available_replicas": 1,
                },
            },
            "statefulsets": {
                "healthy-sts": {
                    "name": "healthy-sts",
                    "namespace": "default",
                    "replicas": 1,
                    "ready_replicas": 1,
                },
            },
            "daemonsets": {
                "healthy-ds": {
                    "name": "healthy-ds",
                    "namespace": "kube-system",
                    "desired_number_scheduled": 3,
                    "number_available": 3,
                },
            },
            "nodes": {},
            "pods": {},
        }
        result = _build_alerts(data)
        assert len(result["degraded_workloads"]) == 1
        assert result["degraded_workloads"][0]["name"] == "sick-deploy"


class TestHandlersEdgeCases:
    """Edge-case tests for WebSocket command handler data functions."""

    def test_overview_skips_non_dict_entry_data(self, mock_hass):
        """Test _get_cluster_overview_data skips non-dict entry values."""
        mock_hass.data = {
            DOMAIN: {
                "entry_1": "not_a_dict",
                "entry_2": 42,
                "entry_3": None,
            }
        }
        result = _get_cluster_overview_data(mock_hass)
        assert result == {"clusters": []}

    def test_nodes_list_skips_non_dict_entry_data(self, mock_hass):
        """Test _get_nodes_list_data skips non-dict entry values."""
        mock_hass.data = {
            DOMAIN: {
                "entry_1": "string_value",
            }
        }
        result = _get_nodes_list_data(mock_hass)
        assert result == {"clusters": []}

    def test_pods_list_skips_non_dict_entry_data(self, mock_hass):
        """Test _get_pods_list_data skips non-dict entry values."""
        mock_hass.data = {
            DOMAIN: {
                "entry_1": 123,
            }
        }
        result = _get_pods_list_data(mock_hass)
        assert result == {"clusters": []}

    def test_workloads_list_skips_non_dict_entry_data(self, mock_hass):
        """Test _get_workloads_list_data skips non-dict entry values."""
        mock_hass.data = {
            DOMAIN: {
                "entry_1": ["a", "list"],
            }
        }
        result = _get_workloads_list_data(mock_hass)
        assert result == {"clusters": []}

    def test_config_list_skips_non_dict_entry_data(self, mock_hass):
        """Test _get_config_list_data skips non-dict entry values."""
        mock_hass.data = {
            DOMAIN: {
                "entry_1": "nope",
            }
        }
        result = _get_config_list_data(mock_hass)
        assert result == {"entries": []}

    def test_overview_coordinator_with_empty_dict_data(self, mock_hass):
        """Test overview handles coordinator.data being an empty dict."""
        coordinator = _make_coordinator({})
        mock_hass.data = {
            DOMAIN: {
                "entry_1": {
                    "config": {"cluster_name": "empty"},
                    "coordinator": coordinator,
                },
            }
        }
        result = _get_cluster_overview_data(mock_hass)
        # Empty dict is truthy, so it goes through the normal path
        cluster = result["clusters"][0]
        assert cluster["counts"]["pods"] == 0
        assert cluster["counts"]["nodes"] == 0
        assert cluster["counts"]["deployments"] == 0
        assert cluster["namespaces"] == {}
        assert cluster["alerts"]["nodes_with_pressure"] == []
        assert cluster["alerts"]["degraded_workloads"] == []
        assert cluster["alerts"]["failed_pods"] == []

    def test_nodes_list_empty_nodes_dict(self, mock_hass):
        """Test nodes list returns empty list when nodes dict is empty."""
        coordinator = _make_coordinator({"nodes": {}})
        mock_hass.data = {
            DOMAIN: {
                "entry_1": {
                    "config": {"cluster_name": "empty"},
                    "coordinator": coordinator,
                },
            }
        }
        result = _get_nodes_list_data(mock_hass)
        assert result["clusters"][0]["nodes"] == []

    def test_pods_list_empty_pods_dict(self, mock_hass):
        """Test pods list returns empty list when pods dict is empty."""
        coordinator = _make_coordinator({"pods": {}})
        mock_hass.data = {
            DOMAIN: {
                "entry_1": {
                    "config": {"cluster_name": "empty"},
                    "coordinator": coordinator,
                },
            }
        }
        result = _get_pods_list_data(mock_hass)
        assert result["clusters"][0]["pods"] == []

    def test_workloads_list_empty_data(self, mock_hass):
        """Test workloads list with empty coordinator data dict."""
        coordinator = _make_coordinator({})
        mock_hass.data = {
            DOMAIN: {
                "entry_1": {
                    "config": {"cluster_name": "empty"},
                    "coordinator": coordinator,
                },
            }
        }
        result = _get_workloads_list_data(mock_hass)
        cluster = result["clusters"][0]
        assert cluster["deployments"] == []
        assert cluster["statefulsets"] == []
        assert cluster["daemonsets"] == []
        assert cluster["cronjobs"] == []
        assert cluster["jobs"] == []

    def test_overview_missing_config_key(self, mock_hass):
        """Test overview when entry_data has no 'config' key."""
        coordinator = _make_coordinator(None)
        mock_hass.data = {
            DOMAIN: {
                "entry_1": {
                    "coordinator": coordinator,
                    # no "config" key
                },
            }
        }
        result = _get_cluster_overview_data(mock_hass)
        cluster = result["clusters"][0]
        # config.get() on empty dict returns defaults
        assert cluster["cluster_name"] == "default"

    def test_nodes_list_missing_config_key(self, mock_hass):
        """Test nodes list uses default cluster name when config is missing."""
        coordinator = _make_coordinator({"nodes": {"n1": {"name": "n1"}}})
        mock_hass.data = {
            DOMAIN: {
                "entry_1": {
                    "coordinator": coordinator,
                },
            }
        }
        result = _get_nodes_list_data(mock_hass)
        assert result["clusters"][0]["cluster_name"] == "default"

    def test_pods_list_missing_config_key(self, mock_hass):
        """Test pods list uses default cluster name when config is missing."""
        coordinator = _make_coordinator({"pods": {}})
        mock_hass.data = {
            DOMAIN: {
                "entry_1": {
                    "coordinator": coordinator,
                },
            }
        }
        result = _get_pods_list_data(mock_hass)
        assert result["clusters"][0]["cluster_name"] == "default"

    def test_workloads_list_missing_config_key(self, mock_hass):
        """Test workloads list uses default cluster name when config is missing."""
        coordinator = _make_coordinator({"deployments": {}})
        mock_hass.data = {
            DOMAIN: {
                "entry_1": {
                    "coordinator": coordinator,
                },
            }
        }
        result = _get_workloads_list_data(mock_hass)
        assert result["clusters"][0]["cluster_name"] == "default"

    def test_overview_with_coordinator_none_in_entry(self, mock_hass):
        """Test overview skips entry where coordinator key exists but is None."""
        mock_hass.data = {
            DOMAIN: {
                "entry_1": {
                    "config": {"cluster_name": "test"},
                    "coordinator": None,
                },
            }
        }
        result = _get_cluster_overview_data(mock_hass)
        assert result == {"clusters": []}


class TestConfigListEdgeCases:
    """Additional edge-case tests for _get_config_list_data."""

    def test_panel_enabled_from_options(self, mock_hass, sample_coordinator_data):
        """Test panel_enabled reflects config entry options."""
        coordinator = _make_coordinator(
            sample_coordinator_data, options={"enable_panel": False}
        )
        mock_hass.data = {
            DOMAIN: {
                "entry_1": {
                    "config": {"cluster_name": "test"},
                    "coordinator": coordinator,
                },
            }
        }
        result = _get_config_list_data(mock_hass)
        assert result["entries"][0]["panel_enabled"] is False

    def test_panel_enabled_defaults_to_true(self, mock_hass, sample_coordinator_data):
        """Test panel_enabled defaults to True when not in options."""
        coordinator = _make_coordinator(sample_coordinator_data, options={})
        mock_hass.data = {
            DOMAIN: {
                "entry_1": {
                    "config": {"cluster_name": "test"},
                    "coordinator": coordinator,
                },
            }
        }
        result = _get_config_list_data(mock_hass)
        assert result["entries"][0]["panel_enabled"] is True

    def test_healthy_false_when_coordinator_failed(
        self, mock_hass, sample_coordinator_data
    ):
        """Test healthy is False when last_update_success is False."""
        coordinator = _make_coordinator(
            sample_coordinator_data, last_update_success=False
        )
        mock_hass.data = {
            DOMAIN: {
                "entry_1": {
                    "config": {"cluster_name": "test"},
                    "coordinator": coordinator,
                },
            }
        }
        result = _get_config_list_data(mock_hass)
        assert result["entries"][0]["healthy"] is False

    def test_namespace_empty_list_when_not_in_config(
        self, mock_hass, sample_coordinator_data
    ):
        """Test namespaces is empty list when namespace key is missing from config."""
        coordinator = _make_coordinator(sample_coordinator_data)
        mock_hass.data = {
            DOMAIN: {
                "entry_1": {
                    "config": {
                        "cluster_name": "test",
                        # no "namespace" key
                    },
                    "coordinator": coordinator,
                },
            }
        }
        result = _get_config_list_data(mock_hass)
        assert result["entries"][0]["namespaces"] == []

    def test_namespace_list_stays_as_list(self, mock_hass, sample_coordinator_data):
        """Test namespace list value is passed through unchanged."""
        coordinator = _make_coordinator(sample_coordinator_data)
        mock_hass.data = {
            DOMAIN: {
                "entry_1": {
                    "config": {
                        "cluster_name": "test",
                        "namespace": ["ns-a", "ns-b", "ns-c"],
                    },
                    "coordinator": coordinator,
                },
            }
        }
        result = _get_config_list_data(mock_hass)
        assert result["entries"][0]["namespaces"] == ["ns-a", "ns-b", "ns-c"]

    def test_multiple_entries_returned(self, mock_hass, sample_coordinator_data):
        """Test multiple config entries are all returned."""
        coord_1 = _make_coordinator(sample_coordinator_data)
        coord_2 = _make_coordinator(
            sample_coordinator_data, options={"enable_watch": True}
        )
        mock_hass.data = {
            DOMAIN: {
                "entry_1": {
                    "config": {"cluster_name": "cluster-a", "host": "10.0.0.1"},
                    "coordinator": coord_1,
                },
                "entry_2": {
                    "config": {"cluster_name": "cluster-b", "host": "10.0.0.2"},
                    "coordinator": coord_2,
                },
            }
        }
        result = _get_config_list_data(mock_hass)
        assert len(result["entries"]) == 2
        names = {e["cluster_name"] for e in result["entries"]}
        assert names == {"cluster-a", "cluster-b"}
        # Verify watch_enabled differs between entries
        entry_map = {e["cluster_name"]: e for e in result["entries"]}
        assert entry_map["cluster-a"]["watch_enabled"] is False
        assert entry_map["cluster-b"]["watch_enabled"] is True

    def test_config_list_missing_config_key(self, mock_hass, sample_coordinator_data):
        """Test config list uses defaults when config dict is missing."""
        coordinator = _make_coordinator(sample_coordinator_data)
        mock_hass.data = {
            DOMAIN: {
                "entry_1": {
                    "coordinator": coordinator,
                    # no "config" key
                },
            }
        }
        result = _get_config_list_data(mock_hass)
        entry = result["entries"][0]
        assert entry["cluster_name"] == "default"
        assert entry["host"] == ""
        assert entry["namespaces"] == []
