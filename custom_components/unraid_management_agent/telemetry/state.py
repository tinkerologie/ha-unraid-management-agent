"""Published telemetry snapshot and domain merge rules."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from custom_components.unraid_management_agent.api.models import (
    AlertRule,
    AlertStatus,
    ArrayStatus,
    CollectorDetails,
    CollectorStatus,
    ContainerInfo,
    ContainerUpdatesResult,
    DiagnosticsSelfTestResponse,
    DiskInfo,
    DiskSettings,
    DockerPortConflict,
    DockerSettings,
    FanControlStatus,
    FlashDriveInfo,
    GPUInfo,
    MoverSettings,
    NetworkInterface,
    NetworkServicesStatus,
    NICList,
    Notification,
    NotificationsResponse,
    NUTInfo,
    ParityHistory,
    ParitySchedule,
    PluginList,
    RegistrationInfo,
    RemoteShare,
    ShareInfo,
    StorageTopology,
    SystemInfo,
    SystemService,
    UnassignedDevice,
    UpdateStatus,
    UPSInfo,
    UserScript,
    VMGuestInfo,
    VMInfo,
    VMSettings,
    ZFSArcStats,
    ZFSDataset,
    ZFSPool,
    ZFSSnapshot,
)

# UnraidData fields read or written while recording (see call_recording_reads)
_reads: set[str] | None = None
# Instance whose writes are recorded, so copies made meanwhile don't count
_write_target: UnraidData | None = None
_writes: set[str] = set()


@dataclass
class UnraidData:
    """Container for Unraid coordinator data."""

    def __getattribute__(self, name: str) -> Any:
        """Record the field read, so an event wakes only the field's readers."""
        if _reads is not None and not name.startswith("_"):
            _reads.add(name)
        return object.__getattribute__(self, name)

    def __setattr__(self, name: str, value: Any) -> None:
        """Record the field written, so an event wakes only the field's readers."""
        if self is _write_target:
            _writes.add(name)
        object.__setattr__(self, name, value)

    system: SystemInfo | None = None
    array: ArrayStatus | None = None
    disks: list[DiskInfo] | None = None
    containers: list[ContainerInfo] | None = None
    vms: list[VMInfo] | None = None
    ups: UPSInfo | None = None
    # /nut: every NUT device (statuses). None when the fetch failed.
    nut: NUTInfo | None = None
    gpu: list[GPUInfo] | None = None
    network: list[NetworkInterface] | None = None
    shares: list[ShareInfo] | None = None
    notifications: NotificationsResponse | None = None
    user_scripts: list[UserScript] | None = None
    zfs_pools: list[ZFSPool] | None = None
    zfs_datasets: list[ZFSDataset] | None = None
    zfs_snapshots: list[ZFSSnapshot] | None = None
    zfs_arc: ZFSArcStats | None = None
    collectors: CollectorStatus | None = None
    # New data for enhanced features
    fan_control: FanControlStatus | None = None
    disk_settings: DiskSettings | None = None
    mover_settings: MoverSettings | None = None
    parity_schedule: ParitySchedule | None = None
    parity_history: ParityHistory | None = None
    flash_info: FlashDriveInfo | None = None
    plugins: PluginList | None = None
    update_status: UpdateStatus | None = None
    docker_settings: DockerSettings | None = None
    vm_settings: VMSettings | None = None
    registration: RegistrationInfo | None = None
    network_services: NetworkServicesStatus | None = None
    unassigned_devices: list[UnassignedDevice] | None = None
    remote_shares: list[RemoteShare] | None = None
    container_updates: ContainerUpdatesResult | None = None
    diagnostics_self_test: DiagnosticsSelfTestResponse | None = None
    docker_port_conflicts: list[DockerPortConflict] | None = None
    # None when the agent has no /storage/topology endpoint or the fetch failed
    storage_topology: StorageTopology | None = None
    # None when network card devices are off, the agent has no /network/cards
    # endpoint, or the fetch failed
    network_cards: NICList | None = None
    # Data read inside configured VMs through the guest agent (/vm/guest).
    # None when VM devices are off, the agent has no such endpoint (404), or
    # the fetch failed; readings inside an entry are None while the VM is off.
    vm_guest: list[VMGuestInfo] | None = None
    # Alerting engine (agent /alerts/rules and /alerts/status). None when the
    # agent does not provide them (older agents: 404) or the fetch failed.
    alert_rules: list[AlertRule] | None = None
    alert_statuses: list[AlertStatus] | None = None
    # Running state of system services (docker, libvirt, nginx, ...) from
    # /services; None when the agent lacks the endpoint or the fetch failed
    system_services: list[SystemService] | None = None


def drop_replaced_vm_guests(
    guests: list[VMGuestInfo] | None,
    old_vms: list[VMInfo] | None,
    new_vms: list[VMInfo],
) -> list[VMGuestInfo] | None:
    """
    Return the guest records without those of VMs replaced under the same name.

    Guest records name their VM but carry no UUID. When a VM list update brings
    a VM with a known name but a new UUID, the cached record belongs to the old
    VM, so it is dropped until the agent reports the new VM's guest data.
    """
    if not guests:
        return guests
    old_ids = {vm.name: vm.id for vm in old_vms or []}
    replaced = {
        name
        for vm in new_vms
        if (name := vm.name) is not None and name in old_ids and old_ids[name] != vm.id
    }
    if not replaced:
        return guests
    return [guest for guest in guests if guest.vm_name not in replaced]


def merge_collector_state(
    status: CollectorStatus | None, details: CollectorDetails
) -> CollectorStatus | None:
    """
    Return the collectors status with one collector's details replaced.

    A collector_state_change event carries a single CollectorDetails, not the
    full CollectorStatus. Without a full status yet (no successful poll),
    keep None so collector checks fall back to their defaults. The agent's
    event has no required, error_count or last_run, so those are kept from
    the polled entry.
    """
    if status is None or not isinstance(details, CollectorDetails):
        return status
    changes = details.model_dump(
        include=set(CollectorDetails.model_fields), exclude_unset=True
    )
    collectors: list[CollectorDetails] = []
    found = False
    for collector in status.collectors or []:
        if collector.name == details.name:
            collectors.append(collector.model_copy(update=changes))
            found = True
        else:
            collectors.append(collector)
    if not found:
        collectors.append(details)
    # Recount like the agent's /collectors/status (enabled or still running)
    enabled = sum(1 for c in collectors if c.enabled or c.status == "running")
    return status.model_copy(
        update={
            "collectors": collectors,
            "total": len(collectors),
            "enabled_count": enabled,
            "disabled_count": len(collectors) - enabled,
        }
    )


def merge_nut(current: NUTInfo | None, incoming: NUTInfo) -> NUTInfo:
    """Keep known per-device lists when an older NUT event omits them."""
    if current is None:
        return incoming
    return incoming.model_copy(
        update={
            field: getattr(current, field)
            for field in ("statuses", "devices")
            if getattr(incoming, field) is None and getattr(current, field) is not None
        }
    )


def merge_notifications(
    current: NotificationsResponse | None,
    notifications: list[Notification],
    previous: NotificationsResponse | None = None,
) -> NotificationsResponse:
    """Replace the list while retaining the separately collected overview."""
    if not isinstance(current, NotificationsResponse):
        current = previous
    if isinstance(current, NotificationsResponse):
        update: dict[str, object] = {"notifications": notifications}
        if previous is not None and current.overview is None:
            update["overview"] = previous.overview
        return current.model_copy(update=update)
    return NotificationsResponse(
        notifications=notifications, overview=None, timestamp=None
    )


def call_recording_reads(func: Callable[[], object]) -> set[str]:
    """Call func and return the UnraidData fields it read, on any instance."""
    global _reads
    outer, _reads = _reads, set()
    try:
        func()
    finally:
        read, _reads = _reads, outer
        if outer is not None:
            outer.update(read)
    return read


def call_recording_writes[T](
    target: UnraidData | None, func: Callable[[], T]
) -> tuple[T, set[str]]:
    """Call func and return its result and the fields it wrote on target."""
    global _write_target, _writes
    outer = _write_target, _writes
    _write_target, _writes = target, set()
    try:
        result = func()
    finally:
        written = _writes
        _write_target, _writes = outer
    return result, written
