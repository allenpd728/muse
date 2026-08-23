# Checkpoint — the egg model, the subtraction method, and the spike state

**Date:** 2026-08-23. **Status:** spike in progress, architecture settled.
This document consolidates the design language and empirical state so a fresh
conversation/sandbox can resume without loss. Read this first, then
[README.md](../README.md), [FORMAT_SPEC.md](../FORMAT_SPEC.md),
[prior-art-spike.md](prior-art-spike.md), and this directory's
[spike/](spike/) artifacts.

## 1. The egg model (settled metaphor)

The `.mu` file is an **egg**:

| Component | Egg | Contents |
|---|---|---|
| **Score** | Shell + white | The fixed work — MusicXML packaged. Structure and protection. |
| **Prompt (seed)** | Yolk | The concentrated fuel — interpretive philosophy, expression budgets, sanctioned space. Small relative to the whole, dense. |
| **Manifest** | The label | Plaintext rights, provenance, AI disclosure. The only human-readable member. |

Two processes act on the egg — **they are different in kind, not degree:**

| Process | What it does | Nature |
|---|---|---|
| **Unzip** (decode) | Egg → its contents, laid out. Score unpacked, seed unpacked. | **Pure mathematics.** Lossless, identical everywhere, invertible, no intelligence. The deterministic player. |
| **Grow** (session work) | Egg contents → the chick. Score + yolk-fuel grown into a living performance. | **Guided by intelligence.** Irreversible, creative, varies within sanctions. The LLM conductor. |

Earlier drafts conflated these as "expansion." Keep them separate: unzip
reveals what is inside the egg; grow turns the egg into the bird.

The **mockup is the chick at a checkpoint** — the grown organism, fully
formed (tempo map, per-note expression, balance), before it sings. The
renderer lets it sing.

## 2. The subtraction method (the mockup's empirical foundation)

Do not invent the mockup format top-down. **Derive it:**

```
artistic DAW session (a human producer's finished mockup)
  −  the same work's MusicXML/MIDI (the raw score)
  =  THE DELTA — exactly the data a mockup must carry
```

Every field in the mockup schema should exist because a real artistic session
contained it and the raw score did not. Evidence before invention — the same
discipline as the corpus ratchet.

Candidate sources: DAWproject files (Bitwig/Studio One open format — see
[prior-art-spike.md](prior-art-spike.md) §Interchange), Ardour sessions,
composer-shared mockups for works that also exist as MusicXML. Ideal: one
work in three forms (MusicXML + MIDI + DAW session). The triple diff is
`docs/mockup-delta-analysis.md` (task pending).

## 3. Spike state (what the chorale taught us)

Artifacts: [spike/](spike/) — WAVs, mockup JSONs, listener page
(`index.html`, deploys on the dev-branch QA site).

| Round | What varied | Founder verdict |
|---|---|---|
| A1/B1 GM choir | interpretation, GM render | "slight difference, not very apparent" — GM masks interpretation |
| A2/B2 SSO strings | interpretation, sample render | "slightly more musical nuance but not sculpted" — per-note layer missing |
| A2/B3 SSO strings | mockup v2: per-note sculpting | "very lightly more musical, not by much" — interpretation too timid and/or sample ceiling |

**Standing hypotheses (unresolved, in priority order):**

1. **Interpretation too timid.** Mockups so far are conservative (±15% tempo,
   gentle swells). A bold reading would make bigger rhetorical moves.
2. **Test material too small.** Nine measures of homophonic chorale gives
   interpretation almost nothing to sculpt — no drama, no texture shifts.
   The Schubert finale or Byrd polyphony are the honest test beds.
3. **Sample ceiling.** SSO sustains have no true legato transitions; singing
   between notes is what free samples lack. Commercial libraries may be the
   event-tier answer (budget decision, deferred).

**Spike status: conditional pass.** The mockup vocabulary and the pipeline
work; interpretation depth unproven. Next spike round: bold interpretation
on dramatic material, informed by the subtraction method's findings.

## 4. Environment persistence (sandbox rebuild runbook)

This sandbox is ephemeral. **Everything that matters is either in the repo
or re-acquirable in minutes:**

| Asset | Location | Persistent? |
|---|---|---|
| WAVs, mockups, listener page | `docs/spike/` in repo | ✅ committed |
| Design docs | repo root + `docs/` | ✅ committed |
| Corpus | `corpus/` in repo | ✅ committed |
| Sample libraries (SSO 1.4GB, VSCO2 2.3GB) | `/tmp/sso`, `/tmp/vsco2` | ❌ re-download |
| Spike renderer `/tmp/render_sso.py` | `/tmp` | ❌ **must graduate to `tools/`** |
| Extract script `/tmp/extract.py` | `/tmp` | ❌ **must graduate to `tools/`** |
| MIDI builder `/tmp/build_midi.py` | `/tmp` | ❌ **must graduate to `tools/`** |

**Rebuild recipe (fresh sandbox):**

```bash
# samples (pick one; SSO is what the spike renders used)
curl -sL https://github.com/peastman/sso/archive/refs/heads/master.zip -o sso.zip
unzip -q sso.zip -d /tmp/sso
# VSCO 2 CE (downloaded but unused — ships without SFZ mappings)
curl -sL https://github.com/sgossner/VSCO-2-CE/archive/refs/heads/master.zip -o vsco2.zip

# system deps
sudo apt-get install -y unzip fluidsynth fluid-soundfont-gm
pip install numpy soundfile mido
```

**Rule going forward:** any script that produces a committed artifact lives
in the repo (`tools/`), not in `/tmp`. Samples are never committed — the repo
carries references (library, version, URL, license); renderers fetch and
cache at run time.

## 5. What carries forward from the spike

- The mockup needs a **per-note expression layer** (v2 proved the vocabulary:
  onset offsets, attack/release, swell curves, legato overlap) — and the
  subtraction method will tell us what else it needs.
- The seed needs **expression budgets** — the permission layer bounding how
  much sculpting a mockup may apply (introduced in mockup v2).
- Renderer quality gates audibility of interpretation — tiers are not
  optional (GM masked everything; SSO made the ritardando audible).
- The listener page (`docs/spike/index.html` → QA deploy) is the standing
  quality gate — future rounds add cards, they don't replace the page.
