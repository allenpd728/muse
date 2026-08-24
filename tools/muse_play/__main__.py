"""muse-play CLI: render a corpus source to WAV.

    python -m muse_play <source> [-o out.wav]

source: a MusicXML (.xml/.mxl) or MIDI (.mid) corpus file, any path the
W1 IR loads, or a `.mu` container (decoded via P1's muse_decode — the
container seam P3 pins).
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ir"))
sys.path.insert(0, os.path.dirname(__file__))

from muse_ir import IRError, load  # noqa: E402
from .play import PlayError, render_work  # noqa: E402


def _load_source(source: str):
    """`.mu` containers decode via P1; everything else goes to the W1 IR."""
    if source.endswith(".mu"):
        here = os.path.dirname(__file__)
        for dep in ("muse_decode", "muse_mu", "muse_roll"):
            sys.path.insert(0, os.path.join(here, "..", dep))
        from muse_decode import DecodeError, decode
        try:
            return decode(source)
        except DecodeError as exc:
            raise IRError(str(exc)) from exc
    return load(source)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="muse-play")
    ap.add_argument("source", help="source file: .xml/.mxl/.mid/.mu")
    ap.add_argument("-o", "--output", default=None)
    args = ap.parse_args(argv)

    try:
        work = _load_source(args.source)
    except IRError as exc:
        print(f"muse-play: {exc}", file=sys.stderr)
        return 2

    out = args.output or os.path.splitext(args.source)[0] + ".wav"
    try:
        meta = render_work(work, out)
    except PlayError as exc:
        print(f"muse-play: {exc}", file=sys.stderr)
        return 1
    print(f"{meta['out']}: {meta['notes']} notes, {meta['parts']} parts, {meta['duration_sec']}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
