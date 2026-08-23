"""muse-diff CLI: compare two corpus files or validate round-trips.

Usage:
  python3 tools/muse_diff/cli.py <file_a> <file_b> [--tolerance-ticks N]
  python3 tools/muse_diff/cli.py --self-test
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))  # tools/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ir"))
from muse_ir import load  # noqa: E402
from muse_diff import diff  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("a", nargs="?")
    ap.add_argument("b", nargs="?")
    ap.add_argument("--tolerance-ticks", type=int, default=0)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        sys.exit(self_test())

    if not (args.a and args.b):
        ap.error("need two files (or --self-test)")

    wa, wb = load(args.a), load(args.b)
    report = diff(wa, wb, args.tolerance_ticks)
    print(f"recall {report.recall:.4f}  precision {report.precision:.4f}  "
          f"matched {report.matched}/{report.total_a} vs {report.total_b}")
    for m in report.mismatches[:20]:
        print("  ", m.describe())
    if len(report.mismatches) > 20:
        print(f"   ... {len(report.mismatches)-20} more")
    sys.exit(0 if report.ok() else 1)


def self_test():
    """Mutation tests: deletions degrade recall, insertions degrade
    precision, onset drift degrades matched quality."""
    here = os.path.dirname(__file__)
    f = os.path.join(here, "..", "..", "corpus", "bach", "bwv227.1.mxl")
    w = load(f)
    r = diff(w, w)
    assert r.ok() and r.recall == 1.0 and r.precision == 1.0, "self-diff != 1.0"
    print("OK  self-diff = 1.0")

    import copy
    # deletion → recall < 1 against original
    w2 = copy.deepcopy(w)
    del w2.parts[0].notes[5]
    r2 = diff(w, w2)
    assert r2.recall < 1.0, "deletion should degrade recall"
    print(f"OK  deletion degrades recall ({r2.recall:.4f})")

    # insertion → precision < 1
    w3 = copy.deepcopy(w)
    from muse_ir.model import Note
    w3.parts[0].notes.append(Note(pitch=99, onset=10**9, duration=1))
    r3 = diff(w, w3)
    assert r3.precision < 1.0, "insertion should degrade precision"
    print(f"OK  insertion degrades precision ({r3.precision:.4f})")

    # onset drift with tolerance=0 counts as missing+extra; with high
    # tolerance it matches but reports onset-drift
    w4 = copy.deepcopy(w)
    w4.parts[0].notes[0] = Note(**{**w4.parts[0].notes[0].__dict__, "onset": w4.parts[0].notes[0].onset + 5})
    r4 = diff(w, w4, tolerance_ticks=10)
    assert any(m.kind == "onset-drift" for m in r4.mismatches), "drift not classified"
    print("OK  onset drift classified within tolerance")
    print("self-test passed.")
    return 0


if __name__ == "__main__":
    main()
