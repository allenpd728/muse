"""muse-grow CLI: one growth iteration + compare against a prior delta.

    python3 tools/muse_grow/cli.py <corpus-file>
    python3 tools/muse_grow/cli.py <corpus-file> --prior <prior-delta.json>

Emits the delta to stdout (or --out), and with --prior a growth report to
stderr/exit 0. Deterministic for fixed inputs.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ir"))

from muse_ir import load  # noqa: E402

from muse_grow.grow import compare_deltas, grow_one  # noqa: E402

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _resolve(path):
    return path if os.path.isabs(path) else os.path.join(REPO, path)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="muse-grow", description=__doc__)
    ap.add_argument("work", help="corpus file (IR-loadable)")
    ap.add_argument("--prior", help="prior delta JSON for the growth report")
    ap.add_argument("--out", help="write delta JSON here")
    ap.add_argument("--seed", help="seed YAML driving this iteration "
                                   "(stamped as the mockup's seed_hash)")
    ap.add_argument("--mockup-out", help="persist the producing mockup here "
                                         "(S3.8b: alongside the seed revision)")
    args = ap.parse_args(argv)

    seed = None
    seed_path = None
    if args.seed:
        from muse_seed import load_seed
        seed_path = _resolve(args.seed)
        seed = load_seed(open(seed_path).read(), fmt="yaml")

    work = load(_resolve(args.work))
    mockup_out = _resolve(args.mockup_out) if args.mockup_out else None
    delta, stand_in = grow_one(work, seed, mockup_out=mockup_out,
                               seed_path=seed_path)
    if "error" in delta:
        print(delta["error"], file=sys.stderr)
        return 1

    if args.prior:
        prior = json.load(open(_resolve(args.prior)))
        report = compare_deltas(delta, prior, args.work, stand_in)
        print(report.to_json(), file=sys.stderr, end="")

    out = json.dumps(delta, indent=1, sort_keys=True) + "\n"
    if args.out:
        with open(args.out, "w") as fh:
            fh.write(out)
        print(f"wrote {args.out}")
    else:
        print(out, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
