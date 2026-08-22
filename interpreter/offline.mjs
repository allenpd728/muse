// Offline deterministic expansion (issue #25, per docs/scope-batch3.md).
// A no-model reference expander sharing the interpreter's callModel
// interface: .muse.json + rendition → performance document, no API key, no
// nondeterminism. It exists so `npm run play` and the end-to-end demo work
// out of the box; the LLM path (expand.mjs default adapters) is the real
// interpreter. Realizes theme phrases from material motifs with transform
// suffixes, voices the section's chord progression for the harmonic bed,
// applies rendition params (tempo_bpm, density, swing) — two renditions of
// the same work audibly differ by construction.
import { pitchToMidi, midiToPitch } from "../importer/ir.mjs";

const TRANSFORMS = {
  // Inversion mirrors intervals about the first pitch.
  inv: (pitches) => pitches.map((p, i) => (i === 0 ? p : pitches[0] - (p - pitches[0]))),
  retro: (pitches) => [...pitches].reverse(),
  seq: (n) => (pitches) => pitches.map((p) => p + n),
  aug: (f) => (pitches, durations) => [pitches, durations.map((d) => d * f)],
  dim: (f) => (pitches, durations) => [pitches, durations.map((d) => d * f)],
};

// Apply a ref's transform chain to a motif's pitches/durations.
const realizeRef = (ref, motifsById) => {
  const [base, ...ops] = String(ref).split("#");
  const motif = motifsById.get(base);
  if (!motif) return null;
  let pitches = (motif.pitches ?? []).map(pitchToMidi);
  let durations = motif.durations ?? pitches.map(() => 1);
  for (const op of ops) {
    const m = /^(seq|aug|dim)\(([+-]?[\d.]+)\)$/.exec(op) ?? /^(inv|retro)$/.exec(op);
    if (!m) continue;
    if (m[1] === "seq") pitches = TRANSFORMS.seq(Number(m[2]))(pitches);
    else if (m[1] === "inv") pitches = TRANSFORMS.inv(pitches);
    else if (m[1] === "retro") pitches = TRANSFORMS.retro(pitches);
    else if (m[1] === "aug") [pitches, durations] = TRANSFORMS.aug(Number(m[2]))(pitches, durations);
    else if (m[1] === "dim") [pitches, durations] = TRANSFORMS.dim(Number(m[2]))(pitches, durations);
  }
  return { pitches, durations };
};

// Chord symbol → midi pitch classes (root + quality), 12-TET triads/7ths.
const CHORD_TONES = { "": [0, 4, 7], m: [0, 3, 7], maj7: [0, 4, 7, 11], m7: [0, 3, 7, 10], 7: [0, 4, 7, 10], dim: [0, 3, 6], aug: [0, 4, 8] };
const chordMidis = (symbol, octave = 3) => {
  const m = /^([A-G])(#|b)?(.*)$/.exec(symbol);
  if (!m) return [];
  const root = pitchToMidi(`${m[1]}${m[2] ?? ""}${octave}`);
  const quality = m[3] || "";
  const tones = CHORD_TONES[quality] ?? CHORD_TONES[quality.replace(/maj/, "maj")] ?? CHORD_TONES[""];
  return tones.map((t) => root + t);
};

const GM_PROGRAMS = { piano: 0, "upright bass": 32, "acoustic bass": 32, bass: 33, violin: 40, viola: 41, cello: 42, "string ensemble": 48, "tenor sax": 66, trumpet: 56, "analog synth": 80, "synth lead": 80, "drum machine": 0, brushes: 0 };

// beatsPerBar handles compound meter arrays ([3,3,2] → 8 eighth-notes = 4 beats at unit 8).
const beatsPerBar = (meter) => {
  const beats = Array.isArray(meter?.beats) ? meter.beats.reduce((a, b) => a + b, 0) : meter?.beats ?? 4;
  return beats * (4 / (meter?.unit ?? 4));
};

// The offline expander, sharing the interpreter's callModel-shaped output.
export function expandOffline(doc, rendition, { at = "2026-08-22T00:00:00Z" } = {}) {
  const bpm = rendition?.params?.tempo_bpm ?? doc.globals?.tempo?.bpm ?? 96;
  const density = rendition?.params?.density ?? 0.6;
  const swing = rendition?.params?.swing ?? 0;
  const spb = 60 / bpm; // seconds per beat
  const barBeats = beatsPerBar(doc.globals?.meter);

  const motifsById = new Map((doc.material?.motifs ?? []).map((m) => [m.id, m]));
  const themesById = new Map((doc.material?.themes ?? []).map((t) => [t.id, t]));
  const progsById = new Map((doc.material?.harmony?.progressions ?? []).map((p) => [p.id, p]));

  const instrumentation = rendition?.params?.instrumentation ?? ["piano"];
  const leadName = instrumentation[0] ?? "piano";
  const bedName = instrumentation[1] ?? "string ensemble";
  const parts = [
    { id: "p.lead", name: leadName, instrument: { name: leadName, program: GM_PROGRAMS[leadName] ?? 0 }, mix: { gain: 0.9, pan: 0.15, reverb_send: 0.25 } },
    { id: "p.bed", name: bedName, instrument: { name: bedName, program: GM_PROGRAMS[bedName] ?? 48 }, mix: { gain: 0.6, pan: -0.15, reverb_send: 0.35 } },
  ];

  const notes = [];
  const sectionsById = new Map((doc.form?.sections ?? []).map((s) => [s.id, s]));
  const repetition = doc.form?.repetition ?? {};
  // Deterministic expander picks the lower repeat bound (spec: min ≤ actual
  // ≤ max; renditions may explore above min).
  const expandOrder = (doc.form?.order ?? []).flatMap((id) => {
    const reps = repetition[id]?.min ?? 1;
    return Array.from({ length: reps }, () => id);
  });
  let bar = 0;
  for (const sectionId of expandOrder) {
    const section = sectionsById.get(sectionId);
    if (!section) continue;
    const sectionBars = section.bars ?? 4;
    const sectionStartBeat = bar * barBeats;
    const energy = section.energy ?? 0.5;
    const velocity = Math.round(55 + 45 * energy * density);

    // Lead: realize each use's theme phrases from motifs.
    let cursor = sectionStartBeat;
    for (const use of section.uses ?? []) {
      const theme = themesById.get(String(use.ref).split("#")[0]);
      const phrases = theme?.phrases ?? [];
      for (const phrase of phrases) {
        for (const motifRef of phrase.motifs ?? []) {
          const realized = realizeRef(motifRef, motifsById);
          // Rhythm-only motifs (no pitches) carry no lead line — the bed
          // already covers the pulse.
          if (!realized || realized.pitches.length === 0) continue;
          // Lead sits an octave above the notated material, clear of the bed.
          realized.pitches = realized.pitches.map((p) => p + 12);
          realized.pitches.forEach((midi, i) => {
            const durBeats = realized.durations[i] ?? 1;
            // Swing: delay offbeat eighths by (swing - 0.5) * 2/3 of the pair.
            const offbeat = (cursor % 1) >= 0.5;
            const swingBeats = swing > 0 && offbeat ? ((swing - 0.5) * 2) / 3 : 0;
            notes.push({
              part: "p.lead", pitch: midi, pitch_name: midiToPitch(midi),
              onset: (cursor + swingBeats) * spb, duration: durBeats * spb * 0.92,
              onset_beat: cursor + swingBeats, duration_beats: durBeats,
              velocity,
            });
            cursor += durBeats;
          });
        }
      }
    }

    // Bed: one chord per bars_per_chord through the section's progression.
    const prog = progsById.get(section.harmony);
    if (prog) {
      const perChord = prog.bars_per_chord ?? 1;
      let chordBar = 0;
      for (let b = 0; b < sectionBars; b += perChord) {
        const chord = prog.chords[chordBar % prog.chords.length];
        chordBar++;
        for (const midi of chordMidis(chord)) {
          notes.push({
            part: "p.bed", pitch: midi, pitch_name: midiToPitch(midi),
            onset: (sectionStartBeat + b * barBeats) * spb, duration: perChord * barBeats * spb * 0.95,
            onset_beat: sectionStartBeat + b * barBeats, duration_beats: perChord * barBeats,
            velocity: Math.round(velocity * 0.7),
          });
        }
      }
    }
    bar += sectionBars;
  }

  const totalBeats = bar * barBeats;
  return {
    muse_perf_version: "0.1.0",
    metadata: {
      source: { schema_id: doc.metadata?.id ?? "unknown", rendition_id: rendition?.id ?? "r.default" },
      interpreter: { model: "offline-expander-v0", at },
    },
    tempo_map: [{ time: 0.0, beat: 0, bpm }],
    parts,
    notes: notes.sort((a, b) => a.onset - b.onset || a.pitch - b.pitch),
    dynamics: [
      { time: 0.0, level: 0.55 },
      { time: totalBeats * spb * 0.5, level: 0.75 },
      { time: totalBeats * spb * 0.95, level: 0.5 },
    ],
  };
}
