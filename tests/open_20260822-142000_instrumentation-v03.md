# Test spec — #76: schema v0.3 structured instrumentation

**Source task:** #76 (orchestral instrumentation depth: spec §2.6 v0.3 amendment
+ `schema/renditions.schema.json` + `examples/full.muse.json` r.chamber)
**Code under test:** `schema/renditions.schema.json` structured
instrumentation entries; spec/schema vocabulary parity.

## Behaviors to verify

- **Structured entries validate:** `r.chamber` in the full example passes the
  root schema (covered by the harness examples scan — pinned there).
- **Free-text entries still validate:** `r.synthwave`/`r.quartet` prove the
  anyOf keeps strings legal (harness examples scan covers; pin explicitly).
- **Rejection paths:**
  - structured entry missing `name` → rejected
  - `program` outside 0–127 → rejected
  - `divisi` value outside the allowed/required enum → rejected
  - unknown property on a structured entry (sealed objects) → rejected
  - unknown *technique key* (e.g. `techniques.strumming`) → rejected
    (`additionalProperties: false` on `techniques`)
  - unknown technique *name* within a known key → **accepted** (spec:
    additive vocabulary, ignore-and-record; pin that schema does not over-reject)
- **Spec ↔ schema parity:** the technique keys named in §2.6's vocabulary
  paragraph (`divisi`, `mute`, `bowing`, `breath`, `production`) match the
  `techniques` properties in the schema — parse the spec's bold-marked key
  names, assert set-equality (same pattern as role-vocabulary parity).
- **Full example guards:** r.chamber exercises divisi + at least one mute or
  bowing technique (guards against example edits quietly dropping the v0.3
  surface).

## How to run

New `tests/instrumentation.test.mjs` (schema-level acceptance/rejection) plus
a parity block in the same file; `npm test` picks it up. Note: harness
convention for rejection channels (`schema` channel sidecars) applies if
fixtures land under `examples/invalid/`.
