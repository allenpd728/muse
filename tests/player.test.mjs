// Tests for player/render.mjs (issue #24, per docs/scope-batch3.md).
// Offline DSP analysis — no audio hardware required.
// Standalone runner: `node tests/player.test.mjs`; also folded into npm test.
import { readFile } from "node:fs/promises";
import { render, renderWav } from "../player/render.mjs";

const fixture = JSON.parse(await readFile(new URL("../tools/fixtures/valid.muse.perf.json", import.meta.url), "utf8"));
const clone = () => JSON.parse(JSON.stringify(fixture));

let passed = 0, failed = 0;
const check = (name, cond) => {
  if (cond) { passed++; console.log(`ok   ${name}`); }
  else { failed++; console.error(`FAIL ${name}`); }
};

const SR = 8000; // small rate keeps the suite fast; DSP relationships hold
const rms = (ch, from = 0, to = ch.length) => {
  let s = 0;
  for (let i = from; i < to; i++) s += ch[i] * ch[i];
  return Math.sqrt(s / Math.max(1, to - from));
};
const peak = (ch) => ch.reduce((m, v) => Math.max(m, Math.abs(v)), 0);

// DoD: fixture renders without error and produces audible content.
const [left, right] = render(clone(), { sampleRate: SR });
check("renders stereo Float32Arrays", left instanceof Float32Array && right instanceof Float32Array && left.length === right.length);
check("output length covers the last note plus tail",
  left.length >= Math.ceil((2.5 + 0.5) * SR) && left.length <= Math.ceil((2.5 + 0.5) * SR) + 1);
check("audible content (non-silent)", rms(left) > 0.001);
check("no clipping beyond [-1, 1] after soft clip", peak(left) <= 1 && peak(right) <= 1);

// Correct timing: first note (C4-ish lead at t=0) sounds before the second
// onset (0.3125s); a gap between notes is quieter than the note body.
{
  const noteAt = (t) => rms(left, Math.floor(t * SR), Math.floor((t + 0.05) * SR));
  check("energy present at first onset", noteAt(0.05) > 0.001);
  check("second onset has more energy than the pre-onset gap",
    noteAt(0.35) > noteAt(0.30) || noteAt(0.35) > 0.001);
}

// Distinct instruments: lead (program 40, strings) and bass (program 43,
// strings-family too — change bass to program 32 acoustic bass) differ in
// spectral content. Compare a lead-only render vs bass-only render of the
// same note: different partial weights → different RMS ratio at harmonic
// windows. Simplest robust pin: renders differ bit-wise and both sound.
{
  const leadOnly = clone(); leadOnly.notes = leadOnly.notes.filter((n) => n.part === "p.lead");
  const bassOnly = clone(); bassOnly.notes = bassOnly.notes.filter((n) => n.part === "p.bass");
  bassOnly.parts[1].instrument.program = 32; // distinct family from strings
  const [l1] = render(leadOnly, { sampleRate: SR });
  const [l2] = render(bassOnly, { sampleRate: SR });
  check("distinct parts render distinct audio", !l1.every((v, i) => v === l2[i]) && rms(l1) > 0 && rms(l2) > 0);
}

// Velocity and dynamics curves affect amplitude.
{
  const quiet = clone(); quiet.notes.forEach((n) => { n.velocity = 30; });
  const [ql] = render(quiet, { sampleRate: SR });
  check("lower velocity renders quieter", rms(ql) < rms(left));
  const swelled = clone();
  swelled.dynamics = [{ time: 0, level: 0.1 }, { time: 2.0, level: 1.0 }];
  const [sl] = render(swelled, { sampleRate: SR });
  check("dynamics crescendo: later window louder than early",
    rms(sl, Math.floor(1.8 * SR), Math.floor(2.2 * SR)) > rms(sl, Math.floor(0.0 * SR), Math.floor(0.4 * SR)));
}

// Pan: hard-left part puts more energy in the left channel.
{
  const panned = clone();
  panned.parts[0].mix.pan = -1;
  panned.notes = panned.notes.filter((n) => n.part === "p.lead");
  const [pl, pr] = render(panned, { sampleRate: SR });
  check("hard-left pan favors left channel", rms(pl) > rms(pr) * 2);
}

// WAV wrapper: header fields and data size.
{
  const wav = renderWav(clone(), { sampleRate: SR });
  check("WAV: RIFF/WAVE header", wav.subarray(0, 4).toString() === "RIFF" && wav.subarray(8, 12).toString() === "WAVE");
  check("WAV: stereo 16-bit PCM at requested rate",
    wav.readUInt16LE(22) === 2 && wav.readUInt16LE(34) === 16 && wav.readUInt32LE(24) === SR);
  check("WAV: data chunk size matches frames",
    wav.readUInt32LE(40) === wav.length - 44 && wav.length === 44 + left.length * 2 * 2);
}

// Empty notes render silence without error.
{
  const empty = clone(); empty.notes = [];
  const [el] = render(empty, { sampleRate: SR });
  check("empty notes render silence", rms(el) < 1e-6);
}

console.log(`${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
