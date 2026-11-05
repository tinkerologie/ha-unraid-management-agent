"""Test per-GPU child devices (the "GPUs as separate devices" option)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant.common import (
    MockConfigEntry,
    mock_restore_cache_with_extra_data,
)

from custom_components.unraid_management_agent import (
    async_remove_config_entry_device,
)
from custom_components.unraid_management_agent.api.models import (
    CollectorDetails,
    CollectorStatus,
    GPUInfo,
)
from custom_components.unraid_management_agent.cleanup import (
    _async_remove_empty_devices,
)
from custom_components.unraid_management_agent.const import (
    CONF_ENABLE_GPU_DEVICES,
    DOMAIN,
)
from custom_components.unraid_management_agent.coordinator import UnraidData
from custom_components.unraid_management_agent.entity import (
    build_gpu_device_info,
    gpu_device_keys,
)
from custom_components.unraid_management_agent.sensor import (
    UnraidGPUEnergySensor,
    UnraidGPUEnergySensorExtraStoredData,
)

from .const import MOCK_CONFIG, MOCK_OPTIONS

ENTRY_ID = "test_entry_id"
RTX_3070_UUID = "GPU-00000000-0000-0000-0000-000000003070"
RTX_4090_UUID = "GPU-00000000-0000-0000-0000-000000004090"
RTX_3070_DEVICE = (DOMAIN, f"{ENTRY_ID}_gpu_uuid_{RTX_3070_UUID.lower()}")
RTX_4090_DEVICE = (DOMAIN, f"{ENTRY_ID}_gpu_uuid_{RTX_4090_UUID.lower()}")
INTEL_DEVICE = (DOMAIN, f"{ENTRY_ID}_gpu_pci_0000:00:02.0")
LEGACY_DEVICE = (DOMAIN, f"{ENTRY_ID}_gpu_index_2")


def _gpu(index: int, name: str, **fields: object) -> GPUInfo:
    """Build a GPUInfo the way the agent reports it."""
    return GPUInfo.model_validate(
        {
            "available": True,
            "index": index,
            "name": name,
            "temperature_celsius": 40,
            "utilization_gpu_percent": 5,
            "power_draw_watts": 20,
            **fields,
        }
    )


def _rtx_3070(index: int = 0) -> GPUInfo:
    return _gpu(
        index,
        "NVIDIA GeForce RTX 3070",
        vendor="nvidia",
        uuid=RTX_3070_UUID,
        pci_id="00000000:42:00.0",
        driver_version="615.78.08",
        memory_total_bytes=8589934592,
        memory_used_bytes=12582912,
    )


def _rtx_4090(index: int = 0) -> GPUInfo:
    return _gpu(
        index,
        "NVIDIA GeForce RTX 4090",
        vendor="nvidia",
        uuid=RTX_4090_UUID,
        pci_id="00000000:01:00.0",
        driver_version="615.78.08",
        memory_total_bytes=25769803776,
        memory_used_bytes=12582912,
    )


# The Intel collector reports the PCI address but no UUID
INTEL_IGPU = _gpu(1, "Intel UHD Graphics 770", vendor="intel", pci_id="0000:00:02.0")
# An older agent that sends neither UUID nor PCI address
LEGACY_GPU = _gpu(2, "Legacy GPU", vendor="nvidia")


def _entry(hass: HomeAssistant, *, gpu_devices: bool = True) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Unraid (unraid-test)",
        data=MOCK_CONFIG,
        options={**MOCK_OPTIONS, CONF_ENABLE_GPU_DEVICES: gpu_devices},
        entry_id=ENTRY_ID,
    )
    entry.add_to_hass(hass)
    return entry


async def _setup(
    hass: HomeAssistant,
    client: MagicMock,
    gpus: list[GPUInfo] | None,
    *,
    gpu_devices: bool = True,
) -> MockConfigEntry:
    client.list_gpus.return_value = gpus
    entry = _entry(hass, gpu_devices=gpu_devices)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def _push_gpus(
    hass: HomeAssistant,
    entry: MockConfigEntry,
    client: MagicMock,
    gpus: list[GPUInfo] | None,
) -> None:
    """Deliver new GPU data, as a websocket event would (and a reload fetches)."""
    client.list_gpus.return_value = gpus
    coordinator = entry.runtime_data.coordinator
    coordinator.data.gpu = gpus
    coordinator.async_set_updated_data(coordinator.data)
    await hass.async_block_till_done()


def _gpu_entities(hass: HomeAssistant) -> dict[str, er.RegistryEntry]:
    """Return the GPU sensors of the entry by key (unique ID without entry ID)."""
    return {
        entity.unique_id.removeprefix(f"{ENTRY_ID}_"): entity
        for entity in er.async_entries_for_config_entry(er.async_get(hass), ENTRY_ID)
        if entity.unique_id.startswith(f"{ENTRY_ID}_gpu_")
    }


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_each_gpu_gets_a_child_device_of_the_server(
    hass: HomeAssistant, mock_async_unraid_client: MagicMock
) -> None:
    """GPU sensors live on a per-GPU child device, keyed by its hardware ID."""
    await _setup(hass, mock_async_unraid_client, [_rtx_3070(), INTEL_IGPU, LEGACY_GPU])

    devices = dr.async_get(hass)
    server = devices.async_get_device_by_identifier((DOMAIN, ENTRY_ID), ENTRY_ID)
    assert server is not None
    expected = {
        RTX_3070_DEVICE: ("GPU · NVIDIA GeForce RTX 3070", "gpu_0_"),
        INTEL_DEVICE: ("GPU · Intel UHD Graphics 770", "gpu_1_"),
        LEGACY_DEVICE: ("GPU · Legacy GPU", "gpu_2_"),
    }
    gpu_entities = _gpu_entities(hass)
    for identifier, (name, key_prefix) in expected.items():
        device = devices.async_get_child_device_by_identifier(identifier, ENTRY_ID)
        assert device is not None
        assert device.name == name
        assert device.parent_device_id == server.id
        on_device = {key for key, e in gpu_entities.items() if e.device_id == device.id}
        assert on_device
        assert all(key.startswith(key_prefix) for key in on_device)
    # No GPU sensor is left on the server device
    assert all(e.device_id != server.id for e in gpu_entities.values())

    # The device name replaces the GPU name the sensor names used to carry
    state = hass.states.get(gpu_entities["gpu_0_temperature"].entity_id)
    assert state is not None
    assert (
        state.entity_id == "sensor.unraid_test_gpu_nvidia_geforce_rtx_3070_temperature"
    )
    assert state.attributes["friendly_name"] == (
        "GPU · NVIDIA GeForce RTX 3070 Temperature"
    )
    vram = hass.states.get(gpu_entities["gpu_0_vram_used"].entity_id)
    assert vram is not None
    assert vram.attributes["friendly_name"] == (
        "GPU · NVIDIA GeForce RTX 3070 VRAM used"
    )


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_existing_gpu_entities_keep_their_ids_and_move_to_the_gpu(
    hass: HomeAssistant, mock_async_unraid_client: MagicMock
) -> None:
    """Upgrading moves existing GPU sensors to the GPU device, keeping entity IDs."""
    entry = _entry(hass)
    devices = dr.async_get(hass)
    server = devices.async_get_or_create(
        config_entry_id=ENTRY_ID, identifiers={(DOMAIN, ENTRY_ID)}, name="unraid"
    )
    entities = er.async_get(hass)
    old = entities.async_get_or_create(
        "sensor",
        DOMAIN,
        f"{ENTRY_ID}_gpu_0_vram_used",
        config_entry=entry,
        device_id=server.id,
        suggested_object_id="unfinished_basement_unraid_gpu_nvidia_geforce_rtx_3070_vram_used",
    )
    assert old.entity_id == (
        "sensor.unfinished_basement_unraid_gpu_nvidia_geforce_rtx_3070_vram_used"
    )

    mock_async_unraid_client.list_gpus.return_value = [_rtx_3070()]
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    moved = entities.async_get(old.entity_id)
    assert moved is not None
    assert moved.unique_id == f"{ENTRY_ID}_gpu_0_vram_used"
    gpu = devices.async_get_child_device_by_identifier(RTX_3070_DEVICE, ENTRY_ID)
    assert gpu is not None
    assert moved.device_id == gpu.id
    assert hass.states.get(old.entity_id) is not None


def test_gpu_device_keys() -> None:
    """Hardware IDs are preferred; missing, placeholder or shared ones use the index."""
    assert gpu_device_keys(None) == {}
    assert gpu_device_keys([_rtx_3070(), INTEL_IGPU, LEGACY_GPU]) == {
        0: f"uuid_{RTX_3070_UUID.lower()}",
        1: "pci_0000:00:02.0",
        2: "index_2",
    }
    # nvidia-smi placeholders and blanks are not IDs; the PCI address is next
    placeholder = _gpu(0, "GPU", uuid="[N/A]", pci_id=" 00000000:0A:00.0 ")
    blank = _gpu(1, "GPU", uuid=" ", pci_id="N/A")
    assert gpu_device_keys([placeholder, blank]) == {
        0: "pci_00000000:0a:00.0",
        1: "index_1",
    }
    # Two GPUs reporting the same ID must not share a device
    twin = _gpu(1, "GPU", uuid=RTX_3070_UUID)
    assert gpu_device_keys([_rtx_3070(), twin]) == {0: "index_0", 1: "index_1"}
    # Without an index the GPU's position is used, as for its sensors
    no_index = GPUInfo.model_validate({"name": "GPU"})
    assert gpu_device_keys([no_index]) == {0: "index_0"}


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_gpu_taking_an_index_moves_the_sensors_to_its_device(
    hass: HomeAssistant, mock_async_unraid_client: MagicMock
) -> None:
    """
    A GPU appearing in front of another shifts the indexes; the entry reloads.

    The sensors of each index then sit on the device of the GPU now at that
    index, and the 3070 keeps its device (and with it its name and area).
    """
    entry = await _setup(hass, mock_async_unraid_client, [_rtx_3070()])
    devices = dr.async_get(hass)
    rtx_3070 = devices.async_get_child_device_by_identifier(RTX_3070_DEVICE, ENTRY_ID)
    assert rtx_3070 is not None
    devices.async_update_child_device(rtx_3070.id, name_by_user="Plex GPU")

    with patch.object(
        hass.config_entries,
        "async_schedule_reload",
        wraps=hass.config_entries.async_schedule_reload,
    ) as schedule_reload:
        await _push_gpus(
            hass, entry, mock_async_unraid_client, [_rtx_4090(0), _rtx_3070(1)]
        )
        # Further updates before the reload finishes don't schedule another
        entry.runtime_data.coordinator.async_update_listeners()
        await hass.async_block_till_done()
    schedule_reload.assert_called_once_with(ENTRY_ID)

    rtx_4090 = devices.async_get_child_device_by_identifier(RTX_4090_DEVICE, ENTRY_ID)
    rtx_3070 = devices.async_get_child_device_by_identifier(RTX_3070_DEVICE, ENTRY_ID)
    assert rtx_4090 is not None
    assert rtx_3070 is not None
    assert rtx_3070.name_by_user == "Plex GPU"
    gpu_entities = _gpu_entities(hass)
    assert gpu_entities["gpu_0_temperature"].device_id == rtx_4090.id
    assert gpu_entities["gpu_1_temperature"].device_id == rtx_3070.id


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
@pytest.mark.parametrize(
    ("setup_gpus", "new_gpus", "device", "key"),
    [
        pytest.param(
            [_rtx_3070()],
            [_rtx_3070(0), _rtx_4090(1)],
            RTX_4090_DEVICE,
            "gpu_1_temperature",
            id="gpu added after the others",
        ),
        pytest.param(
            [_rtx_3070(0)],
            [_rtx_3070(1)],
            RTX_3070_DEVICE,
            "gpu_1_temperature",
            id="gpu moved to a free index",
        ),
        pytest.param(
            None, [_rtx_3070()], RTX_3070_DEVICE, "gpu_0_temperature", id="fetch failed"
        ),
        pytest.param(
            [], [_rtx_3070()], RTX_3070_DEVICE, "gpu_0_temperature", id="no gpus"
        ),
    ],
)
async def test_gpu_at_an_index_without_sensors_gets_them(  # noqa: PLR0913
    hass: HomeAssistant,
    mock_async_unraid_client: MagicMock,
    setup_gpus: list[GPUInfo] | None,
    new_gpus: list[GPUInfo],
    device: tuple[str, str],
    key: str,
) -> None:
    """A GPU at an index that has no sensors yet reloads the entry to add them."""
    entry = await _setup(hass, mock_async_unraid_client, setup_gpus)
    assert key not in _gpu_entities(hass)

    await _push_gpus(hass, entry, mock_async_unraid_client, new_gpus)

    gpu = dr.async_get(hass).async_get_child_device_by_identifier(device, ENTRY_ID)
    assert gpu is not None
    assert _gpu_entities(hass)[key].device_id == gpu.id


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_gpu_back_after_cleanup_gets_its_sensors_again(
    hass: HomeAssistant, mock_async_unraid_client: MagicMock
) -> None:
    """A GPU whose sensors stale cleanup removed while it was gone gets them back."""
    entry = await _setup(hass, mock_async_unraid_client, [_rtx_3070()])
    await _push_gpus(hass, entry, mock_async_unraid_client, [])
    entities = er.async_get(hass)
    for entity in _gpu_entities(hass).values():
        entities.async_remove(entity.entity_id)

    await _push_gpus(hass, entry, mock_async_unraid_client, [_rtx_3070()])

    assert "gpu_0_temperature" in _gpu_entities(hass)


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
@pytest.mark.parametrize(
    "updates",
    [
        pytest.param([None], id="fetch failed"),
        pytest.param([[]], id="gpu missing"),
        pytest.param([[], [_rtx_3070()]], id="gpu back with its sensors"),
    ],
)
async def test_no_reload_while_each_index_keeps_its_gpu(
    hass: HomeAssistant,
    mock_async_unraid_client: MagicMock,
    updates: list[list[GPUInfo] | None],
) -> None:
    """Unavailable GPU data, or a GPU missing for a while, doesn't reload the entry."""
    entry = await _setup(hass, mock_async_unraid_client, [_rtx_3070()])

    with patch.object(hass.config_entries, "async_schedule_reload") as reload:
        for gpus in updates:
            await _push_gpus(hass, entry, mock_async_unraid_client, gpus)
        entry.runtime_data.coordinator.data = None
        entry.runtime_data.coordinator.async_update_listeners()
        await hass.async_block_till_done()
    reload.assert_not_called()


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_gpu_device_removal(
    hass: HomeAssistant, mock_async_unraid_client: MagicMock
) -> None:
    """
    A GPU device can be deleted once the GPU is gone, and is cleaned up.

    While GPU data is unavailable nothing is known to be gone, so the device
    can't be deleted.
    """
    entry = await _setup(hass, mock_async_unraid_client, [_rtx_3070(), INTEL_IGPU])
    devices = dr.async_get(hass)
    entities = er.async_get(hass)
    intel = devices.async_get_child_device_by_identifier(INTEL_DEVICE, ENTRY_ID)
    assert intel is not None

    assert not await async_remove_config_entry_device(hass, entry, intel)
    await _push_gpus(hass, entry, mock_async_unraid_client, None)
    assert not await async_remove_config_entry_device(hass, entry, intel)
    await _push_gpus(hass, entry, mock_async_unraid_client, [_rtx_3070()])
    assert await async_remove_config_entry_device(hass, entry, intel)

    # Once stale cleanup has removed its sensors, the empty device goes too
    for entity in er.async_entries_for_device(
        entities, intel.id, include_disabled_entities=True
    ):
        entities.async_remove(entity.entity_id)
    _async_remove_empty_devices(hass, entry)
    assert devices.async_get_child_device_by_identifier(INTEL_DEVICE, ENTRY_ID) is None
    assert (
        devices.async_get_child_device_by_identifier(RTX_3070_DEVICE, ENTRY_ID)
        is not None
    )


async def test_gpu_device_info_falls_back_to_server_when_server_missing(
    hass: HomeAssistant,
) -> None:
    """Without a registered server device, GPU sensors stay on the server."""
    coordinator = MagicMock()
    coordinator.hass = hass
    coordinator.config_entry = _entry(hass)

    info = build_gpu_device_info(coordinator, 0, "NVIDIA GeForce RTX 3070")

    assert info == {"identifiers": {(DOMAIN, ENTRY_ID)}}


async def test_gpu_device_info_without_data_uses_the_index(
    hass: HomeAssistant,
) -> None:
    """Before any GPU data arrives the device is keyed by the index."""
    entry = _entry(hass)
    server = dr.async_get(hass).async_get_or_create(
        config_entry_id=ENTRY_ID, identifiers={(DOMAIN, ENTRY_ID)}
    )
    coordinator = MagicMock()
    coordinator.hass = hass
    coordinator.config_entry = entry
    coordinator.data = None

    info = build_gpu_device_info(coordinator, 3, "GPU 3")

    assert info == {
        "identifiers": {(DOMAIN, f"{ENTRY_ID}_gpu_index_3")},
        "parent_device_id": server.id,
        "translation_key": "gpu",
        "translation_placeholders": {"name": "GPU 3"},
    }


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_no_gpu_sensors_or_reload_with_the_collector_disabled(
    hass: HomeAssistant, mock_async_unraid_client: MagicMock
) -> None:
    """With the agent's GPU collector disabled, GPUs get no sensors or reloads."""
    mock_async_unraid_client.get_collectors_status.return_value = CollectorStatus(
        collectors=[CollectorDetails(name="gpu", enabled=False)]
    )
    entry = await _setup(hass, mock_async_unraid_client, [_rtx_3070()])
    assert not _gpu_entities(hass)

    with patch.object(hass.config_entries, "async_schedule_reload") as reload:
        await _push_gpus(hass, entry, mock_async_unraid_client, [_rtx_4090()])
    reload.assert_not_called()


ENERGY_ENTITY = "sensor.unraid_test_gpu_nvidia_geforce_rtx_3070_energy"


def _stored_energy(total: str, gpu_key: str | None) -> tuple[State, dict]:
    """Return a restore-cache entry for the index-0 GPU energy sensor."""
    extra = {
        "native_value": float(total),
        "native_unit_of_measurement": "kWh",
        "last_power_watts": 20.0,
        "last_timestamp": 1_000.0,
        "last_uptime_seconds": None,
    }
    if gpu_key is not None:
        extra["gpu_key"] = gpu_key
    return State(ENERGY_ENTITY, total), extra


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
@pytest.mark.parametrize(
    ("gpu_key", "expected"),
    [
        pytest.param(f"uuid_{RTX_3070_UUID.lower()}", 5.0, id="same gpu"),
        pytest.param(None, 5.0, id="stored before gpu keys"),
        pytest.param(f"uuid_{RTX_4090_UUID.lower()}", 0.0, id="another gpu"),
    ],
)
async def test_gpu_energy_is_restored_only_for_the_same_gpu(
    hass: HomeAssistant,
    mock_async_unraid_client: MagicMock,
    gpu_key: str | None,
    expected: float,
) -> None:
    """Energy measured on the GPU that had this index before isn't carried over."""
    entity_registry = er.async_get(hass)
    entity_registry.async_get_or_create(
        "sensor",
        DOMAIN,
        f"{ENTRY_ID}_gpu_0_energy",
        suggested_object_id="unraid_test_gpu_nvidia_geforce_rtx_3070_energy",
    )
    mock_restore_cache_with_extra_data(hass, [_stored_energy("5.0", gpu_key)])

    await _setup(hass, mock_async_unraid_client, [_rtx_3070()])

    state = hass.states.get(ENERGY_ENTITY)
    assert state is not None
    assert float(state.state) == expected


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_gpu_energy_stays_with_its_gpu_when_indexes_shift(
    hass: HomeAssistant, mock_async_unraid_client: MagicMock
) -> None:
    """After an index shift, the index's energy sensor doesn't keep the old GPU's total."""
    mock_restore_cache_with_extra_data(
        hass, [_stored_energy("5.0", f"uuid_{RTX_3070_UUID.lower()}")]
    )
    entry = await _setup(hass, mock_async_unraid_client, [_rtx_3070()])
    assert float(hass.states.get(ENERGY_ENTITY).state) == 5.0

    await _push_gpus(
        hass, entry, mock_async_unraid_client, [_rtx_4090(0), _rtx_3070(1)]
    )

    gpu_entities = _gpu_entities(hass)
    rtx_4090_energy = hass.states.get(gpu_entities["gpu_0_energy"].entity_id)
    assert rtx_4090_energy is not None
    assert float(rtx_4090_energy.state) == 0.0


def test_gpu_energy_ignores_another_gpu_until_the_reload() -> None:
    """Power of a GPU that took the sensor's index is not added to its total."""
    coordinator = MagicMock()
    coordinator.config_entry.options = {CONF_ENABLE_GPU_DEVICES: True}
    coordinator.data = UnraidData(gpu=[_rtx_3070()])
    energy = UnraidGPUEnergySensor(coordinator, MagicMock(), 0, "RTX 3070")
    energy._update_energy()
    assert energy._last_power == 20

    coordinator.data = UnraidData(gpu=[_rtx_4090(0)])
    with patch.object(energy._energy_integrator, "add_sample") as add_sample:
        energy._update_energy()
    add_sample.assert_not_called()


def test_gpu_energy_restore_data_parsing() -> None:
    """Invalid stored data is ignored; a stored key that isn't text is no key."""
    _, extra = _stored_energy("5.0", None)
    assert (
        UnraidGPUEnergySensorExtraStoredData.from_dict(
            {**extra, "last_power_watts": "invalid"}
        )
        is None
    )
    restored = UnraidGPUEnergySensorExtraStoredData.from_dict({**extra, "gpu_key": 3})
    assert restored is not None
    assert restored.gpu_key is None
    assert restored.native_value == 5.0


def test_gpu_energy_restore_data_round_trips_the_gpu_key() -> None:
    """The sensor stores its GPU's key, and it survives as_dict/from_dict."""
    coordinator = MagicMock()
    coordinator.config_entry.options = {CONF_ENABLE_GPU_DEVICES: True}
    coordinator.data = UnraidData(gpu=[_rtx_3070()])
    energy = UnraidGPUEnergySensor(coordinator, MagicMock(), 0, "RTX 3070")

    stored = energy.extra_restore_state_data
    assert stored.gpu_key == f"uuid_{RTX_3070_UUID.lower()}"
    data = stored.as_dict()
    assert data["gpu_key"] == stored.gpu_key

    restored = UnraidGPUEnergySensorExtraStoredData.from_dict(data)
    assert restored == stored


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_option_off_keeps_gpu_sensors_on_the_server_device(
    hass: HomeAssistant, mock_async_unraid_client: MagicMock
) -> None:
    """With the option off (default) GPU sensors stay on the server, named after the GPU."""
    await _setup(
        hass, mock_async_unraid_client, [_rtx_3070(), INTEL_IGPU], gpu_devices=False
    )

    devices = dr.async_get(hass)
    server = devices.async_get_device_by_identifier((DOMAIN, ENTRY_ID), ENTRY_ID)
    assert server is not None
    assert not dr.async_child_entries_for_config_entry(devices, ENTRY_ID)
    gpu_entities = _gpu_entities(hass)
    assert gpu_entities
    assert all(e.device_id == server.id for e in gpu_entities.values())
    state = hass.states.get(gpu_entities["gpu_0_temperature"].entity_id)
    assert state is not None
    assert (
        state.entity_id == "sensor.unraid_test_gpu_nvidia_geforce_rtx_3070_temperature"
    )
    assert state.attributes["friendly_name"] == (
        "unraid-test GPU NVIDIA GeForce RTX 3070 Temperature"
    )


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_option_off_behaves_as_before(
    hass: HomeAssistant, mock_async_unraid_client: MagicMock
) -> None:
    """With the option off GPU indexes don't reload the entry, and energy follows the index."""
    mock_restore_cache_with_extra_data(
        hass, [_stored_energy("5.0", f"uuid_{RTX_4090_UUID.lower()}")]
    )
    entry = await _setup(
        hass, mock_async_unraid_client, [_rtx_3070()], gpu_devices=False
    )
    assert float(hass.states.get(ENERGY_ENTITY).state) == 5.0

    rtx_4090 = _rtx_4090(0).model_copy(update={"power_draw_watts": 350.0})
    with patch.object(hass.config_entries, "async_schedule_reload") as reload:
        await _push_gpus(
            hass, entry, mock_async_unraid_client, [rtx_4090, _rtx_3070(1)]
        )
    reload.assert_not_called()
    # The index-0 sensor now measures the 4090, as before this option existed
    state = hass.states.get(ENERGY_ENTITY)
    assert state.attributes["current_power_watts"] == 350.0
    assert float(state.state) >= 5.0


async def _set_gpu_devices(
    hass: HomeAssistant, entry: MockConfigEntry, *, enabled: bool
) -> None:
    """Change the option through the options flow, which reloads the entry."""
    result = await hass.config_entries.options.async_init(entry.entry_id)
    schema = result["data_schema"].schema
    assert CONF_ENABLE_GPU_DEVICES in {str(key) for key in schema}
    await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={CONF_ENABLE_GPU_DEVICES: enabled}
    )
    await hass.async_block_till_done()


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_turning_the_option_on_and_off(
    hass: HomeAssistant, mock_async_unraid_client: MagicMock
) -> None:
    """
    Turning the option on moves GPU sensors to GPU devices; off moves them back.

    Entity IDs never change. Once the sensors are back on the server, the
    empty GPU devices are removed by the next cleanup.
    """
    entry = await _setup(
        hass, mock_async_unraid_client, [_rtx_3070()], gpu_devices=False
    )
    devices = dr.async_get(hass)
    server = devices.async_get_device_by_identifier((DOMAIN, ENTRY_ID), ENTRY_ID)
    entity_ids = {k: e.entity_id for k, e in _gpu_entities(hass).items()}

    await _set_gpu_devices(hass, entry, enabled=True)
    gpu = devices.async_get_child_device_by_identifier(RTX_3070_DEVICE, ENTRY_ID)
    assert gpu is not None
    gpu_entities = _gpu_entities(hass)
    assert {k: e.entity_id for k, e in gpu_entities.items()} == entity_ids
    assert all(e.device_id == gpu.id for e in gpu_entities.values())
    state = hass.states.get(entity_ids["gpu_0_temperature"])
    assert state.attributes["friendly_name"] == (
        "GPU \u00b7 NVIDIA GeForce RTX 3070 Temperature"
    )

    await _set_gpu_devices(hass, entry, enabled=False)
    gpu_entities = _gpu_entities(hass)
    assert {k: e.entity_id for k, e in gpu_entities.items()} == entity_ids
    assert all(e.device_id == server.id for e in gpu_entities.values())
    state = hass.states.get(entity_ids["gpu_0_temperature"])
    assert state.attributes["friendly_name"] == (
        "unraid-test GPU NVIDIA GeForce RTX 3070 Temperature"
    )
    await entry.runtime_data.coordinator.async_refresh()
    await hass.async_block_till_done()
    assert not dr.async_child_entries_for_config_entry(devices, ENTRY_ID)
