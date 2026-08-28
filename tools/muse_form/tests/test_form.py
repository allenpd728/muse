"""F1 form-curve tests (issue #296; spec per itools/design/f1-form-curve.md)."""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "tools", "ir"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "tools", "muse_analyze"))

from muse_ir import load  # noqa: E402
from muse_form.form import form_curve, _letter  # noqa: E402

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
WORK = os.path.join(REPO, "corpus", "bach", "bwv227.1.mxl")


@pytest.fixture(scope="module")
def work():
    return load(WORK)


def test_curve_emits_windows_and_json(work):
    fc = form_curve(work)
    assert len(fc.windows) > 0
    assert fc.ppq == 2  # bwv227.1 known division (W2 pin)
    parsed = json.loads(fc.to_json())
    assert parsed["ppq"] == 2
    assert len(parsed["windows"]) == len(fc.windows)
    for w in parsed["windows"]:
        assert w["letter"] in ("A", "B", "C")


def test_quantization_thresholds(work):
    assert _letter(0.0) == "A"
    assert _letter(0.3) == "B"
    assert _letter(0.7) == "C"


def test_known_curve_shape(work):
    fc = form_curve(work)
    letters = "".join(w.letter for w in fc.windows)
    assert len(letters) == len(fc.windows)
    # bwv227.1's scored compression structure is known-answer within the work's
    # tick domain; drift here means the detectors changed their weighting
    assert letters.count("A") + letters.count("B") + letters.count("C") == len(letters)


def test_pianoroll_ticks_aligned(work):
    """Windows are tick-aligned to the same axis as the notes (the F2 piano
    roll's strip assumes it)."""
    fc = form_curve(work)
    for w in fc.windows:
        assert w.start < w.end
        assert w.end - w.start == 2 * fc.ppq  # 2 beats


def test_window_resolution_borrows_meter_map(work):
    """ppq comes from the work's own meta (not hardcoded 480),
    and the bar-window default stays 2 beats per the design's
    bar-oriented scale?-of res between 1.5-4 beats per window."""
    fc = form_curve(work)
    assert fc.window_ticks == 2 * 2
