# muse_study — R3 conductor-training study scripts + survival feedback

Precomposed directive sequences (study scripts) keyed to well-known
interpretive issues, plus a per-step survival check that answers *"did
this directive actually do what was asked?"* — how the conductor's ear
gets trained without live musicians. Builds on `muse_rehearse` (R2).
Design: [docs/design/r1-rehearsal-directives.md](../../docs/design/r1-rehearsal-directives.md)
§What R3 builds.

## Usage

```bash
python3 tools/muse_study/cli.py list
python3 tools/muse_study/cli.py run <script> <seed.yaml>
```

`run` compiles each directive step in sequence (the running candidate
carries forward, so steps compound — that's the drill) and reports, per
step, whether the directive's knob landed (`moved`), didn't (`flat`),
or moved the wrong way (`drifted`).

## Survival is measured at the seed-param level

`check_survival` maps each verb to the seed knob it should move
(`VERB_MEASURES`) and compares base vs candidate seed params. The
render/mockup level is **stand-in-blocked**: the deterministic stand-in
produces a flat mockup regardless of seed, so "did it survive the
render" is only meaningful once the real L1 generate loop lands (L1.11,
#276 — the `MOCKUP_FN` swap). The interface is ready for it; the
verdicts today are seed-level.

## The scripts

| Script | Issue it drills |
|---|---|
| `quiet-the-bass` | bass dominates the texture ("quiet the cellos into the development") |
| `phrase-the-pickup` | flat anacrusis; no arch into the downbeat |
| `tempo-architecture` | tempo wanders; the form loses its spine |
| `rubato-calibration` | onset-offset spread mechanical or soupy |

New scripts are added to `SCRIPTS` in `study.py` — a name, the issue
text, and a list of directive steps using the R2 grammar.

## Tests

`cd tools && python -m pytest muse_study -q`. Spec:
[tests/closed_20260826-113000_r3-study-scripts.md](../../tests/closed_20260826-113000_r3-study-scripts.md).

## Dependencies

`muse_rehearse` (the directive compiler), `muse_seed` (params/budgets),
`muse_ir` (work loading), `muse_distill`/`muse_grow` (interpretation
fields + the stand-in pin the render-level check will use).
