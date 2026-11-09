"""
Reconcile REST reads with events received while Home Assistant awaits a poll.

Home Assistant serializes coordinator refreshes and publishes a returned
snapshot immediately. Replay and return are synchronous so an event cannot
fall between the journal and publication.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from typing import Any

from homeassistant.util import dt as dt_util

from custom_components.unraid_management_agent.api.events import WebSocketEvent
from custom_components.unraid_management_agent.api.models import ParityHistory
from custom_components.unraid_management_agent.collection import (
    pushed_fields,
    subscription_topics,
)

from .event_application import STATEFUL_EVENTS, EventOutcome, apply_event
from .ports import TopicSubscription, UnraidTelemetrySource
from .refresh import Fetch, assemble, build_plan
from .state import UnraidData

_LOGGER = logging.getLogger(__name__)

PARITY_HISTORY_INTERVAL = timedelta(minutes=15)
DYNAMIC_FULL_POLL_INTERVAL = timedelta(minutes=10)


class AgentUnavailableError(Exception):
    """The endpoints that establish reachability did not respond."""


@dataclass(frozen=True)
class RefreshResult:
    """A complete poll result, ready for publication."""

    snapshot: UnraidData
    skipped: frozenset[str]

    @property
    def full_poll(self) -> bool:
        """Return whether no WebSocket-covered field was skipped."""
        return not self.skipped


class UnraidTelemetryReconciler:
    """Own the poll cadence, push application and in-flight event ordering."""

    def __init__(
        self,
        source: UnraidTelemetrySource,
        clock: Callable[[], datetime] = dt_util.utcnow,
    ) -> None:
        """Bind the configured server's telemetry source."""
        self._source = source
        self._clock = clock
        self._last_full_poll: datetime | None = None
        self._generation = 0
        self._parity_history: ParityHistory | None = None
        self._parity_history_fetched_at: datetime | None = None
        self._journal: list[tuple[WebSocketEvent, UnraidData | None]] | None = None

    def invalidate_full_poll(self) -> None:
        """Require a full poll after reconnect, including during a current poll."""
        self._last_full_poll = None
        self._generation += 1

    def apply_event(
        self, snapshot: UnraidData | None, event: WebSocketEvent
    ) -> EventOutcome:
        """Apply a live event and retain it for a concurrent poll result."""
        previous = (
            replace(snapshot)
            if self._journal is not None
            and snapshot is not None
            and isinstance(event, STATEFUL_EVENTS)
            else None
        )
        outcome = apply_event(snapshot, event)
        if outcome is EventOutcome.APPLIED and self._journal is not None:
            self._journal.append((event, previous))
        return outcome

    async def _fetch_parity_history(self) -> ParityHistory | None:
        now = self._clock()
        if self._parity_history_fetched_at is None or (
            now - self._parity_history_fetched_at >= PARITY_HISTORY_INTERVAL
        ):
            result = Fetch("parity history", self._source.get_parity_history)
            await result.run()
            if result.value is not None:
                self._parity_history = result.value
                self._parity_history_fetched_at = now
        return self._parity_history

    async def refresh(
        self,
        current: UnraidData | None,
        options: Mapping[str, Any],
        subscription: TopicSubscription | None,
    ) -> RefreshResult:
        """Return a snapshot that includes newer events received during reads."""
        topics = subscription.subscribed_topics if subscription else None
        skipped: frozenset[str] = frozenset()
        if (
            current is not None
            and topics
            and self._last_full_poll is not None
            and self._clock() - self._last_full_poll < DYNAMIC_FULL_POLL_INTERVAL
        ):
            skipped = pushed_fields(topics)
        generation = self._generation
        retained = replace(current) if current is not None else None
        plan = build_plan(self._source, retained, options, self._fetch_parity_history)
        journal: list[tuple[WebSocketEvent, UnraidData | None]] = []
        self._journal = journal
        try:
            await asyncio.gather(*(slot.run(skipped) for slot in plan.initial_reads()))
            if {"system", "array"} <= skipped:
                unreachable = plan.collectors.value is None
            else:
                unreachable = plan.system.value is None and plan.array.value is None
            if unreachable:
                raise AgentUnavailableError
            await plan.container_updates.run()
            snapshot = assemble(plan, retained)

            if subscription is not None and snapshot.collectors is not None:
                try:
                    await subscription.set_topics(
                        subscription_topics(snapshot, options)
                    )
                except Exception as err:
                    _LOGGER.debug("Error sending WebSocket topic filter: %s", err)

            for event, previous in journal:
                apply_event(snapshot, event, previous=previous)
            if not skipped and self._generation == generation:
                self._last_full_poll = self._clock()
            return RefreshResult(snapshot, skipped)
        finally:
            self._journal = None
