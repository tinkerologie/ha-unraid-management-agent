"""Tests for the agent's Dynamic collection mode (#233, agent #280)."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Iterator
from datetime import timedelta
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from freezegun.api import FrozenDateTimeFactory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import UpdateFailed
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import (
    AiohttpClientMocker,
)
from websockets.exceptions import ConnectionClosed

from custom_components.unraid_management_agent.api import (
    UnraidClient,
    UnraidConflictError,
    UnraidDynamicCollectionModeError,
    UnraidWebSocketClient,
)
from custom_components.unraid_management_agent.api.models import (
    CollectorDetails,
    CollectorStatus,
    NotificationOverview,
    NotificationsResponse,
    SystemInfo,
    VMGuestInfo,
)
from custom_components.unraid_management_agent.collection import (
    TOPIC_SOURCES,
    collection_mode,
    pushed_fields,
    subscription_topics,
)
from custom_components.unraid_management_agent.const import (
    CONF_ENABLE_VM_DEVICES,
    DOMAIN,
)
from custom_components.unraid_management_agent.coordinator import (
    _DYNAMIC_FULL_POLL_INTERVAL,
    UnraidData,
    UnraidDataUpdateCoordinator,
)
from custom_components.unraid_management_agent.diagnostics import (
    _collector_cadence,
)
from custom_components.unraid_management_agent.sensor import (
    UnraidSystemStatusSensor,
)

from .const import MOCK_CONFIG, mock_array_status

BASE = "http://192.0.2.10:8043/api/v1"
WS_CONNECT = (
    "custom_components.unraid_management_agent.api.websocket.websockets.connect"
)

# Collector status as a Dynamic-mode agent (v2026.10.01) reports it
_DYNAMIC_STATUS = {
    "mode": "dynamic",
    "total": 3,
    "enabled_count": 2,
    "disabled_count": 1,
    "collectors": [
        {
            "name": "system",
            "enabled": True,
            "interval_seconds": 15,
            "status": "running",
            "mode": "dynamic",
            "effective_interval_seconds": 15,
            "reason": "active",
            "event_driven": False,
            "publish_count": 42,
        },
        {
            "name": "docker",
            "enabled": True,
            "interval_seconds": 30,
            "status": "running",
            "mode": "dynamic",
            "effective_interval_seconds": 300,
            "reason": "idle",
            "event_driven": True,
            "publish_count": 7,
        },
        {
            "name": "gpu",
            "enabled": False,
            "interval_seconds": 0,
            "status": "disabled",
            "mode": "dynamic",
            "effective_interval_seconds": 0,
            "reason": "idle",
        },
    ],
}


def _status(mode: str | None = "dynamic", **overrides: Any) -> CollectorStatus:
    data = {**_DYNAMIC_STATUS, "mode": mode, **overrides}
    return CollectorStatus.model_validate(data)


def _data(mode: str | None = "dynamic") -> UnraidData:
    return UnraidData(
        system=SystemInfo(hostname="tower", uptime_seconds=100),
        array=mock_array_status(),
        collectors=_status(mode),
    )


# --- Models -----------------------------------------------------------------


def test_models_parse_collection_mode_fields() -> None:
    """Dynamic-mode fields parse at both levels."""
    status = _status()
    assert status.mode == "dynamic"
    docker = status.get_collector_by_name("docker")
    assert docker is not None
    assert docker.mode == "dynamic"
    assert docker.effective_interval_seconds == 300
    assert docker.reason == "idle"
    assert docker.event_driven is True
    assert docker.publish_count == 7


def test_models_parse_older_agent() -> None:
    """Agents before #280 send none of the fields: they parse as None."""
    status = CollectorStatus.model_validate(
        {"total": 1, "collectors": [{"name": "system", "enabled": True}]}
    )
    assert status.mode is None
    system = status.get_collector_by_name("system")
    assert system is not None
    assert system.mode is None
    assert system.effective_interval_seconds is None
    assert system.reason is None
    assert system.event_driven is None
    assert system.publish_count is None


# --- collection_mode / subscription_topics / pushed_fields ------------------


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (None, None),
        (CollectorStatus(), None),
        (_status("dynamic"), "dynamic"),
        (_status(" Manual "), "manual"),
        (_status("bogus"), "dynamic"),  # falls back to the collectors' mode
        (
            CollectorStatus(collectors=[CollectorDetails(name="x", mode="manual")]),
            "manual",
        ),
        (CollectorStatus(mode="turbo", collectors=[CollectorDetails(name="x")]), None),
    ],
)
def test_collection_mode(status: CollectorStatus | None, expected: str | None) -> None:
    """The top-level mode wins; unknown values fall through to the collectors."""
    assert collection_mode(status) == expected


def test_subscription_topics_none_outside_dynamic_mode() -> None:
    """Manual mode, older agents and missing data keep every topic."""
    assert subscription_topics(None, {}) is None
    assert subscription_topics(_data("manual"), {}) is None
    assert subscription_topics(UnraidData(), {}) is None


def test_subscription_topics_dynamic_mode() -> None:
    """Topics of enabled collectors, plus the collector-less event topics."""
    topics = subscription_topics(_data(), {})
    assert topics is not None
    assert topics == sorted(topics)
    # Disabled collector: its topic is left out
    assert "gpu_metrics_update" not in topics
    # Collectors the agent reports as enabled, or does not list at all
    for topic in (
        "system_update",
        "container_list_update",
        "array_status_update",
        "notifications_update",
        "fan_control_update",
    ):
        assert topic in topics
    # collector_state_change arrives under the generic "update" name
    assert {"update", "collector_state_change", "source_status_changed"} <= set(topics)
    # Guest agent data only while VMs are shown as devices
    assert "vm_guest_update" not in topics
    assert "vm_guest_update" in (
        subscription_topics(_data(), {CONF_ENABLE_VM_DEVICES: True}) or []
    )
    # Data no entity uses is never subscribed to
    for unused in ("hardware_update", "zfs_snapshots_update", "mover_update"):
        assert unused not in topics


def test_subscription_topics_unknown_enabled_state() -> None:
    """A collector without an enabled flag counts as enabled."""
    data = UnraidData(
        collectors=CollectorStatus(
            mode="dynamic", collectors=[CollectorDetails(name="gpu")]
        )
    )
    assert "gpu_metrics_update" in (subscription_topics(data, {}) or [])


def test_pushed_fields() -> None:
    """Fields come from known topics only."""
    assert pushed_fields(None) == frozenset()
    assert pushed_fields([]) == frozenset()
    assert pushed_fields(["update", "system_update", "zfs_pools_update"]) == {
        "system",
        "zfs_pools",
    }
    every_field = {f for _c, fields in TOPIC_SOURCES.values() for f in fields}
    assert pushed_fields(list(TOPIC_SOURCES)) == every_field
    # Every pushed field exists on UnraidData
    assert every_field <= set(UnraidData.__dataclass_fields__)


# --- REST client ------------------------------------------------------------


async def test_update_collector_interval_patch(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """The interval is sent as PATCH {"interval": n}, as the agent expects."""
    aioclient_mock.patch(
        f"{BASE}/collectors/docker/interval",
        json={
            "success": True,
            "collector": {"name": "docker", "interval_seconds": 60},
        },
    )
    client = UnraidClient("192.0.2.10", 8043, session=async_get_clientsession(hass))
    info = await client.update_collector_interval("docker", 60)

    assert info.collector is not None
    assert info.collector.interval_seconds == 60
    method, _url, body, _headers = aioclient_mock.mock_calls[0]
    assert method == "PATCH"
    assert body == {"interval": 60}


async def test_update_collector_interval_dynamic_mode(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """A 409 (Dynamic mode) raises a dedicated, still-409 conflict error."""
    aioclient_mock.patch(
        f"{BASE}/collectors/docker/interval",
        status=409,
        json={"success": False, "message": "dynamic collection mode"},
    )
    client = UnraidClient("192.0.2.10", 8043, session=async_get_clientsession(hass))
    with pytest.raises(UnraidDynamicCollectionModeError) as err:
        await client.update_collector_interval("docker", 60)

    assert isinstance(err.value, UnraidConflictError)
    assert err.value.status_code == 409
    assert "managed by the agent in Dynamic collection mode" in str(err.value)


# --- WebSocket client -------------------------------------------------------


class _FakeSocket:
    """A connection that yields queued messages, then closes."""

    def __init__(self, messages: list[str] | None = None) -> None:
        self.sent: list[Any] = []
        self.closed = False
        self._messages = list(messages or [])
        self.fail_send = False

    async def send(self, message: str) -> None:
        if self.fail_send:
            raise ConnectionClosed(None, None)
        self.sent.append(json.loads(message))

    async def recv(self) -> str:
        if self._messages:
            return self._messages.pop(0)
        raise ConnectionClosed(None, None)

    async def close(self) -> None:
        self.closed = True


class _Connect:
    """Async context manager standing in for websockets.connect()."""

    def __init__(self, socket: _FakeSocket) -> None:
        self.socket = socket

    async def __aenter__(self) -> _FakeSocket:
        return self.socket

    async def __aexit__(self, *args: object) -> None:
        return None


async def test_ws_subscribes_after_connect_before_on_connect() -> None:
    """start() sends the filter on each connection before on_connect runs."""
    socket = _FakeSocket(['{"event": "system_update", "data": {}}'])
    seen_on_connect: list[list[Any]] = []
    client = UnraidWebSocketClient(
        "192.0.2.10",
        topics=["system_update", "update"],
        auto_reconnect=False,
        on_connect=lambda: seen_on_connect.append(list(socket.sent)),
    )
    with patch(WS_CONNECT, return_value=_Connect(socket)):
        await client.start()

    assert socket.sent == [{"subscribe": ["system_update", "update"]}]
    assert seen_on_connect == [[{"subscribe": ["system_update", "update"]}]]
    # Disconnected: no filter is in use any more
    assert client.subscribed_topics is None


async def test_ws_connect_method_subscribes() -> None:
    """connect() also sends the filter."""
    socket = _FakeSocket()
    client = UnraidWebSocketClient("192.0.2.10", topics=["system_update"])
    with patch(WS_CONNECT, return_value=_Connect(socket)):
        await client.connect()
    assert socket.sent == [{"subscribe": ["system_update"]}]


async def test_ws_no_filter_sends_nothing() -> None:
    """Without topics (Manual mode, older agents) no frame is sent."""
    socket = _FakeSocket()
    client = UnraidWebSocketClient("192.0.2.10", auto_reconnect=False)
    with patch(WS_CONNECT, return_value=_Connect(socket)):
        await client.start()
    assert socket.sent == []


async def test_ws_set_topics() -> None:
    """set_topics sends changes on a live connection and resets with null."""
    socket = _FakeSocket()
    client = UnraidWebSocketClient("192.0.2.10")

    # Not connected: stored for the next connection
    await client.set_topics(["system_update"])
    assert socket.sent == []
    assert client.subscribed_topics is None

    client._websocket = socket
    await client._subscribe_on_connect(socket)
    assert client.subscribed_topics == ["system_update"]

    await client.set_topics(["system_update"])  # unchanged: nothing sent
    await client.set_topics(["array_status_update", "system_update"])
    await client.set_topics(None)
    assert socket.sent == [
        {"subscribe": ["system_update"]},
        {"subscribe": ["array_status_update", "system_update"]},
        {"subscribe": None},
    ]
    assert client.subscribed_topics is None

    # Never filtered on this connection: None needs no reset frame
    await client.set_topics(None)
    assert len(socket.sent) == 3


async def test_ws_set_topics_connection_closed() -> None:
    """A send on a closing connection is retried on the next connection."""
    socket = _FakeSocket()
    client = UnraidWebSocketClient("192.0.2.10")
    client._websocket = socket
    socket.fail_send = True

    await client.set_topics(["system_update"])

    assert client.subscribed_topics is None
    socket.fail_send = False
    # The same filter is retried, since the agent never received it
    await client.set_topics(["system_update"])
    assert socket.sent == [{"subscribe": ["system_update"]}]
    assert client.subscribed_topics == ["system_update"]


async def test_ws_overlapping_filter_changes() -> None:
    """A change made while a send is in flight is sent next and recorded."""
    socket = _FakeSocket()
    client = UnraidWebSocketClient("192.0.2.10")
    client._websocket = socket
    release = asyncio.Event()
    sent_first = asyncio.Event()
    real_send = socket.send

    async def slow_send(message: str) -> None:
        if not sent_first.is_set():
            sent_first.set()
            await release.wait()
        await real_send(message)

    socket.send = slow_send  # type: ignore[method-assign]
    first = asyncio.create_task(client.set_topics(["system_update"]))
    await sent_first.wait()
    second = asyncio.create_task(client.set_topics(["array_status_update"]))
    await asyncio.sleep(0)
    # Mid-send the filter is unknown
    assert client.subscribed_topics is None
    release.set()
    await asyncio.gather(first, second)

    assert socket.sent == [
        {"subscribe": ["system_update"]},
        {"subscribe": ["array_status_update"]},
    ]
    assert client.subscribed_topics == ["array_status_update"]


async def test_ws_failed_filter_change_reports_unfiltered() -> None:
    """A failed change on a filtered connection does not report the old filter."""
    socket = _FakeSocket()
    client = UnraidWebSocketClient("192.0.2.10", topics=["system_update"])
    client._websocket = socket
    await client._subscribe_on_connect(socket)

    async def broken_send(message: str) -> None:
        msg = "send failed"
        raise OSError(msg)

    socket.send = broken_send  # type: ignore[method-assign]
    with pytest.raises(OSError):
        await client.set_topics(["array_status_update"])
    assert client.subscribed_topics is None


async def test_ws_unfiltered_connection_set_topics() -> None:
    """A first filter on an unfiltered live connection is sent right away."""
    socket = _FakeSocket()
    client = UnraidWebSocketClient("192.0.2.10")
    client._websocket = socket
    await client._subscribe_on_connect(socket)
    assert socket.sent == []

    await client.set_topics(["system_update"])
    assert socket.sent == [{"subscribe": ["system_update"]}]
    assert client.subscribed_topics == ["system_update"]


# --- Coordinator ------------------------------------------------------------


def _entry(
    hass: HomeAssistant, options: dict[str, Any] | None = None
) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN, data=MOCK_CONFIG, options=options or {}, entry_id="dyn"
    )
    entry.add_to_hass(hass)
    return entry


@pytest.fixture(autouse=True)
def _no_repairs() -> Iterator[None]:
    """Skip repair checks during updates."""
    with patch(
        "custom_components.unraid_management_agent.repairs.async_check_and_create_issues",
        new_callable=AsyncMock,
    ):
        yield


@pytest.fixture
def coordinator(hass: HomeAssistant) -> UnraidDataUpdateCoordinator:
    """Coordinator against a Dynamic-mode agent; other endpoints give None."""
    client = MagicMock()
    client.host = "192.0.2.10"
    client.port = 8043
    client.get_system_info = AsyncMock(
        return_value=SystemInfo(hostname="tower", uptime_seconds=1000)
    )
    client.get_array_status = AsyncMock(return_value=mock_array_status())
    client.get_collectors_status = AsyncMock(return_value=_status())
    client.list_notifications = AsyncMock(
        return_value=NotificationsResponse(notifications=[])
    )
    client.get_notification_overview = AsyncMock(return_value=NotificationOverview())
    return UnraidDataUpdateCoordinator(
        hass, entry=_entry(hass), client=client, enable_websocket=True
    )


def _ws(topics: list[str] | None) -> MagicMock:
    ws = MagicMock()
    ws.subscribed_topics = topics
    ws.is_connected = topics is not None
    ws.set_topics = AsyncMock()
    return ws


async def _poll(coordinator: UnraidDataUpdateCoordinator) -> UnraidData:
    coordinator.data = await coordinator._async_update_data()
    return coordinator.data


async def test_dynamic_mode_skips_pushed_rest_reads(
    coordinator: UnraidDataUpdateCoordinator, freezer: FrozenDateTimeFactory
) -> None:
    """Between full polls, data the subscribed topics push is not fetched."""
    client = coordinator.client
    first = await _poll(coordinator)  # no WebSocket yet: full poll
    assert client.get_system_info.await_count == 1

    topics = subscription_topics(first, {})
    coordinator._ws_client = _ws(topics)
    assert coordinator.websocket_topics == topics

    freezer.tick(timedelta(seconds=30))
    data = await _poll(coordinator)
    assert client.get_system_info.await_count == 1
    assert client.get_array_status.await_count == 1
    assert client.list_notifications.await_count == 1
    assert client.get_notification_overview.await_count == 1
    # Kept values, not None
    assert data.system is first.system
    assert data.array is first.array
    assert data.notifications is first.notifications
    # Endpoints without a topic are still read every poll
    assert client.get_collectors_status.await_count == 2
    coordinator._ws_client.set_topics.assert_awaited_with(topics)

    # The safety net: everything is fetched once the interval has passed
    freezer.tick(_DYNAMIC_FULL_POLL_INTERVAL)
    await _poll(coordinator)
    assert client.get_system_info.await_count == 2
    assert client.get_notification_overview.await_count == 2


async def test_push_during_poll_is_kept(
    coordinator: UnraidDataUpdateCoordinator, freezer: FrozenDateTimeFactory
) -> None:
    """A WebSocket push that arrives while a skipped poll awaits is not undone."""
    first = await _poll(coordinator)
    coordinator._ws_client = _ws(subscription_topics(first, {}))
    pushed = SystemInfo(hostname="tower", uptime_seconds=2000)

    async def collectors_status() -> CollectorStatus:
        # The event arrives while the poll waits on REST calls
        coordinator.data.system = pushed
        return _status()

    coordinator.client.get_collectors_status.side_effect = collectors_status
    freezer.tick(timedelta(seconds=30))
    data = await _poll(coordinator)
    assert data.system is pushed


async def test_skipped_poll_detects_unreachable_agent(
    coordinator: UnraidDataUpdateCoordinator, freezer: FrozenDateTimeFactory
) -> None:
    """With system and array kept, a failed collector status fails the update."""
    first = await _poll(coordinator)
    coordinator._ws_client = _ws(subscription_topics(first, {}))
    coordinator.client.get_collectors_status.side_effect = Exception("down")
    freezer.tick(timedelta(seconds=30))
    with pytest.raises(UpdateFailed):
        await _poll(coordinator)
    coordinator.client.get_system_info.assert_awaited_once()


async def test_vm_guest_kept_between_full_polls(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """With VM devices on, guest data is pushed and not fetched between full polls."""
    client = MagicMock()
    client.host = "192.0.2.10"
    client.port = 8043
    client.get_system_info = AsyncMock(
        return_value=SystemInfo(hostname="tower", uptime_seconds=1000)
    )
    client.get_array_status = AsyncMock(return_value=mock_array_status())
    client.get_collectors_status = AsyncMock(return_value=_status())
    guests = [VMGuestInfo(vm_name="Home Assistant")]
    client.get_vm_guest = AsyncMock(return_value=guests)
    coordinator = UnraidDataUpdateCoordinator(
        hass,
        entry=_entry(hass, {CONF_ENABLE_VM_DEVICES: True}),
        client=client,
        enable_websocket=True,
    )
    first = await _poll(coordinator)
    assert first.vm_guest == guests
    topics = subscription_topics(first, coordinator.config_entry.options)
    assert topics is not None
    assert "vm_guest_update" in topics
    coordinator._ws_client = _ws(topics)

    freezer.tick(timedelta(seconds=30))
    data = await _poll(coordinator)
    client.get_vm_guest.assert_awaited_once()
    assert data.vm_guest == guests


async def test_topic_filter_send_error_does_not_fail_poll(
    coordinator: UnraidDataUpdateCoordinator,
) -> None:
    """An error sending the filter is logged; the poll still succeeds."""
    coordinator._ws_client = _ws(None)
    coordinator._ws_client.set_topics.side_effect = OSError("send failed")
    data = await _poll(coordinator)
    assert data.system is not None
    coordinator._ws_client.set_topics.assert_awaited_once_with(
        subscription_topics(data, coordinator.config_entry.options)
    )


async def test_reconnect_forces_full_poll(
    coordinator: UnraidDataUpdateCoordinator, freezer: FrozenDateTimeFactory
) -> None:
    """Events may be missed while disconnected: the next poll reads everything."""
    first = await _poll(coordinator)
    coordinator._ws_client = _ws(subscription_topics(first, {}))
    coordinator._handle_ws_connect()

    freezer.tick(timedelta(seconds=30))
    await _poll(coordinator)
    assert coordinator.client.get_system_info.await_count == 2


async def test_unfiltered_websocket_keeps_full_poll(
    coordinator: UnraidDataUpdateCoordinator, freezer: FrozenDateTimeFactory
) -> None:
    """Manual mode, or a WebSocket without a filter, polls everything."""
    await _poll(coordinator)
    coordinator._ws_client = _ws(None)
    freezer.tick(timedelta(seconds=30))
    await _poll(coordinator)
    assert coordinator.client.get_system_info.await_count == 2


async def test_manual_mode_resets_filter(
    coordinator: UnraidDataUpdateCoordinator,
) -> None:
    """Switching the agent to Manual mode sends no filter (every topic)."""
    coordinator.client.get_collectors_status.return_value = _status("manual")
    coordinator._ws_client = _ws(None)
    await _poll(coordinator)
    coordinator._ws_client.set_topics.assert_awaited_once_with(None)
    assert coordinator.collection_mode == "manual"


async def test_missing_collector_status_keeps_filter(
    coordinator: UnraidDataUpdateCoordinator,
) -> None:
    """A failed collector status fetch leaves the current filter alone."""
    coordinator.client.get_collectors_status.side_effect = Exception("down")
    coordinator._ws_client = _ws(["system_update"])
    await _poll(coordinator)
    coordinator._ws_client.set_topics.assert_not_awaited()
    assert coordinator.collection_mode is None


async def test_fetch_pushed_without_data(
    coordinator: UnraidDataUpdateCoordinator,
) -> None:
    """A skipped field with no data yet gives None."""
    coordinator._skip_fields = frozenset({"system"})
    coordinator.data = None
    fetch = AsyncMock()
    assert await coordinator._fetch("system", fetch, pushed="system") is None
    fetch.assert_not_awaited()


async def test_websocket_started_with_filter(
    coordinator: UnraidDataUpdateCoordinator,
) -> None:
    """The WebSocket client is created with the filter for the current data."""
    coordinator.data = _data()
    with patch(
        "custom_components.unraid_management_agent.coordinator.UnraidWebSocketClient"
    ) as ws_class:
        ws_class.return_value.is_connected = False
        ws_class.return_value.start = MagicMock()
        with patch.object(coordinator.config_entry, "async_create_background_task"):
            await coordinator.async_start_websocket()
    assert ws_class.call_args.kwargs["topics"] == subscription_topics(
        coordinator.data, {}
    )


def test_coordinator_properties_without_data(
    coordinator: UnraidDataUpdateCoordinator,
) -> None:
    """No data and no WebSocket: mode and filter are unknown."""
    coordinator.data = None
    assert coordinator.collection_mode is None
    assert coordinator.websocket_topics is None
    assert coordinator._pushed_fields_to_skip() == frozenset()


# --- Visibility -------------------------------------------------------------


def test_collector_cadence_diagnostics() -> None:
    """Diagnostics list each collector's effective interval and reason."""
    cadence = _collector_cadence(_data())
    assert cadence[1] == {
        "name": "docker",
        "enabled": True,
        "mode": "dynamic",
        "interval_seconds": 30,
        "effective_interval_seconds": 300,
        "reason": "idle",
    }
    assert _collector_cadence(None) == []
    assert _collector_cadence(UnraidData()) == []


async def test_diagnostics_include_collection_mode(
    hass: HomeAssistant, coordinator: UnraidDataUpdateCoordinator
) -> None:
    """coordinator_health reports the mode and the topic filter."""
    from custom_components.unraid_management_agent.diagnostics import (
        async_get_config_entry_diagnostics,
    )

    coordinator.data = _data()
    coordinator._ws_client = _ws(["system_update"])
    entry = coordinator.config_entry
    entry.runtime_data = SimpleNamespace(coordinator=coordinator)

    diagnostics = await async_get_config_entry_diagnostics(hass, entry)

    health = diagnostics["coordinator_health"]
    assert health["collection_mode"] == "dynamic"
    assert health["websocket_topics"] == ["system_update"]
    assert [c["reason"] for c in diagnostics["collectors"]] == [
        "active",
        "idle",
        "idle",
    ]


@pytest.mark.parametrize(("mode", "expected"), [("dynamic", "dynamic"), (None, None)])
def test_system_status_collection_mode_attribute(
    mode: str | None, expected: str | None
) -> None:
    """The System status sensor shows the mode; older agents leave it out."""
    coordinator = SimpleNamespace(
        websocket_connected=True,
        collection_mode=mode,
        pending_system_action=None,
        pending_system_action_message=None,
        pending_system_action_requested_at=None,
        data=None,
    )
    attrs = UnraidSystemStatusSensor.extra_state_attributes.fget(  # type: ignore[attr-defined]
        SimpleNamespace(coordinator=coordinator)
    )
    assert attrs.get("collection_mode") == expected
