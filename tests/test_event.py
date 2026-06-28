"""Tests for the Kubernetes event platform."""

from unittest.mock import MagicMock, patch

from homeassistant.core import HomeAssistant
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.kubernetes.const import (
    CONF_ENABLE_EVENTS,
    DOMAIN,
    EVENT_CURATED_REASONS,
    EVENT_TYPE_OTHER,
    event_signal,
)
from custom_components.kubernetes.event import (
    KubernetesClusterEventEntity,
    async_setup_entry,
)


@pytest.fixture
def mock_config_entry(hass: HomeAssistant) -> MockConfigEntry:
    """Create a mock config entry with events disabled (default)."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        entry_id="test_event_entry_id",
        data={"host": "https://kubernetes.example.com", "port": 6443},
        options={},
    )
    entry.add_to_hass(hass)
    return entry


@pytest.fixture
def mock_config_entry_events_enabled(hass: HomeAssistant) -> MockConfigEntry:
    """Create a mock config entry with events enabled."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        entry_id="test_event_entry_id_enabled",
        data={"host": "https://kubernetes.example.com", "port": 6443},
        options={CONF_ENABLE_EVENTS: True},
    )
    entry.add_to_hass(hass)
    return entry


class TestKubernetesEventSetup:
    """Test event platform setup."""

    async def test_setup_skipped_when_events_disabled(
        self,
        hass: HomeAssistant,
        mock_config_entry,
    ):
        """Setup must be a no-op when CONF_ENABLE_EVENTS is False (default)."""
        mock_add_entities = MagicMock()

        await async_setup_entry(hass, mock_config_entry, mock_add_entities)

        mock_add_entities.assert_not_called()

    async def test_setup_skipped_when_events_explicitly_false(
        self,
        hass: HomeAssistant,
    ):
        """Setup must be a no-op when CONF_ENABLE_EVENTS is explicitly False."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            entry_id="explicit_false_entry",
            data={"host": "https://kubernetes.example.com", "port": 6443},
            options={CONF_ENABLE_EVENTS: False},
        )
        entry.add_to_hass(hass)
        mock_add_entities = MagicMock()

        await async_setup_entry(hass, entry, mock_add_entities)

        mock_add_entities.assert_not_called()

    async def test_setup_adds_entity_when_enabled(
        self,
        hass: HomeAssistant,
        mock_config_entry_events_enabled,
    ):
        """Setup adds one KubernetesClusterEventEntity when events are enabled."""
        mock_add_entities = MagicMock()

        await async_setup_entry(
            hass, mock_config_entry_events_enabled, mock_add_entities
        )

        mock_add_entities.assert_called_once()
        added_entities = mock_add_entities.call_args[0][0]
        assert len(added_entities) == 1
        entity = added_entities[0]
        assert isinstance(entity, KubernetesClusterEventEntity)
        assert (
            entity.unique_id
            == f"{mock_config_entry_events_enabled.entry_id}_cluster_events"
        )
        assert "OOMKilling" in entity._attr_event_types
        assert EVENT_TYPE_OTHER in entity._attr_event_types


class TestKubernetesClusterEventEntity:
    """Unit tests for KubernetesClusterEventEntity event mapping."""

    @pytest.fixture
    def entry(self, hass: HomeAssistant) -> MockConfigEntry:
        """Return a minimal config entry for entity instantiation."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            entry_id="unit_test_entry",
            data={"host": "https://kubernetes.example.com", "port": 6443},
            options={CONF_ENABLE_EVENTS: True},
        )
        entry.add_to_hass(hass)
        return entry

    def test_handle_event_maps_curated_reason(self, entry):
        """A curated reason is passed through as the event_type."""
        entity = KubernetesClusterEventEntity(entry)
        payload = {"reason": "OOMKilling", "type": "Warning"}

        with (
            patch.object(entity, "_trigger_event") as mock_trigger,
            patch.object(entity, "async_write_ha_state"),
        ):
            entity._handle_event(payload)

        mock_trigger.assert_called_once_with("OOMKilling", payload)

    def test_handle_event_maps_unknown_reason_to_other(self, entry):
        """An unknown reason is mapped to EVENT_TYPE_OTHER."""
        entity = KubernetesClusterEventEntity(entry)
        payload = {"reason": "SomethingWeird", "type": "Normal"}

        with (
            patch.object(entity, "_trigger_event") as mock_trigger,
            patch.object(entity, "async_write_ha_state"),
        ):
            entity._handle_event(payload)

        mock_trigger.assert_called_once_with(EVENT_TYPE_OTHER, payload)

    def test_handle_event_missing_reason_to_other(self, entry):
        """A payload without a reason key is mapped to EVENT_TYPE_OTHER."""
        entity = KubernetesClusterEventEntity(entry)
        payload = {"type": "Warning", "message": "something happened"}

        with (
            patch.object(entity, "_trigger_event") as mock_trigger,
            patch.object(entity, "async_write_ha_state"),
        ):
            entity._handle_event(payload)

        mock_trigger.assert_called_once_with(EVENT_TYPE_OTHER, payload)

    def test_event_types_include_all_curated_reasons(self, entry):
        """All curated reasons from const are present in _attr_event_types."""
        entity = KubernetesClusterEventEntity(entry)
        for reason in EVENT_CURATED_REASONS:
            assert reason in entity._attr_event_types

    def test_unique_id_format(self, entry):
        """unique_id follows the expected format."""
        entity = KubernetesClusterEventEntity(entry)
        assert entity._attr_unique_id == f"{entry.entry_id}_cluster_events"

    async def test_async_added_to_hass_connects_dispatcher(self, hass, entry):
        """async_added_to_hass wires the entry's event signal to _handle_event.

        The base EventEntity.async_added_to_hass is patched out so the test
        focuses purely on the dispatcher wiring our entity adds, without
        depending on RestoreEntity/platform machinery that is not set up on a
        bare (non-platform-registered) entity in this harness.
        """
        entity = KubernetesClusterEventEntity(entry)
        entity.hass = hass
        entity.async_on_remove = MagicMock()

        with (
            patch(
                "custom_components.kubernetes.event.EventEntity.async_added_to_hass",
            ),
            patch(
                "custom_components.kubernetes.event.async_dispatcher_connect",
            ) as mock_connect,
        ):
            await entity.async_added_to_hass()

        mock_connect.assert_called_once()
        call = mock_connect.call_args[0]
        assert call[0] is hass
        assert call[1] == event_signal(entry.entry_id)
        assert call[2] == entity._handle_event
        # The unsubscribe handle is registered for cleanup.
        entity.async_on_remove.assert_called_once_with(mock_connect.return_value)
