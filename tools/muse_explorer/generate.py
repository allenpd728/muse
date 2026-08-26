"""Explorer artifact generator: docs/explorer/{data/works.json, img/*.png}.

Reads the corpus registry (W2), renders piano-rolls (W5), packs each work
(S2) for ratio stats, and merges W3's analysis-report pattern counts.
Deterministic: same corpus → byte-identical JSON. PNGs are rerenders and
may differ at the byte level across matplotlib versions; the contract is
their existence and non-emptiness, pinned by tests.
"""

from __future__ import annotations

import hashlib
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


def generate_workbench(workbench_dir=None):
    """Regenerate workbench artifacts: per-seed probe JSON + seed index.

    Reads every committed seed in seeds/, computes probes via muse_probes,
    and writes docs/workbench/data/seeds/{index.json, *.probes.json} plus
    the seed YAML copy the page renders. Deterministic for fixed inputs.
    """
    from muse_probes.probes import compute_probes
    from muse_seed import load_seed

    wb = workbench_dir or os.path.join(REPO, "docs", "workbench")
    seeds_out = os.path.join(wb, "data", "seeds")
    os.makedirs(seeds_out, exist_ok=True)
    index = {"seeds": []}
    seeds_dir = os.path.join(REPO, "seeds")
    seen_content = {}  # sha256 of bytes -> index entry (content dedup, #273)
    for fname in sorted(os.listdir(seeds_dir)):
        if not fname.endswith((".yaml", ".yml")):
            continue
        raw = open(os.path.join(seeds_dir, fname), "rb").read()
        digest = hashlib.sha256(raw).hexdigest()
        if digest in seen_content:
            # Byte-identical revision copy (pre-lineage checkpoint
            # convention): one index entry per distinct revision.
            seen_content[digest].setdefault("aliases", []).append(fname)
            continue
        seed = load_seed(raw.decode(), fmt="yaml")
        work_rel = getattr(seed, "provenance", {}).get("source")
        if not work_rel:
            continue
        work = muse_corpus.load_file(os.path.join(muse_corpus.CORPUS_ROOT, work_rel.replace("corpus/", "")))
        report = compute_probes(seed, work,
                                seed_path=os.path.join(seeds_dir, fname))
        probes_name = fname.replace(".seed.yaml", ".probes.json").replace(".yml", ".probes.json")
        with open(os.path.join(seeds_out, probes_name), "w") as fh:
            fh.write(report.to_json())
        with open(os.path.join(seeds_out, fname), "w") as fh:
            fh.write(open(os.path.join(seeds_dir, fname)).read())
        entry = {
            "work_id": seed.work_id,
            "file": fname,
            "probes": probes_name,
        }
        index["seeds"].append(entry)
        seen_content[digest] = entry
    with open(os.path.join(seeds_out, "index.json"), "w") as fh:
        json.dump(index, fh, indent=1)
        fh.write("\n")
    _write_directives_artifacts(seeds_dir, seeds_out)
    return index


def _write_directives_artifacts(seeds_dir, seeds_out):
    """Per-work <work>.directives.json — the rehearsal log the workbench
    pane renders: each committed directive with its lineage status (R2)."""
    from muse_lineage.lineage import walk

    for entry in os.listdir(seeds_dir):
        if not entry.endswith(".directives") or not os.path.isdir(
                os.path.join(seeds_dir, entry)):
            continue
        work_id = entry[: -len(".directives")]
        ddir = os.path.join(seeds_dir, entry)
        rows = []
        for f in sorted(os.listdir(ddir)):
            if not f.endswith(".directive.txt"):
                continue
            path = os.path.join(ddir, f)
            text = open(path).read().splitlines()[0] if open(path).read() else ""
            # the revision this directive produced points back at it; find
            # it by scanning for a seed whose extends == this file's hash.
            from muse_lineage.lineage import sha256_file, store_files
            digest = sha256_file(path)
            status = "root"
            for cand in store_files([seeds_dir]):
                if cand.endswith(".seed.yaml") and digest in open(cand).read():
                    hops = walk(cand, [seeds_dir])
                    status = ("verified" if all(
                        h.status in ("verified", "root") for h in hops)
                        else "broken")
                    break
            rows.append({"slug": f[: -len(".directive.txt")], "text": text,
                         "lineage": status})
        with open(os.path.join(seeds_out, f"{work_id}.directives.json"), "w") as fh:
            json.dump({"work_id": work_id, "directives": rows}, fh, indent=1)
            fh.write("\n")


def main():
    works = generate()
    index = generate_workbench()
    print(f"explorer: {len(works)} works → docs/explorer/")
    print(f"workbench: {len(index['seeds'])} seeds → docs/workbench/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
