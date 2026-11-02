"""Tests for the shared cluster alert helpers."""

from datetime import UTC, datetime

import pytest

from custom_components.kubernetes.alerts import (
    build_alerts,
    degraded_workloads,
    nodes_under_pressure,
    problem_pods,
    restarting_pods,
)

_NOW = datetime(2026, 11, 2, 12, 0, tzinfo=UTC)


def _pod(restarts, finished_at, **extra):
    return {
        "name": "web",
        "namespace": "ns",
        "restart_count": restarts,
        "last_terminated_at": finished_at,
        "last_terminated_reason": "OOMKilled",
        "last_terminated_exit_code": 137,
        **extra,
    }


def test_restarting_pods_reports_recent_restart_loop():
    """A pod at the threshold that restarted inside the window is listed."""
    data = {"pods": {"ns_web": _pod(3, "2026-11-02T11:00:00Z")}}
    assert restarting_pods(data, _NOW) == [
        {
            "name": "web",
            "namespace": "ns",
            "restarts": 3,
            "last_terminated_reason": "OOMKilled",
            "last_terminated_exit_code": 137,
            "last_terminated_at": "2026-11-02T11:00:00Z",
        }
    ]


@pytest.mark.parametrize(
    ("restarts", "finished_at"),
    [
        (2, "2026-11-02T11:59:00Z"),  # below the threshold
        (10, "2026-11-02T10:59:59Z"),  # last restart aged out of the window
        (10, None),  # never terminated
        (None, "2026-11-02T11:59:00Z"),  # restart count missing
        (10, "not-a-timestamp"),  # malformed
        (10, "2026-11-02T11:59:00"),  # naive, cannot be compared
    ],
)
def test_restarting_pods_skips(restarts, finished_at):
    """Pods below the threshold, outside the window or without data are skipped."""
    data = {"pods": {"ns_web": _pod(restarts, finished_at)}}
    assert restarting_pods(data, _NOW) == []


def test_restarting_pods_defaults_to_current_time():
    """Without ``now`` the window ends at the current time."""
    data = {"pods": {"ns_web": _pod(5, datetime.now(UTC).isoformat())}}
    assert len(restarting_pods(data)) == 1
    assert restarting_pods({}) == []


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
    """build_alerts is exactly the four helpers under the panel's keys."""
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
        "restarting_pods": restarting_pods(data),
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
