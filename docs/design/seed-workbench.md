# Seed workbench — design doc scaffold

**Phase 3 — seed authoring (proprietary). Status: scaffold (awaiting sign-off).**

## Purpose — what the explorer is *for*

The current explorer (`docs/explorer/`) answers "what's in the corpus."
That was the right first surface: the known-answer pins made visible. But
the founder's real loop is **seed iteration**: author a seed, generate a
mockup, evaluate it by ear and by probe, adjust, repeat. The workbench is
the same static QA surface, grown into that loop's instrument panel.

The seed is the product's interpretive layer (S3). The mockup (L1) is its
realization. The workbench makes both inspectable per iteration, with
probes that answer "did this seed change do what I intended?" and quality
checks that catch regressions the ear might miss on the first pass.

## The iteration loop it serves

```
seed (YAML)  →  validate (C1)  →  mockup (L1)  →  probes + quality checks
     ↑                                                    │
     └────────────  edit params / philosophy  ←───────────┘
```

Every probe reads artifacts the toolchain already produces; nothing new is
trained, nothing is generated beyond the existing mockup path.

## Probes (per seed iteration)

| Probe | Question it answers | Source |
|---|---|---|
| **Param diff** | What changed since the last seed revision? (tempo bounds, energy, density, variation level, philosophy fields) | seed YAML diff |
| **Budget fit** | Are the seed's ranges inside the era's measured budgets? Where do they sit (center / edge)? | muse_budgets (C3) |
| **Assertion pass/fail** | Do the seed's assertions hold against the work? (register, tempo_bounds, must_contain, form) | muse_assert (S3.5) |
| **Mockup coverage** | How many variation points did the mockup actually exercise? Any sanctioned-but-unused region? | L1 mockup vs S3.4 variation_points |
| **Delta curves** | How does the mockup's tempo/IOI shape compare to the source's and to the era norm? | W3 delta-analysis vocabulary |
| **Determinism probe** | Same seed twice → same mockup? (the LLM-free path must be byte-stable) | L1 generate ×2 |
| **Score fidelity guard** | The mockup never contradicts the score: every score note present at the right onset (W4 diff at tolerance 0 for fixed notes) | muse_diff |

## Quality checks (the "did I break something" tier)

| Check | Failure means |
|---|---|
| **Assertion regression** | a previously-passing assertion now fails |
| **Budget drift** | seed params moved outside era budgets without an explicit override note |
| **Coverage shrink** | mockup exercises fewer variation points than last iteration |
| **Philosophy identity trip** | a philosophy edit trips the identity guard without a license_ref |
| **Byte instability** | same seed produced different mockup bytes |

## Workbench surface (QA, static, dev-- deploy)

- **Per work:** seed editor view (YAML, validated on save client-side),
  current seed's probe panel (the table above, pass/fail + numbers),
  mockup player (when P2 lands; structure view today).
- **Iteration history:** each committed seed revision gets a row; probes
  recompute deterministically; diffs are between revisions.
- **No write path from the browser** — editing happens in the repo; the
  workbench is the read surface for what you committed. (A future C2
  authoring UI is a separate, proprietary task — this is QA, not authoring.)

## Proposed tasks (not started)

| Task | Scope | Blocked by |
|---|---|---|
| **W-B1 — Probe engine** | per-seed probe computation (param diff, budget fit, assertions, coverage, delta curves, determinism, fidelity guard) as a `tools/muse_probes/` package + JSON artifact | C1, C3, L1 (done) |
| **W-B2 — Quality-check gate** | the five regression checks as a pytest suite + runner registration | W-B1 |
| **W-B3 — Workbench page** | explorer view grown: seed panel, probe panel, iteration history rows | W-B1 |
| **W-B4 — Iteration loop docs** | the edit → validate → mockup → probe loop documented for the founder + agents (AGENTS.md section) | done (#188) — docs/seed-iteration.md |

W-B1 is the foundation; W-B2/W-B3/W-B4 decompose from it. Each fits one
agent run.

## Explicitly not (yet)

- Browser-side seed editing (authoring UI — C2's future task)
- LLM-in-the-loop probes (delta analysis produces design knowledge only)
- Audio playback (P2)
