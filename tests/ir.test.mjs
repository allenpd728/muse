// Unit tests for importer/ir.mjs — issue #16 (Batch 2: IR).
// Standalone runner: `node tests/ir.test.mjs`; also folded into npm test.
import { readFile } from "node:fs/promises";
import {
  midiToPitch,
  pitchToMidi,
  spellingToMidi,
  midiToSpelling,
  ticksToBeats,
  beatsToTicks,
  validateIR,
  normalizeIR,
} from "../importer/ir.mjs";

let passed = 0, failed = 0;
const check = (name, cond) => {
  if (cond) { passed++; console.log(`ok   ${name}`); }
  else { failed++; console.error(`FAIL ${name}`); }
};
const eq = (a, b) => JSON.stringify(a) === JSON.stringify(b);
const clone = (o) => JSON.parse(JSON.stringify(o));

// --- Pitch conventions (scope doc: MIDI number internal, SPN emitted, C4 = 60) ---
check("middle C: midiToPitch(60) === 'C4'", midiToPitch(60) === "C4");
check("pitchToMidi('C4') === 60", pitchToMidi("C4") === 60);
check("A4 (concert A) === 69", pitchToMidi("A4") === 69 && midiToPitch(69) === "A4");
check("extremes: midi 0 → C-1, midi 127 → G9", midiToPitch(0) === "C-1" && midiToPitch(127) === "G9");
check("canonical emission uses sharps: 66 → F#4", midiToPitch(66) === "F#4");
check("pitchToMidi parses flats: Gb4 === F#4", pitchToMidi("Gb4") === 66);
check("pitch↔midi round-trips across full range", [0, 1, 12, 57, 59, 61, 69, 96, 127].every(
  (m) => pitchToMidi(midiToPitch(m)) === m));
check("pitchToMidi rejects out-of-range pitch (G#9 → 128)", (() => { try { pitchToMidi("G#9"); return false; } catch { return true; } })());
check("pitchToMidi rejects malformed pitch", (() => { try { pitchToMidi("H4"); return false; } catch { return true; } })());
check("midiToPitch rejects non-integer / out of range", (() => {
  try { midiToPitch(60.5); return false; } catch { try { midiToPitch(128); return false; } catch { return true; } }
})());

// --- MusicXML spelling metadata ---
check("spellingToMidi: D5 === 74", spellingToMidi({ step: "D", alter: 0, octave: 5 }) === 74);
check("spellingToMidi: F#4 === 66", spellingToMidi({ step: "F", alter: 1, octave: 4 }) === 66);
check("spellingToMidi: Eb4 === 63", spellingToMidi({ step: "E", alter: -1, octave: 4 }) === 63);
check("spellingToMidi defaults alter to 0", spellingToMidi({ step: "C", octave: 4 }) === 60);
check("spellingToMidi rejects microtonal alter", (() => { try { spellingToMidi({ step: "E", alter: 0.5, octave: 4 }); return false; } catch { return true; } })());
check("midiToSpelling(66) is F#4", eq(midiToSpelling(66), { step: "F", alter: 1, octave: 4 }));
check("midiToSpelling(60) is C4", eq(midiToSpelling(60), { step: "C", alter: 0, octave: 4 }));

// --- Beats are the canonical time unit; ticks die at the IR boundary ---
check("ticksToBeats: 960 ticks @ 480 tpq = 2 beats", ticksToBeats(960, 480) === 2);
check("beatsToTicks: 0.5 beats @ 480 tpq = 240 ticks", beatsToTicks(0.5, 480) === 240);
check("ticks↔beats round-trip at 480 tpq", [0, 120, 480, 960, 1440].every(
  (t) => beatsToTicks(ticksToBeats(t, 480), 480) === t));

// --- Fixture round-trip (definition of done: lossless) ---
const fixture = JSON.parse(await readFile(new URL("../importer/fixtures/ir-sample.json", import.meta.url), "utf8"));
check("fixture validates with no errors", eq(validateIR(fixture), []));
const roundTrip = JSON.parse(JSON.stringify(normalizeIR(fixture)));
check("normalize → JSON serialize → parse is lossless", eq(roundTrip, fixture));
check("validate(normalize(fixture)) is clean", eq(validateIR(roundTrip), []));

// --- normalizeIR canonicalization ---
const messy = {
  tempoMap: [{ beat: 8, bpm: 72 }, { beat: 0, bpm: 96 }],
  meterMap: [{ beat: 0, beats: 4, unit: 4 }],
  keyMap: [],
  parts: [{
    id: "p1", name: "Flute",
    notes: [
      { midi: 65, onsetBeat: 2, durationBeats: 1 },
      { midi: 77, onsetBeat: 0, durationBeats: 1 },
      { midi: 60, onsetBeat: 0, durationBeats: 1 },
    ],
  }],
};
const tidy = normalizeIR(messy);
check("normalize sorts maps by beat", tidy.tempoMap[0].beat === 0 && tidy.tempoMap[1].beat === 8);
check("normalize sorts notes by (onsetBeat, midi)", eq(
  tidy.parts[0].notes.map((n) => [n.onsetBeat, n.midi]),
  [[0, 60], [0, 77], [2, 65]]));
check("normalize is idempotent", eq(normalizeIR(tidy), tidy));
check("normalize drops no optional fields", (() => {
  const withOpts = normalizeIR({
    tempoMap: [], meterMap: [], keyMap: [],
    parts: [{ id: "p", name: "n", program: 40, notes: [{ midi: 60, spelling: { step: "C", alter: 0, octave: 4 }, onsetBeat: 0, durationBeats: 1, velocity: 100 }] }],
  });
  return withOpts.parts[0].program === 40 && withOpts.parts[0].notes[0].velocity === 100 &&
    eq(withOpts.parts[0].notes[0].spelling, { step: "C", alter: 0, octave: 4 });
})());

// --- validateIR error channels ---
const bad = (mutate) => { const d = clone(fixture); mutate(d); return validateIR(d); };
const has = (errs, needle) => errs.some((e) => e.includes(needle));

check("rejects non-object document", has(validateIR(null), "must be an object") && has(validateIR([1, 2]), "must be an object"));
check("flags unknown top-level field", has(bad((d) => { d.bogus = 1; }), "unknown top-level field"));
check("flags missing tempoMap", has(bad((d) => { delete d.tempoMap; }), "tempoMap: required"));
check("flags non-positive bpm", has(bad((d) => { d.tempoMap[0].bpm = 0; }), "bpm"));
check("flags compound meter with <2 groups", has(bad((d) => { d.meterMap[0].beats = [3]; }), "meterMap[0].beats"));
check("accepts compound meter [3,3,2]", eq(bad((d) => { d.meterMap[0].beats = [3, 3, 2]; }), []));
check("flags key without mode (non-atonal)", has(bad((d) => { delete d.keyMap[0].mode; }), "mode"));
check("accepts atonal key without mode", eq(bad((d) => { d.keyMap[0] = { beat: 0, tonic: "atonal" }; }), []));
check("accepts empty keyMap (parser could not determine key)", eq(bad((d) => { d.keyMap = []; }), []));
check("flags duplicate part ids", has(bad((d) => { d.parts[1].id = "p1"; }), "duplicate part id"));
check("flags missing part name", has(bad((d) => { delete d.parts[0].name; }), "name"));
check("flags program out of range", has(bad((d) => { d.parts[0].program = 128; }), "program"));
check("flags midi out of range", has(bad((d) => { d.parts[0].notes[0].midi = 128; }), "midi"));
check("flags negative onsetBeat", has(bad((d) => { d.parts[0].notes[0].onsetBeat = -0.5; }), "onsetBeat"));
check("flags zero durationBeats", has(bad((d) => { d.parts[0].notes[0].durationBeats = 0; }), "durationBeats"));
check("flags velocity out of range", has(bad((d) => { d.parts[0].notes[0].velocity = 200; }), "velocity"));
check("flags spelling/midi mismatch", has(bad((d) => { d.parts[0].notes[0].spelling = { step: "E", alter: 0, octave: 5 }; }), "does not match midi"));
check("flags unknown note field", has(bad((d) => { d.parts[0].notes[0].seconds = 1.2; }), "unknown field"));

console.log(`${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
