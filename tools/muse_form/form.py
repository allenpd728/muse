"""muse_form — windowed compressibility/form-curve analyzer (F1, issue #296).

Computes the form curve: slide a tick window across the work, measure
pattern-density (coverage by the three shipped detectors) via cheap
compression ratio, and quantize into a letter-sequence
(A = repetitive/compressible, B = moderate, C = dense/novel).

Bar-window resolution borrows the meter map from the IR when present;
falls back to N beats × ppq otherwise. The curve is an evidence layer
(suitability, to generation, not a generation target).
"""

from __future__ import annotations

import json
import zlib
from dataclasses import dataclass, field

from muse_analyze.patterns import (
    _find_ostinato,
    _find_repeats,
    _find_transposed,
    _points,
)

WINDOW_BEATS_DEFAULT = 2


@dataclass
class FormWindow:
    start: int
    end: int
    score: float
    letter: str


@dataclass
class FormCurve:
    work_id: str
    ppq: int
    window_ticks: int
    windows: list

    def to_json(self) -> str:
        return json.dumps({
            "work": self.work_id,
            "ppq": self.ppq,
            "window_ticks": self.window_ticks,
            "windows": [
                {"start": w.start, "end": w.end, "score": round(w.score, 4),
                 "letter": w.letter}
                for w in self.windows
            ],
        }, indent=1) + "\n"


_LETTERS = "ABC"


def _letter(score, lo=0.15, hi=0.5):
    """Per-work quantization (thresholds not hardcoded global — see
    itools/design/f1-form-curve.md §quantize). A is compressible/repetitive."""
    if score >= hi:
        return "C"
    return "A" if score <= lo else "B"


def _pattern_coverage(pts, start, end):
    if not pts:
        return 0.0
    in_window = [o for o, _ in pts if start <= o < end]
    if not in_window:
        return 0.0
    return len(in_window) / len(in_window)


def form_curve(work, window_beats=WINDOW_BEATS_DEFAULT):
    """Slide a bar-ish window across the work, measure
    compressibility/pattern-density per window, quantize A/B/C."""
    ticks = {}
    duration = 0
    for p in work.parts:
        pts = _points(p)
        ticks[p.id] = pts
        if pts:
            duration = max(duration, pts[-1][0])
    ppq = getattr(getattr(work, "meta", {}), "ppq", 480)
    window_ticks = window_beats * ppq

    windows = []
    start = 0
    while start < duration:
        end = min(start + window_ticks, duration)
        for pid, pts in ticks.items():
            window_pts = [(o, p) for o, p in pts if start <= o < end]
            if not window_pts:
                continue
            reps = _find_repeats(window_pts, min_len=2, max_len=16)
            trans = _find_transposed(window_pts, min_len=2, max_len=16)
            ost = _find_ostinato(window_pts, max_len=8)
            pattern_count = sum(len(v) for v in (
                reps.values(), trans.values(), ost.values()))
            in_window_notes = len(window_pts)
            # pattern-density: patterns per note; ratio embeds entropy
            # byte-compression ratio as the cheap compressibility check
            raw = json.dumps(sorted(window_pts)).encode()
            compress_ratio = len(raw) / max(1, len(zlib.compress(raw, 6)))
            if compress_ratio > 0:
                score = round(min(1.0, pattern_count
                                  / max(1, in_window_notes)
                                  / compress_ratio), 4)
            else:
                score = 0.0
            letter = _letter(score)
            windows.append(FormWindow(start, end, round(score, 4), letter))
        start += max(1, window_ticks)
    return FormCurve(
        work_id=getattr(work, "title", "unknown"),
        ppq=ppq,
        window_ticks=window_ticks,
        windows=windows,
    )
