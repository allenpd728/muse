# W1 — Event-stream IR

**Status:** open
**Depends on:** none
**Phase:** 0 (workbench)

## Summary

Define the canonical in-memory event format every Muse tool shares — the IR
that parsers (MusicXML, MIDI) produce and the analyzer, diff tool, packer,
and decoder all consume. Includes the parsers themselves.

## Definition of done

- `tools/` exists with an IR module: notes (pitch, onset ticks, duration
  ticks, velocity), parts (id, name, program), tempo map, meter map, key map,
  dynamics markings, articulations, repeat topology.
- MusicXML parser (`.xml`/`.mxl`) → IR. MIDI parser → IR.
- Fixed-point/integer ticks only — no float nondeterminism anywhere in the IR.
- Known-answer test: parse `corpus/bach/bwv227.1.mxl`, assert part count (4),
  note count (279), measure count.
- Test spec written per TASK_WORKFLOW.

## Context

- corpus/README.md — measured counts per file (known-answer targets)
- FORMAT_SPEC.md §4 (roll stream content model) — what the IR must carry
- Old importer/ir.mjs survives in git history (branch milestone/batch1-3-explorer)
  as an edge-case reference — read it, don't port it blindly: its conventions
  served the dead JSON schema
