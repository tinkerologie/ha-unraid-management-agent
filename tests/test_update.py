"""Test the update platform (Unraid OS, plugin and container update entities)."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest
from homeassistant.components.update import (
    ATTR_IN_PROGRESS,
    ATTR_INSTALLED_VERSION,
    ATTR_LATEST_VERSION,
    ATTR_TITLE,
    DATA_COMPONENT,
    SERVICE_INSTALL,
    UpdateEntityFeature,
)
from homeassistant.components.update import DOMAIN as UPDATE_DOMAIN
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_SUPPORTED_FEATURES,
    STATE_OFF,
    STATE_ON,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant.common import MockConfigEntry

from custom_components.unraid_management_agent.api import UnraidAPIError, UnraidClient
from custom_components.unraid_management_agent.api.models import (
    ContainerUpdateInfo,
    ContainerUpdatesResult,
    DockerSettings,
    PluginInfo,
    PluginList,
    UpdateStatus,
)
from custom_components.unraid_management_agent.cleanup import (
    _build_valid_dynamic_entity_keys,
    _unavailable_data_prefixes,
)
from custom_components.unraid_management_agent.const import (
    CONF_ENABLE_CONTAINER_DEVICES,
    CONF_ENABLE_CONTAINER_UPDATES,
    CONF_READ_ONLY,
    DOMAIN,
)
from custom_components.unraid_management_agent.coordinator import UnraidData
from custom_components.unraid_management_agent.update import (
    UnraidContainerUpdate,
    UnraidPluginUpdate,
    container_update_key,
    plugin_update_key,
)

from .const import MOCK_CONFIG, MOCK_OPTIONS, mock_containers

ENTRY_ID = "test_entry_id"

PLEX_CURRENT = "sha256:" + "a" * 64
PLEX_LATEST = "sha256:" + "b" * 64
SONARR_DIGEST = "sha256:" + "c" * 64

INSTALL_PROGRESS = UpdateEntityFeature.INSTALL | UpdateEntityFeature.PROGRESS


def _plugins(*plugins: PluginInfo) -> PluginList:
    return PluginList(plugins=list(plugins))


def _default_plugins() -> PluginList:
    return _plugins(
        PluginInfo(
            name="community.applications",
            version="2026.10.01",
            update_available=True,
            latest_version="2026.10.06",
        ),
        PluginInfo(name="user.scripts", version="2026.09.01", update_available=False),
        PluginInfo(
            name="unraid-management-agent",
            version="2026.09.01",
            update_available=True,
            latest_version="2026.10.01",
        ),
        PluginInfo(name="unknown.state", version="1.0", update_available=None),
        PluginInfo(
            name="no.latest", version="1.0", update_available=True, latest_version=""
        ),
        # Never get an update entity
        PluginInfo(name="._user.scripts", version="", update_available=False),
        PluginInfo(name="tailscale", version="", update_available=False),
        PluginInfo(name="unRAIDServer", version="7.4.0", update_available=True),
        PluginInfo(name=None, version="1.0"),
    )


def _container_updates() -> ContainerUpdatesResult:
    return ContainerUpdatesResult(
        containers=[
            ContainerUpdateInfo(
                container_name="plex",
                image="plexinc/pms-docker:latest",
                current_digest=PLEX_CURRENT,
                latest_digest=PLEX_LATEST,
                update_available=True,
            ),
            ContainerUpdateInfo(
                container_name="sonarr",
                image="linuxserver/sonarr:latest",
                current_digest=SONARR_DIGEST,
                latest_digest=SONARR_DIGEST,
                update_available=False,
            ),
        ]
    )


async def _setup(hass: HomeAssistant, **options: Any) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Unraid (unraid-test)",
        data=MOCK_CONFIG,
        options={**MOCK_OPTIONS, **options},
        entry_id=ENTRY_ID,
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


def _entity_id(hass: HomeAssistant, key: str) -> str | None:
    return er.async_get(hass).async_get_entity_id(
        UPDATE_DOMAIN, DOMAIN, f"{ENTRY_ID}_{key}"
    )


def _entity(hass: HomeAssistant, key: str) -> Any:
    entity_id = _entity_id(hass, key)
    assert entity_id is not None
    return hass.data[DATA_COMPONENT].get_entity(entity_id)


async def _install(hass: HomeAssistant, entity_id: str) -> None:
    await hass.services.async_call(
        UPDATE_DOMAIN, SERVICE_INSTALL, {ATTR_ENTITY_ID: entity_id}, blocking=True
    )


# ── Unraid OS ─────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (
            UpdateStatus(
                current_version="7.4.0",
                latest_version="7.4.1",
                os_update_available=True,
            ),
            (STATE_ON, "7.4.0", "7.4.1"),
        ),
        (
            # A different (older) release the agent says is not an update
            UpdateStatus(
                current_version="7.4.0-beta.3",
                latest_version="7.3.2",
                os_update_available=False,
            ),
            (STATE_OFF, "7.4.0-beta.3", "7.4.0-beta.3"),
        ),
        (
            # No update flag: Home Assistant compares the versions
            UpdateStatus(current_version="7.4.0", latest_version="7.4.0"),
            (STATE_OFF, "7.4.0", "7.4.0"),
        ),
        (
            # The agent has no update information
            UpdateStatus(current_version="7.4.0", os_update_available=False),
            (STATE_UNKNOWN, "7.4.0", None),
        ),
        (UpdateStatus(current_version=""), (STATE_UNKNOWN, None, None)),
    ],
    ids=["update", "agent_says_no_update", "same_version", "no_info", "no_version"],
)
@pytest.mark.usefixtures(
    "mock_unraid_client_class", "mock_unraid_websocket_client_class"
)
async def test_os_update(
    hass: HomeAssistant,
    mock_async_unraid_client: MagicMock,
    status: UpdateStatus,
    expected: tuple[str, str | None, str | None],
) -> None:
    """The OS entity shows the agent's OS update status and is never installable."""
    state, installed, latest = expected
    mock_async_unraid_client.get_update_status.return_value = status
    await _setup(hass)

    entity_id = _entity_id(hass, "os_update")
    assert entity_id == "update.unraid_test_unraid_os"
    os_state = hass.states.get(entity_id)
    assert os_state.state == state
    assert os_state.attributes[ATTR_INSTALLED_VERSION] == installed
    assert os_state.attributes[ATTR_LATEST_VERSION] == latest
    assert os_state.attributes[ATTR_TITLE] == "Unraid OS"
    assert os_state.attributes[ATTR_SUPPORTED_FEATURES] == 0


@pytest.mark.usefixtures(
    "mock_unraid_client_class", "mock_unraid_websocket_client_class"
)
async def test_os_update_unavailable_without_status(hass: HomeAssistant) -> None:
    """Without update status from the agent the OS entity is unavailable."""
    await _setup(hass)
    assert hass.states.get("update.unraid_test_unraid_os").state == STATE_UNAVAILABLE


# ── Plugins ───────────────────────────────────────────────────────────────────


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_plugin_updates(
    hass: HomeAssistant,
    mock_unraid_client_class: MagicMock,
    mock_async_unraid_client: MagicMock,
) -> None:
    """Each plugin gets an update entity showing its versions."""
    mock_async_unraid_client.list_plugins.return_value = _default_plugins()
    await _setup(hass)

    ca = hass.states.get("update.unraid_test_plugin_community_applications")
    assert ca.state == STATE_ON
    assert ca.attributes[ATTR_INSTALLED_VERSION] == "2026.10.01"
    assert ca.attributes[ATTR_LATEST_VERSION] == "2026.10.06"
    assert ca.attributes[ATTR_TITLE] == "community.applications"
    assert ca.attributes[ATTR_SUPPORTED_FEATURES] == 0

    scripts = hass.states.get("update.unraid_test_plugin_user_scripts")
    assert scripts.state == STATE_OFF
    assert scripts.attributes[ATTR_LATEST_VERSION] == "2026.09.01"

    # The agent's own plugin is shown like any other
    agent = hass.states.get("update.unraid_test_plugin_unraid_management_agent")
    assert agent.state == STATE_ON
    assert agent.attributes[ATTR_SUPPORTED_FEATURES] == 0

    # Update state not known
    assert hass.states.get("update.unraid_test_plugin_unknown_state").state == (
        STATE_UNKNOWN
    )
    assert hass.states.get("update.unraid_test_plugin_no_latest").state == (
        STATE_UNKNOWN
    )

    # OS plugins, hidden files and plugins without a version are skipped
    for name in ("._user.scripts", "tailscale", "unRAIDServer"):
        assert _entity_id(hass, plugin_update_key(name)) is None
    plugin_entities = [
        e
        for e in er.async_entries_for_config_entry(er.async_get(hass), ENTRY_ID)
        if e.unique_id.startswith(f"{ENTRY_ID}_plugin_")
    ]
    assert len(plugin_entities) == 5

    # Plugin entities sit on the server device
    server = dr.async_get(hass).async_get_device_by_identifier(
        (DOMAIN, ENTRY_ID), ENTRY_ID
    )
    assert all(e.device_id == server.id for e in plugin_entities)


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_plugin_updates_are_display_only(
    hass: HomeAssistant,
    mock_unraid_client_class: MagicMock,
    mock_async_unraid_client: MagicMock,
) -> None:
    """A plugin update can't be installed from Home Assistant."""
    mock_async_unraid_client.list_plugins.return_value = _default_plugins()
    await _setup(hass)
    entity_id = "update.unraid_test_plugin_community_applications"

    state = hass.states.get(entity_id)
    assert state.state == STATE_ON
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == 0
    with pytest.raises(HomeAssistantError):
        await _install(hass, entity_id)
    assert not hasattr(UnraidClient, "update_plugin")
    assert not hasattr(UnraidClient, "update_all_plugins")


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_plugin_entities_added_and_removed_dynamically(
    hass: HomeAssistant,
    mock_unraid_client_class: MagicMock,
    mock_async_unraid_client: MagicMock,
) -> None:
    """Plugins installed later get an entity; removed ones become unavailable."""
    mock_async_unraid_client.list_plugins.return_value = _plugins(
        PluginInfo(name="user.scripts", version="1.0", update_available=False)
    )
    entry = await _setup(hass)
    coordinator = entry.runtime_data.coordinator
    assert _entity_id(hass, plugin_update_key("gpustat")) is None

    mock_async_unraid_client.list_plugins.return_value = _plugins(
        PluginInfo(name="gpustat", version="2.0", update_available=False)
    )
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    assert hass.states.get("update.unraid_test_plugin_gpustat").state == STATE_OFF
    assert (
        hass.states.get("update.unraid_test_plugin_user_scripts").state
        == STATE_UNAVAILABLE
    )

    # An entity removed from the registry is re-created when its plugin is seen
    registry = er.async_get(hass)
    registry.async_remove("update.unraid_test_plugin_gpustat")
    await hass.async_block_till_done()
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert _entity_id(hass, plugin_update_key("gpustat")) is not None


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_plugin_properties_without_plugin_data(
    hass: HomeAssistant,
    mock_unraid_client_class: MagicMock,
    mock_async_unraid_client: MagicMock,
) -> None:
    """Versions are unknown once the plugin list is gone."""
    mock_async_unraid_client.list_plugins.return_value = _default_plugins()
    await _setup(hass)
    entity: UnraidPluginUpdate = _entity(
        hass, plugin_update_key("community.applications")
    )

    entity.coordinator.data.plugins = None
    assert entity.available is False
    assert entity.installed_version is None
    assert entity.latest_version is None


# ── Containers ────────────────────────────────────────────────────────────────


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_container_updates(
    hass: HomeAssistant,
    mock_unraid_client_class: MagicMock,
    mock_async_unraid_client: MagicMock,
) -> None:
    """With container update checks on, each container gets an update entity."""
    mock_async_unraid_client.check_all_container_updates.return_value = (
        _container_updates()
    )
    await _setup(hass, **{CONF_ENABLE_CONTAINER_UPDATES: True})

    plex = hass.states.get("update.unraid_test_container_plex_image")
    assert plex.state == STATE_ON
    assert plex.attributes[ATTR_INSTALLED_VERSION] == "aaaaaaaaaaaa"
    assert plex.attributes[ATTR_LATEST_VERSION] == "bbbbbbbbbbbb"
    assert plex.attributes[ATTR_TITLE] == "plexinc/pms-docker:latest"
    assert plex.attributes[ATTR_SUPPORTED_FEATURES] == INSTALL_PROGRESS

    sonarr = hass.states.get("update.unraid_test_container_sonarr_image")
    assert sonarr.state == STATE_OFF
    assert sonarr.attributes[ATTR_INSTALLED_VERSION] == "cccccccccccc"
    assert sonarr.attributes[ATTR_LATEST_VERSION] == "cccccccccccc"

    # Without container devices they sit on the server device
    server = dr.async_get(hass).async_get_device_by_identifier(
        (DOMAIN, ENTRY_ID), ENTRY_ID
    )
    entry = er.async_get(hass).async_get("update.unraid_test_container_plex_image")
    assert entry.device_id == server.id


@pytest.mark.usefixtures(
    "mock_unraid_client_class", "mock_unraid_websocket_client_class"
)
async def test_no_container_updates_without_option(hass: HomeAssistant) -> None:
    """Container update entities need the container update checks option."""
    await _setup(hass)
    assert _entity_id(hass, container_update_key("plex")) is None


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_no_container_updates_when_docker_disabled(
    hass: HomeAssistant,
    mock_unraid_client_class: MagicMock,
    mock_async_unraid_client: MagicMock,
) -> None:
    """No container update entities when the Docker service is disabled."""
    mock_async_unraid_client.get_docker_settings.return_value = DockerSettings(
        enabled=False
    )
    await _setup(hass, **{CONF_ENABLE_CONTAINER_UPDATES: True})
    assert _entity_id(hass, container_update_key("plex")) is None


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_container_updates_added_when_containers_appear(
    hass: HomeAssistant,
    mock_unraid_client_class: MagicMock,
    mock_async_unraid_client: MagicMock,
) -> None:
    """Containers that appear after setup get an update entity."""
    mock_async_unraid_client.list_containers.return_value = []
    entry = await _setup(hass, **{CONF_ENABLE_CONTAINER_UPDATES: True})
    assert _entity_id(hass, container_update_key("plex")) is None

    mock_async_unraid_client.list_containers.return_value = mock_containers()
    await entry.runtime_data.coordinator.async_refresh()
    await hass.async_block_till_done()

    # Not checked yet: no update information for the container
    plex = hass.states.get("update.unraid_test_container_plex_image")
    assert plex.state == STATE_UNKNOWN
    assert plex.attributes[ATTR_INSTALLED_VERSION] is None


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_container_update_states(
    hass: HomeAssistant,
    mock_unraid_client_class: MagicMock,
    mock_async_unraid_client: MagicMock,
) -> None:
    """Unchecked containers are unknown and digests are compared as text."""
    mock_async_unraid_client.check_all_container_updates.return_value = (
        ContainerUpdatesResult(
            containers=[
                # Registry could not be reached: no latest digest
                ContainerUpdateInfo(
                    container_name="plex",
                    current_digest=PLEX_CURRENT,
                    update_available=False,
                ),
                # All-digit digests must not be compared as numbers
                ContainerUpdateInfo(
                    container_name="sonarr",
                    current_digest="sha256:" + "9" * 64,
                    latest_digest="sha256:" + "1" * 64,
                    update_available=True,
                ),
            ]
        )
    )
    await _setup(hass, **{CONF_ENABLE_CONTAINER_UPDATES: True})

    plex = hass.states.get("update.unraid_test_container_plex_image")
    assert plex.state == STATE_UNKNOWN
    assert plex.attributes[ATTR_INSTALLED_VERSION] == "aaaaaaaaaaaa"
    assert plex.attributes[ATTR_LATEST_VERSION] is None

    sonarr = hass.states.get("update.unraid_test_container_sonarr_image")
    assert sonarr.state == STATE_ON
    assert sonarr.attributes[ATTR_INSTALLED_VERSION] == "999999999999"
    assert sonarr.attributes[ATTR_LATEST_VERSION] == "111111111111"


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_container_install(
    hass: HomeAssistant,
    mock_unraid_client_class: MagicMock,
    mock_async_unraid_client: MagicMock,
) -> None:
    """Installing asks the agent to update the container by its ID."""
    mock_async_unraid_client.check_all_container_updates.return_value = (
        _container_updates()
    )
    entry = await _setup(hass, **{CONF_ENABLE_CONTAINER_UPDATES: True})
    entity_id = "update.unraid_test_container_plex_image"

    await _install(hass, entity_id)
    await hass.async_block_till_done()

    mock_async_unraid_client.update_container.assert_awaited_once_with(
        "plex_container_id"
    )
    # The agent's cached check still reports the old digest; the installed
    # digest is shown until the agent reports something new
    state = hass.states.get(entity_id)
    assert state.state == STATE_OFF
    assert state.attributes[ATTR_INSTALLED_VERSION] == "bbbbbbbbbbbb"
    assert state.attributes[ATTR_IN_PROGRESS] is False

    # A newer image is published later
    newer = "sha256:" + "d" * 64
    mock_async_unraid_client.check_all_container_updates.return_value = (
        ContainerUpdatesResult(
            containers=[
                ContainerUpdateInfo(
                    container_name="plex",
                    current_digest=PLEX_LATEST,
                    latest_digest=newer,
                    update_available=True,
                )
            ]
        )
    )
    await entry.runtime_data.coordinator.async_refresh()
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state.state == STATE_ON
    assert state.attributes[ATTR_INSTALLED_VERSION] == "bbbbbbbbbbbb"
    assert state.attributes[ATTR_LATEST_VERSION] == "dddddddddddd"


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_container_install_by_name_and_failure(
    hass: HomeAssistant,
    mock_unraid_client_class: MagicMock,
    mock_async_unraid_client: MagicMock,
) -> None:
    """Without a container ID the name is used; failures raise translated errors."""
    containers = mock_containers()
    containers[0].id = None
    mock_async_unraid_client.list_containers.return_value = containers
    mock_async_unraid_client.check_all_container_updates.return_value = (
        _container_updates()
    )
    mock_async_unraid_client.update_container.side_effect = UnraidAPIError(
        "Failed to update container", status_code=500
    )
    await _setup(hass, **{CONF_ENABLE_CONTAINER_UPDATES: True})
    entity_id = "update.unraid_test_container_plex_image"

    with pytest.raises(HomeAssistantError) as err:
        await _install(hass, entity_id)
    assert err.value.translation_key == "container_update_failed"
    assert err.value.translation_placeholders == {"name": "plex"}
    mock_async_unraid_client.update_container.assert_awaited_once_with("plex")
    state = hass.states.get(entity_id)
    assert state.state == STATE_ON
    assert state.attributes[ATTR_INSTALLED_VERSION] == "aaaaaaaaaaaa"


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_container_install_without_data(
    hass: HomeAssistant,
    mock_unraid_client_class: MagicMock,
    mock_async_unraid_client: MagicMock,
) -> None:
    """Install still works when the container and its check result are gone."""
    mock_async_unraid_client.check_all_container_updates.return_value = (
        _container_updates()
    )
    await _setup(hass, **{CONF_ENABLE_CONTAINER_UPDATES: True})
    entity: UnraidContainerUpdate = _entity(hass, container_update_key("plex"))
    data = entity.coordinator.data

    # Removed while other containers remain; check result without digests
    data.containers = [c for c in data.containers if c.name != "plex"]
    data.container_updates = ContainerUpdatesResult(
        containers=[ContainerUpdateInfo(container_name="plex")]
    )
    assert entity.available is False
    assert entity.installed_version is None
    assert entity.latest_version is None

    data.containers = None
    data.container_updates = ContainerUpdatesResult()
    assert entity.available is False
    assert entity.title is None
    assert entity.installed_version is None

    await entity.async_install(None, backup=False)
    mock_async_unraid_client.update_container.assert_awaited_once_with("plex")


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_container_update_on_container_device(
    hass: HomeAssistant,
    mock_unraid_client_class: MagicMock,
    mock_async_unraid_client: MagicMock,
) -> None:
    """With container devices on, the update entity is the container's Image."""
    mock_async_unraid_client.check_all_container_updates.return_value = (
        _container_updates()
    )
    await _setup(
        hass,
        **{CONF_ENABLE_CONTAINER_UPDATES: True, CONF_ENABLE_CONTAINER_DEVICES: True},
    )

    plex_device = dr.async_get(hass).async_get_child_device_by_identifier(
        (DOMAIN, f"{ENTRY_ID}_container_plex"), ENTRY_ID
    )
    entry = er.async_get(hass).async_get("update.unraid_test_docker_plex_image")
    assert entry is not None
    assert entry.device_id == plex_device.id
    assert hass.states.get("update.unraid_test_docker_plex_image").state == STATE_ON


# ── Read-only mode ────────────────────────────────────────────────────────────


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_read_only_shows_updates_without_install(
    hass: HomeAssistant,
    mock_unraid_client_class: MagicMock,
    mock_async_unraid_client: MagicMock,
) -> None:
    """In read-only mode updates are shown but cannot be installed."""
    mock_async_unraid_client.list_plugins.return_value = _default_plugins()
    mock_async_unraid_client.check_all_container_updates.return_value = (
        _container_updates()
    )
    await _setup(hass, **{CONF_READ_ONLY: True, CONF_ENABLE_CONTAINER_UPDATES: True})

    for entity_id in (
        "update.unraid_test_plugin_community_applications",
        "update.unraid_test_container_plex_image",
    ):
        state = hass.states.get(entity_id)
        assert state.state == STATE_ON
        assert state.attributes[ATTR_SUPPORTED_FEATURES] == 0
        with pytest.raises(HomeAssistantError):
            await _install(hass, entity_id)

    # Called directly anyway, install refuses with the read-only error
    entity = _entity(hass, container_update_key("plex"))
    with pytest.raises(ServiceValidationError) as err:
        await entity.async_install(None, backup=False)
    assert err.value.translation_key == "read_only_mode"
    assert err.value.translation_placeholders == {"title": "Unraid (unraid-test)"}
    mock_async_unraid_client.update_container.assert_not_called()


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_install_refused_after_switching_to_read_only(
    hass: HomeAssistant,
    mock_unraid_client_class: MagicMock,
    mock_async_unraid_client: MagicMock,
) -> None:
    """An entity created before read-only was turned on still refuses to install."""
    mock_async_unraid_client.check_all_container_updates.return_value = (
        _container_updates()
    )
    entry = await _setup(hass, **{CONF_ENABLE_CONTAINER_UPDATES: True})
    entity = _entity(hass, container_update_key("plex"))
    assert entity.supported_features == INSTALL_PROGRESS

    hass.config_entries.async_update_entry(
        entry, options={**entry.options, CONF_READ_ONLY: True}
    )
    with pytest.raises(ServiceValidationError) as err:
        await entity.async_install(None, backup=False)
    assert err.value.translation_key == "read_only_mode"
    mock_async_unraid_client.update_container.assert_not_called()


# ── Stale entity cleanup ──────────────────────────────────────────────────────


def test_valid_keys_include_update_entities() -> None:
    """Plugin and (with the option on) container update keys are kept."""
    data = UnraidData(containers=mock_containers(), plugins=_default_plugins())

    keys = _build_valid_dynamic_entity_keys(data, container_updates=True)
    assert container_update_key("plex") in keys
    assert plugin_update_key("community.applications") in keys
    assert plugin_update_key("tailscale") not in keys
    assert plugin_update_key("unRAIDServer") not in keys

    # With container update checks off, container update entities are stale
    keys = _build_valid_dynamic_entity_keys(data)
    assert container_update_key("plex") not in keys
    assert plugin_update_key("community.applications") in keys


def test_plugin_prefix_protected_when_plugin_list_unavailable() -> None:
    """Plugin update entities are not removed while the plugin list is missing."""
    assert "plugin_" in _unavailable_data_prefixes(UnraidData())
    assert "plugin_" in _unavailable_data_prefixes(UnraidData(plugins=PluginList()))
    assert "plugin_" not in _unavailable_data_prefixes(
        UnraidData(plugins=PluginList(plugins=[]))
    )


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_container_update_entities_removed_when_option_turned_off(
    hass: HomeAssistant,
    mock_unraid_client_class: MagicMock,
    mock_async_unraid_client: MagicMock,
    freezer: Any,
) -> None:
    """Turning container update checks off removes their entities after the grace period."""
    mock_async_unraid_client.check_all_container_updates.return_value = (
        _container_updates()
    )
    entry = await _setup(hass, **{CONF_ENABLE_CONTAINER_UPDATES: True})
    assert _entity_id(hass, container_update_key("plex")) is not None

    hass.config_entries.async_update_entry(
        entry, options={**entry.options, CONF_ENABLE_CONTAINER_UPDATES: False}
    )
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    coordinator = entry.runtime_data.coordinator

    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert _entity_id(hass, container_update_key("plex")) is not None

    freezer.tick(60 * 11)
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert _entity_id(hass, container_update_key("plex")) is None
