"""Test the agent alert rule binary sensors, alert event and firing alerts sensor."""

from __future__ import annotations

from datetime import timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.const import EVENT_STATE_CHANGED, STATE_UNAVAILABLE
from homeassistant.core import Event, HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util
from pytest_homeassistant.common import MockConfigEntry

from custom_components.unraid_management_agent.alerts import (
    ALERT_RULE_KEY_PREFIX,
    alert_rule_key,
    alert_rule_names,
    alert_since,
    find_alert_rule,
    find_alert_status,
)
from custom_components.unraid_management_agent.api.exceptions import (
    UnraidNotFoundError,
)
from custom_components.unraid_management_agent.api.models import (
    AlertRule,
    AlertsStatusResponse,
    AlertStatus,
)
from custom_components.unraid_management_agent.binary_sensor import (
    BINARY_SENSOR_DESCRIPTIONS,
)
from custom_components.unraid_management_agent.cleanup import (
    _ALWAYS_VALID_KEYS,
    _DYNAMIC_KEY_PREFIXES,
    STALE_REMOVAL_GRACE,
    _build_valid_dynamic_entity_keys,
    _unavailable_data_prefixes,
    async_cleanup_stale_entities,
)
from custom_components.unraid_management_agent.const import DOMAIN
from custom_components.unraid_management_agent.coordinator import UnraidData
from custom_components.unraid_management_agent.diagnostics import (
    async_get_config_entry_diagnostics,
)
from custom_components.unraid_management_agent.event import UnraidAlertEvent
from custom_components.unraid_management_agent.sensor import (
    ALERTS_FIRING_DESCRIPTION,
)

from .const import MOCK_CONFIG, MOCK_OPTIONS

ENTRY_ID = "test_entry_id"

# GET /api/v1/alerts/rules and /alerts/status as returned by agent v2026.09.01:
# the built-in rule, plus two rules enabled from the agent's templates
# (/alerts/templates) and one of them disabled again. The ntfy URL is made up.
DEGRADED = {
    "id": "subsystem-degraded",
    "name": "Agent data source degraded",
    "expression": "DegradedSubsystemCount > 0",
    "severity": "warning",
    "channels": ["unraid"],
    "enabled": True,
    "cooldown_minutes": 60,
}
TEMP_CLIMB = {
    "id": "tmpl-disk-temp-climb",
    "name": "Disk temperature climbing",
    "expression": "MaxDiskTempSlopePerMin > 1",
    "severity": "warning",
    "channels": ["unraid", "ntfy://user:secret@ntfy.example.com/unraid"],
    "enabled": True,
    "cooldown_minutes": 30,
}
REALLOCATED = {
    "id": "tmpl-smart-reallocated",
    "name": "Disk reallocated sectors detected",
    "expression": "MaxReallocatedSectors > 0",
    "severity": "critical",
    "channels": ["unraid"],
    "enabled": False,
    "cooldown_minutes": 1440,
}
ZERO_TIME = "0001-01-01T00:00:00Z"
FIRING_SINCE = "2026-10-08T12:34:56.123456789+10:00"


def _status(rule: dict[str, Any], state: str, since: str = ZERO_TIME) -> AlertStatus:
    return AlertStatus.model_validate(
        {
            "rule_id": rule["id"],
            "rule_name": rule["name"],
            "state": state,
            "severity": rule["severity"],
            "since": since,
            "eval_count": 2925,
        }
    )


def _rules(*rules: dict[str, Any]) -> list[AlertRule]:
    return [AlertRule.model_validate(rule) for rule in rules]


def _statuses(*statuses: AlertStatus) -> AlertsStatusResponse:
    return AlertsStatusResponse(statuses=list(statuses))


def _entry(hass: HomeAssistant) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Unraid (unraid-test)",
        data=MOCK_CONFIG,
        options=MOCK_OPTIONS,
        entry_id=ENTRY_ID,
    )
    entry.add_to_hass(hass)
    return entry


def _alert_entity_id(registry: er.EntityRegistry, rule_id: str) -> str | None:
    return registry.async_get_entity_id(
        "binary_sensor", DOMAIN, f"{ENTRY_ID}_{alert_rule_key(rule_id)}"
    )


def _static_entity_id(registry: er.EntityRegistry, platform: str, key: str) -> str:
    entity_id = registry.async_get_entity_id(platform, DOMAIN, f"{ENTRY_ID}_{key}")
    assert entity_id is not None
    return entity_id


async def _setup(hass: HomeAssistant, client: MagicMock) -> MockConfigEntry:
    client.list_alert_rules.return_value = _rules(DEGRADED, TEMP_CLIMB, REALLOCATED)
    client.get_alerts_status.return_value = _statuses(
        _status(DEGRADED, "ok"), _status(TEMP_CLIMB, "firing", FIRING_SINCE)
    )
    entry = _entry(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


def _capture_alert_events(hass: HomeAssistant, entity_id: str) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []

    def _listener(event: Event) -> None:
        new_state, old_state = event.data["new_state"], event.data["old_state"]
        if (
            event.data["entity_id"] == entity_id
            and new_state is not None
            and new_state.attributes.get("event_type")
            and (old_state is None or new_state.state != old_state.state)
        ):
            events.append(dict(new_state.attributes))

    hass.bus.async_listen(EVENT_STATE_CHANGED, _listener)
    return events


# ── Helpers ───────────────────────────────────────────────────────────────────


def test_alert_rule_key() -> None:
    """Keys use the alert_rule_ prefix and keep look-alike IDs apart."""
    key = alert_rule_key("subsystem-degraded")
    assert key.startswith("alert_rule_subsystem_degraded_")
    assert alert_rule_key("disk-temp") != alert_rule_key("disk_temp")
    assert alert_rule_key("subsystem-degraded") == key


def test_alert_rule_names() -> None:
    """Names come from the rule list, falling back to the status list."""
    assert alert_rule_names(None) == {}
    assert alert_rule_names(UnraidData()) == {}
    nameless = AlertRule(id="custom")
    no_id = AlertRule(name="No ID")
    assert alert_rule_names(
        UnraidData(alert_rules=[*_rules(DEGRADED), nameless, no_id])
    ) == {"subsystem-degraded": "Agent data source degraded", "custom": "custom"}
    # Rule list unavailable: enabled rules are still known from their status
    statuses = [_status(TEMP_CLIMB, "ok"), AlertStatus(rule_id="x"), AlertStatus()]
    assert alert_rule_names(UnraidData(alert_statuses=statuses)) == {
        "tmpl-disk-temp-climb": "Disk temperature climbing",
        "x": "x",
    }


def test_find_alert_rule_and_status() -> None:
    """Lookups return None without data or for unknown rules."""
    data = UnraidData(
        alert_rules=_rules(DEGRADED), alert_statuses=[_status(DEGRADED, "ok")]
    )
    assert find_alert_rule(None, "subsystem-degraded") is None
    assert find_alert_status(None, "subsystem-degraded") is None
    assert find_alert_rule(data, "missing") is None
    assert find_alert_status(data, "missing") is None
    rule = find_alert_rule(data, "subsystem-degraded")
    assert rule is not None
    assert rule.cooldown_minutes == 60
    status = find_alert_status(data, "subsystem-degraded")
    assert status is not None
    assert status.state == "ok"


def test_alert_since() -> None:
    """Go's zero time and unparsable values are reported as no timestamp."""
    assert alert_since(_status(DEGRADED, "ok")) is None
    assert alert_since(AlertStatus(rule_id="x")) is None
    assert alert_since(AlertStatus(rule_id="x", since="soon")) is None
    since = alert_since(_status(TEMP_CLIMB, "firing", FIRING_SINCE))
    assert since is not None
    assert since.isoformat() == "2026-10-08T12:34:56.123456+10:00"


def test_alert_rule_prefix_matches_no_static_key() -> None:
    """No static entity key starts with the dynamic alert rule prefix."""
    static_keys = {d.key for d in BINARY_SENSOR_DESCRIPTIONS} | set(_ALWAYS_VALID_KEYS)
    static_keys |= {"alert_event", "alerts_firing", ALERTS_FIRING_DESCRIPTION.key}
    assert not [k for k in static_keys if k.startswith(ALERT_RULE_KEY_PREFIX)]
    # ... and the new static keys match no dynamic prefix at all
    for key in ("alert_event", "alerts_firing"):
        assert not any(key.startswith(p) for p in _DYNAMIC_KEY_PREFIXES)


# ── Coordinator ───────────────────────────────────────────────────────────────


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_coordinator_alert_data(
    hass: HomeAssistant, mock_async_unraid_client: MagicMock
) -> None:
    """Rules and statuses are stored; a null status list means no enabled rule."""
    mock_async_unraid_client.list_alert_rules.return_value = _rules(REALLOCATED)
    mock_async_unraid_client.get_alerts_status.return_value = AlertsStatusResponse(
        statuses=None
    )
    entry = _entry(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    data = entry.runtime_data.coordinator.data
    assert [r.id for r in data.alert_rules] == ["tmpl-smart-reallocated"]
    assert data.alert_statuses == []


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_older_agent_without_alerting(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mock_async_unraid_client: MagicMock,
) -> None:
    """Agents without the alerting endpoints (404) get no alert entities."""
    mock_async_unraid_client.list_alert_rules.side_effect = UnraidNotFoundError(
        "404 page not found", status_code=404
    )
    mock_async_unraid_client.get_alerts_status.side_effect = UnraidNotFoundError(
        "404 page not found", status_code=404
    )
    entry = _entry(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    data = entry.runtime_data.coordinator.data
    assert data.alert_rules is None
    assert data.alert_statuses is None
    unique_ids = {
        e.unique_id
        for e in er.async_entries_for_config_entry(entity_registry, ENTRY_ID)
    }
    assert not [u for u in unique_ids if "alert" in u]
    # The agent still reports, so nothing else is affected
    assert entry.runtime_data.coordinator.last_update_success


# ── Entities ──────────────────────────────────────────────────────────────────


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_alert_entities(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mock_async_unraid_client: MagicMock,
) -> None:
    """One problem binary sensor per rule, the alert event and the firing count."""
    await _setup(hass, mock_async_unraid_client)

    degraded_id = _alert_entity_id(entity_registry, "subsystem-degraded")
    assert degraded_id == "binary_sensor.unraid_test_alert_agent_data_source_degraded"
    state = hass.states.get(degraded_id)
    assert state is not None
    assert state.state == "off"
    assert state.attributes["device_class"] == "problem"
    assert state.attributes["rule_id"] == "subsystem-degraded"
    assert state.attributes["severity"] == "warning"
    assert state.attributes["alert_state"] == "ok"
    assert state.attributes["expression"] == "DegradedSubsystemCount > 0"
    assert state.attributes["cooldown_minutes"] == 60
    assert "since" not in state.attributes
    assert "duration_seconds" not in state.attributes
    assert "channels" not in state.attributes

    climb_id = _alert_entity_id(entity_registry, "tmpl-disk-temp-climb")
    assert climb_id is not None
    state = hass.states.get(climb_id)
    assert state is not None
    assert state.state == "on"
    assert state.attributes["alert_state"] == "firing"
    assert state.attributes["since"] == "2026-10-08T12:34:56.123456+10:00"
    assert "channels" not in state.attributes

    # A disabled rule is not evaluated by the agent: unavailable, not "OK"
    reallocated_id = _alert_entity_id(entity_registry, "tmpl-smart-reallocated")
    assert reallocated_id is not None
    state = hass.states.get(reallocated_id)
    assert state is not None
    assert state.state == STATE_UNAVAILABLE

    count_id = _static_entity_id(entity_registry, "sensor", "alerts_firing")
    assert count_id == "sensor.unraid_test_firing_alerts"
    state = hass.states.get(count_id)
    assert state is not None
    assert state.state == "1"
    assert state.attributes["firing_rules"] == ["Disk temperature climbing"]

    event_id = _static_entity_id(entity_registry, "event", "alert_event")
    assert event_id == "event.unraid_test_alert"
    state = hass.states.get(event_id)
    assert state is not None
    # A rule already firing at startup is not reported as a new event
    assert state.state == "unknown"
    assert state.attributes["event_types"] == ["firing", "resolved"]


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_alert_rule_attributes_without_rule_list(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mock_async_unraid_client: MagicMock,
) -> None:
    """Without the rule list, sensors still report the status with a message."""
    status = AlertStatus.model_validate(
        {
            "rule_id": "subsystem-degraded",
            "rule_name": "Agent data source degraded",
            "state": "pending",
            "since": FIRING_SINCE,
            "message": "Agent data source degraded",
            "eval_count": 3,
        }
    )
    mock_async_unraid_client.list_alert_rules.return_value = None
    mock_async_unraid_client.get_alerts_status.return_value = _statuses(status)
    entry = _entry(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    entity_id = _alert_entity_id(entity_registry, "subsystem-degraded")
    assert entity_id is not None
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == "off"
    attributes = {
        k: v
        for k, v in state.attributes.items()
        if k not in ("friendly_name", "device_class", "icon")
    }
    assert attributes == {
        "rule_id": "subsystem-degraded",
        "alert_state": "pending",
        "since": "2026-10-08T12:34:56.123456+10:00",
        "message": "Agent data source degraded",
    }

    # With the rule list back, its severity and definition are added
    data = entry.runtime_data.coordinator.data
    data.alert_rules = _rules(DEGRADED | {"duration_seconds": 300})
    data.alert_statuses = [AlertStatus(rule_id="subsystem-degraded", state="ok")]
    entry.runtime_data.coordinator.async_update_listeners()
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.attributes["severity"] == "warning"
    assert state.attributes["duration_seconds"] == 300
    assert "alert_state" in state.attributes


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_alert_events(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mock_async_unraid_client: MagicMock,
) -> None:
    """Rules that start firing or resolve fire an event each."""
    entry = await _setup(hass, mock_async_unraid_client)
    coordinator = entry.runtime_data.coordinator
    event_id = _static_entity_id(entity_registry, "event", "alert_event")
    events = _capture_alert_events(hass, event_id)
    client = mock_async_unraid_client

    # Degraded starts firing and the temperature rule resolves in the same poll
    client.get_alerts_status.return_value = _statuses(
        _status(DEGRADED, "firing", FIRING_SINCE), _status(TEMP_CLIMB, "ok")
    )
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert [(e["event_type"], e["rule_id"]) for e in events] == [
        ("firing", "subsystem-degraded"),
        ("resolved", "tmpl-disk-temp-climb"),
    ]
    assert events[0]["rule_name"] == "Agent data source degraded"
    assert events[0]["severity"] == "warning"
    assert events[0]["since"] == "2026-10-08T12:34:56.123456+10:00"
    assert "since" not in events[1]
    count = hass.states.get(
        _static_entity_id(entity_registry, "sensor", "alerts_firing")
    )
    assert count is not None
    assert count.state == "1"

    # Alert status unavailable for a poll: no event, and none when it returns
    # unchanged (the last known states are kept)
    client.get_alerts_status.side_effect = UnraidNotFoundError("gone", status_code=404)
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    count = hass.states.get(
        _static_entity_id(entity_registry, "sensor", "alerts_firing")
    )
    assert count is not None
    assert count.state == STATE_UNAVAILABLE
    client.get_alerts_status.side_effect = None
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert len(events) == 2

    # Pending is not firing; a rule that disappears while firing does not resolve
    client.get_alerts_status.return_value = _statuses(_status(TEMP_CLIMB, "pending"))
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert len(events) == 2

    # A status without a rule ID is ignored
    client.get_alerts_status.return_value = _statuses(
        AlertStatus(state="firing"), _status(TEMP_CLIMB, "firing", FIRING_SINCE)
    )
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert [(e["event_type"], e["rule_id"]) for e in events][2:] == [
        ("firing", "tmpl-disk-temp-climb")
    ]


async def test_alert_event_without_initial_status(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """Without alert status at creation, the first status is the baseline."""
    coordinator = MagicMock()
    coordinator.config_entry = mock_config_entry
    coordinator.data = UnraidData()
    entity = UnraidAlertEvent(coordinator)
    entity.hass = hass
    entity.entity_id = "event.test_alert"
    entity.async_write_ha_state = MagicMock()

    coordinator.data = UnraidData(
        alert_statuses=[_status(TEMP_CLIMB, "firing", FIRING_SINCE)]
    )
    entity._handle_coordinator_update()
    entity.async_write_ha_state.assert_called_once()  # state only, no event
    assert entity.state is None

    coordinator.data = UnraidData(alert_statuses=[_status(TEMP_CLIMB, "ok")])
    entity._handle_coordinator_update()
    assert entity.state_attributes["event_type"] == "resolved"


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_alert_entities_added_after_setup(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mock_async_unraid_client: MagicMock,
) -> None:
    """An upgraded agent or a new rule gets its entities without a reload."""
    client = mock_async_unraid_client
    entry = _entry(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert _alert_entity_id(entity_registry, "subsystem-degraded") is None

    client.list_alert_rules.return_value = _rules(DEGRADED)
    client.get_alerts_status.return_value = _statuses(_status(DEGRADED, "ok"))
    coordinator = entry.runtime_data.coordinator
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert _alert_entity_id(entity_registry, "subsystem-degraded") is not None
    _static_entity_id(entity_registry, "event", "alert_event")
    _static_entity_id(entity_registry, "sensor", "alerts_firing")

    # A rule created later (here: enabled from a template) gets a sensor
    client.list_alert_rules.return_value = _rules(DEGRADED, TEMP_CLIMB)
    client.get_alerts_status.return_value = _statuses(
        _status(DEGRADED, "ok"), _status(TEMP_CLIMB, "ok")
    )
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    climb_id = _alert_entity_id(entity_registry, "tmpl-disk-temp-climb")
    assert climb_id is not None

    # Removed from the registry (stale cleanup or by the user): re-created
    entity_registry.async_remove(climb_id)
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert _alert_entity_id(entity_registry, "tmpl-disk-temp-climb") is not None


# ── Stale entity cleanup ──────────────────────────────────────────────────────


def test_cleanup_valid_keys_and_protection() -> None:
    """Every known rule keeps its key; a failed rule fetch protects them all."""
    data = UnraidData(
        alert_rules=_rules(DEGRADED, REALLOCATED),
        alert_statuses=[_status(DEGRADED, "ok")],
    )
    keys = _build_valid_dynamic_entity_keys(data)
    assert alert_rule_key("subsystem-degraded") in keys
    assert alert_rule_key("tmpl-smart-reallocated") in keys
    assert ALERT_RULE_KEY_PREFIX not in _unavailable_data_prefixes(data)
    assert ALERT_RULE_KEY_PREFIX in _unavailable_data_prefixes(
        UnraidData(alert_statuses=[_status(DEGRADED, "ok")])
    )


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_cleanup_removes_deleted_rule_only(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mock_async_unraid_client: MagicMock,
) -> None:
    """A deleted rule's sensor is removed; static alert entities are kept."""
    entry = await _setup(hass, mock_async_unraid_client)
    coordinator = entry.runtime_data.coordinator
    climb_id = _alert_entity_id(entity_registry, "tmpl-disk-temp-climb")
    assert climb_id is not None

    # The rule is deleted on the agent
    coordinator.data.alert_rules = _rules(DEGRADED, REALLOCATED)
    coordinator.data.alert_statuses = [_status(DEGRADED, "ok")]
    async_cleanup_stale_entities(hass, entry, coordinator)
    unique_id = f"{ENTRY_ID}_{alert_rule_key('tmpl-disk-temp-climb')}"
    assert unique_id in coordinator.stale_entity_candidates
    for candidate in coordinator.stale_entity_candidates:
        coordinator.stale_entity_candidates[candidate] = (
            dt_util.utcnow() - STALE_REMOVAL_GRACE - timedelta(seconds=1)
        )
    async_cleanup_stale_entities(hass, entry, coordinator)

    assert _alert_entity_id(entity_registry, "tmpl-disk-temp-climb") is None
    # The disabled rule (no status) and the static entities stay
    assert _alert_entity_id(entity_registry, "tmpl-smart-reallocated") is not None
    assert _alert_entity_id(entity_registry, "subsystem-degraded") is not None
    _static_entity_id(entity_registry, "event", "alert_event")
    _static_entity_id(entity_registry, "sensor", "alerts_firing")


# ── Diagnostics ───────────────────────────────────────────────────────────────


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_diagnostics_redact_alert_channels(
    hass: HomeAssistant, mock_async_unraid_client: MagicMock
) -> None:
    """Notification channels (URLs that can hold credentials) are redacted."""
    # Unmocked client methods return mocks whose model_dump is an AsyncMock
    mock_async_unraid_client.get_diagnostics_self_test.return_value = None
    mock_async_unraid_client.get_docker_port_conflicts.return_value = []
    entry = await _setup(hass, mock_async_unraid_client)
    diagnostics = await async_get_config_entry_diagnostics(hass, entry)
    rules = diagnostics["coordinator_data"]["alert_rules"]
    assert [rule["channels"] for rule in rules] == ["**REDACTED**"] * 3
    assert "secret" not in str(diagnostics)


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_alert_fetch_errors_are_isolated(
    hass: HomeAssistant, mock_async_unraid_client: MagicMock
) -> None:
    """A disabled alerting engine (503) leaves the rest of the data intact."""
    mock_async_unraid_client.get_alerts_status = AsyncMock(
        side_effect=Exception("Alerting engine not initialized")
    )
    entry = _entry(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    coordinator = entry.runtime_data.coordinator
    assert coordinator.last_update_success
    assert coordinator.data.alert_statuses is None
