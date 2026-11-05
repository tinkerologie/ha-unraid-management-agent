"""Test the network service binary sensors (agent /settings/network-services)."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant.common import MockConfigEntry

from custom_components.unraid_management_agent.api.models import (
    NetworkServicesStatus,
)
from custom_components.unraid_management_agent.const import DOMAIN

from .const import MOCK_CONFIG, MOCK_OPTIONS

ENTRY_ID = "test_entry_id"
PREFIX = f"{ENTRY_ID}_network_service_"


def _service(name: str, port: int, *, enabled: bool = True) -> dict[str, Any]:
    return {
        "name": name,
        "enabled": enabled,
        "running": enabled,
        "port": port,
        "description": f"{name} service",
    }


# Shape of GET /api/v1/settings/network-services from a live agent
# (v2026.09.01): syslog is sent as "syslog_server"
LIVE_RESPONSE: dict[str, Any] = {
    "smb": _service("SMB", 445),
    "nfs": _service("NFS", 2049),
    "afp": _service("AFP", 548, enabled=False),
    "ftp": _service("FTP", 21, enabled=False),
    "ssh": _service("SSH", 22),
    "telnet": _service("Telnet", 23, enabled=False),
    "avahi": _service("Avahi", 5353),
    "netbios": _service("NetBIOS", 137, enabled=False),
    "wsd": _service("WSD", 3702),
    "wireguard": _service("WireGuard", 51820),
    "upnp": _service("UPnP", 1900, enabled=False),
    "ntp": _service("NTP", 123),
    "syslog_server": _service("Syslog", 514),
    "total_services": 13,
    "enabled_services": 8,
    "running_services": 8,
    "timestamp": "2026-10-08T23:01:57.04497073-04:00",
}


@pytest.mark.parametrize("key", ["syslog_server", "syslog"])
def test_syslog_parsed_from_either_key(key: str) -> None:
    """The syslog service is read from "syslog_server" (agent) or "syslog"."""
    status = NetworkServicesStatus.model_validate({key: _service("Syslog", 514)})
    assert status.syslog is not None
    assert status.syslog.name == "Syslog"
    assert status.syslog.port == 514


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_syslog_network_service_sensor_created(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mock_async_unraid_client: MagicMock,
) -> None:
    """Every service in the agent's response, syslog included, gets a sensor."""
    mock_async_unraid_client.get_network_services.return_value = (
        NetworkServicesStatus.model_validate(LIVE_RESPONSE)
    )
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Unraid (unraid-test)",
        data=MOCK_CONFIG,
        options=MOCK_OPTIONS,
        entry_id=ENTRY_ID,
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    services = {
        e.unique_id[len(PREFIX) :]: e
        for e in er.async_entries_for_config_entry(entity_registry, ENTRY_ID)
        if e.unique_id.startswith(PREFIX)
    }
    assert set(services) == {
        "smb",
        "nfs",
        "afp",
        "ftp",
        "ssh",
        "telnet",
        "avahi",
        "netbios",
        "wsd",
        "wireguard",
        "upnp",
        "ntp",
        "syslog",
    }
    assert services["syslog"].entity_id == "binary_sensor.unraid_test_syslog_service"
