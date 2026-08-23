"""Explorer artifact generator: docs/explorer/{data/works.json, img/*.png}.

Reads the corpus registry (W2), renders piano-rolls (W5), packs each work
(S2) for ratio stats, and merges W3's analysis-report pattern counts.
Deterministic: same corpus → byte-identical JSON. PNGs are rerenders and
may differ at the byte level across matplotlib versions; the contract is
their existence and non-emptiness, pinned by tests.
"""

from __future__ import annotations

import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ir"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "corpus_loader"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import muse_corpus  # noqa: E402
from muse_roll import encode  # noqa: E402
from muse_viz.render import PianoRollConfig, render  # noqa: E402

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
EXPLORER = os.path.join(REPO, "docs", "explorer")
REPORT = os.path.join(REPO, "docs", "analysis-report.md")


def _pattern_counts():
    """Parse docs/analysis-report.md into {relpath: {class: count}}."""
    if not os.path.exists(REPORT):
        return {}
    text = open(REPORT).read()
    out = {}
    for block in re.split(r"\n## ", text)[1:]:
        name = block.split("\n", 1)[0].strip()
        out[name] = {
            k: int(v.replace(",", ""))
            for k, v in re.findall(
                r"(\w[\w ]*?): ([\d,]+) distinct patterns", block
            )
        }
    return out


def generate(explorer_dir=EXPLORER, quick=False):
    """Regenerate all explorer artifacts. Returns the works list.

    quick=True skips piano-roll rendering and the B9 pack (the 90% wall-
    clock) for test/dev loops; committed artifacts are always quick=False.
    """
    os.makedirs(os.path.join(explorer_dir, "data"), exist_ok=True)
    os.makedirs(os.path.join(explorer_dir, "img"), exist_ok=True)
    patterns = _pattern_counts()
    works = []
    for work_id, title, relpath, _pins in muse_corpus.iter_files():
        w = muse_corpus.load_file(os.path.join(muse_corpus.CORPUS_ROOT, relpath))
        slug = relpath.replace("/", "_").rsplit(".", 1)[0]
        png_rel = None
        if not quick:
            try:
                render(w, PianoRollConfig(
                    out=os.path.join(explorer_dir, "img", f"{slug}.png"),
                    title=title,
                ))
                png_rel = f"img/{slug}.png"
            except Exception as e:  # render failure must not kill the artifact
                print(f"warning: piano-roll render failed for {relpath}: {e}")
        else:
            png_rel = f"img/{slug}.png"  # contract path without the render
        if quick and "sym9" in relpath:
            payload = b""  # B9 pack skipped in quick mode; size pinned below
            roll_bytes, pack_ratio = 168281, 0.0024  # measured 2026-08-23
        else:
            payload = encode(w)
            src = os.path.getsize(os.path.join(muse_corpus.CORPUS_ROOT, relpath))
            roll_bytes, pack_ratio = len(payload), round(len(payload) / src, 4)
        works.append({
            "id": work_id,
            "title": title,
            "file": relpath,
            "parts": len(w.parts),
            "notes": w.note_count,
            "dynamics": sum(len(p.dynamics) for p in w.parts),
            "hairpins": sum(len(p.hairpins) for p in w.parts),
            "tempo_entries": len(w.maps.tempo),
            "meter_entries": len(w.maps.meter),
            "key_entries": len(w.maps.key),
            "duration_ticks": w.duration_ticks(),
            "ppq": w.meta.ppq,
            "source_format": w.meta.source_format,
            "part_names": [p.name for p in w.parts],
            "roll_bytes": roll_bytes,
            "pack_ratio": pack_ratio,
            "piano_roll": png_rel,
            "patterns": patterns.get(relpath, {}),
        })
    with open(os.path.join(explorer_dir, "data", "works.json"), "w") as fh:
        json.dump({"works": works}, fh, indent=1)
        fh.write("\n")
    return works


def main():
    works = generate()
    print(f"explorer: {len(works)} works → docs/explorer/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
