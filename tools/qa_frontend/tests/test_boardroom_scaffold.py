"""Boardroom scaffold (issue #263; spec
tests/open_20260825-120000_b1-boardroom-scaffold.md).

The B1 deliverable is static markup, so coverage here is source-scan tier:
pages exist with the right structure, the master index links the section,
read-only + D20 compliance asserted on page source. Playwright DOM tests
(HTTP 200, console errors) belong to the content tasks B2–B5, which land
real page behavior.
"""

import os
import re

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DOCS = os.path.join(REPO, "docs")
BOARDROOM = os.path.join(DOCS, "boardroom")
PAGES = ["index.html", "deck.html", "status.html", "competitive.html",
         "appendix.html", "asks.html"]


def _read(name):
    with open(os.path.join(BOARDROOM, name)) as fh:
        return fh.read()


class TestPagesExist:
    def test_all_pages_present(self):
        for name in PAGES:
            path = os.path.join(BOARDROOM, name)
            assert os.path.exists(path), f"missing boardroom/{name}"
            assert "<!doctype html>" in open(path).read().lower()

    def test_landing_links_all_pages(self):
        landing = _read("index.html")
        for name in PAGES[1:]:
            assert f'href="{name}"' in landing, f"landing page missing link to {name}"

    def test_pages_share_site_chrome(self):
        # the dark QA design language + cross-nav to the other surfaces
        for name in PAGES:
            text = _read(name)
            assert "#0d1117" in text, f"{name} lost the site background"
            assert 'href="../index.html"' in text, f"{name} lost the master-index link"
            assert 'href="../workbench/detail.html"' in text, f"{name} lost the workbench link"


class TestMasterIndexLink:
    def test_boardroom_linked(self):
        index = open(os.path.join(DOCS, "index.html")).read()
        assert 'href="boardroom/"' in index
        assert "/boardroom/" in index


class TestReadOnly:
    def test_no_forms_or_mutations(self):
        for name in PAGES:
            text = _read(name)
            assert "<form" not in text.lower(), f"{name} carries a form"
            assert not re.search(r'fetch\([^)]*,\s*\{[^}]*method:\s*["\'](?:POST|PUT|DELETE)',
                                 text), f"{name} carries a mutating fetch"


class TestD20Compliance:
    """The presentation surface must not leak mockup content."""

    def test_no_mockup_artifacts(self):
        for name in PAGES:
            text = _read(name)
            assert ".mockup.json" not in text, f"{name} links a mockup artifact"
            assert '"tempo_map"' not in text, f"{name} embeds mockup data"
            assert "onset_offset_ms" not in text, f"{name} embeds per-note devices"
