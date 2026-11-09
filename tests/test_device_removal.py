"""Manual device removal through Home Assistant's device registry API."""

from unittest.mock import MagicMock

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.setup import async_setup_component
from pytest_homeassistant.common import MockConfigEntry

from custom_components.unraid_management_agent.api.models import ContainerInfo, VMInfo
from custom_components.unraid_management_agent.const import (
    CONF_ENABLE_CONTAINER_DEVICES,
    CONF_ENABLE_VM_DEVICES,
    CONF_ENABLE_WEBSOCKET,
    DOMAIN,
)
from tests.const import MOCK_CONFIG


@pytest.mark.parametrize(
    "resource",
    ["vm", "container"],
)
async def test_registry_removal_requires_a_confirmed_absence(
    hass: HomeAssistant,
    hass_ws_client,
    mock_async_unraid_client: MagicMock,
    resource: str,
) -> None:
    """Refuse removal during a failed fetch, then allow a confirmed absence."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_CONFIG,
        options={
            CONF_ENABLE_CONTAINER_DEVICES: True,
            CONF_ENABLE_VM_DEVICES: True,
            CONF_ENABLE_WEBSOCKET: False,
        },
    )
    entry.add_to_hass(hass)
    if resource == "vm":
        fetch = mock_async_unraid_client.list_vms
        fetch.return_value = [VMInfo(id="target", name="Target", state="running")]
    else:
        fetch = mock_async_unraid_client.list_containers
        fetch.return_value = [
            ContainerInfo(id="0123456789ab", name="target", state="running")
        ]
    assert await hass.config_entries.async_setup(entry.entry_id)
    assert await async_setup_component(hass, "config", {})
    await hass.async_block_till_done()
    client = await hass_ws_client(hass)

    devices = dr.async_get(hass)
    entities = er.async_get(hass)
    target = devices.async_get_child_device_by_identifier(
        (DOMAIN, f"{entry.entry_id}_{resource}_target"), entry.entry_id
    )
    server = devices.async_get_device_by_identifier(
        (DOMAIN, entry.entry_id), entry.entry_id
    )
    assert target is not None
    assert server is not None

    async def remove(device_id: str) -> bool:
        await client.send_json_auto_id(
            {"type": "config/device_registry/remove", "device_id": device_id}
        )
        response = await client.receive_json()
        return response["success"]

    assert not await remove(target.id)
    assert not await remove(server.id)

    coordinator = entry.runtime_data.coordinator
    fetch.side_effect = RuntimeError("Inventory unavailable")
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert not await remove(target.id)
    assert devices.async_get(target.id) is not None
    assert er.async_entries_for_device(entities, target.id)

    fetch.side_effect = None
    fetch.return_value = []
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    # A total outage keeps the last snapshot, including its empty inventory.
    # That snapshot cannot authorize removal until a refresh succeeds again.
    system = mock_async_unraid_client.get_system_info
    array = mock_async_unraid_client.get_array_status
    system.side_effect = array.side_effect = RuntimeError("Agent unavailable")
    await coordinator.async_refresh()
    assert not coordinator.last_update_success
    assert not await remove(target.id)
    assert devices.async_get(target.id) is not None

    system.side_effect = array.side_effect = None
    await coordinator.async_refresh()
    assert coordinator.last_update_success
    assert await remove(target.id)
    assert devices.async_get(target.id) is None


@pytest.mark.parametrize(
    "suffix",
    [
        "vm_target",
        "container_target",
        "gpu_uuid_target",
        "gpu_pci_pci-slot",
        "gpu_index_2",
        "zfs_pool_target",
        "nic_target",
        "storage_controller_target",
        "storage_enclosure_target",
        "hwmon_octo_target",
    ],
)
def test_resource_presence_uses_complete_inventories(suffix):
    """Only a complete inventory can establish that a resource is missing."""
    from custom_components.unraid_management_agent.api.models import (
        FanInfo,
        GPUInfo,
        NICCard,
        NICList,
        StorageController,
        StorageEnclosure,
        StorageTopology,
        SystemInfo,
        ZFSPool,
    )
    from custom_components.unraid_management_agent.presence import (
        Presence,
        device_presence,
    )
    from custom_components.unraid_management_agent.telemetry import UnraidData

    identifier = f"entry_{suffix}"
    assert device_presence(UnraidData(), "entry", identifier) is Presence.UNKNOWN

    empty = UnraidData(
        vms=[],
        containers=[],
        gpu=[],
        zfs_pools=[],
        network_cards=NICList(state="ok"),
        storage_topology=StorageTopology(state="ok"),
        system=SystemInfo(fans=[], temperatures=[]),
    )
    assert device_presence(empty, "entry", identifier) is Presence.ABSENT

    present = UnraidData(
        vms=[VMInfo(id="target", name="Other name")],
        containers=[ContainerInfo(name="target")],
        gpu=[
            GPUInfo(index=0, uuid="TARGET"),
            GPUInfo(index=1, pci_id="pci-slot"),
            GPUInfo(index=2),
        ],
        zfs_pools=[ZFSPool(name="target")],
        network_cards=NICList(state="ok", cards=[NICCard(id="target")]),
        storage_topology=StorageTopology(
            state="ok",
            controllers=[StorageController(id="target")],
            enclosures=[StorageEnclosure(id="target")],
        ),
        system=SystemInfo(
            fans=[FanInfo(source="octo-hid-3-13", device_id="target")],
            temperatures=[],
        ),
    )
    assert device_presence(present, "entry", identifier) is Presence.PRESENT
