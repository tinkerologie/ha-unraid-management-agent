"""Test the exclusive share (FUSE fallback) binary sensors."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest
from homeassistant.const import STATE_OFF, STATE_ON, STATE_UNAVAILABLE, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant.common import MockConfigEntry

from custom_components.unraid_management_agent.api.models import ShareInfo
from custom_components.unraid_management_agent.binary_sensor import (
    UnraidShareFuseFallbackBinarySensor,
)
from custom_components.unraid_management_agent.cleanup import (
    _build_valid_dynamic_entity_keys,
)
from custom_components.unraid_management_agent.const import DOMAIN
from custom_components.unraid_management_agent.coordinator import UnraidData

from .const import MOCK_CONFIG, MOCK_OPTIONS

ENTRY_ID = "test_entry_id"


def _share(name: str, **fields: Any) -> ShareInfo:
    """Return a pool-only share as the agent reports it."""
    return ShareInfo.model_validate(
        {"name": name, "use_cache": "only", "cache_pool": "cache", **fields}
    )


# Shaped like GET /api/v1/shares from a live agent on Unraid 7.4.0-rc.1
EXCLUSIVE = _share(
    "appdata", exclusive=True, exclusive_eligible=True, exclusive_pool="cache"
)
FALLBACK = _share(
    "domains",
    exclusive=False,
    exclusive_eligible=True,
    locations=["cache", "disk1", "nvme"],
)
FALLBACK_NO_STRAY = _share(
    "system", exclusive=False, exclusive_eligible=True, locations=["cache"]
)
INELIGIBLE = _share("media", use_cache="yes", exclusive=False, exclusive_eligible=False)
OLD_AGENT = _share("isos")


def _entry(hass: HomeAssistant) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Unraid (unraid-test)",
        data=MOCK_CONFIG,
        options=MOCK_OPTIONS,
        entry_id=ENTRY_ID,
    )
    entry.add_to_hass(hass)
    return entry


async def _setup(
    hass: HomeAssistant, client: MagicMock, shares: list[ShareInfo]
) -> MockConfigEntry:
    client.list_shares.return_value = shares
    entry = _entry(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def _refresh(
    hass: HomeAssistant,
    entry: MockConfigEntry,
    client: MagicMock,
    shares: list[ShareInfo] | None,
) -> None:
    client.list_shares.return_value = shares
    await entry.runtime_data.coordinator.async_refresh()
    await hass.async_block_till_done()


def _fallback_entities(registry: er.EntityRegistry) -> set[str]:
    return {
        e.unique_id
        for e in er.async_entries_for_config_entry(registry, ENTRY_ID)
        if e.unique_id.endswith("_fuse_fallback")
    }


def test_share_model_properties() -> None:
    """fuse_fallback and stray_locations derive from the agent fields."""
    implicit = ShareInfo(exclusive_pool="first", locations=["first", "disk1"])
    assert implicit.stray_locations == ["disk1"]
    assert FALLBACK.fuse_fallback is True
    assert FALLBACK.stray_locations == ["disk1", "nvme"]
    assert FALLBACK_NO_STRAY.stray_locations == []
    assert EXCLUSIVE.fuse_fallback is False
    assert EXCLUSIVE.stray_locations == []
    assert INELIGIBLE.fuse_fallback is False
    assert OLD_AGENT.fuse_fallback is False
    assert OLD_AGENT.exclusive_state_known is False
    assert _share("x", exclusive=False).exclusive_state_known is False
    assert EXCLUSIVE.exclusive_state_known is True
    assert FALLBACK.exclusive_state_known is True
    assert INELIGIBLE.exclusive_state_known is True


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_sensors_created_for_eligible_shares(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mock_async_unraid_client: MagicMock,
) -> None:
    """Only shares that are or can be exclusive get a FUSE fallback sensor."""
    await _setup(
        hass,
        mock_async_unraid_client,
        [EXCLUSIVE, FALLBACK, INELIGIBLE, OLD_AGENT, _share("")],
    )

    assert _fallback_entities(entity_registry) == {
        f"{ENTRY_ID}_share_appdata_fuse_fallback",
        f"{ENTRY_ID}_share_domains_fuse_fallback",
    }
    entity = entity_registry.async_get(
        "binary_sensor.unraid_test_share_appdata_fuse_fallback"
    )
    assert entity is not None
    assert entity.entity_category is EntityCategory.DIAGNOSTIC
    assert entity.translation_key == "share_fuse_fallback"


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_sensor_state_and_attributes(
    hass: HomeAssistant, mock_async_unraid_client: MagicMock
) -> None:
    """The sensor is a problem while an eligible share is on FUSE."""
    await _setup(hass, mock_async_unraid_client, [EXCLUSIVE, FALLBACK])

    ok = hass.states.get("binary_sensor.unraid_test_share_appdata_fuse_fallback")
    assert ok is not None
    assert ok.state == STATE_OFF
    assert ok.attributes["device_class"] == "problem"
    assert ok.attributes["friendly_name"] == "unraid-test Share appdata FUSE Fallback"
    assert ok.attributes["exclusive"] is True
    assert ok.attributes["exclusive_eligible"] is True
    assert ok.attributes["exclusive_pool"] == "cache"
    assert "locations" not in ok.attributes

    bad = hass.states.get("binary_sensor.unraid_test_share_domains_fuse_fallback")
    assert bad is not None
    assert bad.state == STATE_ON
    assert bad.attributes["exclusive"] is False
    assert "exclusive_pool" not in bad.attributes
    assert bad.attributes["locations"] == ["cache", "disk1", "nvme"]
    assert bad.attributes["stray_locations"] == ["disk1", "nvme"]
    assert "locations_unchecked" not in bad.attributes


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_sensor_follows_updates(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mock_async_unraid_client: MagicMock,
) -> None:
    """Sensors appear with the agent fields and go unavailable without them."""
    entry = await _setup(hass, mock_async_unraid_client, [OLD_AGENT])
    assert _fallback_entities(entity_registry) == set()
    entity_id = "binary_sensor.unraid_test_share_isos_fuse_fallback"

    # Array started: the agent now reports the state
    isos = _share("isos", exclusive=True, exclusive_eligible=True)
    await _refresh(hass, entry, mock_async_unraid_client, [isos])
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == STATE_OFF
    assert "exclusive_pool" not in state.attributes

    # Eligibility unknown (share config unreadable)
    await _refresh(
        hass, entry, mock_async_unraid_client, [_share("isos", exclusive=False)]
    )
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == STATE_UNAVAILABLE

    # Array stopped: state unknown
    await _refresh(hass, entry, mock_async_unraid_client, [OLD_AGENT])
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == STATE_UNAVAILABLE

    # Share removed
    await _refresh(hass, entry, mock_async_unraid_client, [])
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == STATE_UNAVAILABLE

    # Share fetch failed
    await _refresh(hass, entry, mock_async_unraid_client, None)
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == STATE_UNAVAILABLE


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_sensor_without_share_data(
    hass: HomeAssistant, mock_async_unraid_client: MagicMock
) -> None:
    """A sensor whose share is gone reports off with no attributes."""
    entry = await _setup(hass, mock_async_unraid_client, [EXCLUSIVE])
    sensor = UnraidShareFuseFallbackBinarySensor(
        entry.runtime_data.coordinator, "removed"
    )
    assert sensor.available is False
    assert sensor.is_on is False
    assert sensor.extra_state_attributes == {}


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_sensor_without_coordinator_data(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mock_async_unraid_client: MagicMock,
) -> None:
    """A failed update or missing coordinator data leaves the sensor unavailable."""
    entry = await _setup(hass, mock_async_unraid_client, [EXCLUSIVE])
    coordinator = entry.runtime_data.coordinator
    sensor = UnraidShareFuseFallbackBinarySensor(coordinator, "appdata")
    assert sensor.available is True

    coordinator.last_update_success = False
    assert sensor.available is False

    coordinator.last_update_success = True
    coordinator.data = None
    coordinator.async_update_listeners()
    await hass.async_block_till_done()
    assert sensor.available is False
    assert sensor.is_on is False
    assert _fallback_entities(entity_registry) == {
        f"{ENTRY_ID}_share_appdata_fuse_fallback"
    }


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_sensor_recreated_after_registry_removal(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mock_async_unraid_client: MagicMock,
) -> None:
    """A sensor removed from the registry comes back on the next update."""
    entry = await _setup(hass, mock_async_unraid_client, [EXCLUSIVE])
    entity_id = "binary_sensor.unraid_test_share_appdata_fuse_fallback"
    entity_registry.async_remove(entity_id)
    await hass.async_block_till_done()

    await _refresh(hass, entry, mock_async_unraid_client, [EXCLUSIVE])
    assert entity_registry.async_get(entity_id) is not None


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_no_sensors_when_share_collector_disabled(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mock_async_unraid_client: MagicMock,
) -> None:
    """A disabled shares collector gets no sensors until it is enabled."""
    shares_collector = MagicMock(enabled=False)
    collectors = mock_async_unraid_client.get_collectors_status.return_value
    collectors.get_collector_by_name = MagicMock(
        side_effect=lambda name: shares_collector if name == "shares" else None
    )
    entry = await _setup(hass, mock_async_unraid_client, [EXCLUSIVE, FALLBACK])

    assert _fallback_entities(entity_registry) == set()

    # Collector enabled later: the sensors appear without a reload
    shares_collector.enabled = True
    await _refresh(hass, entry, mock_async_unraid_client, [EXCLUSIVE, FALLBACK])
    assert _fallback_entities(entity_registry) == {
        f"{ENTRY_ID}_share_appdata_fuse_fallback",
        f"{ENTRY_ID}_share_domains_fuse_fallback",
    }


def test_cleanup_keeps_fuse_fallback_sensor() -> None:
    """Stale cleanup treats a present share's FUSE fallback sensor as valid."""
    keys = _build_valid_dynamic_entity_keys(UnraidData(shares=[OLD_AGENT]))
    assert "share_isos_fuse_fallback" in keys
    assert "share_isos_usage" in keys
