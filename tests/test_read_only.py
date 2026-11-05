"""Test the read-only option (sensors only, no controls)."""

from __future__ import annotations

import pytest
from homeassistant.config_entries import ConfigEntryDisabler, ConfigEntryState
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant.common import MockConfigEntry

from custom_components.unraid_management_agent.const import CONF_READ_ONLY, DOMAIN

from .const import MOCK_CONFIG, MOCK_OPTIONS


def _entry(
    hass: HomeAssistant,
    *,
    read_only: bool,
    entry_id: str = "test_entry_id",
    host: str = MOCK_CONFIG[CONF_HOST],
    disabled_by: ConfigEntryDisabler | None = None,
) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        title=f"Unraid ({host})",
        data={**MOCK_CONFIG, CONF_HOST: host},
        options={**MOCK_OPTIONS, CONF_READ_ONLY: read_only},
        entry_id=entry_id,
        disabled_by=disabled_by,
    )
    entry.add_to_hass(hass)
    return entry


def _domains(hass: HomeAssistant, entry_id: str) -> set[str]:
    registry = er.async_get(hass)
    return {e.domain for e in er.async_entries_for_config_entry(registry, entry_id)}


@pytest.mark.usefixtures(
    "mock_async_unraid_client", "mock_unraid_websocket_client_class"
)
async def test_read_only_creates_only_sensors(hass: HomeAssistant) -> None:
    """Read-only mode sets up sensors but no switches, buttons or numbers."""
    entry = _entry(hass, read_only=True)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    domains = _domains(hass, entry.entry_id)
    assert "sensor" in domains
    assert not domains & {"switch", "button", "number"}

    # Unloading only unloads what was set up
    assert await hass.config_entries.async_unload(entry.entry_id)
    assert entry.state is ConfigEntryState.NOT_LOADED


@pytest.mark.usefixtures(
    "mock_async_unraid_client", "mock_unraid_websocket_client_class"
)
async def test_enabling_read_only_removes_existing_controls(
    hass: HomeAssistant,
) -> None:
    """Switching to read-only removes the control entities created before."""
    entry = _entry(hass, read_only=False)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert {"switch", "button"} <= _domains(hass, entry.entry_id)

    hass.config_entries.async_update_entry(
        entry, options={**MOCK_OPTIONS, CONF_READ_ONLY: True}
    )
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()

    domains = _domains(hass, entry.entry_id)
    assert "sensor" in domains
    assert not domains & {"switch", "button", "number"}


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_read_only_blocks_services(
    hass: HomeAssistant, mock_async_unraid_client
) -> None:
    """Integration actions refuse to change the server in read-only mode."""
    entry = _entry(hass, read_only=True)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    with pytest.raises(ServiceValidationError) as err:
        await hass.services.async_call(
            DOMAIN, "vm_stop", {"vm_id": "Windows 10"}, blocking=True
        )
    assert err.value.translation_domain == DOMAIN
    assert err.value.translation_key == "read_only_mode"
    assert err.value.translation_placeholders == {"title": entry.title}
    mock_async_unraid_client.stop_vm.assert_not_called()


@pytest.mark.parametrize(
    ("first_read_only", "blocked"),
    [(True, True), (False, False)],
    ids=["acting_entry_read_only", "other_entry_read_only"],
)
@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_read_only_checks_entry_used_by_services(
    hass: HomeAssistant,
    mock_async_unraid_client,
    first_read_only: bool,
    blocked: bool,
) -> None:
    """Only the read-only setting of the entry services act on matters."""
    first = _entry(
        hass, read_only=first_read_only, entry_id="first", host="192.168.1.100"
    )
    second = _entry(
        hass, read_only=not first_read_only, entry_id="second", host="192.168.1.101"
    )
    assert await hass.config_entries.async_setup(first.entry_id)
    await hass.async_block_till_done()
    assert first.state is ConfigEntryState.LOADED
    assert second.state is ConfigEntryState.LOADED

    if blocked:
        with pytest.raises(ServiceValidationError) as err:
            await hass.services.async_call(
                DOMAIN, "vm_stop", {"vm_id": "Windows 10"}, blocking=True
            )
        assert err.value.translation_key == "read_only_mode"
        assert err.value.translation_placeholders == {"title": first.title}
        mock_async_unraid_client.stop_vm.assert_not_called()
    else:
        await hass.services.async_call(
            DOMAIN, "vm_stop", {"vm_id": "Windows 10"}, blocking=True
        )
        mock_async_unraid_client.stop_vm.assert_awaited_once_with("Windows 10")


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_services_refuse_when_entry_not_loaded(
    hass: HomeAssistant, mock_async_unraid_client
) -> None:
    """Services raise a validation error when their entry is not loaded."""
    disabled = _entry(
        hass,
        read_only=False,
        entry_id="disabled",
        host="192.168.1.100",
        disabled_by=ConfigEntryDisabler.USER,
    )
    loaded = _entry(hass, read_only=False, entry_id="loaded", host="192.168.1.101")
    assert await hass.config_entries.async_setup(loaded.entry_id)
    await hass.async_block_till_done()
    assert disabled.state is ConfigEntryState.NOT_LOADED
    assert loaded.state is ConfigEntryState.LOADED

    with pytest.raises(ServiceValidationError) as err:
        await hass.services.async_call(DOMAIN, "array_stop", {}, blocking=True)
    assert err.value.translation_key == "entry_not_loaded"
    assert err.value.translation_placeholders == {"title": disabled.title}
    mock_async_unraid_client.stop_array.assert_not_called()
