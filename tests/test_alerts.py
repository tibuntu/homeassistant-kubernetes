"""Tests for the shared cluster alert helpers."""

from datetime import UTC, datetime

import pytest

from custom_components.kubernetes.alerts import (
    build_alerts,
    degraded_workloads,
    failed_jobs,
    job_state,
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
    """build_alerts is exactly the five helpers under the panel's keys."""
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
        "failed_jobs": failed_jobs(data),
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


def _job(conditions, **extra):
    return {
        "name": "backup-1",
        "namespace": "ns",
        "owner_cronjob": "backup",
        "conditions": conditions,
        **extra,
    }


def _failed(at="2026-11-02T02:00:00Z", status="True", type_="Failed"):
    return {
        "type": type_,
        "status": status,
        "reason": "BackoffLimitExceeded",
        "message": "Job has reached the specified backoff limit",
        "last_transition_time": at,
    }


def test_failed_jobs_reports_recent_failure():
    """A Job whose Failed condition turned True inside the window is listed."""
    data = {"jobs": {"ns_backup-1": _job([_failed()])}}
    assert failed_jobs(data, _NOW) == [
        {
            "name": "backup-1",
            "namespace": "ns",
            "cronjob": "backup",
            "reason": "BackoffLimitExceeded",
            "message": "Job has reached the specified backoff limit",
            "failed_at": "2026-11-02T02:00:00Z",
        }
    ]


@pytest.mark.parametrize(
    "conditions",
    [
        [],  # still running or retrying below backoffLimit
        None,  # job data parsed before conditions were exposed
        [_failed(type_="FailureTarget")],  # interim, pods still terminating
        [_failed(status="False")],
        [_failed(type_="Complete")],
        [_failed(at="2026-11-01T11:59:59Z")],  # aged out of the 24 h window
        [_failed(at=None)],
        [_failed(at="not-a-timestamp")],
        [_failed(at="2026-11-02T02:00:00")],  # naive, cannot be compared
    ],
)
def test_failed_jobs_skips(conditions):
    """Retrying, succeeded, old or undated Jobs are not listed."""
    data = {"jobs": {"ns_backup-1": _job(conditions)}}
    assert failed_jobs(data, _NOW) == []


def test_failed_jobs_defaults_to_current_time():
    """Without ``now`` the window ends at the current time."""
    job = _job([_failed(at=datetime.now(UTC).isoformat())], owner_cronjob=None)
    assert failed_jobs({"jobs": {"j": job}})[0]["cronjob"] is None
    assert failed_jobs({}) == []


@pytest.mark.parametrize(
    ("last_successful_time", "listed"),
    [
        ("2026-11-02T03:00:00Z", False),  # a later run succeeded
        ("2026-11-01T03:00:00Z", True),  # last success predates the failure
        (None, True),  # never succeeded
        ("not-a-timestamp", True),
        ("2026-11-02T03:00:00", True),  # naive, cannot be compared
    ],
)
def test_failed_jobs_clears_after_later_cronjob_success(last_successful_time, listed):
    """A CronJob run that failed drops out once a later run succeeded."""
    data = {
        "jobs": {"ns_backup-1": _job([_failed()])},
        "cronjobs": {
            "ns_backup": {"last_successful_time": last_successful_time},
            # same CronJob name in another namespace must not count
            "other_backup": {"last_successful_time": "2026-11-02T03:00:00Z"},
        },
    }
    assert bool(failed_jobs(data, _NOW)) is listed


def test_failed_jobs_without_cronjob_data():
    """A missing CronJob (standalone Job, bucket absent) keeps the alert."""
    data = {"jobs": {"j": _job([_failed()], owner_cronjob=None)}, "cronjobs": {}}
    assert len(failed_jobs(data, _NOW)) == 1


def _cond(type_, status="True"):
    return {"type": type_, "status": status}


@pytest.mark.parametrize(
    ("job", "expected"),
    [
        ({"conditions": [_cond("Complete")]}, "Complete"),
        ({"conditions": [_cond("Failed")]}, "Failed"),
        ({"conditions": [_cond("Failed"), _cond("Complete")]}, "Complete"),
        ({"conditions": [_cond("SuccessCriteriaMet")], "active": 1}, "Running"),
        ({"conditions": [_cond("FailureTarget")], "failed": 1}, "Retrying"),
        ({"conditions": [_cond("Complete", "False")]}, "Pending"),
        ({"conditions": [_cond("Failed", "False")], "failed": 1}, "Retrying"),
        ({"succeeded": 3, "completions": 3}, "Complete"),
        ({"conditions": [_cond("Suspended")]}, "Suspended"),
        ({"active": 2}, "Running"),
        ({"failed": 1}, "Retrying"),
        ({}, "Pending"),
        ({"conditions": None}, "Pending"),
    ],
    ids=[
        "complete",
        "failed",
        "complete-beats-failed",
        "interim-success-criteria-ignored",
        "interim-failure-target-ignored",
        "complete-status-false-ignored",
        "failed-status-false-ignored",
        "counter-fallback",
        "suspended",
        "running",
        "retrying",
        "pending",
        "conditions-none",
    ],
)
def test_job_state(job, expected):
    """job_state covers every branch of the Job status derivation."""
    assert job_state(job) == expected
