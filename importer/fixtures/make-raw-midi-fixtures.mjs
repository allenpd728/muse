// Generates the hand-crafted raw MIDI fixtures used by tests/midi.test.mjs
// residual coverage (issue #50). tonejs's writer always emits format 1 at
// ppq 480, so format-0 and low-ppq fixtures are built byte by byte here.
// Run: `node importer/fixtures/make-raw-midi-fixtures.mjs`.
import { writeFile } from "node:fs/promises";

const vlq = (n) => {
  const out = [n & 0x7f];
  while ((n >>= 7)) out.unshift(0x80 | (n & 0x7f));
  return out;
};
const text = (s) => [...s].map((c) => c.charCodeAt(0));
const chunk = (id, data) => [...text(id), 0, 0, 0, data.length, ...data];
const file = (format, ppq, tracks) => [
  ...chunk("MThd", [0, format, 0, tracks.length, ppq >> 8, ppq & 0xff]),
  ...tracks.flatMap((t) => chunk("MTrk", t)),
];
const tempo = (bpm) => {
  const us = Math.round(6e7 / bpm);
  return [0x00, 0xff, 0x51, 0x03, us >> 16, (us >> 8) & 0xff, us & 0xff];
};
const timeSig = (num, denPow2) => [0x00, 0xff, 0x58, 0x04, num, denPow2, 0x18, 0x08];
const trackName = (name) => [0x00, 0xff, 0x03, name.length, ...text(name)];
const note = (dt, midi, vel) => [...vlq(dt), 0x90, midi, vel];
const off = (dt, midi) => [...vlq(dt), 0x80, midi, 64];
const eot = (dt = 0) => [...vlq(dt), 0xff, 0x2f, 0x00];

const write = async (name, bytes) => {
  await writeFile(new URL(`./${name}`, import.meta.url), Buffer.from(bytes));
  console.log(`wrote importer/fixtures/${name} (${bytes.length} bytes)`);
};

// Format 0, ppq 96: tempo 120 + 3/4 on the single shared track; one quarter
// note C4 (96 ticks at ppq 96 = 1 beat), velocity 100.
await write("midi-format0-ppq96.mid", file(0, 96, [
  [
    ...tempo(120),
    ...timeSig(3, 2),
    ...note(0, 60, 100),
    ...off(96, 60),
    ...eot(),
  ],
]));

// Format 1: conductor track with 4/4 at beat 0 changing to 3/4 at beat 2,
// and the only tempo at beat 1 (no beat-0 tempo); one named track with no
// program-change events and no notes.
const at = (dt, ev) => [...vlq(dt), ...ev.slice(1)];
await write("midi-midpiece.mid", file(1, 480, [
  [
    ...timeSig(4, 2),                        // beat 0: 4/4
    ...at(480, tempo(90)),                   // beat 1: first tempo appears here
    ...at(480, timeSig(3, 2)),               // beat 2: meter change to 3/4
    ...eot(),
  ],
  [
    ...trackName("Reeds"),
    ...eot(),
  ],
]));
