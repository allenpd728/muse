"""muse-analyze CLI: pattern report per work or full corpus.

Usage:
  python3 tools/muse_analyze/cli.py <work-id> [--max-points N] [--json out.json]
  python3 tools/muse_analyze/cli.py --all
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ir"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "corpus_loader"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import muse_corpus  # noqa: E402

from muse_analyze import patterns as analyzer  # noqa: E402

CORPUS_FILES = [
    "bach/bwv227.1.mxl",
    "bach/bwv227.3.mxl",
    "bach/bwv227.7.mxl",
    "bach/bwv227.11.mxl",
    "byrd/1-Kyrie.mid",
    "byrd/2-Gloria.mid",
    "byrd/3-Credo.mid",
    "byrd/4-Sanctu.mid",
    "byrd/5-Bened.mid",
    "byrd/6-Agnus.mid",
    "schubert/death-and-the-maiden.mxl",
    "beethoven/beethoven-sym5-mov1.xml",
    "beethoven/beethoven-sym9.xml",
]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("work_id", nargs="?")
    ap.add_argument("--max-points", type=int, default=None)
    ap.add_argument("--json", type=str, default=None)
    args = ap.parse_args(argv)

    work_id = args.work_id
    max_points = args.max_points
    resolved = _resolve_work_id(work_id)
    work = muse_corpus.load_file(resolved)

    result = analyzer.analyze(work)
    if args.json:
        patterns = _flatten(result)
        payload = {
            "works": [{
                "id": work_id,
                "stats": {
                    "parts": len(work.parts),
                    "notes": work.note_count,
                    "patterns_total": len(patterns),
                },
                "patterns": patterns,
            }]
        }
        with open(args.json, "w") as f:
            json.dump(payload, f, indent=2)
        return 0

    _print_per_work(work_id, result)
    return 0


def _print_per_work(work_id, result):
    """Print per-work counts in the format the tests pin."""
    print(f"work: {work_id}")
    print(f"  exact repeats: {len(result.exact)}")
    print(f"  transposed repeats: {len(result.transposed)}")
    print(f"  ostinato (rhythm): {len(result.ostinato)}")
    print(f"  imitative entries: {len(result.imitative)}")
    print(f"  delta curve points: {len(result.delta_curve)}")
    total = (len(result.exact) + len(result.transposed) + len(result.ostinato)
             + len(result.imitative))
    print(f"patterns total {total}")


def _flatten(result):
    """Flatten PatternReport dicts into a patterns list for JSON output."""
    patterns = []
    for kind, entries in (
        ("exact", result.exact),
        ("transposed", result.transposed),
        ("ostinato", result.ostinato),
        ("imitative", result.imitative),
    ):
        for pattern, occurrences in entries.items():
            patterns.append({
                "kind": kind,
                "pattern": list(pattern),
                "occurrences": occurrences if hasattr(occurrences, "__iter__") and not isinstance(occurrences, (str, int)) else occurrences,
            })
    return patterns


def _resolve_work_id(work_id):
    """Map a work_id (e.g. bach-bwv227) or a corpus path to a relpath."""
    # if it looks like a path, return it
    if work_id.endswith((".mxl", ".xml", ".mid")):
        return work_id
    for _wid, _title, relpath, _pins in muse_corpus.iter_files():
        if _wid == work_id:
            return relpath
    raise ValueError(f"unknown work_id: {work_id}")


if __name__ == "__main__":
    main()
