"""Entity ID changes update restore sensors in place (Home Assistant 2026.11+)."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_platform
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant.common import MockConfigEntry

from custom_components.unraid_management_agent.const import DOMAIN
from custom_components.unraid_management_agent.sensor import (
    UnraidDiskHealthSensor,
    UnraidGPUEnergySensor,
    UnraidNetworkSensorBase,
    UnraidUPSEnergySensor,
)

RESTORE_CLASSES = (
    UnraidNetworkSensorBase,
    UnraidDiskHealthSensor,
    UnraidUPSEnergySensor,
    UnraidGPUEnergySensor,
)


def _hook_owner(entity_class: type) -> type:
    """Return the integration class that overrides async_added_to_hass."""
    return next(
        klass
        for klass in entity_class.__mro__
        if "async_added_to_hass" in vars(klass)
        and klass.__module__.startswith("custom_components.")
    )


@pytest.mark.parametrize("entity_class", RESTORE_CLASSES, ids=lambda c: c.__name__)
def test_restore_sensors_opt_in_to_in_place_entity_id_changes(
    entity_class: type,
) -> None:
    """
    Each class with its own add hook also implements async_entity_id_changed.

    Home Assistant only changes a custom entity's ID in place when the class
    that overrides async_added_to_hass, or a subclass, opts in.
    """
    assert "async_entity_id_changed" in vars(_hook_owner(entity_class))


@pytest.mark.usefixtures(
    "mock_unraid_client_class", "mock_unraid_websocket_client_class"
)
@pytest.mark.parametrize("entity_class", RESTORE_CLASSES, ids=lambda c: c.__name__)
async def test_entity_id_change_keeps_entity_and_restored_state(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, entity_class: type
) -> None:
    """Renaming the entity ID keeps the entity; it is not removed and added again."""
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    entities = {
        entity_id: entity
        for platform in entity_platform.async_get_platforms(hass, DOMAIN)
        for entity_id, entity in platform.entities.items()
    }
    old_entity_id, entity = next(
        (entity_id, entity)
        for entity_id, entity in entities.items()
        if isinstance(entity, entity_class)
    )
    new_entity_id = f"sensor.renamed_{entity_class.__name__.lower()}"

    # Patch where the hook is defined: a patched subclass would count as a
    # class of its own that overrides the hook without opting in.
    with patch.object(
        _hook_owner(entity_class), "async_added_to_hass", autospec=True
    ) as added_again:
        er.async_get(hass).async_update_entity(
            old_entity_id, new_entity_id=new_entity_id
        )
        await hass.async_block_till_done()

    added_again.assert_not_called()
    assert entity.entity_id == new_entity_id
    assert hass.states.get(old_entity_id) is None
    assert hass.states.get(new_entity_id) is not None
