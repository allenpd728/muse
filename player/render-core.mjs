// Player V1 — performance document → audio (issue #24, per docs/scope-batch3.md).
// Free tier / reference implementation: deterministic offline synthesis, no
// AI, no assets — additive voices with per-family timbre and ADSR-lite
// envelopes standing in for the GM soundfont until a soundfont ships. The
// renderer contract is the scope doc's: render(perfDoc, { sampleRate }) →
// Float32Array[] per channel. renderWav wraps it as a 16-bit PCM WAV buffer.
// Dynamics curves, per-part gain/pan, and articulation envelopes are applied.

const midiHz = (m) => 440 * 2 ** ((m - 69) / 12);

// Per-instrument-family voice: partial weights + envelope times (seconds).
// program is GM 0-127; families are coarse GM groups.
const FAMILIES = [
  { max: 7,   partials: [1, 0.5, 0.25, 0.12], attack: 0.005, release: 0.3,  sustain: 0.0 },  // piano: struck, decays
  { max: 15,  partials: [1, 0.4, 0.2],        attack: 0.01,  release: 0.15, sustain: 0.6 },  // chromatic percussion
  { max: 23,  partials: [1, 0.3, 0.1],        attack: 0.02,  release: 0.2,  sustain: 0.7 },  // organ
  { max: 31,  partials: [1, 0.6, 0.3, 0.15],  attack: 0.02,  release: 0.2,  sustain: 0.4 },  // guitar: plucked
  { max: 39,  partials: [1, 0.25, 0.08],      attack: 0.01,  release: 0.25, sustain: 0.8 },  // bass
  { max: 51,  partials: [1, 0.45, 0.2, 0.1],  attack: 0.06,  release: 0.25, sustain: 0.85 }, // strings
  { max: 55,  partials: [1, 0.5, 0.3],        attack: 0.08,  release: 0.3,  sustain: 0.8 },  // ensemble
  { max: 63,  partials: [1, 0.55, 0.3, 0.12], attack: 0.04,  release: 0.2,  sustain: 0.8 },  // brass
  { max: 71,  partials: [1, 0.4, 0.15],       attack: 0.05,  release: 0.2,  sustain: 0.75 }, // reed
  { max: 79,  partials: [1, 0.2, 0.05],       attack: 0.04,  release: 0.2,  sustain: 0.7 },  // pipe
  { max: 87,  partials: [1, 0.35, 0.1],       attack: 0.03,  release: 0.2,  sustain: 0.65 }, // synth lead
  { max: 127, partials: [1, 0.3, 0.15],       attack: 0.05,  release: 0.3,  sustain: 0.7 },  // everything else
];
const voiceFor = (program = 0) => FAMILIES.find((f) => program <= f.max);

// Articulation shapes the effective duration and gain, per common practice.
const ARTICULATIONS = {
  normal: { dur: 0.9, gain: 1.0 },
  tenuto: { dur: 1.0, gain: 1.0 },
  staccato: { dur: 0.4, gain: 0.9 },
  staccatissimo: { dur: 0.2, gain: 0.85 },
  legato: { dur: 1.05, gain: 0.95 },
  accent: { dur: 0.9, gain: 1.3 },
  marcato: { dur: 0.7, gain: 1.4 },
};

// Piecewise-linear dynamics level at time t for a part (global + part curves).
const levelAt = (curves, partId, t) => {
  const relevant = curves.filter((d) => d.part === undefined || d.part === partId);
  if (relevant.length === 0) return 1;
  const sorted = [...relevant].sort((a, b) => a.time - b.time);
  if (t <= sorted[0].time) return sorted[0].level;
  for (let i = 1; i < sorted.length; i++) {
    if (t <= sorted[i].time) {
      const [a, b] = [sorted[i - 1], sorted[i]];
      return a.level + (b.level - a.level) * ((t - a.time) / (b.time - a.time || 1));
    }
  }
  return sorted[sorted.length - 1].level;
};

// Techniques Player V1 can render (spec §7 honor-or-drop rule): anything
// else on a part's techniques list is dropped and recorded — never a
// failure. V1 honors GM program only, so every technique drops today; the
// recording path is the contract.
const V1_SUPPORTED_TECHNIQUES = [];

// The drop record, per spec §7: unsupported part techniques, one entry
// each. Players fold this into extensions.<player>.dropped; render never
// fails on a technique.
export const droppedTechniques = (perfDoc) => {
  const dropped = [];
  for (const part of perfDoc.parts ?? [])
    for (const t of part.instrument?.techniques ?? [])
      if (!V1_SUPPORTED_TECHNIQUES.includes(t)) dropped.push({ part: part.id, technique: t });
  return dropped;
};

// render(perfDoc, { sampleRate }) → Float32Array[] [left, right].
// This IS the renderer contract (docs/scope-batch3.md): plugins implement
// the same signature.
export function render(perfDoc, { sampleRate = 44100 } = {}) {
  const notes = perfDoc.notes ?? [];
  const partsById = new Map((perfDoc.parts ?? []).map((p) => [p.id, p]));
  const dynamics = perfDoc.dynamics ?? [];
  const tail = 0.5; // release tail past the last note
  const end = notes.reduce((m, n) => Math.max(m, n.onset + n.duration), 0) + tail;
  const frames = Math.max(1, Math.ceil(end * sampleRate));
  const left = new Float32Array(frames);
  const right = new Float32Array(frames);

  for (const note of notes) {
    const part = partsById.get(note.part) ?? {};
    const voice = voiceFor(part.instrument?.program);
    const art = ARTICULATIONS[note.articulation ?? "normal"] ?? ARTICULATIONS.normal;
    const gain = (part.mix?.gain ?? 1) * (note.velocity / 127) * art.gain;
    const pan = part.mix?.pan ?? 0;
    const freq = midiHz(note.pitch);
    const start = Math.floor(note.onset * sampleRate);
    const dur = Math.max(1, Math.floor(note.duration * art.dur * sampleRate));
    const attack = Math.max(1, Math.floor(voice.attack * sampleRate));
    const release = Math.max(1, Math.floor(voice.release * sampleRate));
    const total = Math.min(frames - start, dur + release);
    // Equal-power pan.
    const lGain = Math.cos(((pan + 1) * Math.PI) / 4);
    const rGain = Math.sin(((pan + 1) * Math.PI) / 4);
    for (let i = 0; i < total; i++) {
      const t = (start + i) / sampleRate;
      // Envelope: linear attack, sustain level, linear release after dur.
      const env = i < attack ? i / attack
        : i < dur ? 1 - (1 - voice.sustain) * ((i - attack) / Math.max(1, dur - attack))
        : voice.sustain * Math.max(0, 1 - (i - dur) / release);
      let s = 0;
      for (let h = 0; h < voice.partials.length; h++)
        s += voice.partials[h] * Math.sin(2 * Math.PI * freq * (h + 1) * t);
      const dyn = levelAt(dynamics, note.part, t);
      const v = s * env * gain * dyn * 0.35;
      left[start + i] += v * lGain;
      right[start + i] += v * rGain;
    }
  }
  // Soft clip.
  for (let i = 0; i < frames; i++) {
    left[i] = Math.tanh(left[i]);
    right[i] = Math.tanh(right[i]);
  }
  return [left, right];
}

// 16-bit PCM WAV encoding as a Uint8Array — browser-safe (DataView, no
// Buffer), shared by the node renderWav wrapper and the listener's
// client-side download (#100).
export function encodeWav(channels, { sampleRate = 44100 } = {}) {
  const nCh = channels.length;
  const frames = channels[0]?.length ?? 0;
  const dataSize = frames * nCh * 2;
  const buf = new ArrayBuffer(44 + dataSize);
  const v = new DataView(buf);
  const str = (off, s) => { for (let i = 0; i < s.length; i++) v.setUint8(off + i, s.charCodeAt(i)); };
  str(0, "RIFF"); v.setUint32(4, 36 + dataSize, true); str(8, "WAVE");
  str(12, "fmt "); v.setUint32(16, 16, true); v.setUint16(20, 1, true);
  v.setUint16(22, nCh, true); v.setUint32(24, sampleRate, true);
  v.setUint32(28, sampleRate * nCh * 2, true); v.setUint16(32, nCh * 2, true);
  v.setUint16(34, 16, true);
  str(36, "data"); v.setUint32(40, dataSize, true);
  for (let i = 0; i < frames; i++)
    for (let c = 0; c < nCh; c++)
      v.setInt16(44 + (i * nCh + c) * 2, Math.max(-32768, Math.min(32767, Math.round(channels[c][i] * 32767))), true);
  return new Uint8Array(buf);
}
