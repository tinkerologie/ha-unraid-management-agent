"""Integrity and coverage for the committed producer fixtures."""

import json
import re
from hashlib import sha256

from tests.producer_contract import LEGACY, ROOT, UPSTREAM, fixture
from tests.test_producer_contract_events import EVENTS
from tests.test_producer_contract_rest import ERRORS, REST


def test_corpus_is_pinned_and_each_case_is_accounted_for():
    """Require exact upstream bytes and an explicit consumer for each case."""
    pin = json.loads((ROOT / "pin.json").read_bytes())
    manifest = json.loads((ROOT / "upstream" / "manifest.json").read_bytes())
    assert re.fullmatch(r"[0-9a-f]{40}", pin["commit"])
    assert pin["schema_revision"] == manifest["schema_revision"]
    for folder, cases in (("upstream", UPSTREAM), ("legacy", LEGACY)):
        assert {path.name for path in (ROOT / folder).iterdir()} == {
            "manifest.json",
            *(case["fixture"] for case in cases.values()),
        }
    assert {
        path.name: sha256(path.read_bytes()).hexdigest()
        for path in (ROOT / "upstream").iterdir()
    } == pin["sha256"]
    for case in UPSTREAM.values():
        assert sha256(fixture(case["id"])).hexdigest() == case["sha256"]
    # The integration has no standalone capabilities client call. It receives
    # this exact capabilities payload inside the diagnostics self-test.
    assert json.loads(fixture("source-health"))["capabilities"] == json.loads(
        fixture("capabilities")
    )
    assert not (set(UPSTREAM) & set(LEGACY))
    assert set(UPSTREAM | LEGACY) == set(REST) | set(ERRORS) | set(EVENTS) | {
        "capabilities",
    }
