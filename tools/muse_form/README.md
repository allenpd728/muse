# muse_form — F1 windowed compressibility/form-curve analyzer

Computes the **form curve**: slides a bar-ish window across a work,
measures pattern-density per window against the W3 analyzers' detectors
(exact/transposed/ostinato), and quantizes A/B/C per window
(A = repetitive/compressible, moderate B, C dense/novel). Bar-window
resolution borrows the meter map from the IR when present; otherwise
default beats × ppq. The curve is an evidence layer — its output never
becomes a generation target (caution gate per
itools/design/f1-form-curve.md).

## API

`form_curve(work, window_beats=2) -> FormCurve` — returns
`(work_id, ppq, window_ticks, windows)` where each window is
`(start, end, score, letter)`. `to_json()` serializes it.

Window resolution: bar count = meter's N beats if a meter map exists
(`p.meta.ppq` comes first); else `default_beats × ppq`. Window slides at
1 beat-tick to bar-oriented within the work's tick domain.

## Detection's three shipped analyzers (windowed invocation)
exact repeats, transposed repeats, ostinato (rhythm) — same classes as
W3's analyzer; aggregation goes windowed.

## Tests

`cd tools/muse_form && python3 -m pytest -q` — 5 passing,
single corpus file (bwv227.1), no network outside the corpus.
