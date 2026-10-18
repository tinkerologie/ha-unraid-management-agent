"""Test the capability-aware options form (issues #231 and #195)."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.unraid_management_agent.api.models import (
    CollectorDetails,
    CollectorStatus,
    ContainerInfo,
    DockerSettings,
    FanControlStatus,
    FanDevice,
    FanInfo,
    GPUInfo,
    NICCard,
    NICList,
    SystemInfo,
    TemperatureInfo,
    VMInfo,
    VMSettings,
    ZFSPool,
)
from custom_components.unraid_management_agent.config_flow import (
    _has_controllable_fans,
    _has_fans,
    _has_hwmon_controllers,
    _service_present,
    _visible_option_keys,
)
from custom_components.unraid_management_agent.const import (
    CONF_CPU_TEMPERATURE_SOURCE,
    CONF_ENABLE_CONTAINER_DEVICES,
    CONF_ENABLE_CONTAINER_UPDATES,
    CONF_ENABLE_FAN_CONTROL,
    CONF_ENABLE_GPU_DEVICES,
    CONF_ENABLE_HWMON_DEVICES,
    CONF_ENABLE_NIC_DEVICES,
    CONF_ENABLE_VM_DEVICES,
    CONF_ENABLE_WEBSOCKET,
    CONF_ENABLE_ZFS_POOL_DEVICES,
    CONF_READ_ONLY,
    CPU_TEMPERATURE_SOURCE_AUTO,
    DOMAIN,
)
from custom_components.unraid_management_agent.coordinator import UnraidData

from .const import MOCK_CONFIG

ALL_BOOLEAN_KEYS = [
    CONF_ENABLE_CONTAINER_UPDATES,
    CONF_ENABLE_FAN_CONTROL,
    CONF_READ_ONLY,
    CONF_ENABLE_WEBSOCKET,
    CONF_ENABLE_CONTAINER_DEVICES,
    CONF_ENABLE_GPU_DEVICES,
    CONF_ENABLE_NIC_DEVICES,
    CONF_ENABLE_HWMON_DEVICES,
    CONF_ENABLE_VM_DEVICES,
    CONF_ENABLE_ZFS_POOL_DEVICES,
]

K10TEMP = TemperatureInfo(
    name="k10temp-pci-00c3_Tctl_temp1_input",
    value_celsius=45.12,
    source="k10temp-pci-00c3",
)
CPUTIN = TemperatureInfo(
    name="nct6798-isa-0290_CPUTIN_temp2_input",
    value_celsius=60.0,
    source="nct6798-isa-0290",
)
K10TEMP_KEY = "k10temp_pci_00c3_temp1"
CPUTIN_KEY = "nct6798_isa_0290_temp2"


def _minimal_data() -> UnraidData:
    """Return the data of a server with none of the optional capabilities."""
    return UnraidData(
        system=SystemInfo(fans=[], temperatures=[]),
        containers=[],
        vms=[],
        gpu=[],
        zfs_pools=[],
        network_cards=NICList(cards=[]),
        fan_control=FanControlStatus(
            fans=[FanDevice(id="fan1", name="Fan 1", controllable=False)]
        ),
        docker_settings=DockerSettings(enabled=False),
        vm_settings=VMSettings(enabled=False),
    )


def _full_data() -> UnraidData:
    """Return the data of a server with every optional capability."""
    return UnraidData(
        system=SystemInfo(
            fans=[
                FanInfo(
                    name="octo-hid-3-3_Fan1_fan1_input",
                    rpm=800,
                    source="octo-hid-3-3",
                    device_id="07274-50017",
                )
            ],
            temperatures=[K10TEMP, CPUTIN],
        ),
        containers=[ContainerInfo(id="abc", name="plex")],
        vms=[VMInfo(id="vm1", name="Windows")],
        gpu=[GPUInfo(name="RTX 3080")],
        zfs_pools=[ZFSPool(name="tank")],
        network_cards=NICList(cards=[NICCard(id="0000:01:00.0")]),
        fan_control=FanControlStatus(
            fans=[FanDevice(id="fan1", name="Fan 1", controllable=True)]
        ),
        docker_settings=DockerSettings(enabled=True),
        vm_settings=VMSettings(enabled=True),
    )


def _schema_keys(result: dict[str, Any]) -> list[str]:
    """Return the option keys of a form, in order."""
    return [key.schema for key in result["data_schema"].schema]


def _cpu_choices(result: dict[str, Any]) -> list[dict[str, str]]:
    """Return the CPU temperature source selector's choices."""
    for key, selector in result["data_schema"].schema.items():
        if key.schema == CONF_CPU_TEMPERATURE_SOURCE:
            return list(selector.config["options"])
    msg = "no CPU temperature source field"
    raise AssertionError(msg)


def _default(result: dict[str, Any], option: str) -> Any:
    """Return the default of one field of a form."""
    for key in result["data_schema"].schema:
        if key.schema == option:
            return key.default()
    msg = f"no {option} field"
    raise AssertionError(msg)


@pytest.fixture
async def loaded_entry(
    hass: HomeAssistant,
    mock_async_unraid_client: MagicMock,
    mock_unraid_websocket_client_class: MagicMock,
) -> MockConfigEntry:
    """Return a set-up entry; tests replace its coordinator data."""
    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG, options={})
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def _open(
    hass: HomeAssistant, entry: MockConfigEntry, data: UnraidData | None
) -> dict[str, Any]:
    """Open the options form with the given coordinator data."""
    entry.runtime_data.coordinator.data = data
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    return result


async def test_minimal_server_shows_only_general_options(
    hass: HomeAssistant, loaded_entry: MockConfigEntry
) -> None:
    """A server without optional hardware or services shows two options."""
    result = await _open(hass, loaded_entry, _minimal_data())
    assert _schema_keys(result) == [CONF_READ_ONLY, CONF_ENABLE_WEBSOCKET]


async def test_full_server_shows_every_option(
    hass: HomeAssistant, loaded_entry: MockConfigEntry
) -> None:
    """A server with every capability shows all options in order."""
    result = await _open(hass, loaded_entry, _full_data())
    assert _schema_keys(result) == [*ALL_BOOLEAN_KEYS, CONF_CPU_TEMPERATURE_SOURCE]
    assert _cpu_choices(result) == [
        {"value": CPU_TEMPERATURE_SOURCE_AUTO, "label": "Automatic"},
        {"value": K10TEMP_KEY, "label": "k10temp Tctl (45.1 °C)"},
        {"value": CPUTIN_KEY, "label": "nct6798 CPUTIN (60.0 °C)"},
    ]
    assert _default(result, CONF_CPU_TEMPERATURE_SOURCE) == CPU_TEMPERATURE_SOURCE_AUTO


async def test_enabled_option_stays_visible(
    hass: HomeAssistant, loaded_entry: MockConfigEntry
) -> None:
    """An option stored as on stays visible so it can be turned off."""
    hass.config_entries.async_update_entry(
        loaded_entry,
        options={CONF_ENABLE_GPU_DEVICES: True, CONF_ENABLE_CONTAINER_UPDATES: True},
    )
    result = await _open(hass, loaded_entry, _minimal_data())
    # The Docker options are shown together
    assert _schema_keys(result) == [
        CONF_ENABLE_CONTAINER_UPDATES,
        CONF_READ_ONLY,
        CONF_ENABLE_WEBSOCKET,
        CONF_ENABLE_CONTAINER_DEVICES,
        CONF_ENABLE_GPU_DEVICES,
    ]


async def test_hidden_options_keep_their_values(
    hass: HomeAssistant, loaded_entry: MockConfigEntry
) -> None:
    """Saving the form keeps the stored values of hidden options."""
    hass.config_entries.async_update_entry(
        loaded_entry,
        options={
            CONF_ENABLE_FAN_CONTROL: False,
            CONF_ENABLE_NIC_DEVICES: False,
            CONF_CPU_TEMPERATURE_SOURCE: CPU_TEMPERATURE_SOURCE_AUTO,
        },
    )
    result = await _open(hass, loaded_entry, _minimal_data())
    assert CONF_ENABLE_FAN_CONTROL not in _schema_keys(result)

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_READ_ONLY: True, CONF_ENABLE_WEBSOCKET: False},
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert dict(loaded_entry.options) == {
        CONF_ENABLE_FAN_CONTROL: False,
        CONF_ENABLE_NIC_DEVICES: False,
        CONF_CPU_TEMPERATURE_SOURCE: CPU_TEMPERATURE_SOURCE_AUTO,
        CONF_READ_ONLY: True,
        CONF_ENABLE_WEBSOCKET: False,
    }


async def test_all_options_without_coordinator_data(
    hass: HomeAssistant, loaded_entry: MockConfigEntry
) -> None:
    """Without coordinator data every option is shown."""
    result = await _open(hass, loaded_entry, None)
    assert _schema_keys(result) == [*ALL_BOOLEAN_KEYS, CONF_CPU_TEMPERATURE_SOURCE]
    assert _cpu_choices(result) == [
        {"value": CPU_TEMPERATURE_SOURCE_AUTO, "label": "Automatic"}
    ]


async def test_all_options_when_entry_not_loaded(hass: HomeAssistant) -> None:
    """An entry that is not set up shows every option."""
    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG, options={})
    entry.add_to_hass(hass)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert _schema_keys(result) == [*ALL_BOOLEAN_KEYS, CONF_CPU_TEMPERATURE_SOURCE]


async def test_missing_cpu_source_choice_is_kept(
    hass: HomeAssistant, loaded_entry: MockConfigEntry
) -> None:
    """A stored channel the agent no longer reports stays selectable."""
    hass.config_entries.async_update_entry(
        loaded_entry, options={CONF_CPU_TEMPERATURE_SOURCE: K10TEMP_KEY}
    )
    result = await _open(hass, loaded_entry, _minimal_data())
    assert CONF_CPU_TEMPERATURE_SOURCE in _schema_keys(result)
    assert _cpu_choices(result) == [
        {"value": CPU_TEMPERATURE_SOURCE_AUTO, "label": "Automatic"},
        {"value": K10TEMP_KEY, "label": f"{K10TEMP_KEY} (not currently reported)"},
    ]
    assert _default(result, CONF_CPU_TEMPERATURE_SOURCE) == K10TEMP_KEY


async def test_cpu_source_channel_without_reading(
    hass: HomeAssistant, loaded_entry: MockConfigEntry
) -> None:
    """A channel without a current reading is labelled by name only."""
    data = UnraidData(
        system=SystemInfo(
            temperatures=[
                TemperatureInfo(
                    name="k10temp-pci-00c3_Tctl_temp1_input",
                    source="k10temp-pci-00c3",
                )
            ]
        )
    )
    result = await _open(hass, loaded_entry, data)
    assert _cpu_choices(result)[1] == {"value": K10TEMP_KEY, "label": "k10temp Tctl"}


async def test_save_cpu_source_channel(
    hass: HomeAssistant, loaded_entry: MockConfigEntry
) -> None:
    """Saving a channel stores its key in the entry options."""
    result = await _open(hass, loaded_entry, _full_data())
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={CONF_CPU_TEMPERATURE_SOURCE: K10TEMP_KEY}
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert loaded_entry.options[CONF_CPU_TEMPERATURE_SOURCE] == K10TEMP_KEY


def _collectors(**enabled: bool | None) -> CollectorStatus:
    """Return a collector status listing the given collectors."""
    return CollectorStatus(
        collectors=[
            CollectorDetails(name=name, enabled=value)
            for name, value in enabled.items()
        ]
    )


@pytest.mark.parametrize(
    ("settings", "collectors", "expected"),
    [
        # A known service setting decides
        (DockerSettings(enabled=True), None, True),
        (DockerSettings(enabled=False), _collectors(docker=True), False),
        # Without one, only an explicitly enabled collector counts
        (None, _collectors(docker=True), True),
        (DockerSettings(enabled=None), _collectors(docker=True), True),
        (None, _collectors(docker=False), False),
        (None, _collectors(docker=None), False),
        (None, _collectors(vm=True), False),
        (None, None, False),
    ],
)
def test_service_present_rules(
    settings: DockerSettings | None,
    collectors: CollectorStatus | None,
    expected: bool,
) -> None:
    """Docker/VM visibility needs positive evidence, settings first."""
    data = UnraidData(collectors=collectors)
    assert _service_present(None, settings, "docker", data) is expected


def test_service_present_with_items() -> None:
    """Existing containers show the Docker options whatever the settings say."""
    data = UnraidData()
    containers = [ContainerInfo(id="abc", name="plex")]
    assert _service_present(containers, DockerSettings(enabled=False), "docker", data)


def test_vm_collector_shows_vm_option() -> None:
    """The VM option follows the vm collector when VM settings are unknown."""
    data = UnraidData(collectors=_collectors(vm=True))
    assert CONF_ENABLE_VM_DEVICES in _visible_option_keys(data)
    assert CONF_ENABLE_CONTAINER_DEVICES not in _visible_option_keys(data)


def test_capability_predicates_accept_missing_data() -> None:
    """Every predicate treats missing data as absent."""
    empty = UnraidData()
    assert _has_hwmon_controllers(empty) is False
    assert _has_controllable_fans(empty) is False
    assert _has_hwmon_controllers(UnraidData(system=SystemInfo())) is False
    assert _has_controllable_fans(UnraidData(fan_control=FanControlStatus())) is False
    assert _visible_option_keys(empty) == {CONF_READ_ONLY, CONF_ENABLE_WEBSOCKET}


def test_hwmon_controller_temperature_counts() -> None:
    """A temperature on a USB sensor controller shows the hwmon option."""
    reading = TemperatureInfo(
        name="octo-hid-3-3_Coolant_Temp_temp1_input",
        value_celsius=27.8,
        source="octo-hid-3-3",
        device_id="07274-50017",
    )
    data = UnraidData(system=SystemInfo(temperatures=[reading]))
    assert _has_hwmon_controllers(data) is True


def test_fan_without_id_is_not_controllable() -> None:
    """A controllable fan without an id gets no entity, so it does not count."""
    data = UnraidData(
        fan_control=FanControlStatus(fans=[FanDevice(name="Fan", controllable=True)])
    )
    assert _has_controllable_fans(data) is False


@pytest.mark.parametrize(
    ("collectors", "expected"),
    [
        (_collectors(nic=True), True),
        (_collectors(nic=False), False),
        (_collectors(docker=True), False),
        (None, False),
    ],
)
def test_nic_option_follows_the_nic_collector(
    collectors: CollectorStatus | None, expected: bool
) -> None:
    """With the option off no cards are fetched, so the nic collector decides."""
    data = UnraidData(network_cards=None, collectors=collectors)
    assert (CONF_ENABLE_NIC_DEVICES in _visible_option_keys(data)) is expected


def test_fans_without_control_show_the_fan_option() -> None:
    """Fan RPM sensors depend on the option, so any reported fan shows it."""
    rpm_only = UnraidData(
        system=SystemInfo(
            fans=[FanInfo(name="nct6798_fan1", rpm=900, source="nct6798-isa-0290")]
        ),
        fan_control=FanControlStatus(
            fans=[FanDevice(id="fan1", name="Fan 1", controllable=False)]
        ),
    )
    assert _has_fans(rpm_only) is True
    assert CONF_ENABLE_FAN_CONTROL in _visible_option_keys(rpm_only)
    assert _has_fans(UnraidData(system=SystemInfo(fans=[]))) is False
    assert _has_fans(UnraidData()) is False


@pytest.mark.parametrize("missing", ["runtime_data", "coordinator"])
async def test_all_options_without_runtime_data(
    hass: HomeAssistant, loaded_entry: MockConfigEntry, missing: str
) -> None:
    """A loaded entry without runtime data or coordinator shows every option."""
    runtime_data = loaded_entry.runtime_data
    if missing == "runtime_data":
        loaded_entry.runtime_data = None
    else:
        loaded_entry.runtime_data = MagicMock(coordinator=None)
    try:
        result = await hass.config_entries.options.async_init(loaded_entry.entry_id)
        assert result["type"] is FlowResultType.FORM
        assert _schema_keys(result) == [
            *ALL_BOOLEAN_KEYS,
            CONF_CPU_TEMPERATURE_SOURCE,
        ]
    finally:
        loaded_entry.runtime_data = runtime_data
