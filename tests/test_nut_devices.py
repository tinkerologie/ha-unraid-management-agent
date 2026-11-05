"""Test entities for NUT devices other than the primary UPS."""

from __future__ import annotations

from dataclasses import replace
from typing import Any
from unittest.mock import MagicMock

import pytest
from homeassistant.const import STATE_OFF, STATE_ON, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant.common import MockConfigEntry

from custom_components.unraid_management_agent import UnraidDataUpdateCoordinator
from custom_components.unraid_management_agent.api.constants import EventType
from custom_components.unraid_management_agent.api.events import (
    WebSocketEvent,
    identify_event_type,
    parse_event,
)
from custom_components.unraid_management_agent.api.models import NUTInfo, UPSInfo
from custom_components.unraid_management_agent.cleanup import (
    _build_valid_dynamic_entity_keys,
    _unavailable_data_prefixes,
)
from custom_components.unraid_management_agent.const import DOMAIN
from custom_components.unraid_management_agent.coordinator import UnraidData
from custom_components.unraid_management_agent.diagnostics import (
    async_get_config_entry_diagnostics,
)
from custom_components.unraid_management_agent.nut import (
    async_move_legacy_nut_entities,
    find_nut_status,
    listed_secondary_nut_devices,
    nut_device_key,
    secondary_nut_device_names,
    secondary_nut_statuses,
)

from .const import MOCK_CONFIG, MOCK_OPTIONS, mock_collectors_status

# NUT device keys carry a hash of the exact device name
GPU = nut_device_key("ups-gpu")
UPS = nut_device_key("ups")
ATS = nut_device_key("ats")
ENTRY_ID = "test_entry_id"

# /api/v1/ups from an agent with multi-device support: the first NUT device,
# an APC Smart-UPS X 3000 that reports no load or power.
UPS_PAYLOAD = {
    "connected": True,
    "device_name": "ups",
    "status": "OL",
    "load_percent": None,
    "battery_charge_percent": 100,
    "runtime_left_seconds": 623,
    "power_watts": None,
    "nominal_power_watts": None,
    "model": "Smart-UPS X 3000",
}


def _ups_status(name: str, runtime: int, **extra: Any) -> dict[str, Any]:
    """Return a /nut status for a Smart-UPS X 3000 (no load or power)."""
    return {
        "connected": True,
        "device_name": name,
        "type": "ups",
        "status": "OL",
        "model": "Smart-UPS X 3000",
        "manufacturer": "American Power Conversion",
        "battery_charge_percent": 100,
        "battery_runtime_seconds": runtime,
        "load_percent": None,
        "realpower_watts": None,
        **extra,
    }


# The AP7752 ATS reports no battery, load, runtime or power at all.
ATS_STATUS = {
    "connected": True,
    "device_name": "ats",
    "type": "ats",
    "status": "OL",
    "model": "AP7752",
    "manufacturer": "APC",
    "battery_charge_percent": None,
    "battery_runtime_seconds": None,
    "load_percent": None,
    "realpower_watts": None,
    "output_frequency": 60,
}


def _nut(*statuses: dict[str, Any], devices: list[str] | None = None) -> NUTInfo:
    names = devices if devices is not None else [s["device_name"] for s in statuses]
    return NUTInfo.model_validate(
        {
            "installed": True,
            "running": True,
            "devices": [{"name": n, "available": True} for n in names],
            "status": statuses[0] if statuses else None,
            "statuses": list(statuses),
        }
    )


THREE_DEVICES = _nut(_ups_status("ups", 623), _ups_status("ups-gpu", 508), ATS_STATUS)


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
    hass: HomeAssistant, client: MagicMock, ups: UPSInfo | None, nut: NUTInfo | None
) -> MockConfigEntry:
    client.get_ups_info.return_value = ups
    client.get_nut_info.return_value = nut
    entry = _entry(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


def _nut_keys(entity_registry: er.EntityRegistry) -> set[str]:
    return {
        e.unique_id.removeprefix(f"{ENTRY_ID}_")
        for e in er.async_entries_for_config_entry(entity_registry, ENTRY_ID)
        if e.unique_id.startswith(f"{ENTRY_ID}_nut_")
    }


def _entity_id(entity_registry: er.EntityRegistry, platform: str, key: str) -> str:
    entity_id = entity_registry.async_get_entity_id(
        platform, DOMAIN, f"{ENTRY_ID}_{key}"
    )
    assert entity_id is not None, key
    return entity_id


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_entities_per_nut_device(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mock_async_unraid_client: MagicMock,
) -> None:
    """Each extra NUT device gets entities only for the readings it reports."""
    await _setup(
        hass,
        mock_async_unraid_client,
        UPSInfo.model_validate(UPS_PAYLOAD),
        THREE_DEVICES,
    )

    # The primary UPS keeps its ups_* entities; no nut_ups_* duplicates.
    assert _entity_id(entity_registry, "sensor", "ups_battery") == (
        "sensor.unraid_test_ups_battery"
    )
    assert _entity_id(entity_registry, "binary_sensor", "ups_connected") == (
        "binary_sensor.unraid_test_ups_connected"
    )
    # ups-gpu: battery and runtime only; the ATS: connected only.
    assert _nut_keys(entity_registry) == {
        f"{GPU}_battery",
        f"{GPU}_runtime",
        f"{GPU}_connected",
        f"{ATS}_connected",
    }

    battery = hass.states.get(_entity_id(entity_registry, "sensor", f"{GPU}_battery"))
    assert battery is not None
    assert battery.entity_id == "sensor.unraid_test_ups_ups_gpu_battery"
    assert battery.name == "unraid-test UPS ups-gpu Battery"
    assert float(battery.state) == 100
    assert battery.attributes["unit_of_measurement"] == "%"
    assert battery.attributes["device_class"] == "battery"
    assert battery.attributes["ups_status"] == "OL"
    assert battery.attributes["ups_model"] == "Smart-UPS X 3000"

    runtime = hass.states.get(_entity_id(entity_registry, "sensor", f"{GPU}_runtime"))
    assert runtime is not None
    assert float(runtime.state) == 8  # 508 s
    assert "ups_status" not in runtime.attributes

    ats = hass.states.get(
        _entity_id(entity_registry, "binary_sensor", f"{ATS}_connected")
    )
    assert ats is not None
    assert ats.entity_id == "binary_sensor.unraid_test_ups_ats_connected"
    assert ats.state == STATE_ON
    assert ats.attributes["device_type"] == "ats"
    assert ats.attributes["ups_model"] == "AP7752"

    # All on the server device, like the primary UPS entities.
    server = entity_registry.async_get(
        _entity_id(entity_registry, "sensor", "ups_battery")
    ).device_id
    for key in (f"{GPU}_battery", f"{ATS}_connected"):
        platform = "binary_sensor" if key.endswith("connected") else "sensor"
        entity = entity_registry.async_get(_entity_id(entity_registry, platform, key))
        assert entity is not None
        assert entity.device_id == server


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_readings_and_devices_that_appear_later(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mock_async_unraid_client: MagicMock,
) -> None:
    """New readings get entities on update; a silent device goes unavailable."""
    entry = await _setup(
        hass,
        mock_async_unraid_client,
        UPSInfo.model_validate(UPS_PAYLOAD),
        THREE_DEVICES,
    )
    coordinator = entry.runtime_data.coordinator

    # ups-gpu starts reporting load and power.
    coordinator.async_set_updated_data(
        replace(
            coordinator.data,
            nut=_nut(
                _ups_status("ups", 623),
                _ups_status("ups-gpu", 508, load_percent=21.0, realpower_watts=630.0),
                ATS_STATUS,
            ),
        )
    )
    await hass.async_block_till_done()

    assert {f"{GPU}_load", f"{GPU}_power", f"{GPU}_energy"} <= (
        _nut_keys(entity_registry)
    )
    power = hass.states.get(_entity_id(entity_registry, "sensor", f"{GPU}_power"))
    assert power is not None
    assert float(power.state) == 630
    energy = hass.states.get(_entity_id(entity_registry, "sensor", f"{GPU}_energy"))
    assert energy is not None
    assert energy.name == "unraid-test UPS ups-gpu Energy"
    assert float(energy.state) == 0

    # ups-gpu stops answering but is still listed; the ATS loses its status.
    coordinator.async_set_updated_data(
        replace(
            coordinator.data,
            nut=_nut(
                _ups_status("ups", 623),
                {**ATS_STATUS, "status": ""},
                devices=["ups", "ups-gpu", "ats"],
            ),
        )
    )
    await hass.async_block_till_done()

    for key in (f"{GPU}_battery", f"{GPU}_power", f"{GPU}_energy"):
        state = hass.states.get(_entity_id(entity_registry, "sensor", key))
        assert state is not None
        assert state.state == STATE_UNAVAILABLE, key
    ats = hass.states.get(
        _entity_id(entity_registry, "binary_sensor", f"{ATS}_connected")
    )
    assert ats is not None
    assert ats.state == STATE_OFF
    gpu_connected = hass.states.get(
        _entity_id(entity_registry, "binary_sensor", f"{GPU}_connected")
    )
    assert gpu_connected is not None
    assert gpu_connected.state == STATE_OFF
    assert gpu_connected.attributes.get("ups_status") is None


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_nut_device_energy_unknown_while_power_unknown(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mock_async_unraid_client: MagicMock,
) -> None:
    """The per-device energy sensor follows the same unknown rule as UPS Energy."""
    entry = await _setup(
        hass,
        mock_async_unraid_client,
        UPSInfo.model_validate(UPS_PAYLOAD),
        _nut(_ups_status("ups", 623), _ups_status("ups-gpu", 508, realpower_watts=500)),
    )
    coordinator = entry.runtime_data.coordinator
    coordinator.async_set_updated_data(
        replace(
            coordinator.data,
            nut=_nut(
                _ups_status("ups", 623),
                _ups_status("ups-gpu", 508, realpower_watts=-1),
            ),
        )
    )
    await hass.async_block_till_done()

    energy = hass.states.get(_entity_id(entity_registry, "sensor", f"{GPU}_energy"))
    assert energy is not None
    assert energy.state == STATE_UNKNOWN


_APCUPSD_UPS = UPSInfo.model_validate({**UPS_PAYLOAD, "device_name": None})
# (/ups, /nut, expected nut_* keys)
_SOURCE_CASES: dict[str, tuple[UPSInfo | None, NUTInfo | None, set[str]]] = {
    # Older agent: no statuses, so no extra entities.
    "old-agent": (
        _APCUPSD_UPS,
        NUTInfo.model_validate(
            {"installed": True, "running": True, "devices": [{"name": "ups"}]}
        ),
        set(),
    ),
    # /ups from apcupsd (no device name): every NUT device is extra.
    "apcupsd-primary": (
        _APCUPSD_UPS,
        _nut(_ups_status("ups", 623), ATS_STATUS),
        {
            f"{UPS}_battery",
            f"{UPS}_runtime",
            f"{UPS}_connected",
            f"{ATS}_connected",
        },
    ),
    # No /ups data: the first NUT device is taken as the primary.
    "no-ups-data": (
        None,
        _nut(_ups_status("ups", 623), ATS_STATUS),
        {f"{ATS}_connected"},
    ),
    # No /ups data and the first device did not answer: the first listed
    # device is still the primary, so ups-gpu keeps its entities and ups gets
    # none.
    "no-ups-data-first-silent": (
        None,
        _nut(
            _ups_status("ups-gpu", 508), ATS_STATUS, devices=["ups", "ups-gpu", "ats"]
        ),
        {
            f"{GPU}_battery",
            f"{GPU}_runtime",
            f"{GPU}_connected",
            f"{ATS}_connected",
        },
    ),
    # A listed device that never answered still gets a connected sensor.
    "listed-silent-device": (
        UPSInfo.model_validate(UPS_PAYLOAD),
        _nut(_ups_status("ups", 623), ATS_STATUS, devices=["ups", "ups-gpu", "ats"]),
        {f"{GPU}_connected", f"{ATS}_connected"},
    ),
    # Every device failed its query: listed devices are still connected-off.
    "no-statuses-answered": (
        UPSInfo.model_validate(UPS_PAYLOAD),
        _nut(devices=["ups", "ats"]),
        {f"{ATS}_connected"},
    ),
    # /nut fetch failed.
    "no-nut-data": (UPSInfo.model_validate(UPS_PAYLOAD), None, set()),
}


@pytest.mark.parametrize("case", list(_SOURCE_CASES))
@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_which_nut_devices_get_entities(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mock_async_unraid_client: MagicMock,
    case: str,
) -> None:
    """Only NUT devices not already covered by the ups_* entities are added."""
    ups, nut, expected = _SOURCE_CASES[case]
    await _setup(hass, mock_async_unraid_client, ups, nut)

    assert _nut_keys(entity_registry) == expected


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_first_device_added_once_apcupsd_ups_answers(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mock_async_unraid_client: MagicMock,
) -> None:
    """With /ups down at setup, the first NUT device waits for /ups (apcupsd)."""
    entry = await _setup(
        hass, mock_async_unraid_client, None, _nut(_ups_status("ups", 623), ATS_STATUS)
    )
    assert _nut_keys(entity_registry) == {f"{ATS}_connected"}

    coordinator = entry.runtime_data.coordinator
    coordinator.async_set_updated_data(replace(coordinator.data, ups=_APCUPSD_UPS))
    await hass.async_block_till_done()

    assert _nut_keys(entity_registry) == {
        f"{UPS}_battery",
        f"{UPS}_runtime",
        f"{UPS}_connected",
        f"{ATS}_connected",
    }


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_no_nut_entities_when_nut_collector_disabled(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mock_async_unraid_client: MagicMock,
) -> None:
    """The NUT collector being off means no per-device entities."""
    mock_async_unraid_client.get_collectors_status.return_value = (
        mock_collectors_status(all_enabled=False)
    )
    await _setup(
        hass,
        mock_async_unraid_client,
        UPSInfo.model_validate(UPS_PAYLOAD),
        THREE_DEVICES,
    )

    assert _nut_keys(entity_registry) == set()


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_removed_entity_is_recreated(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mock_async_unraid_client: MagicMock,
) -> None:
    """A NUT entity removed from the registry comes back on the next update (#83)."""
    entry = await _setup(
        hass,
        mock_async_unraid_client,
        UPSInfo.model_validate(UPS_PAYLOAD),
        THREE_DEVICES,
    )
    for platform, key in (
        ("sensor", f"{GPU}_battery"),
        ("binary_sensor", f"{ATS}_connected"),
    ):
        entity_registry.async_remove(_entity_id(entity_registry, platform, key))
    await hass.async_block_till_done()
    assert f"{GPU}_battery" not in _nut_keys(entity_registry)

    coordinator = entry.runtime_data.coordinator
    coordinator.async_set_updated_data(coordinator.data)
    await hass.async_block_till_done()

    assert {f"{GPU}_battery", f"{ATS}_connected"} <= _nut_keys(entity_registry)


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_silent_listed_device_is_disconnected(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mock_async_unraid_client: MagicMock,
) -> None:
    """A listed device that never answered shows as disconnected, not missing."""
    await _setup(
        hass,
        mock_async_unraid_client,
        UPSInfo.model_validate(UPS_PAYLOAD),
        _nut(_ups_status("ups", 623), devices=["ups", "ups-gpu"]),
    )

    state = hass.states.get(
        _entity_id(entity_registry, "binary_sensor", f"{GPU}_connected")
    )
    assert state is not None
    assert state.state == STATE_OFF
    assert listed_secondary_nut_devices(None) == []


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_secondaries_kept_while_ups_data_and_first_device_missing(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mock_async_unraid_client: MagicMock,
) -> None:
    """/ups failing while the first device is silent changes no NUT entity."""
    entry = await _setup(
        hass,
        mock_async_unraid_client,
        UPSInfo.model_validate(UPS_PAYLOAD),
        THREE_DEVICES,
    )
    coordinator = entry.runtime_data.coordinator
    before = _nut_keys(entity_registry)

    coordinator.async_set_updated_data(
        replace(
            coordinator.data,
            ups=None,
            nut=_nut(
                _ups_status("ups-gpu", 508),
                ATS_STATUS,
                devices=["ups", "ups-gpu", "ats"],
            ),
        )
    )
    await hass.async_block_till_done()

    assert _nut_keys(entity_registry) == before
    battery = hass.states.get(_entity_id(entity_registry, "sensor", f"{GPU}_battery"))
    assert battery is not None
    assert float(battery.state) == 100
    # Cleanup keeps every listed device while the primary is not certain.
    keys = _build_valid_dynamic_entity_keys(coordinator.data)
    assert {f"{GPU}_battery", f"{GPU}_connected", f"{ATS}_connected"} <= keys
    assert f"{UPS}_connected" in keys

    coordinator.async_set_updated_data(
        replace(
            coordinator.data, ups=UPSInfo.model_validate(UPS_PAYLOAD), nut=THREE_DEVICES
        )
    )
    await hass.async_block_till_done()

    assert _nut_keys(entity_registry) == before
    keys = _build_valid_dynamic_entity_keys(coordinator.data)
    assert f"{GPU}_battery" in keys
    assert not any(k.startswith(UPS) for k in keys)


def test_cleanup_keeps_listed_devices() -> None:
    """Valid keys cover every listed extra device, even one that missed a query."""
    data = UnraidData(
        ups=UPSInfo.model_validate(UPS_PAYLOAD),
        nut=_nut(_ups_status("ups", 623), devices=["ups", "ups-gpu", "ats"]),
    )

    keys = _build_valid_dynamic_entity_keys(data)

    assert {
        f"{GPU}_battery",
        f"{GPU}_energy",
        f"{GPU}_connected",
        f"{ATS}_connected",
    } <= keys
    assert not any(k.startswith(UPS) for k in keys)
    assert secondary_nut_device_names(data) == {"ups-gpu", "ats"}
    assert "nut_" not in _unavailable_data_prefixes(data)
    assert "nut_" in _unavailable_data_prefixes(UnraidData())
    assert secondary_nut_device_names(UnraidData()) == set()
    assert secondary_nut_statuses(None) == []
    assert find_nut_status(None, "ups") is None
    assert find_nut_status(UnraidData(), "ups") is None
    # An older agent's device list without /ups data: no device is known to be
    # covered, so every listed device keeps valid keys.
    listed_only = UnraidData(
        nut=NUTInfo.model_validate({"devices": [{"name": "ups"}, {"name": "ats"}]})
    )
    assert secondary_nut_device_names(listed_only) == {"ups", "ats"}
    # Statuses without a device list: the first status is the primary.
    statuses_only = UnraidData(
        nut=NUTInfo.model_validate({"statuses": [_ups_status("ups", 623), ATS_STATUS]})
    )
    assert listed_secondary_nut_devices(statuses_only) == ["ats"]
    no_devices = UnraidData(nut=NUTInfo.model_validate({"statuses": []}))
    assert listed_secondary_nut_devices(no_devices) == []


def test_nut_websocket_payload_is_classified() -> None:
    """The agent's /nut payload is a NUT event, never a UPS event, and vice versa."""
    payload = THREE_DEVICES.model_dump(mode="json")
    payload["statuses"][0]["battery_charge_percent"] = 100

    assert identify_event_type(payload) == EventType.NUT_STATUS_UPDATE
    assert identify_event_type({"installed": False, "running": False}) == (
        EventType.NUT_STATUS_UPDATE
    )
    assert identify_event_type(UPS_PAYLOAD) == EventType.UPS_STATUS_UPDATE

    event = parse_event(payload)
    assert isinstance(event.data, NUTInfo)
    assert event.data.statuses is not None
    assert [s.device_name for s in event.data.statuses] == ["ups", "ups-gpu", "ats"]
    assert event.data.statuses[2].runtime_minutes is None
    assert event.data.statuses[1].runtime_minutes == 8.5


async def test_nut_event_updates_nut_data(hass: HomeAssistant) -> None:
    """A nut_status_update event replaces data.nut and leaves data.ups alone."""
    entry = _entry(hass)
    coordinator = UnraidDataUpdateCoordinator(
        hass, entry=entry, client=MagicMock(), enable_websocket=True
    )
    ups = UPSInfo.model_validate(UPS_PAYLOAD)
    coordinator.data = UnraidData(ups=ups)

    coordinator._handle_websocket_event(
        parse_event(THREE_DEVICES.model_dump(mode="json"))
    )

    assert coordinator.data.ups is ups
    assert coordinator.data.nut == THREE_DEVICES


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_diagnostics_redact_nut_raw_variables(
    hass: HomeAssistant, mock_async_unraid_client: MagicMock
) -> None:
    """NUT raw variables (serials, SNMP addresses) are redacted in diagnostics."""
    ats = {
        **ATS_STATUS,
        "serial": "5A0000T00000",
        "raw_variables": {
            "device.serial": "5A0000T00000",
            "driver.parameter.port": "192.0.2.7",
        },
    }
    entry = await _setup(
        hass,
        mock_async_unraid_client,
        UPSInfo.model_validate(UPS_PAYLOAD),
        _nut(_ups_status("ups", 623), ats),
    )

    diagnostics = await async_get_config_entry_diagnostics(hass, entry)

    nut = diagnostics["coordinator_data"]["nut"]
    assert nut["statuses"][1]["device_name"] == "ats"
    assert nut["statuses"][1]["raw_variables"] == "**REDACTED**"
    assert nut["statuses"][1]["serial"] == "**REDACTED**"


def test_device_keys_do_not_collide() -> None:
    """Names that slugify alike get different keys, none equal to the old key."""
    keys = {nut_device_key(n) for n in ("ups", "UPS", "ups_gpu", "ups-gpu", "ups.gpu")}
    assert len(keys) == 5
    assert UPS.startswith("nut_ups-")
    assert GPU.startswith("nut_ups_gpu-")
    # Never the slug-only key of earlier versions
    assert nut_device_key("ups_gpu") != "nut_ups_gpu"


def _register_legacy(
    entity_registry: er.EntityRegistry,
    entry: MockConfigEntry,
    platform: str,
    unique_id: str,
    entity_id: str,
) -> None:
    entity_registry.async_get_or_create(
        platform,
        DOMAIN,
        unique_id,
        config_entry=entry,
        suggested_object_id=entity_id.split(".", 1)[1],
    )


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_slug_keyed_entities_move_to_the_new_key(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mock_async_unraid_client: MagicMock,
) -> None:
    """Entities keyed by the old slug-only key keep their entity IDs."""
    mock_async_unraid_client.get_ups_info.return_value = UPSInfo.model_validate(
        UPS_PAYLOAD
    )
    mock_async_unraid_client.get_nut_info.return_value = THREE_DEVICES
    entry = _entry(hass)
    _register_legacy(
        entity_registry,
        entry,
        "sensor",
        f"{ENTRY_ID}_nut_ups_gpu_battery",
        "sensor.gpu_ups_battery",
    )
    _register_legacy(
        entity_registry,
        entry,
        "binary_sensor",
        f"{ENTRY_ID}_nut_ups_gpu_connected",
        "binary_sensor.gpu_ups_connected",
    )
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    battery = entity_registry.async_get("sensor.gpu_ups_battery")
    connected = entity_registry.async_get("binary_sensor.gpu_ups_connected")
    assert battery is not None
    assert connected is not None
    assert battery.unique_id == f"{ENTRY_ID}_{GPU}_battery"
    assert connected.unique_id == f"{ENTRY_ID}_{GPU}_connected"
    state = hass.states.get("sensor.gpu_ups_battery")
    assert state is not None
    assert state.state == "100.0"


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_slug_keyed_entity_of_silent_device_is_moved(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mock_async_unraid_client: MagicMock,
) -> None:
    """An old entity moves even while its device is silent, so cleanup keeps it."""
    mock_async_unraid_client.get_ups_info.return_value = UPSInfo.model_validate(
        UPS_PAYLOAD
    )
    mock_async_unraid_client.get_nut_info.return_value = _nut(
        _ups_status("ups", 623), ATS_STATUS, devices=["ups", "ups-gpu", "ats"]
    )
    entry = _entry(hass)
    _register_legacy(
        entity_registry,
        entry,
        "sensor",
        f"{ENTRY_ID}_nut_ups_gpu_battery",
        "sensor.gpu_ups_battery",
    )
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    battery = entity_registry.async_get("sensor.gpu_ups_battery")
    assert battery is not None
    assert battery.unique_id == f"{ENTRY_ID}_{GPU}_battery"
    coordinator = entry.runtime_data.coordinator
    assert f"{GPU}_battery" in _build_valid_dynamic_entity_keys(coordinator.data)

    # ups-gpu answers again: its battery sensor keeps the old entity ID.
    coordinator.async_set_updated_data(replace(coordinator.data, nut=THREE_DEVICES))
    await hass.async_block_till_done()

    state = hass.states.get("sensor.gpu_ups_battery")
    assert state is not None
    assert state.state == "100.0"


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_slug_keyed_entity_of_first_device_moved_while_ups_missing(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mock_async_unraid_client: MagicMock,
) -> None:
    """With apcupsd /ups down at setup, the first device's old entities move too."""
    mock_async_unraid_client.get_ups_info.return_value = None
    mock_async_unraid_client.get_nut_info.return_value = _nut(
        _ups_status("ups", 623), ATS_STATUS
    )
    entry = _entry(hass)
    for platform, suffix, entity_id in (
        ("sensor", "battery", "sensor.first_ups_battery"),
        ("binary_sensor", "connected", "binary_sensor.first_ups_connected"),
    ):
        _register_legacy(
            entity_registry, entry, platform, f"{ENTRY_ID}_nut_ups_{suffix}", entity_id
        )
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    # Moved but not created yet: ups is taken as the primary without /ups.
    battery = entity_registry.async_get("sensor.first_ups_battery")
    assert battery is not None
    assert battery.unique_id == f"{ENTRY_ID}_{UPS}_battery"
    assert hass.states.get("sensor.first_ups_battery") is None
    coordinator = entry.runtime_data.coordinator
    keys = _build_valid_dynamic_entity_keys(coordinator.data)
    assert {f"{UPS}_battery", f"{UPS}_connected"} <= keys

    # /ups answers from apcupsd: the entities come back with their entity IDs.
    coordinator.async_set_updated_data(replace(coordinator.data, ups=_APCUPSD_UPS))
    await hass.async_block_till_done()

    state = hass.states.get("sensor.first_ups_battery")
    assert state is not None
    assert state.state == "100.0"
    connected = hass.states.get("binary_sensor.first_ups_connected")
    assert connected is not None
    assert connected.state == STATE_ON
    async_move_legacy_nut_entities(hass, ENTRY_ID, None)


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_ambiguous_slug_keyed_entity_is_not_moved(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mock_async_unraid_client: MagicMock,
) -> None:
    """With "ups-gpu" and "ups_gpu" both present, neither takes the old entity."""
    mock_async_unraid_client.get_ups_info.return_value = UPSInfo.model_validate(
        UPS_PAYLOAD
    )
    mock_async_unraid_client.get_nut_info.return_value = _nut(
        _ups_status("ups", 623),
        _ups_status("ups-gpu", 508),
        _ups_status("ups_gpu", 400),
    )
    entry = _entry(hass)
    _register_legacy(
        entity_registry,
        entry,
        "sensor",
        f"{ENTRY_ID}_nut_ups_gpu_battery",
        "sensor.old_battery",
    )
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    old = entity_registry.async_get("sensor.old_battery")
    assert old is not None
    assert old.unique_id == f"{ENTRY_ID}_nut_ups_gpu_battery"
    assert {
        f"{GPU}_battery",
        f"{nut_device_key('ups_gpu')}_battery",
        "nut_ups_gpu_battery",
    } <= _nut_keys(entity_registry)


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_partial_nut_event_keeps_device_lists(
    hass: HomeAssistant,
    mock_async_unraid_client: MagicMock,
) -> None:
    """A nut_status_update without statuses or devices keeps the known ones."""
    entry = await _setup(
        hass,
        mock_async_unraid_client,
        UPSInfo.model_validate(UPS_PAYLOAD),
        THREE_DEVICES,
    )
    coordinator: UnraidDataUpdateCoordinator = entry.runtime_data.coordinator
    partial = NUTInfo.model_validate({"installed": True, "running": True})
    coordinator._handle_websocket_event(
        WebSocketEvent(event_type=EventType.NUT_STATUS_UPDATE, data=partial)
    )
    assert coordinator.data.nut is not None
    assert coordinator.data.nut.statuses == THREE_DEVICES.statuses
    assert coordinator.data.nut.devices == THREE_DEVICES.devices

    # A full event still replaces the lists
    single = _nut(_ups_status("ups", 600))
    coordinator._handle_websocket_event(
        WebSocketEvent(event_type=EventType.NUT_STATUS_UPDATE, data=single)
    )
    assert coordinator.data.nut.statuses == single.statuses


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_primary_device_counts_for_legacy_ambiguity(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mock_async_unraid_client: MagicMock,
) -> None:
    """A secondary "ups_gpu" does not take an old entity when the primary is "ups-gpu"."""
    mock_async_unraid_client.get_ups_info.return_value = UPSInfo.model_validate(
        {**UPS_PAYLOAD, "device_name": "ups-gpu"}
    )
    mock_async_unraid_client.get_nut_info.return_value = _nut(
        _ups_status("ups-gpu", 623), _ups_status("ups_gpu", 400)
    )
    entry = _entry(hass)
    _register_legacy(
        entity_registry,
        entry,
        "sensor",
        f"{ENTRY_ID}_nut_ups_gpu_battery",
        "sensor.old_battery",
    )
    _register_legacy(
        entity_registry,
        entry,
        "binary_sensor",
        f"{ENTRY_ID}_nut_ups_gpu_connected",
        "binary_sensor.old_connected",
    )
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    for entity_id, key in (
        ("sensor.old_battery", "nut_ups_gpu_battery"),
        ("binary_sensor.old_connected", "nut_ups_gpu_connected"),
    ):
        entity = entity_registry.async_get(entity_id)
        assert entity is not None
        assert entity.unique_id == f"{ENTRY_ID}_{key}"
    assert f"{nut_device_key('ups_gpu')}_battery" in _nut_keys(entity_registry)
