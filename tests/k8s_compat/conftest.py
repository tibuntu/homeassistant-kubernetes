"""Fixtures for Kubernetes API compatibility tests.

These tests run against a real kind cluster in CI. Connection info is
passed via K8S_SERVER and K8S_TOKEN environment variables set by the
k8s-compat workflow.
"""

from __future__ import annotations

import os

import pytest


def _require_cluster() -> tuple[str, str]:
    server = os.environ.get("K8S_SERVER", "")
    token = os.environ.get("K8S_TOKEN", "")
    if not server or not token:
        pytest.skip("K8S_SERVER / K8S_TOKEN not set — skipping compat tests")
    return server, token


def _get_client_class():
    """Load KubernetesClient without triggering __init__.py.

    Uses importlib to load const, metrics_parser, and kubernetes_client
    directly so homeassistant is not required as a dependency.
    """
    import importlib.util
    from pathlib import Path
    import sys

    pkg_dir = Path(__file__).resolve().parents[2] / "custom_components" / "kubernetes"

    def load(name: str, file_name: str):
        # Register under the real name so relative imports within the
        # modules resolve correctly, but only for the duration of loading.
        full_name = f"custom_components.kubernetes.{name}"
        if full_name in sys.modules:
            return sys.modules[full_name]
        spec = importlib.util.spec_from_file_location(full_name, pkg_dir / file_name)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[full_name] = mod
        spec.loader.exec_module(mod)
        return mod

    load("const", "const.py")
    load("metrics_parser", "metrics_parser.py")
    client_mod = load("kubernetes_client", "kubernetes_client.py")
    return client_mod.KubernetesClient


@pytest.fixture
def k8s_client():
    """Real KubernetesClient connected to the kind cluster."""
    server, token = _require_cluster()
    from urllib.parse import urlparse

    KubernetesClient = _get_client_class()

    parsed = urlparse(server)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or 6443

    return KubernetesClient(
        {
            "host": host,
            "port": port,
            "api_token": token,
            "cluster_name": "compat-test",
            "namespace": ["default"],
            "monitor_all_namespaces": True,
            "verify_ssl": False,
            "use_in_cluster": False,
            "exclude_job_pods": True,
        }
    )
