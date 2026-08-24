"""Tier 3 live deploy smoke (issue #184): the QA URL itself is under test.

Asserts the live dev-- deploy serves the explorer: page mounts,
data/works.json is valid with 13 works, a piano-roll PNG 200s, and a
headless pass finds zero console errors. Runs only when QA_LIVE=1 is set
(the CI's post-deploy job sets it; local runs skip by default — the live
site is not a unit-test dependency).
"""

import json
import os
import sys
import urllib.request

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from qa_frontend.harness import PageSession  # noqa: E402

LIVE_URL = "https://dev--muse-qa-58fd708e.netlify.app"

pytestmark = pytest.mark.skipif(
    os.environ.get("QA_LIVE") != "1",
    reason="live deploy smoke runs only with QA_LIVE=1",
)


@pytest.fixture(scope="module")
def session():
    with PageSession() as ps:
        yield ps


def test_explorer_page_200(session):
    page = session.new_page()
    resp = page.goto(LIVE_URL + "/explorer/", wait_until="networkidle")
    assert resp and resp.status == 200, f"/explorer/ returned {resp.status if resp else 'no response'}"


def test_works_json_live_valid():
    with urllib.request.urlopen(LIVE_URL + "/explorer/data/works.json", timeout=30) as r:
        data = json.load(r)
    assert len(data["works"]) == 13
    first = data["works"][0]
    for key in ("id", "title", "parts", "notes", "piano_roll"):
        assert key in first


def test_piano_roll_live_200():
    with urllib.request.urlopen(LIVE_URL + "/explorer/img/bach_bwv227.1.png", timeout=30) as r:
        assert r.status == 200
        assert int(r.headers.get("Content-Length", 0)) > 1000


def test_live_page_zero_console_errors(session):
    page = session.new_page()
    page.goto(LIVE_URL + "/explorer/", wait_until="networkidle")
    rows = page.locator(".work-row")
    assert rows.count() == 13, f"live page shows {rows.count()} rows"
    assert session.console_errors == [], (
        f"console errors on live page: {session.console_errors[:3]}"
    )


def test_live_page_interaction(session):
    """The live page clicks through to detail and back."""
    page = session.new_page()
    page.goto(LIVE_URL + "/explorer/", wait_until="networkidle")
    page.locator(".work-row").first.click()
    assert page.locator(".detail").count() == 1
    page.locator(".back").click()
    assert page.locator(".detail").count() == 0
