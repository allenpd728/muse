# L5 — Sample-quality waiver (design doc, scaffold)

**Phase 4 — The product (sub-task; conditional gate). Status: scaffold.**

## Decision framework

**Trigger:** L2 renders a mockup at maximal fidelity (full DNA density,
correct budgets, proper articulation mapping) and the founder's ear says
"not worth a hall." That's the failure condition.

**Two paths:**

| Path | Cost | Timeline | Quality ceiling |
|---|---|---|---|
| **A — Commercial library contract** | $500–$5,000 per library (Spitfire BBC SO ~$300, Vienna Synchron ~$1,500+, Orchestral Tools ~$500–$2,000 per section) | Weeks (license + integration) | Concert-hall tier; true legato, section blends, hall acoustics |
| **B — Revised event bar** | $0 | Immediate | "Convincing mockup" becomes the bar; event staged with narration/context framing the technology, not the audio fidelity |

**What "convincing failure" means technically:**
- Free samples (SSO/VSCO2/VPO) lack true legato transitions — notes don't
  sing into each other; audible as " MIDI-ish" phrasing.
- Section realism: free libraries are single-instrument or small ensemble;
  orchestral blend is synthetic.
- Hall acoustics: free libraries are dry; convolution reverb helps but
  doesn't replicate a scored hall recording.

**Evidence sources:**
- [../prior-art-spike.md](../prior-art-spike.md) §T4: "free samples reach
  'convincing mockup, demo quality' — section ensembles, basic
  articulations. Commercial (Spitfire/Kontakt) realism needs articulation
  depth free libs lack."
- [../spike/](../spike/) listener: chorale/Byrd renders at SSO tier; the
  founder's verdict ("good enough for now" at v3) was the spike pass
  condition, not the event bar.

## Purpose

L2's sample-tier render is gated on the founder's ear. If it fails despite
maximal mockup fidelity — the "convincing vs. DG-tier" ceiling — this
sub-task opens: either a commercial-library contract (event budget) or a
revision of the event quality bar. Trigger condition keeps this off the
day-to-day path.

## Dependencies

- **Upstream:** L2 (render quality + trigger); spike listener for evidence.
- **Downstream:** E1 (event quality decision).

## Scope (pin in draft)

- **Inputs:** L2 render + founder verdict on the mockup.
- **Outputs:** waiver decision + rationale, recorded in the design doc.
- **Non-goals:** L2's implementation; standalone event staging (E2).

## Open questions

- Threshold: what specifically distinguishes "convincing" failure from
  mockup-craft failure. (Answered above: legato gaps, section blend,
  hall acoustics — measurable in the render, not the mockup.)

## Acceptance criteria (when promoted to draft)

- Decision recorded with rationale; E1's path clarified.
