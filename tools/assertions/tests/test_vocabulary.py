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
