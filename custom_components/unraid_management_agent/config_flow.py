"""Config flow for Unraid Management Agent integration."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigEntryState,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlowWithReload,
)
from homeassistant.const import CONF_API_TOKEN, CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from .api import UnraidAuthenticationError, UnraidClient, UnraidConnectionError
from .const import (
    CONF_CPU_TEMPERATURE_SOURCE,
    CONF_ENABLE_CONTAINER_DEVICES,
    CONF_ENABLE_CONTAINER_UPDATES,
    CONF_ENABLE_FAN_CONTROL,
    CONF_ENABLE_GPU_DEVICES,
    CONF_ENABLE_HWMON_DEVICES,
    CONF_ENABLE_NIC_DEVICES,
    CONF_ENABLE_VM_DEVICES,
    CONF_ENABLE_WEBSOCKET,
    CONF_ENABLE_ZFS_POOL_DEVICES,
    CONF_READ_ONLY,
    CPU_TEMPERATURE_SOURCE_AUTO,
    DEFAULT_CPU_TEMPERATURE_SOURCE,
    DEFAULT_ENABLE_CONTAINER_DEVICES,
    DEFAULT_ENABLE_CONTAINER_UPDATES,
    DEFAULT_ENABLE_FAN_CONTROL,
    DEFAULT_ENABLE_GPU_DEVICES,
    DEFAULT_ENABLE_HWMON_DEVICES,
    DEFAULT_ENABLE_NIC_DEVICES,
    DEFAULT_ENABLE_VM_DEVICES,
    DEFAULT_ENABLE_WEBSOCKET,
    DEFAULT_ENABLE_ZFS_POOL_DEVICES,
    DEFAULT_PORT,
    DEFAULT_READ_ONLY,
    DOMAIN,
    ERROR_CANNOT_CONNECT,
    ERROR_INVALID_AUTH,
    ERROR_TIMEOUT,
    ERROR_UNKNOWN,
)
from .hwmon import hwmon_controller_of, hwmon_temperature_channels

if TYPE_CHECKING:
    from .coordinator import UnraidData

_LOGGER = logging.getLogger(__name__)

# The agent's API token (Settings > Unraid Management Agent > Authentication)
TOKEN_SELECTOR = TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD))


class InvalidAuthError(Exception):
    """The agent rejected the API token."""


STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=65535)
        ),
        vol.Optional(CONF_API_TOKEN): TOKEN_SELECTOR,
        vol.Optional(
            CONF_ENABLE_WEBSOCKET, default=DEFAULT_ENABLE_WEBSOCKET
        ): cv.boolean,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """
    Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    # Use Home Assistant's shared client session (inject-websession)
    session = async_get_clientsession(hass)
    async with UnraidClient(
        host=data[CONF_HOST],
        port=data[CONF_PORT],
        session=session,
        api_token=data.get(CONF_API_TOKEN),
    ) as client:
        try:
            # Test connection by getting system info - returns typed Pydantic model
            system_info = await client.get_system_info()
            hostname = system_info.hostname or "unknown"

            return {
                "title": f"Unraid ({hostname})",
                "hostname": hostname,
            }
        except UnraidAuthenticationError as err:
            _LOGGER.warning("Unraid Management Agent rejected the API token")
            raise InvalidAuthError from err
        except TimeoutError as err:
            _LOGGER.error("Timeout connecting to Unraid server: %s", err)
            raise TimeoutError(ERROR_TIMEOUT) from err
        except UnraidConnectionError as err:
            _LOGGER.error("Cannot connect to Unraid server: %s", err)
            raise ConnectionError(ERROR_CANNOT_CONNECT) from err
        except Exception as err:
            _LOGGER.exception("Unexpected exception: %s", err)
            raise Exception(ERROR_UNKNOWN) from err


class UnraidConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Unraid Management Agent."""

    VERSION = 1
    MINOR_VERSION = 1

    def __init__(self) -> None:
        """Initialize config flow."""
        self._discovered_host: str = ""
        self._discovered_port: int = DEFAULT_PORT

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except InvalidAuthError:
                errors["base"] = ERROR_INVALID_AUTH
            except TimeoutError:
                errors["base"] = ERROR_TIMEOUT
            except ConnectionError:
                errors["base"] = ERROR_CANNOT_CONNECT
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = ERROR_UNKNOWN
            else:
                # Check if already configured
                await self.async_set_unique_id(
                    f"{user_input[CONF_HOST]}:{user_input[CONF_PORT]}"
                )
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=info["title"],
                    data=user_input,
                )

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_HOST, default=self._discovered_host or vol.UNDEFINED
                ): cv.string,
                vol.Required(
                    CONF_PORT,
                    default=self._discovered_port
                    if self._discovered_host
                    else DEFAULT_PORT,
                ): vol.All(vol.Coerce(int), vol.Range(min=1, max=65535)),
                vol.Optional(CONF_API_TOKEN): TOKEN_SELECTOR,
                vol.Optional(
                    CONF_ENABLE_WEBSOCKET, default=DEFAULT_ENABLE_WEBSOCKET
                ): cv.boolean,
            }
        )
        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_zeroconf(
        self, discovery_info: ZeroconfServiceInfo
    ) -> ConfigFlowResult:
        """Handle zeroconf discovery."""
        host = discovery_info.host
        port = discovery_info.port or DEFAULT_PORT

        await self.async_set_unique_id(f"{host}:{port}")
        self._abort_if_unique_id_configured(updates={CONF_HOST: host, CONF_PORT: port})

        self._discovered_host = host
        self._discovered_port = port
        self.context["title_placeholders"] = {"host": host}
        return await self.async_step_user()

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle reconfiguration of the integration."""
        reconfigure_entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except InvalidAuthError:
                errors["base"] = ERROR_INVALID_AUTH
            except TimeoutError:
                errors["base"] = ERROR_TIMEOUT
            except ConnectionError:
                errors["base"] = ERROR_CANNOT_CONNECT
            except Exception:
                _LOGGER.exception("Unexpected exception during reconfigure")
                errors["base"] = ERROR_UNKNOWN
            else:
                # Update the unique ID if host/port changed
                await self.async_set_unique_id(
                    f"{user_input[CONF_HOST]}:{user_input[CONF_PORT]}"
                )
                self._abort_if_unique_id_mismatch(reason="unique_id_mismatch")

                return self.async_update_reload_and_abort(
                    reconfigure_entry,
                    title=info["title"],
                    data=user_input,
                )

        # Pre-fill with current values
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_HOST, default=reconfigure_entry.data.get(CONF_HOST, "")
                    ): cv.string,
                    vol.Required(
                        CONF_PORT,
                        default=reconfigure_entry.data.get(CONF_PORT, DEFAULT_PORT),
                    ): vol.All(vol.Coerce(int), vol.Range(min=1, max=65535)),
                    vol.Optional(
                        CONF_API_TOKEN,
                        description={
                            "suggested_value": reconfigure_entry.data.get(
                                CONF_API_TOKEN
                            )
                        },
                    ): TOKEN_SELECTOR,
                    vol.Optional(
                        CONF_ENABLE_WEBSOCKET,
                        default=reconfigure_entry.data.get(
                            CONF_ENABLE_WEBSOCKET, DEFAULT_ENABLE_WEBSOCKET
                        ),
                    ): cv.boolean,
                }
            ),
            errors=errors,
        )

    async def async_step_reauth(
        self,
        entry_data: Mapping[str, Any],
    ) -> ConfigFlowResult:
        """Start reauthentication after the agent rejected the API token."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for the agent's current API token."""
        reauth_entry = self._get_reauth_entry()
        errors: dict[str, str] = {}

        if user_input is not None:
            data = {**reauth_entry.data, CONF_API_TOKEN: user_input[CONF_API_TOKEN]}
            try:
                await validate_input(self.hass, data)
            except InvalidAuthError:
                errors["base"] = ERROR_INVALID_AUTH
            except TimeoutError:
                errors["base"] = ERROR_TIMEOUT
            except ConnectionError:
                errors["base"] = ERROR_CANNOT_CONNECT
            except Exception:
                _LOGGER.exception("Unexpected exception during reauth")
                errors["base"] = ERROR_UNKNOWN
            else:
                return self.async_update_reload_and_abort(
                    reauth_entry,
                    data_updates={CONF_API_TOKEN: user_input[CONF_API_TOKEN]},
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_API_TOKEN): TOKEN_SELECTOR}),
            description_placeholders={"host": reauth_entry.data[CONF_HOST]},
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,  # noqa: ARG004
    ) -> UnraidOptionsFlowHandler:
        """Get the options flow for this handler."""
        return UnraidOptionsFlowHandler()


# Options in the order the form shows them, with their defaults. The read-only
# and WebSocket options apply to every server; the others are shown only when
# the server has what they are for (see _visible_option_keys).
_BOOLEAN_OPTIONS: tuple[tuple[str, bool], ...] = (
    (CONF_ENABLE_CONTAINER_UPDATES, DEFAULT_ENABLE_CONTAINER_UPDATES),
    (CONF_ENABLE_FAN_CONTROL, DEFAULT_ENABLE_FAN_CONTROL),
    (CONF_READ_ONLY, DEFAULT_READ_ONLY),
    (CONF_ENABLE_WEBSOCKET, DEFAULT_ENABLE_WEBSOCKET),
    (CONF_ENABLE_CONTAINER_DEVICES, DEFAULT_ENABLE_CONTAINER_DEVICES),
    (CONF_ENABLE_GPU_DEVICES, DEFAULT_ENABLE_GPU_DEVICES),
    (CONF_ENABLE_NIC_DEVICES, DEFAULT_ENABLE_NIC_DEVICES),
    (CONF_ENABLE_HWMON_DEVICES, DEFAULT_ENABLE_HWMON_DEVICES),
    (CONF_ENABLE_VM_DEVICES, DEFAULT_ENABLE_VM_DEVICES),
    (CONF_ENABLE_ZFS_POOL_DEVICES, DEFAULT_ENABLE_ZFS_POOL_DEVICES),
)


def _entry_data(entry: ConfigEntry) -> UnraidData | None:
    """
    Return the entry's latest coordinator data, or None if there is none.

    Only a loaded entry has runtime data; before the first successful refresh
    (or after unload) the form falls back to showing every option.
    """
    if entry.state is not ConfigEntryState.LOADED:
        return None
    runtime_data = getattr(entry, "runtime_data", None)
    coordinator = getattr(runtime_data, "coordinator", None)
    return getattr(coordinator, "data", None)


def _collector_enabled(data: UnraidData, name: str) -> bool:
    """Return True only when the agent lists the collector as enabled."""
    collectors = data.collectors
    collector = collectors.get_collector_by_name(name) if collectors else None
    return collector is not None and collector.enabled is True


def _service_present(
    items: list[Any] | None, settings: Any, collector: str, data: UnraidData
) -> bool:
    """
    Return True when the server shows a Docker or VM service.

    Existing containers/VMs count first. Otherwise a known service setting
    decides; only without one does an explicitly enabled collector count.
    Unknown is not enabled here, unlike the coordinator's permissive helpers.
    """
    if items:
        return True
    if settings is not None and getattr(settings, "enabled", None) is not None:
        return settings.enabled is True
    return _collector_enabled(data, collector)


def _has_hwmon_controllers(data: UnraidData) -> bool:
    """Return True when a fan or temperature is on a USB sensor controller."""
    system = data.system
    if system is None:
        return False
    items = [*(system.fans or []), *(system.temperatures or [])]
    return any(hwmon_controller_of(item) is not None for item in items)


def _has_controllable_fans(data: UnraidData) -> bool:
    """Return True when a fan can be controlled (the rule number.py uses)."""
    fans = data.fan_control.fans if data.fan_control else None
    return any(fan.id and fan.controllable for fan in fans or [])


def _has_fans(data: UnraidData) -> bool:
    """
    Return True when the fan control option has anything to act on.

    The option gates the fan RPM sensors (one per reported fan) as well as the
    fan control entities, so any reported fan counts, not only controllable
    ones.
    """
    system = data.system
    return bool(system is not None and system.fans) or _has_controllable_fans(data)


def _visible_option_keys(data: UnraidData) -> set[str]:
    """Return the boolean options that apply to this server's data."""
    visible = {CONF_READ_ONLY, CONF_ENABLE_WEBSOCKET}
    if _service_present(data.containers, data.docker_settings, "docker", data):
        visible |= {CONF_ENABLE_CONTAINER_DEVICES, CONF_ENABLE_CONTAINER_UPDATES}
    if _service_present(data.vms, data.vm_settings, "vm", data):
        visible.add(CONF_ENABLE_VM_DEVICES)
    if data.gpu:
        visible.add(CONF_ENABLE_GPU_DEVICES)
    # Network cards are only fetched while the option is on, so the agent's
    # nic collector is the signal that does not depend on the option itself
    if _collector_enabled(data, "nic") or (
        data.network_cards is not None and data.network_cards.cards
    ):
        visible.add(CONF_ENABLE_NIC_DEVICES)
    if _has_hwmon_controllers(data):
        visible.add(CONF_ENABLE_HWMON_DEVICES)
    if data.zfs_pools:
        visible.add(CONF_ENABLE_ZFS_POOL_DEVICES)
    if _has_fans(data):
        visible.add(CONF_ENABLE_FAN_CONTROL)
    return visible


# Options shown together: a group stays visible while any of its keys is on
_OPTION_GROUPS: tuple[frozenset[str], ...] = (
    frozenset({CONF_ENABLE_CONTAINER_DEVICES, CONF_ENABLE_CONTAINER_UPDATES}),
)


def _cpu_temperature_choices(
    data: UnraidData | None, current: str
) -> list[SelectOptionDict]:
    """
    Return the CPU temperature source choices: automatic, then each channel.

    A channel is offered by its stable key and labelled with its name and
    current reading. A stored choice the agent no longer reports is kept, so
    the form never silently changes the user's selection.
    """
    choices = [SelectOptionDict(value=CPU_TEMPERATURE_SOURCE_AUTO, label="Automatic")]
    system = data.system if data else None
    for key, reading, name in hwmon_temperature_channels(system):
        value = reading.value_celsius
        label = name if value is None else f"{name} ({value:.1f} °C)"
        choices.append(SelectOptionDict(value=key, label=label))
    if current not in {choice["value"] for choice in choices}:
        choices.append(
            SelectOptionDict(value=current, label=f"{current} (not currently reported)")
        )
    return choices


class UnraidOptionsFlowHandler(OptionsFlowWithReload):
    """Handle options flow for Unraid Management Agent."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """
        Manage the options.

        Only the options that apply to the server are shown; hidden options
        keep their stored values when the form is saved.
        """
        options = self.config_entry.options
        if user_input is not None:
            return self.async_create_entry(title="", data={**options, **user_input})

        data = _entry_data(self.config_entry)
        visible = (
            {key for key, _ in _BOOLEAN_OPTIONS}
            if data is None
            else _visible_option_keys(data)
        )
        # An option that is on stays visible so it can be turned off
        visible |= {key for key, _ in _BOOLEAN_OPTIONS if options.get(key) is True}
        for group in _OPTION_GROUPS:
            if visible & group:
                visible |= group

        schema: dict[Any, Any] = {
            vol.Optional(key, default=options.get(key, default)): cv.boolean
            for key, default in _BOOLEAN_OPTIONS
            if key in visible
        }

        cpu_source = options.get(
            CONF_CPU_TEMPERATURE_SOURCE, DEFAULT_CPU_TEMPERATURE_SOURCE
        )
        cpu_choices = _cpu_temperature_choices(data, cpu_source)
        if data is None or len(cpu_choices) > 1:
            schema[vol.Optional(CONF_CPU_TEMPERATURE_SOURCE, default=cpu_source)] = (
                SelectSelector(
                    SelectSelectorConfig(
                        options=cpu_choices,
                        mode=SelectSelectorMode.DROPDOWN,
                        translation_key=CONF_CPU_TEMPERATURE_SOURCE,
                    )
                )
            )

        return self.async_show_form(step_id="init", data_schema=vol.Schema(schema))
