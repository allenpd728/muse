"""Analyzer tests: SIATEC mechanics, classification, CLI integration."""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "corpus_loader"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "ir"))

import muse_corpus  # noqa: E402

from muse_analyze import analyzer  # noqa: E402
from muse_analyze.cli import main as cli_main  # noqa: E402


class MockWork:
    def __init__(self, points):
        self.parts = [MockPart(points)]


class MockPart:
    def __init__(self, points):
        self.notes = [MockNote(o, p) for (o, p) in points]


class MockNote:
    def __init__(self, onset, pitch):
        self.pitch = pitch
        self.onset = onset


def _known(points):
    return MockWork(points)


def test_exact_repeat():
    """Two identical motifs in time -> exact."""
    motif = [(0, 60), (4, 62), (8, 64)]
    work = _known(motif + [(o + 16, p) for (o, p) in motif])
    result = analyzer.analyze(work, max_points=1000)
    ex = [p for p in result["patterns"] if p.kind == "exact"]
    assert ex, "exact repeat must be found"
    best = max(ex, key=lambda p: len(p.points))
    assert len(best.points) == 3


def test_transposed_repeat():
    """Same motif shifted up a constant interval -> transposed."""
    motif = [(0, 60), (4, 62), (8, 64), (12, 65)]
    work = _known(motif + [(o + 16, p + 7) for (o, p) in motif])
    result = analyzer.analyze(work, max_points=1000)
    tr = [p for p in result["patterns"] if p.kind == "transposed"]
    assert tr, "transposed repeat must be found"


def test_sequence():
    """Motif stepping up by a constant shift each entry -> sequence."""
    motif = [(0, 60), (4, 62)]
    occurrences = []
    for k in range(4):
        occurrences += [(o + k * 8, p + k * 2) for (o, p) in motif]
    work = _known(occurrences)
    result = analyzer.analyze(work, max_points=1000)
    seq = [p for p in result["patterns"] if p.kind == "sequence"]
    assert seq, "sequence must be classified"
    assert min(len(p.points) for p in seq) >= 2


def test_ostinato_cycle_found():
    """A repeating rhythm cycle -> ostinato report entry."""
    points = [(0, 50), (8, 51)]
    for k in range(5):
        points += [(16 * (k + 1) + 0, 50 + k % 2), (16 * (k + 1) + 8, 51 + k % 2)]
    work = _known(points)
    result = analyzer.analyze(work, max_points=1000)
    assert result["ostinati"], "ostinato cycle must be reported"


def test_mirror_candidate_flagged():
    """A pattern with symmetric interval content flags mirror=True."""
    work = _known([(0, 60), (4, 62), (8, 60), (12, 62), (16, 60)])
    result = analyzer.analyze(work, max_points=1000)
    mir = [p for p in result["patterns"] if p.extra["mirror"]]
    assert mir, "mirror candidate must be flagged"


def test_known_answer_on_real_corpus():
    """Bach BWV 227.1: point cloud is its sounding notes; exact motif wins."""
    work = muse_corpus.load_file("bach/bwv227.1.mxl")
    result = analyzer.analyze(work, max_points=500)
    assert result["point_count"] == 275
    assert result["patterns"], "patterns must be non-empty on a corpus work"
    kinds = {p.kind for p in result["patterns"]}
    assert "exact" in kinds
    # The tonic pedal chain (long exact run) tops the quality ranking.
    top = result["patterns"][0]
    assert top.kind == "exact"
    assert len(top.points) > 30


def test_deterministic_output():
    """Same input -> identical report, twice."""
    work = muse_corpus.load_file("bach/bwv227.1.mxl")
    r1 = analyzer.analyze(work, max_points=500)
    r2 = analyzer.analyze(work, max_points=500)
    keys1 = [(p.kind, p.quality, len(p.points)) for p in r1["patterns"]]
    keys2 = [(p.kind, p.quality, len(p.points)) for p in r2["patterns"]]
    assert keys1 == keys2


def test_cli_per_work(capsys):
    assert cli_main(["bach-bwv227", "--max-points", "500"]) == 0
    out = capsys.readouterr().out
    assert "bach-bwv227" in out
    assert "patterns total" in out


def test_cli_json_struct(tmp_path):
    out = tmp_path / "r.json"
    assert cli_main(["bach-bwv227", "--max-points", "500", "--json", str(out)]) == 0
    data = json.loads(out.read_text())
    assert data["works"][0]["id"] == "bach-bwv227"
    assert data["works"][0]["stats"]["patterns_total"] > 0
