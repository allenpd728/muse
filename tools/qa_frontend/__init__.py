"""qa_frontend — Tier 2 headless DOM tests for the explorer (issue #183).

Playwright + headless Chromium against a local static server. The page
executes for real: work-list populates, row click renders detail, images
resolve, the failure fallback works, console errors are caught.
"""

from .harness import PageSession, serve_static

__all__ = ["PageSession", "serve_static"]
