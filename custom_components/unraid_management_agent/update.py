"""
Update platform for Unraid Management Agent.

Exposes available updates as Home Assistant update entities:

- Unraid OS: display only. The OS is never installed from Home Assistant.
- Plugins: one per installed plugin, display only. The agent never installs or
  updates plugins; updates are applied from Unraid's Plugins page.
- Docker containers: one per container when the "container update checks"
  option is on, installable through the agent. Versions are shown as short
  image digests, because the registry only provides a digest for the latest
  image (no version number).

All state comes from data the coordinator already fetches (``/updates``,
``/plugins`` and, with the option on, ``/docker/updates``); no extra polling
is added. In read-only mode the entities still report available updates but
do not offer to install them.
"""

from __future__ import annotations

import hashlib
import logging
from typing import Any

from homeassistant.components.update import UpdateEntity, UpdateEntityFeature
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import slugify

from . import UnraidConfigEntry, UnraidDataUpdateCoordinator
from .cleanup import async_prune_seen_names
from .const import DOMAIN
from .entity import (
    UnraidBaseEntity,
    build_container_device_info,
    container_devices_enabled,
    read_only_enabled,
)

_LOGGER = logging.getLogger(__name__)

# Coordinator handles updates, so no parallel update limit
PARALLEL_UPDATES = 0

# The Unraid OS itself is shipped as these plugins. It is covered by the
# display-only OS entity and must never be installable as a plugin.
_OS_PLUGIN_NAMES: frozenset[str] = frozenset({"unRAIDServer", "unRAIDServer-"})

# Length of the digest shown as a container "version" (like `docker images`)
_SHORT_DIGEST_LENGTH = 12


def _name_key(name: str) -> str:
    """Build a stable key from a name: readable slug plus a short hash."""
    name_hash = hashlib.md5(name.encode(), usedforsecurity=False).hexdigest()[:6]
    return f"{slugify(name)}_{name_hash}"


def plugin_update_key(name: str) -> str:
    """Return the entity key of a plugin's update entity."""
    return f"plugin_{_name_key(name)}"


def container_update_key(name: str) -> str:
    """Return the entity key of a container's update entity."""
    return f"container_{_name_key(name)}_update"


def is_updatable_plugin(plugin: Any) -> bool:
    """
    Return True when a plugin from ``/plugins`` gets an update entity.

    Skipped: the OS plugins, hidden files (e.g. macOS ``._name.plg``
    metadata files on the flash drive), and plugins whose version the agent
    could not read (their update state can never be determined).
    """
    name = getattr(plugin, "name", None)
    return bool(
        name
        and not name.startswith(".")
        and name not in _OS_PLUGIN_NAMES
        and getattr(plugin, "version", None)
    )


def _short_digest(digest: str | None) -> str | None:
    """Shorten an image digest (``sha256:<hex>``) to its first 12 hex digits."""
    if not digest:
        return None
    return digest.removeprefix("sha256:")[:_SHORT_DIGEST_LENGTH]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: UnraidConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Unraid update entities."""
    coordinator = entry.runtime_data.coordinator

    async_add_entities([UnraidOSUpdate(coordinator)])

    # Plugin update entities - created as plugins appear
    seen_plugins: set[str] = set()

    def _add_plugin_updates() -> None:
        data = coordinator.data
        if not data or not data.plugins or not data.plugins.plugins:
            return
        # Allow re-creation of entities removed from the registry (see #83)
        async_prune_seen_names(
            hass,
            "update",
            seen_plugins,
            lambda name: f"{entry.entry_id}_{plugin_update_key(name)}",
        )
        new_entities: list[UpdateEntity] = []
        for plugin in data.plugins.plugins:
            if not is_updatable_plugin(plugin) or plugin.name in seen_plugins:
                continue
            seen_plugins.add(plugin.name)
            new_entities.append(UnraidPluginUpdate(coordinator, plugin.name))
        if new_entities:
            async_add_entities(new_entities)

    # Container update entities - only with the "container update checks"
    # option on, since their data is only fetched then
    seen_containers: set[str] = set()

    def _add_container_updates() -> None:
        if not (
            coordinator.is_container_updates_enabled()
            and coordinator.is_collector_enabled("docker")
            and coordinator.is_docker_enabled()
        ):
            return
        data = coordinator.data
        if not data or not data.containers:
            return
        # Allow re-creation of entities removed from the registry (see #83)
        async_prune_seen_names(
            hass,
            "update",
            seen_containers,
            lambda name: f"{entry.entry_id}_{container_update_key(name)}",
        )
        new_entities: list[UpdateEntity] = []
        for container in data.containers:
            name = getattr(container, "name", None)
            if not name or name in seen_containers:
                continue
            seen_containers.add(name)
            new_entities.append(UnraidContainerUpdate(coordinator, name))
        if new_entities:
            async_add_entities(new_entities)

    _add_plugin_updates()
    _add_container_updates()

    entry.async_on_unload(coordinator.async_add_listener(callback(_add_plugin_updates)))
    entry.async_on_unload(
        coordinator.async_add_listener(callback(_add_container_updates))
    )


class _UnraidUpdateBase(UnraidBaseEntity, UpdateEntity):
    """Common behaviour of the installable (container) update entities."""

    _failed_translation_key: str

    def __init__(
        self,
        coordinator: UnraidDataUpdateCoordinator,
        key: str,
        name: str,
    ) -> None:
        """Initialize the entity; INSTALL is never offered in read-only mode."""
        super().__init__(coordinator, key)
        self._update_name = name
        if not read_only_enabled(coordinator):
            # PROGRESS lets Home Assistant reject a second install request
            # while one is still running
            self._attr_supported_features = (
                UpdateEntityFeature.INSTALL | UpdateEntityFeature.PROGRESS
            )

    async def _async_install_update(self) -> None:
        """Ask the agent to install the update."""
        raise NotImplementedError

    async def async_install(
        self, version: str | None, backup: bool, **kwargs: Any
    ) -> None:
        """Install the latest update through the agent."""
        # Install is not offered in read-only mode; refuse if called anyway
        if read_only_enabled(self.coordinator):
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="read_only_mode",
                translation_placeholders={"title": self.coordinator.config_entry.title},
            )
        # Home Assistant clears this when the install returns or fails
        self._attr_in_progress = True
        self.async_write_ha_state()
        try:
            await self._async_install_update()
        except Exception as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key=self._failed_translation_key,
                translation_placeholders={"name": self._update_name},
            ) from err
        await self.coordinator.async_request_refresh()


class UnraidOSUpdate(UnraidBaseEntity, UpdateEntity):
    """
    Unraid OS update (display only).

    OS updates need a reboot and are applied from the Unraid web UI, so this
    entity never supports install.
    """

    _attr_translation_key = "unraid_os"
    _attr_title = "Unraid OS"

    def __init__(self, coordinator: UnraidDataUpdateCoordinator) -> None:
        """Initialize the entity."""
        super().__init__(coordinator, "os_update")

    @property
    def available(self) -> bool:
        """Return True when the agent reported OS update status."""
        data = self.coordinator.data
        return super().available and data is not None and data.update_status is not None

    @property
    def installed_version(self) -> str | None:
        """Return the running Unraid version."""
        status = self.coordinator.data.update_status
        return status.current_version or None

    @property
    def latest_version(self) -> str | None:
        """
        Return the newest Unraid version the agent knows of.

        Unknown when the agent has no update information; equal to the
        installed version when the agent reports no update.
        """
        status = self.coordinator.data.update_status
        if not status.latest_version:
            return None
        if status.os_update_available is False:
            return self.installed_version
        return status.latest_version


class UnraidPluginUpdate(UnraidBaseEntity, UpdateEntity):
    """
    Update entity for an Unraid plugin (display only).

    The agent reports plugin updates but never applies them, so this entity
    never supports install.
    """

    _attr_translation_key = "plugin"

    def __init__(
        self, coordinator: UnraidDataUpdateCoordinator, plugin_name: str
    ) -> None:
        """Initialize the entity."""
        self._plugin_name = plugin_name
        super().__init__(coordinator, plugin_update_key(plugin_name))
        self._attr_translation_placeholders = {"name": plugin_name}
        self._attr_title = plugin_name

    def _find_plugin(self) -> Any | None:
        """Find this plugin in the coordinator data."""
        data = self.coordinator.data
        if not data or not data.plugins or not data.plugins.plugins:
            return None
        for plugin in data.plugins.plugins:
            if plugin.name == self._plugin_name:
                return plugin
        return None

    @property
    def available(self) -> bool:
        """Return True while the plugin is installed."""
        return super().available and self._find_plugin() is not None

    @property
    def installed_version(self) -> str | None:
        """Return the installed plugin version."""
        plugin = self._find_plugin()
        return (plugin.version or None) if plugin else None

    @property
    def latest_version(self) -> str | None:
        """Return the latest plugin version (the installed one if up to date)."""
        plugin = self._find_plugin()
        if plugin is None:
            return None
        if plugin.update_available:
            return plugin.latest_version or None
        if plugin.update_available is False:
            return plugin.version or None
        return None


class UnraidContainerUpdate(_UnraidUpdateBase):
    """
    Update entity for a Docker container's image.

    Installed and latest "versions" are short image digests: the running
    image's digest and the registry's digest for the container's image tag.
    """

    _failed_translation_key = "container_update_failed"

    def __init__(
        self, coordinator: UnraidDataUpdateCoordinator, container_name: str
    ) -> None:
        """Initialize the entity."""
        self._container_name = container_name
        # Digest installed through this entity; see installed_version
        self._installed_digest: str | None = None
        super().__init__(
            coordinator, container_update_key(container_name), container_name
        )
        if container_devices_enabled(coordinator):
            self._attr_translation_key = "container_device_image"
            self._attr_device_info = build_container_device_info(
                coordinator, container_name
            )
        else:
            self._attr_translation_key = "container_image"
            self._attr_translation_placeholders = {"name": container_name}

    def _find_container(self) -> Any | None:
        """Find this container in the coordinator data."""
        data = self.coordinator.data
        if not data or not data.containers:
            return None
        for container in data.containers:
            if getattr(container, "name", None) == self._container_name:
                return container
        return None

    def _find_update_info(self) -> Any | None:
        """Find this container's update check result."""
        data = self.coordinator.data
        if not data or not data.container_updates:
            return None
        for info in data.container_updates.containers or []:
            if info.container_name == self._container_name:
                return info
        return None

    @property
    def available(self) -> bool:
        """Return True while the container exists."""
        return super().available and self._find_container() is not None

    @property
    def title(self) -> str | None:
        """Return the container's image."""
        container = self._find_container()
        return getattr(container, "image", None) if container else None

    @property
    def installed_version(self) -> str | None:
        """
        Return the short digest of the running image.

        The agent re-checks registries only every few hours, so right after
        an update installed from here it still reports the old digest. Until
        it reports something new, the digest that was installed is shown.
        """
        info = self._find_update_info()
        if info is None:
            return None
        if self._installed_digest and info.latest_digest == self._installed_digest:
            return _short_digest(info.latest_digest)
        return _short_digest(info.current_digest)

    @property
    def latest_version(self) -> str | None:
        """Return the short registry digest (the installed one if up to date)."""
        info = self._find_update_info()
        if info is None or not info.latest_digest:
            # Not checked yet, or the registry could not be reached
            return None
        if info.update_available:
            return _short_digest(info.latest_digest)
        return self.installed_version

    def version_is_newer(self, latest_version: str, installed_version: str) -> bool:
        """
        Return True: differing digests always mean an update.

        Digests have no order (an all-digit digest would otherwise be
        compared as a number), and equal digests never reach this method.
        """
        return True

    async def _async_install_update(self) -> None:
        """Pull the latest image and recreate the container through the agent."""
        info = self._find_update_info()
        container = self._find_container()
        container_ref = (
            getattr(container, "id", None) if container else None
        ) or self._container_name
        await self.coordinator.client.update_container(container_ref)
        _LOGGER.info("Updated container: %s", self._container_name)
        if info is not None:
            self._installed_digest = info.latest_digest
