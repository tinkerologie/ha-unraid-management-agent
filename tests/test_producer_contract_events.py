"""Wire contracts consumed by the vendored WebSocket decoder."""

import json

import pytest
from pydantic import ValidationError

from custom_components.unraid_management_agent.api.events import (
    CollectorStateChangeEvent,
    NotificationsResponseEvent,
    NotificationUpdateEvent,
    NUTStatusUpdateEvent,
    ShareListUpdateEvent,
    SourceStatusChangedEvent,
    UnknownEvent,
    UPSStatusUpdateEvent,
    ZFSPoolUpdateEvent,
    parse_event,
)
from tests.producer_contract import assert_values, fixture
from tests.test_producer_contract_rest import NOTIFICATIONS, NUT, UPS, ZFS_LIST

EVENTS = {
    "collector-state-event": (
        CollectorStateChangeEvent,
        {
            "name": "disk",
            "interval_seconds": 30,
            "enabled": False,
            "status": "stopped",
        },
    ),
    "legacy-collector-event": (
        CollectorStateChangeEvent,
        {
            "name": "disk",
            "interval_seconds": 5,
            "last_run": None,
        },
    ),
    "notifications-event": (
        NotificationsResponseEvent,
        NOTIFICATIONS
        | {
            "overview.unread.total": 1,
            "overview.archive.total": 0,
        },
    ),
    "legacy-notification-event": (NotificationUpdateEvent, {"0.subject": "Example"}),
    "nut-event": (NUTStatusUpdateEvent, NUT),
    "legacy-nut-event": (NUTStatusUpdateEvent, NUT),
    "ups-event": (UPSStatusUpdateEvent, UPS),
    "shares-null-event": (ShareListUpdateEvent, []),
    "source-health-event": (
        SourceStatusChangedEvent,
        {
            "subsystem": "shares",
            "state": "degraded",
            "reason": "synthetic incomplete sample",
        },
    ),
    "zfs-pools-event": (ZFSPoolUpdateEvent, ZFS_LIST),
}


def check_event(case, frame):
    """Validate the expected decoder output for one frame."""
    expected_type, expected = EVENTS[case]
    result = parse_event(frame)
    assert type(result) is expected_type
    if isinstance(expected, list):
        assert result.data == expected
    else:
        assert_values(result.data, expected)
    return result


@pytest.mark.parametrize("case", EVENTS)
def test_event_contract(case):
    """Check the typed payload, including consumer-owned field values."""
    parsed = check_event(case, json.loads(fixture(case)))
    if isinstance(parsed, CollectorStateChangeEvent):
        fields = parsed.data.model_fields_set
        assert "required" not in fields
        assert "error_count" not in fields
        assert ("last_run" in fields) == (case == "legacy-collector-event")


def test_unrecognised_event_keeps_frame_and_null_source_event_is_empty():
    """Keep unknown frames available for diagnostics."""
    frame = {"event": "future_event", "data": {"value": 42}}
    parsed = parse_event(frame)
    assert isinstance(parsed, UnknownEvent)
    assert parsed.data == frame
    assert parse_event({"event": "source_status_changed", "data": None}).data == {}


def test_drift_is_detected():
    """Reject plausible drift even when the decoder accepts the payload."""
    pools = json.loads(fixture("zfs-pools-event"))
    check_event("zfs-pools-event", pools)
    with pytest.raises(AssertionError):
        check_event("zfs-pools-event", {**pools, "data": {}})
    with pytest.raises(ValidationError):
        check_event("zfs-pools-event", {**pools, "data": {"wrong": True}})

    nut = json.loads(fixture("nut-event"))
    check_event("nut-event", nut)
    wrong_topic = {**nut, "event": "ups_status_update"}
    with pytest.raises(ValidationError):
        check_event("nut-event", wrong_topic)
    without_legacy_status = dict(nut["data"])
    without_legacy_status.pop("status")
    with pytest.raises(AssertionError):
        check_event("nut-event", {**wrong_topic, "data": without_legacy_status})
