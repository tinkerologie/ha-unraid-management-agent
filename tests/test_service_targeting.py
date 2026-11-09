"""Configured-server targeting at the registered Home Assistant service seam."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
import yaml
from homeassistant.config_entries import ConfigEntryDisabler
from homeassistant.const import ATTR_CONFIG_ENTRY_ID
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import issue_registry as ir
from pytest_homeassistant.common import MockConfigEntry

from custom_components.unraid_management_agent.const import DOMAIN
from tests.test_read_only import _entry


@pytest.fixture
async def configured_servers(
    hass: HomeAssistant, mock_async_unraid_client, mock_unraid_websocket_client_class
):
    """Set up configured servers and provide independent control adapters."""
    first = _entry(hass, read_only=False, entry_id="first", host="192.0.2.10")
    second = _entry(hass, read_only=False, entry_id="second", host="192.0.2.11")
    _entry(hass, read_only=True, entry_id="readonly", host="192.0.2.12")
    _entry(
        hass,
        read_only=False,
        entry_id="disabled",
        host="192.0.2.13",
        disabled_by=ConfigEntryDisabler.USER,
    )
    MockConfigEntry(domain="mqtt", entry_id="foreign").add_to_hass(hass)
    assert await hass.config_entries.async_setup(first.entry_id)
    await hass.async_block_till_done()
    coordinators = [entry.runtime_data.coordinator for entry in (first, second)]
    for coordinator in coordinators:
        coordinator.client = MagicMock()
        coordinator.async_request_refresh = AsyncMock()
    return coordinators


@pytest.mark.parametrize(
    ("action", "fields", "expected_call"),
    [
        ("vm_stop", {"vm_id": "shared"}, ("stop_vm", ("shared",), {})),
        (
            "container_remove",
            {"container_id": "shared"},
            ("remove_container", ("shared",), {"remove_image": False}),
        ),
        (
            "container_set_autostart",
            {"container_id": "shared", "enabled": True},
            ("set_container_autostart", ("shared",), {"enabled": True}),
        ),
        ("array_stop", {}, ("stop_array", (), {})),
    ],
)
async def test_selected_server_owns_action_and_refresh(
    hass, configured_servers, action, fields, expected_call
):
    """Control the selected server even when resource names are identical."""
    first, second = configured_servers
    method, args, kwargs = expected_call
    for coordinator in (first, second):
        setattr(coordinator.client, method, AsyncMock())

    await hass.services.async_call(
        DOMAIN, action, {**fields, ATTR_CONFIG_ENTRY_ID: "second"}, blocking=True
    )

    getattr(first.client, method).assert_not_awaited()
    first.async_request_refresh.assert_not_awaited()
    getattr(second.client, method).assert_awaited_once_with(*args, **kwargs)
    second.async_request_refresh.assert_awaited_once()


@pytest.mark.parametrize(
    ("entry_id", "error"),
    [
        ("unknown", "config_entry_not_found"),
        ("foreign", "config_entry_not_found"),
        ("disabled", "entry_not_loaded"),
        ("readonly", "read_only_mode"),
    ],
)
async def test_rejected_target_does_not_fall_back(
    hass, configured_servers, entry_id, error
):
    """A rejected explicit target does not reach another server."""
    with pytest.raises(ServiceValidationError) as raised:
        await hass.services.async_call(
            DOMAIN, "array_stop", {ATTR_CONFIG_ENTRY_ID: entry_id}, blocking=True
        )
    assert raised.value.translation_key == error
    for coordinator in configured_servers:
        assert not coordinator.client.mock_calls
        coordinator.async_request_refresh.assert_not_awaited()


async def test_ambiguous_legacy_action_warns_and_keeps_the_first_server(
    hass, configured_servers, caplog
):
    """Keep existing automations working while flagging missing selectors."""
    first, second = configured_servers
    first.client.stop_array = AsyncMock()
    second.client.stop_array = AsyncMock()
    await hass.services.async_call(DOMAIN, "array_stop", {}, blocking=True)
    await hass.services.async_call(DOMAIN, "array_stop", {}, blocking=True)
    assert first.client.stop_array.await_count == 2
    second.client.stop_array.assert_not_awaited()
    assert caplog.text.count("omitted config_entry_id with multiple servers") == 1
    assert ir.async_get(hass).async_get_issue(
        DOMAIN, "service_config_entry_id_required"
    )


def test_all_actions_expose_the_same_server_selector():
    """Keep all service metadata and English translations aligned."""
    root = Path(__file__).parents[1] / "custom_components" / DOMAIN
    services = yaml.safe_load((root / "services.yaml").read_text())
    strings = json.loads((root / "strings.json").read_text())
    translated = json.loads((root / "translations" / "en.json").read_text())
    assert len(services) == 22
    assert (
        services.keys() == strings["services"].keys() == translated["services"].keys()
    )
    for action, metadata in services.items():
        field = metadata["fields"][ATTR_CONFIG_ENTRY_ID]
        assert field["required"] is False
        assert field["selector"] == {"config_entry": {"integration": DOMAIN}}
        assert (
            strings["services"][action]["fields"][ATTR_CONFIG_ENTRY_ID]
            == (translated["services"][action]["fields"][ATTR_CONFIG_ENTRY_ID])
        )
