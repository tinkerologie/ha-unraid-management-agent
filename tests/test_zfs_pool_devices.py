"""Test ZFS pool child devices (the "ZFS pools as separate devices" option)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util
from pytest_homeassistant.common import MockConfigEntry

from custom_components.unraid_management_agent import (
    async_remove_config_entry_device,
)
from custom_components.unraid_management_agent.api.models import (
    StorageTopology,
    ZFSPool,
)
from custom_components.unraid_management_agent.cleanup import (
    STALE_REMOVAL_GRACE,
    _build_valid_dynamic_entity_keys,
    async_cleanup_stale_entities,
)
from custom_components.unraid_management_agent.const import (
    CONF_ENABLE_ZFS_POOL_DEVICES,
    DOMAIN,
)
from custom_components.unraid_management_agent.coordinator import UnraidData
from custom_components.unraid_management_agent.entity import (
    build_zfs_pool_device_info,
)
from custom_components.unraid_management_agent.zfs_drives import (
    drive_details,
    drive_locations,
    failing_drives,
    hottest_drive,
    media_errors,
    retained_roll_up_keys,
    roll_up_keys,
    worst_wear,
)

from .const import MOCK_CONFIG, MOCK_OPTIONS, mock_zfs_pools

ENTRY_ID = "test_entry_id"
FIXTURES = Path(__file__).parent / "fixtures"
POOL_KEYS = (
    "usage",
    "health",
    "corrupted_files",
    "scrub_status",
    "last_scrub",
    "scrub_errors",
    "scrub_repaired",
    "read_errors",
    "write_errors",
    "checksum_errors",
    "fragmentation",
)
DRIVE_KEYS = (
    "drive_count",
    "drive_max_temperature",
    "drive_max_wear",
    "drive_media_errors",
    "drives_failing",
)


def _pools() -> list[ZFSPool]:
    """Return the pools with drive health, as agent 2026.10 reports them."""
    raw = json.loads((FIXTURES / "zfs_pools_drives.json").read_text())
    return [ZFSPool.model_validate(pool) for pool in raw]


def _topology() -> StorageTopology:
    """Return the storage topology fixture (two NetApp shelves, an HPT card)."""
    raw = json.loads((FIXTURES / "storage_topology.json").read_text())
    return StorageTopology.model_validate(raw)


def _pool(name: str) -> ZFSPool:
    return next(p for p in _pools() if p.name == name)


def _entry(hass: HomeAssistant, *, pool_devices: bool) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Unraid (unraid-test)",
        data=MOCK_CONFIG,
        options={**MOCK_OPTIONS, CONF_ENABLE_ZFS_POOL_DEVICES: pool_devices},
        entry_id=ENTRY_ID,
    )
    entry.add_to_hass(hass)
    return entry


async def _setup(
    hass: HomeAssistant,
    client: MagicMock,
    pools: list[ZFSPool] | None,
    *,
    pool_devices: bool = True,
    topology: StorageTopology | None = None,
) -> MockConfigEntry:
    client.list_zfs_pools.return_value = pools
    client.get_storage_topology.return_value = topology
    entry = _entry(hass, pool_devices=pool_devices)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def _set_option(
    hass: HomeAssistant, entry: MockConfigEntry, *, pool_devices: bool
) -> None:
    """Change the option the way the options flow does (with a reload)."""
    hass.config_entries.async_update_entry(
        entry, options={**entry.options, CONF_ENABLE_ZFS_POOL_DEVICES: pool_devices}
    )
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()


def _entity(hass: HomeAssistant, domain: str, key: str) -> er.RegistryEntry:
    registry = er.async_get(hass)
    entity_id = registry.async_get_entity_id(domain, DOMAIN, f"{ENTRY_ID}_{key}")
    assert entity_id is not None, key
    entry = registry.async_get(entity_id)
    assert entry is not None
    return entry


def _server(hass: HomeAssistant) -> dr.DeviceEntry:
    server = dr.async_get(hass).async_get_device_by_identifier(
        (DOMAIN, ENTRY_ID), ENTRY_ID
    )
    assert server is not None
    return server


def _pool_device(hass: HomeAssistant, pool: str) -> dr.DeviceEntry | None:
    return dr.async_get(hass).async_get_child_device_by_identifier(
        (DOMAIN, f"{ENTRY_ID}_zfs_pool_{pool}"), ENTRY_ID
    )


# ── Option off (default) ──────────────────────────────────────────────────────


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_option_off_keeps_pool_entities_on_server(
    hass: HomeAssistant, mock_async_unraid_client: MagicMock
) -> None:
    """Without the option, nothing changes: server device, pool-named entities."""
    await _setup(hass, mock_async_unraid_client, _pools(), pool_devices=False)

    server = _server(hass)
    for key in POOL_KEYS:
        assert _entity(hass, "sensor", f"zfs_flash_{key}").device_id == server.id
    assert _entity(hass, "binary_sensor", "zfs_flash_problem").device_id == server.id
    assert _pool_device(hass, "flash") is None

    registry = er.async_get(hass)
    for key in DRIVE_KEYS:
        assert (
            registry.async_get_entity_id(
                "sensor", DOMAIN, f"{ENTRY_ID}_zfs_flash_{key}"
            )
            is None
        )

    usage = hass.states.get(_entity(hass, "sensor", "zfs_flash_usage").entity_id)
    assert usage is not None
    assert usage.attributes["friendly_name"] == "unraid-test ZFS Pool flash Usage"
    corrupted = _entity(hass, "sensor", "zfs_flash_corrupted_files")
    state = hass.states.get(corrupted.entity_id)
    assert state is not None
    assert state.attributes["friendly_name"] == "unraid-test flash Corrupted Files"


# ── Option on ─────────────────────────────────────────────────────────────────


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_option_on_creates_pool_devices_with_drive_health(
    hass: HomeAssistant, mock_async_unraid_client: MagicMock
) -> None:
    """Each pool is a child device holding its entities and drive roll-ups."""
    await _setup(hass, mock_async_unraid_client, _pools(), topology=_topology())

    server = _server(hass)
    for pool in ("nvme8tb", "exos24tb", "flash"):
        device = _pool_device(hass, pool)
        assert device is not None
        assert device.parent_device_id == server.id
        assert device.name == f"ZFS pool · {pool}"
        for key in POOL_KEYS:
            assert _entity(hass, "sensor", f"zfs_{pool}_{key}").device_id == device.id
        problem = _entity(hass, "binary_sensor", f"zfs_{pool}_problem")
        assert problem.device_id == device.id

    def state(pool: str, key: str) -> State:
        entity = _entity(hass, "sensor", f"zfs_{pool}_{key}")
        result = hass.states.get(entity.entity_id)
        assert result is not None
        return result

    # Short names on the pool device.
    assert state("flash", "usage").attributes["friendly_name"] == (
        "ZFS pool · flash Usage"
    )
    assert state("flash", "corrupted_files").attributes["friendly_name"] == (
        "ZFS pool · flash Corrupted files"
    )

    # Hottest awake drive: sdz is asleep (its 52 °C is stale), so sdaa at 40.
    hottest = state("exos24tb", "drive_max_temperature")
    assert hottest.state == "40"
    assert hottest.attributes["drive"] == "sdaa"
    assert state("nvme8tb", "drive_max_temperature").state == "47"

    wear = state("flash", "drive_max_wear")
    assert wear.state == "89"
    assert wear.attributes["drive"] == "nvme2n1"
    assert state("nvme8tb", "drive_max_wear").state == "12"

    errors = state("exos24tb", "drive_media_errors")
    assert errors.state == "3"
    assert errors.attributes["drives"] == {"sdaa": 3}
    assert state("nvme8tb", "drive_media_errors").state == "0"
    assert "drives" not in state("nvme8tb", "drive_media_errors").attributes

    failing = state("exos24tb", "drives_failing")
    assert failing.state == "1"
    assert failing.attributes["drives"] == ["sdaa"]
    # NVMe critical warning (spare below threshold) counts as failing.
    assert state("flash", "drives_failing").attributes["drives"] == ["nvme6n1"]
    assert state("nvme8tb", "drives_failing").state == "0"

    count = state("exos24tb", "drive_count")
    assert count.state == "4"
    drives = count.attributes["drives"]
    assert drives[0] == {
        "name": "sdy1",
        "disk": "sdy",
        "vdev": "raidz2-0",
        "state": "ONLINE",
        "model": "SEAGATE ST24000NM007H",
        "media_type": "hdd",
        "temperature": 37,
        "power_on_hours": 14219,
        "media_errors": 0,
        "smart_passed": True,
        "enclosure": "NETAPP DS424IOM12A (e242)",
        "slot": 0,
    }
    assert drives[1]["standby"] is True
    assert drives[3] == {
        "name": "9876543210123456789",
        "disk": None,
        "vdev": "raidz2-0",
        "state": "UNAVAIL",
    }
    flash = state("flash", "drive_count").attributes["drives"]
    assert flash[1]["critical_warning"] == 1
    assert "enclosure" not in flash[0]  # NVMe on the HPT card: no topology slot
    pool_states = [
        dict(state(pool, key).attributes)
        for pool in ("nvme8tb", "exos24tb", "flash")
        for key in ("drive_count", "drive_max_temperature", "drives_failing")
    ]
    assert "serial" not in json.dumps(pool_states).lower()


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_wear_sensor_only_for_pools_with_nvme(
    hass: HomeAssistant, mock_async_unraid_client: MagicMock
) -> None:
    """A pool of hard drives gets no NVMe wear sensor."""
    await _setup(hass, mock_async_unraid_client, _pools())
    registry = er.async_get(hass)
    assert (
        registry.async_get_entity_id(
            "sensor", DOMAIN, f"{ENTRY_ID}_zfs_exos24tb_drive_max_wear"
        )
        is None
    )
    assert _entity(hass, "sensor", "zfs_exos24tb_drive_max_temperature")


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_older_agent_gets_pool_devices_without_drive_health(
    hass: HomeAssistant, mock_async_unraid_client: MagicMock
) -> None:
    """An agent without pool members still gets pool devices, no roll-ups."""
    await _setup(hass, mock_async_unraid_client, mock_zfs_pools())

    device = _pool_device(hass, "zfs_pool")
    assert device is not None
    assert _entity(hass, "sensor", "zfs_zfs_pool_usage").device_id == device.id
    registry = er.async_get(hass)
    for key in DRIVE_KEYS:
        assert (
            registry.async_get_entity_id(
                "sensor", DOMAIN, f"{ENTRY_ID}_zfs_zfs_pool_{key}"
            )
            is None
        )


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_pool_gone_makes_roll_ups_unknown(
    hass: HomeAssistant, mock_async_unraid_client: MagicMock
) -> None:
    """When the pool disappears from the data its roll-ups have no value."""
    entry = await _setup(hass, mock_async_unraid_client, _pools())
    coordinator = entry.runtime_data.coordinator
    coordinator.data.zfs_pools = [p for p in _pools() if p.name != "flash"]
    coordinator.async_set_updated_data(coordinator.data)
    await hass.async_block_till_done()

    for key in ("drive_count", "drive_max_wear"):
        state = hass.states.get(_entity(hass, "sensor", f"zfs_flash_{key}").entity_id)
        assert state is not None
        assert state.state == "unknown"
        assert "drives" not in state.attributes
        assert "drive" not in state.attributes


# ── Toggling the option ───────────────────────────────────────────────────────


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_toggling_option_moves_entities_and_keeps_ids(
    hass: HomeAssistant, mock_async_unraid_client: MagicMock
) -> None:
    """Off -> on -> off keeps unique and entity IDs; devices come and go."""
    entry = await _setup(hass, mock_async_unraid_client, _pools(), pool_devices=False)
    server = _server(hass)
    before = {
        key: _entity(hass, "sensor", f"zfs_flash_{key}").entity_id for key in POOL_KEYS
    }
    problem_id = _entity(hass, "binary_sensor", "zfs_flash_problem").entity_id

    await _set_option(hass, entry, pool_devices=True)
    device = _pool_device(hass, "flash")
    assert device is not None
    for key, entity_id in before.items():
        moved = _entity(hass, "sensor", f"zfs_flash_{key}")
        assert moved.entity_id == entity_id
        assert moved.device_id == device.id
    assert _entity(hass, "binary_sensor", "zfs_flash_problem").entity_id == problem_id
    assert hass.states.get(problem_id) is not None

    await _set_option(hass, entry, pool_devices=False)
    for key, entity_id in before.items():
        back = _entity(hass, "sensor", f"zfs_flash_{key}")
        assert back.entity_id == entity_id
        assert back.device_id == server.id

    # The roll-ups are stale now: removed after the grace period, and then
    # the empty pool device goes too.
    coordinator = entry.runtime_data.coordinator
    async_cleanup_stale_entities(hass, entry, coordinator)
    roll_up = f"{ENTRY_ID}_zfs_flash_drive_count"
    assert roll_up in coordinator.stale_entity_candidates
    coordinator.stale_entity_candidates[roll_up] = dt_util.utcnow() - (
        STALE_REMOVAL_GRACE * 2
    )
    for key in DRIVE_KEYS:
        unique_id = f"{ENTRY_ID}_zfs_flash_{key}"
        if unique_id in coordinator.stale_entity_candidates:
            coordinator.stale_entity_candidates[unique_id] = dt_util.utcnow() - (
                STALE_REMOVAL_GRACE * 2
            )
    async_cleanup_stale_entities(hass, entry, coordinator)
    registry = er.async_get(hass)
    for key in DRIVE_KEYS:
        assert (
            registry.async_get_entity_id(
                "sensor", DOMAIN, f"{ENTRY_ID}_zfs_flash_{key}"
            )
            is None
        )
    assert _pool_device(hass, "flash") is None


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_roll_ups_stay_valid_while_option_on(
    hass: HomeAssistant, mock_async_unraid_client: MagicMock
) -> None:
    """Cleanup never treats the roll-ups as stale while the option is on."""
    entry = await _setup(hass, mock_async_unraid_client, _pools())
    coordinator = entry.runtime_data.coordinator
    async_cleanup_stale_entities(hass, entry, coordinator)
    assert not any(
        "_drive" in unique_id for unique_id in coordinator.stale_entity_candidates
    )


def test_valid_keys_include_roll_ups_only_with_option() -> None:
    """Roll-up keys are valid only with the option on, and only where they apply."""
    data = UnraidData(zfs_pools=[*_pools(), *mock_zfs_pools()])
    off = _build_valid_dynamic_entity_keys(data)
    on = _build_valid_dynamic_entity_keys(data, zfs_pool_devices=True)
    for key in DRIVE_KEYS:
        assert f"zfs_flash_{key}" not in off
        assert f"zfs_flash_{key}" in on
        # An agent without member drives: no roll-ups at all.
        assert f"zfs_zfs_pool_{key}" not in on
    assert "zfs_flash_usage" in off
    # A pool of hard drives has no wear sensor to keep.
    assert "zfs_exos24tb_drive_max_wear" not in on
    assert "zfs_exos24tb_drive_count" in on


def test_roll_up_keys() -> None:
    """Which roll-ups a pool gets, and which cleanup keeps."""
    assert roll_up_keys(_pool("flash")) == list(DRIVE_KEYS)
    assert "drive_max_wear" not in roll_up_keys(_pool("exos24tb"))
    assert roll_up_keys(mock_zfs_pools()[0]) == []
    assert retained_roll_up_keys(_pool("flash")) == list(DRIVE_KEYS)
    assert "drive_max_wear" not in retained_roll_up_keys(_pool("exos24tb"))
    # Agent without member drives (it reports vdevs): nothing to keep.
    assert retained_roll_up_keys(mock_zfs_pools()[0]) == []

    # NVMe members without SMART readings (a telemetry gap): the wear sensor
    # is not created, but an existing one is kept.
    gap = ZFSPool.model_validate(
        {
            "name": "p",
            "drives": [
                {"name": "nvme0n1p1", "disk": "nvme0n1"},
                {"name": "x", "health": {"media_type": "nvme"}},
            ],
        }
    )
    assert "drive_max_wear" not in roll_up_keys(gap)
    assert "drive_max_wear" in retained_roll_up_keys(gap)
    # Pool status unreadable this cycle (no vdevs, no drives): keep everything.
    assert retained_roll_up_keys(ZFSPool.model_validate({"name": "p"})) == list(
        DRIVE_KEYS
    )


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_wear_sensor_survives_smart_gap(
    hass: HomeAssistant, mock_async_unraid_client: MagicMock
) -> None:
    """A customized wear sensor is not deleted while SMART data is missing."""
    entry = await _setup(hass, mock_async_unraid_client, _pools())
    registry = er.async_get(hass)
    wear = _entity(hass, "sensor", "zfs_flash_drive_max_wear")
    registry.async_update_entity(wear.entity_id, new_entity_id="sensor.my_wear")

    coordinator = entry.runtime_data.coordinator
    raw = json.loads((FIXTURES / "zfs_pools_drives.json").read_text())
    for pool in raw:
        for drive in pool["drives"]:
            drive.pop("health", None)
    coordinator.data.zfs_pools = [ZFSPool.model_validate(p) for p in raw]
    coordinator.async_set_updated_data(coordinator.data)
    await hass.async_block_till_done()
    async_cleanup_stale_entities(hass, entry, coordinator)
    for unique_id in list(coordinator.stale_entity_candidates):
        coordinator.stale_entity_candidates[unique_id] = dt_util.utcnow() - (
            STALE_REMOVAL_GRACE * 2
        )
    async_cleanup_stale_entities(hass, entry, coordinator)

    assert registry.async_get("sensor.my_wear") is not None
    assert hass.states.get("sensor.my_wear").state == "unknown"


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_roll_ups_appear_when_drive_data_appears(
    hass: HomeAssistant, mock_async_unraid_client: MagicMock
) -> None:
    """Roll-ups are created on updates once the agent reports drives."""
    older = [
        ZFSPool.model_validate({**p.model_dump(), "drives": None}) for p in _pools()
    ]
    entry = await _setup(hass, mock_async_unraid_client, older)
    registry = er.async_get(hass)
    assert (
        registry.async_get_entity_id(
            "sensor", DOMAIN, f"{ENTRY_ID}_zfs_flash_drive_count"
        )
        is None
    )

    # The agent is upgraded: drives appear, the roll-ups follow without a reload.
    coordinator = entry.runtime_data.coordinator
    coordinator.data.zfs_pools = [
        *_pools(),
        ZFSPool.model_validate({"name": "new_pool", "drives": []}),
    ]
    coordinator.async_set_updated_data(coordinator.data)
    await hass.async_block_till_done()
    for key in DRIVE_KEYS:
        assert _entity(hass, "sensor", f"zfs_flash_{key}").device_id == (
            _pool_device(hass, "flash").id
        )
    # A pool that appeared after setup waits for a reload, like its other sensors.
    assert (
        registry.async_get_entity_id(
            "sensor", DOMAIN, f"{ENTRY_ID}_zfs_new_pool_drive_count"
        )
        is None
    )
    # A further update adds nothing twice, and an update without data is ignored.
    coordinator.async_set_updated_data(coordinator.data)
    await hass.async_block_till_done()
    count = len(er.async_entries_for_config_entry(registry, ENTRY_ID))
    coordinator.data = None
    coordinator.async_update_listeners()
    await hass.async_block_till_done()
    assert len(er.async_entries_for_config_entry(registry, ENTRY_ID)) == count


# ── Device removal ────────────────────────────────────────────────────────────


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_remove_pool_device_only_when_pool_is_gone(
    hass: HomeAssistant, mock_async_unraid_client: MagicMock
) -> None:
    """A pool device can be deleted once the agent no longer reports the pool."""
    entry = await _setup(hass, mock_async_unraid_client, _pools())
    device = _pool_device(hass, "flash")
    assert device is not None
    coordinator = entry.runtime_data.coordinator

    assert await async_remove_config_entry_device(hass, entry, device) is False

    coordinator.data.zfs_pools = None  # fetch failed: don't allow
    assert await async_remove_config_entry_device(hass, entry, device) is False

    coordinator.data.zfs_pools = [p for p in _pools() if p.name != "flash"]
    assert await async_remove_config_entry_device(hass, entry, device) is True


async def test_pool_device_info_falls_back_to_server(hass: HomeAssistant) -> None:
    """Without a registered server device the entity stays on the server."""
    entry = _entry(hass, pool_devices=True)
    coordinator = MagicMock()
    coordinator.hass = hass
    coordinator.config_entry = entry
    info = build_zfs_pool_device_info(coordinator, "flash")
    assert info == {"identifiers": {(DOMAIN, ENTRY_ID)}}
    assert entry.state is ConfigEntryState.NOT_LOADED


# ── Roll-up helpers ───────────────────────────────────────────────────────────


def test_roll_ups_without_health() -> None:
    """Pools whose members have no SMART reading give no values."""
    # A member on a known disk without a reading is reported as such.
    pool = ZFSPool.model_validate(
        {"name": "p", "drives": [{"name": "sdb1", "disk": "sdb", "state": "ONLINE"}]}
    )
    assert hottest_drive(pool) == (None, {})
    assert worst_wear(pool) == (None, {})
    assert media_errors(pool) == (None, {"unreported": ["sdb"]})
    assert failing_drives(pool) == (None, {"unreported": ["sdb"]})
    # Members without a disk (missing devices) have nothing to report.
    missing = ZFSPool.model_validate(
        {"name": "p", "drives": [{"name": "9876543210", "state": "UNAVAIL"}]}
    )
    assert media_errors(missing) == (None, {})
    assert failing_drives(missing) == (None, {})
    asleep = ZFSPool.model_validate(
        {"name": "p", "drives": [{"name": "sdb1", "health": {"standby": True}}]}
    )
    assert hottest_drive(asleep) == (None, {})
    # The member name is used when the disk could not be resolved.
    assert failing_drives(
        ZFSPool.model_validate(
            {
                "name": "p",
                "drives": [
                    {
                        "name": "x1",
                        "health": {"smart_passed": False, "collected_at": "t"},
                    }
                ],
            }
        )
    ) == (1, {"drives": ["x1"]})


def test_roll_ups_unknown_while_a_member_has_no_reading() -> None:
    """A gap in one member's SMART data must not look like a recovery."""
    raw = json.loads((FIXTURES / "zfs_pools_drives.json").read_text())
    exos = next(p for p in raw if p["name"] == "exos24tb")
    # Only the failing drive's reading is missing (asleep since agent start).
    exos["drives"][2]["health"] = {"standby": True}
    pool = ZFSPool.model_validate(exos)
    assert failing_drives(pool) == (None, {"unreported": ["sdaa"]})
    assert media_errors(pool) == (None, {"unreported": ["sdaa"]})
    # Hard drives don't affect NVMe wear.
    assert worst_wear(pool) == (None, {})

    flash = next(p for p in raw if p["name"] == "flash")
    del flash["drives"][0]["health"]
    pool = ZFSPool.model_validate(flash)
    assert worst_wear(pool) == (None, {"unreported": ["nvme2n1"]})


def test_drive_locations() -> None:
    """Disks map to the enclosure they sit in, by enclosure ID or storcli EID."""
    assert drive_locations(None) == {}
    topology = _topology()
    locations = drive_locations(topology)
    assert locations["sdy"] == ("NETAPP DS424IOM12A (e242)", 0)

    # A drive without enclosure_id is matched by controller and EID; drives
    # without a block device or in an unknown enclosure are skipped.
    patched = StorageTopology.model_validate(
        {
            **topology.model_dump(),
            "drives": [
                {
                    "controller_index": 0,
                    "enclosure_device_id": 245,
                    "slot": 3,
                    "device": "sdq",
                },
                {"controller_index": 0, "enclosure_device_id": 245, "slot": 4},
                {
                    "controller_index": 9,
                    "enclosure_device_id": 1,
                    "slot": 5,
                    "device": "sdr",
                },
            ],
        }
    )
    assert drive_locations(patched) == {"sdq": ("NETAPP DS424IOM12A (e245)", 3)}


def test_drive_details_without_health_or_vdev() -> None:
    """A single-disk vdev member with no health lists only what is known."""
    pool = ZFSPool.model_validate(
        {"name": "p", "drives": [{"name": "sdb1", "disk": "sdb", "state": "ONLINE"}]}
    )
    assert drive_details(pool, {}) == [
        {"name": "sdb1", "disk": "sdb", "state": "ONLINE"}
    ]
