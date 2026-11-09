"""Read-only transport ports used by telemetry reconciliation."""

from __future__ import annotations

from typing import Protocol

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


class UnraidTelemetrySource(Protocol):
    """REST data consumed by a telemetry refresh."""

    async def get_system_info(self) -> SystemInfo:
        """Get system info."""
        ...

    async def get_array_status(self) -> ArrayStatus:
        """Get array status."""
        ...

    async def list_disks(self) -> list[DiskInfo]:
        """List disks."""
        ...

    async def list_containers(self) -> list[ContainerInfo]:
        """List containers."""
        ...

    async def list_vms(self) -> list[VMInfo]:
        """List vms."""
        ...

    async def get_ups_info(self) -> UPSInfo:
        """Get ups info."""
        ...

    async def list_gpus(self) -> list[GPUInfo]:
        """List gpus."""
        ...

    async def list_network_interfaces(self) -> list[NetworkInterface]:
        """List network interfaces."""
        ...

    async def list_shares(self) -> list[ShareInfo]:
        """List shares."""
        ...

    async def list_notifications(self) -> NotificationsResponse:
        """List notifications."""
        ...

    async def get_notification_overview(self) -> NotificationOverview:
        """Get notification overview."""
        ...

    async def list_user_scripts(self) -> list[UserScript]:
        """List user scripts."""
        ...

    async def list_zfs_pools(self) -> list[ZFSPool]:
        """List zfs pools."""
        ...

    async def get_zfs_arc_stats(self) -> ZFSArcStats:
        """Get zfs arc stats."""
        ...

    async def get_collectors_status(self) -> CollectorStatus:
        """Get collectors status."""
        ...

    async def get_fan_status(self) -> FanControlStatus:
        """Get fan status."""
        ...

    async def get_disk_settings(self) -> DiskSettings:
        """Get disk settings."""
        ...

    async def get_mover_settings(self) -> MoverSettings:
        """Get mover settings."""
        ...

    async def get_parity_schedule(self) -> ParitySchedule:
        """Get parity schedule."""
        ...

    async def get_parity_history(self) -> ParityHistory:
        """Get parity history."""
        ...

    async def get_flash_info(self) -> FlashDriveInfo:
        """Get flash info."""
        ...

    async def list_plugins(self) -> PluginList:
        """List plugins."""
        ...

    async def get_update_status(self) -> UpdateStatus:
        """Get update status."""
        ...

    async def get_docker_settings(self) -> DockerSettings:
        """Get docker settings."""
        ...

    async def get_vm_settings(self) -> VMSettings:
        """Get vm settings."""
        ...

    async def get_registration_info(self) -> RegistrationInfo:
        """Get registration info."""
        ...

    async def get_network_services(self) -> NetworkServicesStatus:
        """Get network services."""
        ...

    async def get_unassigned_info(self) -> UnassignedInfo:
        """Get unassigned info."""
        ...

    async def get_diagnostics_self_test(self) -> DiagnosticsSelfTestResponse:
        """Get diagnostics self test."""
        ...

    async def get_docker_port_conflicts(self) -> list[DockerPortConflict]:
        """Get docker port conflicts."""
        ...

    async def list_services(self) -> SystemServiceList:
        """List services."""
        ...

    async def list_alert_rules(self) -> list[AlertRule]:
        """List alert rules."""
        ...

    async def get_alerts_status(self) -> AlertsStatusResponse:
        """Get alerts status."""
        ...

    async def get_storage_topology(self) -> StorageTopology:
        """Get storage topology."""
        ...

    async def get_nut_info(self) -> NUTInfo:
        """Get nut info."""
        ...

    async def get_network_cards(self) -> NICList:
        """Get network cards."""
        ...

    async def get_vm_guest(self) -> list[VMGuestInfo]:
        """Get vm guest."""
        ...

    async def check_all_container_updates(self) -> ContainerUpdatesResult:
        """Check all container updates."""
        ...


class TopicSubscription(Protocol):
    """A WebSocket connection's currently sent topic filter."""

    @property
    def subscribed_topics(self) -> list[str] | None:
        """Get the currently sent topics, or None when unfiltered."""
        ...

    async def set_topics(self, topics: list[str] | None) -> None:
        """Set topics."""
        ...
