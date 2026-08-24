"""muse-distill CLI: mockup → seed revision YAML/JSON.

    python -m muse_distill <mockup.json> [--out delta.yaml] [--format yaml|json]
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "muse_mockup"))
sys.path.insert(0, os.path.dirname(__file__))

from muse_mockup import load_mockup  # noqa: E402
from .distill import dump_delta, seed_revision  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="muse-distill")
    ap.add_argument("mockup", help="mockup session file (JSON)")
    ap.add_argument("--out", default=None)
    ap.add_argument("--format", choices=["yaml", "json"], default="yaml")
    args = ap.parse_args(argv)

    mockup = load_mockup(open(args.mockup).read())
    delta = seed_revision(mockup)
    text = dump_delta(delta, fmt=args.format)
    out = args.out or os.path.splitext(args.mockup)[0] + ".delta." + args.format.replace("yaml", "yaml")
    with open(out, "w") as fh:
        fh.write(text)
    print(f"{out}: {delta['interpretation']['tempo_curve_shape']} curve, {delta['provenance']['note_count']} notes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
