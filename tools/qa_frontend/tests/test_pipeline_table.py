"""Pipeline table on the master index page (issue #247; spec
tests/open_20260825-101500_pipeline-table-master-index.md).

The rendered shape of docs/index.html's pipeline section — seven stages
in fixed order, row shape (io cell, tool link, status class, assets), the
grow row's L1.1–L1.4 issue links, and zero console errors.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from qa_frontend.harness import PageSession, serve_static  # noqa: E402

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DOCS = os.path.join(REPO, "docs")

STAGES = ["package", "unzip / decode", "deterministic baseline",
          "grow", "validate", "render", "distill"]


@pytest.fixture(scope="module")
def server():
    with serve_static(DOCS) as s:
        yield s


@pytest.fixture(scope="module")
def page(server):
    with PageSession() as ps:
        p = ps.new_page()
        p.goto(server.url + "/index.html", wait_until="networkidle")
        yield (p, ps)


def test_seven_rows_in_fixed_order(server, page):
    p, _ = page
    rows = p.locator("#pipeline-table tbody tr")
    assert rows.count() == 7, f"expected 7 stages, got {rows.count()}"
    names = [rows.nth(i).locator("td").first.inner_text().strip() for i in range(7)]
    assert names == STAGES


def test_row_shape_complete(server, page):
    p, _ = page
    rows = p.locator("#pipeline-table tbody tr")
    for i in range(7):
        row = rows.nth(i)
        io = row.locator("td.io")
        assert "→" in io.inner_text(), f"{STAGES[i]}: io cell missing →"
        link = row.locator("td a").first
        assert link.count() >= 1, f"{STAGES[i]}: no tool/issue link"
        status = row.locator("td[class^='status'], td[class*=' status']")
        cls = status.get_attribute("class") or ""
        assert cls.startswith("status-"), f"{STAGES[i]}: status cell unclassed"
        cells = row.locator("td")
        assert cells.nth(4).inner_text().strip(), f"{STAGES[i]}: empty assets cell"


def test_grow_row_links_l1_loop_issues(server, page):
    p, _ = page
    grow = p.locator("#pipeline-table tbody tr").nth(3)
    status = grow.locator("td").nth(3)
    text = status.inner_text()
    assert "#206" in text and "#209" in text, "grow row lost the L1.1–L1.4 issue links"


def test_tool_links_point_at_repo_tree(server, page):
    p, _ = page
    links = p.locator("#pipeline-table tbody td a")
    hrefs = [links.nth(i).get_attribute("href") for i in range(links.count())]
    assert any("/tree/dev/tools/" in h for h in hrefs), (
        "no tool links — they must point at the owning tool dirs"
    )


def test_pipeline_table_clean_console(server, page):
    """Zero console errors with the section present (the Tier-2 bar)."""
    p, ps = page
    p.reload(wait_until="networkidle")
    p.locator("#pipeline-table").wait_for(timeout=5000, state="visible")
    assert ps.console_errors == [], ps.console_errors[:2]


def test_pipeline_table_no_mobile_overflow(server, page):
    """/index.html must fit 375px — the table wraps (io cells) and the
    section scrolls internally rather than overflowing the page (the
    nowrap regression shipped with #241, caught by hand)."""
    _, ps = page  # reuse the module session — nesting sync_playwright is illegal
    p = ps.new_page()
    p.set_viewport_size({"width": 375, "height": 812})
    p.goto(server.url + "/index.html", wait_until="networkidle")
    overflow = p.evaluate(
        "document.documentElement.scrollWidth - document.documentElement.clientWidth"
    )
    assert overflow <= 0, f"horizontal overflow at 375px: {overflow}px"
