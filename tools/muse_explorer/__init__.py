"""muse_explorer — corpus-explorer artifact generator (issue #164).

Regenerates docs/explorer/: per-work JSON (IR summary, W3 patterns, S2 pack
stats) + W5 piano-roll PNGs. QA-only; Netlify publishes docs/ as static.

    python3 tools/muse_explorer/generate.py
"""

from .generate import main

__all__ = ["main"]
