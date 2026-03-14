"""Data coordinator for Kubernetes integration."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from datetime import timedelta
import logging
import time
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_ENABLE_WATCH,
    CONF_SWITCH_UPDATE_INTERVAL,
    DEFAULT_ENABLE_WATCH,
    DEFAULT_FALLBACK_POLL_INTERVAL,
    DEFAULT_SWITCH_UPDATE_INTERVAL,
    DEFAULT_WATCH_RECONNECT_DELAY,
    DOMAIN,
)
from .device import cleanup_orphaned_namespace_devices, get_all_namespaces
from .kubernetes_client import KubernetesClient, ResourceVersionExpired

_LOGGER = logging.getLogger(__name__)


class KubernetesDataCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Kubernetes data."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        client: KubernetesClient,
    ) -> None:
        """Initialize the coordinator."""
        # When watch is enabled, polling becomes a long-interval fallback.
        watch_enabled = config_entry.options.get(
            CONF_ENABLE_WATCH, DEFAULT_ENABLE_WATCH
        )
        if watch_enabled:
            update_interval = DEFAULT_FALLBACK_POLL_INTERVAL
        else:
            update_interval = config_entry.data.get(
                CONF_SWITCH_UPDATE_INTERVAL, DEFAULT_SWITCH_UPDATE_INTERVAL
            )

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{config_entry.entry_id}",
            update_interval=timedelta(seconds=update_interval),
        )

        # Set attributes after super().__init__() to ensure they're not overridden
        self.config_entry = config_entry
        self.client = client

        # Watch API state
        self._watch_tasks: list[asyncio.Task] = []
        self._watch_stop_event: asyncio.Event = asyncio.Event()
        # Prevents watch events from modifying self.data while a poll is building
        # a replacement dict. Without this, watch changes are lost when the poll
        # overwrites self.data.
        self._data_lock: asyncio.Lock = asyncio.Lock()

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data via Kubernetes client.

        Holds _data_lock for the entire fetch cycle so that watch events
        queue up and apply *after* self.data is replaced with the fresh
        snapshot, preventing lost updates.
        """
        async with self._data_lock:
            try:
                _LOGGER.debug("Updating Kubernetes data for coordinator")

                # Fetch deployments, statefulsets, daemonsets, cronjobs, jobs, pods count, nodes count, and detailed nodes info
                deployments = await self.client.get_deployments()
                statefulsets = await self.client.get_statefulsets()
                daemonsets = await self.client.get_daemonsets()
                cronjobs = await self.client.get_cronjobs()
                jobs = await self.client.get_jobs()
                pods_count = await self.client.get_pods_count()
                nodes_count = await self.client.get_nodes_count()

                _LOGGER.debug("Starting to fetch detailed node information")
                nodes = await self.client.get_nodes()
                _LOGGER.debug(
                    "Successfully fetched %d nodes with detailed information",
                    len(nodes),
                )

                _LOGGER.debug("Starting to fetch detailed pod information")
                pods = await self.client.get_pods()
                _LOGGER.debug(
                    "Successfully fetched %d pods with detailed information",
                    len(pods),
                )

                # Fetch node metrics (CPU/memory usage) — best-effort
                node_metrics = await self.client.get_node_metrics()
                if node_metrics:
                    _LOGGER.debug("Fetched metrics for %d nodes", len(node_metrics))
                    for node in nodes:
                        name = node.get("name")
                        if name and name in node_metrics:
                            node["cpu_usage_millicores"] = node_metrics[name]["cpu"]
                            node["memory_usage_mib"] = node_metrics[name]["memory"]

                # Log node names for debugging
                if nodes:
                    node_names = [node.get("name", "Unknown") for node in nodes]
                    _LOGGER.debug("Fetched nodes: %s", node_names)

                # Create a lookup dictionary for quick access
                data = {
                    "deployments": {
                        deployment["name"]: deployment for deployment in deployments
                    },
                    "statefulsets": {
                        statefulset["name"]: statefulset for statefulset in statefulsets
                    },
                    "daemonsets": {
                        daemonset["name"]: daemonset for daemonset in daemonsets
                    },
                    "cronjobs": {cronjob["name"]: cronjob for cronjob in cronjobs},
                    "jobs": {job["name"]: job for job in jobs},
                    "nodes": {node["name"]: node for node in nodes},
                    "pods": {f"{pod['namespace']}_{pod['name']}": pod for pod in pods},
                    "pods_count": pods_count,
                    "nodes_count": nodes_count,
                    "last_update": time.time(),
                }

                _LOGGER.debug(
                    "Successfully updated Kubernetes data: %d deployments, %d statefulsets, %d daemonsets, %d cronjobs, %d jobs, %d pods (detailed: %d), %d nodes (detailed: %d)",
                    len(deployments),
                    len(statefulsets),
                    len(daemonsets),
                    len(cronjobs),
                    len(jobs),
                    pods_count,
                    len(pods),
                    nodes_count,
                    len(nodes),
                )

                # Clean up entities for resources that no longer exist
                await self._cleanup_orphaned_entities(data)

                # Clean up orphaned namespace devices
                current_namespaces = get_all_namespaces(data)
                await cleanup_orphaned_namespace_devices(
                    self.hass, self.config_entry, current_namespaces
                )

                return data

            except Exception as ex:
                _LOGGER.error("Failed to update Kubernetes data: %s", ex)
                raise UpdateFailed(f"Failed to update Kubernetes data: {ex}") from ex

    def get_deployment_data(self, deployment_name: str) -> dict[str, Any] | None:
        """Get deployment data by name."""
        if not self.data or "deployments" not in self.data:
            return None
        return self.data["deployments"].get(deployment_name)

    def get_statefulset_data(self, statefulset_name: str) -> dict[str, Any] | None:
        """Get statefulset data by name."""
        if not self.data or "statefulsets" not in self.data:
            return None
        return self.data["statefulsets"].get(statefulset_name)

    def get_daemonset_data(self, daemonset_name: str) -> dict[str, Any] | None:
        """Get daemonset data by name."""
        if not self.data or "daemonsets" not in self.data:
            return None
        return self.data["daemonsets"].get(daemonset_name)

    def get_cronjob_data(self, cronjob_name: str) -> dict[str, Any] | None:
        """Get cronjob data by name."""
        if not self.data or "cronjobs" not in self.data:
            return None
        return self.data["cronjobs"].get(cronjob_name)

    def get_job_data(self, job_name: str) -> dict[str, Any] | None:
        """Get job data by name."""
        if not self.data or "jobs" not in self.data:
            return None
        return self.data["jobs"].get(job_name)

    def get_node_data(self, node_name: str) -> dict[str, Any] | None:
        """Get node data by name."""
        if not self.data or "nodes" not in self.data:
            _LOGGER.debug(
                "No coordinator data or nodes data available for node %s", node_name
            )
            return None

        node_data = self.data["nodes"].get(node_name)
        if node_data is None:
            _LOGGER.warning(
                "Node %s not found in coordinator data. Available nodes: %s",
                node_name,
                list(self.data["nodes"].keys()),
            )
        else:
            _LOGGER.debug(
                "Retrieved data for node %s: status=%s",
                node_name,
                node_data.get("status", "Unknown"),
            )
        return node_data

    def get_all_nodes_data(self) -> dict[str, dict[str, Any]]:
        """Get all nodes data."""
        if not self.data or "nodes" not in self.data:
            return {}
        return self.data["nodes"]

    def get_pod_data(self, namespace: str, pod_name: str) -> dict[str, Any] | None:
        """Get pod data by namespace and name."""
        if not self.data or "pods" not in self.data:
            return None
        pod_key = f"{namespace}_{pod_name}"
        return self.data["pods"].get(pod_key)

    def get_all_pods_data(self) -> dict[str, dict[str, Any]]:
        """Get all pods data."""
        if not self.data or "pods" not in self.data:
            return {}
        return self.data["pods"]

    def get_last_update_time(self) -> float:
        """Get the timestamp of the last successful update."""
        if not self.data or "last_update" not in self.data:
            return 0.0
        return self.data["last_update"]

    def get_all_namespaces(self) -> set[str]:
        """Get all unique namespaces from coordinator data."""
        return get_all_namespaces(self.data)

    def _build_expected_unique_ids(self, current_data: dict[str, Any]) -> set[str]:
        """Build the set of unique_ids that should exist based on current data.

        Uses the same format strings as the entity classes so there is no
        ambiguous parsing of underscore-delimited IDs.
        """
        eid = self.config_entry.entry_id
        expected: set[str] = set()

        # Count sensors (always valid)
        for suffix in (
            "pods_count",
            "nodes_count",
            "deployments_count",
            "statefulsets_count",
            "daemonsets_count",
            "cronjobs_count",
            "jobs_count",
        ):
            expected.add(f"{eid}_{suffix}")

        # Cluster health binary sensor
        expected.add(f"{eid}_cluster_health")

        # Node sensors + node condition binary sensors
        for node_name in current_data.get("nodes", {}):
            expected.add(f"{eid}_node_{node_name}")
            for condition in (
                "memory_pressure",
                "disk_pressure",
                "pid_pressure",
                "network_unavailable",
            ):
                expected.add(f"{eid}_node_{node_name}_{condition}")

        # Pod sensors: pod_{namespace}_{pod_name}
        for pod_key, pod_data in current_data.get("pods", {}).items():
            namespace = pod_data.get("namespace", "default")
            pod_name = pod_data.get("name", pod_key)
            expected.add(f"{eid}_pod_{namespace}_{pod_name}")

        # Deployment switches: {name}_deployment
        # Deployment metric sensors: {name}_deployment_{metric}
        for name in current_data.get("deployments", {}):
            expected.add(f"{eid}_{name}_deployment")
            for metric in ("cpu", "memory"):
                expected.add(f"{eid}_{name}_deployment_{metric}")

        # StatefulSet switches: {name}_statefulset
        # StatefulSet metric sensors: {name}_statefulset_{metric}
        for name in current_data.get("statefulsets", {}):
            expected.add(f"{eid}_{name}_statefulset")
            for metric in ("cpu", "memory"):
                expected.add(f"{eid}_{name}_statefulset_{metric}")

        # DaemonSet sensors: daemonset_{name}
        for name in current_data.get("daemonsets", {}):
            expected.add(f"{eid}_daemonset_{name}")

        # CronJob sensors: cronjob_{namespace}_{name}
        # CronJob switches: {namespace}_{name}_cronjob
        for name, data in current_data.get("cronjobs", {}).items():
            namespace = data.get("namespace", "default")
            expected.add(f"{eid}_cronjob_{namespace}_{name}")
            expected.add(f"{eid}_{namespace}_{name}_cronjob")

        # Job sensors: job_{namespace}_{name}
        for name, data in current_data.get("jobs", {}).items():
            namespace = data.get("namespace", "default")
            expected.add(f"{eid}_job_{namespace}_{name}")

        return expected

    async def _cleanup_orphaned_entities(self, current_data: dict[str, Any]) -> None:
        """Remove entities for Kubernetes resources that no longer exist."""
        try:
            if not self.config_entry or not hasattr(self.config_entry, "entry_id"):
                _LOGGER.debug("Skipping entity cleanup: config_entry not available")
                return

            entity_registry = async_get_entity_registry(self.hass)

            entities = entity_registry.entities.get_entries_for_config_entry_id(
                self.config_entry.entry_id
            )

            _LOGGER.debug(
                "Entity cleanup: Found %d entities for config entry %s",
                len(entities),
                self.config_entry.entry_id,
            )

            expected_ids = self._build_expected_unique_ids(current_data)
            eid_prefix = f"{self.config_entry.entry_id}_"
            entities_to_remove = []

            for entity in entities:
                if not entity.unique_id:
                    continue

                # Only consider entities belonging to this config entry
                if not entity.unique_id.startswith(eid_prefix):
                    continue

                if entity.unique_id not in expected_ids:
                    _LOGGER.info(
                        "Entity %s (unique_id: %s) no longer matches current data, "
                        "marking for removal",
                        entity.entity_id,
                        entity.unique_id,
                    )
                    entities_to_remove.append(entity.entity_id)

            # Remove the orphaned entities
            for entity_id in entities_to_remove:
                _LOGGER.info("Removing orphaned entity: %s", entity_id)
                entity_registry.async_remove(entity_id)

            if entities_to_remove:
                _LOGGER.info("Removed %d orphaned entities", len(entities_to_remove))
            else:
                _LOGGER.debug("No orphaned entities found")

        except Exception as ex:
            _LOGGER.error("Failed to cleanup orphaned entities: %s", ex)

    # -------------------------------------------------------------------------
    # Watch API support (experimental)
    # -------------------------------------------------------------------------

    def _build_watch_configs(
        self, base_url: str
    ) -> list[tuple[str, str, Callable[..., Any]]]:
        """Return a list of (resource_type, url, parse_fn) tuples for watch tasks."""
        configs: list[tuple[str, str, Callable[..., Any]]] = []
        client = self.client

        # Cluster-scoped: nodes always use the cluster-wide endpoint
        configs.append(("nodes", f"{base_url}/api/v1/nodes", client._parse_node_item))

        # Namespace-scoped resources
        if client.monitor_all_namespaces:
            configs.extend(
                [
                    ("pods", f"{base_url}/api/v1/pods", client._parse_pod_item),
                    (
                        "deployments",
                        f"{base_url}/apis/apps/v1/deployments",
                        client._parse_deployment_item,
                    ),
                    (
                        "statefulsets",
                        f"{base_url}/apis/apps/v1/statefulsets",
                        client._parse_statefulset_item,
                    ),
                    (
                        "daemonsets",
                        f"{base_url}/apis/apps/v1/daemonsets",
                        client._parse_daemonset_item,
                    ),
                    (
                        "cronjobs",
                        f"{base_url}/apis/batch/v1/cronjobs",
                        client._format_cronjob_from_dict,
                    ),
                    (
                        "jobs",
                        f"{base_url}/apis/batch/v1/jobs",
                        client._format_job_from_dict,
                    ),
                ]
            )
        else:
            # One watch per namespace for each namespace-scoped resource
            for namespace in client.namespaces:
                ns = namespace
                configs.extend(
                    [
                        (
                            "pods",
                            f"{base_url}/api/v1/namespaces/{ns}/pods",
                            client._parse_pod_item,
                        ),
                        (
                            "deployments",
                            f"{base_url}/apis/apps/v1/namespaces/{ns}/deployments",
                            client._parse_deployment_item,
                        ),
                        (
                            "statefulsets",
                            f"{base_url}/apis/apps/v1/namespaces/{ns}/statefulsets",
                            client._parse_statefulset_item,
                        ),
                        (
                            "daemonsets",
                            f"{base_url}/apis/apps/v1/namespaces/{ns}/daemonsets",
                            client._parse_daemonset_item,
                        ),
                        (
                            "cronjobs",
                            f"{base_url}/apis/batch/v1/namespaces/{ns}/cronjobs",
                            client._format_cronjob_from_dict,
                        ),
                        (
                            "jobs",
                            f"{base_url}/apis/batch/v1/namespaces/{ns}/jobs",
                            client._format_job_from_dict,
                        ),
                    ]
                )

        return configs

    async def async_start_watch_tasks(self) -> None:
        """Start background watch tasks for all resource types."""
        self._watch_stop_event.clear()
        base_url = f"https://{self.client.host}:{self.client.port}"
        configs = self._build_watch_configs(base_url)
        for resource_type, url, parse_fn in configs:
            task = self.hass.async_create_background_task(
                self._run_watch_loop(resource_type, url, parse_fn),
                f"k8s_watch_{resource_type}_{url}",
            )
            self._watch_tasks.append(task)
        _LOGGER.debug(
            "Started %d watch tasks for coordinator %s",
            len(self._watch_tasks),
            self.name,
        )

    async def async_stop_watch_tasks(self) -> None:
        """Cancel all active watch tasks and wait for them to finish."""
        if not self._watch_tasks:
            return
        self._watch_stop_event.set()
        for task in self._watch_tasks:
            task.cancel()
        await asyncio.gather(*self._watch_tasks, return_exceptions=True)
        self._watch_tasks.clear()
        self._watch_stop_event.clear()
        _LOGGER.debug("Stopped all watch tasks for coordinator %s", self.name)

    def _populate_from_list(
        self,
        resource_type: str,
        items: list[dict[str, Any]],
        parse_fn: Any,
    ) -> None:
        """Merge parsed items from a list response into coordinator.data[resource_type]."""
        if self.data is None:
            return
        parsed: dict[str, dict[str, Any]] = {}
        for item in items:
            try:
                result = parse_fn(item)
                if result:
                    if resource_type == "pods":
                        key = f"{result['namespace']}_{result['name']}"
                    else:
                        key = result["name"]
                    parsed[key] = result
            except Exception as ex:
                _LOGGER.warning(
                    "Failed to parse %s item during list: %s", resource_type, ex
                )
        # Merge into the existing dict so that tasks watching different namespaces
        # for the same resource type don't overwrite each other's initial data.
        self.data.setdefault(resource_type, {}).update(parsed)
        # Sync derived counts
        if resource_type == "pods":
            self.data["pods_count"] = len(self.data["pods"])
        elif resource_type == "nodes":
            self.data["nodes_count"] = len(self.data["nodes"])

    def _apply_watch_event(
        self,
        resource_type: str,
        event_type: str,
        obj: dict[str, Any],
        parse_fn: Any,
    ) -> None:
        """Apply a single watch event (ADDED/MODIFIED/DELETED) to coordinator.data."""
        if self.data is None:
            return

        metadata = obj.get("metadata", {})
        name = metadata.get("name", "")
        namespace = metadata.get("namespace", "")
        key = f"{namespace}_{name}" if resource_type == "pods" else name

        if event_type in ("ADDED", "MODIFIED"):
            try:
                parsed = parse_fn(obj)
                if parsed:
                    self.data.setdefault(resource_type, {})[key] = parsed
            except Exception as ex:
                _LOGGER.warning(
                    "Failed to parse %s %s event for %r: %s",
                    resource_type,
                    event_type,
                    key,
                    ex,
                )
                return
        elif event_type == "DELETED":
            self.data.get(resource_type, {}).pop(key, None)
            self.hass.async_create_task(self._cleanup_orphaned_entities(self.data))
        else:
            return

        # Sync derived counts
        if resource_type == "pods" and "pods" in self.data:
            self.data["pods_count"] = len(self.data["pods"])
        elif resource_type == "nodes" and "nodes" in self.data:
            self.data["nodes_count"] = len(self.data["nodes"])

        self.data["last_update"] = time.time()
        self.async_update_listeners()

    async def _run_watch_loop(
        self,
        resource_type: str,
        url: str,
        parse_fn: Any,
    ) -> None:
        """Run the watch loop for a single resource type with reconnect logic."""
        resource_version = "0"
        reconnect_delay = DEFAULT_WATCH_RECONNECT_DELAY

        while not self._watch_stop_event.is_set():
            try:
                if resource_version == "0":
                    # Full list + extract resourceVersion to anchor the watch
                    (
                        items,
                        resource_version,
                    ) = await self.client.list_resource_with_version(url)
                    async with self._data_lock:
                        self._populate_from_list(resource_type, items, parse_fn)
                    self.async_update_listeners()
                    _LOGGER.debug(
                        "Watch %s: initial list fetched (%d items, rv=%s)",
                        resource_type,
                        len(items),
                        resource_version,
                    )

                async for event in self.client.watch_stream(url, resource_version):
                    if self._watch_stop_event.is_set():
                        return

                    event_type = event.get("type", "")
                    obj = event.get("object", {})

                    # Keep resource_version up to date so we can resume after reconnect
                    new_rv = obj.get("metadata", {}).get("resourceVersion")
                    if new_rv:
                        resource_version = new_rv

                    if event_type == "BOOKMARK":
                        continue

                    async with self._data_lock:
                        self._apply_watch_event(
                            resource_type, event_type, obj, parse_fn
                        )

                # Stream ended cleanly (timeoutSeconds expired); reconnect immediately
                reconnect_delay = DEFAULT_WATCH_RECONNECT_DELAY
                _LOGGER.debug(
                    "Watch %s: stream ended cleanly, reconnecting", resource_type
                )

            except ResourceVersionExpired:
                _LOGGER.info(
                    "Watch %s: resource version %r expired (HTTP 410), relisting",
                    resource_type,
                    resource_version,
                )
                resource_version = "0"
                reconnect_delay = DEFAULT_WATCH_RECONNECT_DELAY

            except asyncio.CancelledError:
                return

            except Exception as ex:
                _LOGGER.warning(
                    "Watch %s error: %s — reconnecting in %d s",
                    resource_type,
                    ex,
                    reconnect_delay,
                )
                try:
                    await asyncio.wait_for(
                        self._watch_stop_event.wait(), timeout=reconnect_delay
                    )
                    # stop_event was set — exit gracefully
                    return
                except TimeoutError:
                    pass
                reconnect_delay = min(reconnect_delay * 2, 60)
