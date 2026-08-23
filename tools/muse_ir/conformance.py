"""Known-answer tests: W1 IR against the corpus conformance table.

Runs every corpus file through the IR and asserts part/note counts and
map coverage per corpus/README.md. Usage: python3 tools/muse_ir/conformance.py
"""

import glob
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from muse_ir import load, ValidationError  # noqa: E402

CORPUS = os.path.join(os.path.dirname(__file__), "..", "..", "corpus")

# (glob, expected_parts, expected_notes_exact_or_None, min_notes)
CASES = [
    ("bach/bwv227.1.mxl", 4, 279, None),
    ("bach/bwv227.3.mxl", 5, None, 300),   # SSATB — 5 parts (registry said 4, measured 5)
    ("bach/bwv227.7.mxl", 4, None, 200),
    ("bach/bwv227.11.mxl", 4, 190, None),  # measured 190 events (registry said ~200)
    ("byrd/1-Kyrie.mid", 3, 71, None),
    ("byrd/2-Gloria.mid", 3, None, 50),
    ("byrd/3-Credo.mid", 3, None, 50),
    ("byrd/4-Sanctu.mid", 3, None, 50),
    ("byrd/5-Bened.mid", 3, None, 30),
    ("byrd/6-Agnus.mid", 3, None, 50),
    ("schubert/death-and-the-maiden.mxl", 4, 24772, None),
    ("beethoven/beethoven-sym5-mov1.xml", 12, 13675, None),
    ("beethoven/beethoven-sym9.xml", 52, 239459, None),
]


def run():
    failures = []
    for rel, exp_parts, exp_notes, min_notes in CASES:
        path = os.path.join(CORPUS, rel)
        if not os.path.exists(path):
            failures.append(f"{rel}: FILE MISSING")
            continue
        try:
            w = load(path)
        except ValidationError as e:
            failures.append(f"{rel}: parse error: {e}")
            continue
        status = []
        if len(w.parts) != exp_parts:
            status.append(f"parts {len(w.parts)} != {exp_parts}")
        if exp_notes is not None and w.note_count != exp_notes:
            status.append(f"notes {w.note_count} != {exp_notes}")
        if min_notes is not None and w.note_count < min_notes:
            status.append(f"notes {w.note_count} < {min_notes}")
        if status:
            failures.append(f"{rel}: {'; '.join(status)}")
        else:
            print(f"OK  {rel}: {len(w.parts)} parts, {w.note_count} notes, "
                  f"ppq {w.ppq}, {w.source_format}")

    # Malformed input must fail loudly
    bad = os.path.join(CORPUS, "README.md")
    try:
        load(bad)
        failures.append("README.md: expected ValidationError, got none")
    except ValidationError:
        print("OK  malformed input rejected loudly")

    if failures:
        print("\nFAILURES:")
        for f in failures:
            print(" ", f)
        sys.exit(1)
    print(f"\nAll {len(CASES)} conformance cases pass.")


if __name__ == "__main__":
    run()
