"""Mobile-width pins for every QA surface (issue #314).

Before this, three near-identical assertions each checked one page at one
width:

  * ``test_pipeline_table_no_mobile_overflow``  (/index.html)
  * ``test_mobile_no_horizontal_overflow``      (/explorer/)
  * ``test_workbench_pages_fit_mobile_width``   (workbench detail/files/terminal)

That fragmentation is why #309 shipped: the two pages with pins were clean,
and nobody added the third. Now one table covers every surface at a width
sweep, and adding a page is one line in ``overflow.PAGES``.

Writing the sweep immediately found three more overflowing pages, unseen by
any existing pin:
  * /boardroom/competitive.html  — 99px at 320px, 44px at 375px
  * /boardroom/status.html       — 32px at 320px
  * /spike/index.html            — 10px at 320px
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from qa_frontend.harness import PageSession, serve_static  # noqa: E402
from qa_frontend.overflow import (  # noqa: E402
    PAGES, WIDTHS, assert_no_overflow, format_offenders, measure,
)

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


@pytest.mark.parametrize("route", PAGES)
def test_surface_fits_every_width(server, session, route):
    """Each surface must fit the full width sweep, not just one mobile point.

    The workbench ``.panel`` breakpoint is 900px, so the 376–899 band was
    previously unswept; 320px (iPhone SE) was unasserted entirely.
    """
    page = session.new_page()
    failures = []
    for width in WIDTHS:
        page.set_viewport_size({"width": width, "height": 800})
        page.goto(server.url + route, wait_until="networkidle")
        page.wait_for_timeout(200)
        result = measure(page)
        if result["overflow"] > 0:
            failures.append(
                "%dpx by %dpx\n%s" % (width, result["overflow"], format_offenders(result))
            )
    page.close()
    assert not failures, "%s overflows:\n" % route + "\n".join(failures)


def test_pages_registry_covers_every_served_page(server):
    """The registry must not drift behind the site: every served HTML page
    should be in PAGES, or a new surface silently ships unpinned."""
    import glob

    def canonical(rel):
        # Index pages are addressed by their directory form (/a/), others by
        # their full path (/a/b.html).
        if rel.endswith("/index.html"):
            return rel[: -len("index.html")]
        if rel == "index.html":
            return "/"
        return rel

    missing = []
    for path in glob.glob(os.path.join(DOCS, "**", "*.html"), recursive=True):
        rel = "/" + os.path.relpath(path, DOCS).replace(os.sep, "/")
        if canonical(rel) not in PAGES:
            missing.append(canonical(rel))
    missing = sorted(set(missing))
    assert not missing, (
        "served page(s) missing from overflow.PAGES — add them so they get a "
        "width pin:\n  " + "\n  ".join(missing)
    )


def test_no_new_surface_has_zero_overflow_silently(server, session):
    """Sanity: the sweep actually measures something (a page that fails to
    load would report 0 and pass vacuously)."""
    page = session.new_page()
    page.set_viewport_size({"width": 375, "height": 800})
    page.goto(server.url + "/index.html", wait_until="networkidle")
    assert page.evaluate("document.body.scrollWidth") > 0
    assert page.locator("body *").count() > 10
    page.close()


def test_offender_reporting_names_the_cause(server, session):
    """When a page does overflow, the helper must name the element — the #309
    diagnosis had to enumerate offenders by hand."""
    page = session.new_page()
    page.set_viewport_size({"width": 320, "height": 800})
    page.goto(server.url + "/index.html", wait_until="networkidle")
    # Inject a deliberately oversized element and confirm it is reported.
    page.evaluate("""() => {
      const d = document.createElement('div');
      d.id = 'too-wide';
      d.style.width = '4000px';
      d.textContent = 'x';
      document.body.appendChild(d);
    }""")
    result = measure(page)
    assert result["overflow"] > 0, "injected overflow not detected"
    assert any(o["tag"] == "div" for o in result["offenders"]), result["offenders"]
    assert "too-wide" in format_offenders(result), format_offenders(result)
    page.close()


def test_clipped_elements_are_not_blamed(server, session):
    """An element inside a scroll container cannot widen the page, so it must
    not appear as an offender (the false lead #314's own diagnosis hit)."""
    page = session.new_page()
    page.set_viewport_size({"width": 320, "height": 800})
    page.goto(server.url + "/boardroom/competitive.html", wait_until="networkidle")
    page.evaluate("""() => {
      // Make the page overflow with an unrelated element, while a wide
      // element sits safely inside the table's scroll container.
      const d = document.createElement('div');
      d.style.width = '4000px';
      d.textContent = 'x';
      document.body.appendChild(d);
    }""")
    result = measure(page)
    blamed = format_offenders(result)
    assert result["overflow"] > 0
    assert "thead" not in blamed and "tbody" not in blamed, (
        "blamed a table part that is clipped by .table-scroll:\n" + blamed
    )
    page.close()