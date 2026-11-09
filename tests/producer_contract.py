"""Offline transport and fixture access for producer contract tests."""

from __future__ import annotations

import asyncio
import json
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, cast
from unittest.mock import Mock, patch

import aiohttp
from aiohttp.helpers import TimerNoop
from multidict import CIMultiDict, CIMultiDictProxy
from yarl import URL

from custom_components.unraid_management_agent.api.client import UnraidClient

ROOT = Path(__file__).parent / "fixtures" / "producer_contract"
ORIGIN = "http://unraid.invalid:8043"


def cases(folder: str) -> dict:
    """Read one manifest indexed by case ID."""
    entries = json.loads((ROOT / folder / "manifest.json").read_bytes())["cases"]
    assert len({item["id"] for item in entries}) == len(entries)
    return {item["id"]: item for item in entries}


UPSTREAM = cases("upstream")
LEGACY = cases("legacy")


def fixture(case: str) -> bytes:
    """Return the exact captured bytes."""
    if case in UPSTREAM:
        return (ROOT / "upstream" / UPSTREAM[case]["fixture"]).read_bytes()
    return (ROOT / "legacy" / LEGACY[case]["fixture"]).read_bytes()


class FixtureSession:
    """Serve one exact request without a connector or network."""

    closed = False

    def __init__(self, case: dict, body: bytes) -> None:
        """Bind the single expected request and response bytes."""
        self.case = case
        self.body = body
        self.calls: list[tuple[str, URL, dict[str, str]]] = []

    @asynccontextmanager
    async def request(self, *, method, url, headers, params, **_: Any):
        """Return a byte-backed aiohttp response and reject unlisted requests."""
        request_url = URL(url).extend_query(params or {})
        self.calls.append((method, request_url, dict(headers)))
        assert (method, request_url) == (
            self.case["method"],
            URL(ORIGIN + self.case["path"]),
        )
        response_headers = CIMultiDictProxy(
            CIMultiDict({"Content-Type": "application/json"})
        )
        response = aiohttp.ClientResponse(
            method,
            request_url,
            writer=None,
            continue100=None,
            timer=TimerNoop(),
            request_info=aiohttp.RequestInfo(
                request_url, method, CIMultiDictProxy(CIMultiDict(headers)), request_url
            ),
            traces=[],
            loop=asyncio.get_running_loop(),
            session=Mock(),
            stream_writer=Mock(),
        )
        response.status = self.case["status"]
        # A real response reads this cache after receiving the transport bytes.
        # Only aiohttp's I/O setup is replaced.
        response._headers = response_headers
        response._body = self.body
        try:
            yield response
        finally:
            response.close()


async def request(case_id: str, method: str, *args: str, body: bytes | None = None):
    """Decode fixture bytes through the public vendored client method."""
    case = (UPSTREAM | LEGACY)[case_id]
    adapter = FixtureSession(case, fixture(case_id) if body is None else body)
    token = "fixture-token"  # noqa: S105 - synthetic offline credential
    client = UnraidClient(
        "unraid.invalid",
        session=cast("aiohttp.ClientSession", adapter),
        api_token=token,
    )
    try:
        with patch(
            "aiohttp.ClientSession", side_effect=AssertionError("Unexpected I/O")
        ):
            return await getattr(client, method)(*args)
    finally:
        assert adapter.calls == [
            (
                case["method"],
                URL(ORIGIN + case["path"]),
                {"Authorization": "Bearer fixture-token"},
            )
        ]


def assert_values(value, fields: dict) -> None:
    """Compare independently specified values at model, list and mapping paths."""
    for path, expected in fields.items():
        actual = value
        for name in path.split("."):
            if isinstance(actual, list):
                index = int(name)
                assert index < len(actual), path
                actual = actual[index]
            elif isinstance(actual, dict):
                actual = actual[name]
            else:
                actual = getattr(actual, name)
        assert actual == expected, path
