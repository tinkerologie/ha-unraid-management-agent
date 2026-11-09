"""Apply typed push updates to a telemetry snapshot."""

from __future__ import annotations

from enum import Enum, auto
from typing import Final

from custom_components.unraid_management_agent.api.events import (
    ArrayStatusUpdateEvent,
    CollectorStateChangeEvent,
    ContainerListUpdateEvent,
    DiskListUpdateEvent,
    FanControlUpdateEvent,
    GPUUpdateEvent,
    NetworkListUpdateEvent,
    NotificationsResponseEvent,
    NotificationUpdateEvent,
    NUTStatusUpdateEvent,
    ShareListUpdateEvent,
    SourceStatusChangedEvent,
    SystemUpdateEvent,
    UPSStatusUpdateEvent,
    VMGuestUpdateEvent,
    VMListUpdateEvent,
    WebSocketEvent,
    ZFSArcUpdateEvent,
    ZFSDatasetUpdateEvent,
    ZFSPoolUpdateEvent,
    ZFSSnapshotUpdateEvent,
)

from .state import (
    UnraidData,
    drop_replaced_vm_guests,
    merge_collector_state,
    merge_notifications,
    merge_nut,
)


class EventOutcome(Enum):
    """What the adapter should do after receiving a WebSocket event."""

    APPLIED = auto()
    REFRESH_REQUESTED = auto()
    IGNORED = auto()


STATEFUL_EVENTS: Final = (
    CollectorStateChangeEvent,
    NotificationUpdateEvent,
    NUTStatusUpdateEvent,
    VMListUpdateEvent,
)


def apply_event(
    data: UnraidData | None,
    event: WebSocketEvent,
    *,
    previous: UnraidData | None = None,
) -> EventOutcome:
    """Apply an event without notifying listeners or scheduling reads."""
    if data is None:
        return EventOutcome.IGNORED
    match event:
        case SystemUpdateEvent():
            data.system = event.data
        case ArrayStatusUpdateEvent():
            data.array = event.data
        case DiskListUpdateEvent():
            data.disks = event.data
        case UPSStatusUpdateEvent():
            data.ups = event.data
        case GPUUpdateEvent():
            data.gpu = event.data
        case NetworkListUpdateEvent():
            data.network = event.data
        case ContainerListUpdateEvent():
            data.containers = event.data
        case VMGuestUpdateEvent():
            data.vm_guest = event.data
        case ShareListUpdateEvent():
            data.shares = event.data
        case NotificationsResponseEvent():
            data.notifications = event.data
        case ZFSPoolUpdateEvent():
            data.zfs_pools = event.data
        case ZFSDatasetUpdateEvent():
            data.zfs_datasets = event.data
        case ZFSSnapshotUpdateEvent():
            data.zfs_snapshots = event.data
        case ZFSArcUpdateEvent():
            data.zfs_arc = event.data
        case FanControlUpdateEvent():
            data.fan_control = event.data
        case VMListUpdateEvent():
            data.vm_guest = drop_replaced_vm_guests(data.vm_guest, data.vms, event.data)
            if previous is not None:
                # A full poll may already have the new VM list but still hold
                # guest data read from the replaced VM before this event.
                data.vm_guest = drop_replaced_vm_guests(
                    data.vm_guest, previous.vms, event.data
                )
            data.vms = event.data
        case NUTStatusUpdateEvent():
            current = data.nut
            if previous is not None:
                current = merge_nut(previous.nut, current) if current else previous.nut
            data.nut = merge_nut(current, event.data)
        case NotificationUpdateEvent():
            data.notifications = merge_notifications(
                data.notifications,
                event.data,
                previous.notifications if previous else None,
            )
        case CollectorStateChangeEvent():
            current = (
                data.collectors
                if data.collectors is not None or previous is None
                else previous.collectors
            )
            data.collectors = merge_collector_state(current, event.data)
        case SourceStatusChangedEvent():
            return EventOutcome.REFRESH_REQUESTED
        case _:
            return EventOutcome.IGNORED
    return EventOutcome.APPLIED
