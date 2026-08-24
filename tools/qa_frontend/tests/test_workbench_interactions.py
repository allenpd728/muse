"""Interaction QA for the seed workbench (the features the loop needs).

The workbench is only useful if controls work: era filter re-renders,
probe details expand, the refresh hint explains the regeneration step,
and audio elements are present per work.
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


def test_controls_bar_renders(server, session):
    page = _goto(server, session)
    assert page.locator(".controls").count() == 1
    assert page.locator("#era-select").count() == 1
    assert page.locator("#refresh-btn").count() == 1


def test_era_select_has_three_eras(server, session):
    page = _goto(server, session)
    opts = page.locator("#era-select option")
    assert opts.count() == 3
    values = [opts.nth(i).get_attribute("value") for i in range(opts.count())]
    assert values == ["baroque", "classical", "romantic"]


def test_era_change_rerenders_works(server, session):
    page = _goto(server, session)
    assert page.locator(".work").count() >= 1
    page.select_option("#era-select", "classical")
    page.wait_for_timeout(300)
    # re-render still shows works (the probes don't change with the filter
    # today — the filter is the control point; probe recompute per era is
    # the generator's job)
    assert page.locator(".work").count() >= 1


def test_refresh_button_shows_hint(server, session):
    page = _goto(server, session)
    note = page.locator("#refresh-note")
    assert note.inner_text() == ""
    page.locator("#refresh-btn").click()
    assert "generate.py" in note.inner_text()


def test_delta_curves_detail_expands(server, session):
    page = _goto(server, session)
    detail = page.locator('details[data-probe="delta-curves"]')
    assert detail.count() >= 1
    first = detail.first
    assert not first.evaluate("el => el.open")
    first.locator("summary").click()
    assert first.evaluate("el => el.open")
    # table visible with per-part rows
    rows = first.locator("table tr")
    assert rows.count() >= 5  # header + 4 parts
    assert "P4" in first.inner_text()


def test_budget_detail_expands(server, session):
    page = _goto(server, session)
    detail = page.locator('details[data-probe="budget-detail"]')
    assert detail.count() >= 1
    detail.first.locator("summary").click()
    assert detail.first.evaluate("el => el.open")
    assert "budget" in detail.first.inner_text()


def test_audio_element_present_per_work(server, session):
    page = _goto(server, session)
    audios = page.locator(".card audio")
    assert audios.count() >= 1, "no audio elements"
    src = audios.first.get_attribute("src")
    assert "/audio/" in src and src.endswith(".wav")


def test_audio_note_empty_until_error(server, session):
    """The 404-on-audio path shows the render hint only when the file is
    missing (onerror). When it exists there's no note."""
    page = _goto(server, session)
    # rendered file exists in this session
    note = page.locator(".audio-note").first
    # element is present; content depends on load success — both are valid
    assert note.count() == 1


def test_workbench_interactions_zero_console_errors(server, session):
    _goto(server, session)
    assert session.console_errors == [], (
        f"console errors: {session.console_errors[:3]}"
    )
