# ruff: noqa: S105, S106  # dummy tokens for tests
"""Test API token (bearer) authentication against the agent."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_API_TOKEN, CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from pytest_homeassistant.common import MockConfigEntry
from pytest_homeassistant.test_util.aiohttp import (
    AiohttpClientMocker,
)

from custom_components.unraid_management_agent.api import (
    UnraidAPIError,
    UnraidAuthenticationError,
    UnraidClient,
    UnraidConnectionError,
    UnraidWebSocketClient,
)
from custom_components.unraid_management_agent.const import DOMAIN

from .const import MOCK_CONFIG, MOCK_OPTIONS, mock_system_info

BASE = "http://192.0.2.10:8043/api/v1"
FLOW_CLIENT = "custom_components.unraid_management_agent.config_flow.UnraidClient"


def _flow_client(*, reject: bool = False, error: Exception | None = None) -> MagicMock:
    client = MagicMock()
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=None)
    if reject:
        error = UnraidAuthenticationError("Unauthorized", status_code=401)
    if error is not None:
        client.get_system_info = AsyncMock(side_effect=error)
    else:
        client.get_system_info = AsyncMock(return_value=mock_system_info())
    return client


def _token_entry(hass: HomeAssistant) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={**MOCK_CONFIG, CONF_API_TOKEN: "old"},
        options=MOCK_OPTIONS,
        unique_id=f"{MOCK_CONFIG[CONF_HOST]}:{MOCK_CONFIG[CONF_PORT]}",
    )
    entry.add_to_hass(hass)
    return entry


async def test_client_sends_bearer_token(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Every REST request carries the token as a bearer credential."""
    aioclient_mock.get(f"{BASE}/system", json={"hostname": "tower"})
    client = UnraidClient(
        "192.0.2.10", 8043, session=async_get_clientsession(hass), api_token=" s3cret "
    )
    info = await client.get_system_info()

    assert info.hostname == "tower"
    headers = aioclient_mock.mock_calls[0][3]
    assert headers["Authorization"] == "Bearer s3cret"


async def test_client_without_token_sends_no_auth_header(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Without a token nothing changes for agents that have auth disabled."""
    aioclient_mock.get(f"{BASE}/system", json={"hostname": "tower"})
    client = UnraidClient("192.0.2.10", 8043, session=async_get_clientsession(hass))
    await client.get_system_info()

    assert "Authorization" not in (aioclient_mock.mock_calls[0][3] or {})


async def test_client_raises_auth_error_on_401(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """A rejected token is a distinct error, not a generic API error."""
    aioclient_mock.get(f"{BASE}/system", status=401, json={"error": "Unauthorized"})
    client = UnraidClient(
        "192.0.2.10", 8043, session=async_get_clientsession(hass), api_token="wrong"
    )
    with pytest.raises(UnraidAuthenticationError) as err:
        await client.get_system_info()
    assert err.value.status_code == 401


async def test_client_treats_403_as_api_error(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """The agent only uses 403 for origin (CSRF) checks, never for a bad token."""
    aioclient_mock.get(
        f"{BASE}/system", status=403, json={"error": "Forbidden: origin not allowed"}
    )
    client = UnraidClient(
        "192.0.2.10", 8043, session=async_get_clientsession(hass), api_token="s3cret"
    )
    with pytest.raises(UnraidAPIError) as err:
        await client.get_system_info()
    assert not isinstance(err.value, UnraidAuthenticationError)
    assert err.value.status_code == 403


def test_websocket_client_sends_bearer_token() -> None:
    """The websocket handshake carries the same bearer credential."""
    assert UnraidWebSocketClient("h", 8043, api_token="s3cret")._headers == {
        "Authorization": "Bearer s3cret"
    }
    assert UnraidWebSocketClient("h", 8043)._headers == {}


async def test_user_flow_invalid_token(hass: HomeAssistant) -> None:
    """A rejected token is reported as invalid authentication."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    with patch(FLOW_CLIENT, return_value=_flow_client(reject=True)):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {**MOCK_CONFIG, CONF_API_TOKEN: "wrong"}
        )
    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}


async def test_user_flow_stores_token(
    hass: HomeAssistant, mock_setup_entry: AsyncMock
) -> None:
    """A valid token is saved with the entry and passed to the client."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    with patch(FLOW_CLIENT, return_value=_flow_client()) as client_class:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {**MOCK_CONFIG, CONF_API_TOKEN: "s3cret"}
        )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_API_TOKEN] == "s3cret"
    assert client_class.call_args.kwargs["api_token"] == "s3cret"


async def test_reauth_flow(hass: HomeAssistant, mock_setup_entry: AsyncMock) -> None:
    """Reauth asks for the current token, rejects a wrong one, then stores it."""
    entry = _token_entry(hass)

    result = await entry.start_reauth_flow(hass)
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    with patch(FLOW_CLIENT, return_value=_flow_client(reject=True)):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_API_TOKEN: "still-wrong"}
        )
    assert result["errors"] == {"base": "invalid_auth"}

    with patch(FLOW_CLIENT, return_value=_flow_client()):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_API_TOKEN: "new"}
        )
        await hass.async_block_till_done()
    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert entry.data[CONF_API_TOKEN] == "new"
    assert entry.data[CONF_HOST] == MOCK_CONFIG[CONF_HOST]


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (TimeoutError("timed out"), "timeout"),
        (UnraidConnectionError("refused"), "cannot_connect"),
        (RuntimeError("boom"), "unknown"),
    ],
)
async def test_reauth_flow_connection_errors(
    hass: HomeAssistant, error: Exception, expected: str
) -> None:
    """Reauth reports agent connection problems and keeps the old token."""
    entry = _token_entry(hass)
    result = await entry.start_reauth_flow(hass)

    with patch(FLOW_CLIENT, return_value=_flow_client(error=error)):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_API_TOKEN: "new"}
        )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"
    assert result["errors"] == {"base": expected}
    assert entry.data[CONF_API_TOKEN] == "old"


async def test_reconfigure_flow_invalid_token(hass: HomeAssistant) -> None:
    """Reconfigure reports a rejected token and keeps the old one."""
    entry = _token_entry(hass)
    result = await entry.start_reconfigure_flow(hass)

    with patch(FLOW_CLIENT, return_value=_flow_client(reject=True)):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {**MOCK_CONFIG, CONF_API_TOKEN: "wrong"}
        )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "reconfigure"
    assert result["errors"] == {"base": "invalid_auth"}
    assert entry.data[CONF_API_TOKEN] == "old"


@pytest.mark.usefixtures("mock_unraid_websocket_client_class")
async def test_rejected_token_at_startup_starts_reauth(
    hass: HomeAssistant, mock_async_unraid_client: MagicMock
) -> None:
    """If the agent rejects the token, setup fails with a reauth prompt."""
    mock_async_unraid_client.get_system_info.side_effect = UnraidAuthenticationError(
        "Unauthorized", status_code=401
    )
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={**MOCK_CONFIG, CONF_API_TOKEN: "revoked"},
        options=MOCK_OPTIONS,
    )
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.SETUP_ERROR
    flows = hass.config_entries.flow.async_progress_by_handler(DOMAIN)
    assert any(f["context"]["source"] == config_entries.SOURCE_REAUTH for f in flows)


async def test_health_check_401_at_startup_starts_reauth(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """A 401 from the startup health check starts reauth instead of retrying."""
    aioclient_mock.get(f"{BASE}/health", status=401, json={"error": "Unauthorized"})
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={**MOCK_CONFIG, CONF_HOST: "192.0.2.10", CONF_API_TOKEN: "revoked"},
        options=MOCK_OPTIONS,
    )
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.SETUP_ERROR
    flows = hass.config_entries.flow.async_progress_by_handler(DOMAIN)
    assert any(f["context"]["source"] == config_entries.SOURCE_REAUTH for f in flows)
