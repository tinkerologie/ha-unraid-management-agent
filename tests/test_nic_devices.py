"""Tests for the network card devices and entities (opt-in)."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
from homeassistant.const import STATE_OFF, STATE_ON, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from pytest_homeassistant.common import MockConfigEntry
from pytest_homeassistant.test_util.aiohttp import (
    AiohttpClientMocker,
)

from custom_components.unraid_management_agent import (
    async_remove_config_entry_device,
)
from custom_components.unraid_management_agent.api import UnraidClient
from custom_components.unraid_management_agent.api.models import (
    CollectorDetails,
    CollectorStatus,
    NICList,
)
from custom_components.unraid_management_agent.cleanup import (
    async_cleanup_stale_entities,
)
from custom_components.unraid_management_agent.const import (
    CONF_ENABLE_NIC_DEVICES,
    DOMAIN,
)
from custom_components.unraid_management_agent.nic import (
    NICEntitySpec,
    build_nic_device_info,
    card_name,
    current_card_ids,
    nic_sensor_specs,
)
from custom_components.unraid_management_agent.sensor import UnraidNICSensor

from .const import MOCK_CONFIG, MOCK_OPTIONS

ENTRY_ID = "test_entry_id"
FIXTURE = Path(__file__).parent / "fixtures" / "network_cards.json"
CX6 = "nic_0000_41_00"
ETH0 = f"{CX6}_port_0000_41_00_0"
ETH1 = f"{CX6}_port_0000_41_00_1"
AQC = "nic_0000_d5_00"
ETH2 = f"{AQC}_port_0000_d5_00_0"


def _cards(mutate: Callable[[dict[str, Any]], None] | None = None) -> NICList:
    """Load the card list the agent reported on the test server."""
    data = json.loads(FIXTURE.read_text())
    if mutate:
        mutate(data)
    return NICList.model_validate(data)


def _card(data: dict[str, Any], card_id: str) -> dict[str, Any]:
    return next(c for c in data["cards"] if c["id"] == card_id)


def _entry(hass: HomeAssistant, *, enabled: bool) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Unraid (unraid-test)",
        data=MOCK_CONFIG,
        options={**MOCK_OPTIONS, CONF_ENABLE_NIC_DEVICES: enabled},
        entry_id=ENTRY_ID,
    )
    entry.add_to_hass(hass)
    return entry


@pytest.fixture
def mock_config_entry(hass: HomeAssistant) -> MockConfigEntry:
    """Config entry with network card devices turned on."""
    return _entry(hass, enabled=True)


@pytest.fixture
def nic_client(mock_async_unraid_client: MagicMock) -> MagicMock:
    """Serve the captured card list."""
    mock_async_unraid_client.get_network_cards.return_value = _cards()
    return mock_async_unraid_client


async def _setup(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


async def _push(hass: HomeAssistant, entry: MockConfigEntry, cards: Any) -> None:
    """Deliver a new card list through the coordinator."""
    coordinator = entry.runtime_data.coordinator
    coordinator.data.network_cards = cards
    coordinator.async_set_updated_data(coordinator.data)
    await hass.async_block_till_done()


def _nic_entities(hass: HomeAssistant) -> list[er.RegistryEntry]:
    return [
        e
        for e in er.async_entries_for_config_entry(er.async_get(hass), ENTRY_ID)
        if e.unique_id.startswith(f"{ENTRY_ID}_nic_")
    ]


def _nic_devices(hass: HomeAssistant) -> list[Any]:
    return [
        d
        for d in dr.async_child_entries_for_config_entry(dr.async_get(hass), ENTRY_ID)
        if any(i[1].startswith(f"{ENTRY_ID}_nic_") for i in d.identifiers)
    ]


def _entity_id(hass: HomeAssistant, platform: str, key: str) -> str:
    entity_id = er.async_get(hass).async_get_entity_id(
        platform, DOMAIN, f"{ENTRY_ID}_{key}"
    )
    assert entity_id is not None, key
    return entity_id


def _state(hass: HomeAssistant, platform: str, key: str) -> Any:
    state = hass.states.get(_entity_id(hass, platform, key))
    assert state is not None, key
    return state


@pytest.mark.usefixtures("nic_client", "mock_unraid_websocket_client_class")
async def test_cards_are_children_of_the_server(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """Each card is a child device named after its model and slot."""
    await _setup(hass, mock_config_entry)

    devices = dr.async_get(hass)
    server = devices.async_get_device_by_identifier((DOMAIN, ENTRY_ID), ENTRY_ID)
    assert server is not None
    names = {}
    for card_id in ("0000:41:00", "0000:d5:00", "0000:d6:00"):
        device = devices.async_get_child_device_by_identifier(
            (DOMAIN, f"{ENTRY_ID}_nic_{card_id}"), ENTRY_ID
        )
        assert device is not None
        assert device.parent_device_id == server.id
        names[card_id] = device.name
    assert names == {
        "0000:41:00": "ConnectX-6 Dx (41:00)",
        "0000:d5:00": "AQC113CS (d5:00)",
        "0000:d6:00": "AQC113CS (d6:00)",
    }

    keys = sorted(e.unique_id.removeprefix(f"{ENTRY_ID}_") for e in _nic_entities(hass))
    per_optic = [
        "link_speed",
        "module_part_number",
        "module_problem",
        "module_temperature",
        "module_vendor",
        "module_voltage",
        "rx_power",
        "tx_power",
    ]
    expected = [
        f"{CX6}_asic_temperature",
        f"{CX6}_firmware",
        *(f"{ETH0}_{k}" for k in per_optic),
        *(f"{ETH1}_{k}" for k in per_optic),
    ]
    for card, func in (("0000_d5_00", "0000_d5_00_0"), ("0000_d6_00", "0000_d6_00_0")):
        expected += [
            f"nic_{card}_firmware",
            f"nic_{card}_port_{func}_link_speed",
            f"nic_{card}_port_{func}_phy_temperature_temperature",
            f"nic_{card}_port_{func}_mac_temperature_temperature",
        ]
    assert keys == sorted(expected)


@pytest.mark.usefixtures("nic_client", "mock_unraid_websocket_client_class")
async def test_card_and_port_entities(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """Temperatures, link speed and optic diagnostics carry the agent's values."""
    await _setup(hass, mock_config_entry)

    asic = _state(hass, "sensor", f"{CX6}_asic_temperature")
    assert float(asic.state) == 89
    assert asic.attributes["critical"] == 105
    assert asic.attributes["highest"] == 90
    assert asic.name == "ConnectX-6 Dx (41:00) ASIC Temperature"

    firmware = _state(hass, "sensor", f"{CX6}_firmware")
    assert firmware.state == "22.47.3576 (MT_0000000359)"
    assert firmware.attributes["driver"] == "mlx5_core"
    assert firmware.attributes["pci_id"] == "15b3:101d"

    speed = _state(hass, "sensor", f"{ETH0}_link_speed")
    assert float(speed.state) == 100000
    assert speed.attributes["master"] == "bond0"
    assert speed.name == "ConnectX-6 Dx (41:00) eth0 Link Speed"

    assert float(_state(hass, "sensor", f"{ETH0}_module_temperature").state) == 51.01
    voltage = _state(hass, "sensor", f"{ETH0}_module_voltage")
    assert float(voltage.state) == 3.2676
    assert voltage.attributes["thresholds"]["high_alarm"] == 3.62

    rx = _state(hass, "sensor", f"{ETH0}_rx_power")
    assert float(rx.state) == 3.19  # worst of 3.66, 3.81, 3.88, 3.19
    assert [lane["dbm"] for lane in rx.attributes["lanes"]] == [3.66, 3.81, 3.88, 3.19]
    assert rx.attributes["measurement"] == "average"
    assert rx.attributes["thresholds"]["low_alarm"] == -13.01
    assert rx.name == "ConnectX-6 Dx (41:00) eth0 RX Power"

    tx = _state(hass, "sensor", f"{ETH0}_tx_power")
    lanes = tx.attributes["lanes"]
    assert float(tx.state) == min(lane["dbm"] for lane in lanes)
    assert all(lane["bias_ma"] > 0 for lane in lanes)
    assert tx.attributes["bias_thresholds"]["high_alarm"] == 14

    problem = _state(hass, "binary_sensor", f"{ETH0}_module_problem")
    assert problem.state == STATE_OFF
    assert problem.attributes["alarms"] == []
    assert problem.name == "ConnectX-6 Dx (41:00) eth0 Optic"

    vendor = _state(hass, "sensor", f"{ETH0}_module_vendor")
    assert vendor.state == "CISCO-PROLINE"
    assert vendor.attributes["identifier"] == "QSFP28"
    assert vendor.attributes["wavelength_nm"] == 850
    assert _state(hass, "sensor", f"{ETH0}_module_part_number").state == (
        "QSFP-100G-AOC-3M"
    )

    phy = _state(hass, "sensor", f"{ETH2}_phy_temperature_temperature")
    assert float(phy.state) == 42
    assert phy.name == "AQC113CS (d5:00) PHY Temperature"
    assert phy.attributes["interface"] == "eth2"
    eth2_speed = _state(hass, "sensor", f"{ETH2}_link_speed")
    assert eth2_speed.state == STATE_UNKNOWN
    assert eth2_speed.attributes["operstate"] == "down"


@pytest.mark.usefixtures("nic_client", "mock_unraid_websocket_client_class")
async def test_optic_flags_turn_the_problem_sensor_on(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """Any alarm or warning flag raises the optic problem sensor."""
    await _setup(hass, mock_config_entry)

    def flags(data: dict[str, Any]) -> None:
        module = _card(data, "0000:41:00")["ports"][0]["module"]
        module["warnings"] = ["lane4_rx_power_low"]
        module["lanes"][3]["rx_power_dbm"] = -9.5

    await _push(hass, mock_config_entry, _cards(flags))
    problem = _state(hass, "binary_sensor", f"{ETH0}_module_problem")
    assert problem.state == STATE_ON
    assert problem.attributes["warnings"] == ["lane4_rx_power_low"]
    assert float(_state(hass, "sensor", f"{ETH0}_rx_power").state) == -9.5

    def not_ready(data: dict[str, Any]) -> None:
        module = _card(data, "0000:41:00")["ports"][0]["module"]
        module.update(
            data_not_ready=True,
            temperature_celsius=None,
            voltage_volts=None,
            lanes=[],
            alarms=[],
            warnings=[],
        )

    # Invalid diagnostics do not clear the raised flag: the state is unknown.
    await _push(hass, mock_config_entry, _cards(not_ready))
    problem = _state(hass, "binary_sensor", f"{ETH0}_module_problem")
    assert problem.state == STATE_UNKNOWN
    assert problem.attributes["data_not_ready"] is True
    assert _state(hass, "sensor", f"{ETH0}_module_temperature").state == STATE_UNKNOWN
    # Without lane readings the power sensors have nothing to show.
    assert _state(hass, "sensor", f"{ETH0}_rx_power").state == STATE_UNAVAILABLE

    def decode_error(data: dict[str, Any]) -> None:
        module = _card(data, "0000:41:00")["ports"][0]["module"]
        module.update(error="invalid external calibration constants", alarms=[])

    await _push(hass, mock_config_entry, _cards(decode_error))
    problem = _state(hass, "binary_sensor", f"{ETH0}_module_problem")
    assert problem.state == STATE_UNKNOWN
    assert problem.attributes["error"] == "invalid external calibration constants"
    # Readings that came with a decode error are not shown either.
    for key in ("module_temperature", "module_voltage", "rx_power", "tx_power"):
        assert _state(hass, "sensor", f"{ETH0}_{key}").state == STATE_UNKNOWN, key

    # Valid diagnostics without flags: recovered.
    await _push(hass, mock_config_entry, _cards())
    assert _state(hass, "binary_sensor", f"{ETH0}_module_problem").state == STATE_OFF
    assert float(_state(hass, "sensor", f"{ETH0}_module_temperature").state) == 51.01


@pytest.mark.usefixtures("nic_client", "mock_unraid_websocket_client_class")
async def test_unplugged_optic_goes_unavailable_and_new_ones_appear(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """Removing an optic leaves the port; plugging one in adds its entities."""
    await _setup(hass, mock_config_entry)

    def unplug(data: dict[str, Any]) -> None:
        _card(data, "0000:41:00")["ports"][1].pop("module")

    await _push(hass, mock_config_entry, _cards(unplug))
    for key in ("module_vendor", "module_temperature", "rx_power", "tx_power"):
        assert _state(hass, "sensor", f"{ETH1}_{key}").state == STATE_UNAVAILABLE
    assert (
        _state(hass, "binary_sensor", f"{ETH1}_module_problem").state
        == STATE_UNAVAILABLE
    )
    assert float(_state(hass, "sensor", f"{ETH1}_link_speed").state) == 100000

    def plug_into_eth2(data: dict[str, Any]) -> None:
        module = _card(data, "0000:41:00")["ports"][0]["module"]
        _card(data, "0000:d5:00")["ports"][0]["module"] = {
            **module,
            "ddm_supported": False,
            "lanes": [],
        }

    await _push(hass, mock_config_entry, _cards(plug_into_eth2))
    assert _state(hass, "sensor", f"{ETH2}_module_vendor").state == "CISCO-PROLINE"
    registry = er.async_get(hass)
    for platform, key in (("sensor", "module_temperature"), ("sensor", "rx_power")):
        assert (
            registry.async_get_entity_id(platform, DOMAIN, f"{ENTRY_ID}_{ETH2}_{key}")
            is None
        )
    assert (
        registry.async_get_entity_id(
            "binary_sensor", DOMAIN, f"{ENTRY_ID}_{ETH2}_module_problem"
        )
        is None
    )


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_multi_port_sensors_name_their_port(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, nic_client: MagicMock
) -> None:
    """Per-port PHY/MAC sensors on multi-port cards carry the port name."""

    def dual_port(data: dict[str, Any]) -> None:
        card = _card(data, "0000:d5:00")
        port = dict(card["ports"][0])
        port.update(id="0000:d5:00.1", interface="eth9", pci_address="0000:d5:00.1")
        card["ports"].append(port)
        card["temperatures"] += [
            {
                "sensor": "phy",
                "label": "PHY Temperature",
                "interface": "eth9",
                "pci_address": "0000:d5:00.1",
                "celsius": 47,
            },
            {
                "sensor": "other",
                "label": "board",
                "pci_address": "0000:d5:00.1",
                "celsius": 39,
                "max_celsius": 95,
            },
            {"sensor": "other", "label": "ghost", "pci_address": "0000:d5:00.7"},
            {"sensor": "module", "label": "Module0", "pci_address": "0000:d5:00.0"},
        ]

    nic_client.get_network_cards.return_value = _cards(dual_port)
    await _setup(hass, mock_config_entry)

    port0 = _state(hass, "sensor", f"{ETH2}_phy_temperature_temperature")
    port1 = _state(
        hass, "sensor", f"{AQC}_port_0000_d5_00_1_phy_temperature_temperature"
    )
    assert port0.name == "AQC113CS (d5:00) eth2 PHY Temperature"
    assert port1.name == "AQC113CS (d5:00) eth9 PHY Temperature"
    assert float(port1.state) == 47
    board = _state(hass, "sensor", f"{AQC}_port_0000_d5_00_1_board_temperature")
    assert board.name == "AQC113CS (d5:00) eth9 board"
    assert board.attributes["max"] == 95
    # A sensor of a function without a port is named after its PCI address.
    ghost = _state(hass, "sensor", f"{AQC}_port_0000_d5_00_7_ghost_temperature")
    assert ghost.name == "AQC113CS (d5:00) 0000:d5:00.7 ghost"
    # Transceiver cage sensors are left out.
    assert not [e for e in _nic_entities(hass) if "module0" in e.unique_id]


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_option_off_fetches_and_creates_nothing(
    hass: HomeAssistant, mock_async_unraid_client: MagicMock
) -> None:
    """With the option off (default) the endpoint is not polled."""
    mock_async_unraid_client.get_network_cards.return_value = _cards()
    entry = _entry(hass, enabled=False)
    await _setup(hass, entry)

    mock_async_unraid_client.get_network_cards.assert_not_awaited()
    assert not _nic_entities(hass)
    assert not _nic_devices(hass)


@pytest.mark.usefixtures("nic_client", "mock_unraid_websocket_client_class")
async def test_turning_the_option_off_removes_devices(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """Turning the option off removes every network card device and entity."""
    await _setup(hass, mock_config_entry)
    assert _nic_entities(hass)
    assert len(_nic_devices(hass)) == 3

    hass.config_entries.async_update_entry(
        mock_config_entry,
        options={**MOCK_OPTIONS, CONF_ENABLE_NIC_DEVICES: False},
    )
    await hass.config_entries.async_reload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert not _nic_entities(hass)
    assert not _nic_devices(hass)
    server = dr.async_get(hass).async_get_device_by_identifier(
        (DOMAIN, ENTRY_ID), ENTRY_ID
    )
    assert server is not None


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_no_entities_without_the_endpoint(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_async_unraid_client: MagicMock,
) -> None:
    """An agent without /network/cards (404) yields no entities or errors."""
    mock_async_unraid_client.get_network_cards.side_effect = Exception("404")
    await _setup(hass, mock_config_entry)

    assert mock_async_unraid_client.get_network_cards.await_count >= 1
    assert not _nic_entities(hass)
    assert not _nic_devices(hass)


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_entities_appear_after_the_first_collection(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_async_unraid_client: MagicMock,
) -> None:
    """While the agent's list is pending there are no entities; then they appear."""
    mock_async_unraid_client.get_network_cards.return_value = NICList.model_validate(
        {"state": "pending"}
    )
    await _setup(hass, mock_config_entry)
    assert not _nic_entities(hass)

    await _push(hass, mock_config_entry, _cards())
    assert float(_state(hass, "sensor", f"{CX6}_asic_temperature").state) == 89


@pytest.mark.usefixtures("nic_client", "mock_unraid_websocket_client_class")
async def test_disabled_collector_makes_entities_unavailable(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """The agent keeps serving its last snapshot when the collector is disabled."""
    await _setup(hass, mock_config_entry)
    coordinator = mock_config_entry.runtime_data.coordinator
    coordinator.data.collectors = CollectorStatus(
        collectors=[CollectorDetails(name="nic", enabled=False)]
    )
    coordinator.async_set_updated_data(coordinator.data)
    await hass.async_block_till_done()

    state = _state(hass, "sensor", f"{CX6}_asic_temperature")
    assert state.state == STATE_UNAVAILABLE
    assert state.attributes.get("critical") is None
    # An unavailable entity has no attributes (HA does not ask; check directly).
    spec = next(s for s in nic_sensor_specs(_cards()) if s.key == f"{CX6}_firmware")
    assert UnraidNICSensor(coordinator, spec).extra_state_attributes is None


@pytest.mark.usefixtures("nic_client", "mock_unraid_websocket_client_class")
async def test_missing_card_is_unavailable_and_removable(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """A card that disappears goes unavailable, survives cleanup and can be deleted."""
    await _setup(hass, mock_config_entry)
    devices = dr.async_get(hass)
    cx6 = devices.async_get_child_device_by_identifier(
        (DOMAIN, f"{ENTRY_ID}_nic_0000:41:00"), ENTRY_ID
    )
    assert cx6 is not None
    assert not await async_remove_config_entry_device(hass, mock_config_entry, cx6)

    def drop(data: dict[str, Any]) -> None:
        data["cards"] = [c for c in data["cards"] if c["id"] != "0000:41:00"]

    await _push(hass, mock_config_entry, _cards(drop))
    assert _state(hass, "sensor", f"{CX6}_asic_temperature").state == STATE_UNAVAILABLE
    assert _state(hass, "sensor", f"{ETH0}_link_speed").state == STATE_UNAVAILABLE
    coordinator = mock_config_entry.runtime_data.coordinator
    async_cleanup_stale_entities(hass, mock_config_entry, coordinator)
    assert _entity_id(hass, "sensor", f"{CX6}_asic_temperature")

    assert await async_remove_config_entry_device(hass, mock_config_entry, cx6)
    aqc = devices.async_get_child_device_by_identifier(
        (DOMAIN, f"{ENTRY_ID}_nic_0000:d5:00"), ENTRY_ID
    )
    assert aqc is not None
    assert not await async_remove_config_entry_device(hass, mock_config_entry, aqc)

    # Unknown card state (fetch failed): nothing can be removed.
    await _push(hass, mock_config_entry, None)
    assert not await async_remove_config_entry_device(hass, mock_config_entry, cx6)


async def test_device_info_falls_back_to_server_when_server_missing(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """Without a registered server device, card entities stay on the server."""
    coordinator = MagicMock()
    coordinator.hass = hass
    coordinator.config_entry = mock_config_entry

    info = build_nic_device_info(coordinator, "0000:41:00", "Card")

    assert info == {"identifiers": {(DOMAIN, ENTRY_ID)}}


def test_helpers() -> None:
    """Names, IDs and keys for unusual cards."""
    cards = _cards()
    assert current_card_ids(None) == set()
    assert current_card_ids(cards) == {"0000:41:00", "0000:d5:00", "0000:d6:00"}

    card = cards.cards[0].model_copy(update={"model": None, "id": "0001:03:00"})
    assert card_name(card) == "Network card (0001:03:00)"

    # Two ports on one PCI function (mlx4): the second port ID has a suffix.
    spec = next(
        s
        for s in nic_sensor_specs(cards)
        if s.item == ("port", "0000:41:00.0") and s.description.key == "link_speed"
    )
    second = NICEntitySpec(
        spec.description, spec.card_id, spec.device_name, ("port", "0000:03:00.0-1")
    )
    assert second.key == "nic_0000_41_00_port_0000_03_00_0_1_link_speed"


async def test_client_get_network_cards(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """The client parses GET /network/cards."""
    aioclient_mock.get(
        "http://192.0.2.10:8043/api/v1/network/cards",
        json=json.loads(FIXTURE.read_text()),
    )
    client = UnraidClient("192.0.2.10", 8043, session=async_get_clientsession(hass))
    cards = await client.get_network_cards()

    assert cards.state == "ok"
    assert [c.model for c in cards.cards] == ["ConnectX-6 Dx", "AQC113CS", "AQC113CS"]
    module = cards.cards[0].ports[0].module
    assert module is not None
    assert module.vendor_pn == "QSFP-100G-AOC-3M"
    assert module.thresholds is not None
    assert module.thresholds.temperature_celsius is not None
    assert module.thresholds.temperature_celsius.high_alarm == 90
