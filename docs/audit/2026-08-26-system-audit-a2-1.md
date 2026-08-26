# System audit — A2.1 corpus loading + IR (2026-08-26)

**Task:** #289. **Modules:** corpus_loader, ir.
**Method:** known-answer gate (corpus check), doc-claim IR API probes, round-trip load on mxl + mid. Suites: 123 passed (two modules); full gate green.

| Module | Doc claim | Evidence | Verdict | Findings |
|---|---|---|---|---|
| corpus_loader | \`check\` gate: every corpus file parses, matches parts/notes/dynamics/hairpins pins; exit 0 | \`check\` → "All 13 corpus files pass their known-answer pins." | works | — |
| ir | API per README: load(.mxl/.mid) → Work with parts, maps, meta; rests first-class; unpitched events; integer ticks | mxl: musicxml ppq=2, 4 parts, 279 notes; mid: midi ppq=192, 3 parts, 71 notes; b9 unpitched events: 835 (README's exact pin) | works | — |
| reg/dispatch (README "dispatches on extension") | extension dispatch | mxl + mid both via \`load\` | works | — |

**Doc-level nuance noted (not a finding):** \`bwv227.7/.11\` parse to ppq=10080 (MIDI-style LCM) while \`bwv227.1\` is ppq=2 — a known-answer fact of the mxl parser, not drift.

**Findings:** none filed. Load is the pipeline's front door; it reads clean.

**Suites at close:** full gate all green.
