"""Tier 2 DOM tests for the corpus explorer (issue #183).

The page executes for real in headless Chromium: work-list populates, row
click renders detail, images resolve, the failure fallback works, and zero
console errors are tolerated on load.
"""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from qa_frontend.harness import PageSession, serve_static  # noqa: E402

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DOCS = os.path.join(REPO, "docs")
EXPLORER = os.path.join(DOCS, "explorer")


@pytest.fixture(scope="module")
def server():
    with serve_static(DOCS) as s:
        yield s


@pytest.fixture(scope="module")
def session():
    with PageSession() as ps:
        yield ps


def _goto(server, session, path="/explorer/"):
    page = session.new_page()
    page.goto(server.url + path, wait_until="networkidle")
    return page


def test_work_list_populates(server, session):
    page = _goto(server, session)
    rows = page.locator(".work-row")
    assert rows.count() == 13, f"expected 13 work rows, got {rows.count()}"


def test_first_row_click_renders_detail(server, session):
    page = _goto(server, session)
    page.locator(".work-row").first.click()
    detail = page.locator(".detail")
    assert detail.count() == 1
    assert "Bach" in detail.inner_text()
    # stats grid has the pinned fields
    for label in ("parts", "notes", "dynamics", "hairpins", "packed"):
        assert label in detail.inner_text().lower()


def test_detail_includes_pattern_table(server, session):
    page = _goto(server, session)
    page.locator(".work-row").first.click()
    table = page.locator(".detail table")
    assert table.count() >= 1
    assert "exact repeats" in table.inner_text()


def test_piano_roll_image_resolves(server, session):
    page = _goto(server, session)
    page.locator(".work-row").first.click()
    img = page.locator(".detail img").first
    assert img.count() == 1
    width = img.evaluate("el => el.naturalWidth")
    assert width and width > 0, "piano-roll image failed to load"


def test_back_button_returns_to_list(server, session):
    page = _goto(server, session)
    page.locator(".work-row").first.click()
    assert page.locator(".detail").count() == 1
    page.locator(".back").click()
    assert page.locator(".detail").count() == 0
    assert page.locator(".work-row").count() == 13


def test_zero_console_errors_on_load(server, session):
    _goto(server, session)
    assert session.console_errors == [], (
        f"console errors on load: {session.console_errors[:3]}"
    )


def test_fetch_failure_shows_fallback(server, session):
    """Kill the JSON endpoint via a 404 and assert the error fallback
    renders instead of a blank page."""
    page = session.new_page()
    page.route("**/data/works.json", lambda route: route.abort())
    page.goto(server.url + "/explorer/", wait_until="networkidle")
    app = page.locator("#app")
    assert "failed to load" in app.inner_text().lower()


def test_data_endpoint_serves_valid_json(server):
    import urllib.request

    with urllib.request.urlopen(server.url + "/explorer/data/works.json") as r:
        data = json.load(r)
    assert len(data["works"]) == 13


def test_every_row_has_parts_and_notes(server, session):
    page = _goto(server, session)
    metas = page.locator(".work-row .meta")
    assert metas.count() == 13
    for i in range(metas.count()):
        text = metas.nth(i).inner_text()
        assert "parts" in text and "notes" in text


def test_schubert_row_shows_large_counts(server, session):
    """The Schubert row (24,772 notes) renders its formatted count."""
    page = _goto(server, session)
    rows = page.locator(".work-row")
    for i in range(rows.count()):
        text = rows.nth(i).inner_text()
        if "Death and the Maiden" in text:
            assert "24,772" in text
            return
    pytest.fail("Schubert row not found")
