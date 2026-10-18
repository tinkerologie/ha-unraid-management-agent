"""Test the selectable CPU temperature source (issue #195)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.unraid_management_agent.api.models import TemperatureInfo
from custom_components.unraid_management_agent.const import (
    CONF_CPU_TEMPERATURE_SOURCE,
    DOMAIN,
)

from .const import MOCK_CONFIG, MOCK_OPTIONS

ENTRY_ID = "test_entry_id"
K10TEMP = TemperatureInfo(
    name="k10temp-pci-00c3_Tctl_temp1_input",
    value_celsius=45.16,
    sensor_type="cpu",
    source="k10temp-pci-00c3",
)
CPUTIN = TemperatureInfo(
    name="nct6798-isa-0290_CPUTIN_temp2_input",
    value_celsius=60.0,
    sensor_type="other",
    source="nct6798-isa-0290",
)
K10TEMP_KEY = "k10temp_pci_00c3_temp1"


async def _setup(hass: HomeAssistant, **options: object) -> MockConfigEntry:
    """Set up an entry with the given options."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Unraid (unraid-test)",
        data=MOCK_CONFIG,
        options={**MOCK_OPTIONS, **options},
        entry_id=ENTRY_ID,
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


def _cpu_state(hass: HomeAssistant) -> str:
    """Return the CPU temperature entity's state."""
    entity_id = er.async_get(hass).async_get_entity_id(
        "sensor", DOMAIN, f"{ENTRY_ID}_cpu_temperature"
    )
    assert entity_id is not None
    state = hass.states.get(entity_id)
    assert state is not None
    return state.state


async def _refresh(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    """Poll the agent again."""
    await entry.runtime_data.coordinator.async_refresh()
    await hass.async_block_till_done()


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_default_uses_agent_cpu_temperature(
    hass: HomeAssistant, mock_async_unraid_client: MagicMock
) -> None:
    """Without the option the agent's CPU temperature is shown."""
    mock_async_unraid_client.get_system_info.return_value.temperatures = [
        K10TEMP,
        CPUTIN,
    ]
    await _setup(hass)
    assert float(_cpu_state(hass)) == 55.0


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_selected_channel_is_used(
    hass: HomeAssistant, mock_async_unraid_client: MagicMock
) -> None:
    """A picked channel supplies the value, though its own entity is disabled."""
    mock_async_unraid_client.get_system_info.return_value.temperatures = [
        K10TEMP,
        CPUTIN,
    ]
    await _setup(hass, **{CONF_CPU_TEMPERATURE_SOURCE: K10TEMP_KEY})

    assert float(_cpu_state(hass)) == 45.2
    channel = er.async_get(hass).async_get(
        er.async_get(hass).async_get_entity_id(
            "sensor", DOMAIN, f"{ENTRY_ID}_temperature_{K10TEMP_KEY}"
        )
        or ""
    )
    assert channel is not None
    assert channel.disabled_by is er.RegistryEntryDisabler.INTEGRATION


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_selected_channel_disappears_and_returns(
    hass: HomeAssistant, mock_async_unraid_client: MagicMock
) -> None:
    """A missing picked channel makes the entity unavailable until it returns."""
    system = mock_async_unraid_client.get_system_info.return_value
    system.temperatures = [K10TEMP, CPUTIN]
    entry = await _setup(hass, **{CONF_CPU_TEMPERATURE_SOURCE: K10TEMP_KEY})

    system.temperatures = [CPUTIN]
    await _refresh(hass, entry)
    assert _cpu_state(hass) == STATE_UNAVAILABLE

    system.temperatures = [K10TEMP, CPUTIN]
    await _refresh(hass, entry)
    assert float(_cpu_state(hass)) == 45.2


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_selected_channel_without_reading(
    hass: HomeAssistant, mock_async_unraid_client: MagicMock
) -> None:
    """A picked channel without a value gives an unknown state."""
    mock_async_unraid_client.get_system_info.return_value.temperatures = [
        TemperatureInfo(
            name="k10temp-pci-00c3_Tctl_temp1_input", source="k10temp-pci-00c3"
        )
    ]
    await _setup(hass, **{CONF_CPU_TEMPERATURE_SOURCE: K10TEMP_KEY})
    assert _cpu_state(hass) == STATE_UNKNOWN


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_selected_channel_without_coordinator_data(
    hass: HomeAssistant, mock_async_unraid_client: MagicMock
) -> None:
    """With no coordinator data a picked channel gives no value and is unavailable."""
    mock_async_unraid_client.get_system_info.return_value.temperatures = [K10TEMP]
    entry = await _setup(hass, **{CONF_CPU_TEMPERATURE_SOURCE: K10TEMP_KEY})
    coordinator = entry.runtime_data.coordinator
    coordinator.data = None
    coordinator.async_update_listeners()
    await hass.async_block_till_done()
    assert _cpu_state(hass) == STATE_UNAVAILABLE

    entity = next(
        e
        for e in hass.data["sensor"].entities
        if getattr(e, "unique_id", None) == f"{ENTRY_ID}_cpu_temperature"
    )
    assert entity.native_value is None
    assert entity.available is False
