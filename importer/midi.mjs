// MIDI → IR parser (issue #17, per docs/scope-importer.md).
// @tonejs/midi does the meta-event work; this module's job is the boundary
// conversion: ticks → beats at the IR edge, velocity 0-1 → 0-127, tonejs
// key {key, scale} → IR {tonic, mode}. Output is normalized IR — nothing
// downstream sees ticks or seconds.
import pkg from "@tonejs/midi";
import midiParsePkg from "midi-file";
import { normalizeIR, ticksToBeats } from "./ir.mjs";

const { Midi } = pkg;
const { parseMidi } = midiParsePkg;

// tonejs's Instrument defaults number to 0 when the track has no
// program-change event, which is indistinguishable from an explicit acoustic
// grand. Decision (tested in tests/midi.test.mjs): `program` is emitted only
// when a program-change event actually exists in the file — a part that never
// chose an instrument gets none.
const programTicks = (input) => {
  const ticksPerProgram = new Map();
  try {
    for (const track of parseMidi(input instanceof ArrayBuffer ? new Uint8Array(input) : input).tracks) {
      let abs = 0;
      for (const ev of track) {
        abs += ev.deltaTime;
        if (ev.type === "programChange" && !ticksPerProgram.has(ev.programNumber))
          ticksPerProgram.set(ev.programNumber, abs);
      }
    }
  } catch {
    // parseMidi already failed or the file is malformed — tonejs will surface
    // the real error when midiToIR constructs the Midi instance below.
  }
  return [...ticksPerProgram.entries()].sort((a, b) => a[1] - b[1]).map(([program]) => program);
};

// input: Buffer/Uint8Array of a .mid file.
export function midiToIR(input) {
  const midi = new Midi(input);
  const programs = programTicks(input);
  const ppq = midi.header.ppq;
  const beat = (ticks) => ticksToBeats(ticks, ppq);

  return normalizeIR({
    tempoMap: midi.header.tempos.map((t) => ({ beat: beat(t.ticks), bpm: t.bpm })),
    meterMap: midi.header.timeSignatures.map((ts) => ({
      beat: beat(ts.ticks),
      beats: ts.timeSignature[0],
      unit: ts.timeSignature[1],
    })),
    // tonejs round-trips key signatures partially (key can be absent); only
    // entries with a tonic survive — a missing key is unknown, not C major.
    keyMap: midi.header.keySignatures
      .filter((k) => typeof k.key === "string" && k.key.length > 0)
      .map((k) => ({ beat: beat(k.ticks), tonic: k.key, mode: k.scale ?? "major" })),
    parts: midi.tracks.map((t, i) => {
      const part = {
        id: `track.${i + 1}`,
        name: t.name || `Track ${i + 1}`,
        notes: t.notes.map((n) => ({
          midi: n.midi,
          onsetBeat: beat(n.ticks),
          durationBeats: beat(n.durationTicks),
          velocity: Math.round(n.velocity * 127),
        })),
      };
      if (programs[i] !== undefined) part.program = programs[i];
      return part;
    }),
  });
}
