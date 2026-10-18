"""
Agent collection mode support (tinkerologie/unraid-management-agent#280).

In Dynamic mode the agent runs each collector at its active rate only while
something consumes its data: a WebSocket client subscribed to one of its
topics, or a REST read in the last five minutes. A client without a topic
filter consumes every topic. The integration therefore subscribes to the
topics its entities use, and skips the REST reads of data those topics push
while the WebSocket is connected. Manual mode and older agents keep the
unfiltered WebSocket and the full poll.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Final

from .const import CONF_ENABLE_VM_DEVICES, DEFAULT_ENABLE_VM_DEVICES

if TYPE_CHECKING:
    from .api.models import CollectorStatus
    from .coordinator import UnraidData

COLLECTION_MODE_DYNAMIC: Final = "dynamic"
COLLECTION_MODE_MANUAL: Final = "manual"

# Agent topics the integration consumes: topic -> (collector that publishes
# it, UnraidData fields the coordinator updates from it)
TOPIC_SOURCES: Final[dict[str, tuple[str, tuple[str, ...]]]] = {
    "system_update": ("system", ("system",)),
    "array_status_update": ("array", ("array",)),
    "disk_list_update": ("disk", ("disks",)),
    "share_list_update": ("shares", ("shares",)),
    "container_list_update": ("docker", ("containers",)),
    "vm_list_update": ("vm", ("vms",)),
    "vm_guest_update": ("vm", ("vm_guest",)),
    "ups_status_update": ("ups", ("ups",)),
    "nut_status_update": ("nut", ("nut",)),
    "gpu_metrics_update": ("gpu", ("gpu",)),
    "network_list_update": ("network", ("network",)),
    "notifications_update": ("notification", ("notifications",)),
    "zfs_pools_update": ("zfs", ("zfs_pools",)),
    "zfs_arc_stats_update": ("zfs", ("zfs_arc",)),
    "fan_control_update": ("fancontrol", ("fan_control",)),
}

# Topics without a collector: collector_state_change (which the agent sends
# under the generic "update" name) and source_status_changed. They create no
# demand, so they are always included.
_EVENT_TOPICS: Final = ("update", "collector_state_change", "source_status_changed")


def collection_mode(status: CollectorStatus | None) -> str | None:
    """
    Return the agent's collection mode: "dynamic", "manual" or None.

    None means an agent without collection modes, or no collector status.
    The top-level mode is preferred; the per-collector one is a fallback.
    """
    if status is None:
        return None
    modes = [status.mode, *(c.mode for c in status.collectors or [])]
    for mode in modes:
        if isinstance(mode, str):
            normalized = mode.strip().lower()
            if normalized in (COLLECTION_MODE_DYNAMIC, COLLECTION_MODE_MANUAL):
                return normalized
    return None


def _collector_enabled(status: CollectorStatus, name: str) -> bool:
    """Return False only for a collector the agent reports as disabled."""
    collector = status.get_collector_by_name(name)
    if collector is None or collector.enabled is None:
        return True
    return bool(collector.enabled)


def subscription_topics(
    data: UnraidData | None, options: Mapping[str, Any]
) -> list[str] | None:
    """
    Return the topic filter to send, or None to receive every topic.

    A filter is only used in Dynamic mode. It holds the topics of enabled
    collectors whose data the entities use; guest agent data only while VMs
    are shown as devices.
    """
    if (
        data is None
        or data.collectors is None
        or collection_mode(data.collectors) != COLLECTION_MODE_DYNAMIC
    ):
        return None
    status = data.collectors
    vm_devices = bool(options.get(CONF_ENABLE_VM_DEVICES, DEFAULT_ENABLE_VM_DEVICES))
    topics = [
        topic
        for topic, (collector, _fields) in TOPIC_SOURCES.items()
        if _collector_enabled(status, collector)
        and (topic != "vm_guest_update" or vm_devices)
    ]
    return sorted([*topics, *_EVENT_TOPICS])


def pushed_fields(topics: list[str] | None) -> frozenset[str]:
    """Return the UnraidData fields the subscribed topics keep up to date."""
    if not topics:
        return frozenset()
    return frozenset(
        field
        for topic in topics
        if topic in TOPIC_SOURCES
        for field in TOPIC_SOURCES[topic][1]
    )
