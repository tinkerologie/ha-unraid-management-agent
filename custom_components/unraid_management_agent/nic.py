"""
Network cards: devices and entity descriptions.

The agent's ``/network/cards`` endpoint reports each physical (PCI) network
card with its hwmon temperatures, its ports' link state and the diagnostics
(DDM) of the SFP/QSFP optics plugged into them. With the "Show network cards
as separate devices" option on, each card becomes a child device of the
Unraid server, named after its model and PCI slot (``ConnectX-6 Dx (41:00)``).

Entities:

- per card: one temperature sensor per ASIC, PHY, MAC or other hwmon sensor
  (transceiver cage sensors are left out: the optic's own module temperature
  is the same reading), and the firmware version (diagnostic);
- per port: link speed; and with an optic, its module temperature and
  voltage, worst-lane RX and TX power in dBm (every lane's power and laser
  bias as attributes), a problem binary sensor that is on while any alarm or
  warning flag is raised, and the optic's vendor and part number (diagnostic).

Unique IDs are keyed by PCI slot and port ID (the PCI function address), so
renaming an interface does not change them. Like storage devices, card
entities are not part of stale-entity cleanup: a card or optic that
disappears makes its entities unavailable, and the device of a card the agent
no longer reports can be deleted from the UI. Turning the option off removes
every network card device and entity.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Final

from homeassistant.components.binary_sensor import BinarySensorEntityDescription
from homeassistant.components.binary_sensor.const import BinarySensorDeviceClass
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    EntityCategory,
    UnitOfDataRate,
    UnitOfElectricPotential,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import ChildDeviceInfo, DeviceInfo
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.util import slugify

from .api.models import NIC_STATE_OK, NICCard, NICList, NICModule, NICPort
from .cleanup import async_prune_seen_names
from .const import DOMAIN
from .entity import UnraidBaseEntity

if TYPE_CHECKING:
    from .coordinator import UnraidConfigEntry, UnraidDataUpdateCoordinator

NIC_COLLECTOR: Final = "nic"
# hwmon sensor kinds shown as card temperature sensors (module cages are not).
_TEMPERATURE_SENSORS: Final = ("asic", "phy", "mac", "other")
_RX = "rx"
_TX = "tx"


def network_cards(coordinator: UnraidDataUpdateCoordinator) -> NICList | None:
    """
    Return the collected network cards, or None when they are not usable.

    None covers the option being off (nothing is fetched), an agent without
    the endpoint (404), a failed fetch, a list that is still pending, and a
    disabled collector (whose last snapshot the agent would keep serving).
    """
    data = coordinator.data
    cards = data.network_cards if data else None
    if (
        cards is None
        or cards.state != NIC_STATE_OK
        or not coordinator.is_collector_enabled(NIC_COLLECTOR)
    ):
        return None
    return cards


def device_identifier(entry_id: str, card_id: str) -> str:
    """Return the device registry identifier of a network card."""
    return f"{entry_id}_nic_{card_id}"


def card_name(card: NICCard) -> str:
    """Return the device name of a card: model and PCI slot (bus:device)."""
    slot = card.id.removeprefix("0000:")
    return f"{card.model or 'Network card'} ({slot})"


def build_nic_device_info(
    coordinator: UnraidDataUpdateCoordinator, card_id: str, name: str
) -> DeviceInfo | ChildDeviceInfo:
    """Build device info for a network card, a child of the server."""
    entry_id = coordinator.config_entry.entry_id
    # The server device is registered during setup, before the platforms load.
    server = dr.async_get(coordinator.hass).async_get_device_by_identifier(
        (DOMAIN, entry_id), entry_id
    )
    if server is None:
        # Keep the entity on the server device if it is somehow missing.
        return DeviceInfo(identifiers={(DOMAIN, entry_id)})
    return ChildDeviceInfo(
        identifiers={(DOMAIN, device_identifier(entry_id, card_id))},
        name=name,
        parent_device_id=server.id,
    )


def current_card_ids(cards: NICList | None) -> set[str]:
    """Return the IDs of the cards currently reported."""
    return {card.id for card in cards.cards} if cards else set()


@callback
def async_remove_nic_devices(hass: HomeAssistant, entry: UnraidConfigEntry) -> None:
    """Remove every network card device and entity (the option is off)."""
    prefix = f"{entry.entry_id}_nic_"
    entity_registry = er.async_get(hass)
    for entity_entry in er.async_entries_for_config_entry(
        entity_registry, entry.entry_id
    ):
        if entity_entry.unique_id.startswith(prefix):
            entity_registry.async_remove(entity_entry.entity_id)
    device_registry = dr.async_get(hass)
    for device in dr.async_child_entries_for_config_entry(
        device_registry, entry.entry_id
    ):
        if any(
            domain == DOMAIN and identifier.startswith(prefix)
            for domain, identifier in device.identifiers
        ):
            device_registry.async_remove_device(device.id)


# =============================================================================
# Context: the card (and port or temperature sensor) an entity shows
# =============================================================================


@dataclass(frozen=True)
class NICContext:
    """The data an entity reads: its card, and its port or sensor."""

    card: NICCard
    port: NICPort | None = None
    temperature: Any = None

    @property
    def module(self) -> NICModule | None:
        """Return the port's module, if any."""
        return self.port.module if self.port else None


def resolve(
    cards: NICList, card_id: str, item: tuple[str, str] | None
) -> NICContext | None:
    """Find an entity's card, and port or temperature sensor, in the list."""
    card = next((c for c in cards.cards if c.id == card_id), None)
    if card is None:
        return None
    if item is None:
        return NICContext(card)
    kind, item_id = item
    if kind == "port":
        port = next((p for p in card.ports if p.id == item_id), None)
        return NICContext(card, port=port) if port else None
    sensor = next((t for t in card.temperatures if temperature_id(t) == item_id), None)
    return NICContext(card, temperature=sensor) if sensor else None


def temperature_id(sensor: Any) -> str:
    """
    Return a temperature sensor's stable ID within its card.

    The ASIC is one sensor per card; every other sensor belongs to a PCI
    function, which is part of its ID.
    """
    if sensor.sensor == "asic":
        return sensor.label
    return f"{sensor.pci_address}/{sensor.label}"


# =============================================================================
# Value and attribute helpers
# =============================================================================


def _lane_values(module: NICModule | None, field: str) -> list[float]:
    """Return a lane field's values, skipping lanes that do not report it."""
    if module is None:
        return []
    return [v for lane in module.lanes if (v := getattr(lane, field)) is not None]


def _valid_diagnostics(ctx: NICContext) -> NICModule | None:
    """
    Return the module when its readings are valid, else None.

    Readings of a module whose monitors are not ready, or whose EEPROM could
    not be decoded, are not trustworthy, so numeric sensors show unknown.
    """
    module = ctx.module
    if module is None or module.data_not_ready or module.error:
        return None
    return module


def _worst_power(direction: str) -> Callable[[NICContext], float | None]:
    """Return the lowest (worst) lane power in dBm."""

    def value(ctx: NICContext) -> float | None:
        values = _lane_values(_valid_diagnostics(ctx), f"{direction}_power_dbm")
        return min(values) if values else None

    return value


def _module_reading(field: str) -> Callable[[NICContext], float | None]:
    """Return a module-wide reading (temperature, voltage) when valid."""

    def value(ctx: NICContext) -> float | None:
        module = _valid_diagnostics(ctx)
        return getattr(module, field) if module else None

    return value


def _has_power(direction: str) -> Callable[[NICContext], bool]:
    def exists(ctx: NICContext) -> bool:
        return bool(_lane_values(ctx.module, f"{direction}_power_dbm"))

    return exists


def _thresholds(module: NICModule, name: str) -> dict[str, Any] | None:
    thresholds = module.thresholds
    threshold = getattr(thresholds, name, None) if thresholds else None
    return threshold.model_dump() if threshold else None


def _rx_attrs(ctx: NICContext) -> dict[str, Any]:
    module = ctx.module
    return {
        "lanes": [
            {"lane": lane.lane, "mw": lane.rx_power_mw, "dbm": lane.rx_power_dbm}
            for lane in module.lanes
        ],
        "measurement": module.rx_power_type,
        "thresholds": _thresholds(module, "rx_power_dbm"),
    }


def _tx_attrs(ctx: NICContext) -> dict[str, Any]:
    module = ctx.module
    return {
        "lanes": [
            {
                "lane": lane.lane,
                "mw": lane.tx_power_mw,
                "dbm": lane.tx_power_dbm,
                "bias_ma": lane.tx_bias_ma,
            }
            for lane in module.lanes
        ],
        "thresholds": _thresholds(module, "tx_power_dbm"),
        "bias_thresholds": _thresholds(module, "tx_bias_ma"),
    }


def _module_problem(ctx: NICContext) -> bool | None:
    """
    Return True while an alarm or warning flag is raised.

    Unknown (None) while the module's monitors are not ready or could not be
    decoded: empty flags then do not mean the optic is healthy.
    """
    module = _valid_diagnostics(ctx)
    if module is None:
        return None
    return bool(module.alarms or module.warnings)


def _module_problem_attrs(ctx: NICContext) -> dict[str, Any]:
    module = ctx.module
    return {
        "alarms": list(module.alarms),
        "warnings": list(module.warnings),
        "data_not_ready": bool(module.data_not_ready),
        "error": module.error,
    }


def _module_identity_attrs(ctx: NICContext) -> dict[str, Any]:
    module = ctx.module
    return {
        "identifier": module.identifier,
        "standard": module.standard,
        "connector": module.connector,
        "compliance": module.compliance,
        "vendor_oui": module.vendor_oui,
        "vendor_rev": module.vendor_rev,
        "wavelength_nm": module.wavelength_nm,
    }


def _port_attrs(ctx: NICContext) -> dict[str, Any]:
    port = ctx.port
    return {
        "interface": port.interface,
        "pci_address": port.pci_address,
        "operstate": port.operstate,
        "carrier": port.carrier,
        "duplex": port.duplex,
        "mtu": port.mtu,
        "master": port.master,
    }


def _card_attrs(ctx: NICContext) -> dict[str, Any]:
    card = ctx.card
    return {
        "vendor": card.vendor,
        "device_name": card.device_name,
        "driver": card.driver,
        "pci_slot": card.id,
        "pci_id": f"{card.vendor_id}:{card.device_id}"
        if card.vendor_id and card.device_id
        else None,
    }


def _temperature_attrs(ctx: NICContext) -> dict[str, Any]:
    sensor = ctx.temperature
    return {
        "label": sensor.label,
        "pci_address": sensor.pci_address,
        "interface": sensor.interface,
        "highest": sensor.highest_celsius,
        "max": sensor.max_celsius,
        "critical": sensor.crit_celsius,
    }


def _has_module(ctx: NICContext) -> bool:
    return ctx.module is not None


def _has_ddm(ctx: NICContext) -> bool:
    return ctx.module is not None and ctx.module.ddm_supported


# =============================================================================
# Entity descriptions
# =============================================================================


@dataclass(frozen=True, kw_only=True)
class UnraidNICSensorEntityDescription(SensorEntityDescription):
    """Description of a network card sensor."""

    value_fn: Callable[[NICContext], StateType]
    attrs_fn: Callable[[NICContext], dict[str, Any]] | None = None
    # False makes the entity unavailable (e.g. the optic was unplugged).
    exists_fn: Callable[[NICContext], bool] | None = None


@dataclass(frozen=True, kw_only=True)
class UnraidNICBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Description of a network card binary sensor."""

    is_on_fn: Callable[[NICContext], bool | None]
    attrs_fn: Callable[[NICContext], dict[str, Any]] | None = None
    exists_fn: Callable[[NICContext], bool] | None = None


def _temperature_description(
    translation_key: str,
) -> UnraidNICSensorEntityDescription:
    return UnraidNICSensorEntityDescription(
        key="temperature",
        translation_key=translation_key,
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda ctx: ctx.temperature.celsius,
        attrs_fn=_temperature_attrs,
    )


# Translation keys per sensor kind: (single-port card, multi-port card).
_TEMPERATURE_KEYS: dict[str, tuple[str, str]] = {
    "asic": ("nic_asic_temperature", "nic_asic_temperature"),
    "phy": ("nic_phy_temperature", "nic_port_phy_temperature"),
    "mac": ("nic_mac_temperature", "nic_port_mac_temperature"),
    "other": ("nic_temperature", "nic_port_temperature"),
}
_TEMPERATURES: dict[str, UnraidNICSensorEntityDescription] = {
    key: _temperature_description(key)
    for keys in _TEMPERATURE_KEYS.values()
    for key in keys
}

_FIRMWARE = UnraidNICSensorEntityDescription(
    key="firmware",
    translation_key="nic_firmware",
    entity_category=EntityCategory.DIAGNOSTIC,
    value_fn=lambda ctx: ctx.card.firmware_version,
    attrs_fn=_card_attrs,
)
_LINK_SPEED = UnraidNICSensorEntityDescription(
    key="link_speed",
    translation_key="nic_link_speed",
    device_class=SensorDeviceClass.DATA_RATE,
    native_unit_of_measurement=UnitOfDataRate.MEGABITS_PER_SECOND,
    state_class=SensorStateClass.MEASUREMENT,
    value_fn=lambda ctx: ctx.port.speed_mbps if ctx.port else None,
    attrs_fn=_port_attrs,
)
_MODULE_TEMPERATURE = UnraidNICSensorEntityDescription(
    key="module_temperature",
    translation_key="nic_module_temperature",
    device_class=SensorDeviceClass.TEMPERATURE,
    native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    state_class=SensorStateClass.MEASUREMENT,
    value_fn=_module_reading("temperature_celsius"),
    attrs_fn=lambda ctx: (
        {"thresholds": _thresholds(ctx.module, "temperature_celsius")}
        if ctx.module
        else {}
    ),
    exists_fn=_has_ddm,
)
_MODULE_VOLTAGE = UnraidNICSensorEntityDescription(
    key="module_voltage",
    translation_key="nic_module_voltage",
    device_class=SensorDeviceClass.VOLTAGE,
    native_unit_of_measurement=UnitOfElectricPotential.VOLT,
    state_class=SensorStateClass.MEASUREMENT,
    entity_category=EntityCategory.DIAGNOSTIC,
    value_fn=_module_reading("voltage_volts"),
    attrs_fn=lambda ctx: (
        {"thresholds": _thresholds(ctx.module, "voltage_volts")} if ctx.module else {}
    ),
    exists_fn=_has_ddm,
)
_RX_POWER = UnraidNICSensorEntityDescription(
    key="rx_power",
    translation_key="nic_rx_power",
    device_class=SensorDeviceClass.SIGNAL_STRENGTH,
    native_unit_of_measurement="dBm",
    state_class=SensorStateClass.MEASUREMENT,
    suggested_display_precision=2,
    value_fn=_worst_power(_RX),
    attrs_fn=_rx_attrs,
    exists_fn=_has_power(_RX),
)
_TX_POWER = UnraidNICSensorEntityDescription(
    key="tx_power",
    translation_key="nic_tx_power",
    device_class=SensorDeviceClass.SIGNAL_STRENGTH,
    native_unit_of_measurement="dBm",
    state_class=SensorStateClass.MEASUREMENT,
    suggested_display_precision=2,
    value_fn=_worst_power(_TX),
    attrs_fn=_tx_attrs,
    exists_fn=_has_power(_TX),
)
_MODULE_VENDOR = UnraidNICSensorEntityDescription(
    key="module_vendor",
    translation_key="nic_module_vendor",
    entity_category=EntityCategory.DIAGNOSTIC,
    value_fn=lambda ctx: ctx.module.vendor_name if ctx.module else None,
    attrs_fn=_module_identity_attrs,
    exists_fn=_has_module,
)
_MODULE_PART_NUMBER = UnraidNICSensorEntityDescription(
    key="module_part_number",
    translation_key="nic_module_part_number",
    entity_category=EntityCategory.DIAGNOSTIC,
    value_fn=lambda ctx: ctx.module.vendor_pn if ctx.module else None,
    attrs_fn=_module_identity_attrs,
    exists_fn=_has_module,
)
_MODULE_PROBLEM = UnraidNICBinarySensorEntityDescription(
    key="module_problem",
    translation_key="nic_module_problem",
    device_class=BinarySensorDeviceClass.PROBLEM,
    is_on_fn=_module_problem,
    attrs_fn=_module_problem_attrs,
    exists_fn=_has_ddm,
)


# =============================================================================
# Entity specs: which entities a card list produces
# =============================================================================


@dataclass(frozen=True)
class NICEntitySpec:
    """One network card entity to create: what it shows and where it lives."""

    description: (
        UnraidNICSensorEntityDescription | UnraidNICBinarySensorEntityDescription
    )
    card_id: str
    device_name: str
    item: tuple[str, str] | None = None
    # Translation placeholders of the entity name.
    placeholders: dict[str, str] | None = None

    @property
    def key(self) -> str:
        """Return the entity key (the unique ID without the entry ID)."""
        parts = ["nic", slugify(self.card_id)]
        if self.item is not None:
            kind, item_id = self.item
            if kind == "port":
                parts.append(f"port_{slugify(item_id)}")
            elif "/" in item_id:
                pci_address, label = item_id.split("/", 1)
                parts.append(f"port_{slugify(pci_address)}_{slugify(label)}")
            else:
                parts.append(slugify(item_id))
        parts.append(self.description.key)
        return "_".join(parts)


def _port_label(port: NICPort) -> str:
    return port.interface or port.id


def nic_sensor_specs(cards: NICList) -> list[NICEntitySpec]:
    """Return the sensor entities for a card list."""
    specs: list[NICEntitySpec] = []
    for card in cards.cards:
        name = card_name(card)
        multi_port = len(card.ports) > 1
        ports_by_function: dict[str, NICPort] = {}
        for port in card.ports:
            ports_by_function.setdefault(port.pci_address, port)

        for sensor in card.temperatures:
            if sensor.sensor not in _TEMPERATURE_SENSORS:
                continue
            single_key, multi_key = _TEMPERATURE_KEYS[sensor.sensor]
            per_port = sensor.sensor != "asic" and multi_port
            port = ports_by_function.get(sensor.pci_address)
            placeholders = {"label": sensor.label}
            if per_port:
                placeholders["port"] = (
                    sensor.interface or (_port_label(port) if port else "")
                ) or sensor.pci_address
            specs.append(
                NICEntitySpec(
                    _TEMPERATURES[multi_key if per_port else single_key],
                    card.id,
                    name,
                    ("temperature", temperature_id(sensor)),
                    placeholders,
                )
            )

        specs.append(NICEntitySpec(_FIRMWARE, card.id, name))

        for port in card.ports:

            def port_spec(
                description: UnraidNICSensorEntityDescription,
                *,
                port: NICPort = port,
                card_id: str = card.id,
                device_name: str = name,
            ) -> NICEntitySpec:
                return NICEntitySpec(
                    description,
                    card_id,
                    device_name,
                    ("port", port.id),
                    {"port": _port_label(port)},
                )

            specs.append(port_spec(_LINK_SPEED))
            module = port.module
            if module is None:
                continue
            ctx = NICContext(card, port=port)
            specs.append(port_spec(_MODULE_VENDOR))
            specs.append(port_spec(_MODULE_PART_NUMBER))
            if module.ddm_supported:
                specs.append(port_spec(_MODULE_TEMPERATURE))
                specs.append(port_spec(_MODULE_VOLTAGE))
            if _has_power(_RX)(ctx):
                specs.append(port_spec(_RX_POWER))
            if _has_power(_TX)(ctx):
                specs.append(port_spec(_TX_POWER))
    return specs


def nic_binary_sensor_specs(cards: NICList) -> list[NICEntitySpec]:
    """Return the binary sensor entities for a card list."""
    return [
        NICEntitySpec(
            _MODULE_PROBLEM,
            card.id,
            card_name(card),
            ("port", port.id),
            {"port": _port_label(port)},
        )
        for card in cards.cards
        for port in card.ports
        if port.module is not None and port.module.ddm_supported
    ]


# =============================================================================
# Entity base and setup
# =============================================================================


class UnraidNICEntity(UnraidBaseEntity):
    """Base for entities of a network card device."""

    def __init__(
        self, coordinator: UnraidDataUpdateCoordinator, spec: NICEntitySpec
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator, spec.key)
        self._spec = spec
        self._attr_device_info = build_nic_device_info(
            coordinator, spec.card_id, spec.device_name
        )
        if spec.placeholders:
            self._attr_translation_placeholders = spec.placeholders

    def _nic_context(self) -> NICContext | None:
        """Return this entity's data, or None when it is not reported."""
        cards = network_cards(self.coordinator)
        if cards is None:
            return None
        ctx = resolve(cards, self._spec.card_id, self._spec.item)
        exists_fn = self._spec.description.exists_fn
        if ctx is None or (exists_fn is not None and not exists_fn(ctx)):
            return None
        return ctx

    @property
    def available(self) -> bool:
        """Return True while the card (and port, sensor or optic) is reported."""
        return super().available and self._nic_context() is not None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return details about the card, port, sensor or optic."""
        attrs_fn = self._spec.description.attrs_fn
        ctx = self._nic_context()
        if attrs_fn is None or ctx is None:
            return None
        return attrs_fn(ctx)


def async_setup_nic_entities(
    entry: UnraidConfigEntry,
    platform_domain: str,
    specs_fn: Callable[[NICList], list[NICEntitySpec]],
    entity_factory: Callable[[UnraidDataUpdateCoordinator, NICEntitySpec], Entity],
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """
    Add network card entities now and whenever new ones appear.

    Cards are reported some time after the agent starts and optics can be
    plugged in later, so entities are created from a coordinator listener.
    Nothing is added while the option is off (no card list is fetched).
    """
    coordinator = entry.runtime_data.coordinator
    hass = coordinator.hass
    seen: set[str] = set()

    @callback
    def _add_entities() -> None:
        cards = network_cards(coordinator)
        if cards is None:
            return
        # Allow re-creation of entities removed from the registry (see #83)
        async_prune_seen_names(
            hass, platform_domain, seen, lambda key: f"{entry.entry_id}_{key}"
        )
        new_entities: list[Entity] = []
        for spec in specs_fn(cards):
            if spec.key not in seen:
                seen.add(spec.key)
                new_entities.append(entity_factory(coordinator, spec))
        if new_entities:
            async_add_entities(new_entities)

    _add_entities()
    entry.async_on_unload(coordinator.async_add_listener(_add_entities))
