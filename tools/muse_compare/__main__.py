"""muse-compare CLI: blind A/B harness.

    python -m muse_compare <work> [--models A,B] [--era classical] [--out-dir DIR]
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ir"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from muse_ir import load  # noqa: E402
from .compare import run_compare  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="muse-compare")
    ap.add_argument("work")
    ap.add_argument("--models", default="stub-a,stub-b")
    ap.add_argument("--era", default="classical")
    ap.add_argument("--out-dir", default=None)
    args = ap.parse_args(argv)

    work = load(args.work)
    models = args.models.split(",")
    out_dir = args.out_dir or f"compare_{os.path.splitext(os.path.basename(args.work))[0]}"
    meta = run_compare(work, args.era, models, out_dir)
    print(f"{meta['out_dir']}: models={meta['models']}")
    for m, a in meta["artifacts"].items():
        print(f"  {m}: {a['path']} [{a['hash']}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
