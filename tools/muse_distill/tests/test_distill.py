"""L4 distiller tests: interpretation extraction, revision shape, curve-shape classification."""

import hashlib

from muse_distill import dump_delta, extract_interpretation, seed_revision
from muse_mockup import Mockup, Note, dump_mockup


def make_mockup(notes, tempo_map=None):
    m = Mockup(work_id="w")
    m.notes = notes
    m.tempo_map = tempo_map or [(0, 120000)]
    m.part_map = {"P1": "piano"}
    return m


def test_extraction_stats():
    m = make_mockup([Note(60, 0, 480, 60), Note(64, 480, 480, 80), Note(67, 960, 960, 100)])
    i = extract_interpretation(m)
    assert i.velocity_mean == 80.0
    assert i.velocity_pstdev > 0
    assert i.note_count == 3


def test_flat_curve_classified_flat():
    m = make_mockup([Note(60, 0, 480, 60)], tempo_map=[(0, 120000)])
    i = extract_interpretation(m)
    assert i.tempo_curve_shape == "flat"


def test_arch_curve_classified_arch():
    m = make_mockup(
        [Note(60, 0, 480, 60)],
        tempo_map=[(0, 60000), (100, 90000), (200, 80000)],
    )
    i = extract_interpretation(m)
    assert i.tempo_curve_shape == "arch"


def test_seed_revision_shape():
    m = make_mockup([Note(60, 0, 480, 60), Note(64, 480, 480, 80)])
    d = seed_revision(m)
    assert d["work_id"] == "w"
    assert "tempo" in d["params"]
    assert "interpretation" in d


def test_dump_yaml_and_json():
    m = make_mockup([Note(60, 0, 480, 60)])
    d = seed_revision(m)
    y = dump_delta(d, fmt="yaml")
    j = dump_delta(d, fmt="json")
    assert "tempo_range" in y or "tempo" in y
    assert '"tempo"' in j


def test_wavering_curve_classified_wavering():
    """Spec gap 1: a monotonic fall is neither flat (range ≥ 2) nor arch
    (first > last) — the wavering path, pinned positive."""
    m = make_mockup(
        [Note(60, 0, 480, 60)],
        tempo_map=[(0, 120000), (100, 110000), (200, 100000)],
    )
    i = extract_interpretation(m)
    assert i.tempo_curve_shape == "wavering"
    assert i.tempo_range == (100.0, 120.0)


def test_cli_end_to_end(tmp_path):
    """Spec gap 4: the CLI entry point writes the delta YAML."""
    import os
    import subprocess
    import sys

    from muse_mockup import dump_mockup

    m = make_mockup(
        [Note(60, 0, 480, 60), Note(64, 480, 480, 80)],
        tempo_map=[(0, 60000), (100, 90000), (200, 80000)],
    )
    mockup_path = tmp_path / "w.mockup.json"
    mockup_path.write_text(dump_mockup(m, fmt="json"))
    out_path = tmp_path / "w.delta.yaml"
    tools_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
    proc = subprocess.run(
        [sys.executable, "-m", "muse_distill", str(mockup_path),
         "--out", str(out_path)],
        cwd=tools_dir, capture_output=True, text=True, timeout=30,
    )
    assert proc.returncode == 0, proc.stderr
    assert "arch curve" in proc.stdout
    text = out_path.read_text()
    assert "tempo_curve_shape: arch" in text
    assert "min_bpm: 60.0" in text

# --- S3.8b stamping (issue #262; spec
# tests/open_20260826-004500_s3-8b-mockup-persistence.md) ---


def test_stamping_omitted_without_mockup_path():
    """Backward compat: no mockup_path → operation stamped, extends absent."""
    m = make_mockup([Note(60, 0, 480, 60)])
    delta = seed_revision(m)
    assert delta["provenance"]["operation"] == "muse_distill@1"
    assert "extends" not in delta["provenance"]


def test_stamping_extends_matches_persisted_bytes(tmp_path):
    """With mockup_path: extends == SHA-256 of the file's committed bytes."""
    m = make_mockup([Note(60, 0, 480, 60)])
    p = tmp_path / "m.mockup.json"
    p.write_text(dump_mockup(m, fmt="json"))
    delta = seed_revision(m, mockup_path=str(p))
    expect = hashlib.sha256(p.read_bytes()).hexdigest()
    assert delta["provenance"]["extends"] == expect
    assert delta["provenance"]["operation"] == "muse_distill@1"
