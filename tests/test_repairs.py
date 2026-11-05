"""Test the Unraid Management Agent repairs."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from pytest_homeassistant.common import MockConfigEntry

from custom_components.unraid_management_agent.api.models import ArrayStatus, DiskInfo
from custom_components.unraid_management_agent.const import (
    CONF_ACKNOWLEDGED_DISK_IO_ERRORS,
    DOMAIN,
)
from custom_components.unraid_management_agent.coordinator import UnraidData
from custom_components.unraid_management_agent.repairs import (
    ArrayIssueRepairFlow,
    ConnectionIssueRepairFlow,
    DiskHealthRepairFlow,
    DiskIOErrorRepairFlow,
    ParityCheckRepairFlow,
    async_check_and_create_issues,
    async_create_fix_flow,
    async_delete_disk_issues,
)


async def test_create_fix_flow_connection(hass: HomeAssistant) -> None:
    """Test creating connection issue repair flow."""
    flow = await async_create_fix_flow(
        hass, "connection_test", {"error": "test error", "host": "192.168.1.100"}
    )
    assert isinstance(flow, ConnectionIssueRepairFlow)


async def test_create_fix_flow_disk_health(hass: HomeAssistant) -> None:
    """Test creating disk health repair flow."""
    flow = await async_create_fix_flow(
        hass, "disk_health_disk1", {"disk_name": "disk1", "smart_status": "OK"}
    )
    assert isinstance(flow, DiskHealthRepairFlow)


async def test_create_fix_flow_array(hass: HomeAssistant) -> None:
    """Test creating array issue repair flow."""
    flow = await async_create_fix_flow(hass, "array_parity", {"array_state": "Started"})
    assert isinstance(flow, ArrayIssueRepairFlow)


async def test_create_fix_flow_parity(hass: HomeAssistant) -> None:
    """Test creating parity check repair flow."""
    flow = await async_create_fix_flow(hass, "parity_check_stuck", {"sync_percent": 95})
    assert isinstance(flow, ParityCheckRepairFlow)


async def test_create_fix_flow_unknown(hass: HomeAssistant) -> None:
    """Test creating flow for unknown issue type."""
    from homeassistant.components.repairs import RepairsFlow

    flow = await async_create_fix_flow(hass, "unknown_issue", {})
    assert isinstance(flow, RepairsFlow)


async def test_connection_issue_repair_flow_init(hass: HomeAssistant) -> None:
    """Test connection issue repair flow initial step."""
    flow = ConnectionIssueRepairFlow(
        hass,
        "connection_test",
        {"error": "Connection refused", "host": "192.168.1.100", "port": 8043},
    )

    result = await flow.async_step_init(user_input=None)

    assert result["type"] == "form"
    assert result["step_id"] == "init"
    assert "error" in result["description_placeholders"]
    assert result["description_placeholders"]["error"] == "Connection refused"


async def test_connection_issue_repair_flow_resolve(hass: HomeAssistant) -> None:
    """Test connection issue repair flow resolution."""
    flow = ConnectionIssueRepairFlow(hass, "connection_test", {"error": "test error"})

    with patch(
        "custom_components.unraid_management_agent.repairs.ir.async_delete_issue"
    ) as mock_delete:
        result = await flow.async_step_init(user_input={})

    assert result["type"] == "create_entry"
    mock_delete.assert_called_once()


async def test_disk_health_repair_flow_init(hass: HomeAssistant) -> None:
    """Test disk health repair flow initial step."""
    flow = DiskHealthRepairFlow(
        hass,
        "disk_health_disk1",
        {
            "disk_name": "disk1",
            "smart_status": "FAILING",
            "smart_errors": 5,
            "temperature": 55,
        },
    )

    result = await flow.async_step_init(user_input=None)

    assert result["type"] == "form"
    assert result["step_id"] == "init"
    assert result["description_placeholders"]["disk_name"] == "disk1"
    assert result["description_placeholders"]["smart_status"] == "FAILING"


async def test_disk_health_repair_flow_resolve(hass: HomeAssistant) -> None:
    """Test disk health repair flow resolution."""
    flow = DiskHealthRepairFlow(hass, "disk_health_disk1", {})

    with patch(
        "custom_components.unraid_management_agent.repairs.ir.async_delete_issue"
    ):
        result = await flow.async_step_init(user_input={})

    assert result["type"] == "create_entry"


async def test_array_issue_repair_flow_init(hass: HomeAssistant) -> None:
    """Test array issue repair flow initial step."""
    flow = ArrayIssueRepairFlow(
        hass,
        "array_parity_invalid",
        {"array_state": "Started", "issue_description": "Parity disk is invalid"},
    )

    result = await flow.async_step_init(user_input=None)

    assert result["type"] == "form"
    assert result["description_placeholders"]["array_state"] == "Started"


async def test_array_issue_repair_flow_resolve(hass: HomeAssistant) -> None:
    """Test array issue repair flow resolution."""
    flow = ArrayIssueRepairFlow(hass, "array_parity", {})

    with patch(
        "custom_components.unraid_management_agent.repairs.ir.async_delete_issue"
    ):
        result = await flow.async_step_init(user_input={})

    assert result["type"] == "create_entry"


async def test_parity_check_repair_flow_init(hass: HomeAssistant) -> None:
    """Test parity check repair flow initial step."""
    flow = ParityCheckRepairFlow(
        hass,
        "parity_check_stuck",
        {"parity_status": "Running", "sync_percent": 96, "errors_found": 0},
    )

    result = await flow.async_step_init(user_input=None)

    assert result["type"] == "form"
    assert result["description_placeholders"]["parity_status"] == "Running"
    assert result["description_placeholders"]["sync_percent"] == "96"


async def test_parity_check_repair_flow_resolve(hass: HomeAssistant) -> None:
    """Test parity check repair flow resolution."""
    flow = ParityCheckRepairFlow(hass, "parity_check", {})

    with patch(
        "custom_components.unraid_management_agent.repairs.ir.async_delete_issue"
    ):
        result = await flow.async_step_init(user_input={})

    assert result["type"] == "create_entry"


async def test_check_and_create_issues_connection_failed(
    hass: HomeAssistant,
) -> None:
    """Test issue creation when connection fails."""
    coordinator = MagicMock()
    coordinator.config_entry.entry_id = "test_entry"
    coordinator.config_entry.options = {}
    coordinator.config_entry.data = {"host": "192.168.1.100", "port": 8043}
    coordinator.last_update_success = False
    coordinator.last_exception = Exception("Connection timeout")
    coordinator.data = None

    with patch(
        "custom_components.unraid_management_agent.repairs.ir.async_create_issue"
    ) as mock_create:
        await async_check_and_create_issues(hass, coordinator)

    mock_create.assert_called_once()
    # Check that the issue was created with the expected issue_id pattern
    # The first 3 args are positional: hass, domain, issue_id
    call_args = mock_create.call_args
    assert call_args[0][2] == "connection_test_entry"


async def test_check_and_create_issues_connection_success(
    hass: HomeAssistant,
) -> None:
    """Test issue deletion when connection succeeds."""
    coordinator = MagicMock()
    coordinator.config_entry.entry_id = "test_entry"
    coordinator.config_entry.options = {}
    coordinator.config_entry.data = {"host": "192.168.1.100", "port": 8043}
    coordinator.last_update_success = True
    coordinator.data = UnraidData(disks=[], array=None)

    with (
        patch(
            "custom_components.unraid_management_agent.repairs.ir.async_delete_issue"
        ) as mock_delete,
        patch(
            "custom_components.unraid_management_agent.repairs.ir.async_create_issue"
        ),
    ):
        await async_check_and_create_issues(hass, coordinator)

    # Should delete connection issue
    assert any("connection_" in str(call) for call in mock_delete.call_args_list)


async def test_check_and_create_issues_disk_high_temp(
    hass: HomeAssistant,
) -> None:
    """Test issue creation for high disk temperature."""
    coordinator = MagicMock()
    coordinator.config_entry.entry_id = "test_entry"
    coordinator.config_entry.options = {}
    coordinator.config_entry.data = {"host": "192.168.1.100", "port": 8043}
    coordinator.last_update_success = True

    # Mock disk_settings with thresholds
    mock_disk_settings = MagicMock()
    mock_disk_settings.hdd_temp_warning_celsius = 45
    mock_disk_settings.hdd_temp_critical_celsius = 55

    coordinator.data = UnraidData(
        disks=[
            DiskInfo(
                id="disk1",
                name="disk1",
                device="sda",
                role="data",
                smart_errors=0,
                smart_status="OK",
                temperature_celsius=50,  # Above 45 warning threshold for HDD
            )
        ],
        disk_settings=mock_disk_settings,
        array=None,
    )

    with (
        patch(
            "custom_components.unraid_management_agent.repairs.ir.async_create_issue"
        ) as mock_create,
        patch(
            "custom_components.unraid_management_agent.repairs.ir.async_delete_issue"
        ),
    ):
        await async_check_and_create_issues(hass, coordinator)

    # Check high temp issue was created
    assert any("high_temp" in str(call) for call in mock_create.call_args_list)


async def test_check_and_create_issues_disk_critical_temp(
    hass: HomeAssistant,
) -> None:
    """Test issue creation for critical disk temperature."""
    coordinator = MagicMock()
    coordinator.config_entry.entry_id = "test_entry"
    coordinator.config_entry.options = {}
    coordinator.config_entry.data = {"host": "192.168.1.100", "port": 8043}
    coordinator.last_update_success = True

    # Mock disk_settings with thresholds
    mock_disk_settings = MagicMock()
    mock_disk_settings.hdd_temp_warning_celsius = 45
    mock_disk_settings.hdd_temp_critical_celsius = 55

    coordinator.data = UnraidData(
        disks=[
            DiskInfo(
                id="disk1",
                name="disk1",
                device="sda",
                role="data",
                smart_errors=0,
                temperature_celsius=60,  # Above 55 critical threshold for HDD
            )
        ],
        disk_settings=mock_disk_settings,
        array=None,
    )

    with (
        patch(
            "custom_components.unraid_management_agent.repairs.ir.async_create_issue"
        ) as mock_create,
        patch(
            "custom_components.unraid_management_agent.repairs.ir.async_delete_issue"
        ),
    ):
        await async_check_and_create_issues(hass, coordinator)

    # Check critical temp issue was created
    assert any("critical_temp" in str(call) for call in mock_create.call_args_list)


async def test_check_and_create_issues_parity_invalid(
    hass: HomeAssistant,
) -> None:
    """Test issue creation for invalid parity."""
    coordinator = MagicMock()
    coordinator.config_entry.entry_id = "test_entry"
    coordinator.config_entry.options = {}
    coordinator.config_entry.data = {"host": "192.168.1.100", "port": 8043}
    coordinator.last_update_success = True
    coordinator.data = UnraidData(
        disks=[],
        array=ArrayStatus(parity_valid=False, state="Started", num_parity_disks=1),
    )

    with (
        patch(
            "custom_components.unraid_management_agent.repairs.ir.async_create_issue"
        ) as mock_create,
        patch(
            "custom_components.unraid_management_agent.repairs.ir.async_delete_issue"
        ),
    ):
        await async_check_and_create_issues(hass, coordinator)

    # Check parity invalid issue was created
    assert any("parity_invalid" in str(call) for call in mock_create.call_args_list)


async def test_check_and_create_issues_parity_check_stuck(
    hass: HomeAssistant,
) -> None:
    """Test issue creation for stuck parity check."""
    coordinator = MagicMock()
    coordinator.config_entry.entry_id = "test_entry"
    coordinator.config_entry.options = {}
    coordinator.config_entry.data = {"host": "192.168.1.100", "port": 8043}
    coordinator.last_update_success = True
    coordinator.data = UnraidData(
        disks=[],
        array=ArrayStatus(
            parity_valid=True,
            parity_check_status="running",
            parity_check_progress=97,
        ),
    )

    with (
        patch(
            "custom_components.unraid_management_agent.repairs.ir.async_create_issue"
        ) as mock_create,
        patch(
            "custom_components.unraid_management_agent.repairs.ir.async_delete_issue"
        ),
    ):
        await async_check_and_create_issues(hass, coordinator)

    # Check stuck parity check issue was created
    assert any("stuck" in str(call) for call in mock_create.call_args_list)


async def test_check_and_create_issues_no_data(
    hass: HomeAssistant,
) -> None:
    """Test no additional issues created when coordinator has no data."""
    coordinator = MagicMock()
    coordinator.config_entry.entry_id = "test_entry"
    coordinator.config_entry.options = {}
    coordinator.config_entry.data = {"host": "192.168.1.100", "port": 8043}
    coordinator.last_update_success = True
    coordinator.data = None

    with (
        patch(
            "custom_components.unraid_management_agent.repairs.ir.async_create_issue"
        ) as mock_create,
        patch(
            "custom_components.unraid_management_agent.repairs.ir.async_delete_issue"
        ),
    ):
        await async_check_and_create_issues(hass, coordinator)

    # Should not create any disk or array issues
    assert not any("disk_" in str(call) for call in mock_create.call_args_list)
    assert not any("array_" in str(call) for call in mock_create.call_args_list)


async def test_check_and_create_issues_parity_invalid_no_state(
    hass: HomeAssistant,
) -> None:
    """Test parity invalid issue is created."""
    coordinator = MagicMock()
    coordinator.config_entry.entry_id = "test_entry"
    coordinator.config_entry.options = {}
    coordinator.config_entry.data = {"host": "192.168.1.100", "port": 8043}
    coordinator.last_update_success = True
    coordinator.data = UnraidData(
        disks=[],
        array=ArrayStatus(
            parity_valid=False,  # Invalid parity
            parity_check_status=None,
            parity_check_progress=None,
            num_parity_disks=1,
        ),
    )

    with (
        patch(
            "custom_components.unraid_management_agent.repairs.ir.async_create_issue"
        ) as mock_create,
        patch(
            "custom_components.unraid_management_agent.repairs.ir.async_delete_issue"
        ),
    ):
        await async_check_and_create_issues(hass, coordinator)

    # Check parity invalid issue was created
    assert any("parity_invalid" in str(call) for call in mock_create.call_args_list)


async def test_check_and_create_issues_parity_valid(
    hass: HomeAssistant,
) -> None:
    """Test parity valid removes existing issue."""
    coordinator = MagicMock()
    coordinator.config_entry.entry_id = "test_entry"
    coordinator.config_entry.options = {}
    coordinator.config_entry.data = {"host": "192.168.1.100", "port": 8043}
    coordinator.last_update_success = True
    coordinator.data = UnraidData(
        disks=[],
        array=ArrayStatus(
            parity_valid=True,  # Valid parity
            parity_check_status=None,
            parity_check_progress=None,
        ),
    )

    with (
        patch(
            "custom_components.unraid_management_agent.repairs.ir.async_create_issue"
        ),
        patch(
            "custom_components.unraid_management_agent.repairs.ir.async_delete_issue"
        ) as mock_delete,
    ):
        await async_check_and_create_issues(hass, coordinator)

    # Check parity invalid issue was deleted
    assert any("parity_invalid" in str(call) for call in mock_delete.call_args_list)


async def test_check_and_create_issues_no_parity_disks(
    hass: HomeAssistant,
) -> None:
    """Test no parity issue created when server has no parity disks (pools only)."""
    coordinator = MagicMock()
    coordinator.config_entry.entry_id = "test_entry"
    coordinator.config_entry.options = {}
    coordinator.config_entry.data = {"host": "192.168.1.100", "port": 8043}
    coordinator.last_update_success = True
    coordinator.data = UnraidData(
        disks=[],
        array=ArrayStatus(
            parity_valid=False,  # False because no parity exists
            num_parity_disks=0,  # No parity disks - pools only setup
        ),
    )

    with (
        patch(
            "custom_components.unraid_management_agent.repairs.ir.async_create_issue"
        ) as mock_create,
        patch(
            "custom_components.unraid_management_agent.repairs.ir.async_delete_issue"
        ),
    ):
        await async_check_and_create_issues(hass, coordinator)

    # Should NOT create parity invalid issue when there are no parity disks
    assert not any("parity_invalid" in str(call) for call in mock_create.call_args_list)


async def test_check_and_create_issues_temp_warning(
    hass: HomeAssistant,
) -> None:
    """Test temperature warning issue is created when disk is above warning threshold."""
    coordinator = MagicMock()
    coordinator.config_entry.entry_id = "test_entry"
    coordinator.config_entry.options = {}
    coordinator.config_entry.data = {"host": "192.168.1.100", "port": 8043}
    coordinator.last_update_success = True
    coordinator.last_exception = None

    # Disk with high temperature (warning level: 45+)
    disk = DiskInfo(
        device="sda",
        role="data",
        name="disk1",
        id="WDC_WD80EFAX",
        temperature_celsius=50,  # Above 45 warning threshold, below 55 critical
    )

    # Mock disk_settings with thresholds
    mock_disk_settings = MagicMock()
    mock_disk_settings.hdd_temp_warning_celsius = 45
    mock_disk_settings.hdd_temp_critical_celsius = 55

    coordinator.data = UnraidData(
        disks=[disk],
        disk_settings=mock_disk_settings,
        array=ArrayStatus(parity_valid=True),
    )

    with (
        patch(
            "custom_components.unraid_management_agent.repairs.ir.async_create_issue"
        ) as mock_create,
        patch(
            "custom_components.unraid_management_agent.repairs.ir.async_delete_issue"
        ) as mock_delete,
    ):
        await async_check_and_create_issues(hass, coordinator)

    # Check temperature warning issue was created
    create_calls = [str(call) for call in mock_create.call_args_list]
    assert any("high_temp" in str(call) for call in create_calls)


async def test_check_and_create_issues_temp_critical(
    hass: HomeAssistant,
) -> None:
    """Test temperature critical issue is created when disk is above critical threshold."""
    coordinator = MagicMock()
    coordinator.config_entry.entry_id = "test_entry"
    coordinator.config_entry.options = {}
    coordinator.config_entry.data = {"host": "192.168.1.100", "port": 8043}
    coordinator.last_update_success = True
    coordinator.last_exception = None

    # Disk with critical temperature (55+ for HDD)
    disk = DiskInfo(
        device="sda",
        role="data",
        name="disk1",
        id="WDC_WD80EFAX",
        temperature_celsius=60,  # Above 55 critical threshold
    )

    # Mock disk_settings with thresholds
    mock_disk_settings = MagicMock()
    mock_disk_settings.hdd_temp_warning_celsius = 45
    mock_disk_settings.hdd_temp_critical_celsius = 55

    coordinator.data = UnraidData(
        disks=[disk],
        disk_settings=mock_disk_settings,
        array=ArrayStatus(parity_valid=True),
    )

    with (
        patch(
            "custom_components.unraid_management_agent.repairs.ir.async_create_issue"
        ) as mock_create,
        patch(
            "custom_components.unraid_management_agent.repairs.ir.async_delete_issue"
        ) as mock_delete,
    ):
        await async_check_and_create_issues(hass, coordinator)

    # Check temperature critical issue was created
    create_calls = [str(call) for call in mock_create.call_args_list]
    assert any("critical_temp" in str(call) for call in create_calls)


async def test_check_and_create_issues_temp_normal_clears(
    hass: HomeAssistant,
) -> None:
    """Test normal temperature clears existing issues."""
    coordinator = MagicMock()
    coordinator.config_entry.entry_id = "test_entry"
    coordinator.config_entry.options = {}
    coordinator.config_entry.data = {"host": "192.168.1.100", "port": 8043}
    coordinator.last_update_success = True
    coordinator.last_exception = None

    # Disk with normal temperature (below 45 warning threshold for HDD)
    disk = DiskInfo(
        device="sda",
        role="data",
        name="disk1",
        id="WDC_WD80EFAX",
        temperature_celsius=35,  # Normal temperature
    )

    # Mock disk_settings with thresholds
    mock_disk_settings = MagicMock()
    mock_disk_settings.hdd_temp_warning_celsius = 45
    mock_disk_settings.hdd_temp_critical_celsius = 55

    coordinator.data = UnraidData(
        disks=[disk],
        disk_settings=mock_disk_settings,
        array=ArrayStatus(parity_valid=True),
    )

    with (
        patch(
            "custom_components.unraid_management_agent.repairs.ir.async_create_issue"
        ) as mock_create,
        patch(
            "custom_components.unraid_management_agent.repairs.ir.async_delete_issue"
        ) as mock_delete,
    ):
        await async_check_and_create_issues(hass, coordinator)

    # Check temperature issues were deleted (for normal temps, both are deleted)
    delete_calls = [str(call) for call in mock_delete.call_args_list]
    # Should delete both warning and critical temp issues
    assert any("high_temp" in str(call) for call in delete_calls)
    assert any("critical_temp" in str(call) for call in delete_calls)


async def test_check_and_create_issues_no_temp_clears(
    hass: HomeAssistant,
) -> None:
    """Test missing temperature clears existing issues."""
    coordinator = MagicMock()
    coordinator.config_entry.entry_id = "test_entry"
    coordinator.config_entry.options = {}
    coordinator.config_entry.data = {"host": "192.168.1.100", "port": 8043}
    coordinator.last_update_success = True
    coordinator.last_exception = None

    # Disk without temperature reading
    disk = DiskInfo(
        device="sda",
        role="data",
        name="disk1",
        id="WDC_WD80EFAX",
        temperature_celsius=None,
    )

    coordinator.data = UnraidData(
        disks=[disk],
        disk_settings=None,
        array=ArrayStatus(parity_valid=True),
    )

    with (
        patch(
            "custom_components.unraid_management_agent.repairs.ir.async_create_issue"
        ) as mock_create,
        patch(
            "custom_components.unraid_management_agent.repairs.ir.async_delete_issue"
        ) as mock_delete,
    ):
        await async_check_and_create_issues(hass, coordinator)

    # Check temperature issues were deleted (for missing temp, both are deleted)
    delete_calls = [str(call) for call in mock_delete.call_args_list]
    # Should delete both warning and critical temp issues when no temp reading
    assert any("high_temp" in str(call) for call in delete_calls)
    assert any("critical_temp" in str(call) for call in delete_calls)


def _disk(**kwargs: Any) -> DiskInfo:
    """Return disk1 with a serial and a passing SMART status by default."""
    defaults: dict[str, Any] = {
        "id": "disk1",
        "name": "disk1",
        "serial_number": "SER1",
        "smart_status": "PASSED",
        "smart_errors": 0,
        "temperature_celsius": 35,
    }
    return DiskInfo(**{**defaults, **kwargs})


async def _check(
    hass: HomeAssistant, entry: MockConfigEntry, disks: list[DiskInfo] | None
) -> None:
    """Run the issue check against the real registry and config entry."""
    coordinator = MagicMock()
    coordinator.config_entry = entry
    coordinator.last_update_success = True
    await async_check_and_create_issues(
        hass, coordinator, UnraidData(disks=disks, array=None)
    )


def _issue(
    hass: HomeAssistant, entry: MockConfigEntry, kind: str
) -> ir.IssueEntry | None:
    """Return a disk1 issue of the entry from the real registry."""
    return ir.async_get(hass).async_get_issue(
        DOMAIN, f"disk_health_{entry.entry_id}_disk1_{kind}"
    )


async def _acknowledge(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    """Complete the repair flow of disk1's current I/O error issue."""
    issue = _issue(hass, entry, "io_errors")
    assert issue is not None
    flow = await async_create_fix_flow(hass, issue.issue_id, issue.data)
    assert isinstance(flow, DiskIOErrorRepairFlow)
    form = await flow.async_step_init()
    assert form["type"] == "form"
    assert form["description_placeholders"]["io_errors"] == str(issue.data["io_errors"])
    result = await flow.async_step_init(user_input={})
    assert result["type"] == "create_entry"


@pytest.fixture
def entry(hass: HomeAssistant) -> MockConfigEntry:
    """Return a config entry registered with Home Assistant."""
    config_entry = MockConfigEntry(domain=DOMAIN, options={"keep": True})
    config_entry.add_to_hass(hass)
    return config_entry


async def test_io_errors_with_smart_passed_are_not_a_smart_failure(
    hass: HomeAssistant, entry: MockConfigEntry
) -> None:
    """The reported case: PASSED with 72 I/O errors raises only an I/O issue."""
    await _check(hass, entry, [_disk(smart_errors=72)])

    issue = _issue(hass, entry, "io_errors")
    assert issue is not None
    assert issue.translation_key == "disk_io_errors"
    assert issue.severity == ir.IssueSeverity.WARNING
    assert issue.is_fixable is True
    assert _issue(hass, entry, "smart_failure") is None


async def test_acknowledgement_persists_until_count_increases(
    hass: HomeAssistant, entry: MockConfigEntry
) -> None:
    """An acknowledged count stays quiet, and a higher count warns again."""
    await _check(hass, entry, [_disk(smart_errors=72)])
    await _acknowledge(hass, entry)

    assert _issue(hass, entry, "io_errors") is None
    assert entry.options[CONF_ACKNOWLEDGED_DISK_IO_ERRORS] == {"SER1": 72}
    assert entry.options["keep"] is True

    await _check(hass, entry, [_disk(smart_errors=72)])
    assert _issue(hass, entry, "io_errors") is None

    await _check(hass, entry, [_disk(smart_errors=73)])
    issue = _issue(hass, entry, "io_errors")
    assert issue is not None
    assert issue.translation_placeholders["acknowledged"] == "72"


async def test_acknowledges_displayed_count_not_latest(
    hass: HomeAssistant, entry: MockConfigEntry
) -> None:
    """Errors counted after the issue was shown are not acknowledged."""
    await _check(hass, entry, [_disk(smart_errors=72)])
    issue = _issue(hass, entry, "io_errors")
    assert issue is not None
    await _check(hass, entry, [_disk(smart_errors=75)])

    flow = await async_create_fix_flow(hass, issue.issue_id, issue.data)
    await flow.async_step_init(user_input={})

    assert entry.options[CONF_ACKNOWLEDGED_DISK_IO_ERRORS] == {"SER1": 72}
    await _check(hass, entry, [_disk(smart_errors=75)])
    assert _issue(hass, entry, "io_errors") is not None


async def test_counter_reset_removes_acknowledgement(
    hass: HomeAssistant, entry: MockConfigEntry
) -> None:
    """Errors after a counter reset are new errors."""
    hass.config_entries.async_update_entry(
        entry, options={CONF_ACKNOWLEDGED_DISK_IO_ERRORS: {"SER1": 72, "SER2": 3}}
    )
    await _check(hass, entry, [_disk(smart_errors=5)])

    assert entry.options[CONF_ACKNOWLEDGED_DISK_IO_ERRORS] == {"SER2": 3}
    issue = _issue(hass, entry, "io_errors")
    assert issue is not None
    assert issue.translation_placeholders["acknowledged"] == "0"


async def test_unavailable_data_changes_nothing(
    hass: HomeAssistant, entry: MockConfigEntry
) -> None:
    """A missing count or disk list keeps issues and acknowledgements."""
    stored = {CONF_ACKNOWLEDGED_DISK_IO_ERRORS: {"SER1": 5, "GONE": 1}}
    hass.config_entries.async_update_entry(entry, options=stored)
    await _check(hass, entry, [_disk(smart_errors=9)])
    assert _issue(hass, entry, "io_errors") is not None

    await _check(hass, entry, [_disk(smart_errors=None)])
    await _check(hass, entry, None)
    await _check(hass, entry, [])

    assert _issue(hass, entry, "io_errors") is not None
    assert entry.options == stored


async def test_replacement_disk_is_not_acknowledged(
    hass: HomeAssistant, entry: MockConfigEntry
) -> None:
    """An acknowledgement follows the serial, not the slot."""
    hass.config_entries.async_update_entry(
        entry, options={CONF_ACKNOWLEDGED_DISK_IO_ERRORS: {"SER1": 72}}
    )
    await _check(hass, entry, [_disk(serial_number="SER2", smart_errors=1)])
    assert _issue(hass, entry, "io_errors") is not None


async def test_disk_without_identity_cannot_be_acknowledged(
    hass: HomeAssistant, entry: MockConfigEntry
) -> None:
    """Without a serial or ID nothing can bind an acknowledgement to the disk."""
    await _check(
        hass, entry, [_disk(id=None, name="disk1", serial_number=None, smart_errors=4)]
    )
    issue = _issue(hass, entry, "io_errors")
    assert issue is not None
    assert issue.is_fixable is False


async def test_smart_failure_is_independent_of_acknowledgement(
    hass: HomeAssistant, entry: MockConfigEntry
) -> None:
    """SMART FAILED raises its issue even when the I/O count is acknowledged."""
    hass.config_entries.async_update_entry(
        entry, options={CONF_ACKNOWLEDGED_DISK_IO_ERRORS: {"SER1": 72}}
    )
    await _check(hass, entry, [_disk(smart_status="FAILED", smart_errors=72)])

    issue = _issue(hass, entry, "smart_failure")
    assert issue is not None
    assert issue.severity == ir.IssueSeverity.ERROR
    assert issue.is_fixable is False
    assert _issue(hass, entry, "io_errors") is None


@pytest.mark.parametrize("status", [None, "UNKNOWN"])
async def test_smart_failure_survives_unknown_status(
    hass: HomeAssistant, entry: MockConfigEntry, status: str | None
) -> None:
    """A spun-down disk does not clear a failure; a healthy status does."""
    await _check(hass, entry, [_disk(smart_status="FAILED")])
    await _check(hass, entry, [_disk(smart_status=status)])
    assert _issue(hass, entry, "smart_failure") is not None

    await _check(hass, entry, [_disk(smart_status="PASSED")])
    assert _issue(hass, entry, "smart_failure") is None


async def test_legacy_smart_errors_issue_is_removed(
    hass: HomeAssistant, entry: MockConfigEntry
) -> None:
    """The combined issue from older versions does not survive an update."""
    ir.async_create_issue(
        hass,
        DOMAIN,
        "disk_health_disk1_smart_errors",
        is_fixable=True,
        severity=ir.IssueSeverity.WARNING,
        translation_key="disk_smart_errors",
    )
    await _check(hass, entry, [_disk()])
    assert (
        ir.async_get(hass).async_get_issue(DOMAIN, "disk_health_disk1_smart_errors")
        is None
    )


async def test_acknowledge_flow_without_entry_only_clears_issue(
    hass: HomeAssistant,
) -> None:
    """A stale payload finishes the flow without writing anything."""
    flow = DiskIOErrorRepairFlow(hass, "disk_health_x_io_errors", {"entry_id": "gone"})
    result = await flow.async_step_init(user_input={})
    assert result["type"] == "create_entry"


async def test_delete_disk_issues_keeps_other_entries(
    hass: HomeAssistant, entry: MockConfigEntry
) -> None:
    """Removing an entry deletes only that entry's disk issues."""
    await _check(hass, entry, [_disk(smart_errors=1)])
    other_id = "disk_health_other_disk1_io_errors"
    ir.async_create_issue(
        hass,
        DOMAIN,
        other_id,
        is_fixable=False,
        severity=ir.IssueSeverity.WARNING,
        translation_key="disk_io_errors",
    )
    async_delete_disk_issues(hass, entry.entry_id)

    assert _issue(hass, entry, "io_errors") is None
    assert ir.async_get(hass).async_get_issue(DOMAIN, other_id) is not None
