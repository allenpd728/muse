# W7 — Mockup schema v0 (design doc, scaffold)

**Phase 0 — Analysis workbench (sub-task). Status: scaffold.**

## Purpose

L1 cannot run without the mockup session-file schema. This sub-task drafts
it from delta-analysis evidence + the spike JSONs, validated through W4.
The schema covers the full DNA vocabulary: tempo map, dynamic curve,
per-note offsets (chord spread etc.), articulation/balance, with a filed
transition from the spike cycle.

## Dependencies

- **Upstream:** W4 (defined-ish draft; may overlap with W-series);
  delta-analysis docs ([../mockup-delta-analysis.md](../mockup-delta-analysis.md));
  spike artifacts ([../spike/](../spike/) JSONs).
- **Downstream:** L1 (scheme it validates/consumes).

## Scope (pin in draft)

- **Inputs:** delta-analysis measured ranges; spike mockup JSONs (v1–v3).
- **Outputs:** `docs/design/w7-mockup-schema.md` schema + W4-validated
  example.
- **Non-goals:** L1's generate/validate/fix loop (it consumes the schema).

## Open questions

- Whether expressive devices (chord spread, attack/release, swell) are
  first-class fields or free-form per-note numbers.

## Acceptance criteria (when promoted to draft)

- Schema file committed; example mockup validates via W4.
