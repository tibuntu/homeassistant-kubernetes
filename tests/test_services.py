"""Tests for the Kubernetes services."""

import os
from unittest.mock import ANY, AsyncMock, MagicMock, patch

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
    _extract_workload_info,
    _get_entry_data,
    _get_workload_info_from_entity,
    _log_no_workloads_found,
    _normalize_entity_id_list,
    _resolve_raw_workload_name,
    _validate_entity_workload_type,
    async_setup_services,
    async_unload_services,
)


@pytest.fixture
def mock_hass():
    """Mock Home Assistant instance."""
    hass = MagicMock(spec=HomeAssistant)
    hass.services = MagicMock()
    hass.states = MagicMock()
    hass.data = {
        DOMAIN: {
            "test-entry-id": {
                "config": {
                    "host": "test-cluster.example.com",
                    "port": 6443,
                    "api_token": "test-token",
                    "namespace": "default",
                    "verify_ssl": True,
                }
            }
        }
    }
    return hass


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


class TestServiceRegistration:
    """Test service registration and unregistration."""

    async def test_async_setup_services(self, mock_hass):
        """Test that all services are registered."""
        with patch(
            "custom_components.kubernetes.kubernetes_client.KubernetesClient"
        ) as mock_client_class:
            mock_client_class.return_value = MagicMock()
            await async_setup_services(mock_hass)

        # Verify all services are registered
        registered_services = [
            SERVICE_SCALE_WORKLOAD,
            SERVICE_START_WORKLOAD,
            SERVICE_STOP_WORKLOAD,
        ]

        for service in registered_services:
            mock_hass.services.async_register.assert_any_call(
                DOMAIN, service, ANY, schema=ANY
            )

    async def test_async_unload_services(self, mock_hass):
        """Test that all services are unregistered."""
        await async_unload_services(mock_hass)

        # Verify all services are unregistered
        unregistered_services = [
            SERVICE_SCALE_WORKLOAD,
            SERVICE_START_WORKLOAD,
            SERVICE_STOP_WORKLOAD,
        ]

        for service in unregistered_services:
            mock_hass.services.async_remove.assert_any_call(DOMAIN, service)


class TestGenericWorkloadServices:
    """Test generic workload services (scale_workload, start_workload, stop_workload)."""

    async def test_scale_workload_deployment(self, mock_hass, mock_client):
        """Test scaling a deployment using the generic scale_workload service."""
        with patch(
            "custom_components.kubernetes.kubernetes_client.KubernetesClient"
        ) as mock_client_class:
            mock_client_class.return_value = mock_client

            await async_setup_services(mock_hass)

            # Find the scale_workload service function
            service_func = None
            for call_args in mock_hass.services.async_register.call_args_list:
                if call_args[0][1] == SERVICE_SCALE_WORKLOAD:
                    service_func = call_args[0][2]
                    break

            assert service_func is not None, "Service function not found"

            # Mock entity state
            mock_hass.states.get.return_value = MagicMock(
                attributes={
                    ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_DEPLOYMENT,
                    "namespace": "default",
                    "deployment_name": "test-deployment",
                }
            )

            # Create a mock call object
            mock_call = MagicMock()
            mock_call.data = {
                ATTR_WORKLOAD_NAME: "switch.test_deployment",
                ATTR_REPLICAS: 3,
                ATTR_NAMESPACE: "default",
            }

            # Execute service
            await service_func(mock_call)

            # Verify
            mock_client.scale_deployment.assert_called_once_with(
                "test-deployment", 3, "default"
            )

    async def test_start_workload_cronjob(self, mock_hass, mock_client):
        """Test starting a CronJob using the generic start_workload service."""
        with patch(
            "custom_components.kubernetes.kubernetes_client.KubernetesClient"
        ) as mock_client_class:
            mock_client_class.return_value = mock_client
            mock_client.trigger_cronjob.return_value = {
                "success": True,
                "job_name": "test-job-123",
            }

            await async_setup_services(mock_hass)

            # Find the start_workload service function
            service_func = None
            for call_args in mock_hass.services.async_register.call_args_list:
                if call_args[0][1] == SERVICE_START_WORKLOAD:
                    service_func = call_args[0][2]
                    break

            assert service_func is not None, "Service function not found"

            # Mock entity state
            mock_hass.states.get.return_value = MagicMock(
                attributes={
                    ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_CRONJOB,
                    "namespace": "default",
                    "cronjob_name": "test-cronjob",
                }
            )

            # Create a mock call object
            mock_call = MagicMock()
            mock_call.data = {
                ATTR_WORKLOAD_NAME: "switch.test_cronjob",
                ATTR_NAMESPACE: "default",
            }

            # Execute service
            await service_func(mock_call)

            # Verify
            mock_client.trigger_cronjob.assert_called_once_with(
                "test-cronjob", "default"
            )

    async def test_stop_workload_statefulset(self, mock_hass, mock_client):
        """Test stopping a StatefulSet using the generic stop_workload service."""
        with patch(
            "custom_components.kubernetes.kubernetes_client.KubernetesClient"
        ) as mock_client_class:
            mock_client_class.return_value = mock_client

            await async_setup_services(mock_hass)

            # Find the stop_workload service function
            service_func = None
            for call_args in mock_hass.services.async_register.call_args_list:
                if call_args[0][1] == SERVICE_STOP_WORKLOAD:
                    service_func = call_args[0][2]
                    break

            assert service_func is not None, "Service function not found"

            # Mock entity state
            mock_hass.states.get.return_value = MagicMock(
                attributes={
                    ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_STATEFULSET,
                    "namespace": "default",
                    "statefulset_name": "test-statefulset",
                }
            )

            # Create a mock call object
            mock_call = MagicMock()
            mock_call.data = {
                ATTR_WORKLOAD_NAME: "switch.test_statefulset",
                ATTR_NAMESPACE: "default",
            }

            # Execute service
            await service_func(mock_call)

            # Verify
            mock_client.stop_statefulset.assert_called_once_with(
                "test-statefulset", "default"
            )

    async def test_stop_workload_cronjob_ignored(self, mock_hass, mock_client):
        """Test that stop_workload ignores CronJobs."""
        with patch(
            "custom_components.kubernetes.kubernetes_client.KubernetesClient"
        ) as mock_client_class:
            mock_client_class.return_value = mock_client

            await async_setup_services(mock_hass)

            # Find the stop_workload service function
            service_func = None
            for call_args in mock_hass.services.async_register.call_args_list:
                if call_args[0][1] == SERVICE_STOP_WORKLOAD:
                    service_func = call_args[0][2]
                    break

            assert service_func is not None, "Service function not found"

            # Mock entity state for CronJob
            mock_hass.states.get.return_value = MagicMock(
                attributes={
                    ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_CRONJOB,
                    "namespace": "default",
                    "cronjob_name": "test-cronjob",
                }
            )

            # Create a mock call object
            mock_call = MagicMock()
            mock_call.data = {
                ATTR_WORKLOAD_NAME: "switch.test_cronjob",
                ATTR_NAMESPACE: "default",
            }

            # Execute service
            await service_func(mock_call)

            # Verify that suspend_cronjob was NOT called
            mock_client.suspend_cronjob.assert_not_called()

    async def test_stop_workload_with_workload_names_entity_id_list(
        self, mock_hass, mock_client
    ):
        """Test stop_workload with workload_names as list of {entity_id: [switch.…, …]} (UI format)."""
        with patch(
            "custom_components.kubernetes.kubernetes_client.KubernetesClient"
        ) as mock_client_class:
            mock_client_class.return_value = mock_client

            await async_setup_services(mock_hass)

            service_func = None
            for call_args in mock_hass.services.async_register.call_args_list:
                if call_args[0][1] == SERVICE_STOP_WORKLOAD:
                    service_func = call_args[0][2]
                    break

            assert service_func is not None, "Service function not found"

            # Mock states.get to return different attributes per entity_id (UI sends list of dicts)
            def states_get(entity_id):
                if entity_id == "switch.default_audiobookshelf_audiobookshelf":
                    return MagicMock(
                        attributes={
                            ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_DEPLOYMENT,
                            "namespace": "audiobookshelf",
                            "deployment_name": "audiobookshelf",
                        }
                    )
                if entity_id == "switch.default_cert_manager_cert_manager":
                    return MagicMock(
                        attributes={
                            ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_DEPLOYMENT,
                            "namespace": "cert-manager",
                            "deployment_name": "cert-manager",
                        }
                    )
                return None

            mock_hass.states.get.side_effect = states_get

            mock_call = MagicMock()
            mock_call.data = {
                ATTR_WORKLOAD_NAMES: [
                    {
                        "entity_id": [
                            "switch.default_audiobookshelf_audiobookshelf",
                            "switch.default_cert_manager_cert_manager",
                        ]
                    }
                ],
            }

            await service_func(mock_call)

            assert mock_client.stop_deployment.call_count == 2
            mock_client.stop_deployment.assert_any_call(
                "audiobookshelf", "audiobookshelf"
            )
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

    def test_non_switch_entity_always_valid(self):
        hass = MagicMock()
        assert (
            _validate_entity_workload_type(hass, "my-deployment", "Deployment") is True
        )
        hass.states.get.assert_not_called()

    def test_switch_entity_correct_type(self):
        hass = MagicMock()
        hass.states.get.return_value = MagicMock(
            attributes={ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_DEPLOYMENT}
        )
        assert (
            _validate_entity_workload_type(
                hass, "switch.nginx", WORKLOAD_TYPE_DEPLOYMENT
            )
            is True
        )

    def test_switch_entity_wrong_type(self):
        hass = MagicMock()
        hass.states.get.return_value = MagicMock(
            attributes={ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_STATEFULSET}
        )
        assert (
            _validate_entity_workload_type(
                hass, "switch.nginx", WORKLOAD_TYPE_DEPLOYMENT
            )
            is False
        )

    def test_switch_entity_not_found(self):
        hass = MagicMock()
        hass.states.get.return_value = None
        assert (
            _validate_entity_workload_type(
                hass, "switch.missing", WORKLOAD_TYPE_DEPLOYMENT
            )
            is False
        )

    def test_switch_entity_no_attributes(self):
        hass = MagicMock()
        hass.states.get.return_value = MagicMock(attributes=None)
        assert (
            _validate_entity_workload_type(
                hass, "switch.noattr", WORKLOAD_TYPE_DEPLOYMENT
            )
            is False
        )

    def test_exception_returns_false(self):
        hass = MagicMock()
        hass.states.get.side_effect = Exception("boom")
        assert (
            _validate_entity_workload_type(
                hass, "switch.error", WORKLOAD_TYPE_DEPLOYMENT
            )
            is False
        )


class TestGetWorkloadInfoFromEntity:
    """Test the _get_workload_info_from_entity helper."""

    def test_switch_entity_deployment(self):
        hass = MagicMock()
        hass.states.get.return_value = MagicMock(
            attributes={
                ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_DEPLOYMENT,
                "namespace": "production",
                "deployment_name": "nginx",
                "statefulset_name": None,
                "cronjob_name": None,
            }
        )
        ns, name, wtype = _get_workload_info_from_entity(hass, "switch.nginx")
        assert ns == "production"
        assert name == "nginx"
        assert wtype == WORKLOAD_TYPE_DEPLOYMENT

    def test_switch_entity_statefulset(self):
        hass = MagicMock()
        hass.states.get.return_value = MagicMock(
            attributes={
                ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_STATEFULSET,
                "namespace": "default",
                "deployment_name": None,
                "statefulset_name": "redis",
                "cronjob_name": None,
            }
        )
        ns, name, wtype = _get_workload_info_from_entity(hass, "switch.redis")
        assert name == "redis"
        assert wtype == WORKLOAD_TYPE_STATEFULSET

    def test_switch_entity_cronjob(self):
        hass = MagicMock()
        hass.states.get.return_value = MagicMock(
            attributes={
                ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_CRONJOB,
                "namespace": "default",
                "deployment_name": None,
                "statefulset_name": None,
                "cronjob_name": "backup",
            }
        )
        ns, name, wtype = _get_workload_info_from_entity(hass, "switch.backup")
        assert name == "backup"
        assert wtype == WORKLOAD_TYPE_CRONJOB

    def test_non_switch_entity_builds_id(self):
        hass = MagicMock()
        hass.states.get.return_value = MagicMock(
            attributes={
                ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_DEPLOYMENT,
                "namespace": "default",
                "deployment_name": "nginx",
                "statefulset_name": None,
                "cronjob_name": None,
            }
        )
        ns, name, wtype = _get_workload_info_from_entity(hass, "nginx")
        # Should have looked up "switch.nginx"
        hass.states.get.assert_called_once_with("switch.nginx")
        assert name == "nginx"

    def test_entity_not_found_returns_nones(self):
        hass = MagicMock()
        hass.states.get.return_value = None
        ns, name, wtype = _get_workload_info_from_entity(hass, "switch.missing")
        assert ns is None
        assert name is None
        assert wtype is None

    def test_exception_returns_nones(self):
        hass = MagicMock()
        hass.states.get.side_effect = Exception("boom")
        ns, name, wtype = _get_workload_info_from_entity(hass, "switch.error")
        assert ns is None
        assert name is None
        assert wtype is None


class TestExtractWorkloadInfo:
    """Test the _extract_workload_info helper."""

    def _make_hass(self, attrs):
        hass = MagicMock()
        hass.states.get.return_value = MagicMock(attributes=attrs)
        return hass

    def test_workload_name_string_switch(self):
        hass = self._make_hass(
            {
                ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_DEPLOYMENT,
                "namespace": "default",
                "deployment_name": "nginx",
                "statefulset_name": None,
                "cronjob_name": None,
            }
        )
        result = _extract_workload_info({ATTR_WORKLOAD_NAME: "switch.nginx"}, hass)
        assert result == [("nginx", "default", WORKLOAD_TYPE_DEPLOYMENT)]

    def test_workload_name_dict_with_entity_id(self):
        hass = self._make_hass(
            {
                ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_STATEFULSET,
                "namespace": "prod",
                "deployment_name": None,
                "statefulset_name": "redis",
                "cronjob_name": None,
            }
        )
        result = _extract_workload_info(
            {ATTR_WORKLOAD_NAME: {"entity_id": "switch.redis"}}, hass
        )
        assert result == [("redis", "prod", WORKLOAD_TYPE_STATEFULSET)]

    def test_workload_names_as_string(self):
        hass = self._make_hass(
            {
                ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_DEPLOYMENT,
                "namespace": "default",
                "deployment_name": "nginx",
                "statefulset_name": None,
                "cronjob_name": None,
            }
        )
        result = _extract_workload_info({ATTR_WORKLOAD_NAMES: "switch.nginx"}, hass)
        assert result == [("nginx", "default", WORKLOAD_TYPE_DEPLOYMENT)]

    def test_workload_names_as_dict_entity_id(self):
        hass = self._make_hass(
            {
                ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_DEPLOYMENT,
                "namespace": "default",
                "deployment_name": "app",
                "statefulset_name": None,
                "cronjob_name": None,
            }
        )
        result = _extract_workload_info(
            {ATTR_WORKLOAD_NAMES: {"entity_id": ["switch.app"]}}, hass
        )
        assert result == [("app", "default", WORKLOAD_TYPE_DEPLOYMENT)]

    def test_workload_names_as_list_of_strings(self):
        def states_get(eid):
            if eid == "switch.a":
                return MagicMock(
                    attributes={
                        ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_DEPLOYMENT,
                        "namespace": "ns1",
                        "deployment_name": "a",
                        "statefulset_name": None,
                        "cronjob_name": None,
                    }
                )
            if eid == "switch.b":
                return MagicMock(
                    attributes={
                        ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_STATEFULSET,
                        "namespace": "ns2",
                        "deployment_name": None,
                        "statefulset_name": "b",
                        "cronjob_name": None,
                    }
                )
            return None

        hass = MagicMock()
        hass.states.get.side_effect = states_get
        result = _extract_workload_info(
            {ATTR_WORKLOAD_NAMES: ["switch.a", "switch.b"]}, hass
        )
        assert len(result) == 2
        assert ("a", "ns1", WORKLOAD_TYPE_DEPLOYMENT) in result
        assert ("b", "ns2", WORKLOAD_TYPE_STATEFULSET) in result

    def test_workload_names_list_of_dicts(self):
        hass = self._make_hass(
            {
                ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_DEPLOYMENT,
                "namespace": "default",
                "deployment_name": "app",
                "statefulset_name": None,
                "cronjob_name": None,
            }
        )
        result = _extract_workload_info(
            {ATTR_WORKLOAD_NAMES: [{"entity_id": ["switch.app"]}]}, hass
        )
        assert result == [("app", "default", WORKLOAD_TYPE_DEPLOYMENT)]

    def test_target_fallback(self):
        hass = self._make_hass(
            {
                ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_DEPLOYMENT,
                "namespace": "default",
                "deployment_name": "app",
                "statefulset_name": None,
                "cronjob_name": None,
            }
        )
        result = _extract_workload_info({"target": {"entity_id": ["switch.app"]}}, hass)
        assert result == [("app", "default", WORKLOAD_TYPE_DEPLOYMENT)]

    def test_provided_namespace_overrides(self):
        hass = self._make_hass(
            {
                ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_DEPLOYMENT,
                "namespace": "original",
                "deployment_name": "app",
                "statefulset_name": None,
                "cronjob_name": None,
            }
        )
        result = _extract_workload_info(
            {ATTR_WORKLOAD_NAME: "switch.app", ATTR_NAMESPACE: "override"},
            hass,
        )
        assert result == [("app", "override", WORKLOAD_TYPE_DEPLOYMENT)]

    def test_entity_not_found_returns_empty(self):
        hass = MagicMock()
        hass.states.get.return_value = None
        result = _extract_workload_info({ATTR_WORKLOAD_NAME: "switch.missing"}, hass)
        assert result == []

    def test_no_workload_keys_returns_empty(self):
        hass = MagicMock()
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

    def _find_service(self, mock_hass, service_name):
        """Extract a registered service handler by name."""
        for call_args in mock_hass.services.async_register.call_args_list:
            if call_args[0][1] == service_name:
                return call_args[0][2]
        return None

    async def test_scale_workload_no_workloads_found(self, mock_hass, mock_client):
        """Test scale_workload logs error when no workloads found."""
        mock_hass.states.get.return_value = None
        with patch(
            "custom_components.kubernetes.kubernetes_client.KubernetesClient",
            return_value=mock_client,
        ):
            await async_setup_services(mock_hass)
            func = self._find_service(mock_hass, SERVICE_SCALE_WORKLOAD)
            mock_call = MagicMock()
            mock_call.data = {ATTR_WORKLOAD_NAME: "switch.missing", ATTR_REPLICAS: 2}
            await func(mock_call)
        mock_client.scale_deployment.assert_not_called()

    async def test_scale_workload_statefulset(self, mock_hass, mock_client):
        """Test scale_workload scales a StatefulSet."""
        mock_hass.states.get.return_value = MagicMock(
            attributes={
                ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_STATEFULSET,
                "namespace": "default",
                "deployment_name": None,
                "statefulset_name": "redis",
                "cronjob_name": None,
            }
        )
        with patch(
            "custom_components.kubernetes.kubernetes_client.KubernetesClient",
            return_value=mock_client,
        ):
            await async_setup_services(mock_hass)
            func = self._find_service(mock_hass, SERVICE_SCALE_WORKLOAD)
            mock_call = MagicMock()
            mock_call.data = {
                ATTR_WORKLOAD_NAME: "switch.redis",
                ATTR_REPLICAS: 2,
                ATTR_NAMESPACE: "default",
            }
            await func(mock_call)
        mock_client.scale_statefulset.assert_called_once_with("redis", 2, "default")

    async def test_scale_workload_unsupported_type(self, mock_hass, mock_client):
        """Test scale_workload warns for CronJob type."""
        mock_hass.states.get.return_value = MagicMock(
            attributes={
                ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_CRONJOB,
                "namespace": "default",
                "deployment_name": None,
                "statefulset_name": None,
                "cronjob_name": "backup",
            }
        )
        with patch(
            "custom_components.kubernetes.kubernetes_client.KubernetesClient",
            return_value=mock_client,
        ):
            await async_setup_services(mock_hass)
            func = self._find_service(mock_hass, SERVICE_SCALE_WORKLOAD)
            mock_call = MagicMock()
            mock_call.data = {ATTR_WORKLOAD_NAME: "switch.backup", ATTR_REPLICAS: 1}
            await func(mock_call)
        mock_client.scale_deployment.assert_not_called()
        mock_client.scale_statefulset.assert_not_called()

    async def test_scale_workload_failure_logged(self, mock_hass, mock_client):
        """Test scale_workload logs error when scale returns False."""
        mock_client.scale_deployment.return_value = False
        mock_hass.states.get.return_value = MagicMock(
            attributes={
                ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_DEPLOYMENT,
                "namespace": "default",
                "deployment_name": "nginx",
                "statefulset_name": None,
                "cronjob_name": None,
            }
        )
        with patch(
            "custom_components.kubernetes.kubernetes_client.KubernetesClient",
            return_value=mock_client,
        ):
            await async_setup_services(mock_hass)
            func = self._find_service(mock_hass, SERVICE_SCALE_WORKLOAD)
            mock_call = MagicMock()
            mock_call.data = {
                ATTR_WORKLOAD_NAME: "switch.nginx",
                ATTR_REPLICAS: 3,
                ATTR_NAMESPACE: "default",
            }
            await func(mock_call)
        mock_client.scale_deployment.assert_called_once()

    async def test_scale_workload_no_kubernetes_data(self, mock_hass, mock_client):
        """Test scale_workload exits early when no kubernetes data in hass."""
        mock_hass.states.get.return_value = MagicMock(
            attributes={
                ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_DEPLOYMENT,
                "namespace": "default",
                "deployment_name": "nginx",
                "statefulset_name": None,
                "cronjob_name": None,
            }
        )
        with patch(
            "custom_components.kubernetes.kubernetes_client.KubernetesClient",
            return_value=mock_client,
        ):
            await async_setup_services(mock_hass)
            func = self._find_service(mock_hass, SERVICE_SCALE_WORKLOAD)
            mock_hass.data = {}
            mock_call = MagicMock()
            mock_call.data = {ATTR_WORKLOAD_NAME: "switch.nginx", ATTR_REPLICAS: 2}
            await func(mock_call)
        mock_client.scale_deployment.assert_not_called()

    async def test_scale_multiple_workloads_logs_completion(
        self, mock_hass, mock_client
    ):
        """Test scale_workload logs completion when multiple workloads scaled."""

        def states_get(eid):
            if eid == "switch.a":
                return MagicMock(
                    attributes={
                        ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_DEPLOYMENT,
                        "namespace": "default",
                        "deployment_name": "a",
                        "statefulset_name": None,
                        "cronjob_name": None,
                    }
                )
            if eid == "switch.b":
                return MagicMock(
                    attributes={
                        ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_DEPLOYMENT,
                        "namespace": "default",
                        "deployment_name": "b",
                        "statefulset_name": None,
                        "cronjob_name": None,
                    }
                )
            return None

        mock_hass.states.get.side_effect = states_get
        with patch(
            "custom_components.kubernetes.kubernetes_client.KubernetesClient",
            return_value=mock_client,
        ):
            await async_setup_services(mock_hass)
            func = self._find_service(mock_hass, SERVICE_SCALE_WORKLOAD)
            mock_call = MagicMock()
            mock_call.data = {
                ATTR_WORKLOAD_NAMES: ["switch.a", "switch.b"],
                ATTR_REPLICAS: 1,
            }
            await func(mock_call)
        assert mock_client.scale_deployment.call_count == 2

    async def test_start_workload_deployment(self, mock_hass, mock_client):
        """Test start_workload starts a Deployment."""
        mock_hass.states.get.return_value = MagicMock(
            attributes={
                ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_DEPLOYMENT,
                "namespace": "default",
                "deployment_name": "nginx",
                "statefulset_name": None,
                "cronjob_name": None,
            }
        )
        with patch(
            "custom_components.kubernetes.kubernetes_client.KubernetesClient",
            return_value=mock_client,
        ):
            await async_setup_services(mock_hass)
            func = self._find_service(mock_hass, SERVICE_START_WORKLOAD)
            mock_call = MagicMock()
            mock_call.data = {
                ATTR_WORKLOAD_NAME: "switch.nginx",
                ATTR_REPLICAS: 2,
                ATTR_NAMESPACE: "default",
            }
            await func(mock_call)
        mock_client.start_deployment.assert_called_once_with("nginx", 2, "default")

    async def test_start_workload_statefulset(self, mock_hass, mock_client):
        """Test start_workload starts a StatefulSet."""
        mock_hass.states.get.return_value = MagicMock(
            attributes={
                ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_STATEFULSET,
                "namespace": "default",
                "deployment_name": None,
                "statefulset_name": "redis",
                "cronjob_name": None,
            }
        )
        with patch(
            "custom_components.kubernetes.kubernetes_client.KubernetesClient",
            return_value=mock_client,
        ):
            await async_setup_services(mock_hass)
            func = self._find_service(mock_hass, SERVICE_START_WORKLOAD)
            mock_call = MagicMock()
            mock_call.data = {
                ATTR_WORKLOAD_NAME: "switch.redis",
                ATTR_REPLICAS: 1,
                ATTR_NAMESPACE: "default",
            }
            await func(mock_call)
        mock_client.start_statefulset.assert_called_once_with("redis", 1, "default")

    async def test_start_workload_cronjob_failure(self, mock_hass, mock_client):
        """Test start_workload logs error when CronJob trigger fails."""
        mock_client.trigger_cronjob.return_value = {
            "success": False,
            "error": "quota exceeded",
        }
        mock_hass.states.get.return_value = MagicMock(
            attributes={
                ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_CRONJOB,
                "namespace": "default",
                "deployment_name": None,
                "statefulset_name": None,
                "cronjob_name": "backup",
            }
        )
        with patch(
            "custom_components.kubernetes.kubernetes_client.KubernetesClient",
            return_value=mock_client,
        ):
            await async_setup_services(mock_hass)
            func = self._find_service(mock_hass, SERVICE_START_WORKLOAD)
            mock_call = MagicMock()
            mock_call.data = {
                ATTR_WORKLOAD_NAME: "switch.backup",
                ATTR_NAMESPACE: "default",
            }
            await func(mock_call)
        mock_client.trigger_cronjob.assert_called_once_with("backup", "default")

    async def test_start_workload_unsupported_type(self, mock_hass, mock_client):
        """Test start_workload warns for unsupported type."""
        mock_hass.states.get.return_value = MagicMock(
            attributes={
                ATTR_WORKLOAD_TYPE: "DaemonSet",
                "namespace": "default",
                "deployment_name": None,
                "statefulset_name": None,
                "cronjob_name": None,
            }
        )
        with patch(
            "custom_components.kubernetes.kubernetes_client.KubernetesClient",
            return_value=mock_client,
        ):
            await async_setup_services(mock_hass)
            func = self._find_service(mock_hass, SERVICE_START_WORKLOAD)
            mock_call = MagicMock()
            mock_call.data = {ATTR_WORKLOAD_NAME: "switch.ds", ATTR_REPLICAS: 1}
            await func(mock_call)
        mock_client.start_deployment.assert_not_called()
        mock_client.start_statefulset.assert_not_called()

    async def test_start_workload_no_workloads(self, mock_hass, mock_client):
        """Test start_workload logs error when no workloads found."""
        mock_hass.states.get.return_value = None
        with patch(
            "custom_components.kubernetes.kubernetes_client.KubernetesClient",
            return_value=mock_client,
        ):
            await async_setup_services(mock_hass)
            func = self._find_service(mock_hass, SERVICE_START_WORKLOAD)
            mock_call = MagicMock()
            mock_call.data = {ATTR_WORKLOAD_NAME: "switch.missing"}
            await func(mock_call)
        mock_client.start_deployment.assert_not_called()

    async def test_stop_workload_deployment(self, mock_hass, mock_client):
        """Test stop_workload stops a Deployment."""
        mock_hass.states.get.return_value = MagicMock(
            attributes={
                ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_DEPLOYMENT,
                "namespace": "default",
                "deployment_name": "nginx",
                "statefulset_name": None,
                "cronjob_name": None,
            }
        )
        with patch(
            "custom_components.kubernetes.kubernetes_client.KubernetesClient",
            return_value=mock_client,
        ):
            await async_setup_services(mock_hass)
            func = self._find_service(mock_hass, SERVICE_STOP_WORKLOAD)
            mock_call = MagicMock()
            mock_call.data = {
                ATTR_WORKLOAD_NAME: "switch.nginx",
                ATTR_NAMESPACE: "default",
            }
            await func(mock_call)
        mock_client.stop_deployment.assert_called_once_with("nginx", "default")

    async def test_stop_workload_deployment_failure(self, mock_hass, mock_client):
        """Test stop_workload logs error when stop returns False."""
        mock_client.stop_deployment.return_value = False
        mock_hass.states.get.return_value = MagicMock(
            attributes={
                ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_DEPLOYMENT,
                "namespace": "default",
                "deployment_name": "nginx",
                "statefulset_name": None,
                "cronjob_name": None,
            }
        )
        with patch(
            "custom_components.kubernetes.kubernetes_client.KubernetesClient",
            return_value=mock_client,
        ):
            await async_setup_services(mock_hass)
            func = self._find_service(mock_hass, SERVICE_STOP_WORKLOAD)
            mock_call = MagicMock()
            mock_call.data = {
                ATTR_WORKLOAD_NAME: "switch.nginx",
                ATTR_NAMESPACE: "default",
            }
            await func(mock_call)
        mock_client.stop_deployment.assert_called_once()

    async def test_stop_workload_statefulset_failure(self, mock_hass, mock_client):
        """Test stop_workload logs error when StatefulSet stop returns False."""
        mock_client.stop_statefulset.return_value = False
        mock_hass.states.get.return_value = MagicMock(
            attributes={
                ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_STATEFULSET,
                "namespace": "default",
                "deployment_name": None,
                "statefulset_name": "redis",
                "cronjob_name": None,
            }
        )
        with patch(
            "custom_components.kubernetes.kubernetes_client.KubernetesClient",
            return_value=mock_client,
        ):
            await async_setup_services(mock_hass)
            func = self._find_service(mock_hass, SERVICE_STOP_WORKLOAD)
            mock_call = MagicMock()
            mock_call.data = {
                ATTR_WORKLOAD_NAME: "switch.redis",
                ATTR_NAMESPACE: "default",
            }
            await func(mock_call)
        mock_client.stop_statefulset.assert_called_once_with("redis", "default")

    async def test_stop_workload_unsupported_type(self, mock_hass, mock_client):
        """Test stop_workload warns for unsupported types."""
        mock_hass.states.get.return_value = MagicMock(
            attributes={
                ATTR_WORKLOAD_TYPE: "DaemonSet",
                "namespace": "default",
                "deployment_name": None,
                "statefulset_name": None,
                "cronjob_name": None,
            }
        )
        with patch(
            "custom_components.kubernetes.kubernetes_client.KubernetesClient",
            return_value=mock_client,
        ):
            await async_setup_services(mock_hass)
            func = self._find_service(mock_hass, SERVICE_STOP_WORKLOAD)
            mock_call = MagicMock()
            mock_call.data = {ATTR_WORKLOAD_NAME: "switch.ds"}
            await func(mock_call)
        mock_client.stop_deployment.assert_not_called()

    async def test_stop_workload_no_workloads(self, mock_hass, mock_client):
        """Test stop_workload logs error when no workloads found."""
        mock_hass.states.get.return_value = None
        with patch(
            "custom_components.kubernetes.kubernetes_client.KubernetesClient",
            return_value=mock_client,
        ):
            await async_setup_services(mock_hass)
            func = self._find_service(mock_hass, SERVICE_STOP_WORKLOAD)
            mock_call = MagicMock()
            mock_call.data = {ATTR_WORKLOAD_NAME: "switch.missing"}
            await func(mock_call)
        mock_client.stop_deployment.assert_not_called()

    async def test_stop_workload_no_kubernetes_data(self, mock_hass, mock_client):
        """Test stop_workload exits early when no kubernetes data."""
        mock_hass.states.get.return_value = MagicMock(
            attributes={
                ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_DEPLOYMENT,
                "namespace": "default",
                "deployment_name": "nginx",
                "statefulset_name": None,
                "cronjob_name": None,
            }
        )
        with patch(
            "custom_components.kubernetes.kubernetes_client.KubernetesClient",
            return_value=mock_client,
        ):
            await async_setup_services(mock_hass)
            func = self._find_service(mock_hass, SERVICE_STOP_WORKLOAD)
            mock_hass.data = {}
            mock_call = MagicMock()
            mock_call.data = {ATTR_WORKLOAD_NAME: "switch.nginx"}
            await func(mock_call)
        mock_client.stop_deployment.assert_not_called()

    async def test_start_workload_no_kubernetes_data(self, mock_hass, mock_client):
        """Test start_workload exits early when no kubernetes data."""
        mock_hass.states.get.return_value = MagicMock(
            attributes={
                ATTR_WORKLOAD_TYPE: WORKLOAD_TYPE_DEPLOYMENT,
                "namespace": "default",
                "deployment_name": "nginx",
                "statefulset_name": None,
                "cronjob_name": None,
            }
        )
        with patch(
            "custom_components.kubernetes.kubernetes_client.KubernetesClient",
            return_value=mock_client,
        ):
            await async_setup_services(mock_hass)
            func = self._find_service(mock_hass, SERVICE_START_WORKLOAD)
            mock_hass.data = {}
            mock_call = MagicMock()
            mock_call.data = {ATTR_WORKLOAD_NAME: "switch.nginx", ATTR_REPLICAS: 1}
            await func(mock_call)
        mock_client.start_deployment.assert_not_called()


class TestResolveRawWorkloadName:
    """Tests for _resolve_raw_workload_name."""

    def _make_coordinator_with_data(self, data):
        """Create a mock coordinator with the given data."""
        coordinator = MagicMock()
        coordinator.data = data
        return coordinator

    def test_resolves_deployment(self, mock_hass):
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
        mock_hass.data = {
            DOMAIN: {
                "entry_1": {"coordinator": coordinator},
            }
        }

        result = _resolve_raw_workload_name(mock_hass, "nginx", None)
        assert result == ("nginx", "default", WORKLOAD_TYPE_DEPLOYMENT)

    def test_resolves_statefulset(self, mock_hass):
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
        mock_hass.data = {
            DOMAIN: {
                "entry_1": {"coordinator": coordinator},
            }
        }

        result = _resolve_raw_workload_name(mock_hass, "redis", None)
        assert result == ("redis", "cache", WORKLOAD_TYPE_STATEFULSET)

    def test_resolves_cronjob(self, mock_hass):
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
        mock_hass.data = {
            DOMAIN: {
                "entry_1": {"coordinator": coordinator},
            }
        }

        result = _resolve_raw_workload_name(mock_hass, "backup", None)
        assert result == ("backup", "default", WORKLOAD_TYPE_CRONJOB)

    def test_filters_by_namespace(self, mock_hass):
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
        mock_hass.data = {
            DOMAIN: {
                "entry_1": {"coordinator": coordinator},
            }
        }

        result = _resolve_raw_workload_name(mock_hass, "nginx", "production")
        assert result is not None
        assert result[1] == "production"

    def test_returns_none_when_not_found(self, mock_hass):
        """Test returns None when workload name doesn't match."""
        coordinator = self._make_coordinator_with_data(
            {
                "deployments": {},
                "statefulsets": {},
                "cronjobs": {},
            }
        )
        mock_hass.data = {
            DOMAIN: {
                "entry_1": {"coordinator": coordinator},
            }
        }

        result = _resolve_raw_workload_name(mock_hass, "nonexistent", None)
        assert result is None

    def test_returns_none_when_no_domain_data(self, mock_hass):
        """Test returns None when no DOMAIN data exists."""
        mock_hass.data = {}

        result = _resolve_raw_workload_name(mock_hass, "nginx", None)
        assert result is None

    def test_skips_metadata_keys(self, mock_hass):
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
        mock_hass.data = {
            DOMAIN: {
                "panel_registered": True,
                "switch_add_entities": MagicMock(),
                "entry_1": {"coordinator": coordinator},
            }
        }

        result = _resolve_raw_workload_name(mock_hass, "nginx", None)
        assert result == ("nginx", "default", WORKLOAD_TYPE_DEPLOYMENT)

    def test_skips_entries_without_coordinator(self, mock_hass):
        """Test skips entries that have no coordinator."""
        mock_hass.data = {
            DOMAIN: {
                "entry_1": {"config": {}},
            }
        }

        result = _resolve_raw_workload_name(mock_hass, "nginx", None)
        assert result is None

    def test_skips_coordinator_with_none_data(self, mock_hass):
        """Test skips coordinator with None data."""
        coordinator = self._make_coordinator_with_data(None)
        mock_hass.data = {
            DOMAIN: {
                "entry_1": {"coordinator": coordinator},
            }
        }

        result = _resolve_raw_workload_name(mock_hass, "nginx", None)
        assert result is None


class TestGetEntryData:
    """Tests for _get_entry_data helper."""

    def test_returns_none_when_no_domain_data(self, mock_hass):
        """Test returns None when no DOMAIN data exists."""
        mock_hass.data = {}
        result = _get_entry_data(mock_hass, {})
        assert result is None

    def test_returns_specified_entry(self, mock_hass):
        """Test returns the entry matching entry_id."""
        entry_a = {"config": {"host": "a"}}
        entry_b = {"config": {"host": "b"}}
        mock_hass.data = {DOMAIN: {"entry_a": entry_a, "entry_b": entry_b}}

        result = _get_entry_data(mock_hass, {"entry_id": "entry_b"})
        assert result is entry_b

    def test_falls_back_to_first_entry(self, mock_hass):
        """Test falls back to first real entry when no entry_id provided."""
        entry_a = {"config": {"host": "a"}}
        mock_hass.data = {DOMAIN: {"entry_a": entry_a}}

        result = _get_entry_data(mock_hass, {})
        assert result is entry_a

    def test_skips_metadata_keys(self, mock_hass):
        """Test skips metadata keys when falling back."""
        entry_a = {"config": {"host": "a"}}
        mock_hass.data = {DOMAIN: {"panel_registered": True, "entry_a": entry_a}}

        result = _get_entry_data(mock_hass, {})
        assert result is entry_a

    def test_ignores_invalid_entry_id(self, mock_hass):
        """Test falls back when entry_id doesn't match any entry."""
        entry_a = {"config": {"host": "a"}}
        mock_hass.data = {DOMAIN: {"entry_a": entry_a}}

        result = _get_entry_data(mock_hass, {"entry_id": "nonexistent"})
        assert result is entry_a

    def test_ignores_metadata_key_as_entry_id(self, mock_hass):
        """Test rejects metadata keys passed as entry_id."""
        entry_a = {"config": {"host": "a"}}
        mock_hass.data = {DOMAIN: {"panel_registered": True, "entry_a": entry_a}}

        result = _get_entry_data(mock_hass, {"entry_id": "panel_registered"})
        assert result is entry_a
