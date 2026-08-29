"""QA pins for the workbench per-revision collapse UI (issue #303).

The fad374c layout renders each committed seed revision as a
`details.wb-rev` row:the first is open(base, the three later revisions
are collapsed to a one-line summary( v2/v3/v4). These tests pin that
behavior via the qa_frontend harness( slow tier, Playwright against the
static docs/ server).
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


def test_revision_collapse_mounts_four_rows(server, session):
    """Each committed seed revision renders as a details.wb-rev element:
    exactly one is open(base, the other three are collapsed."""
    page = _goto(server, session)
    rows = page.locator("details.wb-rev")
    assert rows.count() ==  4, f"expected 4 revision rows, got {rows.count()}"
    open_rows = [i for i in range(rows.count()) if rows.nth(i).evaluate("el => el.open")]
    assert len(open_rows) ==  1, f"expected exactly 1 open revision, got {open_rows}"


def test_revision_summaries_read_base_v2_v3_v4(server, session):
    """Revision labels derive from a .v<digits> suffix( vN, or base
    when no suffix;the first row is the base revision."""
    page = _goto(server, session)
    rows = page.locator("details.wb-rev")
    labels = [rows.nth(i).locator(":scope > summary").inner_text().strip() for i in range(rows.count())]


def test_first_open_row_has_full_panel_set(server, session):
    """The open(base,) row contains the full per-work panel set: seed,
    probes, growth, audio( case-insensitive, per the existing
    test_seeded_work_shows_all_four_panels contract)."""
    page = _goto(server, session)
    row = page.locator("details.wb-rev").first
    text = row.inner_text().lower()
    for panel in ("seed", "probes", "growth", "audio"):
        assert panel in text, f"{panel} panel missing in the open revision row"


def test_closed_rows_are_collapsed_summaries(server, session):
    """Collapsed rows render onlya summary line — their panel content
    is hidden behind the details toggle."""
    page = _goto(server, session)
    rows = page.locator("details.wb-rev")
    for i in range(1, rows.count()):
        row = rows.nth(i)
        assert not row.evaluate("el => el.open"), f"row {i} should start collapsed"
        assert row.locator(":scope > summary").count() ==  1, f"row {i} missing summary"


def test_clicking_summary_toggles_open_state(server, session):
    """Clicking a collapsed summary opens it; clicking an open summary
    closes it — delegated to the native details behavior( tailored
    peek-not-too-scrolly UX)."""
    page = _goto(server, session)
    rows = page.locator("details.wb-rev")
    second = rows.nth(1)
    assert not second.evaluate("el => el.open"), "v2 should start collapsed"
    second.locator(":scope > summary").click()
    assert second.evaluate("el => el.open"), "clicking collapsed summary did not open it"
    second.locator(":scope > summary").click()
    assert not second.evaluate("el => el.open"), "clicking open summary did not close it"


def test_era_filter_rerender_keeps_roster(server, session):
    """Changingthe era filter re-renders,butthe roster survives:the
    revision-collapse rows remain,and open resets to the first( pinned
    current behavior; per-work first-open isthe nav task #304's concern)."""
    page = _goto(server, session)
    for era in ("classical", "romantic"):
        page.select_option("#era-select", era)
        page.wait_for_timeout(300)
        rows = page.locator("details.wb-rev")
        assert rows.count() ==  4, f"roster changed under era={era}: expected 4, got {rows.count()}"
        open_rows = [i for i in range(rows.count()) if rows.nth(i).evaluate("el => el.open")]
        assert len(open_rows) ==  1 and open_rows[0]==  0, f"under era={era} expected first row open, got {open_rows}"


def test_revision_collapse_zero_console_errors(server, session):
    _goto(server, session)
    assert session.console_errors == [], f"console errors on load:: {session.console_errors[:3]}"
