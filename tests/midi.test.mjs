// Tests for importer/midi.mjs (issue #17) against the known fixture
// importer/fixtures/midi-sample.mid (regenerate: importer/fixtures/make-midi-sample.mjs).
// Standalone runner: `node tests/midi.test.mjs`; also folded into npm test.
import { readFile } from "node:fs/promises";
import { midiToIR } from "../importer/midi.mjs";
import { validateIR } from "../importer/ir.mjs";

const buf = await readFile(new URL("../importer/fixtures/midi-sample.mid", import.meta.url));
const ir = midiToIR(buf);

let passed = 0, failed = 0;
const check = (name, cond) => {
  if (cond) { passed++; console.log(`ok   ${name}`); }
  else {
    failed++;
    console.error(`FAIL ${name}`);
    console.error(JSON.stringify(ir, null, 2));
  }
};
// bpm round-trips through the MIDI microsecond field with float dust —
// compare at musically meaningless precision, not bit equality.
const bpmClose = (a, b) => Math.abs(a - b) < 1e-4;

check("IR validates", validateIR(ir).length === 0);
check("two parts in score order", ir.parts.length === 2 && ir.parts[0].id === "track.1" && ir.parts[1].id === "track.2");
check("track names and programs", ir.parts[0].name === "Lead" && ir.parts[0].program === 40
  && ir.parts[1].name === "Bass" && ir.parts[1].program === 43);

check("tempo map has both entries in beat order", ir.tempoMap.length === 2
  && ir.tempoMap[0].beat === 0 && bpmClose(ir.tempoMap[0].bpm, 120)
  && ir.tempoMap[1].beat === 2 && bpmClose(ir.tempoMap[1].bpm, 90));

check("meter map: 3/4 at beat 0", ir.meterMap.length === 1
  && ir.meterMap[0].beat === 0 && ir.meterMap[0].beats === 3 && ir.meterMap[0].unit === 4);

// Key signature encoding drops the tonic through tonejs's writer, so the
// fixture carries none — parser must not invent one.
check("no key signature parsed as empty keyMap", Array.isArray(ir.keyMap) && ir.keyMap.length === 0);

const lead = ir.parts[0].notes;
check("lead notes: pitches sorted by onset", lead.length === 3
  && lead[0].midi === 60 && lead[1].midi === 64 && lead[2].midi === 67);
check("lead notes: ticks converted to beats", lead[0].onsetBeat === 0 && lead[0].durationBeats === 1
  && lead[1].onsetBeat === 1 && lead[1].durationBeats === 1
  && lead[2].onsetBeat === 2 && lead[2].durationBeats === 2);
// tonejs floors on encode: 0.8 → byte 101.
check("lead notes: velocity scaled to 0-127", lead[0].velocity === 101 && lead[1].velocity === 76 && lead[2].velocity === 127);

const bass = ir.parts[1].notes;
check("bass note spans the whole fixture", bass.length === 1
  && bass[0].midi === 36 && bass[0].onsetBeat === 0 && bass[0].durationBeats === 4);

console.log(`${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
