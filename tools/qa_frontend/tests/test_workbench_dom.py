"""Tier 2 DOM tests for the seed workbench (workbench UI QA).

The workbench page must actually render its seed + probe data — not just
exist as a file. These tests execute the page in headless Chromium against
a local static server and assert the probe panel shows real probe results.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from qa_frontend.harness import PageSession, serve_static  # noqa: E402

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DOCS = os.path.join(REPO, "docs")


@pytest.fixture(scope="module")
def server():
    with serve_static(DOCS) as s:
        yield s


@pytest.fixture(scope="module")
def session():
    with PageSession() as ps:
        yield ps


def _goto(server, session):
    page = session.new_page()
    page.goto(server.url + "/workbench/detail.html", wait_until="networkidle")
    return page


def test_workbench_page_loads(server, session):
    page = _goto(server, session)
    assert "seed workbench" in page.inner_text("body").lower()


def test_seed_panel_renders_seed_params(server, session):
    page = _goto(server, session)
    card = page.locator(".card", has_text="Seed").first
    assert card.count() == 1, "seed panel missing"
    text = card.inner_text()
    assert "tempo" in text and "min_bpm" in text


def test_probe_panel_shows_real_probes(server, session):
    """The probe panel must show actual probe results, not 'no probe artifact'."""
    page = _goto(server, session)
    probe_card = page.locator(".card", has_text="Probes").first
    assert probe_card.count() == 1, "probe panel missing"
    text = probe_card.inner_text()
    assert "no probe artifact" not in text.lower(), (
        f"probe panel shows the empty state: {text[:200]}"
    )
    # real probe rows present
    assert "assertion" in text.lower()
    assert "determinism" in text.lower()


def test_probe_panel_assertions_pass(server, session):
    page = _goto(server, session)
    rows = page.locator(".probe")
    assert rows.count() >= 2, f"expected >=2 probe rows, got {rows.count()}"
    # at least one assertion row shows pass
    texts = [rows.nth(i).inner_text() for i in range(rows.count())]
    assert any("pass" in t for t in texts), texts


def test_probe_panel_budget_row_present(server, session):
    page = _goto(server, session)
    text = page.locator(".card", has_text="Probes").first.inner_text()
    assert "budget" in text.lower()
    assert ("inside budget" in text) or ("outside" in text)


def test_probe_panel_determinism_stable(server, session):
    page = _goto(server, session)
    text = page.locator(".card", has_text="Probes").first.inner_text()
    assert "stable" in text.lower() or "unstable" in text.lower()


def test_workbench_zero_console_errors(server, session):
    _goto(server, session)
    assert session.console_errors == [], (
        f"console errors on workbench: {session.console_errors[:3]}"
    )


def test_workbench_missing_probes_shows_fallback(server, session):
    """If probe JSON is absent, the page shows 'no probe artifact' (the
    failure mode the QA tests exist to catch — it must not be silent)."""
    page = session.new_page()
    page.route("**/data/seeds/*.probes.json", lambda route: route.abort())
    page.goto(server.url + "/workbench/detail.html", wait_until="networkidle")
    text = page.locator("body").inner_text()
    assert "no probe artifact" in text.lower() or "load error" in text.lower()


def test_seed_index_has_entries(server):
    import json as _json
    import urllib.request

    with urllib.request.urlopen(server.url + "/workbench/data/seeds/index.json") as r:
        idx = _json.load(r)
    assert len(idx["seeds"]) >= 1
    entry = idx["seeds"][0]
    assert "work_id" in entry and "probes" in entry
