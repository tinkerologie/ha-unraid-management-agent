"""Test share measurements separately from old and new storage counters."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from custom_components.unraid_management_agent.api.events import (
    ShareListUpdateEvent,
    parse_event,
)
from custom_components.unraid_management_agent.api.models import ShareInfo
from custom_components.unraid_management_agent.coordinator import UnraidData
from custom_components.unraid_management_agent.sensor import UnraidShareUsageSensor


def _sensor(payload: dict[str, Any]) -> UnraidShareUsageSensor:
    """Build the actual sensor around a parsed share and a local coordinator."""
    coordinator = MagicMock()
    coordinator.config_entry.entry_id = "test_entry"
    coordinator.config_entry.data = {}
    coordinator.data = UnraidData(
        shares=[ShareInfo.model_validate({"name": "appdata", **payload})]
    )
    return UnraidShareUsageSensor(coordinator, coordinator.config_entry, "appdata")


@pytest.mark.parametrize("used", [None, 0, 512])
def test_legacy_storage_usage(used: int | None) -> None:
    """Old used_bytes is storage usage, and is never a share measurement."""
    payload = {"total_bytes": 2048, "free_bytes": 1024, "usage_percent": 25}
    if used is not None:
        payload["used_bytes"] = used
    original = dict(payload)
    share = ShareInfo.model_validate(payload)
    assert payload == original
    assert share.storage_used_bytes == (1024 if used is None else used)
    assert share.storage_total_bytes == 2048
    assert share.storage_free_bytes == 1024
    assert share.storage_usage_percent == 25
    assert share.computed_used_percent == 25
    assert share.used_bytes is None
    sensor = _sensor(payload)
    assert sensor.native_value == 25.0
    assert "used_size" not in sensor.extra_state_attributes
    assert sensor.extra_state_attributes["storage_used"] == (
        "1.0 KB" if used is None else f"{used:.1f} B"
    )


@pytest.mark.parametrize("measured", [None, 0, 256])
@pytest.mark.parametrize("legacy_aliases", [False, True])
def test_new_storage_and_measured_usage(
    measured: int | None, legacy_aliases: bool
) -> None:
    """New storage figures win, with optional independent share measurements."""
    payload: dict[str, Any] = {
        "storage_used_bytes": "1024",
        "storage_free_bytes": "3072",
        "storage_total_bytes": "4096",
        "storage_usage_percent": "25.04",
        "use_cache": "prefer",
        "cache_pool": "cache",
        "mover_action": "cache_to_array",
    }
    if measured is not None:
        payload["used_bytes"] = measured
    if legacy_aliases:
        payload.update(total_bytes=8192, free_bytes=7168, usage_percent=12.5)
    share = ShareInfo.model_validate(payload)
    assert share.storage_used_bytes == 1024
    assert share.storage_free_bytes == 3072
    assert share.storage_total_bytes == 4096
    assert share.storage_usage_percent == 25.04
    assert share.computed_used_percent == 25.04
    assert share.used_bytes == measured
    sensor = _sensor(payload)
    assert sensor.native_value == 25.0
    assert sensor.unique_id == "test_entry_share_appdata_usage"
    assert sensor.translation_key == "share_usage"
    expected = {
        "share_name": "appdata",
        "storage_used": "1.0 KB",
        "storage_free": "3.0 KB",
        "storage_total": "4.0 KB",
        "total_size": "4.0 KB",
        "free_size": "3.0 KB",
        "use_cache": "prefer",
        "cache_pool": "cache",
        "mover_action": "cache_to_array",
    }
    if measured is not None:
        expected["used_size"] = f"{measured:.1f} B"
    assert sensor.extra_state_attributes == expected


@pytest.mark.parametrize("absent", [None, "", "-"])
def test_null_canonical_fields_use_legacy_values(absent: Any) -> None:
    """Resolve aliases independently, and derive used storage when necessary."""
    share = ShareInfo.model_validate(
        {
            "storage_used_bytes": absent,
            "storage_free_bytes": absent,
            "storage_total_bytes": absent,
            "storage_usage_percent": absent,
            "free_bytes": "750",
            "total_bytes": "1000",
            "usage_percent": "25",
            "used_bytes": "100",
        }
    )
    assert share.storage_used_bytes == 250
    assert share.storage_free_bytes == 750
    assert share.storage_total_bytes == 1000
    assert share.storage_usage_percent == 25
    assert share.used_bytes == 100
    assert share.computed_used_percent == 25


@pytest.mark.parametrize("zero", [0, "0"])
def test_canonical_zero_wins(zero: int | str) -> None:
    """Canonical zero is a value, even when legacy aliases disagree."""
    share = ShareInfo.model_validate(
        {
            "storage_used_bytes": zero,
            "storage_free_bytes": zero,
            "storage_total_bytes": zero,
            "storage_usage_percent": zero,
            "used_bytes": 100,
            "free_bytes": 750,
            "total_bytes": 1000,
            "usage_percent": 25,
        }
    )
    assert share.storage_used_bytes == 0
    assert share.storage_free_bytes == 0
    assert share.storage_total_bytes == 0
    assert share.storage_usage_percent == 0
    assert share.computed_used_percent == 0


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        ({"total_bytes": 1000, "used_bytes": 600}, 60.0),
        ({"total_bytes": 1000, "free_bytes": 750}, 25.0),
        ({"total_bytes": 1000}, None),
        ({"used_bytes": 600}, None),
        ({"total_bytes": 0, "used_bytes": 600}, None),
        ({"storage_total_bytes": 1000, "used_bytes": 600}, None),
        ({"storage_total_bytes": 0, "storage_used_bytes": 600}, None),
        ({"storage_total_bytes": None, "storage_used_bytes": 600}, None),
        (
            {"storage_total_bytes": 1000, "storage_free_bytes": 750, "used_bytes": 600},
            25.0,
        ),
        (
            {"storage_total_bytes": 1000, "storage_used_bytes": 0, "used_bytes": 600},
            0.0,
        ),
    ],
)
def test_storage_percentage(payload: dict[str, Any], expected: float | None) -> None:
    """Only storage figures determine utilisation, including old used counters."""
    share = ShareInfo.model_validate(payload)
    assert share.computed_used_percent == expected
    assert _sensor(payload).native_value == expected


def test_mixed_storage_fields_and_full_storage() -> None:
    """A full pool exposes zero free space; mixed aliases resolve per field."""
    sensor = _sensor({"storage_total_bytes": 2048, "free_bytes": 0, "used_bytes": 128})
    assert sensor.native_value == 100.0
    assert sensor.extra_state_attributes == {
        "share_name": "appdata",
        "storage_used": "2.0 KB",
        "storage_free": "0.0 B",
        "storage_total": "2.0 KB",
        "total_size": "2.0 KB",
        "used_size": "128.0 B",
    }


@pytest.mark.parametrize("total", [None, 0])
def test_unknown_storage_keeps_measurement_separate(total: int | None) -> None:
    """Null storage attributes distinguish measurements from the legacy schema."""
    sensor = _sensor({"storage_total_bytes": total, "used_bytes": 0})
    assert sensor.native_value is None
    assert sensor.extra_state_attributes == {
        "share_name": "appdata",
        "storage_used": None,
        "storage_free": None,
        "storage_total": None,
        "used_size": "0.0 B",
    }


@pytest.mark.parametrize("measured", [None, 0, 256])
def test_share_websocket_storage_fields(measured: int | None) -> None:
    """WebSocket list updates use the same resolved models as REST responses."""
    payload = {
        "name": "appdata",
        "storage_used_bytes": "1024",
        "storage_total_bytes": "4096",
        "storage_free_bytes": "3072",
    }
    if measured is not None:
        payload["used_bytes"] = measured
    event = parse_event({"event": "share_list_update", "data": [payload]})
    assert isinstance(event, ShareListUpdateEvent)
    share = event.data[0]
    assert share.storage_used_bytes == 1024
    assert share.storage_total_bytes == 4096
    assert share.storage_free_bytes == 3072
    assert share.computed_used_percent == 25.0
    assert share.used_bytes == measured
