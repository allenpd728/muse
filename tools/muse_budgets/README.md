# tools/muse_budgets — C3 budgets engine

Era/style budget suggestions per issue #175, turned *measured* ranges into
the seed schema's sanctioned defaults (C1 downstream, C2 wires in via
`muse_author.author._propose`).

## Corpus audit

- **baroque:** measured on music21's public-domain `bach` corpus (192
  accessible chorales, 93 measured IOI-spread values). Bound: pstdev ≤0.65.
  Provisional = False.
- **classical, romantic:** provisional defaults; the delta-analysis plan's
  Vienna 4x22 / Batik / Magaloff corpora aren't reachable from this
  sandbox (network-restricted; GitHub search returns nothing, not a
  scope block). Uplink is a recognized follow-up (C5 in the pipeline's
  sub-task list).

## API

```python
from muse_budgets import budgets, suggest
suggest("baroque")  # {"tempo_bpm"…min/max, dynamics range, chord_spread bound}
suggest("romantic")  # provisional defaults
```

## Tests

`cd tools/muse_budgets && python -m pytest` (4 tests, <1 s).

## Follow-ups

The provisional eras need measured data — that's C5 (Baroque-delta
measurement) and the delta plan's Vienna/Batik upload.
