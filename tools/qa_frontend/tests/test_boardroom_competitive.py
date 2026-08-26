"""B4 competitive/moat memo (issue #266; spec
tests/open_20260825-120000_b4-competitive-memo.md).

Tool table rows, the pinned load-bearing claim, legal section, risk
register, source link, zero console errors.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from qa_frontend.harness import PageSession, serve_static  # noqa: E402

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DOCS = os.path.join(REPO, "docs")

TOOLS = ["Ableton Live 12", "Logic Pro", "FL Studio", "Pro Tools",
         "Cubase", "Studio One", "BandLab", "Suno Studio"]
RESEARCH = ["Basis Mixer", "VirtuosoNet", "S2A", "Midi-LLM"]
RISKS = ["walled garden", "patent", "niche"]


@pytest.fixture(scope="module")
def server():
    with serve_static(DOCS) as s:
        yield s


@pytest.fixture(scope="module")
def page(server):
    with PageSession() as ps:
        p = ps.new_page()
        p.goto(server.url + "/boardroom/competitive.html", wait_until="networkidle")
        yield p, ps


def test_tool_table_rows(page):
    p, _ = page
    text = p.locator("#tools").text_content()
    for t in TOOLS:
        assert t in text, f"tool table lost {t}"
    for r in RESEARCH:
        assert r in text, f"research line lost {r}"


def test_load_bearing_claim_pinned(page):
    """The memo's claim sentence must survive edits — a test fails if the
    claim is silently softened."""
    p, _ = page
    text = p.locator("body").text_content().lower()
    assert "score-aware ai interpretation ships nowhere" in text


def test_legal_section_present(page):
    p, _ = page
    text = p.locator("body").text_content().lower()
    assert "licensed" in text and "settlement" in text or "post-settlement" in text
    assert "copyrightable" in text  # the schema-as-legal-asset point


def test_risk_register_named(page):
    p, _ = page
    text = p.locator("body").text_content().lower()
    for r in RISKS:
        assert r in text, f"risk register lost {r}"
    for name in ("endel", "lifescore", "reactional"):
        assert name in text, f"patent FTO row lost {name}"


def test_prior_art_link(page):
    p, _ = page
    hrefs = p.locator("a").evaluate_all("els => els.map(e => e.getAttribute('href'))")
    assert any("PRIOR_ART_REVIEW.md" in (h or "") for h in hrefs), hrefs


def test_competitive_zero_console_errors(page):
    p, ps = page
    p.reload(wait_until="networkidle")
    errors = [e for e in ps.console_errors]
    assert errors == [], errors[:2]
