#!/usr/bin/env python3
# script/ha_next/resolve_versions.py: Resolve HA Next and its matching test harness
"""Select the newest published Home Assistant, including betas, without fallback."""

from __future__ import annotations

import json
import os
import sys
import urllib.request
from pathlib import Path
from typing import Any

from packaging.requirements import Requirement
from packaging.version import InvalidVersion, Version

PYPI = "https://pypi.org/pypi"
HARNESS = "pytest-homeassistant"


def fetch_json(project: str, version: str = "") -> dict[str, Any]:
    """Read metadata from a fixed HTTPS PyPI endpoint."""
    suffix = f"/{version}" if version else ""
    request = urllib.request.Request(  # noqa: S310 - fixed HTTPS PyPI endpoint
        f"{PYPI}/{project}{suffix}/json",
        headers={"User-Agent": "ha-unraid-management-agent-ha-next"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310
        return json.load(response)


def published_versions(project: str) -> list[Version]:
    """Return non-development, non-yanked releases in descending PEP 440 order."""
    versions = []
    for name, files in fetch_json(project)["releases"].items():
        try:
            version = Version(name)
        except InvalidVersion:
            continue
        if not version.is_devrelease and any(not file.get("yanked") for file in files):
            versions.append(version)
    return sorted(versions, reverse=True)


def matching_harness(target: Version) -> str:
    """Return the newest harness with an exact pin to the selected HA version."""
    for version in published_versions(HARNESS)[:40]:
        requirements = (
            fetch_json(HARNESS, str(version))["info"].get("requires_dist") or []
        )
        for value in requirements:
            requirement = Requirement(value)
            if requirement.name != "homeassistant" or requirement.marker is not None:
                continue
            pins = [
                item
                for item in requirement.specifier
                if item.operator == "==" and "*" not in item.version
            ]
            if len(pins) != 1:
                continue
            pin = Version(pins[0].version)
            if pin == target:
                return str(version)
            if pin < target:
                return ""
    return ""


def main() -> int:
    """Write the selected versions to the Actions output file and stdout."""
    try:
        versions = published_versions("homeassistant")
        if not versions:
            message = "PyPI has no usable Home Assistant releases"
            raise ValueError(message)
        version = versions[0]
        outputs = f"ha_version={version}\nharness_version={matching_harness(version)}\n"
        if output := os.environ.get("GITHUB_OUTPUT"):
            with Path(output).open("a", encoding="utf-8") as stream:
                stream.write(outputs)
        print(outputs, end="")
    except (OSError, ValueError, KeyError) as err:
        print(f"Cannot resolve HA Next versions: {err}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
