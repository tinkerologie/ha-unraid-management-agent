#!/usr/bin/env python3
# script/ha_next/import_check.py: Probe all integration imports for deprecations
"""Import every integration module in an isolated Home Assistant interpreter."""

from __future__ import annotations

import importlib
import logging
import pkgutil
import re
import sys
import traceback
import warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = "custom_components.unraid_management_agent"
PACKAGE_DIR = ROOT / "custom_components" / "unraid_management_agent"
DEPRECATIONS = (DeprecationWarning, PendingDeprecationWarning)
# Keep these patterns aligned with tests/conftest.py.
DEPRECATION_REPORT_PATTERNS = (
    re.compile(r"Detected that custom integration 'unraid_management_agent'"),
    re.compile(r"The deprecated .+ was used from unraid_management_agent\b"),
    re.compile(
        r"custom_components\.unraid_management_agent(?:\.\w+)*::[\w.]+ "
        r"provides the deprecated .+, this will stop working in Home Assistant"
    ),
)


class ReportCollector(logging.Handler):
    """Collect log messages that report deprecated use by the integration."""

    def __init__(self) -> None:
        """Collect from DEBUG upwards; the logger levels decide the rest."""
        super().__init__()
        self.reports: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        """Keep the message when it matches one of the report formats."""
        message = record.getMessage()
        if any(p.search(message) for p in DEPRECATION_REPORT_PATTERNS):
            self.reports.append(f"{record.name}: {message}")


def module_names() -> list[str]:
    """Return the integration package and every module below it."""
    modules = pkgutil.walk_packages([str(PACKAGE_DIR)], prefix=f"{PACKAGE}.")
    return [PACKAGE, *sorted(info.name for info in modules)]


def is_own_warning(message: warnings.WarningMessage) -> bool:
    """Return whether a deprecation warning was raised from the integration."""
    if not issubclass(message.category, DEPRECATIONS):
        return False
    return Path(message.filename).resolve().is_relative_to(PACKAGE_DIR)


def import_check() -> int:
    """Import every module; print findings and return the exit status."""
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    collector = ReportCollector()
    root_logger = logging.getLogger()
    root_logger.addHandler(collector)
    failures: list[str] = []
    imported = 0
    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            try:
                names = module_names()
            except Exception:
                failures.append(f"Module discovery failed:\n{traceback.format_exc()}")
                names = [PACKAGE]
            for name in names:
                try:
                    module = importlib.import_module(name)
                    if not module.__file__ or not Path(
                        module.__file__
                    ).resolve().is_relative_to(PACKAGE_DIR):
                        raise ImportError(
                            f"{name} was loaded from outside the checkout: {module.__file__}"
                        )
                except Exception:
                    failures.append(f"import {name} failed:\n{traceback.format_exc()}")
                else:
                    imported += 1
    finally:
        root_logger.removeHandler(collector)

    ignored = 0
    for message in caught:
        if is_own_warning(message):
            failures.append(
                f"{message.category.__name__}: {message.message} "
                f"({message.filename}:{message.lineno})"
            )
        elif issubclass(message.category, DEPRECATIONS):
            ignored += 1
            print(
                f"Information: {message.category.__name__}: {message.message} ({message.filename}:{message.lineno})"
            )
    failures.extend(f"Home Assistant report: {r}" for r in collector.reports)

    from homeassistant.const import __version__ as ha_version

    print(f"## Home Assistant {ha_version}: imported {imported} modules of {PACKAGE}")
    if ignored:
        print(f"Ignored {ignored} deprecation warning(s) raised outside {PACKAGE}")
    if failures:
        print(f"{len(failures)} problem(s):")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("No import errors or deprecated use found")
    return 0


if __name__ == "__main__":
    sys.exit(import_check())
