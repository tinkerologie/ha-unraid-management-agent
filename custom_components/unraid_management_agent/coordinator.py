"""Coordinator for Unraid Management Agent."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import UnraidClient
from .api.events import WebSocketEvent, parse_event
from .api.exceptions import UnraidAuthenticationError
from .api.websocket import UnraidWebSocketClient
from .collection import collection_mode as agent_collection_mode
from .collection import subscription_topics
from .const import (
    CONF_ENABLE_CONTAINER_DEVICES,
    CONF_ENABLE_CONTAINER_UPDATES,
    CONF_ENABLE_FAN_CONTROL,
    CONF_ENABLE_GPU_DEVICES,
    CONF_ENABLE_HWMON_DEVICES,
    CONF_ENABLE_NIC_DEVICES,
    CONF_ENABLE_VM_DEVICES,
    CONF_ENABLE_ZFS_POOL_DEVICES,
    DEFAULT_ENABLE_CONTAINER_DEVICES,
    DEFAULT_ENABLE_CONTAINER_UPDATES,
    DEFAULT_ENABLE_FAN_CONTROL,
    DEFAULT_ENABLE_GPU_DEVICES,
    DEFAULT_ENABLE_HWMON_DEVICES,
    DEFAULT_ENABLE_NIC_DEVICES,
    DEFAULT_ENABLE_VM_DEVICES,
    DEFAULT_ENABLE_ZFS_POOL_DEVICES,
    DOMAIN,
    UPDATE_INTERVAL,
)
from .telemetry import EventOutcome, UnraidTelemetryReconciler
from .telemetry import UnraidData as UnraidData  # noqa: PLC0414 - compatibility export
from .telemetry.reconciler import AgentUnavailableError

_LOGGER = logging.getLogger(__name__)

# Warn after this many consecutive failed update cycles (likely plugin stall).
_FAILED_UPDATE_WARN_THRESHOLD = 3

# Minimum time between coordinator refreshes triggered by WebSocket reconnects,
# so rapid connect/disconnect cycles don't hammer the API.
_RECONNECT_REFRESH_DEBOUNCE = timedelta(seconds=10)


def has_no_array_disks(data: UnraidData | None) -> bool:
    """
    Return True when the server has no Unraid array disks (pool-only server).

    Only an explicit report of zero data disks and zero parity disks counts.
    Missing array data or missing counts mean "unknown" and return False, so a
    failed fetch never hides parity support on a server that has an array.
    """
    return array_disks_absent(data) is True


def array_disks_absent(data: UnraidData | None) -> bool | None:
    """
    Return whether the server has no Unraid array disks, or None if unknown.

    None means the array data or its disk counts are missing (for example a
    failed fetch), so callers can tell "unknown" apart from a known answer.
    """
    if data is None or data.array is None:
        return None
    num_data = data.array.num_data_disks
    num_parity = data.array.num_parity_disks
    if num_data is None or num_parity is None:
        return None
    return num_data == 0 and num_parity == 0


@dataclass
class UnraidRuntimeData:
    """Runtime data for Unraid Management Agent."""

    coordinator: UnraidDataUpdateCoordinator
    client: UnraidClient
    # Platforms forwarded at setup (fewer in read-only mode); unload uses the same list
    platforms: list[Platform]


type UnraidConfigEntry = ConfigEntry[UnraidRuntimeData]


class UnraidDataUpdateCoordinator(DataUpdateCoordinator[UnraidData]):
    """Class to manage fetching Unraid data from the API."""

    config_entry: UnraidConfigEntry
    update_success: bool = False

    def __init__(
        self,
        hass: HomeAssistant,
        entry: UnraidConfigEntry,
        client: UnraidClient,
        enable_websocket: bool,
    ) -> None:
        """Initialize the coordinator."""
        self.client = client
        self.enable_websocket = enable_websocket
        self._ws_client: UnraidWebSocketClient | None = None
        self._ws_task: asyncio.Task[None] | None = None
        self._websocket_disconnect_logged = False
        self._unavailable_logged = False
        self._consecutive_failed_updates = 0
        self._last_successful_update: datetime | None = None
        # Seed with the current time so the initial WebSocket connection during
        # setup doesn't trigger a refresh right after the first data fetch.
        self._last_reconnect_refresh: datetime | None = dt_util.utcnow()
        # Tracks when each dynamic entity unique_id was first seen missing from
        # coordinator data; used by cleanup.py to defer removal until the item
        # has been absent for a sustained period (not just one bad poll).
        self.stale_entity_candidates: dict[str, datetime] = {}
        self._pending_system_action: str | None = None
        self._pending_system_action_message: str | None = None
        self._pending_system_action_requested_at: datetime | None = None
        self._pending_system_action_disconnected = False
        self._previous_uptime_seconds: int | None = None
        self._last_reboot_detected_at: datetime | None = None
        self._telemetry = UnraidTelemetryReconciler(client)

        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )

    async def _async_setup(self) -> None:
        """
        Set up the coordinator.

        This is called once during async_config_entry_first_refresh.
        Use for one-time initialization that requires async operations.

        Note: Connection health is already verified in async_setup_entry,
        so we don't need to check it again here.
        """

    @property
    def websocket_connected(self) -> bool:
        """Return True if websocket is connected."""
        return self._ws_client is not None and self._ws_client.is_connected

    @property
    def collection_mode(self) -> str | None:
        """Return the agent's collection mode: "dynamic", "manual" or None (older agent)."""
        return agent_collection_mode(self.data.collectors if self.data else None)

    @property
    def websocket_topics(self) -> list[str] | None:
        """Return the WebSocket topic filter in use; None means every topic."""
        return self._ws_client.subscribed_topics if self._ws_client else None

    @property
    def last_successful_update(self) -> datetime | None:
        """Return the timestamp of the last successful data fetch."""
        return self._last_successful_update

    @property
    def consecutive_failed_updates(self) -> int:
        """Return the number of consecutive failed update cycles."""
        return self._consecutive_failed_updates

    @property
    def in_reboot_grace_period(self) -> bool:
        """
        Return True if we're in the grace period after a server reboot.

        During this period, stale entity cleanup is suppressed to allow APIs
        to stabilize and return complete data.

        Returns:
            True if a reboot was detected within the last 5 minutes.

        """
        if self._last_reboot_detected_at is None:
            return False
        grace_period = timedelta(minutes=5)
        return dt_util.utcnow() - self._last_reboot_detected_at < grace_period

    @property
    def pending_system_action(self) -> str | None:
        """Return the pending reboot or shutdown action, if any."""
        return self._pending_system_action

    @property
    def pending_system_action_message(self) -> str | None:
        """Return the last action response message for the pending system action."""
        return self._pending_system_action_message

    @property
    def pending_system_action_requested_at(self) -> datetime | None:
        """Return when the current pending system action was requested."""
        return self._pending_system_action_requested_at

    def set_pending_system_action(
        self,
        action: str,
        message: str | None = None,
    ) -> None:
        """Track a reboot or shutdown action requested through the integration."""
        self._pending_system_action = action
        self._pending_system_action_message = message
        self._pending_system_action_requested_at = dt_util.utcnow()
        self._pending_system_action_disconnected = False
        self.async_update_listeners()

    def _clear_pending_system_action(self) -> None:
        """Clear any pending reboot or shutdown action state."""
        self._pending_system_action = None
        self._pending_system_action_message = None
        self._pending_system_action_requested_at = None
        self._pending_system_action_disconnected = False

    @property
    def system_status(self) -> str:
        """Return a high-level status string for the Unraid system."""
        data = self.data
        array_state = (
            getattr(data.array, "state", None) if data and data.array else None
        )
        normalized_array_state = (
            str(array_state).lower() if array_state is not None else None
        )

        if self._pending_system_action == "shutdown":
            if not self.last_update_success or data is None:
                return "server_shutdown"
            if normalized_array_state == "stopping":
                return "stopping_array"
            if normalized_array_state == "stopped":
                return "shutting_down"
            return "shutdown_requested"

        if self._pending_system_action == "reboot":
            if not self.last_update_success or data is None:
                return "server_rebooting"
            if normalized_array_state == "stopping":
                return "stopping_array"
            if normalized_array_state == "stopped":
                return "server_rebooting"
            return "reboot_requested"

        if not self.last_update_success:
            return "offline"

        if normalized_array_state == "starting":
            return "starting_array"
        if normalized_array_state == "stopping":
            return "stopping_array"
        if normalized_array_state == "stopped":
            return "array_stopped"
        return "online"

    def is_collector_enabled(self, collector_name: str) -> bool:
        """
        Check if a specific collector is enabled.

        Args:
            collector_name: Name of the collector (e.g., 'docker', 'vm', 'ups', 'gpu', 'zfs')

        Returns:
            True if collector is enabled or if collectors status is unavailable (default to enabled)

        """
        if not self.data or not self.data.collectors:
            # If we can't determine collector status, default to enabled
            return True

        collector = self.data.collectors.get_collector_by_name(collector_name)
        if collector is not None:
            return getattr(collector, "enabled", True)

        # Collector not found in list, default to enabled
        return True

    def is_docker_enabled(self) -> bool:
        """
        Check if Docker service is enabled in Unraid settings.

        Returns:
            True if Docker is enabled, False if explicitly disabled,
            or True if settings are unavailable (default to enabled)

        """
        if not self.data or not self.data.docker_settings:
            # If we can't determine, default to enabled for backwards compatibility
            return True
        return getattr(self.data.docker_settings, "enabled", True)

    def is_container_updates_enabled(self) -> bool:
        """
        Check if container update checking is enabled in options.

        Returns:
            True if container updates should be fetched and exposed as entities.

        """
        return self.config_entry.options.get(
            CONF_ENABLE_CONTAINER_UPDATES, DEFAULT_ENABLE_CONTAINER_UPDATES
        )

    def is_fan_control_enabled(self) -> bool:
        """Return True when fan control is enabled in options."""
        return bool(
            self.config_entry.options.get(
                CONF_ENABLE_FAN_CONTROL, DEFAULT_ENABLE_FAN_CONTROL
            )
        )

    def is_container_devices_enabled(self) -> bool:
        """Return True when containers are shown as separate devices."""
        return bool(
            self.config_entry.options.get(
                CONF_ENABLE_CONTAINER_DEVICES, DEFAULT_ENABLE_CONTAINER_DEVICES
            )
        )

    def is_vm_devices_enabled(self) -> bool:
        """Return True when VMs are shown as separate devices."""
        return bool(
            self.config_entry.options.get(
                CONF_ENABLE_VM_DEVICES, DEFAULT_ENABLE_VM_DEVICES
            )
        )

    def is_gpu_devices_enabled(self) -> bool:
        """Return True when GPUs are shown as separate devices."""
        return bool(
            self.config_entry.options.get(
                CONF_ENABLE_GPU_DEVICES, DEFAULT_ENABLE_GPU_DEVICES
            )
        )

    def is_hwmon_devices_enabled(self) -> bool:
        """Return True when hwmon controllers are shown as separate devices."""
        return bool(
            self.config_entry.options.get(
                CONF_ENABLE_HWMON_DEVICES, DEFAULT_ENABLE_HWMON_DEVICES
            )
        )

    def is_zfs_pool_devices_enabled(self) -> bool:
        """Return True when ZFS pools are shown as separate devices."""
        return bool(
            self.config_entry.options.get(
                CONF_ENABLE_ZFS_POOL_DEVICES, DEFAULT_ENABLE_ZFS_POOL_DEVICES
            )
        )

    def is_nic_devices_enabled(self) -> bool:
        """Return True when network cards are shown as separate devices (options)."""
        return bool(
            self.config_entry.options.get(
                CONF_ENABLE_NIC_DEVICES, DEFAULT_ENABLE_NIC_DEVICES
            )
        )

    def is_vm_enabled(self) -> bool:
        """
        Check if VM service is enabled in Unraid settings.

        Returns:
            True if VM service is enabled, False if explicitly disabled,
            or True if settings are unavailable (default to enabled)

        """
        if not self.data or not self.data.vm_settings:
            # If we can't determine, default to enabled for backwards compatibility
            return True
        return getattr(self.data.vm_settings, "enabled", True)

    async def _async_update_data(self) -> UnraidData:
        """Fetch and publish telemetry for this configured server."""
        try:
            result = await self._telemetry.refresh(
                self.data, self.config_entry.options, self._ws_client
            )
            data = result.snapshot
            system = data.system

            # Log recovery if we were previously unavailable
            if self._unavailable_logged:
                _LOGGER.info("Connection to Unraid server restored")
                self._unavailable_logged = False

            if self._pending_system_action and self._pending_system_action_disconnected:
                _LOGGER.info(
                    "Clearing pending system %s action after server became reachable again",
                    self._pending_system_action,
                )
                self._clear_pending_system_action()

            # Mark update as successful
            self.update_success = True
            self._consecutive_failed_updates = 0
            self._last_successful_update = dt_util.utcnow()

            # Detect if the server rebooted by checking if uptime decreased
            if system and system.uptime_seconds is not None:
                current_uptime = system.uptime_seconds
                if (
                    self._previous_uptime_seconds is not None
                    and current_uptime < self._previous_uptime_seconds
                ):
                    # Uptime decreased - server rebooted
                    _LOGGER.warning(
                        "Server reboot detected (uptime was %d seconds, now %d seconds). "
                        "Suppressing stale entity cleanup for 5 minutes to allow APIs to stabilize.",
                        self._previous_uptime_seconds,
                        current_uptime,
                    )
                    self._last_reboot_detected_at = dt_util.utcnow()
                self._previous_uptime_seconds = current_uptime

            return data
        except AgentUnavailableError as err:
            if not self._unavailable_logged:
                _LOGGER.warning(
                    "Unraid server is unreachable (core endpoints returned no data)"
                )
                self._unavailable_logged = True
            self._record_failed_update()
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="api_error",
            ) from err
        except UnraidAuthenticationError as err:
            self._record_failed_update()
            raise ConfigEntryAuthFailed(
                translation_domain=DOMAIN,
                translation_key="auth_failed",
            ) from err

        except Exception as err:
            # Log unavailable only once
            if not self._unavailable_logged:
                _LOGGER.warning("Error communicating with Unraid API: %s", err)
                self._unavailable_logged = True
            self._record_failed_update()
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="api_error",
            ) from err

    def _record_failed_update(self) -> None:
        """Track a failed update cycle and warn on sustained failures."""
        if self._pending_system_action:
            self._pending_system_action_disconnected = True
        self.update_success = False
        self._consecutive_failed_updates += 1
        if self._consecutive_failed_updates == _FAILED_UPDATE_WARN_THRESHOLD:
            _LOGGER.warning(
                "Unraid data fetch has failed %d times in a row. The Unraid "
                "Management Agent plugin may be stalled or unreachable; check "
                "its status on the Unraid server (Settings > Management Agent)",
                self._consecutive_failed_updates,
            )

    def _handle_websocket_event(self, event: WebSocketEvent) -> None:
        """Apply the parsed event without resetting the polling timer."""
        match self._telemetry.apply_event(self.data, event):
            case EventOutcome.APPLIED:
                self.async_update_listeners()
            case EventOutcome.REFRESH_REQUESTED:
                self.hass.async_create_task(self.async_request_refresh())

    def _handle_raw_message(self, data: dict) -> None:
        """Handle raw WebSocket message and parse to typed event."""
        try:
            event = parse_event(data)
            self._handle_websocket_event(event)
        except Exception as err:
            _LOGGER.debug("Error parsing WebSocket event: %s", err)

    @callback
    def _handle_ws_connect(self) -> None:
        """
        Handle WebSocket (re)connection.

        Triggers an immediate coordinator refresh so data recovers right away
        after a server reboot or network interruption instead of waiting for
        the next poll cycle. Debounced to avoid hammering the API during rapid
        connect/disconnect cycles.
        """
        # Events may have been missed while disconnected: fetch everything
        self._telemetry.invalidate_full_poll()
        if self._websocket_disconnect_logged:
            _LOGGER.info("WebSocket reconnected")
            self._websocket_disconnect_logged = False
        else:
            _LOGGER.info("WebSocket connected")
        now = dt_util.utcnow()
        if (
            self._last_reconnect_refresh is not None
            and now - self._last_reconnect_refresh < _RECONNECT_REFRESH_DEBOUNCE
        ):
            _LOGGER.debug("Skipping reconnect-triggered refresh (debounced)")
            return
        self._last_reconnect_refresh = now
        self.hass.async_create_task(self.async_request_refresh())

    @callback
    def _handle_ws_disconnect(
        self,
        close_code: int | None = None,
        close_reason: str | None = None,
    ) -> None:
        """Handle WebSocket disconnection with detailed close metadata."""
        details: list[str] = []
        if close_code is not None:
            details.append(f"code={close_code}")
        if close_reason:
            details.append(f"reason={close_reason!r}")
        detail_suffix = f" ({', '.join(details)})" if details else ""

        message = f"WebSocket disconnected{detail_suffix}"
        if not self._websocket_disconnect_logged:
            _LOGGER.warning(message)
            self._websocket_disconnect_logged = True
            return

        _LOGGER.debug(message)

    async def async_start_websocket(self) -> None:
        """Start WebSocket connection for real-time updates."""
        if not self.enable_websocket:
            _LOGGER.debug("WebSocket disabled in configuration")
            return

        if self._ws_client and self._ws_client.is_connected:
            _LOGGER.debug("WebSocket already running")
            return

        self._websocket_disconnect_logged = False

        try:
            # Create the vendored WebSocket client with auto-reconnect
            self._ws_client = UnraidWebSocketClient(
                host=self.client.host,
                port=self.client.port,
                on_message=self._handle_raw_message,
                on_connect=self._handle_ws_connect,
                on_disconnect=self._handle_ws_disconnect,
                auto_reconnect=True,
                reconnect_delays=[1, 2, 5, 10, 30],
                max_retries=10,
                api_token=self.client.api_token,
                topics=subscription_topics(self.data, self.config_entry.options),
            )

            # Start the WebSocket client as a background task
            # The start() method blocks forever, so we run it in a task
            self._ws_task = self.config_entry.async_create_background_task(
                hass=self.hass,
                target=self._ws_client.start(),
                name="unraid_websocket_task",
            )
            _LOGGER.info("WebSocket client started as background task")

        except Exception as err:
            _LOGGER.error("Failed to start WebSocket client: %s", err)
            self._ws_client = None

    async def async_stop_websocket(self) -> None:
        """Stop WebSocket connection."""
        if self._ws_client:
            await self._ws_client.stop()
            self._ws_client = None
        if self._ws_task:
            self._ws_task.cancel()
            try:
                await self._ws_task
            except asyncio.CancelledError:
                # Task cancellation is expected during shutdown
                pass
            self._ws_task = None
            _LOGGER.info("WebSocket client stopped")
