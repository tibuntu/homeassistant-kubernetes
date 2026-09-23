"""Kubernetes API compatibility tests.

Run against a real kind cluster to verify that every API path the
integration uses returns parseable responses on the tested k8s version.

Marked with ``k8s_compat`` — the main test suite skips these (no cluster),
and the k8s-compat workflow runs only these.
"""

from __future__ import annotations

import asyncio

import pytest

pytestmark = pytest.mark.k8s_compat


async def _poll_until(check, timeout: int = 30, interval: int = 1) -> None:
    """Poll an async predicate until it's True, bounded by a timeout."""
    async with asyncio.timeout(timeout):
        while not await check():
            await asyncio.sleep(interval)


class TestClusterHealth:
    async def test_is_cluster_healthy(self, k8s_client):
        assert await k8s_client.is_cluster_healthy() is True


class TestPods:
    async def test_get_pods(self, k8s_client):
        pods = await k8s_client.get_pods()
        assert isinstance(pods, list)
        assert len(pods) > 0
        pod = pods[0]
        assert "name" in pod
        assert "namespace" in pod
        assert "phase" in pod

    async def test_get_pods_count(self, k8s_client):
        count = await k8s_client.get_pods_count()
        assert isinstance(count, int)
        assert count > 0

    async def test_pod_container_state_fields(self, k8s_client):
        pods = await k8s_client.get_pods()
        for pod in pods:
            assert "problem" in pod
            assert isinstance(pod["problem"], bool)


class TestNodes:
    async def test_get_nodes(self, k8s_client):
        nodes = await k8s_client.get_nodes()
        assert isinstance(nodes, list)
        assert len(nodes) > 0
        node = nodes[0]
        assert "name" in node
        assert "status" in node
        assert "cpu_cores" in node
        assert "memory_capacity_gib" in node

    async def test_get_nodes_count(self, k8s_client):
        count = await k8s_client.get_nodes_count()
        assert isinstance(count, int)
        assert count >= 1


class TestDeployments:
    async def test_get_deployments(self, k8s_client):
        deployments = await k8s_client.get_deployments()
        assert isinstance(deployments, list)
        names = [d["name"] for d in deployments]
        assert "test-nginx" in names
        dep = next(d for d in deployments if d["name"] == "test-nginx")
        assert "replicas" in dep
        assert "available_replicas" in dep
        assert "namespace" in dep

    async def test_get_deployments_count(self, k8s_client):
        count = await k8s_client.get_deployments_count()
        assert isinstance(count, int)
        assert count >= 1


class TestStatefulSets:
    async def test_get_statefulsets(self, k8s_client):
        statefulsets = await k8s_client.get_statefulsets()
        assert isinstance(statefulsets, list)
        names = [s["name"] for s in statefulsets]
        assert "test-statefulset" in names

    async def test_get_statefulsets_count(self, k8s_client):
        count = await k8s_client.get_statefulsets_count()
        assert isinstance(count, int)
        assert count >= 1


class TestDaemonSets:
    async def test_get_daemonsets(self, k8s_client):
        daemonsets = await k8s_client.get_daemonsets()
        assert isinstance(daemonsets, list)
        names = [d["name"] for d in daemonsets]
        assert "test-daemonset" in names

    async def test_get_daemonsets_count(self, k8s_client):
        count = await k8s_client.get_daemonsets_count()
        assert isinstance(count, int)
        assert count >= 1


class TestCronJobs:
    async def test_get_cronjobs(self, k8s_client):
        cronjobs = await k8s_client.get_cronjobs()
        assert isinstance(cronjobs, list)
        names = [c["name"] for c in cronjobs]
        assert "test-cronjob" in names
        cj = next(c for c in cronjobs if c["name"] == "test-cronjob")
        assert "schedule" in cj
        assert "suspend" in cj

    async def test_get_cronjobs_count(self, k8s_client):
        count = await k8s_client.get_cronjobs_count()
        assert isinstance(count, int)
        assert count >= 1


class TestJobs:
    async def test_get_jobs(self, k8s_client):
        jobs = await k8s_client.get_jobs()
        assert isinstance(jobs, list)
        names = [j["name"] for j in jobs]
        assert "test-job" in names

    async def test_get_jobs_count(self, k8s_client):
        count = await k8s_client.get_jobs_count()
        assert isinstance(count, int)
        assert count >= 1


class TestIngresses:
    async def test_get_ingresses(self, k8s_client):
        ingresses = await k8s_client.get_ingresses()
        assert isinstance(ingresses, list)
        names = [i["name"] for i in ingresses]
        assert "test-ingress" in names
        ing = next(i for i in ingresses if i["name"] == "test-ingress")
        assert "rules" in ing

    async def test_get_ingresses_count(self, k8s_client):
        count = await k8s_client.get_ingresses_count()
        assert isinstance(count, int)
        assert count >= 1


class TestServices:
    async def test_get_services(self, k8s_client):
        services = await k8s_client.get_services()
        assert isinstance(services, list)
        names = [s["name"] for s in services]
        assert "test-nginx-svc" in names

    async def test_get_services_count(self, k8s_client):
        count = await k8s_client.get_services_count()
        assert isinstance(count, int)
        assert count >= 1


class TestMetrics:
    async def test_get_node_metrics_no_crash(self, k8s_client):
        """Metrics API may or may not be available — must not raise."""
        metrics = await k8s_client.get_node_metrics()
        assert isinstance(metrics, dict)


class TestWatch:
    async def test_watch_stream_connects(self, k8s_client):
        """Verify the watch API accepts our request and yields events."""
        base = f"https://{k8s_client.host}:{k8s_client.port}"
        url = f"{base}/api/v1/pods"
        items, rv = await k8s_client.list_resource_with_version(url)
        assert isinstance(items, list)
        assert rv != "0"

        try:
            async with asyncio.timeout(5):
                async for event in k8s_client.watch_stream(url, rv):
                    assert "type" in event
                    break
        except TimeoutError:
            pass


class TestMutations:
    """Write operations against the real cluster."""

    async def test_suspend_resume_cronjob(self, k8s_client):
        result = await k8s_client.suspend_cronjob("test-cronjob", "default")
        assert result["success"] is True
        cronjobs = await k8s_client.get_cronjobs()
        cj = next(c for c in cronjobs if c["name"] == "test-cronjob")
        assert cj["suspend"] is True

        result = await k8s_client.resume_cronjob("test-cronjob", "default")
        assert result["success"] is True
        cronjobs = await k8s_client.get_cronjobs()
        cj = next(c for c in cronjobs if c["name"] == "test-cronjob")
        assert cj["suspend"] is False

    async def test_rollout_restart_deployment(self, k8s_client):
        result = await k8s_client.rollout_restart_deployment("test-nginx", "default")
        assert result is True

    async def test_rollout_restart_statefulset(self, k8s_client):
        result = await k8s_client.rollout_restart_statefulset(
            "test-statefulset", "default"
        )
        assert result is True

    async def test_rollout_restart_daemonset(self, k8s_client):
        result = await k8s_client.rollout_restart_daemonset("test-daemonset", "default")
        assert result is True

    async def test_cordon_uncordon_node(self, k8s_client):
        nodes = await k8s_client.get_nodes()
        node_name = nodes[0]["name"]

        result = await k8s_client.cordon_node(node_name)
        assert result is True

        result = await k8s_client.uncordon_node(node_name)
        assert result is True

    async def test_delete_job(self, k8s_client):
        result = await k8s_client.delete_job("test-job", "default")
        assert result is True

    async def test_scale_deployment_and_restore(self, k8s_client):
        try:
            assert await k8s_client.scale_deployment("test-nginx", 2, "default") is True

            async def _scaled_up():
                deployments = await k8s_client.get_deployments()
                dep = next(d for d in deployments if d["name"] == "test-nginx")
                return dep["replicas"] == 2

            await _poll_until(_scaled_up)
        finally:
            await k8s_client.scale_deployment("test-nginx", 1, "default")

        async def _scaled_back():
            deployments = await k8s_client.get_deployments()
            dep = next(d for d in deployments if d["name"] == "test-nginx")
            return dep["replicas"] == 1

        await _poll_until(_scaled_back, timeout=60)

    async def test_scale_statefulset_and_restore(self, k8s_client):
        try:
            assert (
                await k8s_client.scale_statefulset("test-statefulset", 2, "default")
                is True
            )

            async def _scaled_up():
                statefulsets = await k8s_client.get_statefulsets()
                sts = next(s for s in statefulsets if s["name"] == "test-statefulset")
                return sts["replicas"] == 2

            await _poll_until(_scaled_up)
        finally:
            await k8s_client.scale_statefulset("test-statefulset", 1, "default")

        async def _scaled_back():
            statefulsets = await k8s_client.get_statefulsets()
            sts = next(s for s in statefulsets if s["name"] == "test-statefulset")
            return sts["replicas"] == 1

        await _poll_until(_scaled_back, timeout=60)

    async def test_stop_start_deployment_restores_replicas(self, k8s_client):
        try:
            assert await k8s_client.stop_deployment("test-nginx", "default") is True

            async def _scaled_to_zero():
                deployments = await k8s_client.get_deployments()
                dep = next(d for d in deployments if d["name"] == "test-nginx")
                return dep["replicas"] == 0

            await _poll_until(_scaled_to_zero)
        finally:
            await k8s_client.start_deployment("test-nginx", 1, "default")

        async def _scaled_back_up():
            deployments = await k8s_client.get_deployments()
            dep = next(d for d in deployments if d["name"] == "test-nginx")
            return dep["replicas"] == 1 and dep["available_replicas"] == 1

        await _poll_until(_scaled_back_up, timeout=60)

    async def test_delete_pod_recreated(self, k8s_client):
        pods = await k8s_client.get_pods()
        pod = next(
            p
            for p in pods
            if p["namespace"] == "default" and p["name"].startswith("test-nginx-")
        )
        assert await k8s_client.delete_pod(pod["name"], "default") is True

        async def _replacement_ready():
            deployments = await k8s_client.get_deployments()
            dep = next(d for d in deployments if d["name"] == "test-nginx")
            return dep["available_replicas"] == 1

        await _poll_until(_replacement_ready, timeout=60)

    async def test_trigger_cronjob_creates_and_cleans_up_job(self, k8s_client):
        result = await k8s_client.trigger_cronjob("test-cronjob", "default")
        assert result["success"] is True
        job_name = result["job_name"]

        try:

            async def _job_exists():
                jobs = await k8s_client.get_jobs()
                return any(j["name"] == job_name for j in jobs)

            await _poll_until(_job_exists)
        finally:
            await k8s_client.delete_job(job_name, "default")

    async def test_get_pod_metrics_no_crash(self, k8s_client):
        """Metrics API may or may not be available — must not raise."""
        metrics = await k8s_client.get_pod_metrics()
        assert isinstance(metrics, dict)
