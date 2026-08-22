// Regenerates importer/fixtures/midi-sample.mid — the known-content fixture
// for tests/midi.test.mjs (issue #17). Run: `node importer/fixtures/make-midi-sample.mjs`.
// Keep the assertions in tests/midi.test.mjs in sync with the values below.
import { writeFile } from "node:fs/promises";
import pkg from "@tonejs/midi";

const { Midi } = pkg;

const midi = new Midi(); // ppq 480
midi.header.tempos.push({ ticks: 0, bpm: 120 });
midi.header.tempos.push({ ticks: 960, bpm: 90 }); // tempo change at beat 2
midi.header.timeSignatures.push({ ticks: 0, timeSignature: [3, 4] });
midi.header.update();

const lead = midi.addTrack();
lead.name = "Lead";
lead.instrument.number = 40; // violin
lead.addNote({ midi: 60, ticks: 0, durationTicks: 480, velocity: 0.8 });
lead.addNote({ midi: 64, ticks: 480, durationTicks: 480, velocity: 0.6 });
lead.addNote({ midi: 67, ticks: 960, durationTicks: 960, velocity: 1 });

const bass = midi.addTrack();
bass.name = "Bass";
bass.instrument.number = 43; // cello
bass.addNote({ midi: 36, ticks: 0, durationTicks: 1920, velocity: 0.9 });

const out = new URL("./midi-sample.mid", import.meta.url);
await writeFile(out, Buffer.from(midi.toArray()));
console.log(`wrote ${out.pathname}`);
