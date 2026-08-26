"""B3 status dashboard (issue #265; spec
tests/open_20260825-120000_b3-status-dashboard.md).

Phase lines match pipeline.md's gate statements, live counts come from
the generated stats.json (never hardcoded HTML), blockers carry their
reasons, the frontier call-out is present, and the page degrades
gracefully without the stats file.
"""

import json
import os
import re
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from qa_frontend.harness import PageSession, serve_static  # noqa: E402

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DOCS = os.path.join(REPO, "docs")
PAGE = os.path.join(DOCS, "boardroom", "status.html")
STATS = os.path.join(DOCS, "boardroom", "data", "stats.json")


@pytest.fixture(scope="module")
def server():
    with serve_static(DOCS) as s:
        yield s


@pytest.fixture(scope="module")
def page(server):
    with PageSession() as ps:
        p = ps.new_page()
        p.goto(server.url + "/boardroom/status.html", wait_until="networkidle")
        yield p, ps


def test_phase_lines_match_pipeline(page):
    """Six phase rows with status words consistent with pipeline.md's
    phase-gate statements (0–3 done, 4 the frontier, 5 deferred)."""
    p, _ = page
    rows = p.locator("#phases tr")
    assert rows.count() == 7, f"expected header + 6 phase rows, got {rows.count()}"
    statuses = [rows.nth(i).locator("td").nth(2).inner_text().lower() for i in range(1, 7)]
    for i, s in enumerate(statuses[:4]):
        assert "done" in s, f"phase {i} not marked done: {s!r}"
    assert "progress" in statuses[4] or "frontier" in statuses[4]
    assert "deferred" in statuses[5]


def test_counts_come_from_stats_json_not_hardcoded(page):
    """The page's rendered counts equal the generated stats.json — an HTML
    count that disagrees with the data file fails (the no-hardcoding pin)."""
    stats = json.load(open(STATS))
    p, _ = page
    p.wait_for_selector("#stats ul", timeout=5000)
    text = p.locator("#stats").inner_text()
    for key in ("suites", "tests_fast_tier", "corpus_works"):
        assert str(stats[key]) in text, f"page count for {key} != stats.json ({stats[key]})"
    # and the page's static HTML must not carry digits-only count claims
    html = open(PAGE).read()
    static = html.split('<div id="stats">')[0]
    assert not re.search(r">\s*\d{2,}\s+(test|suite|work)s?\b", static), (
        "status.html hardcodes a count outside the stats div"
    )


def test_blockers_listed_with_reasons(page):
    p, _ = page
    text = p.locator("body").text_content()
    assert "#211" in text and "event" in text.lower()
    assert "#224" in text and "paused" in text.lower()


def test_frontier_callout_present(page):
    p, _ = page
    frontier = p.locator("#frontier").inner_text().lower()
    assert "founder" in frontier and "ear" in frontier


def test_graceful_degradation_without_stats(server, page):
    """Stats fetch 404s → the regenerate note shows, no crash, no console
    errors beyond the (expected) 404."""
    _, ps = page  # module session — nesting sync_playwright is illegal
    p = ps.new_page()
    errors = []
    p.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    p.route("**/boardroom/data/stats.json", lambda route: route.abort())
    p.goto(server.url + "/boardroom/status.html", wait_until="networkidle")
    note = p.locator("#stats").inner_text()
    assert "regenerate" in note.lower()
    real = [e for e in errors if "404" not in e and "Failed to load resource" not in e]
    assert real == [], real[:2]


def test_status_page_zero_console_errors(server, page):
    """Zero console errors on the happy path. Scoped to this test's own
    page: the shared session also collects the degradation test's
    intentionally-aborted fetch."""
    _, ps = page
    p = ps.new_page()
    errors = []
    p.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    p.goto(server.url + "/boardroom/status.html", wait_until="networkidle")
    assert errors == [], errors[:2]
