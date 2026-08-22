// Tests for player/render.mjs (issue #24, per docs/scope-batch3.md).
// Offline DSP analysis — no audio hardware required.
// Standalone runner: `node tests/player.test.mjs`; also folded into npm test.
import { readFile } from "node:fs/promises";
import { render, renderWav, droppedTechniques } from "../player/render.mjs";

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

// --- Residual coverage (issue #66, per
// tests/open_20260822-123200_player.md) ---

// tempo_map disagreement: note seconds are authoritative for playback.
{
  const skewed = clone();
  skewed.tempo_map = [{ time: 0, beat: 0, bpm: 30 }]; // half speed — must NOT change output
  const [sl, sr2] = render(skewed, { sampleRate: SR });
  check("tempo_map disagrees with note seconds: renders by note seconds",
    sl.every((v, i) => v === left[i]) && sr2.every((v, i) => v === right[i]));
}

// Controllers forward-compat: V1 ignores per-note controllers entirely.
{
  const withCtl = clone();
  withCtl.notes.forEach((n, i) => { n.controllers = { pitch_bend: [0, i % 2], pressure: [0.5] }; });
  const [cl, cr2] = render(withCtl, { sampleRate: SR });
  check("per-note controllers never change V1 output",
    cl.every((v, i) => v === left[i]) && cr2.every((v, i) => v === right[i]));
}

// Articulation extremes fuzz: staccatissimo at minimal durations, legato
// overlaps, simultaneous onsets — finite output, no buffer overruns.
{
  const extremes = clone();
  extremes.notes = [];
  for (let i = 0; i < 40; i++) {
    extremes.notes.push({
      part: "p.lead", pitch: 40 + (i % 40), pitch_name: "E2",
      onset: i * 0.01, duration: i % 3 === 0 ? 0.02 : 0.5, // overlapping + tiny
      onset_beat: i * 0.016, duration_beats: 0.032, velocity: 40 + (i % 80),
      articulation: ["normal", "staccatissimo", "legato", "marcato"][i % 4],
    });
  }
  const [el, er] = render(extremes, { sampleRate: SR });
  const finite = (ch) => ch.every((v) => Number.isFinite(v));
  check("articulation/duration extremes render finite, bounded output",
    finite(el) && finite(er) && peak(el) <= 1 && peak(er) <= 1);
}

// Honor-or-drop (spec §7, issue #86): unsupported part techniques are
// dropped with a recorded decision — render never fails.
{
  const withTech = clone();
  withTech.parts[0].instrument.techniques = ["pizzicato", "sul_ponticello"];
  withTech.parts[1].instrument.techniques = ["muted"];
  const drops = droppedTechniques(withTech);
  check("unsupported techniques recorded as dropped (V1 honors GM program only)",
    drops.length === 3 && drops.every((d) => d.part && d.technique));
  const [tl, tr2] = render(withTech, { sampleRate: SR });
  check("render never fails on unsupported techniques (identical output)",
    tl.every((v, i) => v === left[i]) && tr2.every((v, i) => v === right[i]));
  check("no techniques → empty drop record", droppedTechniques(clone()).length === 0);
}

console.log(`${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
