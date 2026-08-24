"""Tier 2 viewport + a11y pins for the corpus explorer (issue #223).

The spec's unpinned gap: layout at mobile widths and keyboard navigation.
These pin the contract that exists today on /explorer/ — no horizontal
overflow at mobile width, content column capped at desktop width, lang
declared, images alted, and the back control keyboard-operable.

Known gap deliberately not pinned: .work-row divs are click-only (no
tabindex) — keyboard users can't open a work. That's a page-owner
decision (QA surface v0), recorded in the spec's disposition.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from qa_frontend.harness import PageSession, serve_static  # noqa: E402

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DOCS = os.path.join(REPO, "docs")

MOBILE = {"width": 375, "height": 667}
DESKTOP = {"width": 1280, "height": 800}


@pytest.fixture(scope="module")
def server():
    with serve_static(DOCS) as s:
        yield s


@pytest.fixture(scope="module")
def session():
    with PageSession() as ps:
        yield ps


def _goto(server, session, viewport):
    page = session.new_page()
    page.set_viewport_size(viewport)
    page.goto(server.url + "/explorer/", wait_until="networkidle")
    return page


def test_mobile_no_horizontal_overflow(server, session):
    page = _goto(server, session, MOBILE)
    overflow = page.evaluate(
        "document.documentElement.scrollWidth - window.innerWidth"
    )
    assert overflow <= 0, f"horizontal overflow at 375px: {overflow}px"


def test_mobile_list_populates_and_rows_tap(server, session):
    page = _goto(server, session, MOBILE)
    rows = page.locator(".work-row")
    assert rows.count() == 13
    rows.first.click()
    assert page.locator(".detail").count() == 1


def test_desktop_content_column_capped_and_centered(server, session):
    page = _goto(server, session, DESKTOP)
    box = page.locator("main").bounding_box()
    # border-box: 900px max-width + 2 × 1.25rem (20px) padding
    assert box["width"] <= 940, f"content column not capped: {box['width']}"
    assert box["x"] > 100, f"content column not centered: x={box['x']}"


def test_html_lang_declared(server, session):
    page = _goto(server, session, DESKTOP)
    assert page.locator("html").get_attribute("lang") == "en"


def test_piano_roll_image_has_alt(server, session):
    page = _goto(server, session, DESKTOP)
    page.locator(".work-row").first.click()
    img = page.locator(".detail img")
    assert img.count() == 1
    alt = img.get_attribute("alt")
    assert alt and "piano roll" in alt


def test_back_button_keyboard_operable(server, session):
    page = _goto(server, session, DESKTOP)
    page.locator(".work-row").first.click()
    back = page.locator("button.back")
    back.focus()
    assert page.evaluate("document.activeElement.className") == "back"
    page.keyboard.press("Enter")
    assert page.locator(".detail").count() == 0


def test_work_rows_keyboard_focusable_and_activatable(server, session):
    """#245: rows must be tabbable and Enter/Space must open the detail."""
    page = _goto(server, session, DESKTOP)
    row = page.locator(".work-row").first
    assert row.get_attribute("tabindex") == "0"
    assert row.get_attribute("role") == "button"
    row.focus()
    assert page.evaluate("document.activeElement.className") == "work-row"
    page.keyboard.press("Enter")
    assert page.locator(".detail").count() == 1
    # Space on the same pattern: back to list, re-activate with Space
    page.locator("button.back").click()
    page.locator(".work-row").first.focus()
    page.keyboard.press(" ")
    assert page.locator(".detail").count() == 1
