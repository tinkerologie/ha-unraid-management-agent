"""Test Docker containers as (optional) child devices of the Unraid server."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant.common import MockConfigEntry

from custom_components.unraid_management_agent import (
    async_remove_config_entry_device,
)
from custom_components.unraid_management_agent.cleanup import (
    _async_remove_empty_devices,
)
from custom_components.unraid_management_agent.const import (
    CONF_ENABLE_CONTAINER_DEVICES,
    DOMAIN,
)
from custom_components.unraid_management_agent.entity import (
    build_container_device_info,
)

from .const import MOCK_CONFIG, MOCK_OPTIONS

ENTRY_ID = "test_entry_id"
PLEX = (DOMAIN, f"{ENTRY_ID}_container_plex")


def _entry(hass: HomeAssistant, *, container_devices: bool) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Unraid (unraid-test)",
        data=MOCK_CONFIG,
        options={**MOCK_OPTIONS, CONF_ENABLE_CONTAINER_DEVICES: container_devices},
        entry_id=ENTRY_ID,
    )
    entry.add_to_hass(hass)
    return entry


async def _setup(hass: HomeAssistant, *, container_devices: bool) -> MockConfigEntry:
    entry = _entry(hass, container_devices=container_devices)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


@pytest.mark.usefixtures(
    "mock_unraid_client_class", "mock_unraid_websocket_client_class"
)
async def test_containers_are_child_devices_of_the_docker_device(
    hass: HomeAssistant,
) -> None:
    """With the option on, each container's entities share a child device."""
    await _setup(hass, container_devices=True)

    devices = dr.async_get(hass)
    server = devices.async_get_device_by_identifier((DOMAIN, ENTRY_ID), ENTRY_ID)
    plex = devices.async_get_child_device_by_identifier(PLEX, ENTRY_ID)
    docker = devices.async_get_device_by_identifier(
        (DOMAIN, f"{ENTRY_ID}_docker"), ENTRY_ID
    )
    assert server is not None
    assert docker is not None
    assert docker.name == "unraid-test Docker"
    assert docker.via_device_id == server.id
    assert plex is not None
    assert plex.name == "plex"
    assert plex.parent_device_id == docker.id

    entities = er.async_get(hass)
    on_plex = {
        e.entity_id
        for e in entities.entities.values()
        if e.config_entry_id == ENTRY_ID and e.device_id == plex.id
    }
    assert "switch.unraid_test_docker_plex_running" in on_plex
    assert "switch.unraid_test_docker_plex_autostart" in on_plex
    assert "button.unraid_test_docker_plex_restart" in on_plex
    assert "sensor.unraid_test_docker_plex_cpu" in on_plex

    # Containers do not show up as separate main devices
    main_devices = dr.async_entries_for_config_entry(devices, ENTRY_ID)
    assert all("_container_" not in next(iter(d.identifiers))[1] for d in main_devices)


@pytest.mark.usefixtures(
    "mock_unraid_client_class", "mock_unraid_websocket_client_class"
)
async def test_container_sensor_entity_ids_do_not_collide(
    hass: HomeAssistant,
) -> None:
    """Memory (bytes) and memory usage (%) get distinct entity IDs."""
    await _setup(hass, container_devices=True)

    entities = er.async_get(hass)
    assert entities.async_get("sensor.unraid_test_docker_plex_memory") is not None
    assert entities.async_get("sensor.unraid_test_docker_plex_memory_usage") is not None
    assert entities.async_get("sensor.unraid_test_docker_plex_memory_2") is None


@pytest.mark.usefixtures(
    "mock_unraid_client_class", "mock_unraid_websocket_client_class"
)
async def test_option_off_keeps_containers_on_the_server_device(
    hass: HomeAssistant,
) -> None:
    """With the option off (default) containers stay on the server device."""
    await _setup(hass, container_devices=False)

    devices = dr.async_get(hass)
    assert not dr.async_child_entries_for_config_entry(devices, ENTRY_ID)
    server = devices.async_get_device_by_identifier((DOMAIN, ENTRY_ID), ENTRY_ID)
    entities = er.async_get(hass)
    switch = entities.async_get("switch.unraid_test_container_plex")
    assert switch is not None
    assert switch.device_id == server.id


@pytest.mark.usefixtures(
    "mock_unraid_client_class", "mock_unraid_websocket_client_class"
)
async def test_device_without_entities_is_removed(hass: HomeAssistant) -> None:
    """A container device whose entities are all gone is removed."""
    entry = await _setup(hass, container_devices=True)
    devices = dr.async_get(hass)
    entities = er.async_get(hass)
    plex = devices.async_get_child_device_by_identifier(PLEX, ENTRY_ID)
    for entity in er.async_entries_for_device(
        entities, plex.id, include_disabled_entities=True
    ):
        entities.async_remove(entity.entity_id)

    _async_remove_empty_devices(hass, entry)

    assert devices.async_get_child_device_by_identifier(PLEX, ENTRY_ID) is None
    # The server device is never removed, even without entities of its own
    assert devices.async_get_device_by_identifier((DOMAIN, ENTRY_ID), ENTRY_ID)


@pytest.mark.usefixtures(
    "mock_unraid_client_class", "mock_unraid_websocket_client_class"
)
async def test_only_devices_of_deleted_containers_can_be_removed(
    hass: HomeAssistant,
) -> None:
    """Users may delete a container device once the container is gone."""
    entry = await _setup(hass, container_devices=True)
    devices = dr.async_get(hass)
    server = devices.async_get_device_by_identifier((DOMAIN, ENTRY_ID), ENTRY_ID)
    plex = devices.async_get_child_device_by_identifier(PLEX, ENTRY_ID)

    assert not await async_remove_config_entry_device(hass, entry, server)
    assert not await async_remove_config_entry_device(hass, entry, plex)

    coordinator = entry.runtime_data.coordinator
    observed = coordinator.data.containers
    coordinator.data.containers = None
    assert not await async_remove_config_entry_device(hass, entry, plex)
    coordinator.data.containers = [c for c in observed if c.name != "plex"]
    assert await async_remove_config_entry_device(hass, entry, plex)


async def test_container_device_falls_back_to_server_when_server_missing(
    hass: HomeAssistant,
) -> None:
    """Without a registered server device, container entities stay on the server."""
    entry = _entry(hass, container_devices=True)
    coordinator = MagicMock()
    coordinator.hass = hass
    coordinator.config_entry = entry

    info = build_container_device_info(coordinator, "plex")

    assert info == {"identifiers": {(DOMAIN, ENTRY_ID)}}


@pytest.mark.usefixtures(
    "mock_unraid_client_class", "mock_unraid_websocket_client_class"
)
async def test_toggling_container_devices_option_moves_entities_and_removes_devices(
    hass: HomeAssistant,
) -> None:
    """Toggling container devices from True to False reparents entities to server and removes child devices."""
    entry = await _setup(hass, container_devices=True)
    devices = dr.async_get(hass)
    entities = er.async_get(hass)
    server = devices.async_get_device_by_identifier((DOMAIN, ENTRY_ID), ENTRY_ID)
    plex = devices.async_get_child_device_by_identifier(PLEX, ENTRY_ID)
    assert plex is not None

    switch = entities.async_get("switch.unraid_test_docker_plex_running")
    assert switch is not None
    assert switch.device_id == plex.id

    hass.config_entries.async_update_entry(
        entry, options={**entry.options, CONF_ENABLE_CONTAINER_DEVICES: False}
    )
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()

    # The container device is removed immediately
    assert devices.async_get_child_device_by_identifier(PLEX, ENTRY_ID) is None

    # The container switch is reparented to the server device (keeping entity_id)
    switch = entities.async_get("switch.unraid_test_docker_plex_running")
    assert switch is not None
    assert switch.device_id == server.id
