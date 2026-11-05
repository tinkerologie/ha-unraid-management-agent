"""Test per-GPU VRAM sensors."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity import EntityDescription
from pytest_homeassistant.common import MockConfigEntry

from custom_components.unraid_management_agent import (
    binary_sensor,
    button,
    number,
    sensor,
    switch,
)
from custom_components.unraid_management_agent.api.models import GPUInfo
from custom_components.unraid_management_agent.cleanup import (
    _build_valid_dynamic_entity_keys,
)
from custom_components.unraid_management_agent.const import DOMAIN
from custom_components.unraid_management_agent.coordinator import UnraidData
from custom_components.unraid_management_agent.sensor import (
    UnraidGPUVramTotalSensor,
    UnraidGPUVramUsageSensor,
    UnraidGPUVramUsedSensor,
)

from .const import MOCK_CONFIG, MOCK_OPTIONS

ENTRY_ID = "test_entry_id"
VRAM_SUFFIXES = ("vram_used", "vram_total", "vram_usage")

# Real /api/v1/gpu payload from an Unraid host (UUID anonymised)
RTX_3070 = GPUInfo.model_validate(
    {
        "available": True,
        "index": 0,
        "pci_id": "00000000:42:00.0",
        "vendor": "nvidia",
        "uuid": "GPU-00000000-0000-0000-0000-000000000000",
        "name": "NVIDIA GeForce RTX 3070",
        "driver_version": "615.78.08",
        "temperature_celsius": 29,
        "utilization_gpu_percent": 0,
        "utilization_memory_percent": 0.146484375,
        "memory_total_bytes": 8589934592,
        "memory_used_bytes": 12582912,
        "power_draw_watts": 14.9,
        "timestamp": "2026-10-08T23:09:53.086819829-04:00",
    }
)
# The agent sends 0 (not null) VRAM for an Intel iGPU, which shares system RAM
INTEL_IGPU = GPUInfo.model_validate(
    {
        "available": True,
        "index": 1,
        "vendor": "intel",
        "name": "Intel UHD Graphics 770",
        "driver_version": "i915",
        "temperature_celsius": 0,
        "cpu_temperature_celsius": 41,
        "utilization_gpu_percent": 3.2,
        "utilization_memory_percent": 0,
        "memory_total_bytes": 0,
        "memory_used_bytes": 0,
        "power_draw_watts": 1.1,
    }
)
# An older agent that does not send the memory fields at all
LEGACY_GPU = GPUInfo.model_validate(
    {"available": True, "index": 2, "vendor": "nvidia", "name": "Legacy GPU"}
)


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


def _coordinator(gpus: list[GPUInfo]) -> MagicMock:
    coordinator = MagicMock()
    coordinator.data = UnraidData(gpu=gpus)
    return coordinator


def _static_description_keys() -> set[str]:
    """Return the keys of every static (whole unique-ID) entity description."""
    keys: set[str] = set()
    for module in (binary_sensor, button, number, sensor, switch):
        for name, value in vars(module).items():
            # VM_SENSOR_DESCRIPTIONS keys are only used inside vm_<id>_<key>
            if not name.endswith("_DESCRIPTIONS") or name == "VM_SENSOR_DESCRIPTIONS":
                continue
            keys.update(d.key for d in value if isinstance(d, EntityDescription))
    return keys


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_vram_sensors_created_for_gpus_reporting_vram(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mock_async_unraid_client: MagicMock,
) -> None:
    """Only GPUs that report VRAM get VRAM sensors, with the real values."""
    mock_async_unraid_client.list_gpus.return_value = [
        RTX_3070,
        INTEL_IGPU,
        LEGACY_GPU,
    ]
    entry = _entry(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    vram = {
        e.unique_id.removeprefix(f"{ENTRY_ID}_"): e
        for e in er.async_entries_for_config_entry(entity_registry, ENTRY_ID)
        if "_vram_" in e.unique_id
    }
    assert set(vram) == {f"gpu_0_{suffix}" for suffix in VRAM_SUFFIXES}

    used = hass.states.get(vram["gpu_0_vram_used"].entity_id)
    assert used is not None
    assert used.entity_id == "sensor.unraid_test_gpu_nvidia_geforce_rtx_3070_vram_used"
    assert float(used.state) == 12  # 12582912 B
    assert used.attributes["unit_of_measurement"] == "MiB"
    assert used.attributes["device_class"] == "data_size"
    assert used.attributes["state_class"] == "measurement"
    assert vram["gpu_0_vram_used"].entity_category is None

    total = hass.states.get(vram["gpu_0_vram_total"].entity_id)
    assert total is not None
    assert float(total.state) == 8  # 8589934592 B
    assert total.attributes["unit_of_measurement"] == "GiB"
    assert total.attributes["device_class"] == "data_size"
    assert "state_class" not in total.attributes
    assert vram["gpu_0_vram_total"].entity_category is EntityCategory.DIAGNOSTIC

    usage = hass.states.get(vram["gpu_0_vram_usage"].entity_id)
    assert usage is not None
    assert float(usage.state) == 0.15
    assert usage.attributes["unit_of_measurement"] == "%"
    assert usage.attributes["state_class"] == "measurement"

    # All VRAM sensors are enabled by default
    assert all(e.disabled_by is None for e in vram.values())


def test_agent_memory_percent_is_vram_usage_not_controller_load() -> None:
    """
    The agent's utilization_memory_percent is used/total VRAM.

    So there is no memory-controller utilization to expose; the VRAM usage
    sensor derives the same figure from the byte counts.
    """
    sensor_entity = UnraidGPUVramUsageSensor(
        _coordinator([RTX_3070]), MagicMock(), 0, "RTX 3070"
    )
    assert RTX_3070.utilization_memory_percent == pytest.approx(
        RTX_3070.memory_used_bytes / RTX_3070.memory_total_bytes * 100
    )
    assert sensor_entity.native_value == round(RTX_3070.utilization_memory_percent, 2)


@pytest.mark.parametrize("gpus", [[], [INTEL_IGPU], [LEGACY_GPU]])
def test_vram_sensors_unknown_without_vram_data(gpus: list[GPUInfo]) -> None:
    """Missing GPU or no VRAM data (after setup) reads as unknown, not 0."""
    coordinator = _coordinator(gpus)
    index = gpus[0].index if gpus else 0
    for cls in (
        UnraidGPUVramUsedSensor,
        UnraidGPUVramTotalSensor,
        UnraidGPUVramUsageSensor,
    ):
        assert cls(coordinator, MagicMock(), index, "GPU").native_value is None


def test_vram_usage_unknown_without_used_bytes() -> None:
    """Usage is unknown when the agent sends a total but no used figure."""
    gpu = GPUInfo.model_validate({"index": 0, "memory_total_bytes": 8589934592})
    coordinator = _coordinator([gpu])
    assert (
        UnraidGPUVramUsedSensor(coordinator, MagicMock(), 0, "GPU").native_value is None
    )
    assert (
        UnraidGPUVramTotalSensor(coordinator, MagicMock(), 0, "GPU").native_value
        == 8589934592
    )
    assert (
        UnraidGPUVramUsageSensor(coordinator, MagicMock(), 0, "GPU").native_value
        is None
    )


def test_cleanup_keeps_vram_keys_for_every_present_gpu() -> None:
    """VRAM keys stay valid for each present GPU, so a transient 0 never deletes them."""
    keys = _build_valid_dynamic_entity_keys(UnraidData(gpu=[RTX_3070, INTEL_IGPU]))
    for index in (0, 1):
        assert {f"gpu_{index}_{suffix}" for suffix in VRAM_SUFFIXES} <= keys
    assert not any(k.startswith("gpu_2_") for k in keys)


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_gpu_keys_survive_cleanup_and_do_not_collide(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mock_async_unraid_client: MagicMock,
) -> None:
    """Every GPU entity key is in cleanup's valid set and is not a static key."""
    mock_async_unraid_client.list_gpus.return_value = [RTX_3070, INTEL_IGPU]
    entry = _entry(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    gpu_keys = {
        e.unique_id.removeprefix(f"{ENTRY_ID}_")
        for e in er.async_entries_for_config_entry(entity_registry, ENTRY_ID)
        if e.unique_id.startswith(f"{ENTRY_ID}_gpu_")
    }
    assert {f"gpu_0_{suffix}" for suffix in VRAM_SUFFIXES} <= gpu_keys
    valid = _build_valid_dynamic_entity_keys(entry.runtime_data.coordinator.data)
    assert gpu_keys <= valid
    assert not gpu_keys & _static_description_keys()
