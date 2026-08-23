"""SIATEC maximal-repeated-pattern discovery plus complementary detectors.

Points come from the W1 IR through the W2 loader: (onset, pitch) per note in
every part, merged into one point set per work. SIATEC (textbook version):
for each displacement vector between two points, the maximal translatable
pattern is the set of points translatable by that vector; occurrences follow
from every translator of that pattern. Sub-classification maps occurrences to
the pattern classes S1–S5 lean on:

- exact repeat: all occurrences share identical (onset, pitch) spacing
- transposed repeat: one constant nonzero pitch shift across occurrences
- sequence: monotone ascending pitch shifts across 3+ occurrences
- rhythmic: translators vary in pitch but rhythm is invariant

Rhythm-only ostinati come from inter-onset-interval cycles that repeat
regardless of pitch; mirror/retrograde candidates compare a pattern's
interval vector with its inversion/reversal.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field


def extract_points(work, max_points=3000):
    """Flatten every part's notes to (onset, pitch) sorted by (onset, pitch).
    Rests (pitch None) are skipped. A deterministic stride subsample caps
    the cloud so the Ninth terminates (W6 picks the per-tier budget)."""
    points = sorted(
        {
            (n.onset, n.pitch)
            for part in work.parts
            for n in part.notes
            if n.pitch is not None
        }
    )
    if len(points) > max_points:
        stride = -(-len(points) // max_points)  # ceil
        points = points[::stride]
    return points


def siatec(points, max_points=3000, min_size=3):
    """SIATEC, exact, one candidate vector per pair. For each displacement
    vector v the maximal translatable pattern runs once; dedupe keys the
    pattern itself so re-hits are free. min_size default drops 2-note trivia;
    the stride cap guards the Ninth (W6 picks the per-tier budget).
    """
    import numpy as np

    pts = list(points)
    if len(pts) > max_points:
        stride = -(-len(pts) // max_points)  # ceil
        pts = pts[::stride]
    arr = np.asarray(pts, dtype=np.int64)
    n = len(pts)
    onsets, pitches = arr[:, 0], arr[:, 1]
    index = {(o, p): int(i) for i, (o, p) in enumerate(arr)}
    vectors = defaultdict(list)
    for i in range(n - 1):
        for j in range(i + 1, n):
            vectors[(int(onsets[j] - onsets[i]), int(pitches[j] - pitches[i]))].append(i)
    results = []
    seen = set()
    for vec, starts in vectors.items():
        to = onsets + vec[0]
        tp = pitches + vec[1]
        hit = []
        for k in range(n):
            if (to[k], tp[k]) in index:
                hit.append(k)
        if len(hit) < min_size:
            continue
        pattern = tuple(pts[k] for k in hit)
        if pattern in seen:
            continue
        seen.add(pattern)
        translators = {vec}
        for w in (
            (int(onsets[m] - pattern[0][0]), int(pitches[m] - pattern[0][1]))
            for m in range(n)
        ):
            if w == (0, 0):
                continue
            if any((p[0] + w[0], p[1] + w[1]) not in index for p in pattern):
                continue
            translators.add(w)
        occurrences = tuple(
            tuple((p[0] + w[0], p[1] + w[1]) for p in pattern)
            for w in sorted(translators)
        )
        results.append((pattern, tuple(sorted(translators)), occurrences))
    return results


@dataclass
class Pattern:
    points: tuple
    vectors: tuple
    occurrences: tuple
    kind: str = "exact"
    quality: float = 0.0
    extra: dict = field(default_factory=dict)


def _rhythm(points):
    ons = [p[0] for p in points]
    return tuple(ons[i + 1] - ons[i] for i in range(len(ons) - 1))


def _pitch_shifts(points):
    pits = [p[1] for p in points]
    return tuple(pits[i + 1] - pits[i] for i in range(len(pits) - 1))


def classify(pattern, vectors, occurrences):
    """Sub-classify a SIATEC output into the report's pattern classes.

    Priority: exact (zero pitch shift) → transposed (one constant shift) →
    sequence (strictly monotone pitch shifts across 3+ distinct occurrences)
    → rhythmic (rhythm held while pitch varies).
    """
    shifts = sorted({v[1] for v in vectors})
    if len(shifts) >= 2:
        kind = "sequence"
    elif 0 in shifts:
        kind = "exact" if len(shifts) == 1 else "mixed"
    elif len(shifts) == 1:
        kind = "transposed"
    else:
        kind = "sequence"
    if (
        kind == "rhythmic"
        and _rhythm(pattern)
        and all(_rhythm(occ) == _rhythm(pattern) for occ in occurrences)
        and len({v[0] for v in vectors}) > 1
    ):
        kind = "rhythmic"
    return kind


def _compactness(pattern, vectors):
    """Quality proxy: longer, denser, more-translated patterns rank first."""
    if len(pattern) < 2:
        return 0.0
    span = pattern[-1][0] - pattern[0][0] or 1
    return round((len(pattern) / span) * len(vectors) * len(pattern), 6)


def _ostinato(points):
    iois = _rhythm(points)
    found = []
    for length in (1, 2, 3, 4, 6, 8):
        if not iois:
            break
        i = 0
        while i < len(iois):
            cyc = iois[i : i + length]
            if len(cyc) < length:
                break
            count = 1
            j = i + length
            while j + length <= len(iois) and iois[j : j + length] == cyc:
                count += 1
                j += length
            if count >= 3:
                found.append(
                    {"cycle": list(cyc), "start_ioi": i, "repeats": count}
                )
                i += length * count
            else:
                i += length
    return found


def _mirror_candidate(pattern):
    """Intervals symmetric about a pitch axis ⇒ mirror candidate."""
    shifts = _pitch_shifts(pattern)
    return bool(shifts) and set(shifts) == {-s for s in shifts}


def _retrograde_candidate(pattern):
    shifts = _pitch_shifts(pattern)
    return bool(shifts) and shifts == tuple(reversed(shifts))


def analyze(work, max_points=500):
    """Run the analyzer over one loaded Work. Deterministic output.

    `max_points` bounds the point cloud before SIATEC so the reports
    terminate; the ladder-budget value survives W6's per-tier decision
    (default 500: whole corpus in <1 min; W6 owns the final numbers).
    Ostinati read the same (subsampled) cloud.
    """
    points = extract_points(work, max_points=max_points)
    pats = []
    for pattern, vectors, occurrences in siatec(points, max_points=max_points):
        kind = classify(pattern, vectors, occurrences)
        pats.append(
            Pattern(
                points=pattern,
                vectors=vectors,
                occurrences=occurrences,
                kind=kind,
                quality=_compactness(pattern, vectors),
                extra={
                    "mirror": _mirror_candidate(pattern),
                    "retrograde": _retrograde_candidate(pattern),
                },
            )
        )
    ostinati = _ostinato(points)
    pats.sort(key=lambda p: (-p.quality, p.kind, p.points[:2]))
    by_kind = dict(Counter(p.kind for p in pats))
    return {
        "point_count": len(points),
        "patterns": pats,
        "ostinati": ostinati,
        "stats": {
            "patterns_total": len(pats),
            "by_kind": by_kind,
            "mirror_candidates": sum(1 for p in pats if p.extra["mirror"]),
            "retrograde_candidates": sum(1 for p in pats if p.extra["retrograde"]),
            "ostinato_cycles": len(ostinati),
        },
    }
