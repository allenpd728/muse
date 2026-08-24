"""W-B6 corpus-tree DOM tests: master index groups 5 works / 13 files."

The attached workbench folder is served via `docs/` so the tree path is
`/index.html` and detail pages live at `/workbench/detail.html`.
"""

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


def test_tree_groups_five_files(site):
    sess, pg = page(f"{site.url}/index.html")
    count = pg.evaluate("document.querySelectorAll('ul.files li a').length")
    sess.close()
    assert count == 13


def test_seed_pill_states(site):
    sess, pg = page(f"{site.url}/index.html")
    states = pg.evaluate("""
      [...document.querySelectorAll('ul.files li .seed-pill')].map(e => e.textContent)
    """)
    sess.close()
    assert len(states) == 13
    assert states.count('seeded') == 1
    assert states.count('unseeded') == 12


def test_links_to_detail_route(site):
    sess, pg = page(f"{site.url}/index.html")
    hrefs = pg.evaluate("""
      [...document.querySelectorAll('ul.files li a')].map(a => a.getAttribute('href'))
    """)
    sess.close()
    assert all(h.startswith('workbench/detail.html#') for h in hrefs)