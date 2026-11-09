"""Exercise telemetry reconciliation across a full REST poll."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable

import pytest

from custom_components.unraid_management_agent.api.events import (
    CollectorStateChangeEvent,
    NotificationUpdateEvent,
    NUTStatusUpdateEvent,
    VMGuestUpdateEvent,
    VMListUpdateEvent,
)
from custom_components.unraid_management_agent.api.exceptions import UnraidNotFoundError
from custom_components.unraid_management_agent.api.models import (
    CollectorDetails,
    CollectorStatus,
    Notification,
    NotificationOverview,
    NotificationsResponse,
    NUTInfo,
    SystemInfo,
    VMGuestInfo,
    VMInfo,
)
from custom_components.unraid_management_agent.const import CONF_ENABLE_VM_DEVICES
from custom_components.unraid_management_agent.telemetry import (
    EventOutcome,
    UnraidData,
    UnraidTelemetryReconciler,
)


class RecordingSource:
    """An offline source with an event hook on a mandatory endpoint."""

    def __init__(self, **responses: Callable[[], Awaitable[object]]) -> None:
        """Store endpoint overrides without starting any I/O."""
        self.responses = responses

    def __getattr__(self, name: str) -> Callable[[], Awaitable[object]]:
        """Expose a response for an optional REST read."""
        return self.responses.get(name, self.no_data)

    async def get_system_info(self) -> SystemInfo:
        """Provide a reachable core endpoint."""
        return SystemInfo(hostname="test")

    @staticmethod
    async def no_data() -> None:
        """Represent an unavailable optional endpoint."""


async def test_partial_nut_push_keeps_known_lists_during_full_poll():
    """Missing REST data cannot erase lists retained by a concurrent NUT event."""
    current = UnraidData(
        nut=NUTInfo.model_validate({"running": True, "devices": [{"name": "known"}]})
    )

    async def collectors() -> CollectorStatus:
        outcome = reconciler.apply_event(
            current, NUTStatusUpdateEvent(data=NUTInfo(installed=True, running=False))
        )
        assert outcome is EventOutcome.APPLIED
        return CollectorStatus()

    reconciler = UnraidTelemetryReconciler(
        RecordingSource(get_collectors_status=collectors)
    )
    result = await reconciler.refresh(current, {}, None)
    assert result.full_poll
    assert result.snapshot.nut.running is False
    assert [device.name for device in result.snapshot.nut.devices] == ["known"]


async def test_partial_notifications_and_collector_pushes_during_full_poll():
    """Replay push updates while preserving metadata missing from the poll."""
    overview = NotificationOverview(timestamp="previous")
    docker = CollectorDetails(name="docker", enabled=True, error_count=2)
    disk = CollectorDetails(name="disk", enabled=True, required=True)
    current = UnraidData(
        notifications=NotificationsResponse(overview=overview),
        collectors=CollectorStatus(collectors=[docker, disk]),
    )
    notification = Notification(subject="pushed")

    async def collectors() -> None:
        assert (
            reconciler.apply_event(
                current, NotificationUpdateEvent(data=[notification])
            )
            is EventOutcome.APPLIED
        )
        assert (
            reconciler.apply_event(
                current,
                CollectorStateChangeEvent(
                    data=CollectorDetails(name="docker", enabled=False)
                ),
            )
            is EventOutcome.APPLIED
        )

    reconciler = UnraidTelemetryReconciler(
        RecordingSource(get_collectors_status=collectors)
    )
    result = await reconciler.refresh(current, {}, None)
    assert result.full_poll
    assert result.snapshot.notifications is not None
    assert result.snapshot.notifications.notifications == [notification]
    assert result.snapshot.notifications.overview == overview
    assert result.snapshot.collectors is not None
    assert result.snapshot.collectors.collectors == [
        CollectorDetails(name="docker", enabled=False, error_count=2),
        disk,
    ]


async def test_optional_typed_not_found_is_quiet(caplog: pytest.LogCaptureFixture):
    """Suppress optional 404s even when the status is absent from the message."""

    async def not_found() -> None:
        message = "Not found"
        raise UnraidNotFoundError(message, status_code=404)

    reconciler = UnraidTelemetryReconciler(
        RecordingSource(get_nut_info=not_found, get_collectors_status=not_found)
    )
    with caplog.at_level(logging.DEBUG):
        result = await reconciler.refresh(UnraidData(), {}, None)

    assert result.full_poll
    assert result.snapshot.nut is None
    assert "Error fetching NUT status" not in caplog.text
    assert "Error fetching collectors status" in caplog.text


@pytest.mark.parametrize("guest_pushed_later", [False, True])
async def test_vm_replacement_push_invalidates_guest_read_during_full_poll(
    guest_pushed_later: bool,
):
    """A fetched VM list cannot hide the identity change that invalidates guest data."""
    guest = VMGuestInfo(vm_name="VM", hostname="old")
    new_guest = VMGuestInfo(vm_name="VM", hostname="new")
    current = UnraidData(vms=[VMInfo(name="VM", id="old")], vm_guest=[guest])
    vms = [VMInfo(name="VM", id="new")]

    async def list_vms() -> list[VMInfo]:
        return vms

    async def guests() -> list[VMGuestInfo]:
        outcome = reconciler.apply_event(current, VMListUpdateEvent(data=vms))
        assert outcome is EventOutcome.APPLIED
        if guest_pushed_later:
            outcome = reconciler.apply_event(
                current, VMGuestUpdateEvent(data=[new_guest])
            )
            assert outcome is EventOutcome.APPLIED
        return [guest]

    reconciler = UnraidTelemetryReconciler(
        RecordingSource(list_vms=list_vms, get_vm_guest=guests)
    )
    result = await reconciler.refresh(current, {CONF_ENABLE_VM_DEVICES: True}, None)
    assert result.snapshot.vms == vms
    assert result.snapshot.vm_guest == ([new_guest] if guest_pushed_later else [])
