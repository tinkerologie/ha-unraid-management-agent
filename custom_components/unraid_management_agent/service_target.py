"""Resolve a domain action to its configured server."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import ATTR_CONFIG_ENTRY_ID
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import issue_registry as ir

from .const import CONF_READ_ONLY, DEFAULT_READ_ONLY, DOMAIN

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant, ServiceCall

    from .coordinator import UnraidConfigEntry, UnraidDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)
_SERVICE_TARGET_ISSUE = "service_config_entry_id_required"


def is_read_only(entry: UnraidConfigEntry) -> bool:
    """Return whether control actions are disabled for the configured server."""
    return bool(entry.options.get(CONF_READ_ONLY, DEFAULT_READ_ONLY))


def resolve_service_target(
    hass: HomeAssistant, call: ServiceCall
) -> UnraidDataUpdateCoordinator:
    """Return the selected server's coordinator or raise a translated error."""
    if ATTR_CONFIG_ENTRY_ID in call.data:
        entry_id = call.data[ATTR_CONFIG_ENTRY_ID]
        entry = hass.config_entries.async_get_entry(entry_id)
        if entry is None or entry.domain != DOMAIN:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="config_entry_not_found",
                translation_placeholders={"config_entry_id": entry_id},
            )
    else:
        entries = hass.config_entries.async_entries(DOMAIN)
        if not entries:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="no_config_entries",
            )
        entry = entries[0]
        if (
            len(entries) > 1
            and ir.async_get(hass).async_get_issue(DOMAIN, _SERVICE_TARGET_ISSUE)
            is None
        ):
            _LOGGER.warning(
                "Action %s omitted config_entry_id with multiple servers configured. "
                "Using %s for compatibility",
                call.service,
                entry.title,
            )
            ir.async_create_issue(
                hass,
                DOMAIN,
                _SERVICE_TARGET_ISSUE,
                is_fixable=False,
                is_persistent=False,
                severity=ir.IssueSeverity.WARNING,
                translation_key=_SERVICE_TARGET_ISSUE,
            )

    if entry.state is not ConfigEntryState.LOADED:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="entry_not_loaded",
            translation_placeholders={"title": entry.title},
        )
    if is_read_only(entry):
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="read_only_mode",
            translation_placeholders={"title": entry.title},
        )
    return entry.runtime_data.coordinator
