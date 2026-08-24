"""Workbench DoD additions (issue #229): work-index/file-id pins, seeded
state semantics, and era-filter verdict behavior.

These grow test_workbench_dom.py / test_workbench_interactions.py per the
issue's Definition of done, against the design doc
(docs/design/seed-workbench.md + the W-B6/B7/B8 page structure as landed).
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


# --- Work index groups (DoD: file ids rendered; seeded state asserted) ---

def test_seeded_work_renders_heading_and_passing_tag(server, session):
    """Each committed seed gets a work group headed by its work_id, with a
    'passing' tag driven by the probe artifact's ok flag."""
    page = _goto(server, session)
    heading = page.locator(".work h2", has_text="bwv227.1")
    assert heading.count() == 1, "seeded work bwv227.1 missing from the index"
    tag = heading.locator(".tag")
    assert tag.inner_text() == "passing"
    assert "ok" in (tag.get_attribute("class") or "")


def test_seeded_work_shows_all_four_panels(server, session):
    """Seed + probes + growth + audio — the full per-work panel set the
    iteration loop reads. Case-insensitive: card headings render in CSS
    small-caps."""
    page = _goto(server, session)
    work = page.locator(".work", has_text="bwv227.1").first
    text = work.inner_text().lower()
    for panel in ("seed", "probes", "growth", "audio"):
        assert panel in text, f"{panel} panel missing for bwv227.1"


def test_works_json_data_contract(server):
    """The index data carries the file ids the page renders (data-level pin
    for the DOM assertions above)."""
    import json as _json
    import urllib.request

    with urllib.request.urlopen(server.url + "/workbench/data/works.json") as r:
        data = _json.load(r)
    assert isinstance(data["works"], list) and data["works"], "no works in index"
    for w in data["works"]:
        assert w["id"] and w["file"], f"work entry missing id/file: {w}"


# --- Era filter behavior (DoD: era filter changes probe verdicts) ---

def test_era_filter_verdicts_are_artifact_driven_today(server, session):
    """Truth pin: the era select re-renders, but probe verdicts come from
    the committed artifact (probes.json, computed at era=baroque by the
    generator) — the budget row is *identical* across eras today. The
    DoD's "era filter changes probe verdicts" requires page-side per-era
    budget recompute (data carries no per-era budgets yet); this test must
    flip to assert the flip when that lands."""
    page = _goto(server, session)
    row = page.locator(".probe", has_text="budget").first
    verdicts = []
    for era in ("baroque", "classical", "romantic"):
        page.select_option("#era-select", era)
        page.wait_for_timeout(300)
        verdicts.append((row.get_attribute("class"), row.inner_text()))
    assert len(set(verdicts)) == 1, (
        f"budget verdict now varies by era {verdicts} — the per-era recompute "
        f"landed; flip this pin to assert the flip"
    )


def test_era_filter_preserves_work_index(server, session):
    """Filtering re-renders verdicts, not the roster: the seeded work group
    survives every era selection."""
    page = _goto(server, session)
    for era in ("baroque", "classical", "romantic"):
        page.select_option("#era-select", era)
        page.wait_for_timeout(300)
        assert page.locator(".work h2", has_text="bwv227.1").count() == 1, (
            f"bwv227.1 disappeared under era={era}"
        )


# --- Files page (W-B7 surface, read-only explorer) ---

def test_files_page_renders_tree(server, session):
    """The read-only file explorer lists the repo tree — the W-B7 surface
    gets a mount check alongside the detail page's."""
    page = session.new_page()
    page.goto(server.url + "/workbench/files.html", wait_until="networkidle")
    body = page.inner_text("body").lower()
    assert "files" in body or "tree" in body or "seeds" in body


def test_terminal_page_mounts(server, session):
    """W-B8 terminal mode mounts its prompt surface."""
    page = session.new_page()
    page.goto(server.url + "/workbench/terminal.html", wait_until="networkidle")
    assert "terminal" in page.inner_text("body").lower()
