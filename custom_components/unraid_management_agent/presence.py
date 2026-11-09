"""Resource presence decisions shared by manual removal and stale cleanup."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import TYPE_CHECKING

from .entity import (
    gpu_device_identifier,
    gpu_device_keys,
    hwmon_controller_identifier,
    zfs_pool_device_identifier,
)
from .hwmon import hid_drivers_without_ids, hwmon_controller_of

if TYPE_CHECKING:
    from collections.abc import Collection, Container

    from .api.models import ContainerInfo, GPUInfo, VMInfo, ZFSPool
    from .coordinator import UnraidData


class Presence(Enum):
    """Whether a complete inventory includes a particular resource."""

    PRESENT = auto()
    ABSENT = auto()
    UNKNOWN = auto()


@dataclass(frozen=True)
class Inventory[T]:
    """The last report of an inventory, including unavailability."""

    items: list[T] | None

    @property
    def known(self) -> bool:
        """Return whether this report is usable as evidence of absence."""
        return self.items is not None


def vms(data: UnraidData | None) -> Inventory[VMInfo]:
    """Return the VM inventory."""
    return Inventory(data.vms if data else None)


def containers(data: UnraidData | None) -> Inventory[ContainerInfo]:
    """Return the container inventory."""
    return Inventory(data.containers if data else None)


def gpus(data: UnraidData | None) -> Inventory[GPUInfo]:
    """Return the GPU inventory."""
    return Inventory(data.gpu if data else None)


def pools(data: UnraidData | None) -> Inventory[ZFSPool]:
    """Return the ZFS pool inventory."""
    return Inventory(data.zfs_pools if data else None)


def _membership(key: str, keys: Container[str | None] | None) -> Presence:
    if keys is None:
        return Presence.UNKNOWN
    return Presence.PRESENT if key in keys else Presence.ABSENT


def device_presence(
    data: UnraidData | None, entry_id: str, identifier: str
) -> Presence | None:
    """Classify a recognized device identifier for this configured server."""
    # NIC and storage platform code also registers stale entity cleanup.
    from .nic import current_card_ids
    from .nic import device_identifier as nic_device_identifier
    from .storage import CONTROLLER, ENCLOSURE, current_storage_ids, device_identifier

    if identifier.startswith(nic_prefix := nic_device_identifier(entry_id, "")):
        cards = data.network_cards if data else None
        keys = (
            current_card_ids(cards)
            if cards is not None and cards.state == "ok"
            else None
        )
        return _membership(identifier[len(nic_prefix) :], keys)
    for kind in (CONTROLLER, ENCLOSURE):
        prefix = device_identifier(entry_id, kind, "")
        if identifier.startswith(prefix):
            topology = data.storage_topology if data else None
            keys = (
                current_storage_ids(topology, kind)
                if topology is not None and topology.state == "ok"
                else None
            )
            return _membership(identifier[len(prefix) :], keys)
    if identifier.startswith(vm_prefix := f"{entry_id}_vm_"):
        items = vms(data).items
        keys = {vm.id or vm.name for vm in items} if items is not None else None
        return _membership(identifier[len(vm_prefix) :], keys)
    if identifier.startswith(gpu_prefix := gpu_device_identifier(entry_id, "")):
        items = gpus(data).items
        keys = gpu_device_keys(items).values() if items is not None else None
        return _membership(identifier[len(gpu_prefix) :], keys)
    if identifier.startswith(container_prefix := f"{entry_id}_container_"):
        items = containers(data).items
        keys = {container.name for container in items} if items is not None else None
        return _membership(identifier[len(container_prefix) :], keys)
    if identifier.startswith(f"{entry_id}_hwmon_"):
        system = data.system if data else None
        if system is None or system.fans is None or system.temperatures is None:
            return Presence.UNKNOWN
        readings = [*system.fans, *system.temperatures]
        if hid_drivers_without_ids(readings):
            return Presence.UNKNOWN
        return _membership(
            identifier,
            {
                hwmon_controller_identifier(entry_id, *controller)
                for item in readings
                if (controller := hwmon_controller_of(item)) is not None
            },
        )
    if identifier.startswith(pool_prefix := zfs_pool_device_identifier(entry_id, "")):
        items = pools(data).items
        keys = {pool.name for pool in items if pool.name} if items is not None else None
        return _membership(identifier[len(pool_prefix) :], keys)
    return None


def entity_key_presence(
    key: str, valid_keys: Collection[str], unknown_prefixes: Collection[str]
) -> Presence:
    """Classify a dynamic entity key using available inventory evidence."""
    if key in valid_keys:
        return Presence.PRESENT
    if any(key.startswith(prefix) for prefix in unknown_prefixes):
        return Presence.UNKNOWN
    return Presence.ABSENT
