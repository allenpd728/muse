"""muse-render CLI: render a mockup JSON to WAV.

    python -m muse_render <mockup.json> [-o out.wav]
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))

from muse_mockup import load_mockup  # noqa: E402
from .render import render_to_file  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="muse-render")
    ap.add_argument("mockup", help="mockup JSON (L1 session file)")
    ap.add_argument("-o", "--output", default=None)
    args = ap.parse_args(argv)

    mockup = load_mockup(open(args.mockup).read())
    out = args.output or os.path.splitext(args.mockup)[0] + ".wav"
    meta = render_to_file(mockup, out)
    print(f"{meta['out']}: {meta['notes']} notes, {meta['duration_sec']}s, parts={meta['parts']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
