"""Test ZFS pool parsing and the per-pool scrub, error and problem entities."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock

import pytest
from homeassistant.const import STATE_OFF, STATE_ON, STATE_UNKNOWN, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant.common import MockConfigEntry

from custom_components.unraid_management_agent.api.models import ZFSPool
from custom_components.unraid_management_agent.binary_sensor import (
    UnraidZFSPoolProblemBinarySensor,
)
from custom_components.unraid_management_agent.cleanup import (
    _build_valid_dynamic_entity_keys,
)
from custom_components.unraid_management_agent.const import DOMAIN
from custom_components.unraid_management_agent.coordinator import UnraidData
from custom_components.unraid_management_agent.sensor import (
    ZFS_POOL_SENSOR_DESCRIPTIONS,
    ZFS_SCAN_STATE_OPTIONS,
    UnraidZFSPoolSensor,
    _zfs_error_attrs,
    _zfs_scan_attrs,
    _zfs_scan_state,
    _zfs_scan_time,
)

from .const import MOCK_CONFIG, MOCK_OPTIONS


def test_zfs_pool_usage_from_allocated_bytes() -> None:
    """The agent reports pool usage as allocated_bytes (zpool ALLOC)."""
    pool = ZFSPool.model_validate(
        {"name": "tank", "size_bytes": 400, "allocated_bytes": 100, "free_bytes": 300}
    )
    assert pool.used_bytes == 100
    assert pool.computed_used_percent == 25.0


def test_zfs_pool_usage_from_used_bytes() -> None:
    """used_bytes still works for agents that send it."""
    pool = ZFSPool(name="tank", size_bytes=400, used_bytes=200)
    assert pool.computed_used_percent == 50.0


# ---------------------------------------------------------------------------
# Scrub, error and fragmentation entities
# ---------------------------------------------------------------------------

ENTRY_ID = "test_entry_id"

# One pool from a live agent's /api/v1/zfs/pools (GUID replaced), with the
# scrub times this agent reports once it parses `zpool status` scan lines.
LIVE_POOL: dict[str, Any] = {
    "name": "ssd8tb",
    "guid": "1234567890123456789",
    "health": "ONLINE",
    "state": "ONLINE",
    "size_bytes": 7679401525248,
    "allocated_bytes": 4528324333568,
    "free_bytes": 3151077191680,
    "fragmentation_percent": 18,
    "capacity_percent": 58,
    "dedup_ratio": 1,
    "readonly": False,
    "autoexpand": True,
    "autotrim": "on",
    "vdevs": [
        {
            "name": "mirror-0",
            "type": "mirror",
            "state": "ONLINE",
            "read_errors": 0,
            "write_errors": 0,
            "checksum_errors": 0,
            "devices": [
                {
                    "name": "sdb1",
                    "state": "ONLINE",
                    "read_errors": 0,
                    "write_errors": 0,
                    "checksum_errors": 0,
                },
                {
                    "name": "sdc1",
                    "state": "ONLINE",
                    "read_errors": 0,
                    "write_errors": 0,
                    "checksum_errors": 0,
                },
            ],
        }
    ],
    "scan_status": "scrub completed",
    "scan_state": "finished",
    "scan_errors": 0,
    "scan_repaired_bytes": 0,
    "scan_start_time": "2026-10-07T09:00:01-04:00",
    "scan_end_time": "2026-10-07T13:27:01-04:00",
    "scan_progress_percent": 100,
    "read_errors": 0,
    "write_errors": 0,
    "checksum_errors": 0,
    "is_boot_pool": False,
    "timestamp": "2026-10-08T22:43:53.241662432-04:00",
}

# What agents before the scan-time fix report for the same pool.
OLD_AGENT_POOL: dict[str, Any] = {
    **LIVE_POOL,
    "scan_start_time": "0001-01-01T00:00:00Z",
    "scan_end_time": "0001-01-01T00:00:00Z",
    "scan_progress_percent": 0,
}

SENSOR_KEYS = {d.key for d in ZFS_POOL_SENSOR_DESCRIPTIONS}


def _pool(**overrides: Any) -> ZFSPool:
    return ZFSPool.model_validate({**LIVE_POOL, **overrides})


def _with_device_errors(**counters: int) -> ZFSPool:
    vdev = LIVE_POOL["vdevs"][0]
    device = {**vdev["devices"][0], **counters}
    return _pool(vdevs=[{**vdev, "devices": [device, vdev["devices"][1]]}])


def test_error_total_sums_pool_vdevs_and_devices() -> None:
    """Device errors that zpool does not roll up into the pool row are counted."""
    assert _pool().error_total("checksum_errors") == 0
    pool = _with_device_errors(checksum_errors=3, read_errors=1)
    assert pool.error_total("checksum_errors") == 3
    assert pool.error_total("read_errors") == 1
    pool = _pool(write_errors=2, vdevs=[{**LIVE_POOL["vdevs"][0], "write_errors": 1}])
    assert pool.error_total("write_errors") == 3


def test_error_total_missing_counters() -> None:
    """Without any counter from the agent the total is unknown, not zero."""
    pool = ZFSPool.model_validate({"name": "tank", "vdevs": [{"devices": [{}]}]})
    assert pool.error_total("read_errors") is None
    pool = ZFSPool.model_validate({"name": "tank", "checksum_errors": 0})
    assert pool.error_total("checksum_errors") == 0


@pytest.mark.parametrize(
    ("scan_status", "scan_state", "expected"),
    [
        ("scrub completed", "finished", "scrub_finished"),
        ("scrub in progress", "scanning", "scrubbing"),
        ("scrub paused", "paused", "scrub_paused"),
        ("scrub canceled", "canceled", "scrub_canceled"),
        ("resilver in progress", "scanning", "resilvering"),
        ("resilver completed", "finished", "resilver_finished"),
        ("resilver canceled", "canceled", "resilver_canceled"),
        # Agents before the scan fix report "in progress" for running scrubs
        ("in progress", "scanning", "scrubbing"),
        (None, None, "none"),
        ("", "", "none"),
        ("scrub completed", "unexpected", None),
    ],
)
def test_zfs_scan_state(
    scan_status: str | None, scan_state: str | None, expected: str | None
) -> None:
    """The agent's scan status/state map onto the enum options."""
    pool = _pool(scan_status=scan_status, scan_state=scan_state)
    assert _zfs_scan_state(pool) == expected
    assert expected is None or expected in ZFS_SCAN_STATE_OPTIONS


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("2026-10-07T13:27:01-04:00", datetime(2026, 10, 7, 17, 27, 1, tzinfo=UTC)),
        ("2026-10-07T17:27:01", datetime(2026, 10, 7, 17, 27, 1, tzinfo=UTC)),
        ("0001-01-01T00:00:00Z", None),
        ("not a time", None),
        ("", None),
        (None, None),
    ],
)
def test_zfs_scan_time(value: str | None, expected: datetime | None) -> None:
    """Zero (never scanned) and unparsable times become None; naive is UTC."""
    assert _zfs_scan_time(value) == expected


def test_zfs_scan_attrs() -> None:
    """Start time is always shown; progress only while a scan runs or is paused."""
    assert _zfs_scan_attrs(_pool()) == {"scan_start_time": "2026-10-07T09:00:01-04:00"}
    running = _pool(
        scan_status="scrub in progress",
        scan_state="scanning",
        scan_end_time="0001-01-01T00:00:00Z",
        scan_progress_percent=48.06,
    )
    assert _zfs_scan_attrs(running) == {
        "scan_start_time": "2026-10-07T09:00:01-04:00",
        "progress_percent": 48.06,
    }
    assert _zfs_scan_attrs(ZFSPool.model_validate(OLD_AGENT_POOL)) == {}


def test_zfs_error_attrs_lists_failing_devices() -> None:
    """The error sensors name the vdevs/devices with non-zero counters."""
    attrs_fn = _zfs_error_attrs("checksum_errors")
    assert attrs_fn(_pool()) == {}
    assert attrs_fn(_with_device_errors(checksum_errors=3)) == {"devices": {"sdb1": 3}}
    assert attrs_fn(ZFSPool.model_validate({"name": "tank"})) == {}


def _pool_entity_ids(registry: er.EntityRegistry, pool_name: str) -> dict[str, str]:
    """Map key suffix -> entity_id for one pool's entities."""
    prefix = f"{ENTRY_ID}_zfs_{pool_name}_"
    return {
        entry.unique_id.removeprefix(prefix): entry.entity_id
        for entry in er.async_entries_for_config_entry(registry, ENTRY_ID)
        if entry.unique_id.startswith(prefix)
    }


async def _setup(hass: HomeAssistant) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Unraid (unraid-test)",
        data=MOCK_CONFIG,
        options=MOCK_OPTIONS,
        entry_id=ENTRY_ID,
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_zfs_pool_scrub_entities(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mock_async_unraid_client: MagicMock,
) -> None:
    """Each pool gets scrub, error and problem entities with the right defaults."""
    mock_async_unraid_client.list_zfs_pools.return_value = [_pool()]
    entry = await _setup(hass)

    ids = _pool_entity_ids(entity_registry, "ssd8tb")
    assert set(ids) == {"usage", "health", "corrupted_files", "problem"} | SENSOR_KEYS
    enabled = {"usage", "health", "corrupted_files", "scrub_status", "last_scrub"}
    for key, entity_id in ids.items():
        reg = entity_registry.async_get(entity_id)
        assert reg is not None
        if key in enabled or key == "problem":
            assert reg.disabled_by is None, key
        else:
            assert reg.disabled_by is er.RegistryEntryDisabler.INTEGRATION, key
        if key in SENSOR_KEYS:
            assert reg.entity_category is EntityCategory.DIAGNOSTIC, key

    assert ids["scrub_status"] == "sensor.unraid_test_zfs_pool_ssd8tb_scrub_status"
    assert ids["last_scrub"] == "sensor.unraid_test_zfs_pool_ssd8tb_last_scrub"
    assert ids["problem"] == "binary_sensor.unraid_test_zfs_pool_ssd8tb_problem"

    status = hass.states.get(ids["scrub_status"])
    assert status is not None
    assert status.state == "scrub_finished"
    assert status.attributes["options"] == ZFS_SCAN_STATE_OPTIONS
    assert status.attributes["scan_start_time"] == "2026-10-07T09:00:01-04:00"
    last = hass.states.get(ids["last_scrub"])
    assert last is not None
    assert last.state == "2026-10-07T17:27:01+00:00"
    problem = hass.states.get(ids["problem"])
    assert problem is not None
    assert problem.state == STATE_OFF
    assert problem.attributes["health"] == "ONLINE"
    assert problem.attributes["checksum_errors"] == 0

    # Enable the disabled sensors and check their values
    for key in SENSOR_KEYS - enabled:
        entity_registry.async_update_entity(ids[key], disabled_by=None)
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    expected = {
        "scrub_errors": "0",
        "scrub_repaired": "0.0",
        "read_errors": "0",
        "write_errors": "0",
        "checksum_errors": "0",
        "fragmentation": "18.0",
    }
    for key, value in expected.items():
        state = hass.states.get(ids[key])
        assert state is not None
        assert state.state == value, key
    repaired = hass.states.get(ids["scrub_repaired"])
    assert repaired is not None
    assert repaired.attributes["unit_of_measurement"] == "MiB"

    # A checksum error on one disk turns the problem sensor on
    mock_async_unraid_client.list_zfs_pools.return_value = [
        _with_device_errors(checksum_errors=3)
    ]
    await entry.runtime_data.coordinator.async_refresh()
    await hass.async_block_till_done()
    checksum = hass.states.get(ids["checksum_errors"])
    assert checksum is not None
    assert checksum.state == "3"
    assert checksum.attributes["devices"] == {"sdb1": 3}
    problem = hass.states.get(ids["problem"])
    assert problem is not None
    assert problem.state == STATE_ON
    assert problem.attributes["checksum_errors"] == 3


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_zfs_pool_scrub_entities_old_agent(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mock_async_unraid_client: MagicMock,
) -> None:
    """Zero scan times from older agents show as unknown, not year 1."""
    mock_async_unraid_client.list_zfs_pools.return_value = [
        ZFSPool.model_validate(OLD_AGENT_POOL)
    ]
    await _setup(hass)
    ids = _pool_entity_ids(entity_registry, "ssd8tb")
    last = hass.states.get(ids["last_scrub"])
    assert last is not None
    assert last.state == STATE_UNKNOWN
    status = hass.states.get(ids["scrub_status"])
    assert status is not None
    assert status.state == "scrub_finished"
    assert "scan_start_time" not in status.attributes


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_zfs_pool_entities_without_scan_fields(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mock_async_unraid_client: MagicMock,
) -> None:
    """A pool with only basic fields still sets up; scan values are empty."""
    mock_async_unraid_client.list_zfs_pools.return_value = [
        ZFSPool.model_validate({"name": "tank", "health": "ONLINE"})
    ]
    await _setup(hass)
    ids = _pool_entity_ids(entity_registry, "tank")
    status = hass.states.get(ids["scrub_status"])
    assert status is not None
    assert status.state == "none"
    last = hass.states.get(ids["last_scrub"])
    assert last is not None
    assert last.state == STATE_UNKNOWN
    problem = hass.states.get(ids["problem"])
    assert problem is not None
    assert problem.state == STATE_OFF


def _problem_sensor(pools: list[ZFSPool] | None) -> UnraidZFSPoolProblemBinarySensor:
    coordinator = MagicMock()
    coordinator.config_entry.entry_id = ENTRY_ID
    coordinator.data = UnraidData(zfs_pools=pools)
    return UnraidZFSPoolProblemBinarySensor(coordinator, "ssd8tb")


@pytest.mark.parametrize(
    ("pool", "expected"),
    [
        (_pool(), False),
        (_pool(health="DEGRADED", state="DEGRADED"), True),
        (_pool(health=None, state="FAULTED"), True),
        (_pool(scan_errors=2), True),
        (_pool(read_errors=1), True),
        (_with_device_errors(write_errors=1), True),
    ],
)
def test_zfs_pool_problem(pool: ZFSPool, expected: bool) -> None:
    """Problem is on for a non-ONLINE pool or any error count above zero."""
    assert _problem_sensor([pool]).is_on is expected


def test_zfs_pool_problem_pool_missing() -> None:
    """Without data for the pool, the problem state is unknown."""
    sensor = _problem_sensor(None)
    assert sensor.is_on is None
    assert sensor.extra_state_attributes == {}
    sensor = _problem_sensor([_pool(name="other")])
    assert sensor.is_on is None


def test_zfs_pool_sensor_pool_missing() -> None:
    """Pool sensors report nothing when the pool is gone from the data."""
    coordinator = MagicMock()
    coordinator.config_entry.entry_id = ENTRY_ID
    coordinator.data = UnraidData(zfs_pools=[_pool(name="other")])
    by_key = {d.key: d for d in ZFS_POOL_SENSOR_DESCRIPTIONS}
    status = UnraidZFSPoolSensor(
        coordinator, MagicMock(), "ssd8tb", by_key["scrub_status"]
    )
    assert status.native_value is None
    assert status.extra_state_attributes is None
    last = UnraidZFSPoolSensor(coordinator, MagicMock(), "ssd8tb", by_key["last_scrub"])
    coordinator.data = UnraidData(zfs_pools=[_pool()])
    assert last.extra_state_attributes is None


def test_cleanup_keeps_zfs_scrub_keys() -> None:
    """Stale-entity cleanup knows every per-pool key."""
    keys = _build_valid_dynamic_entity_keys(UnraidData(zfs_pools=[_pool()]))
    expected = {f"zfs_ssd8tb_{key}" for key in SENSOR_KEYS | {"problem"}}
    assert expected <= keys
