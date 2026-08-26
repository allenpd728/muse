"""B2 board deck (issue #264; spec tests/open_20260825-120000_b2-deck.md).

Slide structure, required slides, demo links, thesis fidelity, D20, and
zero console errors for docs/boardroom/deck.html.
"""

import os
import re
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from qa_frontend.harness import PageSession, serve_static  # noqa: E402

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DOCS = os.path.join(REPO, "docs")
DECK = os.path.join(DOCS, "boardroom", "deck.html")

REQUIRED_SLIDES = [
    "thesis", "event", "five-second-wav", "architecture",
    "business-model", "demo", "competitive", "roadmap", "asks",
]


@pytest.fixture(scope="module")
def server():
    with serve_static(DOCS) as s:
        yield s


@pytest.fixture(scope="module")
def page(server):
    with PageSession() as ps:
        p = ps.new_page()
        p.goto(server.url + "/boardroom/deck.html", wait_until="networkidle")
        yield p, ps


def test_slide_deck_structure(page):
    """~10–16 slides, one <section class='slide'> each, keyboard navigation
    wired."""
    p, _ = page
    slides = p.locator("section.slide")
    count = slides.count()
    assert 8 <= count <= 18, f"deck has {count} slides — outside the intended band"
    # keyboard nav: ArrowRight advances the active slide
    assert slides.nth(0).evaluate("el => el.classList.contains('active')")
    p.keyboard.press("ArrowRight")
    assert slides.nth(1).evaluate("el => el.classList.contains('active')")
    p.keyboard.press("ArrowLeft")
    assert slides.nth(0).evaluate("el => el.classList.contains('active')")


def test_required_slides_present(page):
    p, _ = page
    ids = [p.locator("section.slide").nth(i).get_attribute("data-slide")
           for i in range(p.locator("section.slide").count())]
    for slug in REQUIRED_SLIDES:
        assert slug in ids, f"required slide {slug!r} missing (have {ids})"


def test_demo_slide_links_workbench_and_render(page):
    p, _ = page
    demo = p.locator('section.slide[data-slide="demo"]')
    hrefs = demo.locator("a").evaluate_all("els => els.map(e => e.getAttribute('href'))")
    assert any("workbench/detail.html" in h for h in hrefs), hrefs
    assert any("bwv227.1.llm-v2.wav" in h for h in hrefs), hrefs


def test_thesis_fidelity(page):
    """The vision phrases must survive — paraphrase drift is caught.
    text_content (not inner_text): non-active slides are display:none, so
    inner_text only sees the first."""
    p, _ = page
    text = p.locator("body").text_content()
    assert "event, not a render" in text
    for work in ("Bach", "Byrd", "Schubert", "Beethoven"):
        assert work in text, f"corpus ladder lost {work}"


def test_no_mockup_content_d20(page):
    """Source scan: no mockup artifact paths or session-file internals."""
    src = open(DECK).read()
    for banned in ("mockup.json", ".mockup", "session file", "tools/muse_generate/tests/fixtures"):
        assert banned not in src, f"D20: deck references {banned!r}"


def test_deck_zero_console_errors(page):
    p, ps = page
    p.reload(wait_until="networkidle")
    assert ps.console_errors == [], ps.console_errors[:2]
