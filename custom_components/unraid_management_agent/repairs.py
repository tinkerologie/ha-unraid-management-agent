"""Repair flows for Unraid Management Agent integration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.components.repairs import RepairsFlow, RepairsFlowResult
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import issue_registry as ir

from .const import CONF_ACKNOWLEDGED_DISK_IO_ERRORS, DOMAIN

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry

    from .api.models import DiskInfo, ShareInfo
    from .coordinator import UnraidData, UnraidDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_create_fix_flow(
    hass: HomeAssistant,
    issue_id: str,
    data: dict[str, str | int | float | None] | None,
) -> RepairsFlow:
    """Create a fix flow for an issue."""
    if issue_id.startswith("connection_"):
        return ConnectionIssueRepairFlow(hass, issue_id, data)
    if issue_id.startswith("disk_health_") and issue_id.endswith("_io_errors"):
        return DiskIOErrorRepairFlow(hass, issue_id, data)
    if issue_id.startswith("disk_health_"):
        return DiskHealthRepairFlow(hass, issue_id, data)
    if issue_id.startswith("array_"):
        return ArrayIssueRepairFlow(hass, issue_id, data)
    if issue_id.startswith("parity_"):
        return ParityCheckRepairFlow(hass, issue_id, data)
    return RepairsFlow()


class ConnectionIssueRepairFlow(RepairsFlow):
    """Handler for connection issue repairs."""

    def __init__(
        self,
        hass: HomeAssistant,
        issue_id: str,
        data: dict[str, str | int | float | None] | None,
    ) -> None:
        """Initialize the repair flow."""
        super().__init__()
        self.hass = hass
        self.issue_id = issue_id
        self.data = data or {}

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> RepairsFlowResult:
        """Handle the initial step."""
        if user_input is not None:
            # Mark issue as resolved
            ir.async_delete_issue(self.hass, DOMAIN, self.issue_id)
            return self.async_create_entry(title="", data={})

        data = self.data or {}
        return self.async_show_form(
            step_id="init",
            description_placeholders={
                "error": str(data.get("error", "Unknown error")),
                "host": str(data.get("host", "Unknown")),
                "port": str(data.get("port", "Unknown")),
            },
        )


class DiskHealthRepairFlow(RepairsFlow):
    """Handler for disk health issue repairs."""

    def __init__(
        self,
        hass: HomeAssistant,
        issue_id: str,
        data: dict[str, str | int | float | None] | None,
    ) -> None:
        """Initialize the repair flow."""
        super().__init__()
        self.hass = hass
        self.issue_id = issue_id
        self.data = data or {}

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> RepairsFlowResult:
        """Handle the initial step."""
        if user_input is not None:
            # Mark issue as resolved
            ir.async_delete_issue(self.hass, DOMAIN, self.issue_id)
            return self.async_create_entry(title="", data={})

        data = self.data or {}
        return self.async_show_form(
            step_id="init",
            description_placeholders={
                "disk_name": str(data.get("disk_name", "Unknown")),
                "smart_status": str(data.get("smart_status", "Unknown")),
                "smart_errors": str(data.get("smart_errors", 0)),
                "temperature": str(data.get("temperature", "Unknown")),
            },
        )


class DiskIOErrorRepairFlow(RepairsFlow):
    """Acknowledge a disk's I/O error count without touching Unraid's statistics."""

    def __init__(
        self,
        hass: HomeAssistant,
        issue_id: str,
        data: dict[str, str | int | float | None] | None,
    ) -> None:
        """Initialize the repair flow."""
        super().__init__()
        self.hass = hass
        self.issue_id = issue_id
        self.data = data or {}

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> RepairsFlowResult:
        """Acknowledge the count shown in the issue, so a later increase warns."""
        data = self.data or {}
        if user_input is None:
            return self.async_show_form(
                step_id="init",
                description_placeholders={
                    "disk_name": str(data.get("disk_name", "Unknown")),
                    "io_errors": str(data.get("io_errors", "?")),
                },
            )

        entry = self.hass.config_entries.async_get_entry(str(data.get("entry_id")))
        physical_key = data.get("physical_key")
        count = data.get("io_errors")
        if entry is not None and isinstance(physical_key, str) and count is not None:
            acknowledged = dict(entry.options.get(CONF_ACKNOWLEDGED_DISK_IO_ERRORS, {}))
            acknowledged[physical_key] = count
            self.hass.config_entries.async_update_entry(
                entry,
                options={
                    **entry.options,
                    CONF_ACKNOWLEDGED_DISK_IO_ERRORS: acknowledged,
                },
            )
        ir.async_delete_issue(self.hass, DOMAIN, self.issue_id)
        return self.async_create_entry(title="", data={})


class ArrayIssueRepairFlow(RepairsFlow):
    """Handler for array issue repairs."""

    def __init__(
        self,
        hass: HomeAssistant,
        issue_id: str,
        data: dict[str, str | int | float | None] | None,
    ) -> None:
        """Initialize the repair flow."""
        super().__init__()
        self.hass = hass
        self.issue_id = issue_id
        self.data = data or {}

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> RepairsFlowResult:
        """Handle the initial step."""
        if user_input is not None:
            # Mark issue as resolved
            ir.async_delete_issue(self.hass, DOMAIN, self.issue_id)
            return self.async_create_entry(title="", data={})

        data = self.data or {}
        return self.async_show_form(
            step_id="init",
            description_placeholders={
                "array_state": str(data.get("array_state", "Unknown")),
                "issue_description": str(
                    data.get("issue_description", "Unknown issue")
                ),
            },
        )


class ParityCheckRepairFlow(RepairsFlow):
    """Handler for parity check issue repairs."""

    def __init__(
        self,
        hass: HomeAssistant,
        issue_id: str,
        data: dict[str, str | int | float | None] | None,
    ) -> None:
        """Initialize the repair flow."""
        super().__init__()
        self.hass = hass
        self.issue_id = issue_id
        self.data = data or {}

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> RepairsFlowResult:
        """Handle the initial step."""
        if user_input is not None:
            # Mark issue as resolved
            ir.async_delete_issue(self.hass, DOMAIN, self.issue_id)
            return self.async_create_entry(title="", data={})

        data = self.data or {}
        return self.async_show_form(
            step_id="init",
            description_placeholders={
                "parity_status": str(data.get("parity_status", "Unknown")),
                "sync_percent": str(data.get("sync_percent", 0)),
                "errors_found": str(data.get("errors_found", 0)),
            },
        )


async def async_check_and_create_issues(
    hass: HomeAssistant,
    coordinator: UnraidDataUpdateCoordinator,
    data: UnraidData | None = None,
) -> None:
    """
    Check for issues and create repair flows if needed.

    The coordinator passes the data it is about to return, since
    ``coordinator.data`` still holds the previous update at that point.
    """
    entry_id = coordinator.config_entry.entry_id

    # Check for connection issues
    if not coordinator.last_update_success:
        ir.async_create_issue(
            hass,
            DOMAIN,
            f"connection_{entry_id}",
            is_fixable=True,
            severity=ir.IssueSeverity.ERROR,
            translation_key="connection_failed",
            translation_placeholders={
                "host": coordinator.config_entry.data.get("host", "Unknown"),
                "port": str(coordinator.config_entry.data.get("port", "Unknown")),
                "error": (
                    str(coordinator.last_exception)
                    if coordinator.last_exception
                    else "Unknown error"
                ),
            },
        )
    else:
        # Connection is successful, remove any existing connection issue
        ir.async_delete_issue(hass, DOMAIN, f"connection_{entry_id}")

    if data is None:
        data = coordinator.data
    # Skip further checks if coordinator data is not available
    if not data:
        return

    # Get disk settings for temperature thresholds
    disk_settings = data.disk_settings

    # Check for disk health issues
    disks = data.disks or []
    stored_acknowledged = coordinator.config_entry.options.get(
        CONF_ACKNOWLEDGED_DISK_IO_ERRORS, {}
    )
    acknowledged = dict(stored_acknowledged)
    for disk in disks:
        disk_id = getattr(disk, "id", None) or getattr(disk, "name", None) or "unknown"

        # Issues from before SMART failures and I/O errors were separated
        ir.async_delete_issue(hass, DOMAIN, f"disk_health_{disk_id}_smart_errors")
        _check_disk_smart_failure(hass, entry_id, disk, disk_id)
        _check_disk_io_errors(hass, entry_id, disk, disk_id, acknowledged)

        # Get temperature status using library method
        temp_warning_issue_id = f"disk_health_{disk_id}_high_temp"
        temp_critical_issue_id = f"disk_health_{disk_id}_critical_temp"

        temp_status = disk.temperature_status(disk_settings)
        temperature = getattr(disk, "temperature_celsius", None) or 0

        if temp_status == "critical":
            warning_threshold, critical_threshold = disk.get_temp_thresholds(
                disk_settings
            )
            ir.async_create_issue(
                hass,
                DOMAIN,
                temp_critical_issue_id,
                is_fixable=True,
                severity=ir.IssueSeverity.ERROR,
                translation_key="disk_critical_temperature",
                translation_placeholders={
                    "disk_name": getattr(disk, "name", None) or disk_id,
                    "temperature": str(int(temperature)),
                    "threshold": str(critical_threshold) if critical_threshold else "?",
                },
            )
            # Remove warning issue if critical is active
            ir.async_delete_issue(hass, DOMAIN, temp_warning_issue_id)
        elif temp_status == "warning":
            warning_threshold, _critical_threshold = disk.get_temp_thresholds(
                disk_settings
            )
            ir.async_create_issue(
                hass,
                DOMAIN,
                temp_warning_issue_id,
                is_fixable=True,
                severity=ir.IssueSeverity.WARNING,
                translation_key="disk_high_temperature",
                translation_placeholders={
                    "disk_name": getattr(disk, "name", None) or disk_id,
                    "temperature": str(int(temperature)),
                    "threshold": str(warning_threshold) if warning_threshold else "?",
                },
            )
            # Remove critical issue if only warning
            ir.async_delete_issue(hass, DOMAIN, temp_critical_issue_id)
        else:
            # Temperature is normal, remove any existing issues
            ir.async_delete_issue(hass, DOMAIN, temp_warning_issue_id)
            ir.async_delete_issue(hass, DOMAIN, temp_critical_issue_id)

    if acknowledged != stored_acknowledged:
        _store_acknowledged_io_errors(hass, coordinator.config_entry, acknowledged)

    # Check for array issues (only if parity disks are configured)
    array_data = data.array
    num_parity_disks = (
        getattr(array_data, "num_parity_disks", None) if array_data else None
    )
    has_parity = num_parity_disks is not None and num_parity_disks > 0
    # Be strict about parity_valid - only consider it invalid if explicitly False
    # None, missing, or any other value should be treated as valid/unknown
    # Also skip if there are no parity disks (pools-only setups)
    parity_valid = getattr(array_data, "parity_valid", None) if array_data else None
    parity_issue_id = f"array_parity_invalid_{entry_id}"

    if has_parity and parity_valid is False:
        ir.async_create_issue(
            hass,
            DOMAIN,
            parity_issue_id,
            is_fixable=True,
            severity=ir.IssueSeverity.ERROR,
            translation_key="array_parity_invalid",
            translation_placeholders={
                "array_state": str(array_data.state)
                if array_data and array_data.state
                else "Unknown",
            },
        )
    else:
        # Parity is valid or unknown, remove any existing issue
        ir.async_delete_issue(hass, DOMAIN, parity_issue_id)

    # Check for parity check issues
    stuck_issue_id = f"parity_check_stuck_{entry_id}"

    if array_data and getattr(array_data, "is_parity_check_stuck", False):
        ir.async_create_issue(
            hass,
            DOMAIN,
            stuck_issue_id,
            is_fixable=True,
            severity=ir.IssueSeverity.WARNING,
            translation_key="parity_check_stuck",
            translation_placeholders={
                "sync_percent": str(
                    getattr(array_data, "parity_check_progress", 0) or 0
                ),
            },
        )
    else:
        # Parity check is not stuck, remove any existing issue
        ir.async_delete_issue(hass, DOMAIN, stuck_issue_id)

    _check_share_fuse_fallback(hass, coordinator.config_entry.entry_id, data.shares)


def _check_disk_smart_failure(
    hass: HomeAssistant, entry_id: str, disk: DiskInfo, disk_id: str
) -> None:
    """Raise an issue while a disk's SMART health status is FAILED."""
    issue_id = f"disk_health_{entry_id}_{disk_id}_smart_failure"
    if disk.has_smart_failure:
        ir.async_create_issue(
            hass,
            DOMAIN,
            issue_id,
            is_fixable=False,
            severity=ir.IssueSeverity.ERROR,
            translation_key="disk_smart_failure",
            translation_placeholders={
                "disk_name": disk.name or disk_id,
                "smart_status": str(disk.smart_status),
            },
        )
    elif disk.smart_status and disk.smart_status.upper() != "UNKNOWN":
        # A spun-down disk reports no status: that does not clear a failure
        ir.async_delete_issue(hass, DOMAIN, issue_id)


def _check_disk_io_errors(
    hass: HomeAssistant,
    entry_id: str,
    disk: DiskInfo,
    disk_id: str,
    acknowledged: dict[str, int],
) -> None:
    """
    Raise an issue while a disk's I/O error count exceeds its acknowledged count.

    A count below the acknowledged one means the counter was reset, so the
    acknowledgement is removed from ``acknowledged``. The agent reports a missing
    numErrors as 0, which looks like a reset too; the next positive count then
    warns again, which is the safe outcome.
    """
    current = disk.smart_errors
    if not isinstance(current, int):
        return  # Unavailable: keep the current state

    # A serial stays with the disk, so a replacement disk starts unacknowledged
    physical_key = disk.serial_number or disk.id
    issue_id = f"disk_health_{entry_id}_{disk_id}_io_errors"
    acknowledged_count = acknowledged.get(physical_key, 0) if physical_key else 0
    if current < acknowledged_count:
        acknowledged.pop(str(physical_key), None)
        acknowledged_count = 0

    if current <= acknowledged_count:
        ir.async_delete_issue(hass, DOMAIN, issue_id)
        return

    disk_name = disk.name or disk_id
    ir.async_create_issue(
        hass,
        DOMAIN,
        issue_id,
        data={
            "entry_id": entry_id,
            "physical_key": physical_key,
            "disk_name": disk_name,
            "io_errors": current,
        },
        is_fixable=physical_key is not None and physical_key != "",
        severity=ir.IssueSeverity.WARNING,
        translation_key="disk_io_errors",
        translation_placeholders={
            "disk_name": disk_name,
            "io_errors": str(current),
            "acknowledged": str(acknowledged_count),
        },
    )


def _store_acknowledged_io_errors(
    hass: HomeAssistant, entry: ConfigEntry, acknowledged: dict[str, int]
) -> None:
    """Persist the acknowledged counts in the config entry's options."""
    hass.config_entries.async_update_entry(
        entry,
        options={**entry.options, CONF_ACKNOWLEDGED_DISK_IO_ERRORS: acknowledged},
    )


def _check_share_fuse_fallback(
    hass: HomeAssistant, entry_id: str, shares: list[ShareInfo] | None
) -> None:
    """Raise an issue per exclusive-eligible share that fell back to FUSE."""
    if shares is None:
        # Share fetch failed this cycle; keep the current issues
        return

    prefix = _share_issue_prefix(entry_id)
    keep: set[str] = set()
    for share in shares:
        if not share.name:
            continue
        issue_id = f"{prefix}{share.name}"
        if not share.exclusive_state_known:
            # State unknown (array stopped, older agent, unreadable config):
            # leave any issue as is
            keep.add(issue_id)
            continue
        if not share.fuse_fallback:
            continue
        keep.add(issue_id)
        placeholders = {
            "share_name": share.name,
            "pool": share.exclusive_pool or share.cache_pool or "?",
        }
        if share.locations is None:
            # The agent could not scan the disks (disk list unavailable)
            translation_key = "share_fuse_fallback_unknown"
        elif stray := share.stray_locations:
            placeholders["locations"] = ", ".join(stray)
            if share.locations_unchecked:
                # Spun-down disks may hold more stray folders
                translation_key = "share_fuse_fallback_stray_unchecked"
                placeholders["unchecked"] = ", ".join(share.locations_unchecked)
            else:
                translation_key = "share_fuse_fallback"
        elif share.locations_unchecked:
            # The agent leaves spun-down disks unchecked rather than wake them
            translation_key = "share_fuse_fallback_unchecked"
            placeholders["unchecked"] = ", ".join(share.locations_unchecked)
        else:
            translation_key = "share_fuse_fallback_restart"
        ir.async_create_issue(
            hass,
            DOMAIN,
            issue_id,
            is_fixable=False,
            severity=ir.IssueSeverity.WARNING,
            translation_key=translation_key,
            translation_placeholders=placeholders,
        )

    # Clear issues for shares that are exclusive again or no longer exist
    async_delete_share_issues(hass, entry_id, keep)


def _share_issue_prefix(entry_id: str) -> str:
    """Return the issue ID prefix of a config entry's share issues."""
    return f"share_fuse_fallback_{entry_id}_"


@callback
def async_delete_share_issues(
    hass: HomeAssistant, entry_id: str, keep: set[str] | None = None
) -> None:
    """Delete a config entry's share FUSE fallback issues, except ``keep``."""
    prefix = _share_issue_prefix(entry_id)
    for domain, issue_id in list(ir.async_get(hass).issues):
        if (
            domain == DOMAIN
            and issue_id.startswith(prefix)
            and issue_id not in (keep or ())
        ):
            ir.async_delete_issue(hass, DOMAIN, issue_id)


@callback
def async_delete_disk_issues(hass: HomeAssistant, entry_id: str) -> None:
    """Delete a config entry's SMART failure and I/O error issues."""
    prefix = f"disk_health_{entry_id}_"
    for domain, issue_id in list(ir.async_get(hass).issues):
        if domain == DOMAIN and issue_id.startswith(prefix):
            ir.async_delete_issue(hass, DOMAIN, issue_id)
