"""Test that websocket events only update data with the model they carry."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from pytest_homeassistant.common import MockConfigEntry

from custom_components.unraid_management_agent import UnraidDataUpdateCoordinator
from custom_components.unraid_management_agent.api.constants import EventType
from custom_components.unraid_management_agent.api.events import parse_event
from custom_components.unraid_management_agent.api.models import (
    CollectorDetails,
    CollectorStatus,
)
from custom_components.unraid_management_agent.const import DOMAIN
from custom_components.unraid_management_agent.coordinator import UnraidData

from .const import MOCK_CONFIG, mock_system_info, mock_ups_info


@pytest.fixture
def coordinator(hass: HomeAssistant) -> UnraidDataUpdateCoordinator:
    """Coordinator with UPS, system and collector data from a poll."""
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
                CollectorDetails(name="docker", enabled=True, interval_seconds=60),
                CollectorDetails(name="vm", enabled=True, interval_seconds=60),
            ],
        ),
    )
    return coordinator


def test_nut_status_update_keeps_ups_data(
    coordinator: UnraidDataUpdateCoordinator,
) -> None:
    """A NUT event (NUTInfo) does not replace the UPS data (UPSInfo)."""
    ups = coordinator.data.ups
    event = parse_event({"installed": True, "running": True, "config_mode": "slave"})
    assert event.event_type == EventType.NUT_STATUS_UPDATE

    coordinator._handle_websocket_event(event)

    assert coordinator.data.ups is ups


def test_hardware_update_keeps_system_data(
    coordinator: UnraidDataUpdateCoordinator,
) -> None:
    """A hardware (DMI) event does not replace the system data."""
    system = coordinator.data.system
    event = parse_event({"bios": {}, "baseboard": {}})
    assert event.event_type == EventType.HARDWARE_UPDATE

    coordinator._handle_websocket_event(event)

    assert coordinator.data.system is system


def test_collector_state_change_updates_one_collector(
    coordinator: UnraidDataUpdateCoordinator,
) -> None:
    """A collector event replaces only that collector in the full status."""
    event = parse_event({"name": "docker", "enabled": False, "interval_seconds": 0})
    assert event.event_type == EventType.COLLECTOR_STATE_CHANGE

    coordinator._handle_websocket_event(event)

    status = coordinator.data.collectors
    assert isinstance(status, CollectorStatus)
    assert status.total == 2
    assert not coordinator.is_collector_enabled("docker")
    assert coordinator.is_collector_enabled("vm")


def test_collector_state_change_before_first_status(
    coordinator: UnraidDataUpdateCoordinator,
) -> None:
    """Without a full status yet, a collector event leaves it unset."""
    coordinator.data.collectors = None
    event = parse_event({"name": "docker", "enabled": False, "interval_seconds": 0})

    coordinator._handle_websocket_event(event)

    assert coordinator.data.collectors is None
    assert coordinator.is_collector_enabled("docker")
