"""muse-viz CLI: render a corpus file to piano-roll PNG.

Usage:
  python3 tools/muse_viz/cli.py <file> [--parts P1,P2] [--out out.png]
  python3 tools/muse_viz/cli.py <file> [--first N]     # first N parts only
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ir"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from muse_ir import load  # noqa: E402
from muse_viz import render, PianoRollConfig  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--parts", type=str, default=None, help="comma-separated part ids")
    ap.add_argument("--first", type=int, default=None, help="render only first N parts")
    ap.add_argument("--out", type=str, default=None)
    ap.add_argument("--title", type=str, default=None)
    args = ap.parse_args()

    w = load(args.file)
    parts = None
    if args.parts:
        parts = args.parts.split(",")
    elif args.first:
        parts = [p.id for p in w.parts[: args.first]]

    out = args.out or os.path.splitext(os.path.basename(args.file))[0] + "_piano.png"
    res = render(w, PianoRollConfig(parts=parts, out=out, title=args.title))
    print(f"OK  rendered {len(res.parts_rendered)} parts → {res.path}")


if __name__ == "__main__":
    main()
