"""Tests for the shared cluster alert helpers."""

from custom_components.kubernetes.alerts import (
    build_alerts,
    degraded_workloads,
    nodes_under_pressure,
    problem_pods,
)


def test_problem_pods_uses_parser_flag():
    """Running pods flagged ``problem`` are alerts; benign ones are not."""
    data = {
        "pods": {
            "a": {
                "name": "crash",
                "namespace": "ns",
                "phase": "Running",
                "problem": True,
                "problem_reason": "CrashLoopBackOff",
            },
            "b": {"name": "starting", "namespace": "ns", "phase": "Pending"},
            "c": {"name": "lost", "namespace": "ns", "phase": "Unknown"},
        }
    }
    assert problem_pods(data) == [
        {
            "name": "crash",
            "namespace": "ns",
            "phase": "Running",
            "reason": "CrashLoopBackOff",
        },
        # phase Unknown is not derived by the parser; the reason falls back to it
        {"name": "lost", "namespace": "ns", "phase": "Unknown", "reason": "Unknown"},
    ]


def test_build_alerts_composes_helpers():
    """build_alerts is exactly the three helpers under the panel's keys."""
    data = {
        "nodes": {"n1": {"disk_pressure": True}},
        "daemonsets": {
            "x": {
                "name": "ds",
                "namespace": "kube-system",
                "desired_number_scheduled": 3,
                "number_available": None,
            }
        },
        "pods": {"p": {"name": "p", "namespace": "ns", "phase": "Failed"}},
    }
    assert build_alerts(data) == {
        "nodes_with_pressure": nodes_under_pressure(data),
        "degraded_workloads": degraded_workloads(data),
        "failed_pods": problem_pods(data),
    }
    assert build_alerts(data)["degraded_workloads"][0]["ready"] == 0


def test_degraded_workloads_includes_stalled_rollouts():
    """A stalled Deployment is listed even with every replica available."""
    data = {
        "deployments": {
            "a": {
                "name": "stalled",
                "namespace": "ns",
                "replicas": 2,
                "available_replicas": 2,
                "rollout_stalled": True,
                "rollout_reason": "ProgressDeadlineExceeded",
            },
            "b": {
                "name": "short",
                "namespace": "ns",
                "replicas": 2,
                "available_replicas": 1,
            },
            "c": {
                "name": "ok",
                "namespace": "ns",
                "replicas": 2,
                "available_replicas": 2,
            },
            "d": {
                "name": "off",
                "namespace": "ns",
                "replicas": 0,
                "rollout_stalled": True,
                "rollout_reason": "ProgressDeadlineExceeded",
            },
        }
    }
    assert degraded_workloads(data) == [
        {
            "name": "stalled",
            "type": "Deployment",
            "namespace": "ns",
            "ready": 2,
            "desired": 2,
            "reason": "ProgressDeadlineExceeded",
        },
        {
            "name": "short",
            "type": "Deployment",
            "namespace": "ns",
            "ready": 1,
            "desired": 2,
            "reason": None,
        },
    ]
