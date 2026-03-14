"""Tests for the Kubernetes services."""

import os
from unittest.mock import AsyncMock, MagicMock

from homeassistant.core import HomeAssistant
import pytest
import yaml

from custom_components.kubernetes.const import (
    ATTR_NAMESPACE,
    ATTR_REPLICAS,
    ATTR_WORKLOAD_NAME,
    ATTR_WORKLOAD_NAMES,
    ATTR_WORKLOAD_TYPE,
    DOMAIN,
    SERVICE_SCALE_WORKLOAD,
    SERVICE_START_WORKLOAD,
    SERVICE_STOP_WORKLOAD,
    WORKLOAD_TYPE_CRONJOB,
    WORKLOAD_TYPE_DEPLOYMENT,
    WORKLOAD_TYPE_STATEFULSET,
)
from custom_components.kubernetes.services import (
    _collect_entity_ids,
    _extract_entity_ids_from_value,
    _extract_workload_info,
    _get_entry_data,
    _get_workload_info_from_entity,
    _log_no_workloads_found,
    _normalize_entity_id_list,
    _resolve_raw_workload_name,
    _validate_entity_workload_type,
    _validate_workload_schema,
    async_setup_services,
    async_unload_services,
)


@pytest.fixture
def mock_client():
    """Mock Kubernetes client."""
    client = MagicMock()
    client.scale_deployment = AsyncMock(return_value=True)
    client.scale_statefulset = AsyncMock(return_value=True)
    client.stop_deployment = AsyncMock(return_value=True)
    client.stop_statefulset = AsyncMock(return_value=True)
    client.start_deployment = AsyncMock(return_value=True)
    client.start_statefulset = AsyncMock(return_value=True)
    client.trigger_cronjob = AsyncMock(
        return_value={"success": True, "job_name": "test-job-123"}
    )
    client.suspend_cronjob = AsyncMock(return_value={"success": True})
    client.resume_cronjob = AsyncMock(return_value={"success": True})
    return client


@pytest.fixture
def setup_domain_data(hass: HomeAssistant, mock_client) -> None:
    """Set up hass.data with kubernetes domain data."""
    mock_coordinator = MagicMock()
    mock_coordinator.client = mock_client
    hass.data[DOMAIN] = {
        "test-entry-id": {
            "config": {
                "host": "test-cluster.example.com",
                "port": 6443,
                "api_token": "test-token",
                "namespace": "default",
                "verify_ssl": True,
            },
            "coordinator": mock_coordinator,
        }
    }


class TestServiceRegistration:
    """Test service registration and unregistration."""

    async def test_async_setup_services(self, hass: HomeAssistant):
        """Test that all services are registered."""
        await async_setup_services(hass)

        assert hass.services.has_service(DOMAIN, SERVICE_SCALE_WORKLOAD)
        assert hass.services.has_service(DOMAIN, SERVICE_START_WORKLOAD)
        assert hass.services.has_service(DOMAIN, SERVICE_STOP_WORKLOAD)

    async def test_async_unload_services(self, hass: HomeAssistant):
        """Test that all services are unregistered."""
        await async_setup_services(hass)
        await async_unload_services(hass)

        assert not hass.services.has_service(DOMAIN, SERVICE_SCALE_WORKLOAD)
        assert not hass.services.has_service(DOMAIN, SERVICE_START_WORKLOAD)
        assert not hass.services.has_service(DOMAIN, SERVICE_STOP_WORKLOAD)


class TestGenericWorkloadServices:
    """Test generic workload services (scale_workload, start_workload, stop_workload)."""

    async def test_scale_workload_deployment(
        self, hass: HomeAssistant, mock_client, setup_domain_data
    ):
        """Test scaling a deployment using the generic scale_workload service."""
        hass.states.async_set(
            "switch.test_deployment",
            "on",
            {
                ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_DEPLOYMENT,
                "namespace": "default",
                "deployment_name": "test-deployment",
            },
        )
        await async_setup_services(hass)
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SCALE_WORKLOAD,
            {
                ATTR_WORKLOAD_NAME: "switch.test_deployment",
                ATTR_REPLICAS: 3,
                ATTR_NAMESPACE: "default",
            },
            blocking=True,
        )

        mock_client.scale_deployment.assert_called_once_with(
            "test-deployment", 3, "default"
        )

    async def test_start_workload_cronjob(
        self, hass: HomeAssistant, mock_client, setup_domain_data
    ):
        """Test starting a CronJob using the generic start_workload service."""
        mock_client.trigger_cronjob.return_value = {
            "success": True,
            "job_name": "test-job-123",
        }
        hass.states.async_set(
            "switch.test_cronjob",
            "on",
            {
                ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_CRONJOB,
                "namespace": "default",
                "cronjob_name": "test-cronjob",
            },
        )
        await async_setup_services(hass)
        await hass.services.async_call(
            DOMAIN,
            SERVICE_START_WORKLOAD,
            {
                ATTR_WORKLOAD_NAME: "switch.test_cronjob",
                ATTR_NAMESPACE: "default",
            },
            blocking=True,
        )

        mock_client.trigger_cronjob.assert_called_once_with("test-cronjob", "default")

    async def test_stop_workload_statefulset(
        self, hass: HomeAssistant, mock_client, setup_domain_data
    ):
        """Test stopping a StatefulSet using the generic stop_workload service."""
        hass.states.async_set(
            "switch.test_statefulset",
            "on",
            {
                ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_STATEFULSET,
                "namespace": "default",
                "statefulset_name": "test-statefulset",
            },
        )
        await async_setup_services(hass)
        await hass.services.async_call(
            DOMAIN,
            SERVICE_STOP_WORKLOAD,
            {
                ATTR_WORKLOAD_NAME: "switch.test_statefulset",
                ATTR_NAMESPACE: "default",
            },
            blocking=True,
        )

        mock_client.stop_statefulset.assert_called_once_with(
            "test-statefulset", "default"
        )

    async def test_stop_workload_cronjob_ignored(
        self, hass: HomeAssistant, mock_client, setup_domain_data
    ):
        """Test that stop_workload ignores CronJobs."""
        hass.states.async_set(
            "switch.test_cronjob",
            "on",
            {
                ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_CRONJOB,
                "namespace": "default",
                "cronjob_name": "test-cronjob",
            },
        )
        await async_setup_services(hass)
        await hass.services.async_call(
            DOMAIN,
            SERVICE_STOP_WORKLOAD,
            {
                ATTR_WORKLOAD_NAME: "switch.test_cronjob",
                ATTR_NAMESPACE: "default",
            },
            blocking=True,
        )

        mock_client.suspend_cronjob.assert_not_called()
        mock_client.stop_deployment.assert_not_called()
        mock_client.stop_statefulset.assert_not_called()

    async def test_stop_workload_with_workload_names_entity_id_list(
        self, hass: HomeAssistant, mock_client, setup_domain_data
    ):
        """Test stop_workload with workload_names as list of {entity_id: [switch.…, …]} (UI format)."""
        hass.states.async_set(
            "switch.default_audiobookshelf_audiobookshelf",
            "on",
            {
                ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_DEPLOYMENT,
                "namespace": "audiobookshelf",
                "deployment_name": "audiobookshelf",
            },
        )
        hass.states.async_set(
            "switch.default_cert_manager_cert_manager",
            "on",
            {
                ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_DEPLOYMENT,
                "namespace": "cert-manager",
                "deployment_name": "cert-manager",
            },
        )
        await async_setup_services(hass)
        await hass.services.async_call(
            DOMAIN,
            SERVICE_STOP_WORKLOAD,
            {
                ATTR_WORKLOAD_NAMES: [
                    {
                        "entity_id": [
                            "switch.default_audiobookshelf_audiobookshelf",
                            "switch.default_cert_manager_cert_manager",
                        ]
                    }
                ],
            },
            blocking=True,
        )

        assert mock_client.stop_deployment.call_count == 2
        mock_client.stop_deployment.assert_any_call("audiobookshelf", "audiobookshelf")
        mock_client.stop_deployment.assert_any_call("cert-manager", "cert-manager")


class TestServiceSelectorConfiguration:
    """Test that service selectors are correctly configured."""

    def test_services_yaml_selector_structure(self):
        """Test that all entity selectors have the correct structure."""
        services_yaml_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "custom_components",
            "kubernetes",
            "services.yaml",
        )

        with open(services_yaml_path) as f:
            services_config = yaml.safe_load(f)

        # Check that all services with entity selectors have the correct structure
        for service_name, service_config in services_config.items():
            fields = service_config.get("fields", {})
            for field_name, field_config in fields.items():
                selector_config = field_config.get("selector", {})

                # Check entity selector
                if "entity" in selector_config:
                    entity_selector = selector_config["entity"]
                    assert "domain" in entity_selector, (
                        f"{service_name}.{field_name} entity selector missing domain"
                    )
                    assert entity_selector["domain"] == "switch", (
                        f"{service_name}.{field_name} entity selector has wrong domain"
                    )
                    assert "integration" in entity_selector, (
                        f"{service_name}.{field_name} entity selector missing integration"
                    )
                    assert entity_selector["integration"] == DOMAIN, (
                        f"{service_name}.{field_name} entity selector has wrong integration"
                    )

                # Check target selector (for multi-select fields)
                if "target" in selector_config:
                    target_selector = selector_config["target"]
                    assert "entity" in target_selector, (
                        f"{service_name}.{field_name} target selector missing entity"
                    )
                    entity_selector = target_selector["entity"]
                    assert "domain" in entity_selector, (
                        f"{service_name}.{field_name} target entity selector missing domain"
                    )
                    assert entity_selector["domain"] == "switch", (
                        f"{service_name}.{field_name} target entity selector has wrong domain"
                    )
                    assert "integration" in entity_selector, (
                        f"{service_name}.{field_name} target entity selector missing integration"
                    )
                    assert entity_selector["integration"] == DOMAIN, (
                        f"{service_name}.{field_name} target entity selector has wrong integration"
                    )


class TestNormalizeEntityIdList:
    """Test the _normalize_entity_id_list helper."""

    def test_none_returns_empty(self):
        assert _normalize_entity_id_list(None) == []

    def test_empty_list_returns_empty(self):
        assert _normalize_entity_id_list([]) == []

    def test_list_of_strings(self):
        assert _normalize_entity_id_list(["switch.a", "switch.b"]) == [
            "switch.a",
            "switch.b",
        ]

    def test_list_strips_whitespace(self):
        assert _normalize_entity_id_list(["  switch.a  ", " switch.b"]) == [
            "switch.a",
            "switch.b",
        ]

    def test_list_skips_empty_strings(self):
        assert _normalize_entity_id_list(["switch.a", "", "  "]) == ["switch.a"]

    def test_single_string(self):
        assert _normalize_entity_id_list("switch.a") == ["switch.a"]

    def test_comma_separated_string(self):
        assert _normalize_entity_id_list("switch.a, switch.b, switch.c") == [
            "switch.a",
            "switch.b",
            "switch.c",
        ]

    def test_single_string_strips_whitespace(self):
        assert _normalize_entity_id_list("  switch.a  ") == ["switch.a"]

    def test_unsupported_type_returns_empty(self):
        assert _normalize_entity_id_list(42) == []

    def test_list_skips_non_string_items(self):
        assert _normalize_entity_id_list(["switch.a", 123, None]) == ["switch.a"]


class TestValidateEntityWorkloadType:
    """Test the _validate_entity_workload_type helper."""

    async def test_non_switch_entity_always_valid(self, hass: HomeAssistant):
        assert (
            _validate_entity_workload_type(hass, "my-deployment", "Deployment") is True
        )

    async def test_switch_entity_correct_type(self, hass: HomeAssistant):
        hass.states.async_set(
            "switch.nginx",
            "on",
            {ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_DEPLOYMENT},
        )
        assert (
            _validate_entity_workload_type(
                hass, "switch.nginx", WORKLOAD_TYPE_DEPLOYMENT
            )
            is True
        )

    async def test_switch_entity_wrong_type(self, hass: HomeAssistant):
        hass.states.async_set(
            "switch.nginx",
            "on",
            {ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_STATEFULSET},
        )
        assert (
            _validate_entity_workload_type(
                hass, "switch.nginx", WORKLOAD_TYPE_DEPLOYMENT
            )
            is False
        )

    async def test_switch_entity_not_found(self, hass: HomeAssistant):
        assert (
            _validate_entity_workload_type(
                hass, "switch.missing", WORKLOAD_TYPE_DEPLOYMENT
            )
            is False
        )

    async def test_switch_entity_no_attributes(self, hass: HomeAssistant):
        # Real HA State with no explicit attributes has empty MappingProxyType (falsy)
        hass.states.async_set("switch.noattr", "on")
        assert (
            _validate_entity_workload_type(
                hass, "switch.noattr", WORKLOAD_TYPE_DEPLOYMENT
            )
            is False
        )

    def test_exception_returns_false(self):
        mock_hass = MagicMock()
        mock_hass.states.get.side_effect = Exception("boom")
        assert (
            _validate_entity_workload_type(
                mock_hass, "switch.error", WORKLOAD_TYPE_DEPLOYMENT
            )
            is False
        )


class TestGetWorkloadInfoFromEntity:
    """Test the _get_workload_info_from_entity helper."""

    async def test_switch_entity_deployment(self, hass: HomeAssistant):
        hass.states.async_set(
            "switch.nginx",
            "on",
            {
                ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_DEPLOYMENT,
                "namespace": "production",
                "deployment_name": "nginx",
            },
        )
        ns, name, wtype = _get_workload_info_from_entity(hass, "switch.nginx")
        assert ns == "production"
        assert name == "nginx"
        assert wtype == WORKLOAD_TYPE_DEPLOYMENT

    async def test_switch_entity_statefulset(self, hass: HomeAssistant):
        hass.states.async_set(
            "switch.redis",
            "on",
            {
                ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_STATEFULSET,
                "namespace": "default",
                "statefulset_name": "redis",
            },
        )
        ns, name, wtype = _get_workload_info_from_entity(hass, "switch.redis")
        assert name == "redis"
        assert wtype == WORKLOAD_TYPE_STATEFULSET

    async def test_switch_entity_cronjob(self, hass: HomeAssistant):
        hass.states.async_set(
            "switch.backup",
            "on",
            {
                ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_CRONJOB,
                "namespace": "default",
                "cronjob_name": "backup",
            },
        )
        ns, name, wtype = _get_workload_info_from_entity(hass, "switch.backup")
        assert name == "backup"
        assert wtype == WORKLOAD_TYPE_CRONJOB

    async def test_non_switch_entity_builds_id(self, hass: HomeAssistant):
        # The function prepends "switch." to bare names, so "nginx" → "switch.nginx"
        hass.states.async_set(
            "switch.nginx",
            "on",
            {
                ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_DEPLOYMENT,
                "namespace": "default",
                "deployment_name": "nginx",
            },
        )
        ns, name, wtype = _get_workload_info_from_entity(hass, "nginx")
        assert ns == "default"
        assert name == "nginx"
        assert wtype == WORKLOAD_TYPE_DEPLOYMENT

    async def test_entity_not_found_returns_nones(self, hass: HomeAssistant):
        ns, name, wtype = _get_workload_info_from_entity(hass, "switch.missing")
        assert ns is None
        assert name is None
        assert wtype is None

    def test_exception_returns_nones(self):
        mock_hass = MagicMock()
        mock_hass.states.get.side_effect = Exception("boom")
        ns, name, wtype = _get_workload_info_from_entity(mock_hass, "switch.error")
        assert ns is None
        assert name is None
        assert wtype is None


class TestExtractWorkloadInfo:
    """Test the _extract_workload_info helper."""

    async def test_workload_name_string_switch(self, hass: HomeAssistant):
        hass.states.async_set(
            "switch.nginx",
            "on",
            {
                ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_DEPLOYMENT,
                "namespace": "default",
                "deployment_name": "nginx",
            },
        )
        result = _extract_workload_info({ATTR_WORKLOAD_NAME: "switch.nginx"}, hass)
        assert result == [("nginx", "default", WORKLOAD_TYPE_DEPLOYMENT)]

    async def test_workload_name_dict_with_entity_id(self, hass: HomeAssistant):
        hass.states.async_set(
            "switch.redis",
            "on",
            {
                ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_STATEFULSET,
                "namespace": "prod",
                "statefulset_name": "redis",
            },
        )
        result = _extract_workload_info(
            {ATTR_WORKLOAD_NAME: {"entity_id": "switch.redis"}}, hass
        )
        assert result == [("redis", "prod", WORKLOAD_TYPE_STATEFULSET)]

    async def test_workload_names_as_string(self, hass: HomeAssistant):
        hass.states.async_set(
            "switch.nginx",
            "on",
            {
                ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_DEPLOYMENT,
                "namespace": "default",
                "deployment_name": "nginx",
            },
        )
        result = _extract_workload_info({ATTR_WORKLOAD_NAMES: "switch.nginx"}, hass)
        assert result == [("nginx", "default", WORKLOAD_TYPE_DEPLOYMENT)]

    async def test_workload_names_as_dict_entity_id(self, hass: HomeAssistant):
        hass.states.async_set(
            "switch.app",
            "on",
            {
                ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_DEPLOYMENT,
                "namespace": "default",
                "deployment_name": "app",
            },
        )
        result = _extract_workload_info(
            {ATTR_WORKLOAD_NAMES: {"entity_id": ["switch.app"]}}, hass
        )
        assert result == [("app", "default", WORKLOAD_TYPE_DEPLOYMENT)]

    async def test_workload_names_as_list_of_strings(self, hass: HomeAssistant):
        hass.states.async_set(
            "switch.a",
            "on",
            {
                ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_DEPLOYMENT,
                "namespace": "ns1",
                "deployment_name": "a",
            },
        )
        hass.states.async_set(
            "switch.b",
            "on",
            {
                ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_STATEFULSET,
                "namespace": "ns2",
                "statefulset_name": "b",
            },
        )
        result = _extract_workload_info(
            {ATTR_WORKLOAD_NAMES: ["switch.a", "switch.b"]}, hass
        )
        assert len(result) == 2
        assert ("a", "ns1", WORKLOAD_TYPE_DEPLOYMENT) in result
        assert ("b", "ns2", WORKLOAD_TYPE_STATEFULSET) in result

    async def test_workload_names_list_of_dicts(self, hass: HomeAssistant):
        hass.states.async_set(
            "switch.app",
            "on",
            {
                ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_DEPLOYMENT,
                "namespace": "default",
                "deployment_name": "app",
            },
        )
        result = _extract_workload_info(
            {ATTR_WORKLOAD_NAMES: [{"entity_id": ["switch.app"]}]}, hass
        )
        assert result == [("app", "default", WORKLOAD_TYPE_DEPLOYMENT)]

    async def test_target_fallback(self, hass: HomeAssistant):
        hass.states.async_set(
            "switch.app",
            "on",
            {
                ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_DEPLOYMENT,
                "namespace": "default",
                "deployment_name": "app",
            },
        )
        result = _extract_workload_info({"target": {"entity_id": ["switch.app"]}}, hass)
        assert result == [("app", "default", WORKLOAD_TYPE_DEPLOYMENT)]

    async def test_provided_namespace_overrides(self, hass: HomeAssistant):
        hass.states.async_set(
            "switch.app",
            "on",
            {
                ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_DEPLOYMENT,
                "namespace": "original",
                "deployment_name": "app",
            },
        )
        result = _extract_workload_info(
            {ATTR_WORKLOAD_NAME: "switch.app", ATTR_NAMESPACE: "override"},
            hass,
        )
        assert result == [("app", "override", WORKLOAD_TYPE_DEPLOYMENT)]

    async def test_entity_not_found_returns_empty(self, hass: HomeAssistant):
        result = _extract_workload_info({ATTR_WORKLOAD_NAME: "switch.missing"}, hass)
        assert result == []

    async def test_no_workload_keys_returns_empty(self, hass: HomeAssistant):
        result = _extract_workload_info({}, hass)
        assert result == []


class TestLogNoWorkloadsFound:
    """Test the _log_no_workloads_found helper."""

    def test_logs_with_workload_name_string(self):
        call_data = {ATTR_WORKLOAD_NAME: "switch.nginx"}
        # Should not raise
        _log_no_workloads_found(call_data, "scale_workload")

    def test_logs_with_workload_names_list(self):
        call_data = {ATTR_WORKLOAD_NAMES: ["switch.a", "switch.b"]}
        _log_no_workloads_found(call_data, "stop_workload")

    def test_logs_with_workload_names_dict(self):
        call_data = {ATTR_WORKLOAD_NAMES: {"entity_id": "switch.x"}}
        _log_no_workloads_found(call_data, "start_workload")

    def test_logs_with_workload_names_dict_list_entity_id(self):
        call_data = {ATTR_WORKLOAD_NAMES: {"entity_id": ["switch.x", "switch.y"]}}
        _log_no_workloads_found(call_data, "start_workload")

    def test_logs_with_no_relevant_keys(self):
        call_data = {}
        _log_no_workloads_found(call_data, "scale_workload")


class TestServiceHandlerEdgeCases:
    """Test edge cases in the service handler functions."""

    async def test_scale_workload_no_workloads_found(
        self, hass: HomeAssistant, mock_client, setup_domain_data
    ):
        """Test scale_workload logs error when no workloads found."""
        await async_setup_services(hass)
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SCALE_WORKLOAD,
            {ATTR_WORKLOAD_NAME: "switch.missing", ATTR_REPLICAS: 2},
            blocking=True,
        )
        mock_client.scale_deployment.assert_not_called()

    async def test_scale_workload_statefulset(
        self, hass: HomeAssistant, mock_client, setup_domain_data
    ):
        """Test scale_workload scales a StatefulSet."""
        hass.states.async_set(
            "switch.redis",
            "on",
            {
                ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_STATEFULSET,
                "namespace": "default",
                "statefulset_name": "redis",
            },
        )
        await async_setup_services(hass)
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SCALE_WORKLOAD,
            {
                ATTR_WORKLOAD_NAME: "switch.redis",
                ATTR_REPLICAS: 2,
                ATTR_NAMESPACE: "default",
            },
            blocking=True,
        )
        mock_client.scale_statefulset.assert_called_once_with("redis", 2, "default")

    async def test_scale_workload_unsupported_type(
        self, hass: HomeAssistant, mock_client, setup_domain_data
    ):
        """Test scale_workload warns for CronJob type."""
        hass.states.async_set(
            "switch.backup",
            "on",
            {
                ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_CRONJOB,
                "namespace": "default",
                "cronjob_name": "backup",
            },
        )
        await async_setup_services(hass)
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SCALE_WORKLOAD,
            {ATTR_WORKLOAD_NAME: "switch.backup", ATTR_REPLICAS: 1},
            blocking=True,
        )
        mock_client.scale_deployment.assert_not_called()
        mock_client.scale_statefulset.assert_not_called()

    async def test_scale_workload_failure_logged(
        self, hass: HomeAssistant, mock_client, setup_domain_data
    ):
        """Test scale_workload logs error when scale returns False."""
        mock_client.scale_deployment.return_value = False
        hass.states.async_set(
            "switch.nginx",
            "on",
            {
                ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_DEPLOYMENT,
                "namespace": "default",
                "deployment_name": "nginx",
            },
        )
        await async_setup_services(hass)
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SCALE_WORKLOAD,
            {
                ATTR_WORKLOAD_NAME: "switch.nginx",
                ATTR_REPLICAS: 3,
                ATTR_NAMESPACE: "default",
            },
            blocking=True,
        )
        mock_client.scale_deployment.assert_called_once()

    async def test_scale_workload_no_kubernetes_data(
        self, hass: HomeAssistant, mock_client, setup_domain_data
    ):
        """Test scale_workload exits early when no kubernetes data in hass."""
        hass.states.async_set(
            "switch.nginx",
            "on",
            {
                ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_DEPLOYMENT,
                "namespace": "default",
                "deployment_name": "nginx",
            },
        )
        await async_setup_services(hass)
        hass.data.pop(DOMAIN, None)
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SCALE_WORKLOAD,
            {ATTR_WORKLOAD_NAME: "switch.nginx", ATTR_REPLICAS: 2},
            blocking=True,
        )
        mock_client.scale_deployment.assert_not_called()

    async def test_scale_multiple_workloads_logs_completion(
        self, hass: HomeAssistant, mock_client, setup_domain_data
    ):
        """Test scale_workload logs completion when multiple workloads scaled."""
        hass.states.async_set(
            "switch.a",
            "on",
            {
                ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_DEPLOYMENT,
                "namespace": "default",
                "deployment_name": "a",
            },
        )
        hass.states.async_set(
            "switch.b",
            "on",
            {
                ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_DEPLOYMENT,
                "namespace": "default",
                "deployment_name": "b",
            },
        )
        await async_setup_services(hass)
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SCALE_WORKLOAD,
            {
                ATTR_WORKLOAD_NAMES: ["switch.a", "switch.b"],
                ATTR_REPLICAS: 1,
            },
            blocking=True,
        )
        assert mock_client.scale_deployment.call_count == 2

    async def test_start_workload_deployment(
        self, hass: HomeAssistant, mock_client, setup_domain_data
    ):
        """Test start_workload starts a Deployment."""
        hass.states.async_set(
            "switch.nginx",
            "on",
            {
                ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_DEPLOYMENT,
                "namespace": "default",
                "deployment_name": "nginx",
            },
        )
        await async_setup_services(hass)
        await hass.services.async_call(
            DOMAIN,
            SERVICE_START_WORKLOAD,
            {
                ATTR_WORKLOAD_NAME: "switch.nginx",
                ATTR_REPLICAS: 2,
                ATTR_NAMESPACE: "default",
            },
            blocking=True,
        )
        mock_client.start_deployment.assert_called_once_with("nginx", 2, "default")

    async def test_start_workload_statefulset(
        self, hass: HomeAssistant, mock_client, setup_domain_data
    ):
        """Test start_workload starts a StatefulSet."""
        hass.states.async_set(
            "switch.redis",
            "on",
            {
                ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_STATEFULSET,
                "namespace": "default",
                "statefulset_name": "redis",
            },
        )
        await async_setup_services(hass)
        await hass.services.async_call(
            DOMAIN,
            SERVICE_START_WORKLOAD,
            {
                ATTR_WORKLOAD_NAME: "switch.redis",
                ATTR_REPLICAS: 1,
                ATTR_NAMESPACE: "default",
            },
            blocking=True,
        )
        mock_client.start_statefulset.assert_called_once_with("redis", 1, "default")

    async def test_start_workload_cronjob_failure(
        self, hass: HomeAssistant, mock_client, setup_domain_data
    ):
        """Test start_workload logs error when CronJob trigger fails."""
        mock_client.trigger_cronjob.return_value = {
            "success": False,
            "error": "quota exceeded",
        }
        hass.states.async_set(
            "switch.backup",
            "on",
            {
                ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_CRONJOB,
                "namespace": "default",
                "cronjob_name": "backup",
            },
        )
        await async_setup_services(hass)
        await hass.services.async_call(
            DOMAIN,
            SERVICE_START_WORKLOAD,
            {
                ATTR_WORKLOAD_NAME: "switch.backup",
                ATTR_NAMESPACE: "default",
            },
            blocking=True,
        )
        mock_client.trigger_cronjob.assert_called_once_with("backup", "default")

    async def test_start_workload_unsupported_type(
        self, hass: HomeAssistant, mock_client, setup_domain_data
    ):
        """Test start_workload warns for unsupported type."""
        hass.states.async_set(
            "switch.ds",
            "on",
            {
                ATTR_WORKLOAD_TYPE: "DaemonSet",
                "namespace": "default",
            },
        )
        await async_setup_services(hass)
        await hass.services.async_call(
            DOMAIN,
            SERVICE_START_WORKLOAD,
            {ATTR_WORKLOAD_NAME: "switch.ds", ATTR_REPLICAS: 1},
            blocking=True,
        )
        mock_client.start_deployment.assert_not_called()
        mock_client.start_statefulset.assert_not_called()

    async def test_start_workload_no_workloads(
        self, hass: HomeAssistant, mock_client, setup_domain_data
    ):
        """Test start_workload logs error when no workloads found."""
        await async_setup_services(hass)
        await hass.services.async_call(
            DOMAIN,
            SERVICE_START_WORKLOAD,
            {ATTR_WORKLOAD_NAME: "switch.missing"},
            blocking=True,
        )
        mock_client.start_deployment.assert_not_called()

    async def test_stop_workload_deployment(
        self, hass: HomeAssistant, mock_client, setup_domain_data
    ):
        """Test stop_workload stops a Deployment."""
        hass.states.async_set(
            "switch.nginx",
            "on",
            {
                ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_DEPLOYMENT,
                "namespace": "default",
                "deployment_name": "nginx",
            },
        )
        await async_setup_services(hass)
        await hass.services.async_call(
            DOMAIN,
            SERVICE_STOP_WORKLOAD,
            {
                ATTR_WORKLOAD_NAME: "switch.nginx",
                ATTR_NAMESPACE: "default",
            },
            blocking=True,
        )
        mock_client.stop_deployment.assert_called_once_with("nginx", "default")

    async def test_stop_workload_deployment_failure(
        self, hass: HomeAssistant, mock_client, setup_domain_data
    ):
        """Test stop_workload logs error when stop returns False."""
        mock_client.stop_deployment.return_value = False
        hass.states.async_set(
            "switch.nginx",
            "on",
            {
                ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_DEPLOYMENT,
                "namespace": "default",
                "deployment_name": "nginx",
            },
        )
        await async_setup_services(hass)
        await hass.services.async_call(
            DOMAIN,
            SERVICE_STOP_WORKLOAD,
            {
                ATTR_WORKLOAD_NAME: "switch.nginx",
                ATTR_NAMESPACE: "default",
            },
            blocking=True,
        )
        mock_client.stop_deployment.assert_called_once()

    async def test_stop_workload_statefulset_failure(
        self, hass: HomeAssistant, mock_client, setup_domain_data
    ):
        """Test stop_workload logs error when StatefulSet stop returns False."""
        mock_client.stop_statefulset.return_value = False
        hass.states.async_set(
            "switch.redis",
            "on",
            {
                ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_STATEFULSET,
                "namespace": "default",
                "statefulset_name": "redis",
            },
        )
        await async_setup_services(hass)
        await hass.services.async_call(
            DOMAIN,
            SERVICE_STOP_WORKLOAD,
            {
                ATTR_WORKLOAD_NAME: "switch.redis",
                ATTR_NAMESPACE: "default",
            },
            blocking=True,
        )
        mock_client.stop_statefulset.assert_called_once_with("redis", "default")

    async def test_stop_workload_unsupported_type(
        self, hass: HomeAssistant, mock_client, setup_domain_data
    ):
        """Test stop_workload warns for unsupported types."""
        hass.states.async_set(
            "switch.ds",
            "on",
            {
                ATTR_WORKLOAD_TYPE: "DaemonSet",
                "namespace": "default",
            },
        )
        await async_setup_services(hass)
        await hass.services.async_call(
            DOMAIN,
            SERVICE_STOP_WORKLOAD,
            {ATTR_WORKLOAD_NAME: "switch.ds"},
            blocking=True,
        )
        mock_client.stop_deployment.assert_not_called()

    async def test_stop_workload_no_workloads(
        self, hass: HomeAssistant, mock_client, setup_domain_data
    ):
        """Test stop_workload logs error when no workloads found."""
        await async_setup_services(hass)
        await hass.services.async_call(
            DOMAIN,
            SERVICE_STOP_WORKLOAD,
            {ATTR_WORKLOAD_NAME: "switch.missing"},
            blocking=True,
        )
        mock_client.stop_deployment.assert_not_called()

    async def test_stop_workload_no_kubernetes_data(
        self, hass: HomeAssistant, mock_client, setup_domain_data
    ):
        """Test stop_workload exits early when no kubernetes data."""
        hass.states.async_set(
            "switch.nginx",
            "on",
            {
                ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_DEPLOYMENT,
                "namespace": "default",
                "deployment_name": "nginx",
            },
        )
        await async_setup_services(hass)
        hass.data.pop(DOMAIN, None)
        await hass.services.async_call(
            DOMAIN,
            SERVICE_STOP_WORKLOAD,
            {ATTR_WORKLOAD_NAME: "switch.nginx"},
            blocking=True,
        )
        mock_client.stop_deployment.assert_not_called()

    async def test_start_workload_no_kubernetes_data(
        self, hass: HomeAssistant, mock_client, setup_domain_data
    ):
        """Test start_workload exits early when no kubernetes data."""
        hass.states.async_set(
            "switch.nginx",
            "on",
            {
                ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_DEPLOYMENT,
                "namespace": "default",
                "deployment_name": "nginx",
            },
        )
        await async_setup_services(hass)
        hass.data.pop(DOMAIN, None)
        await hass.services.async_call(
            DOMAIN,
            SERVICE_START_WORKLOAD,
            {ATTR_WORKLOAD_NAME: "switch.nginx", ATTR_REPLICAS: 1},
            blocking=True,
        )
        mock_client.start_deployment.assert_not_called()


class TestResolveRawWorkloadName:
    """Tests for _resolve_raw_workload_name."""

    def _make_coordinator_with_data(self, data):
        """Create a mock coordinator with the given data."""
        coordinator = MagicMock()
        coordinator.data = data
        return coordinator

    async def test_resolves_deployment(self, hass: HomeAssistant):
        """Test resolves a deployment name to its type."""
        coordinator = self._make_coordinator_with_data(
            {
                "deployments": {
                    "nginx": {"name": "nginx", "namespace": "default"},
                },
                "statefulsets": {},
                "cronjobs": {},
            }
        )
        hass.data[DOMAIN] = {
            "entry_1": {"coordinator": coordinator},
        }

        result = _resolve_raw_workload_name(hass, "nginx", None)
        assert result == ("nginx", "default", WORKLOAD_TYPE_DEPLOYMENT)

    async def test_resolves_statefulset(self, hass: HomeAssistant):
        """Test resolves a statefulset name to its type."""
        coordinator = self._make_coordinator_with_data(
            {
                "deployments": {},
                "statefulsets": {
                    "redis": {"name": "redis", "namespace": "cache"},
                },
                "cronjobs": {},
            }
        )
        hass.data[DOMAIN] = {
            "entry_1": {"coordinator": coordinator},
        }

        result = _resolve_raw_workload_name(hass, "redis", None)
        assert result == ("redis", "cache", WORKLOAD_TYPE_STATEFULSET)

    async def test_resolves_cronjob(self, hass: HomeAssistant):
        """Test resolves a cronjob name to its type."""
        coordinator = self._make_coordinator_with_data(
            {
                "deployments": {},
                "statefulsets": {},
                "cronjobs": {
                    "backup": {"name": "backup", "namespace": "default"},
                },
            }
        )
        hass.data[DOMAIN] = {
            "entry_1": {"coordinator": coordinator},
        }

        result = _resolve_raw_workload_name(hass, "backup", None)
        assert result == ("backup", "default", WORKLOAD_TYPE_CRONJOB)

    async def test_filters_by_namespace(self, hass: HomeAssistant):
        """Test namespace filtering when provided."""
        coordinator = self._make_coordinator_with_data(
            {
                "deployments": {
                    "nginx-default": {"name": "nginx", "namespace": "default"},
                    "nginx-prod": {"name": "nginx", "namespace": "production"},
                },
                "statefulsets": {},
                "cronjobs": {},
            }
        )
        hass.data[DOMAIN] = {
            "entry_1": {"coordinator": coordinator},
        }

        result = _resolve_raw_workload_name(hass, "nginx", "production")
        assert result is not None
        assert result[1] == "production"

    async def test_returns_none_when_not_found(self, hass: HomeAssistant):
        """Test returns None when workload name doesn't match."""
        coordinator = self._make_coordinator_with_data(
            {
                "deployments": {},
                "statefulsets": {},
                "cronjobs": {},
            }
        )
        hass.data[DOMAIN] = {
            "entry_1": {"coordinator": coordinator},
        }

        result = _resolve_raw_workload_name(hass, "nonexistent", None)
        assert result is None

    async def test_returns_none_when_no_domain_data(self, hass: HomeAssistant):
        """Test returns None when no DOMAIN data exists."""
        result = _resolve_raw_workload_name(hass, "nginx", None)
        assert result is None

    async def test_skips_metadata_keys(self, hass: HomeAssistant):
        """Test skips panel_registered and other metadata keys."""
        coordinator = self._make_coordinator_with_data(
            {
                "deployments": {
                    "nginx": {"name": "nginx", "namespace": "default"},
                },
                "statefulsets": {},
                "cronjobs": {},
            }
        )
        hass.data[DOMAIN] = {
            "panel_registered": True,
            "switch_add_entities": MagicMock(),
            "entry_1": {"coordinator": coordinator},
        }

        result = _resolve_raw_workload_name(hass, "nginx", None)
        assert result == ("nginx", "default", WORKLOAD_TYPE_DEPLOYMENT)

    async def test_skips_entries_without_coordinator(self, hass: HomeAssistant):
        """Test skips entries that have no coordinator."""
        hass.data[DOMAIN] = {
            "entry_1": {"config": {}},
        }

        result = _resolve_raw_workload_name(hass, "nginx", None)
        assert result is None

    async def test_skips_coordinator_with_none_data(self, hass: HomeAssistant):
        """Test skips coordinator with None data."""
        coordinator = self._make_coordinator_with_data(None)
        hass.data[DOMAIN] = {
            "entry_1": {"coordinator": coordinator},
        }

        result = _resolve_raw_workload_name(hass, "nginx", None)
        assert result is None


class TestGetEntryData:
    """Tests for _get_entry_data helper."""

    async def test_returns_none_when_no_domain_data(self, hass: HomeAssistant):
        """Test returns None when no DOMAIN data exists."""
        result = _get_entry_data(hass, {})
        assert result is None

    async def test_returns_specified_entry(self, hass: HomeAssistant):
        """Test returns the entry matching entry_id."""
        entry_a = {"config": {"host": "a"}}
        entry_b = {"config": {"host": "b"}}
        hass.data[DOMAIN] = {"entry_a": entry_a, "entry_b": entry_b}

        result = _get_entry_data(hass, {"entry_id": "entry_b"})
        assert result is entry_b

    async def test_falls_back_to_first_entry(self, hass: HomeAssistant):
        """Test falls back to first real entry when no entry_id provided."""
        entry_a = {"config": {"host": "a"}}
        hass.data[DOMAIN] = {"entry_a": entry_a}

        result = _get_entry_data(hass, {})
        assert result is entry_a

    async def test_skips_metadata_keys(self, hass: HomeAssistant):
        """Test skips metadata keys when falling back."""
        entry_a = {"config": {"host": "a"}}
        hass.data[DOMAIN] = {"panel_registered": True, "entry_a": entry_a}

        result = _get_entry_data(hass, {})
        assert result is entry_a

    async def test_ignores_invalid_entry_id(self, hass: HomeAssistant):
        """Test falls back when entry_id doesn't match any entry."""
        entry_a = {"config": {"host": "a"}}
        hass.data[DOMAIN] = {"entry_a": entry_a}

        result = _get_entry_data(hass, {"entry_id": "nonexistent"})
        assert result is entry_a

    async def test_ignores_metadata_key_as_entry_id(self, hass: HomeAssistant):
        """Test rejects metadata keys passed as entry_id."""
        entry_a = {"config": {"host": "a"}}
        hass.data[DOMAIN] = {"panel_registered": True, "entry_a": entry_a}

        result = _get_entry_data(hass, {"entry_id": "panel_registered"})
        assert result is entry_a


class TestCollectEntityIds:
    """Tests for _collect_entity_ids."""

    def test_single_string_entity_id_in_workload_names(self):
        """Test single string entity_id via workload_names key."""
        result = _collect_entity_ids({ATTR_WORKLOAD_NAMES: "switch.nginx"})
        assert result == ["switch.nginx"]

    def test_list_of_entity_ids_in_workload_names(self):
        """Test list of entity_ids via workload_names key."""
        result = _collect_entity_ids(
            {ATTR_WORKLOAD_NAMES: ["switch.nginx", "switch.redis"]}
        )
        assert result == ["switch.nginx", "switch.redis"]

    def test_dict_with_entity_id_key_in_workload_names(self):
        """Test dict with entity_id key via workload_names."""
        result = _collect_entity_ids(
            {ATTR_WORKLOAD_NAMES: {"entity_id": "switch.nginx"}}
        )
        assert result == ["switch.nginx"]

    def test_dict_with_entity_ids_key_in_workload_names(self):
        """Test dict with entity_ids key (list) via workload_names."""
        result = _collect_entity_ids(
            {ATTR_WORKLOAD_NAMES: {"entity_ids": ["switch.nginx", "switch.redis"]}}
        )
        assert result == ["switch.nginx", "switch.redis"]

    def test_target_selector_format(self):
        """Test target selector format as fallback."""
        result = _collect_entity_ids({"target": {"entity_id": "switch.nginx"}})
        assert result == ["switch.nginx"]

    def test_target_fallback_only_when_workload_names_empty(self):
        """Test target is only used when workload_names yields no results."""
        result = _collect_entity_ids(
            {
                ATTR_WORKLOAD_NAMES: "switch.nginx",
                "target": {"entity_id": "switch.redis"},
            }
        )
        assert result == ["switch.nginx"]

    def test_comma_separated_string_in_workload_names(self):
        """Test comma-separated string via workload_names key."""
        result = _collect_entity_ids(
            {ATTR_WORKLOAD_NAMES: "switch.nginx, switch.redis"}
        )
        assert result == ["switch.nginx", "switch.redis"]

    def test_empty_workload_names_falls_back_to_target(self):
        """Test empty workload_names falls back to target."""
        result = _collect_entity_ids(
            {ATTR_WORKLOAD_NAMES: [], "target": "switch.nginx"}
        )
        assert result == ["switch.nginx"]

    def test_none_workload_names_falls_back_to_target(self):
        """Test None workload_names falls back to target."""
        result = _collect_entity_ids(
            {ATTR_WORKLOAD_NAMES: None, "target": "switch.nginx"}
        )
        assert result == ["switch.nginx"]

    def test_empty_dict_returns_empty(self):
        """Test empty call data returns empty list."""
        result = _collect_entity_ids({})
        assert result == []

    def test_filters_non_switch_entities(self):
        """Test that non-switch entities are filtered out."""
        result = _collect_entity_ids(
            {ATTR_WORKLOAD_NAMES: ["switch.nginx", "sensor.cpu", "switch.redis"]}
        )
        assert result == ["switch.nginx", "switch.redis"]

    def test_all_non_switch_entities_returns_empty(self):
        """Test that only non-switch entities returns empty list."""
        result = _collect_entity_ids(
            {ATTR_WORKLOAD_NAMES: ["sensor.cpu", "binary_sensor.health"]}
        )
        assert result == []

    def test_mixed_list_with_dicts_and_strings(self):
        """Test mixed list containing both dicts and strings in workload_names."""
        result = _collect_entity_ids(
            {
                ATTR_WORKLOAD_NAMES: [
                    {"entity_id": "switch.nginx"},
                    "switch.redis",
                ]
            }
        )
        assert result == ["switch.nginx", "switch.redis"]

    def test_target_with_list_of_entity_ids(self):
        """Test target with a list of entity IDs."""
        result = _collect_entity_ids({"target": ["switch.nginx", "switch.redis"]})
        assert result == ["switch.nginx", "switch.redis"]


class TestExtractEntityIdsFromValue:
    """Tests for _extract_entity_ids_from_value."""

    def test_string_input(self):
        """Test plain string input."""
        result = _extract_entity_ids_from_value("switch.nginx")
        assert result == ["switch.nginx"]

    def test_comma_separated_string_input(self):
        """Test comma-separated string input."""
        result = _extract_entity_ids_from_value("switch.nginx, switch.redis")
        assert result == ["switch.nginx", "switch.redis"]

    def test_list_of_strings(self):
        """Test list of strings input."""
        result = _extract_entity_ids_from_value(["switch.nginx", "switch.redis"])
        assert result == ["switch.nginx", "switch.redis"]

    def test_dict_with_entity_id(self):
        """Test dict with entity_id key."""
        result = _extract_entity_ids_from_value({"entity_id": "switch.nginx"})
        assert result == ["switch.nginx"]

    def test_dict_with_entity_ids(self):
        """Test dict with entity_ids key (list)."""
        result = _extract_entity_ids_from_value(
            {"entity_ids": ["switch.nginx", "switch.redis"]}
        )
        assert result == ["switch.nginx", "switch.redis"]

    def test_dict_with_neither_key(self):
        """Test dict without entity_id or entity_ids returns empty."""
        result = _extract_entity_ids_from_value({"foo": "bar"})
        assert result == []

    def test_mixed_list_with_dicts_and_strings(self):
        """Test mixed list containing dicts and strings."""
        result = _extract_entity_ids_from_value(
            [{"entity_id": "switch.nginx"}, "switch.redis"]
        )
        assert result == ["switch.nginx", "switch.redis"]

    def test_list_with_dict_entity_ids(self):
        """Test list containing dict with entity_ids (list) key."""
        result = _extract_entity_ids_from_value(
            [{"entity_ids": ["switch.nginx", "switch.redis"]}]
        )
        assert result == ["switch.nginx", "switch.redis"]

    def test_none_input(self):
        """Test None input returns empty list."""
        result = _extract_entity_ids_from_value(None)
        assert result == []

    def test_integer_input(self):
        """Test integer input returns empty list."""
        result = _extract_entity_ids_from_value(42)
        assert result == []

    def test_boolean_input(self):
        """Test boolean input returns empty list."""
        result = _extract_entity_ids_from_value(True)
        assert result == []

    def test_empty_string(self):
        """Test empty string returns empty list."""
        result = _extract_entity_ids_from_value("")
        assert result == []

    def test_empty_list(self):
        """Test empty list returns empty list."""
        result = _extract_entity_ids_from_value([])
        assert result == []

    def test_empty_dict(self):
        """Test empty dict returns empty list."""
        result = _extract_entity_ids_from_value({})
        assert result == []

    def test_list_with_non_string_non_dict_items(self):
        """Test list with non-string, non-dict items ignores them."""
        result = _extract_entity_ids_from_value(["switch.nginx", 42, None])
        assert result == ["switch.nginx"]

    def test_string_with_whitespace(self):
        """Test string values are trimmed of whitespace."""
        result = _extract_entity_ids_from_value("  switch.nginx  ")
        assert result == ["switch.nginx"]

    def test_dict_entity_id_prefers_entity_id_over_entity_ids(self):
        """Test dict with both entity_id and entity_ids uses entity_id first."""
        result = _extract_entity_ids_from_value(
            {"entity_id": "switch.nginx", "entity_ids": ["switch.redis"]}
        )
        assert result == ["switch.nginx"]


class TestValidateWorkloadSchema:
    """Tests for _validate_workload_schema."""

    def test_valid_with_workload_name(self):
        """Test passes validation when workload_name is provided."""
        data = {ATTR_WORKLOAD_NAME: "switch.nginx"}
        result = _validate_workload_schema(data)
        assert result is data

    def test_valid_with_workload_names(self):
        """Test passes validation when workload_names is provided."""
        data = {ATTR_WORKLOAD_NAMES: ["switch.nginx", "switch.redis"]}
        result = _validate_workload_schema(data)
        assert result is data

    def test_valid_with_both_fields(self):
        """Test passes validation when both workload_name and workload_names provided."""
        data = {
            ATTR_WORKLOAD_NAME: "switch.nginx",
            ATTR_WORKLOAD_NAMES: ["switch.redis"],
        }
        result = _validate_workload_schema(data)
        assert result is data

    def test_invalid_with_neither_field(self):
        """Test raises vol.Invalid when neither field provided."""
        import voluptuous as vol

        with pytest.raises(vol.Invalid, match="Either workload_name or workload_names"):
            _validate_workload_schema({})

    def test_invalid_with_unrelated_keys(self):
        """Test raises vol.Invalid when only unrelated keys are present."""
        import voluptuous as vol

        with pytest.raises(vol.Invalid, match="Either workload_name or workload_names"):
            _validate_workload_schema({"replicas": 3, "namespace": "default"})

    def test_valid_with_extra_keys(self):
        """Test passes validation when workload_name is present alongside other keys."""
        data = {
            ATTR_WORKLOAD_NAME: "switch.nginx",
            "replicas": 3,
            "namespace": "default",
        }
        result = _validate_workload_schema(data)
        assert result is data
