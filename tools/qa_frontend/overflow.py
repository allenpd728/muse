"""Shared horizontal-overflow helper for the QA surfaces (issue #314).

Before this, three near-identical assertions each re-implemented the same
`scrollWidth - clientWidth` check on one page at one width. That is why #309
(workbench pages) survived: the two pages with pins were clean, and nobody
added the third pin. Consolidating makes a new surface one line.

The helper also reports *which elements* overflow. Diagnosing #309 meant
enumerating offending elements by hand; a bare number tells you nothing about
what to fix.
"""

from __future__ import annotations

# A width sweep, not a single mobile point. The workbench `.panel` breakpoint
# is 900px, so the 376–899 band was previously unswept; 320px (iPhone SE) was
# unasserted entirely.
WIDTHS = (320, 375, 768, 900, 1024, 1280)

# Every page the site serves. A new surface should be added here once; the
# registry test in test_mobile_widths.py fails if the site grows past it.
PAGES = (
    "/",
    "/index.html",
    "/explorer/",
    "/workbench/",
    "/workbench/detail.html",
    "/workbench/files.html",
    "/workbench/terminal.html",
    "/boardroom/",
    "/boardroom/deck.html",
    "/boardroom/status.html",
    "/boardroom/competitive.html",
    "/boardroom/appendix.html",
    "/boardroom/asks.html",
    "/spike/",
    "/spike/index.html",
)

OVERFLOW_JS = """() => {
  const doc = document.documentElement;
  const overflow = doc.scrollWidth - doc.clientWidth;
  if (overflow <= 0) return { overflow: 0, offenders: [] };
  const limit = doc.clientWidth;
  // An element inside a scroll container (overflow-x auto/scroll/hidden) is
  // clipped by it and cannot widen the page — reporting it sends you to the
  // wrong place. #314's first diagnosis hit exactly that false lead.
  const clipped = el => {
    for (let a = el.parentElement; a; a = a.parentElement) {
      const ox = getComputedStyle(a).overflowX;
      if (ox === 'auto' || ox === 'scroll' || ox === 'hidden') return true;
    }
    return false;
  };
  const offenders = [];
  for (const el of document.querySelectorAll('body *')) {
    const r = el.getBoundingClientRect();
    if (r.width === 0 && r.height === 0) continue;      // collapsed
    if (r.right <= limit + 1) continue;
    const style = getComputedStyle(el);
    if (style.position === 'fixed') continue;           // fixed overlays do not scroll the page
    const isScroller = style.overflowX === 'auto' || style.overflowX === 'scroll';
    if (clipped(el) && !isScroller) continue;
    offenders.push({
      tag: el.tagName.toLowerCase(),
      cls: (el.className && el.className.toString().slice(0, 60)) || '',
      id: el.id || '',
      right: Math.round(r.right),
      width: Math.round(r.width),
      scroller: isScroller,
    });
  }
  offenders.sort((a, b) => b.right - a.right);
  return { overflow, offenders: offenders.slice(0, 6) };
}"""


def measure(page):
    """Return {'overflow': int, 'offenders': [...]} for the current page."""
    return page.evaluate(OVERFLOW_JS)


def format_offenders(result):
    """Human-readable blame list for a failure message."""
    if not result["offenders"]:
        return "  (no offending element identified — likely a scrollbar or margin effect)"
    lines = []
    for o in result["offenders"]:
        ident = " id=%r" % o["id"] if o.get("id") else ""
        kind = " [scroll container]" if o.get("scroller") else ""
        lines.append(
            "  <%s%s class=%r> right=%dpx width=%dpx%s" % (
                o["tag"], ident, o["cls"], o["right"], o["width"], kind)
        )
    return "\n".join(lines)


def assert_no_overflow(page, label, width):
    """Assert the page fits `width`, naming the offending elements if not."""
    result = measure(page)
    assert result["overflow"] <= 0, (
        "%s overflows at %dpx by %dpx:\n%s"
        % (label, width, result["overflow"], format_offenders(result))
    )