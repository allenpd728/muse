# Lineage chain, growth measurement, and workbench trust surface — consolidated proposal

**Status:** tasks filed (2026-08-25, run=20260825-2247-qogi): S3.7
[#248](https://github.com/allenpd728/muse/issues/248), S5.1
[#249](https://github.com/allenpd728/muse/issues/249), L1.10
[#250](https://github.com/allenpd728/muse/issues/250), S3.8
[#251](https://github.com/allenpd728/muse/issues/251), G4
[#252](https://github.com/allenpd728/muse/issues/252), W-B9
[#253](https://github.com/allenpd728/muse/issues/253). Native blocked-by
relationships set per the table in §3.

Written to resolve a real conflict between two independently-drafted docs
before either lands, and to turn the resolution into filed tasks rather
than a third pitch document. Revised against the repo at commit `48453d4`
(dev, 2026-08-25) before filing — every file/field claim below was
verified by reading the code.

**Supersedes/reconciles:**
- `proposal-interpretation-chain.md` (earlier proposal — seed-lineage
  chain, complexity-scaled expansion, workbench framing)
- `l1-typed-provider-and-slice.md` (L1.5–L1.9 — typed provider contract,
  §2 "provenance" object)

(Neither source doc is in the repo; both were pre-filing drafts.)

**Touches (existing, unmodified structure otherwise):**
`docs/design/s3-seed-format/SPEC.md`, `docs/design/seed-growth-harness.md`,
`docs/design/seed-workbench.md`, `docs/design/s5-container-manifest.md`,
`tools/muse_mu/manifest.py`, `tools/muse_mockup/schema/v1.json`,
`tools/muse_distill/distill.py`, `tools/muse_grow/grow.py`.
`tools/muse_provider/provider.py` and `tools/muse_generate/generate.py`
are deliberately untouched (§2.6).


---

## 0. Why this doc exists

Two proposals each invented a `provenance` object to solve adjacent
problems, and they disagree:

| | seed-lineage chain | L1.5 §2 (typed provider doc) |
|---|---|---|
| Lives in | seed YAML / `manifest.json` `provenance` | `tools/muse_mockup/schema/v1.json`'s new `provenance` object |
| Fields | `extends` (hash of parent artifact), `operation` (tool@version) | `run_id`, `provider`, `model_version`, `seed_hash`, `status` |
| Links to prior artifact via | hash of the whole parent artifact | `seed_hash` only |

Both are correct in isolation. Filed separately, they ship two
incompatible provenance shapes with overlapping intent — a maintenance
trap the moment someone tries to walk a lineage from directive to seed to
mockup and finds the hop from seed→mockup uses a different vocabulary than
the hop from seed→seed.

**The resolution below is one decision, not two designs**, and everything
after §1 is just wiring that decision into the existing docs and tools.


---

## 1. The resolved model (read this first, it's the whole idea)

One chain, two hops, one hash convention:

```
directive (text)
    │  extends: absent (root — see directive note below)
    ▼
seed v1  ──(author/propose, C1/C2)──┐
    │  extends: <64-hex sha256 of the directive, if any>          │
    │                                                              ▼
    │                                                    mockup (L1)
    │                                                        provenance.seed_hash:
    │                                                          <64-hex sha256 of seed v1>
    │                                                          = the SAME hash seed v1
    │                                                            carries as its identity
    │                                                            when referenced forward
    ▼
seed v2  (distilled from the mockup, L4)
    extends: <64-hex sha256 of the mockup file that produced it>
```

- **`extends`** (seed/manifest `provenance`) is the hash of whatever
  artifact this one was produced *from* — a directive, a prior seed, or a
  mockup. It is how you walk backward through an authoring chain.
- **`seed_hash`** (mockup `provenance`) is not a separate concept — it is
  the same hash value the *next* seed revision would put in its own
  `extends` field if it were distilled from that mockup. The mockup's
  `provenance.seed_hash` names its parent going backward (seed→mockup); a
  future seed's `extends` names its parent going backward (mockup→seed).
- **Hash convention — bare 64-hex, no prefix.** The exact digest shape
  `tools/muse_mu/manifest.py`'s `_validate_hashes` already validates
  (`len(digest) == 64`, parses as hex), produced by its existing
  `sha256_hex()`. An earlier draft of this proposal used a `sha256:<hex>`
  prefix; that prefix exists nowhere in the repo (manifest hashes and the
  audio manifest both store bare hex), so adopting it would have invented
  a second convention while claiming to reuse the first. Bare hex it is.
- **What gets hashed — committed file bytes, not a canonical form.**
  `extends`/`seed_hash` is the SHA-256 of the parent artifact's committed
  file bytes. Seeds are author-edited YAML and mockups are
  insertion-ordered JSON, so a "canonical serialization" would be fragile
  machinery out of proportion to the guarantee needed. Lineage points
  backward at immutable committed revisions: editing a parent produces a
  new revision (a new link), which is exactly what the chain should
  detect. Re-hashing the committed file is the whole verification step.
- **Directive root: deferred.** Directives are not files anywhere yet —
  there is nothing to hash. Root seeds omit `extends`; chain v1 covers
  seed↔seed and seed↔mockup hops only.
- **`operation` vocabulary:** lowercase tool dir name `@` semver
  (e.g. `muse_distill@1`, `muse_author@1`). Informational only —
  chain-walk never verifies it, and it must never be load-bearing for
  integrity.
- **Mockup persistence is a precondition for the mockup hop.** Mockups
  are not persisted anywhere today (`tools/muse_grow` runs the stand-in
  in memory and writes nothing). The growth loop must commit the
  producing mockup alongside each committed seed revision (scoped under
  S3.8, §3) or every mockup hop is unverifiable. "Parent missing" is a
  first-class verify result, distinct from "parent hash mismatch".
- **What does NOT get unified:** `run_id`, `provider`, `model_version`,
  `status` (L1.5 §2/§3) are generation-run metadata, not lineage. They
  stay exactly where L1.5 put them, in the mockup schema's `provenance`
  object. Only the *lineage pointer* (`seed_hash`) is tied to the
  seed-side `extends` convention — the rest of L1.5's design is
  unaffected.
- **What the chain proves and doesn't:** the chain proves an artifact's
  lineage wasn't forged or silently swapped. It says nothing about
  musical validity — that's still S3.5 assertions + the workbench's
  probe/quality tables (`seed-workbench.md`), which are unchanged by this
  proposal and should stay the separate mechanism they already are.

This model requires no `format_version` bump (additive optional fields on
both sides) and no new top-level task category in `docs/design/index.md`.


---

## 2. Concrete edits, file by file

### 2.1 `docs/design/s3-seed-format/SPEC.md` — a decisions-log entry, not a scaffold edit

The live S3 spec is `SPEC.md` (written as a dated decisions log:
"Philosophy (S3.3, 2026-08-23)", "Variation points (S3.4, …)", "Era
budget (2026-08-24, #236)"); `s3-seed-format.md` in the same directory is
the Phase 1 scaffold. Add a new decisions-log entry — matching the
existing format and citing the S3.7 issue (#248) — sanctioning two new
optional seed `provenance` fields:

```yaml
provenance:
  source: corpus/bach/bwv227.1.mxl
  author: <name>
  ai_assisted: true
  extends: <64-hex sha256 of parent artifact's committed bytes>   # NEW, optional; omitted for a root seed
  operation: muse_distill@1                                       # NEW, optional; tool@version that produced this revision
```

(The example uses the seed-level vocabulary — `author`, `ai_assisted`,
`license_ref` per S3.3 and `tools/muse_seed/philosophy.py` — not the
manifest-level `ai_involvement` enum. The two surfaces differ; an earlier
draft mixed them.)

Cross-reference `seed_hash` in the mockup schema (§2.2 below) as the same
hash, one hop over. This makes S3 the single place both docs point to
instead of each defining its own vocabulary.

### 2.2 `tools/muse_mockup/schema/v1.json` — narrow, and delete the vestige

L1.5 §2 proposed adding a full `provenance` object to the mockup schema.
Keep it, with one change: `seed_hash` is documented as "the SHA-256 this
mockup's seed carries as its identity — the value the next distilled
revision puts in `extends`" (i.e., point at §1, don't redefine hashing).

The schema's `"seed"` property (embedded full seed "for provenance") is
**optional and vestigial**: nothing writes it (`dump_mockup()` emits no
`seed` key; the `Mockup` dataclass has no seed field), and grep across
`tools/` finds no producer or consumer outside `test_mockup_schema.py`,
which hand-constructs one. Drop it in the same change that adds
`provenance.seed_hash` — same guarantee, one hash instead of a full copy.
There is **no `mockup_schema_version` mechanism** (v1.json has no version
field; `docs/design/w7-mockup-schema.md` is a Phase 0 scaffold) — don't
invent one for this: only `muse_mockup/schema.py` (plus two spike
scripts) consumes the schema, and an optional `provenance` property is
purely additive. This resolves the consumer-grep question an earlier
draft left open (formerly §5).

### 2.3 `tools/muse_mu/manifest.py` — additive field, one place

`PROVENANCE_KEYS` currently:

```python
PROVENANCE_KEYS = frozenset({
    "source", "tools", "ai_involvement", "author", "license_ref",
})
```

Add `extends`, `operation`. Both optional (no `_validate_provenance`
requirement change beyond accepting the keys and, if `extends` is
present, checking it with the exact bare-64-hex digest check already
written in `_validate_hashes` — extract or share the check, don't
duplicate the logic).

Sync rule: `docs/design/s5-container-manifest.md` already states the
manifest provenance field set mirrors the S3.3 philosophy provenance
where they overlap — that is the mechanism keeping `extends`/`operation`
consistent across both surfaces. S5.1 adds one sentence: at pack time,
manifest-level `extends`/`operation` are copied from the packed seed's
provenance.

### 2.4 `docs/design/seed-growth-harness.md` — instrumentation, not a new doc

Add to the harness's `grow.py` description: log wall-clock
`expansion_time_ms` per `operation` tag (§1) against
`(variation_point_count, note_count)` for each `grow_one(work, seed)`
call. This is the complexity-scaling idea from the earlier proposal,
scoped as **measurement riding on the harness that already exists**,
producing data toward an eventual expansion-cost estimate — not a new
report generator, not a new subsystem. In-repo precedent for keying an
operational decision on note count: `tools/muse_chain/chain.py`'s
`DIFF_BUDGET_NOTES` / `RENDER_BUDGET_NOTES` — hard gates that refuse
work over 30k notes at the diff/render stage. (They are gates, not
scaling curves; the harness logging stands on its own as the first
actual cost data.)

### 2.5 `docs/design/seed-workbench.md` — two sentences, no new doc

Add a row to the existing probe table:

| Probe | Question it answers | Source |
|---|---|---|
| **Lineage check** | Does this seed revision's `extends` resolve to a real, hash-matching parent artifact? | `provenance.extends` (§1), via S3.8's walker |

And one sentence under "Iteration history": each committed seed
revision's row can now show whether its lineage verifies —
verified / broken / missing, reusing S3.8's three-state report —
distinct from whether its assertions pass. The workbench already
separates regression from growth; this adds a third, orthogonal signal
(integrity) to the same surface without new UI concepts.

### 2.6 `tools/muse_provider/provider.py`, `tools/muse_generate/generate.py`

Unchanged from L1.5's own scoping (its §1, §3, §4, §5, and the
Phase A→F sequencing). This proposal does not alter L1.5's
typed-contract design, failure taxonomy, or sequencing — only the shape
of the `provenance` object it introduces in schema v1.json, per §2.2.

One adjacent scope line for L4: `tools/muse_distill/distill.py`'s
`seed_revision()` already stamps `provenance: {distilled_from: work_id,
note_count}` — it is the natural emitter of `extends` (hash of the
producing mockup) and `operation: muse_distill@<v>` on distilled
revisions. Scoped under S3.8, since the chain-walk needs it.


---

## 3. Tasks (filed 2026-08-25, run=20260825-2247-qogi)

| Task | Issue | Scope | Blocked by | Blocks | Size |
|---|---|---|---|---|---|
| **S3.7 — Lineage fields on seed provenance** | [#248](https://github.com/allenpd728/muse/issues/248) | `extends`/`operation` decisions-log entry in `s3-seed-format/SPEC.md` + C1 validator acceptance, per §1 hash convention | none | #249, #250, #251, #252 | S |
| **S5.1 — Manifest provenance lineage fields** | [#249](https://github.com/allenpd728/muse/issues/249) | `PROVENANCE_KEYS` += `extends`, `operation`; digest validation shared with `_validate_hashes`; pack-time copy sentence in `s5-container-manifest.md` | #248 | #251 | S |
| **S3.8 — Chain-walk/verify helper** | [#251](https://github.com/allenpd728/muse/issues/251) | walk `extends` across seed revision files + persisted mockups; three-state per-hop report (verified / mismatch / missing); growth loop persists producing mockups; `muse_distill` stamps `extends`/`operation` | #248, #249 | #253 | M |
| **L1.10 — Mockup `provenance.seed_hash`** | [#250](https://github.com/allenpd728/muse/issues/250) | optional `provenance` object in mockup schema v1 per §2.2; delete vestigial optional `"seed"` property (zero consumers — verified) | #248 | — | M |
| **G4 — Growth harness expansion-time logging** | [#252](https://github.com/allenpd728/muse/issues/252) | `expansion_time_ms` keyed by `operation` against `(variation_point_count, note_count)` in the growth report JSON | #248 | corpus-ladder cost report (future, not yet scoped) | S |
| **W-B9 — Workbench lineage probe** | [#253](https://github.com/allenpd728/muse/issues/253) | "Lineage check" row in the probe table; verified/broken/missing surfaced per revision in iteration history | #251 | none | S |

Numbering notes (why not the numbers in earlier drafts of this doc):
**S3.6** was already taken ("Example seed", #147, closed); **W-B5**
likewise ("Workbench runner + allow-list gate", #232, closed — W-B6/7/8
are #233–235); **L1.6b/L1.9b** used a b-suffix with no repo precedent —
the mockup-provenance task takes **L1.10** to avoid squatting on the
typed-provider doc's planned L1.5–L1.9 range, and the harness-logging
task moves to the growth harness's own series as **G4** (G1–G3 are
#203–205). Only #248 carries `status:available`; the rest become
available as their blockers close, per TASK_WORKFLOW.md.

**L1.5's own task table (L1.5–L1.9, typed contract/failure taxonomy/
event_chain wiring) is unchanged and should be filed as originally
scoped**, with one edit: its provenance task should reference S3.7's
hash convention for `seed_hash` instead of defining its own, per §2.2.
Sequencing: **S3.7 (#248) and S5.1 (#249) land before the L1.5-series
provenance task is implemented** (not necessarily before it's filed) so
it doesn't have to be revised after the fact.


---

## 4. What's explicitly out of scope here

- Any change to L1.5's typed `Provider` contract, failure taxonomy, or
  `event_chain()` wiring sequencing — that design is sound and unrelated
  to the provenance-shape conflict.
- A new expansion-cost estimator/report tool — §2.4 only proposes
  logging; building the estimator is a follow-on task once data exists.
- Any `format_version` bump — every field added here is optional and
  additive, consistent with `FORMAT_SPEC.md` §7's semver policy. (There
  is likewise no mockup-schema version mechanism to bump; §2.2.)
- Re-litigating the workbench's existing regression-detection design
  (`seed-workbench.md`'s probe/quality tables) — lineage is a new, third
  signal alongside it, not a replacement.
- Directive-root hashes — deferred until directives exist as files (§1).
- YAML/JSON canonicalization for hashing — rejected; committed file
  bytes are the hash input (§1).


---

## 5. Open question — resolved

An earlier draft asked whether dropping the mockup schema's embedded full
`"seed"` object breaks consumers (`muse_compare`, `muse_explorer`). The
grep is done: **zero consumers.** Nothing writes the field
(`dump_mockup()` has no `seed` key; the `Mockup` dataclass has no seed
field) and nothing reads it outside `test_mockup_schema.py`, which
hand-constructs one. L1.10 (#250) drops it in the same commit that adds
`provenance`, with no transition period.
