"""Workbench growth panel QA (issue #204): trait trajectory rendering."""

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


def test_growth_panel_renders(server, session):
    page = _goto(server, session)
    card = page.locator(".card", has_text="Growth").first
    assert card.count() == 1, "growth panel missing"
    assert "V1" in card.inner_text().upper()


def test_growth_traits_have_verdicts(server, session):
    page = _goto(server, session)
    card = page.locator(".card", has_text="Growth").first
    text = card.inner_text().lower()
    for trait in ("velocity_pstdev", "rubato_pstdev_ms", "budget_position", "tempo_curve_shape"):
        assert trait in text, f"{trait} missing from growth panel"
    # growing verdicts present (v1→v2 fixture is deliberately growing)
    assert "growing" in text


def test_growth_delta_values_shown(server, session):
    page = _goto(server, session)
    card = page.locator(".card", has_text="Growth").first
    # numeric deltas render with a sign
    assert "+8.5" in card.inner_text() or "+12" in card.inner_text()


def test_growth_panel_zero_console_errors(server, session):
    _goto(server, session)
    assert session.console_errors == [], (
        f"console errors: {session.console_errors[:3]}"
    )
