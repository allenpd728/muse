"""muse-roll CLI: pack/unpack/verify corpus works.

Usage:
  python3 tools/muse_roll/cli.py pack <work> -o <roll.bin>
  python3 tools/muse_roll/cli.py verify <work> <roll.bin>   # W4 ground truth
  python3 tools/muse_roll/cli.py unpack <roll.bin> -o <summary.json>
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))  # tools/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ir"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "muse_diff"))

from muse_ir import load  # noqa: E402
from muse_roll import RollError, decode, encode  # noqa: E402


def cmd_pack(args):
    work = load(args.work)
    data = encode(work)
    out = args.out or os.path.splitext(os.path.basename(args.work))[0] + ".roll.bin"
    with open(out, "wb") as f:
        f.write(data)
    src_size = os.path.getsize(args.work)
    print(f"OK  {args.work} ({src_size} B) → {out} ({len(data)} B, "
          f"{len(data) / src_size:.1%})")
    return 0


def cmd_verify(args):
    try:
        work = load(args.work)
        round_tripped = decode(open(args.roll, "rb").read())
    except RollError as e:
        print(f"FAIL  roll: {e}", file=sys.stderr)
        return 1
    from muse_diff import diff

    report = diff(work, round_tripped)
    print(f"recall={report.recall:.4f} precision={report.precision:.4f} "
          f"matched={report.matched}/{report.total_a}")
    if report.ok():
        print("LOSSLESS")
        return 0
    for m in report.mismatches[:20]:
        print(f"  {m.describe()}")
    print("LOSSY", file=sys.stderr)
    return 1


def cmd_unpack(args):
    try:
        work = decode(open(args.roll, "rb").read())
    except RollError as e:
        print(f"FAIL  roll: {e}", file=sys.stderr)
        return 1
    summary = {
        "source_format": work.meta.source_format,
        "ppq": work.meta.ppq,
        "title": work.meta.title,
        "parts": len(work.parts),
        "notes": work.note_count,
        "tempo_entries": len(work.maps.tempo),
        "duration_ticks": work.duration_ticks(),
    }
    text = json.dumps(summary, indent=2) + "\n"
    if args.out:
        open(args.out, "w").write(text)
    print(text, end="")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="muse-roll", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pack")
    p.add_argument("work")
    p.add_argument("-o", "--out")
    v = sub.add_parser("verify")
    v.add_argument("work")
    v.add_argument("roll")
    u = sub.add_parser("unpack")
    u.add_argument("roll")
    u.add_argument("-o", "--out")
    args = ap.parse_args(argv)
    return {"pack": cmd_pack, "verify": cmd_verify, "unpack": cmd_unpack}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
