"""
Test parsing of the agent's websocket envelope.

The agent sends every websocket message as
``{"event": "<topic>", "timestamp": "...", "data": <payload>}``.
``fixtures/websocket_events.json`` holds frames recorded from the agent's own
websocket handler (unraid-management-agent ``broadcastEvents`` and ``WSHub``,
commit 911400c) for one sample payload per topic.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from pytest_homeassistant.common import MockConfigEntry

from custom_components.unraid_management_agent import UnraidDataUpdateCoordinator
from custom_components.unraid_management_agent.api.constants import EventType
from custom_components.unraid_management_agent.api.events import (
    ArrayStatusUpdateEvent,
    CollectorStateChangeEvent,
    ContainerListUpdateEvent,
    DiskListUpdateEvent,
    FanControlUpdateEvent,
    GPUUpdateEvent,
    HardwareUpdateEvent,
    NetworkListUpdateEvent,
    NotificationsResponseEvent,
    NotificationUpdateEvent,
    NUTStatusUpdateEvent,
    ShareListUpdateEvent,
    SourceStatusChangedEvent,
    SystemUpdateEvent,
    UnknownEvent,
    UPSStatusUpdateEvent,
    VMListUpdateEvent,
    WebSocketEvent,
    ZFSArcUpdateEvent,
    ZFSDatasetUpdateEvent,
    ZFSPoolUpdateEvent,
    ZFSSnapshotUpdateEvent,
    parse_event,
)
from custom_components.unraid_management_agent.api.models import (
    CollectorDetails,
    CollectorStatus,
)
from custom_components.unraid_management_agent.const import DOMAIN
from custom_components.unraid_management_agent.coordinator import UnraidData

from .const import MOCK_CONFIG, mock_system_info, mock_ups_info

FRAMES: list[dict[str, Any]] = json.loads(
    (Path(__file__).parent / "fixtures" / "websocket_events.json").read_text()
)

# (envelope event name, expected event class), in fixture order
EXPECTED: list[tuple[str, type[WebSocketEvent]]] = [
    ("system_update", SystemUpdateEvent),
    ("array_status_update", ArrayStatusUpdateEvent),
    ("disk_list_update", DiskListUpdateEvent),
    ("share_list_update", ShareListUpdateEvent),
    ("container_list_update", ContainerListUpdateEvent),
    ("container_list_update", ContainerListUpdateEvent),  # empty list
    ("vm_list_update", VMListUpdateEvent),
    ("ups_status_update", UPSStatusUpdateEvent),
    ("nut_status_update", NUTStatusUpdateEvent),
    ("gpu_metrics_update", GPUUpdateEvent),
    ("gpu_metrics_update", GPUUpdateEvent),  # null list
    ("network_list_update", NetworkListUpdateEvent),
    ("hardware_update", HardwareUpdateEvent),
    ("notifications_update", NotificationsResponseEvent),
    ("zfs_pools_update", ZFSPoolUpdateEvent),
    ("zfs_datasets_update", ZFSDatasetUpdateEvent),
    ("zfs_snapshots_update", ZFSSnapshotUpdateEvent),
    ("zfs_arc_stats_update", ZFSArcUpdateEvent),
    ("fan_control_update", FanControlUpdateEvent),
    ("update", CollectorStateChangeEvent),  # collector_state_change
    ("source_status_changed", SourceStatusChangedEvent),
    ("mover_update", UnknownEvent),  # not used by the integration
]


def _frame(name: str, index: int = 0) -> dict[str, Any]:
    """Return the index-th recorded frame with this envelope event name."""
    return [f for f in FRAMES if f["event"] == name][index]


def test_fixture_matches_expectations() -> None:
    """The recorded frames are envelopes in the expected order."""
    assert [f["event"] for f in FRAMES] == [name for name, _ in EXPECTED]
    for frame in FRAMES:
        assert set(frame) == {"event", "timestamp", "data"}


@pytest.mark.parametrize(
    ("frame", "expected"),
    [(f, cls) for f, (_, cls) in zip(FRAMES, EXPECTED, strict=True)],
    ids=[f"{i}-{name}" for i, (name, _) in enumerate(EXPECTED)],
)
def test_envelope_parses_to_model(
    frame: dict[str, Any], expected: type[WebSocketEvent]
) -> None:
    """Each recorded envelope parses to the event class for its topic."""
    assert type(parse_event(frame)) is expected


def test_envelope_payloads() -> None:
    """Payloads come from the envelope's data, not the envelope itself."""
    system = parse_event(_frame("system_update"))
    assert system.data.hostname == "tower"
    assert system.data.cpu_usage_percent == 12.5

    array = parse_event(_frame("array_status_update"))
    assert array.data.state == "STARTED"

    assert [d.name for d in parse_event(_frame("disk_list_update")).data] == ["disk1"]
    assert [c.name for c in parse_event(_frame("container_list_update")).data] == [
        "plex"
    ]
    # An empty list is a real "no containers", not an unknown event
    assert parse_event(_frame("container_list_update", 1)).data == []
    # The agent sends null for a nil GPU slice; /gpu returns [] for it
    assert parse_event(_frame("gpu_metrics_update", 1)).data == []

    notifications = parse_event(_frame("notifications_update"))
    assert [n.subject for n in notifications.data.notifications] == ["Test"]

    source = parse_event(_frame("source_status_changed"))
    assert source.data["subsystem"] == "unassigned"
    empty = parse_event({"event": "source_status_changed", "data": None})
    assert isinstance(empty, SourceStatusChangedEvent)
    assert empty.data == {}


def test_collector_state_change_envelope() -> None:
    """The agent's collector event (generic "update" topic) maps to CollectorDetails."""
    event = parse_event(_frame("update"))
    assert isinstance(event, CollectorStateChangeEvent)
    assert event.data.name == "docker"
    assert event.data.enabled is False
    assert event.data.status == "stopped"
    assert event.data.interval_seconds == 30


def test_older_agent_generic_update_envelope() -> None:
    """Agents before v2026.03.00 named every event "update"; use the payload shape."""
    event = parse_event(
        {
            "event": "update",
            "timestamp": "2026-01-01T00:00:00Z",
            "data": {"hostname": "tower", "cpu_usage_percent": 3.0},
        }
    )
    assert isinstance(event, SystemUpdateEvent)
    assert event.data.hostname == "tower"

    unknown = parse_event({"event": "update", "data": {"something": "else"}})
    assert isinstance(unknown, UnknownEvent)


@pytest.mark.parametrize(
    ("topic", "expected"),
    [
        ("array_status_update", ArrayStatusUpdateEvent),
        ("zfs_datasets_update", ZFSDatasetUpdateEvent),
        ("zfs_snapshots_update", ZFSSnapshotUpdateEvent),
    ],
)
def test_generic_update_with_agent_payload_shapes(
    topic: str, expected: type[WebSocketEvent]
) -> None:
    """Recorded payloads that the older shape rules miss are still identified."""
    frame = {**_frame(topic), "event": "update"}
    assert type(parse_event(frame)) is expected


@pytest.mark.parametrize(
    "payload",
    ["text", [], ["text"], [{"something": "else"}]],
    ids=["string", "empty-list", "list-of-strings", "unknown-list"],
)
def test_generic_update_unidentifiable_payloads(payload: Any) -> None:
    """Payloads with no recognisable shape stay unknown."""
    assert isinstance(parse_event({"event": "update", "data": payload}), UnknownEvent)


def test_unenveloped_payloads_still_parse() -> None:
    """Bare payloads (no envelope) are still identified from their shape."""
    event = parse_event({"hostname": "tower", "cpu_usage_percent": 3.0})
    assert isinstance(event, SystemUpdateEvent)

    collector = parse_event(
        {"event": "collector_state_change", "collector": "vm", "enabled": True}
    )
    assert isinstance(collector, CollectorStateChangeEvent)
    assert collector.data.name == "vm"

    notifications = parse_event([{"importance": "warning", "subject": "Disk hot"}])
    assert isinstance(notifications, NotificationUpdateEvent)

    assert isinstance(parse_event("not an event"), UnknownEvent)


def test_envelope_event_type_value_names() -> None:
    """Envelope names that equal an EventType value are accepted too."""
    event = parse_event(
        {
            "event": EventType.GPU_UPDATE.value,
            "data": [{"name": "RTX 3070", "vendor": "nvidia"}],
        }
    )
    assert isinstance(event, GPUUpdateEvent)


@pytest.fixture
def coordinator(hass: HomeAssistant) -> UnraidDataUpdateCoordinator:
    """Coordinator holding data from a poll."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_CONFIG,
        unique_id=f"{MOCK_CONFIG[CONF_HOST]}:{MOCK_CONFIG[CONF_PORT]}",
        entry_id="test_entry_id",
    )
    entry.add_to_hass(hass)
    coordinator = UnraidDataUpdateCoordinator(
        hass, entry=entry, client=MagicMock(), enable_websocket=True
    )
    coordinator.data = UnraidData(
        system=mock_system_info(),
        ups=mock_ups_info(),
        collectors=CollectorStatus(
            total=2,
            collectors=[
                CollectorDetails(
                    name="docker",
                    enabled=True,
                    interval_seconds=30,
                    status="running",
                    required=False,
                    error_count=0,
                ),
                CollectorDetails(name="vm", enabled=True, interval_seconds=30),
            ],
        ),
    )
    return coordinator


async def test_recorded_frames_update_coordinator(
    hass: HomeAssistant, coordinator: UnraidDataUpdateCoordinator
) -> None:
    """Every recorded agent frame lands in the right coordinator field."""
    ups = coordinator.data.ups
    with (
        patch.object(coordinator, "async_update_listeners") as update_listeners,
        patch.object(coordinator, "async_request_refresh") as request_refresh,
    ):
        for frame in FRAMES:
            coordinator._handle_raw_message(frame)
        await hass.async_block_till_done()

    data = coordinator.data
    assert data.system.hostname == "tower"
    assert data.array.state == "STARTED"
    assert [d.name for d in data.disks] == ["disk1"]
    assert [s.name for s in data.shares] == ["appdata"]
    assert data.containers == []  # the later, empty container list
    assert [v.name for v in data.vms] == ["win11"]
    assert data.ups is not ups
    assert data.ups.status == "OL"  # NUT and hardware events left ups/system alone
    assert data.gpu == []  # the later, null GPU list
    assert [n.name for n in data.network] == ["eth0"]
    assert [n.subject for n in data.notifications.notifications] == ["Test"]
    assert [p.name for p in data.zfs_pools] == ["tank"]
    assert [d.name for d in data.zfs_datasets] == ["tank/data"]
    assert [s.name for s in data.zfs_snapshots] == ["tank/data@s1"]
    assert data.zfs_arc is not None
    assert data.fan_control is not None

    # collector_state_change updates one collector and keeps its other fields
    assert not coordinator.is_collector_enabled("docker")
    assert coordinator.is_collector_enabled("vm")
    docker = data.collectors.get_collector_by_name("docker")
    assert docker.status == "stopped"
    assert docker.required is False
    assert docker.error_count == 0
    assert data.collectors.total == 2
    assert data.collectors.enabled_count == 1
    assert data.collectors.disabled_count == 1

    # source_status_changed schedules a full refresh
    request_refresh.assert_called_once()
    # Entities are notified of the changes (mover_update is covered below)
    assert update_listeners.called


def test_unused_event_does_not_notify(
    coordinator: UnraidDataUpdateCoordinator,
) -> None:
    """An event the integration does not use leaves entities alone."""
    with patch.object(coordinator, "async_update_listeners") as update_listeners:
        coordinator._handle_raw_message(_frame("mover_update"))
    update_listeners.assert_not_called()


def test_collector_event_for_unlisted_collector(
    coordinator: UnraidDataUpdateCoordinator,
) -> None:
    """A collector missing from the polled status is added."""
    coordinator._handle_raw_message(
        {
            "event": "update",
            "data": {
                "event": "collector_state_change",
                "collector": "zfs",
                "enabled": False,
                "interval": 30,
            },
        }
    )
    names = [c.name for c in coordinator.data.collectors.collectors]
    assert names == ["docker", "vm", "zfs"]
    assert coordinator.data.collectors.total == 3
    assert coordinator.data.collectors.enabled_count == 2
    assert coordinator.data.collectors.disabled_count == 1
    assert not coordinator.is_collector_enabled("zfs")
