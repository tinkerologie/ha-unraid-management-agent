"""
Keep hwmon sensors (temperatures, fans) on their entities when their keys change.

USB HID sensor chips (Aquacomputer Octo, Corsair Commander, ...) used to be
keyed by their lm-sensors address, which changes on every USB reconnect, or by
their driver name only, which two identical controllers share. Newer agents
report a device_id (USB serial or port) for them. When a sensor's key moves to
the device-based form, its existing registry entry is given the new unique ID
so the entity keeps its entity ID, name, area and enabled state.
"""

from __future__ import annotations

import hashlib
import logging
import re
from typing import Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.util import slugify

from .api.models import FanInfo, TemperatureInfo, hwmon_temperature_keys
from .const import DOMAIN
from .entity import hwmon_controller_identifier

_LOGGER = logging.getLogger(__name__)


def hwmon_readings_by_key(system: Any) -> dict[str, TemperatureInfo]:
    """
    Map each hwmon temperature channel's entity key to its reading.

    A None system or temperature list gives an empty mapping.
    """
    keyed: dict[str, TemperatureInfo] = {}
    for key, reading in hwmon_temperature_keys(
        getattr(system, "temperatures", None)
    ).items():
        keyed.setdefault(slugify(key), reading)
    return keyed


def hwmon_temperature_channels(
    system: Any,
) -> list[tuple[str, TemperatureInfo, str]]:
    """
    Return (key, reading, display name) for each hwmon temperature channel.

    The key comes from the chip name and channel (hwmon_temperature_keys), so
    it stays the same whichever other chips are present and when a USB device
    reconnects with a new address. The display name uses the short chip name
    ('octo') unless several chips share it (several 'nvme' drives); it only
    sets the initial entity ID, so it may differ between setups without
    affecting identity.
    """
    keyed = hwmon_readings_by_key(system)

    def short_chip(reading: TemperatureInfo) -> str:
        """Return the chip name without its bus address ('k10temp')."""
        return (reading.source or "").split("-")[0]

    counts: dict[tuple[str, str | None], int] = {}
    for reading in keyed.values():
        ident = (short_chip(reading), reading.hwmon_feature)
        counts[ident] = counts.get(ident, 0) + 1

    channels: list[tuple[str, TemperatureInfo, str]] = []
    for key, reading in sorted(keyed.items(), key=lambda kv: kv[1].name or ""):
        chip = reading.source or ""
        if counts[(short_chip(reading), reading.hwmon_feature)] == 1:
            chip = short_chip(reading)
        elif reading.device_id:
            chip = f"{short_chip(reading)} {reading.device_id}"
        channels.append((key, reading, f"{chip} {reading.label}".strip()))
    return channels


@callback
def async_adopt_unique_id(
    hass: HomeAssistant, domain: str, target: str, candidates: list[str]
) -> str | None:
    """
    Give the first existing candidate entity the target unique ID, if free.

    Returns the candidate's former unique ID when an entity was moved.
    """
    registry = er.async_get(hass)
    if registry.async_get_entity_id(domain, DOMAIN, target):
        return None
    for candidate in candidates:
        if candidate == target:
            continue
        entity_id = registry.async_get_entity_id(domain, DOMAIN, candidate)
        if entity_id is None:
            continue
        registry.async_update_entity(entity_id, new_unique_id=target)
        _LOGGER.info("Moved %s from unique ID %s to %s", entity_id, candidate, target)
        return candidate
    return None


def _registry_match(
    hass: HomeAssistant, entry_id: str, pattern: re.Pattern[str]
) -> list[str]:
    """
    Return the one matching sensor unique ID of the entry, or none if unclear.

    The single enabled match, else the single match; several enabled (or
    several disabled and none enabled) matches could be different devices.
    """
    registry = er.async_get(hass)
    entries = [
        entity
        for entity in er.async_entries_for_config_entry(registry, entry_id)
        if entity.domain == "sensor" and pattern.match(entity.unique_id)
    ]
    enabled = [entity for entity in entries if entity.disabled_by is None]
    chosen = enabled or entries
    return [chosen[0].unique_id] if len(chosen) == 1 else []


def _controllers(chip: str, readings: list[Any], fans: list[Any]) -> set[str]:
    """Return the devices of one controller model seen in the current data."""
    devices = {
        reading.device_id or reading.source or ""
        for reading in readings
        if isinstance(reading, TemperatureInfo) and reading.hwmon_hid_chip == chip
    }
    driver = chip.removesuffix("-hid")
    devices.update(
        fan.device_id or fan.source or ""
        for fan in fans
        if isinstance(fan, FanInfo) and fan.chip_short == driver
    )
    return devices


def fan_model_is_shared(fan: Any, fans: list[Any]) -> bool:
    """Return True when another controller of this fan's model is present."""
    if not isinstance(fan, FanInfo) or not fan.chip_short:
        return False
    devices = {
        other.device_id or other.source
        for other in fans
        if isinstance(other, FanInfo) and other.chip_short == fan.chip_short
    }
    return len(devices) > 1


def temperature_legacy_unique_ids(
    hass: HomeAssistant,
    entry_id: str,
    reading: TemperatureInfo,
    readings: list[TemperatureInfo],
    fans: list[Any] | None = None,
) -> list[str]:
    """
    Return earlier unique IDs a USB HID temperature channel may be stored under.

    The channel's own address-based ID first. The driver-only ID and IDs at
    other addresses could belong to any controller of that model, so they are
    only offered when this is the only one present (by any of its temperature
    channels or fans), and an address-based ID only when it is the only one.
    """
    hid_chip = reading.hwmon_hid_chip
    feature = reading.hwmon_feature
    if not hid_chip or not feature:
        return []
    prefix = f"{entry_id}_temperature_"
    ids = [f"{prefix}{slugify(reading.hwmon_address_key or '')}"]
    if len(_controllers(hid_chip, readings, fans or [])) == 1:
        chip = slugify(hid_chip)
        ids.append(f"{prefix}{chip}_{feature}")
        ids.extend(
            _registry_match(
                hass,
                entry_id,
                re.compile(
                    re.escape(f"{prefix}{chip}_")
                    + r"\d+_[0-9a-f]+_"
                    + re.escape(feature)
                    + "$"
                ),
            )
        )
    return ids


def fan_legacy_unique_ids(
    entry_id: str, fan: Any, fans: list[Any], readings: list[Any] | None = None
) -> list[str]:
    """
    Return the name-based unique ID a device-keyed fan was stored under.

    Only when this is the only controller of its model, by its fans or its
    temperature readings: the name-based ID ('octo_fan8') does not say which
    of two identical controllers it was.
    """
    if not isinstance(fan, FanInfo) or not fan.device_key or not fan.chip_short:
        return []
    chip = fan.chip_short
    if len(_controllers(f"{chip}-hid", readings or [], fans)) > 1:
        return []
    channel = (fan.name or "").rsplit("_", 1)[-1]
    return [f"{entry_id}_fan_{f'{chip}_{channel}'.lower()}"]


# Known USB HID sensor chips (lm-sensors driver name) -> (model, kind) for the
# device name of a controller ("Octo (fan controller)").
_CONTROLLER_MODELS: dict[str, tuple[str, str]] = {
    "octo": ("Octo", "fan controller"),
    "quadro": ("Quadro", "fan controller"),
    "aquaero": ("Aquaero", "fan controller"),
    "d5next": ("D5 Next", "pump"),
    "highflownext": ("High Flow Next", "flow sensor"),
    "highflow": ("High Flow", "flow sensor"),
    "leakshield": ("Leakshield", "leak monitor"),
    "farbwerk": ("Farbwerk", "RGB controller"),
    "farbwerk360": ("Farbwerk 360", "RGB controller"),
    "corsaircpro": ("Commander Pro", "fan controller"),
    "corsairpsu": ("Corsair PSU", "power supply"),
}


def hwmon_controller_of(item: Any) -> tuple[str, str] | None:
    """
    Return the (driver, device_id) of the USB HID controller a reading is on.

    Only fans and temperatures the agent reports with a device_id (a USB
    serial or port, which does not change on reconnect) belong to one;
    others, and every reading from an older agent, return None.
    """
    if isinstance(item, FanInfo) and item.device_id and item.chip_short:
        return item.chip_short, item.device_id
    if isinstance(item, TemperatureInfo) and item.device_id and item.hwmon_hid_chip:
        return item.hwmon_hid_chip.removesuffix("-hid"), item.device_id
    return None


def hid_drivers_without_ids(items: Any) -> set[str]:
    """
    Return the USB HID drivers ('octo') with a fan or temperature lacking a device_id.

    That happens with agents from before device_id was reported (or after a
    downgrade): those controllers can't be told apart, so their device-keyed
    entities and devices must not be treated as gone.
    """
    drivers: set[str] = set()
    for item in items or []:
        if getattr(item, "device_id", None):
            continue
        if isinstance(item, FanInfo) and "-hid-" in (item.source or ""):
            drivers.add(item.chip_short or "")
        elif isinstance(item, TemperatureInfo) and item.hwmon_hid_chip:
            drivers.add(item.hwmon_hid_chip.removesuffix("-hid"))
    return drivers


def hwmon_controller_names(
    entry_id: str,
    fans: list[Any],
    readings: list[Any],
    known_identifiers: set[str] | frozenset[str] = frozenset(),
) -> dict[tuple[str, str], str]:
    """
    Name each USB HID controller in the current data.

    "Octo (fan controller)" while it is the only Octo known. Once several of
    one model are known (in the current data or as devices in the registry),
    each name gets a tag derived from its device identifier ("Octo 3f9a (fan
    controller)"). The tag never changes and never moves to other hardware,
    and the serial number cannot be read from it.
    """
    controllers = {
        controller
        for item in [*fans, *readings]
        if (controller := hwmon_controller_of(item)) is not None
    }
    names: dict[tuple[str, str], str] = {}
    for driver, device_id in controllers:
        model, kind = _CONTROLLER_MODELS.get(driver, (driver, "sensors"))
        identifier = hwmon_controller_identifier(entry_id, driver, device_id)
        prefix = f"{hwmon_controller_identifier(entry_id, driver, '')}_"
        peers = {i for i in known_identifiers if i.startswith(prefix)} | {
            hwmon_controller_identifier(entry_id, drv, dev)
            for drv, dev in controllers
            if drv == driver
        }
        tag = ""
        if len(peers) > 1:
            tag = " " + hashlib.sha256(identifier.encode()).hexdigest()[:4]
        names[(driver, device_id)] = f"{model}{tag} ({kind})"
    return names
