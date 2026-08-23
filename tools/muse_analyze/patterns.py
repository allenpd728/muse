"""Pattern discovery engine over (onset, pitch) events.

We use suffix/point-set family matching in the spirit of SIATEC without
external deps: sorted point-set comparison with normalization variants
(exact, transposed, sequence, mirror/retrograde, ostinato, imitative).
Per-phrase delta curves land in the same report.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class Pattern:
    kind: str            # exact | transposed | sequence | mirror | retrograde | ostinato | imitative
    length: int          # notes in pattern
    occurrences: list    # [(onset, delta_pitch or transform)]
    work: str = ""

    def translate(self, notes, transform=None):
        return notes


PITCH_CLASSES = ["exact", "transposed", "sequence", "mirror", "retrograde"]
RHYTHM_CLASSES = ["ostinato", "imitative"]


def _points(part):
    """(onset, pitch) sorted; ties by pitch. Excludes rests/unpitched."""
    pts = [(n.onset, n.pitch) for n in part.notes
           if n.pitch is not None and not getattr(n, "is_rest", False)
           and not getattr(n, "is_unpitched", False)]
    pts.sort()
    return pts


def _normalize(pts, kind):
    """Normalize onset to 0 for shape comparison."""
    if not pts:
        return pts
    o0 = pts[0][0]
    if kind == "exact":
        return [(o - o0, p) for o, p in pts]
    if kind == "transposed":
        p0 = pts[0][1]
        return [(o - o0, p - p0) for o, p in pts]
    if kind == "mirror":
        return [(o - o0, -p) for o, p in pts]
    if kind == "retrograde":
        return [(o - o0, p) for o, p in pts]
    return [(o - o0, p) for o, p in pts]


def _find_repeats(pts, min_len=4, max_len=64, max_window=2000):
    """Exact + normalized repeat patterns.

    Scale budget: works longer than max_window points get their pattern
    lengths capped (W6's ladder budget — geometric discovery on the Ninth
    is a separate study; this keeps small/mid works exhaustive).
    """
    n = len(pts)
    if n > max_window:
        max_len = min(max_len, 16)
    found = defaultdict(list)  # pattern_tuple -> [start_onsets]
    for L in range(min_len, min(max_len, n // 2) + 1):
        for i in range(n - L + 1):
            seg = pts[i:i + L]
            norm = _normalize(seg, "exact")
            found[tuple(norm)].append(pts[i][0])
    return {k: sorted(set(v)) for k, v in found.items() if len(set(v)) > 1}


def _find_transposed(pts, min_len=4, max_len=48, max_window=2000):
    n = len(pts)
    if n > max_window:
        max_len = min(max_len, 12)
    found = defaultdict(list)
    for L in range(min_len, min(max_len, n // 2) + 1):
        for i in range(n - L + 1):
            seg = pts[i:i + L]
            norm = _normalize(seg, "transposed")
            found[tuple(norm)].append(pts[i][0])
    return {k: sorted(set(v)) for k, v in found.items() if len(set(v)) > 1}


def _find_ostinato(pts, min_len=2, max_len=16):
    """Rhythm-only: onset intervals repeat (pitch ignored)."""
    if len(pts) < 2:
        return {}
    intervals = [pts[i + 1][0] - pts[i][0] for i in range(len(pts) - 1)]
    # count recurring interval sequences
    counts = defaultdict(int)
    for L in range(min_len, max_len + 1):
        for i in range(len(intervals) - L + 1):
            seq = tuple(intervals[i:i + L])
            counts[seq] += 1
    return {k: v for k, v in counts.items() if v > 2}


def _find_imitative(parts_snapshots, min_notes=6):
    """Imitative entries: same normalized pattern appears at different onsets
    in different parts (Renaissance polyphony signature)."""
    norms = {}
    for pid, pts in parts_snapshots.items():
        if len(pts) < min_notes:
            continue
        seg = pts[:min_notes]
        norm = _normalize(seg, "transposed")
        norms[tuple(norm)] = (pid, pts[0][0])
    hits = defaultdict(list)
    for norm, (pid, onset) in norms.items():
        hits[norm].append((pid, onset))
    return {k: v for k, v in hits.items() if len(v) > 1}


def _delta_curve(pts, window=16):
    """Per-phrase curve: IOI (inter-onset interval) series within a window
    size, used by C-composing budget calibration."""
    iois = [pts[i + 1][0] - pts[i][0] for i in range(len(pts) - 1)]
    if not iois:
        return []
    mean = sum(iois) / len(iois)
    # curve: the sequence of IOI ratios vs mean (where freedom concentrates)
    return [(pts[i + 1][0], iois[i] / mean if mean else 1.0) for i in range(len(iois))]


@dataclass
class PatternReport:
    work: str
    parts: dict                  # part_id -> count
    exact: dict = field(default_factory=dict)
    transposed: dict = field(default_factory=dict)
    ostinato: dict = field(default_factory=dict)
    imitative: dict = field(default_factory=dict)
    delta_curve: list = field(default_factory=list)

    def summary(self):
        def fmt(d, name):
            return f"  {name}: {len(d)} distinct patterns"
        return "\n".join([
            f"work: {self.work}",
            f"parts: {self.parts}",
            fmt(self.exact, "exact repeats"),
            fmt(self.transposed, "transposed repeats"),
            fmt(self.ostinato, "ostinato (rhythm)"),
            fmt(self.imitative, "imitative entries"),
            f"  delta curve points: {len(self.delta_curve)}",
        ])


def analyze(work, name_hint=""):
    """Analyze all parts for pattern classes."""
    parts_snap = {}
    rep = PatternReport(work=name_hint or getattr(work, "title", "unknown"),
                        parts={p.id: len(p.notes) for p in work.parts})
    for p in work.parts:
        pts = _points(p)
        parts_snap[p.id] = pts
        if len(pts) < 4:
            continue
        rep.exact.update(_find_repeats(pts))
        rep.transposed.update(_find_transposed(pts))
        rep.ostinato.update(_find_ostinato(pts))
        if not rep.delta_curve:
            rep.delta_curve = _delta_curve(pts)
    if len(parts_snap) > 1:
        rep.imitative = _find_imitative(parts_snap)
    return rep
