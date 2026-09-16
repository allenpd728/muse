"""Diff engine: deterministic sorted-onset pairing within a tick tolerance."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Mismatch:
    kind: str        # missing | extra | onset-drift | velocity-drift
    pitch: int
    onset_a: int
    onset_b: int | None = None
    part: str = ""

    def describe(self) -> str:
        if self.kind == "missing":
            return f"missing note p{self.pitch} @{self.onset_a} ({self.part})"
        if self.kind == "extra":
            return f"extra note p{self.pitch} @{self.onset_b} ({self.part})"
        return f"{self.kind} p{self.pitch} @{self.onset_a}→{self.onset_b} ({self.part})"


@dataclass
class DiffReport:
    recall: float
    precision: float
    matched: int
    total_a: int
    total_b: int
    mismatches: list = field(default_factory=list)

    def ok(self) -> bool:
        return self.recall == 1.0 and self.precision == 1.0


def _notes_flat(work):
    """(part_id, note) sorted by onset then pitch — deterministic.

    Robust to either IR layout (tools/muse_ir had -1/-2 sentinels; tools/ir
    uses is_rest/is_unpitched properties with pitch possibly None).
    """
    flat = []
    for p in work.parts:
        for n in p.notes:
            raw_pitch = n.pitch if n.pitch is not None else -1
            flat.append((p.id, n, raw_pitch))
    flat.sort(key=lambda x: (x[1].onset, x[2], x[1].voice or 0))
    return [(pid, n) for pid, n, _ in flat]


def diff(work_a, work_b, tolerance_ticks: int = 0) -> DiffReport:
    """Pair notes between two works; recall/precision plus a mismatch list.

    Two paths, chosen because the chain's own call is ``tolerance_ticks=0``
    (exact reconstruction) and that case need not search:

    * **tolerance == 0** — an exact match is fully determined by
      ``(pitch, onset)``, so a bucket lookup pairs in O(n_a + n_b). The
      previous implementation scanned every unmatched ``b`` note for every
      ``a`` note, which is O(n_a x n_b): Beethoven 9 (239,459 notes) exceeded
      15 minutes and had to be skipped by the chain's budget gate. Note that
      the key is **pitch and onset only** — parts are not compared, matching
      the tolerance>0 path (part is reported, never matched on).
    * **tolerance > 0** — unchanged nearest-onset-within-tolerance search.

    Both paths are behaviour-identical: same pairing, same counts, same
    mismatch list (see ``test_muse_diff.py`` and the differential test).
    """
    if tolerance_ticks == 0:
        return _diff_exact(_notes_flat(work_a), _notes_flat(work_b))
    return _diff_within_tolerance(work_a, work_b, tolerance_ticks)


def _diff_exact(a, b) -> DiffReport:
    """O(n_a + n_b) exact pairing on (pitch, onset).

    Tie behaviour matches the previous linear scan: notes are matched in
    ``a`` order, and among equal keys the **lowest ``b`` index** wins (the
    old loop kept the first strictly-better candidate, and equal onsets never
    compare strictly better). ``b`` is sorted by onset, so equal keys are
    contiguous and ascending — a FIFO bucket reproduces that order exactly.
    """
    from collections import deque

    def pitch_of(note):
        return note.pitch if note.pitch is not None else -1

    buckets = {}
    for j, (pb, nb) in enumerate(b):
        buckets.setdefault((pitch_of(nb), nb.onset), deque()).append(j)

    matched = 0
    mismatches = []
    for pa, na in a:
        bucket = buckets.get((pitch_of(na), na.onset))
        if bucket:
            j = bucket.popleft()
            pb, nb = b[j]
            matched += 1
            # onsets are equal by construction, so onset-drift is impossible here
            if na.velocity is not None and nb.velocity is not None and na.velocity != nb.velocity:
                mismatches.append(Mismatch("velocity-drift", na.pitch, na.onset, nb.onset, pa))
        else:
            mismatches.append(Mismatch("missing", na.pitch, na.onset, part=pa))

    leftovers = sorted(j for bucket in buckets.values() for j in bucket)
    for j in leftovers:
        pb, nb = b[j]
        mismatches.append(Mismatch("extra", nb.pitch, 0, nb.onset, pb))

    total_a, total_b = len(a), len(b)
    recall = matched / total_a if total_a else 1.0
    precision = matched / total_b if total_b else 1.0
    return DiffReport(recall, precision, matched, total_a, total_b, mismatches)


def _diff_within_tolerance(work_a, work_b, tolerance_ticks: int) -> DiffReport:
    """Greedy sorted-onset pairing; both walks advance monotonically."""
    a = _notes_flat(work_a)
    b = _notes_flat(work_b)
    unmatched_b = set(range(len(b)))
    mismatches = []
    matched = 0

    for pa, na in a:
        pa_pitch = na.pitch if na.pitch is not None else -1
        best = None
        for j in list(unmatched_b):
            pb, nb = b[j]
            pb_pitch = nb.pitch if nb.pitch is not None else -1
            if pa_pitch != pb_pitch:
                continue
            if abs(na.onset - nb.onset) <= tolerance_ticks:
                if best is None or abs(na.onset - nb.onset) < abs(na.onset - b[best][1].onset):
                    best = j
        if best is not None:
            pb, nb = b[best]
            unmatched_b.discard(best)
            matched += 1
            if na.onset != nb.onset:
                mismatches.append(Mismatch("onset-drift", na.pitch, na.onset, nb.onset, pa))
            if na.velocity is not None and nb.velocity is not None and na.velocity != nb.velocity:
                mismatches.append(Mismatch("velocity-drift", na.pitch, na.onset, nb.onset, pa))
        else:
            mismatches.append(Mismatch("missing", na.pitch, na.onset, part=pa))

    for j in unmatched_b:
        pb, nb = b[j]
        mismatches.append(Mismatch("extra", nb.pitch, 0, nb.onset, pb))

    total_a, total_b = len(a), len(b)
    recall = matched / total_a if total_a else 1.0
    precision = matched / total_b if total_b else 1.0
    return DiffReport(recall, precision, matched, total_a, total_b, mismatches)
