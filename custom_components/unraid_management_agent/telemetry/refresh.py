"""Typed REST fetch plan and telemetry snapshot assembly."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass, fields
from typing import Any

from custom_components.unraid_management_agent.api.exceptions import (
    UnraidAuthenticationError,
    UnraidNotFoundError,
    UnraidTimeoutError,
)
from custom_components.unraid_management_agent.api.models import (
    AlertRule,
    AlertsStatusResponse,
    ArrayStatus,
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
    NotificationOverview,
    NotificationsResponse,
    NUTInfo,
    ParityHistory,
    ParitySchedule,
    PluginList,
    RegistrationInfo,
    ShareInfo,
    StorageTopology,
    SystemInfo,
    SystemServiceList,
    UnassignedInfo,
    UpdateStatus,
    UPSInfo,
    UserScript,
    VMGuestInfo,
    VMInfo,
    VMSettings,
    ZFSArcStats,
    ZFSPool,
)
from custom_components.unraid_management_agent.collection import TOPIC_SOURCES
from custom_components.unraid_management_agent.const import (
    CONF_ENABLE_CONTAINER_UPDATES,
    CONF_ENABLE_NIC_DEVICES,
    CONF_ENABLE_VM_DEVICES,
    DEFAULT_ENABLE_CONTAINER_UPDATES,
    DEFAULT_ENABLE_NIC_DEVICES,
    DEFAULT_ENABLE_VM_DEVICES,
)

from .ports import UnraidTelemetrySource
from .state import UnraidData

_LOGGER = logging.getLogger(__name__)


@dataclass
class Fetch[T]:
    """One typed read, including skip policy and its eventual value."""

    label: str
    read: Callable[[], Awaitable[T | None]]
    suppress_404: bool = False
    skip_key: str | None = None
    retained: T | None = None
    enabled: bool = True
    value: T | None = None

    async def run(self, skipped: frozenset[str] = frozenset()) -> None:
        """Read once or retain the captured value for a skipped field."""
        if not self.enabled:
            return
        if self.skip_key in skipped:
            self.value = self.retained
            return
        try:
            self.value = await self.read()
        except UnraidAuthenticationError:
            raise
        except UnraidTimeoutError as err:
            _LOGGER.debug("Timeout fetching %s: %s", self.label, err)
        except Exception as err:
            if self.suppress_404 and (
                isinstance(err, UnraidNotFoundError) or "404" in str(err)
            ):
                return
            _LOGGER.debug("Error fetching %s: %s", self.label, err)


@dataclass
class RefreshPlan:
    """Named REST results, independent of the order requests finish."""

    system: Fetch[SystemInfo]
    array: Fetch[ArrayStatus]
    disks: Fetch[list[DiskInfo]]
    containers: Fetch[list[ContainerInfo]]
    vms: Fetch[list[VMInfo]]
    ups: Fetch[UPSInfo]
    gpu: Fetch[list[GPUInfo]]
    network: Fetch[list[NetworkInterface]]
    shares: Fetch[list[ShareInfo]]
    notifications: Fetch[NotificationsResponse | list[Notification]]
    notification_overview: Fetch[NotificationOverview]
    user_scripts: Fetch[list[UserScript]]
    zfs_pools: Fetch[list[ZFSPool]]
    zfs_arc: Fetch[ZFSArcStats]
    collectors: Fetch[CollectorStatus]
    fan_control: Fetch[FanControlStatus]
    disk_settings: Fetch[DiskSettings]
    mover_settings: Fetch[MoverSettings]
    parity_schedule: Fetch[ParitySchedule]
    parity_history: Fetch[ParityHistory]
    flash_info: Fetch[FlashDriveInfo]
    plugins: Fetch[PluginList]
    update_status: Fetch[UpdateStatus]
    docker_settings: Fetch[DockerSettings]
    vm_settings: Fetch[VMSettings]
    registration: Fetch[RegistrationInfo]
    network_services: Fetch[NetworkServicesStatus]
    unassigned_info: Fetch[UnassignedInfo]
    diagnostics_self_test: Fetch[DiagnosticsSelfTestResponse]
    docker_port_conflicts: Fetch[list[DockerPortConflict]]
    system_service_list: Fetch[SystemServiceList]
    alert_rules: Fetch[list[AlertRule]]
    alerts_status: Fetch[AlertsStatusResponse]
    storage_topology: Fetch[StorageTopology]
    nut: Fetch[NUTInfo]
    network_cards: Fetch[NICList]
    vm_guest: Fetch[list[VMGuestInfo]]
    container_updates: Fetch[ContainerUpdatesResult]

    def initial_reads(self) -> tuple[Fetch[Any], ...]:
        """Return the reads allowed before checking server reachability."""
        return tuple(
            getattr(self, field.name)
            for field in fields(self)
            if field.name != "container_updates"
        )


def build_plan(
    source: UnraidTelemetrySource,
    current: UnraidData | None,
    options: Mapping[str, Any],
    parity_history: Callable[[], Awaitable[ParityHistory | None]],
) -> RefreshPlan:
    """Capture the current values and policy for a single poll."""
    plan = RefreshPlan(
        system=Fetch(
            "system info",
            source.get_system_info,
            skip_key="system",
            retained=current.system if current else None,
        ),
        array=Fetch(
            "array status",
            source.get_array_status,
            skip_key="array",
            retained=current.array if current else None,
        ),
        disks=Fetch(
            "disks",
            source.list_disks,
            skip_key="disks",
            retained=current.disks if current else None,
        ),
        containers=Fetch(
            "containers",
            source.list_containers,
            skip_key="containers",
            retained=current.containers if current else None,
        ),
        vms=Fetch(
            "VMs",
            source.list_vms,
            skip_key="vms",
            retained=current.vms if current else None,
        ),
        ups=Fetch(
            "UPS status",
            source.get_ups_info,
            skip_key="ups",
            retained=current.ups if current else None,
        ),
        gpu=Fetch(
            "GPU metrics",
            source.list_gpus,
            suppress_404=True,
            skip_key="gpu",
            retained=current.gpu if current else None,
        ),
        network=Fetch(
            "network interfaces",
            source.list_network_interfaces,
            skip_key="network",
            retained=current.network if current else None,
        ),
        shares=Fetch(
            "shares",
            source.list_shares,
            skip_key="shares",
            retained=current.shares if current else None,
        ),
        notifications=Fetch(
            "notifications",
            source.list_notifications,
            skip_key="notifications",
            retained=current.notifications if current else None,
        ),
        notification_overview=Fetch(
            "notification overview",
            source.get_notification_overview,
            skip_key="notifications",
        ),
        user_scripts=Fetch("user scripts", source.list_user_scripts),
        zfs_pools=Fetch(
            "ZFS pools",
            source.list_zfs_pools,
            skip_key="zfs_pools",
            retained=current.zfs_pools if current else None,
        ),
        zfs_arc=Fetch(
            "ZFS ARC stats",
            source.get_zfs_arc_stats,
            suppress_404=True,
            skip_key="zfs_arc",
            retained=current.zfs_arc if current else None,
        ),
        collectors=Fetch("collectors status", source.get_collectors_status),
        fan_control=Fetch(
            "fan control status",
            source.get_fan_status,
            suppress_404=True,
            skip_key="fan_control",
            retained=current.fan_control if current else None,
        ),
        disk_settings=Fetch("disk settings", source.get_disk_settings),
        mover_settings=Fetch("mover settings", source.get_mover_settings),
        parity_schedule=Fetch("parity schedule", source.get_parity_schedule),
        parity_history=Fetch("parity history", parity_history),
        flash_info=Fetch("flash info", source.get_flash_info),
        plugins=Fetch("plugins", source.list_plugins),
        update_status=Fetch("update status", source.get_update_status),
        docker_settings=Fetch("docker settings", source.get_docker_settings),
        vm_settings=Fetch("VM settings", source.get_vm_settings),
        registration=Fetch("registration info", source.get_registration_info),
        network_services=Fetch("network services", source.get_network_services),
        unassigned_info=Fetch(
            "unassigned devices", source.get_unassigned_info, suppress_404=True
        ),
        diagnostics_self_test=Fetch(
            "diagnostics self-test", source.get_diagnostics_self_test, suppress_404=True
        ),
        docker_port_conflicts=Fetch(
            "docker port conflicts", source.get_docker_port_conflicts, suppress_404=True
        ),
        system_service_list=Fetch(
            "system services", source.list_services, suppress_404=True
        ),
        alert_rules=Fetch("alert rules", source.list_alert_rules, suppress_404=True),
        alerts_status=Fetch(
            "alert status", source.get_alerts_status, suppress_404=True
        ),
        storage_topology=Fetch(
            "storage topology", source.get_storage_topology, suppress_404=True
        ),
        nut=Fetch(
            "NUT status",
            source.get_nut_info,
            suppress_404=True,
            skip_key="nut",
            retained=current.nut if current else None,
        ),
        network_cards=Fetch(
            "network cards",
            source.get_network_cards,
            suppress_404=True,
            enabled=bool(
                options.get(CONF_ENABLE_NIC_DEVICES, DEFAULT_ENABLE_NIC_DEVICES)
            ),
        ),
        vm_guest=Fetch(
            "VM guest data",
            source.get_vm_guest,
            suppress_404=True,
            skip_key="vm_guest",
            retained=current.vm_guest if current else None,
            enabled=bool(
                options.get(CONF_ENABLE_VM_DEVICES, DEFAULT_ENABLE_VM_DEVICES)
            ),
        ),
        container_updates=Fetch(
            "container updates",
            source.check_all_container_updates,
            suppress_404=True,
            enabled=bool(
                options.get(
                    CONF_ENABLE_CONTAINER_UPDATES, DEFAULT_ENABLE_CONTAINER_UPDATES
                )
            ),
        ),
    )
    declared = {slot.skip_key for slot in plan.initial_reads()}
    covered = {key for _, field_names in TOPIC_SOURCES.values() for key in field_names}
    if not covered <= declared:
        msg = "A WebSocket-covered field is missing from the poll plan"
        raise RuntimeError(msg)
    return plan


_DERIVED_FIELDS = {
    "unassigned_devices",
    "remote_shares",
    "system_services",
    "alert_statuses",
}
_EVENT_ONLY_FIELDS = {"zfs_datasets", "zfs_snapshots"}
_INTERMEDIATE_READS = {
    "notification_overview",
    "unassigned_info",
    "system_service_list",
    "alerts_status",
}
_OWNED_FIELDS = (
    ({field.name for field in fields(RefreshPlan)} - _INTERMEDIATE_READS)
    | _DERIVED_FIELDS
    | _EVENT_ONLY_FIELDS
)
if {field.name for field in fields(UnraidData)} != _OWNED_FIELDS:
    msg = "The telemetry plan must account for each snapshot field"
    raise RuntimeError(msg)


def assemble(plan: RefreshPlan, current: UnraidData | None) -> UnraidData:
    """Build the published snapshot while preserving unknown versus empty data."""
    notifications = plan.notifications.value
    overview = plan.notification_overview.value
    if isinstance(notifications, list):
        notifications = NotificationsResponse(
            notifications=notifications, overview=None, timestamp=None
        )
    if overview is not None:
        if notifications is None:
            notifications = NotificationsResponse(
                overview=overview, notifications=None, timestamp=None
            )
        else:
            notifications = notifications.model_copy(update={"overview": overview})
    unassigned_info = plan.unassigned_info.value
    system_service_list = plan.system_service_list.value
    alerts_status = plan.alerts_status.value
    return UnraidData(
        system=plan.system.value,
        array=plan.array.value,
        disks=plan.disks.value,
        containers=plan.containers.value,
        vms=plan.vms.value,
        ups=plan.ups.value,
        nut=plan.nut.value,
        gpu=plan.gpu.value,
        network=plan.network.value,
        shares=plan.shares.value,
        notifications=notifications,
        user_scripts=plan.user_scripts.value,
        zfs_pools=plan.zfs_pools.value,
        # Not polled (no entity uses them); keep values from WebSocket
        zfs_datasets=current.zfs_datasets if current else None,
        zfs_snapshots=current.zfs_snapshots if current else None,
        zfs_arc=plan.zfs_arc.value,
        collectors=plan.collectors.value,
        fan_control=plan.fan_control.value,
        disk_settings=plan.disk_settings.value,
        mover_settings=plan.mover_settings.value,
        parity_schedule=plan.parity_schedule.value,
        parity_history=plan.parity_history.value,
        flash_info=plan.flash_info.value,
        plugins=plan.plugins.value,
        update_status=plan.update_status.value,
        docker_settings=plan.docker_settings.value,
        vm_settings=plan.vm_settings.value,
        registration=plan.registration.value,
        network_services=plan.network_services.value,
        unassigned_devices=list(unassigned_info.devices or [])
        if unassigned_info
        else None,
        remote_shares=list(unassigned_info.remote_shares or [])
        if unassigned_info
        else None,
        container_updates=plan.container_updates.value,
        diagnostics_self_test=plan.diagnostics_self_test.value,
        docker_port_conflicts=plan.docker_port_conflicts.value,
        # A null service list is treated like a failed fetch (None)
        system_services=list(system_service_list.services)
        if system_service_list and system_service_list.services is not None
        else None,
        alert_rules=plan.alert_rules.value,
        # The agent sends "statuses": null when no rule is enabled
        alert_statuses=list(alerts_status.statuses or [])
        if alerts_status is not None
        else None,
        storage_topology=plan.storage_topology.value,
        network_cards=plan.network_cards.value,
        vm_guest=plan.vm_guest.value,
    )
