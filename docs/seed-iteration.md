# Seed iteration walkthrough — bwv227.1

How to iterate on a seed: edit, validate, generate, probe, repeat. The
loop is the way seed work happens (see AGENTS.md §Seed iteration loop).

## 1. Edit

Open `seeds/bwv227.1.seed.yaml` in your editor. The seed declares the
interpretive space: tempo bounds, energy/density/variation parameters,
philosophy fields, variation points, and assertions.

Current example:

```yaml
params:
  tempo:
    min_bpm: 62
    max_bpm: 129
    default_bpm: 96
  energy: { level: 0.5, shape: arch }
  variation: { level: 1, points: [] }
assertions:
  register: { part: P4, min: C2, max: C4 }
  tempo_bounds: { min_bpm: 60, max_bpm: 130 }
```

Change something — say, widen the tempo bounds:

```yaml
  tempo: { min_bpm: 50, max_bpm: 150, default_bpm: 96 }
```

## 2. Validate

```bash
python3 tools/muse_seed_cli/cli.py validate \
    seeds/bwv227.1.seed.yaml \
    corpus/bach/bwv227.1.mxl
```

Output:

```
OK  seed schema valid
OK  assertions pass on work
OK  seed validates against work
```

The validator checks: schema (required keys, types), assertions (register,
tempo bounds against the actual corpus work), and budgets (tempo range
against era-calibrated limits from C3's delta-analysis).

## 3. Generate the mockup

```bash
python3 tools/muse_mockup/cli.py corpus/bach/bwv227.1.mxl
```

Output:

```
OK  mockup written: corpus/bach/bwv227.1.mockup.json (279 notes)
```

The mockup is the session file: every pitched note with onset, duration,
velocity, and room for the DNA layer (chord spread, attack/release, swell).
Dense data, not sketches — that's the spike lesson.

## 4. Probe (when W-B1 lands)

Probes read artifacts the loop already produces:

- **Param diff** — what changed since the last seed revision?
- **Budget fit** — are the ranges inside the era's measured budgets?
- **Assertion pass/fail** — do the assertions hold?
- **Mockup coverage** — how many variation points did the mockup exercise?
- **Determinism probe** — same seed twice → same mockup bytes?
- **Score fidelity guard** — every score note present at the right onset?

The workbench page (W-B3) shows these per seed revision; quality checks
(W-B2) catch regressions the ear might miss.

## 5. Listen

Render the revision to audio and put your ear on it (W-B audio, #243):

```bash
python3 tools/muse_audio/cli.py corpus/bach/bwv227.1.mxl \
    --seed seeds/bwv227.1.v2.seed.yaml --label v2
# live LLM reading of the same seed (Gemini free tier):
python3 tools/muse_audio/cli.py corpus/bach/bwv227.1.mxl \
    --seed seeds/bwv227.1.v2.seed.yaml --label v2 --live
```

WAVs land in `docs/audio/` (session-local, regenerable); the committed
`docs/audio/manifest.json` is the workbench page's per-revision audio
index. The page plays v1 vs v2 side by side next to the growth diff —
"did this seed change do what I intended?" answered by ear, with the
probes as backup.

## 6. Iterate

Commit the seed revision; the workbench shows the probe history. Edit
again — the loop is the craft. The seed is the product's interpretive
layer; the mockup is its realization. The workbench makes both inspectable
per iteration.

## The commands in order

```bash
# 1. edit seeds/bwv227.1.seed.yaml (your editor)
# 2. validate
python3 tools/muse_seed_cli/cli.py validate seeds/bwv227.1.seed.yaml corpus/bach/bwv227.1.mxl
# 3. mockup
python3 tools/muse_mockup/cli.py corpus/bach/bwv227.1.mxl
# 4. probes (W-B1, tools/muse_probes)
# 5. listen (muse_audio; --live for the LLM reading)
# 6. commit, iterate
```
