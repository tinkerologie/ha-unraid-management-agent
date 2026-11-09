"""Test per-VM devices and their sensors."""

from __future__ import annotations

from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant.common import MockConfigEntry

from custom_components.unraid_management_agent import (
    async_remove_config_entry_device,
)
from custom_components.unraid_management_agent.api.models import VMInfo
from custom_components.unraid_management_agent.cleanup import (
    _async_remove_empty_devices,
    _build_valid_dynamic_entity_keys,
)
from custom_components.unraid_management_agent.const import (
    CONF_ENABLE_VM_DEVICES,
    DOMAIN,
)
from custom_components.unraid_management_agent.coordinator import UnraidData

from .const import MOCK_CONFIG, MOCK_OPTIONS

GIB = 1024**3
T0 = datetime(2026, 10, 8, 12, 0, 0, tzinfo=UTC)
ENTRY_ID = "test_entry_id"
WIN10_ID = "b823288b65f87be1e892140bb4a8929b"
UBUNTU_ID = "985351ae2bb817c5484904fc57076fa5"


def _entry(hass: HomeAssistant, *, vm_devices: bool) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Unraid (unraid-test)",
        data=MOCK_CONFIG,
        options={**MOCK_OPTIONS, CONF_ENABLE_VM_DEVICES: vm_devices},
        entry_id=ENTRY_ID,
    )
    entry.add_to_hass(hass)
    return entry


@pytest.fixture
def mock_config_entry(hass: HomeAssistant) -> MockConfigEntry:
    """Config entry with "VMs as separate devices" turned on."""
    return _entry(hass, vm_devices=True)


def _vm(  # noqa: PLR0913
    *,
    vm_id: str = WIN10_ID,
    name: str = "Windows 10",
    state: str = "running",
    rx: int = 1_000_000,
    tx: int = 500_000,
    at: datetime = T0,
) -> VMInfo:
    """Build a VMInfo the way the agent reports it."""
    return VMInfo(
        id=vm_id,
        name=name,
        state=state,
        cpu_count=16,
        guest_cpu_percent=12.5,
        memory_allocated_bytes=32 * GIB,
        memory_used_bytes=32 * GIB,
        disk_size_bytes=0,
        disk_read_bytes=0,
        disk_write_bytes=0,
        network_rx_bytes=rx,
        network_tx_bytes=tx,
        autostart=False,
        persistent=True,
        timestamp=at.isoformat(),
    )


@pytest.fixture
def vm_client(mock_async_unraid_client: MagicMock) -> Generator[MagicMock]:
    """Serve real VMInfo models: one running VM and one stopped VM."""
    mock_async_unraid_client.list_vms.return_value = [
        _vm(),
        _vm(vm_id=UBUNTU_ID, name="Ubuntu", state="shut off"),
    ]
    return mock_async_unraid_client


async def _push_vms(hass: HomeAssistant, entry, vms: list[VMInfo]) -> None:
    """Deliver new VM data through the coordinator, as a websocket event would."""
    coordinator = entry.runtime_data.coordinator
    coordinator.data.vms = vms
    coordinator.async_set_updated_data(coordinator.data)
    await hass.async_block_till_done()


@pytest.mark.usefixtures("vm_client", "mock_unraid_websocket_client_class")
async def test_each_vm_gets_a_child_device_of_the_vms_device(
    hass: HomeAssistant, mock_config_entry
) -> None:
    """VM controls and metrics live on a per-VM child device of the VMs device."""
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    devices = dr.async_get(hass)
    server = devices.async_get_device_by_identifier((DOMAIN, ENTRY_ID), ENTRY_ID)
    vm_device = devices.async_get_child_device_by_identifier(
        (DOMAIN, f"{ENTRY_ID}_vm_{WIN10_ID}"), ENTRY_ID
    )
    vms = devices.async_get_device_by_identifier((DOMAIN, f"{ENTRY_ID}_vms"), ENTRY_ID)
    assert server is not None
    assert vms is not None
    assert vms.name == "unraid-test VMs"
    assert vms.via_device_id == server.id
    assert vm_device is not None
    assert vm_device.name == "Windows 10"
    assert vm_device.parent_device_id == vms.id

    entities = er.async_get(hass)
    on_vm_device = {
        e.entity_id
        for e in er.async_entries_for_device(
            entities, vm_device.id, include_disabled_entities=True
        )
    }
    assert "switch.unraid_test_vms_windows_10_power" in on_vm_device
    assert "button.unraid_test_vms_windows_10_force_stop" in on_vm_device
    assert "sensor.unraid_test_vms_windows_10_cpu_usage" in on_vm_device
    assert "sensor.unraid_test_vms_windows_10_disk_read_rate" in on_vm_device


@pytest.mark.usefixtures("vm_client", "mock_unraid_websocket_client_class")
async def test_option_off_keeps_vms_on_the_server_device(hass: HomeAssistant) -> None:
    """With the option off (default) nothing changes: no VM devices or sensors."""
    entry = _entry(hass, vm_devices=False)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    devices = dr.async_get(hass)
    assert not dr.async_child_entries_for_config_entry(devices, ENTRY_ID)
    server = devices.async_get_device_by_identifier((DOMAIN, ENTRY_ID), ENTRY_ID)
    assert server is not None

    entities = er.async_get(hass)
    switch = entities.async_get("switch.unraid_test_vm_windows_10")
    assert switch is not None
    assert switch.device_id == server.id
    vm_sensors = [
        e
        for e in er.async_entries_for_config_entry(entities, ENTRY_ID)
        if e.domain == "sensor" and e.unique_id.startswith(f"{ENTRY_ID}_vm_")
    ]
    assert not vm_sensors


def test_cleanup_keeps_vm_sensors_only_with_the_option() -> None:
    """VM sensor keys are valid only while VMs are separate devices."""
    data = UnraidData(vms=[_vm()])
    sensor_key = f"vm_{WIN10_ID}_cpu_usage"
    assert sensor_key in _build_valid_dynamic_entity_keys(data, vm_devices=True)
    assert sensor_key not in _build_valid_dynamic_entity_keys(data, vm_devices=False)


@pytest.mark.usefixtures("vm_client", "mock_unraid_websocket_client_class")
async def test_vm_device_without_entities_is_removed(
    hass: HomeAssistant, mock_config_entry
) -> None:
    """A VM device whose entities are all gone is removed from the registry."""
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    devices = dr.async_get(hass)
    entities = er.async_get(hass)
    ubuntu = devices.async_get_child_device_by_identifier(
        (DOMAIN, f"{ENTRY_ID}_vm_{UBUNTU_ID}"), ENTRY_ID
    )
    assert ubuntu is not None
    for entity in er.async_entries_for_device(
        entities, ubuntu.id, include_disabled_entities=True
    ):
        entities.async_remove(entity.entity_id)

    _async_remove_empty_devices(hass, mock_config_entry)

    assert (
        devices.async_get_child_device_by_identifier(
            (DOMAIN, f"{ENTRY_ID}_vm_{UBUNTU_ID}"), ENTRY_ID
        )
        is None
    )
    assert (
        devices.async_get_child_device_by_identifier(
            (DOMAIN, f"{ENTRY_ID}_vm_{WIN10_ID}"), ENTRY_ID
        )
        is not None
    )


@pytest.mark.usefixtures("vm_client", "mock_unraid_websocket_client_class")
async def test_only_devices_of_deleted_vms_can_be_removed(
    hass: HomeAssistant, mock_config_entry
) -> None:
    """Users may delete a VM device once the VM is gone, never the server."""
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    devices = dr.async_get(hass)
    server = devices.async_get_device_by_identifier((DOMAIN, ENTRY_ID), ENTRY_ID)
    ubuntu = devices.async_get_child_device_by_identifier(
        (DOMAIN, f"{ENTRY_ID}_vm_{UBUNTU_ID}"), ENTRY_ID
    )

    assert not await async_remove_config_entry_device(hass, mock_config_entry, server)
    assert not await async_remove_config_entry_device(hass, mock_config_entry, ubuntu)
    mock_config_entry.runtime_data.coordinator.data.vms = None
    assert not await async_remove_config_entry_device(hass, mock_config_entry, ubuntu)
    await _push_vms(hass, mock_config_entry, [_vm()])
    assert await async_remove_config_entry_device(hass, mock_config_entry, ubuntu)


@pytest.mark.usefixtures("vm_client", "mock_unraid_websocket_client_class")
async def test_removed_vm_sensor_is_recreated(
    hass: HomeAssistant, mock_config_entry
) -> None:
    """VM sensors removed from the registry come back on the next update (#83)."""
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    entities = er.async_get(hass)
    for entity in er.async_entries_for_config_entry(entities, ENTRY_ID):
        if entity.unique_id.startswith(f"{ENTRY_ID}_vm_{WIN10_ID}_"):
            entities.async_remove(entity.entity_id)
    assert entities.async_get("sensor.unraid_test_vms_windows_10_state") is None

    await _push_vms(hass, mock_config_entry, [_vm()])

    assert hass.states.get("sensor.unraid_test_vms_windows_10_state").state == "running"


@pytest.mark.usefixtures("vm_client", "mock_unraid_websocket_client_class")
async def test_vm_metric_sensors(hass: HomeAssistant, mock_config_entry) -> None:
    """Metrics are numeric sensors with units, not formatted attribute strings."""
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert hass.states.get("sensor.unraid_test_vms_windows_10_state").state == "running"
    assert (
        hass.states.get("sensor.unraid_test_vms_windows_10_state").attributes[
            "autostart"
        ]
        is False
    )
    assert (
        float(hass.states.get("sensor.unraid_test_vms_windows_10_cpu_usage").state)
        == 12.5
    )
    assert hass.states.get("sensor.unraid_test_vms_windows_10_vcpus").state == "16"
    memory = hass.states.get("sensor.unraid_test_vms_windows_10_memory_allocated")
    assert float(memory.state) == 32
    assert memory.attributes["unit_of_measurement"] == "GiB"
    assert hass.states.get("sensor.unraid_test_vms_ubuntu_state").state == "shut off"

    # Disabled by default: disk counters are often 0 and memory used == allocated
    entities = er.async_get(hass)
    assert entities.async_get(
        "sensor.unraid_test_vms_windows_10_disk_read_rate"
    ).disabled_by
    assert entities.async_get(
        "sensor.unraid_test_vms_windows_10_memory_used"
    ).disabled_by


@pytest.mark.usefixtures("vm_client", "mock_unraid_websocket_client_class")
async def test_vm_network_rate(hass: HomeAssistant, mock_config_entry) -> None:
    """Network rate comes from successive agent samples of the byte counters."""
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    rx = "sensor.unraid_test_vms_windows_10_network_receive_rate"
    # One sample is not a rate yet; like the host network sensors it reads 0
    assert float(hass.states.get(rx).state) == 0

    # 7.5 MB in 60 s = 1 Mbit/s
    later = T0 + timedelta(seconds=60)
    await _push_vms(hass, mock_config_entry, [_vm(rx=8_500_000, at=later)])
    state = hass.states.get(rx)
    assert float(state.state) == pytest.approx(1.0)
    assert state.attributes["unit_of_measurement"] == "Mbit/s"

    # A websocket push that re-delivers the same VM sample changes nothing
    await _push_vms(hass, mock_config_entry, [_vm(rx=8_500_000, at=later)])
    assert float(hass.states.get(rx).state) == pytest.approx(1.0)

    # A new sample with no traffic is a real zero
    await _push_vms(
        hass,
        mock_config_entry,
        [_vm(rx=8_500_000, at=later + timedelta(seconds=60))],
    )
    assert float(hass.states.get(rx).state) == 0

    # VM restarted: the counter dropped, so no huge "wrapped" rate
    await _push_vms(
        hass,
        mock_config_entry,
        [_vm(rx=10_000, at=later + timedelta(seconds=120))],
    )
    assert float(hass.states.get(rx).state) == 0

    # A stopped VM has no traffic
    await _push_vms(
        hass,
        mock_config_entry,
        [_vm(state="shut off", at=later + timedelta(seconds=180))],
    )
    assert float(hass.states.get(rx).state) == 0


@pytest.mark.usefixtures("vm_client", "mock_unraid_websocket_client_class")
async def test_vm_sensors_unavailable_when_vm_removed(
    hass: HomeAssistant, mock_config_entry
) -> None:
    """Sensors of a VM the agent no longer reports become unavailable."""
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    await _push_vms(hass, mock_config_entry, [_vm()])
    assert hass.states.get("sensor.unraid_test_vms_ubuntu_state").state == "unavailable"


@pytest.mark.usefixtures("vm_client", "mock_unraid_websocket_client_class")
async def test_vm_added_later_gets_sensors(
    hass: HomeAssistant, mock_config_entry
) -> None:
    """A VM created after setup gets its device and sensors without a reload."""
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    await _push_vms(
        hass,
        mock_config_entry,
        [_vm(), _vm(vm_id="cc51802580ace090e783627716506e13", name="k3s-ag-2")],
    )
    assert hass.states.get("sensor.unraid_test_vms_k3s_ag_2_state").state == "running"


@pytest.mark.usefixtures("vm_client", "mock_unraid_websocket_client_class")
async def test_renamed_vm_is_not_confused_with_one_reusing_its_name(
    hass: HomeAssistant, mock_config_entry
) -> None:
    """The VM identifier wins over a name match on another VM."""
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    # Windows 10 is renamed; a new VM (listed first) takes its old name
    await _push_vms(
        hass,
        mock_config_entry,
        [
            _vm(vm_id="aaaa", name="Windows 10", state="shut off"),
            _vm(name="Windows 10 (old)"),
        ],
    )
    assert hass.states.get("sensor.unraid_test_vms_windows_10_state").state == "running"


@pytest.mark.usefixtures("vm_client", "mock_unraid_websocket_client_class")
async def test_existing_vm_device_moves_under_the_vms_device(
    hass: HomeAssistant, mock_config_entry
) -> None:
    """A "VM · " device under the server moves under the VMs device, renamed."""
    devices = dr.async_get(hass)
    entities = er.async_get(hass)
    # The registry as the previous version left it: a prefixed child device of
    # the server
    server = devices.async_get_or_create(
        config_entry_id=ENTRY_ID, identifiers={(DOMAIN, ENTRY_ID)}, name="unraid-test"
    )
    vm_device = devices.async_get_or_create_child(
        config_entry_id=ENTRY_ID,
        identifiers={(DOMAIN, f"{ENTRY_ID}_vm_{WIN10_ID}")},
        name="VM · Windows 10",
        parent_device_id=server.id,
    )
    old_device_id = vm_device.id
    cpu = entities.async_get_or_create(
        "sensor",
        DOMAIN,
        f"{ENTRY_ID}_vm_{WIN10_ID}_cpu_usage",
        config_entry=mock_config_entry,
        device_id=vm_device.id,
        suggested_object_id="unraid_test_vm_windows_10_cpu_usage",
    )
    assert cpu.entity_id == "sensor.unraid_test_vm_windows_10_cpu_usage"

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    vms = devices.async_get_device_by_identifier((DOMAIN, f"{ENTRY_ID}_vms"), ENTRY_ID)
    vm_device = devices.async_get_child_device_by_identifier(
        (DOMAIN, f"{ENTRY_ID}_vm_{WIN10_ID}"), ENTRY_ID
    )
    assert vms is not None
    assert vm_device is not None
    assert vm_device.id == old_device_id
    assert vm_device.parent_device_id == vms.id
    assert vm_device.name == "Windows 10"
    cpu_entry = entities.async_get("sensor.unraid_test_vm_windows_10_cpu_usage")
    assert cpu_entry is not None
    assert cpu_entry.unique_id == f"{ENTRY_ID}_vm_{WIN10_ID}_cpu_usage"
    assert cpu_entry.device_id == old_device_id
    assert (
        float(hass.states.get("sensor.unraid_test_vm_windows_10_cpu_usage").state)
        == 12.5
    )


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_renamed_vm_device_follows_the_new_name(
    hass: HomeAssistant, mock_config_entry, vm_client: MagicMock
) -> None:
    """After a VM rename the device name follows; entity IDs stay the same."""
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    devices = dr.async_get(hass)
    entities = er.async_get(hass)
    unique_id = f"{ENTRY_ID}_vm_{WIN10_ID}_cpu_usage"
    entity_id = entities.async_get_entity_id("sensor", DOMAIN, unique_id)
    assert entity_id == "sensor.unraid_test_vms_windows_10_cpu_usage"

    vm_client.list_vms.return_value = [_vm(name="Windows 11")]
    assert await hass.config_entries.async_reload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    vm_device = devices.async_get_child_device_by_identifier(
        (DOMAIN, f"{ENTRY_ID}_vm_{WIN10_ID}"), ENTRY_ID
    )
    assert vm_device is not None
    assert vm_device.name == "Windows 11"
    assert entities.async_get_entity_id("sensor", DOMAIN, unique_id) == entity_id


@pytest.mark.usefixtures("vm_client", "mock_unraid_websocket_client_class")
async def test_user_set_vm_device_name_is_kept(
    hass: HomeAssistant, mock_config_entry
) -> None:
    """A name the user gave the VM device survives a reload."""
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    devices = dr.async_get(hass)
    identifier = (DOMAIN, f"{ENTRY_ID}_vm_{WIN10_ID}")
    vm_device = devices.async_get_child_device_by_identifier(identifier, ENTRY_ID)
    assert vm_device is not None
    devices.async_update_child_device(vm_device.id, name_by_user="Gaming PC")

    assert await hass.config_entries.async_reload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    vm_device = devices.async_get_child_device_by_identifier(identifier, ENTRY_ID)
    assert vm_device is not None
    assert vm_device.name_by_user == "Gaming PC"
    assert vm_device.name == "Windows 10"


@pytest.mark.usefixtures("vm_client", "mock_unraid_websocket_client_class")
async def test_toggling_vm_devices_option_removes_sensors_and_devices(
    hass: HomeAssistant,
) -> None:
    """Toggling VM devices from True to False removes VM sensors and removes VM child devices."""
    entry = _entry(hass, vm_devices=True)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    devices = dr.async_get(hass)
    entities = er.async_get(hass)
    server = devices.async_get_device_by_identifier((DOMAIN, ENTRY_ID), ENTRY_ID)
    assert server is not None

    vm_device = devices.async_get_child_device_by_identifier(
        (DOMAIN, f"{ENTRY_ID}_vm_{WIN10_ID}"), ENTRY_ID
    )
    assert vm_device is not None

    # Per-VM sensor exists on the VM device
    cpu_sensor = entities.async_get("sensor.unraid_test_vms_windows_10_cpu_usage")
    assert cpu_sensor is not None
    assert cpu_sensor.device_id == vm_device.id

    # VM switch exists on the VM device
    vm_switch = entities.async_get("switch.unraid_test_vms_windows_10_power")
    assert vm_switch is not None
    assert vm_switch.device_id == vm_device.id

    hass.config_entries.async_update_entry(
        entry, options={**entry.options, CONF_ENABLE_VM_DEVICES: False}
    )
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()

    # VM device is gone immediately
    assert (
        devices.async_get_child_device_by_identifier(
            (DOMAIN, f"{ENTRY_ID}_vm_{WIN10_ID}"), ENTRY_ID
        )
        is None
    )

    # Per-VM sensor is removed from registry
    assert entities.async_get("sensor.unraid_test_vms_windows_10_cpu_usage") is None

    # VM switch is preserved and reparented to server
    vm_switch = entities.async_get("switch.unraid_test_vms_windows_10_power")
    assert vm_switch is not None
    assert vm_switch.device_id == server.id
