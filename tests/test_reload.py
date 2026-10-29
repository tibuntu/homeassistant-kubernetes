"""End-to-end: every entity is provided again after a config entry reload.

Runs the real integration (coordinator + all platforms) against a mocked
client. Guards against a platform deduplicating against the entity registry,
which outlives a reload/restart and leaves registered entities "no longer
provided" (1.14.1 replica numbers).
"""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant import loader
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from custom_components.kubernetes.const import DOMAIN

_COMPONENT_DIR = Path(__file__).parents[1] / "custom_components" / "kubernetes"


def _client() -> MagicMock:
    client = MagicMock()
    client.auth_failed = False
    client.get_deployments = AsyncMock(
        return_value=[
            {"name": "web", "namespace": "default", "replicas": 2, "is_running": True}
        ]
    )
    client.get_statefulsets = AsyncMock(
        return_value=[
            {"name": "pg", "namespace": "db", "replicas": 1, "is_running": True}
        ]
    )
    for method in (
        "get_cronjobs",
        "get_daemonsets",
        "get_jobs",
        "get_ingresses",
        "get_services",
        "get_hpas",
        "get_pods",
    ):
        setattr(client, method, AsyncMock(return_value=[]))
    client.get_nodes = AsyncMock(return_value=[{"name": "node-1", "status": "Ready"}])
    client.get_nodes_count = AsyncMock(return_value=1)
    client.get_node_metrics = AsyncMock(
        return_value={"node-1": {"cpu": 100, "memory": 512}}
    )
    client.get_server_version = AsyncMock(return_value="v1.36.0")
    client.is_cluster_healthy = AsyncMock(return_value=True)
    return client


def _register_integration(hass: HomeAssistant) -> None:
    """Hand HA's loader the integration directly.

    HA's own custom_components scan trips over the editable install's path
    hook in CI (see load_translations in conftest.py), so seed its cache.
    """
    manifest = json.loads((_COMPONENT_DIR / "manifest.json").read_text())
    integration = loader.Integration(
        hass,
        f"custom_components.{DOMAIN}",
        _COMPONENT_DIR,
        manifest,
        {p.name for p in _COMPONENT_DIR.iterdir()},
    )
    hass.data[loader.DATA_CUSTOM_COMPONENTS] = {DOMAIN: integration}


async def test_all_entities_provided_after_reload(
    hass: HomeAssistant, make_config_entry
):
    """A reload must provide every registered entity of the entry again."""
    _register_integration(hass)
    # Satisfy the manifest dependencies without loading the real frontend.
    hass.config.components.update({"http", "frontend"})
    entry = make_config_entry(options={"enable_watch": False})

    with (
        patch("custom_components.kubernetes.KubernetesClient", return_value=_client()),
        patch("custom_components.kubernetes._async_sync_panel", new=AsyncMock()),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        registry = er.async_get(hass)
        before = {
            e.entity_id
            for e in er.async_entries_for_config_entry(registry, entry.entry_id)
        }
        # Non-vacuous: every workload/node platform produced something
        for domain in ("sensor", "switch", "number", "binary_sensor"):
            assert any(eid.startswith(f"{domain}.") for eid in before), domain

        assert await hass.config_entries.async_reload(entry.entry_id)
        await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.LOADED
    after = {
        e.entity_id for e in er.async_entries_for_config_entry(registry, entry.entry_id)
    }
    assert after == before
    not_provided = [
        eid
        for eid in after
        if (state := hass.states.get(eid)) is None or state.attributes.get("restored")
    ]
    assert not_provided == []
