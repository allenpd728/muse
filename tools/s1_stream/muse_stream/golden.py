"""S1 golden-vector generator.

A golden vector is (source file → canonical JSON dump of the parsed IR) —
the pair every S1 decoder must reproduce byte-for-byte. JSON is the
interchange encoding only (readability, diffability); the binary layout is
pinned by S2. Canonical form: json.dumps(sort_keys=True, separators) +
trailing newline; integers only.

    python -m muse_stream.golden generate <source> -o <vector.json>
    python -m muse_stream.golden verify <source> <vector.json>
"""

from __future__ import annotations

import argparse
import json
import sys

from muse_ir import UNPITCHED, Work, load


def work_to_canonical(work: Work) -> dict:
    """Deterministic canonical dump of a Work. Ordering follows the IR's
    own deterministic sort (notes by sort_key, maps by tick)."""
    return {
        "s1_version": 0,
        "meta": {
            "source_format": work.meta.source_format,
            "ppq": work.meta.ppq,
            "title": work.meta.title,
            "warnings": sorted(work.meta.warnings),
        },
        "maps": {
            "tempo": [[t, mb] for t, mb in work.maps.tempo],
            "meter": [[t, n, d] for t, n, d in work.maps.meter],
            "key": [[t, f, m] for t, f, m in work.maps.key],
        },
        "parts": [
            {
                "id": p.id,
                "name": p.name,
                "instrument": {
                    "name": p.instrument.name,
                    "gm_program": p.instrument.gm_program,
                },
                "inferred_voice": p.inferred_voice,
                "dynamics": [[d.tick, d.text] for d in p.dynamics],
                "hairpins": [
                    [h.kind, h.start_tick, h.end_tick] for h in p.hairpins
                ],
                "notes": [
                    {
                        "pitch": n.pitch,
                        "onset": n.onset,
                        "duration": n.duration,
                        "voice": n.voice,
                        "velocity": n.velocity,
                        "velocity_inferred": n.velocity_inferred,
                        "articulations": list(n.articulations),
                        "notations": sorted(n.notations),
                        "unpitched": UNPITCHED in n.notations,
                    }
                    for n in p.notes
                ],
            }
            for p in work.parts
        ],
    }


def canonical_json(work: Work) -> str:
    return json.dumps(work_to_canonical(work), sort_keys=True, separators=(",", ":")) + "\n"


def generate(source: str, out_path: str) -> None:
    work = load(source)
    with open(out_path, "w") as fh:
        fh.write(canonical_json(work))


def verify(source: str, vector_path: str) -> bool:
    work = load(source)
    expected = canonical_json(work)
    with open(vector_path) as fh:
        actual = fh.read()
    return expected == actual


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="muse-stream-golden")
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("generate")
    g.add_argument("source")
    g.add_argument("-o", "--output", required=True)
    v = sub.add_parser("verify")
    v.add_argument("source")
    v.add_argument("vector")
    args = ap.parse_args(argv)

    if args.cmd == "generate":
        generate(args.source, args.output)
        print(f"wrote {args.output}")
        return 0
    ok = verify(args.source, args.vector)
    print("verify:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
