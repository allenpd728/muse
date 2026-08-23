# Muse — Product Vision

**Revised 2026-08-23.** This revision supersedes the component model of the
original draft (kept in git history). The thesis stands; the architecture
changed.

## The idea

A `.mu` file is to a MusicXML score what a well-punched piano roll is to a
crude one: the same work, better encoded, so the existing machine produces a
better performance. Technology advancing hardware by changing only the
software.

MusicXML is the existing roll — the full score, verbose, uncompressed. Muse
compresses and adapts it into `.mu`: a portable, executable container holding
**two streams**:

- **The roll stream** — the fixed score. Our MusicXML: notes, structure,
  dynamics, compressed and packaged. Any deterministic player reads it and
  plays the work exactly, identically, everywhere. This is the baseline —
  our MIDI player — free, open, and what proves the format works.
- **The seed stream** — the interpretive space. What may vary, within what
  sanctions, guided by what philosophy. An LLM player reads the seed, bounded
  by the roll, and **brings the work to life**. This is the product.

The deterministic player is never the product — it is the root system, the
conformance proof, the free tier. The LLM player is the musician: the bloom.

## The conductor, not the cover

Interpretation in Muse is **conducting, not genre covers**. The seed stream
carries performance philosophy — tempo architecture, dynamic shaping,
articulation stance — as explicit, inspectable, licensed data. Wildly
different readings are valid when they satisfy the work's assertions: the
Gould/Bernstein case is in-spec by design. The encoder is the composer's
advocate, and advocacy includes the freedom to argue.

Because the seed stream is data, **different LLMs are different conductors**.
The same `.mu` interpreted by different models produces measurably different
performances — a controlled experiment in machine musicality. The format
preserves the differences; audiences decide which readings resonate.

## The event, not the stream

Muse's unveiling is a **performance event**, not an app launch. The precedent
is 1957's Illiac Suite and the 1962 Gould/Bernstein controversy: computer
music enters culture through public spectacle and public argument. The
question "can a machine conduct Beethoven?" fills seats. The controversy is
the coverage.

This changes the quality bar: the deterministic baseline only needs to be
correct; the LLM player's render must be **worth a concert hall** — sample
tier or better, expression fully dialed. The expansion may take minutes on a
workstation. That is fine. Performances are not notifications.

## The corpus and the Ninth

The format is proven against a fixed public-domain corpus: Bach chorales →
Byrd's Mass for Three Voices → Schubert's *Death and the Maiden* finale →
Beethoven's Fifth → **the complete Beethoven's Ninth**, which is the v1.0
conformance target. In 1980 the CD was sized for the slowest Ninth; the `.mu`
format is designed for the space of all of them.

## Business model

- **The format is open** (at launch): spec, reference player, conformance
  suite. Adoption comes from openness — the MIDI play.
- **The tools are proprietary**: the compressor (MusicXML → `.mu`, AI-assisted,
  human-evaluated) and the LLM player are the products. PDF is the precedent:
  open spec, proprietary Acrobat.
- **The content is licensed**: `.mu` files carry a plaintext manifest —
  license, provenance, AI disclosure. Public-domain works first; living
  composers by direct agreement. No artist lookalikes, ever, without license.
- **Constant human evaluation.** The founder knows these scores. Metrics
  support judgment; the ear decides.

## Explicitly not

- A streaming service or consumer app (the event comes first; the platform is downstream)
- Recording → `.mu` → identical recording (audio→symbolic at orchestral density is unsolved research)
- A sealed model + subscription as the only way to hear a work (the deterministic baseline must always be free)
- Scanned-historic-document ingestion (MusicXML sources only; we are not in the digitization business)

## Roadmap

Tracked in [pipeline.md](pipeline.md) — W (workbench) → S (spec) → P
(player) → C (compressor) → L (LLM player). Tools before spec; corpus before
claims; the Ninth before v1.0.
