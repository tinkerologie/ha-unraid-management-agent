"""Test USB sensor controller devices (the "sensor controllers as devices" option)."""

from __future__ import annotations

import hashlib
from unittest.mock import MagicMock

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util
from pytest_homeassistant.common import MockConfigEntry

from custom_components.unraid_management_agent import (
    async_remove_config_entry_device,
)
from custom_components.unraid_management_agent.api.models import (
    FanInfo,
    TemperatureInfo,
)
from custom_components.unraid_management_agent.cleanup import (
    STALE_REMOVAL_GRACE,
    async_cleanup_stale_entities,
)
from custom_components.unraid_management_agent.const import (
    CONF_ENABLE_FAN_CONTROL,
    CONF_ENABLE_HWMON_DEVICES,
    DOMAIN,
)
from custom_components.unraid_management_agent.entity import (
    build_hwmon_controller_device_info,
)
from custom_components.unraid_management_agent.hwmon import (
    hwmon_controller_names,
    hwmon_controller_of,
)

from .const import MOCK_CONFIG, MOCK_OPTIONS

ENTRY_ID = "01TESTENTRYID"
FAN = f"{ENTRY_ID}_fan_"
TEMP = f"{ENTRY_ID}_temperature_"
# Not real serial numbers
SERIAL_A = "00000-00001"
SERIAL_B = "00000-00002"
CONTROLLER_A = (DOMAIN, f"{ENTRY_ID}_hwmon_octo_00000_00001")
CONTROLLER_B = (DOMAIN, f"{ENTRY_ID}_hwmon_octo_00000_00002")
TAG_A = hashlib.sha256(CONTROLLER_A[1].encode()).hexdigest()[:4]
TAG_B = hashlib.sha256(CONTROLLER_B[1].encode()).hexdigest()[:4]


def _octo_fans(
    source: str, serial: str, *, labels: bool = True, prefix: str = "octo"
) -> list[FanInfo]:
    """Fans 1-8 of an Octo; channel 8 is a flow meter labelled in sensors.conf."""
    fans = []
    for channel in range(1, 9):
        label = f"Array Fan{channel}" if channel < 8 else "Coolant Flow (rpm)"
        fans.append(
            FanInfo(
                name=f"{prefix}_fan{channel}",
                rpm=2800 + channel if channel < 8 else 742,
                source=source,
                device_id=serial,
                label=label if labels else None,
            )
        )
    return fans


def _coolant(source: str, serial: str | None) -> TemperatureInfo:
    """Build a coolant temperature reading from a USB controller."""
    return TemperatureInfo(
        name=f"{source}_Coolant_Temp_temp1_input",
        value_celsius=35.8,
        sensor_type="other",
        source=source,
        device_id=serial,
    )


MOTHERBOARD_FAN = FanInfo(name="nct6798_fan1", rpm=700, source="nct6798-isa-0290")
CPU_TEMP = TemperatureInfo(
    name="coretemp-isa-0000_Package_id_0_temp1_input",
    value_celsius=45.0,
    sensor_type="cpu",
    source="coretemp-isa-0000",
)


def _entry(hass: HomeAssistant, *, controller_devices: bool) -> MockConfigEntry:
    """Create the config entry, with the controller devices option set."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Unraid (unraid-test)",
        data=MOCK_CONFIG,
        options={
            **MOCK_OPTIONS,
            CONF_ENABLE_FAN_CONTROL: True,
            CONF_ENABLE_HWMON_DEVICES: controller_devices,
        },
        entry_id=ENTRY_ID,
    )
    entry.add_to_hass(hass)
    return entry


def _register(
    registry: er.EntityRegistry, entry: MockConfigEntry, unique_id: str, entity_id: str
) -> None:
    """Pre-register a sensor entity in the entity registry."""
    registry.async_get_or_create(
        "sensor",
        DOMAIN,
        unique_id,
        config_entry=entry,
        suggested_object_id=entity_id.removeprefix("sensor."),
    )


async def _setup(
    hass: HomeAssistant,
    client: MagicMock,
    fans: list[FanInfo],
    temps: list[TemperatureInfo],
    *,
    controller_devices: bool = True,
) -> MockConfigEntry:
    """Set up the integration with a mocked client and coordinator data."""
    system = client.get_system_info.return_value
    system.fans = fans
    system.temperatures = temps
    entry = _entry(hass, controller_devices=controller_devices)
    # The entity IDs the user's automations reference.
    registry = er.async_get(hass)
    for unique_id, entity_id in (
        (f"{FAN}octo_00000_00001_fan8", "sensor.unraid_fan_octo_fan8"),
        (f"{FAN}octo_00000_00001_fan1", "sensor.unraid_fan_octo_fan1"),
        (f"{TEMP}octo_hid_00000_00001_temp1", "sensor.unraid_coolant_temp"),
    ):
        _register(registry, entry, unique_id, entity_id)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


def _server(hass: HomeAssistant) -> dr.DeviceEntry:
    """Return the server device of the config entry."""
    server = dr.async_get(hass).async_get_device_by_identifier(
        (DOMAIN, ENTRY_ID), ENTRY_ID
    )
    assert server is not None
    return server


def _controller(hass: HomeAssistant, identifier: tuple[str, str]) -> dr.DeviceEntry:
    """Return the child device of the server with the given identifier."""
    device = dr.async_get(hass).async_get_child_device_by_identifier(
        identifier, ENTRY_ID
    )
    assert device is not None
    return device


def _entity(hass: HomeAssistant, unique_id: str) -> er.RegistryEntry:
    """Return the registered sensor entity with the given unique ID."""
    registry = er.async_get(hass)
    entity_id = registry.async_get_entity_id("sensor", DOMAIN, unique_id)
    assert entity_id is not None, unique_id
    entity = registry.async_get(entity_id)
    assert entity is not None
    return entity


def _attrs(hass: HomeAssistant, entity_id: str) -> dict:
    """Return the state attributes of an entity."""
    state = hass.states.get(entity_id)
    assert state is not None
    return dict(state.attributes)


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_option_off_keeps_sensors_on_server_and_honours_flow_label(
    hass: HomeAssistant, mock_async_unraid_client: MagicMock
) -> None:
    """Off: no new device; a channel labelled as flow is still shown as flow."""
    await _setup(
        hass,
        mock_async_unraid_client,
        [*_octo_fans("octo-hid-3-13", SERIAL_A), MOTHERBOARD_FAN],
        [_coolant("octo-hid-3-13", SERIAL_A), CPU_TEMP],
        controller_devices=False,
    )
    server = _server(hass)
    assert _entity(hass, f"{FAN}octo_00000_00001_fan8").device_id == server.id
    assert _entity(hass, f"{TEMP}octo_hid_00000_00001_temp1").device_id == server.id
    assert (
        dr.async_get(hass).async_get_child_device_by_identifier(CONTROLLER_A, ENTRY_ID)
        is None
    )

    flow = _attrs(hass, "sensor.unraid_fan_octo_fan8")
    assert flow["friendly_name"] == "unraid-test Fan octo_fan8"
    assert flow["unit_of_measurement"] == "RPM"
    assert flow["icon"] == "mdi:waves-arrow-right"
    assert flow["label"] == "Coolant Flow (rpm)"
    assert flow["channel_type"] == "flow"
    assert hass.states.get("sensor.unraid_fan_octo_fan8").state == "742"

    fan1 = _attrs(hass, "sensor.unraid_fan_octo_fan1")
    assert fan1["label"] == "Array Fan1"
    assert "channel_type" not in fan1
    assert fan1["icon"] == "mdi:fan"


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_option_on_moves_controller_sensors_and_keeps_entity_ids(
    hass: HomeAssistant, mock_async_unraid_client: MagicMock
) -> None:
    """On: the Octo is a child device holding its fans and coolant temperature."""
    await _setup(
        hass,
        mock_async_unraid_client,
        [*_octo_fans("octo-hid-3-13", SERIAL_A), MOTHERBOARD_FAN],
        [_coolant("octo-hid-3-13", SERIAL_A), CPU_TEMP],
    )
    server = _server(hass)
    octo = _controller(hass, CONTROLLER_A)
    assert octo.name == "Octo (fan controller)"
    assert octo.parent_device_id == server.id

    for channel in range(1, 9):
        fan = _entity(hass, f"{FAN}octo_00000_00001_fan{channel}")
        assert fan.device_id == octo.id
    coolant = _entity(hass, f"{TEMP}octo_hid_00000_00001_temp1")
    assert coolant.device_id == octo.id
    # Entity IDs referenced by automations are unchanged.
    assert coolant.entity_id == "sensor.unraid_coolant_temp"
    assert _entity(hass, f"{FAN}octo_00000_00001_fan8").entity_id == (
        "sensor.unraid_fan_octo_fan8"
    )
    # Other chips stay on the server.
    assert _entity(hass, f"{FAN}nct6798_fan1").device_id == server.id

    flow = _attrs(hass, "sensor.unraid_fan_octo_fan8")
    assert flow["friendly_name"] == "Octo (fan controller) Coolant Flow (rpm)"
    assert flow["channel_type"] == "flow"
    assert flow["unit_of_measurement"] == "RPM"
    assert hass.states.get("sensor.unraid_fan_octo_fan8").state == "742"
    assert _attrs(hass, "sensor.unraid_fan_octo_fan1")["friendly_name"] == (
        "Octo (fan controller) Array Fan1"
    )
    temp = _attrs(hass, "sensor.unraid_coolant_temp")
    assert temp["friendly_name"] == "Octo (fan controller) Coolant Temp"
    assert hass.states.get("sensor.unraid_coolant_temp").state == "35.8"


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_unlabelled_channels_are_named_by_number(
    hass: HomeAssistant, mock_async_unraid_client: MagicMock
) -> None:
    """Without labels (an older agent) the channels are "Fan 1".."Fan 8"."""
    await _setup(
        hass,
        mock_async_unraid_client,
        _octo_fans("octo-hid-3-13", SERIAL_A, labels=False),
        [],
    )
    fan8 = _attrs(hass, "sensor.unraid_fan_octo_fan8")
    assert fan8["friendly_name"] == "Octo (fan controller) Fan 8"
    assert "channel_type" not in fan8


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_two_controllers_are_told_apart(
    hass: HomeAssistant, mock_async_unraid_client: MagicMock
) -> None:
    """Two Octos get separate devices with stable tags, never the serial."""
    entry = await _setup(
        hass,
        mock_async_unraid_client,
        [
            *_octo_fans("octo-hid-3-13", SERIAL_A, prefix=f"octo-{SERIAL_A}"),
            *_octo_fans("octo-hid-3-14", SERIAL_B, prefix=f"octo-{SERIAL_B}"),
        ],
        [_coolant("octo-hid-3-13", SERIAL_A), _coolant("octo-hid-3-14", SERIAL_B)],
    )
    first = _controller(hass, CONTROLLER_A)
    second = _controller(hass, CONTROLLER_B)
    assert first.name == f"Octo {TAG_A} (fan controller)"
    assert second.name == f"Octo {TAG_B} (fan controller)"
    assert "00000" not in first.name
    assert _entity(hass, f"{FAN}octo_00000_00002_fan8").device_id == second.id
    assert _entity(hass, f"{TEMP}octo_hid_00000_00002_temp1").device_id == second.id

    # The second Octo is unplugged and the entry reloads: the first keeps its
    # name, since the second is still known as a device.
    system = mock_async_unraid_client.get_system_info.return_value
    system.fans = _octo_fans("octo-hid-3-13", SERIAL_A, prefix=f"octo-{SERIAL_A}")
    system.temperatures = [_coolant("octo-hid-3-13", SERIAL_A)]
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert _controller(hass, CONTROLLER_A).name == f"Octo {TAG_A} (fan controller)"


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_older_agent_without_device_ids_stays_on_server(
    hass: HomeAssistant, mock_async_unraid_client: MagicMock
) -> None:
    """Readings without a device_id have no stable controller: no device."""
    await _setup(
        hass,
        mock_async_unraid_client,
        [FanInfo(name="octo_fan1", rpm=900, source="octo-hid-3-13")],
        [_coolant("octo-hid-3-13", None)],
    )
    server = _server(hass)
    assert _entity(hass, f"{FAN}octo_fan1").device_id == server.id
    assert _entity(hass, f"{TEMP}octo_hid_temp1").device_id == server.id


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_turning_option_off_moves_sensors_back(
    hass: HomeAssistant, mock_async_unraid_client: MagicMock
) -> None:
    """On -> off: same entity IDs back on the server; the empty device goes."""
    entry = await _setup(
        hass,
        mock_async_unraid_client,
        _octo_fans("octo-hid-3-13", SERIAL_A),
        [_coolant("octo-hid-3-13", SERIAL_A)],
    )
    assert _controller(hass, CONTROLLER_A)

    hass.config_entries.async_update_entry(
        entry, options={**entry.options, CONF_ENABLE_HWMON_DEVICES: False}
    )
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()

    server = _server(hass)
    fan8 = _entity(hass, f"{FAN}octo_00000_00001_fan8")
    assert fan8.entity_id == "sensor.unraid_fan_octo_fan8"
    assert fan8.device_id == server.id
    coolant = _entity(hass, f"{TEMP}octo_hid_00000_00001_temp1")
    assert coolant.entity_id == "sensor.unraid_coolant_temp"
    assert coolant.device_id == server.id

    async_cleanup_stale_entities(hass, entry, entry.runtime_data.coordinator)
    assert (
        dr.async_get(hass).async_get_child_device_by_identifier(CONTROLLER_A, ENTRY_ID)
        is None
    )


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_remove_controller_device_only_when_gone(
    hass: HomeAssistant, mock_async_unraid_client: MagicMock
) -> None:
    """A controller device can be deleted once the agent no longer reports it."""
    entry = await _setup(
        hass,
        mock_async_unraid_client,
        _octo_fans("octo-hid-3-13", SERIAL_A),
        [_coolant("octo-hid-3-13", SERIAL_A)],
    )
    device = _controller(hass, CONTROLLER_A)
    coordinator = entry.runtime_data.coordinator
    assert await async_remove_config_entry_device(hass, entry, device) is False

    system = coordinator.data.system
    coordinator.data.system = None
    assert await async_remove_config_entry_device(hass, entry, device) is False
    coordinator.data.system = system

    # Without a complete inventory the controller may still be there.
    system.fans = None
    system.temperatures = [CPU_TEMP]
    assert await async_remove_config_entry_device(hass, entry, device) is False
    system.fans = [MOTHERBOARD_FAN]
    system.temperatures = None
    assert await async_remove_config_entry_device(hass, entry, device) is False
    # A USB HID chip reported without a device_id (agent downgrade).
    system.temperatures = [_coolant("octo-hid-3-13", None)]
    assert await async_remove_config_entry_device(hass, entry, device) is False
    system.temperatures = [CPU_TEMP]
    system.fans = [FanInfo(name="octo_fan1", rpm=1, source="octo-hid-3-13")]
    assert await async_remove_config_entry_device(hass, entry, device) is False

    system.fans = [MOTHERBOARD_FAN]
    assert await async_remove_config_entry_device(hass, entry, device) is True


async def test_controller_device_info_falls_back_to_server(
    hass: HomeAssistant,
) -> None:
    """Without a registered server device the entity stays on the server."""
    entry = _entry(hass, controller_devices=True)
    coordinator = MagicMock()
    coordinator.hass = hass
    coordinator.config_entry = entry
    info = build_hwmon_controller_device_info(coordinator, "octo", SERIAL_A, "Octo")
    assert info == {"identifiers": {(DOMAIN, ENTRY_ID)}}


def test_controller_helpers() -> None:
    """Controller identity and names."""
    assert hwmon_controller_of(MOTHERBOARD_FAN) is None
    assert hwmon_controller_of(CPU_TEMP) is None
    assert hwmon_controller_of({"name": "x"}) is None
    assert hwmon_controller_of(_coolant("octo-hid-3-13", SERIAL_A)) == (
        "octo",
        SERIAL_A,
    )
    unknown = FanInfo(
        name="widget_fan1", rpm=1, source="widget-hid-3-9", device_id="usb-3-9"
    )
    assert hwmon_controller_names(ENTRY_ID, [unknown], []) == {
        ("widget", "usb-3-9"): "widget (sensors)"
    }
    # Another Octo known only from the registry tags this one too.
    octo = _coolant("octo-hid-3-13", SERIAL_A)
    assert hwmon_controller_names(ENTRY_ID, [], [octo]) == {
        ("octo", SERIAL_A): "Octo (fan controller)"
    }
    assert hwmon_controller_names(ENTRY_ID, [], [octo], {CONTROLLER_B[1]}) == {
        ("octo", SERIAL_A): f"Octo {TAG_A} (fan controller)"
    }
    assert FanInfo(name="octo_fan8", label="Coolant FLOW").is_flow
    assert not FanInfo(name="octo_fan1", label="Array Fan1").is_flow
    assert not FanInfo(name="octo_fan1").is_flow


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_partial_inventory_never_removes_controller(
    hass: HomeAssistant, mock_async_unraid_client: MagicMock
) -> None:
    """Missing lists or device IDs (agent downgrade) keep the controller's sensors."""
    entry = await _setup(
        hass,
        mock_async_unraid_client,
        [*_octo_fans("octo-hid-3-13", SERIAL_A), MOTHERBOARD_FAN],
        [_coolant("octo-hid-3-13", SERIAL_A), CPU_TEMP],
    )
    coordinator = entry.runtime_data.coordinator
    system = coordinator.data.system
    long_ago = dt_util.utcnow() - STALE_REMOVAL_GRACE * 2

    def cleanup_past_grace() -> None:
        """Run stale cleanup with every candidate past its grace period."""
        async_cleanup_stale_entities(hass, entry, coordinator)
        for unique_id in list(coordinator.stale_entity_candidates):
            coordinator.stale_entity_candidates[unique_id] = long_ago
        async_cleanup_stale_entities(hass, entry, coordinator)

    # Lists missing from the agent's response.
    system.fans = None
    system.temperatures = None
    cleanup_past_grace()
    # An older agent: the same Octo without a device_id.
    system.fans = [FanInfo(name="octo_fan8", rpm=742, source="octo-hid-3-13")]
    system.temperatures = [_coolant("octo-hid-3-13", None)]
    cleanup_past_grace()

    assert _entity(hass, f"{FAN}octo_00000_00001_fan8").entity_id == (
        "sensor.unraid_fan_octo_fan8"
    )
    assert _entity(hass, f"{TEMP}octo_hid_00000_00001_temp1").entity_id == (
        "sensor.unraid_coolant_temp"
    )
    assert _controller(hass, CONTROLLER_A)

    # The Octo really is gone (complete inventory without it): removed.
    system.fans = [MOTHERBOARD_FAN]
    system.temperatures = [CPU_TEMP]
    coordinator.data.fan_control = MagicMock(fans=[])
    cleanup_past_grace()
    registry = er.async_get(hass)
    assert (
        registry.async_get_entity_id("sensor", DOMAIN, f"{FAN}octo_00000_00001_fan8")
        is None
    )
    assert (
        dr.async_get(hass).async_get_child_device_by_identifier(CONTROLLER_A, ENTRY_ID)
        is None
    )
