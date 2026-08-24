"""W-B7 readonly file viewer: tree navigation + safe <pre> render."""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from qa_frontend.harness import PageSession, serve_static  # noqa: E402

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DOCS = os.path.join(REPO, "docs")


@pytest.fixture(scope="module")
def site():
    with serve_static(DOCS) as srv:
        yield srv


def page(url):
    sess = PageSession()
    pg = sess.new_page()
    pg.goto(url)
    return sess, pg


def test_tree_renders_listing(site):
    sess, pg = page(f"{site.url}/index.html")
    uls = pg.evaluate("document.querySelectorAll('ul').length")
    sess.close()
    assert uls > 0


def test_click_renders_safe(site):
    sess, pg = page(f"{site.url}/workbench/files.html")
    # wait for listing fetch+render
    pg.wait_for_selector("ul")
    pg.evaluate("document.querySelectorAll('li .file')[0].click()")
    # async view; wait for the pre to render
    pg.wait_for_selector("main pre")
    text = pg.evaluate("document.querySelectorAll('main pre')[0].textContent")
    sess.close()
    assert "DOCTYPE html" in text or "Muse seed" in text
