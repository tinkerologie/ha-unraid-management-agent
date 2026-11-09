"""Wire contracts consumed by the vendored REST client."""

import json

import pytest
from pydantic import ValidationError

from custom_components.unraid_management_agent.api.exceptions import (
    UnraidAPIError,
    UnraidNotFoundError,
)
from tests.producer_contract import assert_values, fixture, request

NETWORK = {
    "syslog.port": 514,
    "syslog.enabled": True,
    "syslog.running": True,
    "services_enabled": 2,
    "services_running": 2,
}
for name, port in {
    "smb": 445,
    "nfs": 2049,
    "afp": 548,
    "ftp": 21,
    "ssh": 22,
    "telnet": 23,
    "avahi": 5353,
    "netbios": 137,
    "wsd": 3702,
    "wireguard": None,
    "upnp": None,
    "ntp": 123,
}.items():
    NETWORK.update(
        {
            f"{name}.port": port,
            f"{name}.enabled": name == "smb",
            f"{name}.running": name == "smb",
        }
    )

ZFS_LIST = {
    "0.name": "sample",
    "0.corrupted_file_count": 1,
    "0.corrupted_file_paths": ["/mnt/sample/example.bin"],
    "1.corrupted_file_count": 0,
}
NOTIFICATIONS = {
    "notifications.0.id": "sample-notification",
    "notifications.0.subject": "Example",
    "notifications.0.importance": "info",
    "notifications.0.timestamp": "2026-01-01T00:00:00Z",
}
OVERVIEW = {
    "unread.info": 1,
    "unread.warning": 0,
    "unread.alert": 0,
    "unread.total": 1,
    "archive.total": 0,
}
UPS = {
    "load_percent": 0,
    "battery_charge_percent": None,
    "power_watts": None,
    "runtime_left_seconds": None,
}
NUT = {
    "installed": True,
    "running": True,
    "statuses.0.device_name": "sample-ups",
    "statuses.1.device_name": "sample-ats",
    "statuses.0.battery_runtime_seconds": None,
    "statuses.0.realpower_watts": None,
}

REST = {
    "network-services": ("get_network_services", (), NETWORK),
    "legacy-network": ("get_network_services", (), NETWORK),
    "zfs-pools": ("list_zfs_pools", (), ZFS_LIST),
    "zfs-pool": (
        "get_zfs_pool",
        ("sample",),
        {
            "name": "sample",
            "corrupted_file_count": 1,
            "corrupted_file_paths": ["/mnt/sample/example.bin"],
        },
    ),
    "legacy-zfs": (
        "list_zfs_pools",
        (),
        {"0.corrupted_file_count": 3, "0.corrupted_file_paths": []},
    ),
    "ups-empty": (
        "get_ups_info",
        (),
        {"connected": False, "load_percent": None, "runtime_left_seconds": None},
    ),
    "ups-measurements": ("get_ups_info", (), UPS),
    "legacy-ups": ("get_ups_info", (), {"connected": True, "runtime_left_seconds": 0}),
    "nut-not-installed": (
        "get_nut_info",
        (),
        {"installed": False, "running": False, "statuses": None},
    ),
    "nut-stopped": (
        "get_nut_info",
        (),
        {"installed": True, "running": False, "statuses": None},
    ),
    "nut-running": ("get_nut_info", (), NUT),
    "notifications": (
        "list_notifications",
        (),
        NOTIFICATIONS | {f"overview.{k}": v for k, v in OVERVIEW.items()},
    ),
    "notifications-unread": ("list_unread_notifications", (), NOTIFICATIONS),
    "notifications-overview": ("get_notification_overview", (), OVERVIEW),
    "notifications-fallback": (
        "list_notifications",
        (),
        {"notifications": [], "overview.unread.total": 0},
    ),
    "notifications-collected-empty": (
        "list_notifications",
        (),
        {"notifications": None, "overview.unread.total": 0},
    ),
    "shares-empty": ("list_shares", (), []),
    "shares-usage": (
        "list_shares",
        (),
        {
            "0.storage_used_bytes": 60,
            "0.storage_total_bytes": 100,
            "0.storage_free_bytes": 40,
            "0.storage_usage_percent": 60,
            "0.used_bytes": 25,
            "1.used_bytes": 0,
            "2.used_bytes": None,
        },
    ),
    "legacy-shares": (
        "list_shares",
        (),
        {"0.storage_used_bytes": 40, "0.used_bytes": None},
    ),
    "source-health": (
        "get_diagnostics_self_test",
        (),
        {
            "overall_state": "unavailable",
            "degraded_subsystem_count": 2,
            "subsystems.0.state": "healthy",
            "subsystems.1.state": "unavailable",
            "subsystems.2.state": "disabled",
            "capabilities.items.2.state": "unknown",
        },
    ),
    "collector-status": (
        "get_collector",
        ("disk",),
        {
            "collector.name": "disk",
            "collector.interval_seconds": 30,
            "collector.status": "running",
        },
    ),
    "collector-status-list": (
        "get_collectors_status",
        (),
        {
            "mode": "dynamic",
            "collectors.0.name": "disk",
            "collectors.0.required": False,
            "collectors.0.publish_count": 2,
        },
    ),
}
ERRORS = {
    "network-services-error": (
        "get_network_services",
        (),
        UnraidAPIError,
        500,
        "Failed to get network services status",
    ),
    "notification-missing": (
        "get_notification",
        ("missing",),
        UnraidNotFoundError,
        404,
        "Notification not found",
    ),
    "zfs-pool-missing": (
        "get_zfs_pool",
        ("missing",),
        UnraidNotFoundError,
        404,
        "ZFS pool not found: missing",
    ),
}


@pytest.mark.parametrize("case", REST)
async def test_rest_contract(case):
    """Assert what the integration consumes from a real REST response."""
    method, args, expected = REST[case]
    value = await request(case, method, *args)
    if isinstance(expected, list):
        assert value == expected
    else:
        assert_values(value, expected)


@pytest.mark.parametrize("case", ERRORS)
async def test_error_contract(case):
    """Preserve the error response status and message."""
    method, args, error, status, message = ERRORS[case]
    with pytest.raises(error, match=message) as result:
        await request(case, method, *args)
    assert result.value.status_code == status
    assert result.value.error_code == "UNKNOWN_ERROR"


async def test_drift_is_detected():
    """A model accepting extra fields cannot mask producer contract drift."""
    data = json.loads(fixture("network-services"))
    assert_values(await request("network-services", "get_network_services"), NETWORK)
    syslog = data["syslog_server"]
    syslog["service_port"] = syslog.pop("port")
    result = await request(
        "network-services", "get_network_services", body=json.dumps(data).encode()
    )
    with pytest.raises(AssertionError, match=r"syslog\.port"):
        assert_values(result, NETWORK)

    assert_values(await request("zfs-pools", "list_zfs_pools"), ZFS_LIST)
    empty = await request("zfs-pools", "list_zfs_pools", body=b"{}")
    with pytest.raises(AssertionError):
        assert_values(empty, ZFS_LIST)
    with pytest.raises(ValidationError):
        await request("zfs-pools", "list_zfs_pools", body=b'{"wrong":true}')


async def test_malformed_error_body_reaches_aiohttp_text_fallback():
    """The byte-backed response uses aiohttp's real JSON and text methods."""
    with pytest.raises(UnraidAPIError, match="invalid JSON") as result:
        await request(
            "network-services-error", "get_network_services", body=b"invalid JSON"
        )
    assert result.value.status_code == 500
