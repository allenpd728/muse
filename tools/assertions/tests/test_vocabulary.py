"""C4 assertion vocabulary tests: authored sets exist for both works and
validate cleanly through S3.5's validator on their own source."""

import os

import pytest

from muse_ir import load
from muse_assert import validate_assertions
from vocabulary import AUTHORED, get

CORPUS_ROOT = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "corpus")
)


def corpus_path(*parts):
    return os.path.join(CORPUS_ROOT, *parts)


def test_authored_sets_exist():
    assert set(AUTHORED) == {"BWV227.1", "Schubert D.810"}


def test_bach_authored_validates_against_source():
    work = load(corpus_path("bach", "bwv227.1.mxl"))
    validate_assertions(work, get("BWV227.1"))


def test_schubert_authored_validates_against_source():
    work = load(corpus_path("schubert", "death-and-the-maiden.mxl"))
    validate_assertions(work, get("Schubert D.810"))


def test_violation_fails_loudly():
    work = load(corpus_path("bach", "bwv227.1.mxl"))
    from muse_assert import AssertionError
    with pytest.raises(AssertionError):
        validate_assertions(work, {"register": {"min": "G4", "max": "G5"}})


def test_compliant_mockup_passes_silently():
    """A work that obeys its own bounds must not raise."""
    work = load(corpus_path("bach", "bwv227.1.mxl"))
    validate_assertions(work, get("BWV227.1"))


def test_unknown_work_returns_empty():
    assert get("not-a-work") == {}


# --- Kind coverage (issue #216): every vocabulary kind exercised through
# the real validator against the real corpus. Theme pitches and tempo
# values below are derived from the source files once and pinned — the
# same no-silent-drift mechanism as the authored sets themselves.

BACH_OPENING_P1 = [71, 71, 69, 67, 66, 64]  # BWV227.1 first part, first 6 pitches


def test_must_contain_finds_real_theme():
    work = load(corpus_path("bach", "bwv227.1.mxl"))
    validate_assertions(work, {"must_contain": [BACH_OPENING_P1]})


def test_must_contain_missing_theme_fails():
    work = load(corpus_path("bach", "bwv227.1.mxl"))
    from muse_assert import AssertionError
    with pytest.raises(AssertionError) as exc:
        validate_assertions(work, {"must_contain": [[1, 2, 3]]})
    assert exc.value.kind == "must_contain"


def test_form_empty_sections_passes():
    work = load(corpus_path("bach", "bwv227.1.mxl"))
    validate_assertions(work, {"form": {"sections": []}})


def test_form_missing_section_fails():
    work = load(corpus_path("bach", "bwv227.1.mxl"))
    from muse_assert import AssertionError
    with pytest.raises(AssertionError) as exc:
        validate_assertions(work, {"form": {"sections": ["never-a-section"]}})
    assert exc.value.kind == "form"


def test_tempo_bounds_authored_pass_on_source():
    """BWV227.1 pins a single 96 bpm tempo; authored 60–180 bounds hold."""
    work = load(corpus_path("bach", "bwv227.1.mxl"))
    validate_assertions(work, {"tempo_bounds": {"min_bpm": 60, "max_bpm": 180}})


def test_tempo_bounds_violation_fails():
    work = load(corpus_path("bach", "bwv227.1.mxl"))
    from muse_assert import AssertionError
    with pytest.raises(AssertionError) as exc:
        validate_assertions(work, {"tempo_bounds": {"max_bpm": 50}})
    assert exc.value.kind == "tempo_bounds"


def test_register_scoped_to_absent_part_passes():
    """The part filter skips non-matching parts: an unscoped failing bound
    (G4–G5) passes when scoped to a part id the work doesn't have."""
    work = load(corpus_path("bach", "bwv227.1.mxl"))
    validate_assertions(
        work, {"register": {"min": "G4", "max": "G5", "part": "NO-SUCH-PART"}}
    )


def test_unknown_kind_fails_loudly():
    work = load(corpus_path("bach", "bwv227.1.mxl"))
    from muse_assert import AssertionError
    with pytest.raises(AssertionError) as exc:
        validate_assertions(work, {"not-a-kind": {}})
    assert exc.value.kind == "unknown-assertion-kind"
