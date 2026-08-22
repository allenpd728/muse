// Residual coverage for interpreter/expand.mjs (issue #65, spec:
// tests/closed_…_interpreter.md). The new clock-consistency semantic
// (tools/semantics.mjs checkClockConsistency) is exercised here against the
// interpreter's fixture — the live-model smoke and constraint-semantics pass
// stay deferred per the spec. Standalone runner; folded into npm test.
import { readFile } from "node:fs/promises";
import { checkClockConsistency } from "../tools/semantics.mjs";

let passed = 0, failed = 0;
const check = (name, cond) => {
  if (cond) { passed++; console.log(`ok   ${name}`); }
  else {
    failed++;
    console.error(`FAIL ${name}`);
  }
};

const fixture = JSON.parse(await readFile(new URL("../interpreter/fixtures/minimal-expansion.muse.perf.json", import.meta.url), "utf8"));

// The interpreter's own fixture must be clock-consistent — 0.625s = 1 beat
// at 96 bpm.
check("interpreter fixture is clock-consistent", checkClockConsistency(fixture).length === 0);

// Multi-segment tempo_map: 120 bpm for 2 beats (1.0s), then 60 bpm.
const twoTempo = {
  tempo_map: [{ time: 0, beat: 0, bpm: 120 }, { time: 1.0, beat: 2, bpm: 60 }],
  parts: [{ id: "p" }],
  notes: [
    { part: "p", pitch: 60, pitch_name: "C4", onset: 0.5, duration: 0.5, onset_beat: 1, duration_beats: 1, velocity: 80 },
    { part: "p", pitch: 62, pitch_name: "D4", onset: 2.0, duration: 1.0, onset_beat: 3, duration_beats: 1, velocity: 80 },
  ],
};
check("two-segment tempo_map: notes agree in both segments", checkClockConsistency(twoTempo).length === 0);

// Drift beyond tolerance flags (onset and duration both checked — moving the
// onset without moving the duration drags both out of agreement).
const drifted = structuredClone(fixture);
drifted.notes[0].onset = 0.75; // 1 beat at 96bpm is 0.625s — 125ms off
const errs = checkClockConsistency(drifted);
check("onset drift flags", errs.length === 2 && errs[0].includes("notes[0]") && errs[0].includes("onset"));
check("onset drift also flags duration (span moved)", errs[1].includes("duration"));

// Missing clocks skip silently (schema enforces presence; the lint tolerates).
const partial = structuredClone(fixture);
delete partial.notes[0].onset_beat;
check("missing onset_beat skipped (schema owns presence)", checkClockConsistency(partial).length === 0);

// Empty tempo_map: nothing to check against.
check("empty tempo_map skips", checkClockConsistency({ parts: [], notes: [], tempo_map: [] }).length === 0);

console.log(`${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
