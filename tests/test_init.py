"""Test the Unraid Management Agent integration setup."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import issue_registry as ir

from custom_components.unraid_management_agent import (
    _async_migrate_legacy_entity_unique_ids,
    _make_vm_key,
)
from custom_components.unraid_management_agent.api import UnraidConnectionError
from custom_components.unraid_management_agent.const import DOMAIN
from custom_components.unraid_management_agent.coordinator import UnraidData


async def test_setup_entry_success(
    hass: HomeAssistant,
    mock_config_entry,
    mock_async_unraid_client,
    mock_websocket_client,
) -> None:
    """Test successful setup of config entry."""
    with (
        patch(
            "custom_components.unraid_management_agent.UnraidClient",
            return_value=mock_async_unraid_client,
        ),
        patch(
            "custom_components.unraid_management_agent.UnraidWebSocketClient",
            return_value=mock_websocket_client,
        ),
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    assert mock_config_entry.state == ConfigEntryState.LOADED
    # Verify runtime_data is set
    assert mock_config_entry.runtime_data is not None
    assert mock_config_entry.runtime_data.coordinator is not None
    assert mock_config_entry.runtime_data.client is not None

    # Verify health check was called
    mock_async_unraid_client.health_check.assert_called_once()


async def test_setup_entry_connection_error(
    hass: HomeAssistant, mock_config_entry, mock_async_unraid_client
) -> None:
    """Test setup failure due to connection error."""
    mock_async_unraid_client.health_check.side_effect = UnraidConnectionError(
        "Connection failed"
    )

    with patch(
        "custom_components.unraid_management_agent.UnraidClient",
        return_value=mock_async_unraid_client,
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    assert mock_config_entry.state == ConfigEntryState.SETUP_RETRY


async def test_setup_entry_unexpected_error(
    hass: HomeAssistant, mock_config_entry, mock_async_unraid_client
) -> None:
    """Test setup failure due to unexpected error."""
    mock_async_unraid_client.health_check.side_effect = Exception("Unexpected error")

    with patch(
        "custom_components.unraid_management_agent.UnraidClient",
        return_value=mock_async_unraid_client,
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    assert mock_config_entry.state == ConfigEntryState.SETUP_RETRY


async def test_unload_entry(
    hass: HomeAssistant,
    mock_config_entry,
    mock_async_unraid_client,
    mock_websocket_client,
) -> None:
    """Test unloading a config entry."""
    with (
        patch(
            "custom_components.unraid_management_agent.UnraidClient",
            return_value=mock_async_unraid_client,
        ),
        patch(
            "custom_components.unraid_management_agent.UnraidWebSocketClient",
            return_value=mock_websocket_client,
        ),
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    assert mock_config_entry.state == ConfigEntryState.LOADED

    await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state == ConfigEntryState.NOT_LOADED
    # Verify client was closed
    mock_async_unraid_client.close.assert_called_once()


async def test_reload_entry(
    hass: HomeAssistant,
    mock_config_entry,
    mock_async_unraid_client,
    mock_websocket_client,
) -> None:
    """Test reloading a config entry."""
    with (
        patch(
            "custom_components.unraid_management_agent.UnraidClient",
            return_value=mock_async_unraid_client,
        ),
        patch(
            "custom_components.unraid_management_agent.UnraidWebSocketClient",
            return_value=mock_websocket_client,
        ),
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    assert mock_config_entry.state == ConfigEntryState.LOADED

    with (
        patch(
            "custom_components.unraid_management_agent.UnraidClient",
            return_value=mock_async_unraid_client,
        ),
        patch(
            "custom_components.unraid_management_agent.UnraidWebSocketClient",
            return_value=mock_websocket_client,
        ),
    ):
        await hass.config_entries.async_reload(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    assert mock_config_entry.state == ConfigEntryState.LOADED


async def test_services_registered(
    hass: HomeAssistant,
    mock_config_entry,
    mock_async_unraid_client,
    mock_websocket_client,
) -> None:
    """Test services are registered after setup."""
    with (
        patch(
            "custom_components.unraid_management_agent.UnraidClient",
            return_value=mock_async_unraid_client,
        ),
        patch(
            "custom_components.unraid_management_agent.UnraidWebSocketClient",
            return_value=mock_websocket_client,
        ),
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    # Verify services are registered
    assert hass.services.has_service(DOMAIN, "container_start")
    assert hass.services.has_service(DOMAIN, "container_stop")
    assert hass.services.has_service(DOMAIN, "container_restart")
    assert hass.services.has_service(DOMAIN, "vm_start")
    assert hass.services.has_service(DOMAIN, "vm_stop")
    assert hass.services.has_service(DOMAIN, "array_start")
    assert hass.services.has_service(DOMAIN, "array_stop")
    assert hass.services.has_service(DOMAIN, "parity_check_start")
    assert hass.services.has_service(DOMAIN, "parity_check_stop")


def test_make_vm_key_uses_identifier_when_name_changes() -> None:
    """Test VM key prefers the backend identifier when it differs from the display name."""
    assert (
        _make_vm_key("Windows Server 2016", "Home Assistant") == "windows_server_2016"
    )


async def test_migrate_legacy_unique_ids_skips_when_no_data(
    hass: HomeAssistant,
    mock_config_entry,
) -> None:
    """Test legacy unique ID migration exits early when coordinator data is unavailable."""
    coordinator = MagicMock()
    coordinator.data = None

    await _async_migrate_legacy_entity_unique_ids(hass, mock_config_entry, coordinator)


async def test_migrate_legacy_vm_unique_id_skips_when_target_exists(
    hass: HomeAssistant,
    mock_config_entry,
) -> None:
    """Test legacy VM migration does not rewrite entities when the target unique ID already exists."""
    coordinator = MagicMock()
    vm = MagicMock()
    vm.id = "Windows Server 2016"
    vm.name = "Home Assistant"
    coordinator.data = UnraidData(vms=[vm])

    source_entry = MagicMock(
        domain="switch",
        unique_id=f"{mock_config_entry.entry_id}_vm_switch_Windows Server 2016",
        entity_id="switch.cube_vm_home_assistant_old",
    )
    target_entry = MagicMock(
        domain="switch",
        unique_id=f"{mock_config_entry.entry_id}_vm_windows_server_2016",
        entity_id="switch.cube_vm_home_assistant",
    )
    registry = MagicMock()

    with (
        patch(
            "custom_components.unraid_management_agent.er.async_get",
            return_value=registry,
        ),
        patch(
            "custom_components.unraid_management_agent.er.async_entries_for_config_entry",
            return_value=[source_entry, target_entry],
        ),
    ):
        await _async_migrate_legacy_entity_unique_ids(
            hass, mock_config_entry, coordinator
        )

    registry.async_update_entity.assert_not_called()


async def test_migrate_legacy_vm_unique_id_handles_registry_update_error(
    hass: HomeAssistant,
    mock_config_entry,
) -> None:
    """Test legacy VM migration tolerates registry update errors."""
    coordinator = MagicMock()
    vm = MagicMock()
    vm.id = "Windows Server 2016"
    vm.name = "Home Assistant"
    coordinator.data = UnraidData(vms=[vm])

    source_entry = MagicMock(
        domain="switch",
        unique_id=f"{mock_config_entry.entry_id}_vm_switch_Windows Server 2016",
        entity_id="switch.cube_vm_home_assistant_old",
    )
    registry = MagicMock()
    registry.async_update_entity.side_effect = ValueError("duplicate entity")

    with (
        patch(
            "custom_components.unraid_management_agent.er.async_get",
            return_value=registry,
        ),
        patch(
            "custom_components.unraid_management_agent.er.async_entries_for_config_entry",
            return_value=[source_entry],
        ),
    ):
        await _async_migrate_legacy_entity_unique_ids(
            hass, mock_config_entry, coordinator
        )

    registry.async_update_entity.assert_called_once_with(
        "switch.cube_vm_home_assistant_old",
        new_unique_id=f"{mock_config_entry.entry_id}_vm_windows_server_2016",
    )


async def test_migrate_legacy_gpu_unique_ids(
    hass: HomeAssistant,
    mock_config_entry,
) -> None:
    """Test legacy single-GPU unique IDs are migrated to index 0 IDs."""
    coordinator = MagicMock()
    gpu0 = MagicMock()
    gpu0.index = 0
    coordinator.data = UnraidData(gpu=[gpu0])

    source_entries = [
        MagicMock(
            domain="sensor",
            unique_id=f"{mock_config_entry.entry_id}_gpu_utilization",
            entity_id="sensor.unraid_test_gpu_utilization",
        ),
        MagicMock(
            domain="sensor",
            unique_id=f"{mock_config_entry.entry_id}_gpu_temperature",
            entity_id="sensor.unraid_test_gpu_temperature",
        ),
        MagicMock(
            domain="sensor",
            unique_id=f"{mock_config_entry.entry_id}_gpu_power",
            entity_id="sensor.unraid_test_gpu_power",
        ),
        MagicMock(
            domain="sensor",
            unique_id=f"{mock_config_entry.entry_id}_gpu_energy",
            entity_id="sensor.unraid_test_gpu_energy",
        ),
    ]
    registry = MagicMock()

    with (
        patch(
            "custom_components.unraid_management_agent.er.async_get",
            return_value=registry,
        ),
        patch(
            "custom_components.unraid_management_agent.er.async_entries_for_config_entry",
            return_value=source_entries,
        ),
    ):
        await _async_migrate_legacy_entity_unique_ids(
            hass, mock_config_entry, coordinator
        )

    expected_calls = [
        (
            ("sensor.unraid_test_gpu_utilization",),
            {"new_unique_id": f"{mock_config_entry.entry_id}_gpu_0_utilization"},
        ),
        (
            ("sensor.unraid_test_gpu_temperature",),
            {"new_unique_id": f"{mock_config_entry.entry_id}_gpu_0_temperature"},
        ),
        (
            ("sensor.unraid_test_gpu_power",),
            {"new_unique_id": f"{mock_config_entry.entry_id}_gpu_0_power"},
        ),
        (
            ("sensor.unraid_test_gpu_energy",),
            {"new_unique_id": f"{mock_config_entry.entry_id}_gpu_0_energy"},
        ),
    ]
    assert registry.async_update_entity.call_count == 4
    for args, kwargs in expected_calls:
        assert any(
            call.args == args and call.kwargs == kwargs
            for call in registry.async_update_entity.call_args_list
        )


async def test_migrate_legacy_gpu_unique_ids_skips_when_target_exists(
    hass: HomeAssistant,
    mock_config_entry,
) -> None:
    """Test GPU migration is skipped when indexed target unique ID already exists."""
    coordinator = MagicMock()
    gpu0 = MagicMock()
    gpu0.index = 0
    coordinator.data = UnraidData(gpu=[gpu0])

    source_entry = MagicMock(
        domain="sensor",
        unique_id=f"{mock_config_entry.entry_id}_gpu_utilization",
        entity_id="sensor.unraid_test_gpu_utilization",
    )
    target_entry = MagicMock(
        domain="sensor",
        unique_id=f"{mock_config_entry.entry_id}_gpu_0_utilization",
        entity_id="sensor.unraid_test_gpu_0_utilization",
    )
    registry = MagicMock()

    with (
        patch(
            "custom_components.unraid_management_agent.er.async_get",
            return_value=registry,
        ),
        patch(
            "custom_components.unraid_management_agent.er.async_entries_for_config_entry",
            return_value=[source_entry, target_entry],
        ),
    ):
        await _async_migrate_legacy_entity_unique_ids(
            hass, mock_config_entry, coordinator
        )

    assert registry.async_update_entity.call_count == 0


async def test_async_reload_entry(
    hass: HomeAssistant,
    mock_config_entry,
) -> None:
    """Test reloading entry."""
    with patch.object(
        hass.config_entries, "async_reload", new_callable=AsyncMock
    ) as mock_reload:
        from custom_components.unraid_management_agent import async_reload_entry

        await async_reload_entry(hass, mock_config_entry)
        mock_reload.assert_called_once_with(mock_config_entry.entry_id)


async def test_duplicate_services_setup(hass: HomeAssistant) -> None:
    """Test async_setup_services exits early when services already registered."""
    from custom_components.unraid_management_agent import async_setup_services

    with (
        patch("homeassistant.core.ServiceRegistry.has_service", return_value=True),
        patch("homeassistant.core.ServiceRegistry.async_register") as mock_register,
    ):
        await async_setup_services(hass)
        mock_register.assert_not_called()


async def test_services_calls_and_actions(
    hass: HomeAssistant,
    mock_config_entry,
    mock_async_unraid_client,
    mock_websocket_client,
) -> None:
    """Test container and system services execution."""
    with (
        patch(
            "custom_components.unraid_management_agent.UnraidClient",
            return_value=mock_async_unraid_client,
        ),
        patch(
            "custom_components.unraid_management_agent.UnraidWebSocketClient",
            return_value=mock_websocket_client,
        ),
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    # container_start
    await hass.services.async_call(
        DOMAIN,
        "container_start",
        {"container_id": "test_container"},
        blocking=True,
    )
    mock_async_unraid_client.start_container.assert_called_once_with("test_container")

    # container_remove
    await hass.services.async_call(
        DOMAIN,
        "container_remove",
        {"container_id": "test_container", "remove_image": True},
        blocking=True,
    )
    mock_async_unraid_client.remove_container.assert_called_once_with(
        "test_container", remove_image=True
    )

    # container_set_autostart
    await hass.services.async_call(
        DOMAIN,
        "container_set_autostart",
        {"container_id": "test_container", "enabled": True},
        blocking=True,
    )
    mock_async_unraid_client.set_container_autostart.assert_called_once_with(
        "test_container", enabled=True
    )

    # vm_start
    await hass.services.async_call(
        DOMAIN,
        "vm_start",
        {"vm_id": "test_vm"},
        blocking=True,
    )
    mock_async_unraid_client.start_vm.assert_called_once_with("test_vm")

    # array_start
    await hass.services.async_call(
        DOMAIN,
        "array_start",
        {},
        blocking=True,
    )
    mock_async_unraid_client.start_array.assert_called_once()


async def test_services_error_handling(
    hass: HomeAssistant,
    mock_config_entry,
    mock_async_unraid_client,
    mock_websocket_client,
) -> None:
    """Test services handle exceptions by raising HomeAssistantError."""
    with (
        patch(
            "custom_components.unraid_management_agent.UnraidClient",
            return_value=mock_async_unraid_client,
        ),
        patch(
            "custom_components.unraid_management_agent.UnraidWebSocketClient",
            return_value=mock_websocket_client,
        ),
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    mock_async_unraid_client.start_container.side_effect = Exception("API error")
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            DOMAIN,
            "container_start",
            {"container_id": "test_container"},
            blocking=True,
        )

    # Test service call when no config entries exist
    with (
        patch.object(hass.config_entries, "async_entries", return_value=[]),
        pytest.raises(HomeAssistantError),
    ):
        await hass.services.async_call(
            DOMAIN,
            "container_stop",
            {"container_id": "test_container"},
            blocking=True,
        )


@pytest.mark.usefixtures(
    "mock_unraid_client_class", "mock_unraid_websocket_client_class"
)
async def test_setup_removes_legacy_repair_issues(
    hass: HomeAssistant, mock_config_entry
) -> None:
    """Repair issues and I/O error acknowledgements of older versions are removed."""
    for issue_id in (
        "disk_health_disk1_high_temp",
        f"disk_health_{mock_config_entry.entry_id}_disk1_io_errors",
        f"connection_{mock_config_entry.entry_id}",
    ):
        ir.async_create_issue(
            hass,
            DOMAIN,
            issue_id,
            is_fixable=True,
            severity=ir.IssueSeverity.WARNING,
            translation_key="disk_high_temperature",
        )
    ir.async_create_issue(
        hass,
        DOMAIN,
        "future_notice",
        is_fixable=False,
        severity=ir.IssueSeverity.WARNING,
        translation_key="future_notice",
    )
    ir.async_create_issue(
        hass,
        "other_domain",
        "disk_health_disk1_high_temp",
        is_fixable=False,
        severity=ir.IssueSeverity.WARNING,
        translation_key="other",
    )
    hass.config_entries.async_update_entry(
        mock_config_entry,
        options={**mock_config_entry.options, "acknowledged_disk_io_errors": {"S": 3}},
    )

    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    issues = ir.async_get(hass).issues
    # Only the legacy repairs are removed, not other issues of the integration
    assert [key for key in issues if key[0] == DOMAIN] == [(DOMAIN, "future_notice")]
    assert ("other_domain", "disk_health_disk1_high_temp") in issues
    assert "acknowledged_disk_io_errors" not in mock_config_entry.options
