"""L4 distiller tests: interpretation extraction, revision shape, curve-shape classification."""

from muse_distill import dump_delta, extract_interpretation, seed_revision
from muse_mockup import Mockup, Note


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