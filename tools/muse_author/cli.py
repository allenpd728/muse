"""muse-author CLI: propose a seed from a work IR, validate via C1.

Usage:
  python3 tools/muse_author/cli.py <work> [--era classical|romantic|...]
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ir"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from muse_ir import load  # noqa: E402
from muse_author import propose_seed  # noqa: E402
from muse_seed import Seed, dump_seed, validate_seed  # noqa: E402
from muse_seed_cli.cli import _validate  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("work")
    ap.add_argument("--era", default="classical")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    w = load(args.work)
    proposal = propose_seed(w, era_hint=args.era)
    sd = proposal.seed_dict

    out = args.out or f"{os.path.splitext(os.path.basename(args.work))[0]}.proposal.yaml"
    seed = Seed(
        format_version=sd["format_version"],
        work_id=sd["work_id"],
        title=sd["title"],
        params=sd["params"],
        philosophy=sd["philosophy"],
        variation_points=sd["variation_points"],
        assertions=sd["assertions"],
        provenance=sd["provenance"],
    )
    try:
        validate_seed(seed)
    except Exception as e:
        print(f"FAIL  proposed seed invalid: {e}")
        sys.exit(1)
    open(out, "w").write(dump_seed(seed, fmt="yaml"))
    print(f"OK  proposed → {out}")

    rc = _validate(out, args.work)
    print(f"validation exit: {rc}")
    sys.exit(rc)


if __name__ == "__main__":
    main()
