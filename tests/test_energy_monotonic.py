"""Computed energy totals never go backwards (issue #260)."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.unraid_management_agent.sensor import (
    UnraidEnergySensorExtraStoredData,
    UnraidGPUEnergySensor,
    UnraidGPUEnergySensorExtraStoredData,
    UnraidUPSEnergySensor,
)

UTCNOW = "custom_components.unraid_management_agent.sensor.dt_util.utcnow"
WATTS = 3600.0  # 1 kWh per 1000 s, so 100 s adds 0.1 kWh


def _coordinator() -> MagicMock:
    coordinator = MagicMock()
    coordinator.data.ups.power_watts = WATTS
    gpu = MagicMock(index=0, power_draw_watts=WATTS)
    coordinator.data.gpu = [gpu]
    coordinator.config_entry.entry_id = "test_entry"
    coordinator.config_entry.options = {}
    return coordinator


def _ups() -> UnraidUPSEnergySensor:
    return UnraidUPSEnergySensor(_coordinator(), MagicMock(entry_id="test_entry"))


def _gpu() -> UnraidGPUEnergySensor:
    return UnraidGPUEnergySensor(
        _coordinator(), MagicMock(entry_id="test_entry"), 0, "GPU"
    )


def _sample(sensor: Any, timestamp: float, uptime: int | None) -> None:
    sensor.coordinator.data.system.uptime_seconds = uptime
    with patch(
        UTCNOW, return_value=MagicMock(timestamp=MagicMock(return_value=timestamp))
    ):
        sensor._update_energy()


@pytest.mark.parametrize("make_sensor", [_ups, _gpu])
def test_stale_uptime_keeps_accumulating(make_sensor: Any) -> None:
    """Alternating fresh and stale uptime neither rewinds nor stalls the total."""
    sensor = make_sensor()
    sensor._total_energy = 427.0
    # A slow poll publishes the older snapshot after each WebSocket event
    uptimes = [1000, 1100, 1090, 1200, 1190, 1300, None, 1290, 1400]
    for step, uptime in enumerate(uptimes):
        _sample(sensor, 100.0 * step, uptime)

    assert sensor.native_value == pytest.approx(427.8)
    assert sensor._last_uptime_seconds == 1400


@pytest.mark.parametrize("make_sensor", [_ups, _gpu])
def test_reboot_keeps_total_and_skips_the_gap(make_sensor: Any) -> None:
    """A real reboot keeps the total and adds nothing for the time it was down."""
    sensor = make_sensor()
    sensor._total_energy = 427.0
    _sample(sensor, 0.0, 5000)
    _sample(sensor, 100.0, 5100)
    assert sensor.native_value == pytest.approx(427.1)

    _sample(sensor, 200.0, 30)
    assert sensor.native_value == pytest.approx(427.1)
    assert sensor._last_uptime_seconds == 30

    _sample(sensor, 300.0, 130)
    assert sensor.native_value == pytest.approx(427.2)


@pytest.mark.parametrize(
    ("state", "extra", "expected"),
    [
        ("1.0", 5.0, 5.0),
        ("5.0", 1.0, 5.0),
        ("unknown", 5.0, 5.0),
        ("unavailable", 5.0, 5.0),
        ("nan", 5.0, 5.0),
        ("inf", 5.0, 5.0),
        ("5.0", "nan", 5.0),
        ("unknown", None, 0.0),
    ],
)
@pytest.mark.parametrize(
    ("make_sensor", "make_extra"),
    [
        (_ups, UnraidEnergySensorExtraStoredData),
        (
            _gpu,
            lambda *args: UnraidGPUEnergySensorExtraStoredData(*args, gpu_key=None),
        ),
    ],
)
async def test_restore_keeps_the_larger_valid_total(
    make_sensor: Any, make_extra: Any, state: str, extra: Any, expected: float
) -> None:
    """A reload restores the larger valid total of the state and extra data."""
    sensor = make_sensor()
    sensor.async_get_last_state = AsyncMock(return_value=MagicMock(state=state))
    sensor.async_get_last_extra_data = AsyncMock(
        return_value=make_extra(extra, "kWh", 100.0, 1000.0, 500)
    )

    await sensor._async_restore_energy_state()

    assert sensor._total_energy == expected
    assert sensor._last_uptime_seconds == 500


@pytest.mark.parametrize("make_sensor", [_ups, _gpu])
async def test_restore_finishes_before_the_coordinator_listener(
    make_sensor: Any,
) -> None:
    """No coordinator update can reach the sensor before its total is restored."""
    sensor = make_sensor()
    order: list[str] = []

    async def restore() -> None:
        order.append("restore")

    async def added(_self: Any) -> None:
        order.append("listener")

    sensor._async_restore_energy_state = restore
    with patch(
        "homeassistant.helpers.update_coordinator.BaseCoordinatorEntity.async_added_to_hass",
        added,
    ):
        await sensor.async_added_to_hass()

    assert order == ["restore", "listener"]


@pytest.mark.parametrize(
    "field", ["last_power_watts", "last_timestamp", "last_uptime_seconds"]
)
@pytest.mark.parametrize("value", ["nan", "inf", float("inf")])
def test_restore_data_rejects_non_finite_values(field: str, value: Any) -> None:
    """A non-finite baseline value invalidates the stored record."""
    stored = {
        "native_value": 1.0,
        "native_unit_of_measurement": "kWh",
        "last_power_watts": 100.0,
        "last_timestamp": 1000.0,
        "last_uptime_seconds": 500,
        field: value,
    }

    assert UnraidEnergySensorExtraStoredData.from_dict(stored) is None
