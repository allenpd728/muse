// Conformance metrics harness (issue #72): the Batch 1 §3 conformance contract
// made measurable. Given a .muse.json schema and a performance document (§7),
// compute:
//   motif_recall       — every must_contain motif (or, when must_contain is
//                        absent, every declared motif) appears recognizably,
//                        with transform tolerance per the §2.3 grammar:
//                        transposition (interval-contour match), augmentation/
//                        diminution (uniformly scaled durations), inversion,
//                        retrograde.
//   structure_fidelity — form length within repetition/deviation bounds.
// CLI: node benchmark/metrics.mjs <schema.muse.json> <performance.json>
import { readFile } from "node:fs/promises";
import path from "node:path";
import { pitchToMidi } from "../importer/ir.mjs";

const EPS = 1e-3;

const baseRef = (ref) => String(ref).split("#")[0];

const contour = (pitches) => pitches.slice(1).map((p, i) => p - pitches[i]);
const normalizeDurations = (durs) => {
  if (durs.length === 0 || durs[0] <= 0) return durs.map(() => 1);
  return durs.map((d) => d / durs[0]);
};

// Match a motif against one part's notes (onset-ordered). Returns
// { match, at_beat } or null. Contour equality covers transposition; duration
// comparison is first-duration-normalized, covering uniform aug/dim.
const findMotif = (motifPitches, motifDurations, notes) => {
  if (motifPitches.length === 0) return null;
  const target = contour(motifPitches);
  const targetDur = normalizeDurations(motifDurations);
  // Each variant pairs a contour with its duration grid; retrograde reverses
  // both (the whole sequence runs backwards).
  const variants = [
    ["exact", target, targetDur],
    ["inversion", contour([motifPitches[0], ...motifPitches.slice(1).map((p) => motifPitches[0] - (p - motifPitches[0]))]), targetDur],
    ["retrograde", contour([...motifPitches].reverse()), normalizeDurations([...motifDurations].reverse())],
  ];
  const len = motifPitches.length;
  for (let start = 0; start + len <= notes.length; start++) {
    const run = notes.slice(start, start + len);
    const runContour = contour(run.map((n) => n.pitch));
    const runDur = normalizeDurations(run.map((n) => n.duration_beats));
    for (const [kind, v, vDur] of variants) {
      const contourOk = v.length === runContour.length && v.every((d, i) => d === runContour[i]);
      const durOk =
        vDur.length === 0 ||
        (runDur.length === vDur.length && vDur.every((d, i) => Math.abs(d - runDur[i]) <= EPS * Math.max(1, Math.abs(d))));
      if (contourOk && durOk) return { match: kind, at_beat: run[0].onset_beat };
    }
  }
  return null;
};

export function motifRecall(schema, perf) {
  const motifsById = new Map((schema.material?.motifs ?? []).map((m) => [m.id, m]));
  const required = schema.constraints?.must_contain;
  // No must_contain: every declared motif is a target (imports infer motifs
  // as recurring patterns — a faithful rendition should recall them).
  const targetIds = required?.length ? required.map(baseRef) : [...motifsById.keys()];
  const detail = [];
  const parts = new Map();
  for (const n of perf.notes ?? []) {
    const arr = parts.get(n.part) ?? [];
    arr.push(n);
    parts.set(n.part, arr);
  }
  for (const notes of parts.values()) notes.sort((a, b) => a.onset_beat - b.onset_beat || a.pitch - b.pitch);
  for (const id of targetIds) {
    const motif = motifsById.get(id);
    if (!motif || !(motif.pitches ?? []).length) {
      // Rhythm-only motifs recall on the duration grid alone (normalized —
      // uniform aug/dim tolerated, same convention as pitch recall).
      if (motif && (motif.durations ?? []).length >= 2) {
        const target = normalizeDurations(motif.durations);
        let hit = null;
        for (const [part, notes] of parts) {
          for (let start = 0; start + target.length <= notes.length; start++) {
            const runDur = normalizeDurations(notes.slice(start, start + target.length).map((n) => n.duration_beats));
            if (target.every((d, i) => Math.abs(d - runDur[i]) <= EPS * Math.max(1, Math.abs(d)))) {
              hit = { match: "rhythm-grid", part, at_beat: notes[start].onset_beat };
              break;
            }
          }
          if (hit) break;
        }
        detail.push(hit ? { id, found: true, ...hit } : { id, found: false, match: "rhythm-grid" });
      } else {
        detail.push({ id, found: false, reason: motif ? "rhythm-only motif (no pitch contour to recall)" : "unknown motif id" });
      }
      continue;
    }
    const pitches = motif.pitches.map(pitchToMidi);
    let hit = null;
    for (const [part, notes] of parts) {
      hit = findMotif(pitches, motif.durations ?? [], notes);
      if (hit) { hit.part = part; break; }
    }
    detail.push(hit ? { id, found: true, ...hit } : { id, found: false });
  }
  const found = detail.filter((d) => d.found).length;
  return { score: detail.length ? found / detail.length : 1, targets: targetIds.length, found, detail };
}

const beatsPerBar = (meter) =>
  (Array.isArray(meter?.beats) ? meter.beats.reduce((a, b) => a + b, 0) : meter?.beats ?? 4) * (4 / (meter?.unit ?? 4));

export function structureFidelity(schema, perf) {
  const sections = new Map((schema.form?.sections ?? []).map((s) => [s.id, s]));
  const order = schema.form?.order ?? [];
  if (order.length === 0) return { score: 1, reason: "no form declared" };
  const barBeats = beatsPerBar(schema.globals?.meter);
  const rep = schema.form?.repetition ?? {};
  let minBars = 0, maxBars = 0;
  for (const id of order) {
    const s = sections.get(id);
    if (!s) continue;
    const bars = s.bars ?? 4;
    const r = rep[id];
    minBars += bars * (r?.min ?? 1);
    maxBars += bars * (r?.max ?? 1);
  }
  const actualBeats = (perf.notes ?? []).reduce((m, n) => Math.max(m, n.onset_beat + n.duration_beats), 0);
  const actualBars = actualBeats / barBeats;
  const deviation = schema.constraints?.structure?.form_deviation ?? "none";
  // abridge sanctions shorter; reorder changes sequence, not length (only
  // total is measurable at the perf layer).
  const inBounds = actualBars >= (deviation === "abridge" ? 0 : minBars) && actualBars <= maxBars + EPS;
  const score = inBounds
    ? 1
    : Math.max(0, 1 - Math.min(Math.abs(actualBars - minBars), Math.abs(actualBars - maxBars)) / Math.max(1, maxBars));
  return {
    score, deviation, expected_bars: [minBars, maxBars], actual_bars: Math.round(actualBars * 1000) / 1000,
    bar_beats: barBeats, sections_in_order: order.length,
  };
}

// Tempo-shape conformance (spec §2.5, v0.3): a perf tempo_map must realize
// every constraints.tempo_shapes entry — rit./accel. as a monotone ramp
// ending at target_bpm within the span; rubato within the deviation band,
// returning to base tempo at section end.
export function tempoShapeConformance(schema, perf) {
  const shapes = schema.constraints?.tempo_shapes ?? {};
  const map = [...(perf.tempo_map ?? [])].sort((a, b) => a.beat - b.beat);
  const barBeats = beatsPerBar(schema.globals?.meter);
  const sections = new Map((schema.form?.sections ?? []).map((s) => [s.id, s]));
  const repetition = schema.form?.repetition ?? {};
  // Section spans in the expanded order (repetition min applied, matching
  // the interpreter's expansion rule); a repeated section's span covers its
  // first through last occurrence.
  const spans = new Map();
  let bar = 0;
  for (const id of schema.form?.order ?? []) {
    const s = sections.get(id);
    if (!s) continue;
    const bars = s.bars ?? 4;
    const reps = repetition[id]?.min ?? 1;
    for (let r = 0; r < reps; r++) {
      const prev = spans.get(id);
      spans.set(id, {
        start: Math.min(prev?.start ?? Infinity, bar * barBeats),
        end: Math.max(prev?.end ?? -Infinity, (bar + bars) * barBeats),
      });
      bar += bars;
    }
  }

  const detail = [];
  for (const [sectionId, shape] of Object.entries(shapes)) {
    const span = spans.get(sectionId);
    if (!span) { detail.push({ section: sectionId, kind: shape.kind, conformant: false, reason: "section not in form" }); continue; }
    const inSpan = map.filter((p) => p.beat >= span.start - EPS && p.beat <= span.end + EPS);
    if (shape.kind === "ritardando" || shape.kind === "accelerando") {
      const dir = shape.kind === "ritardando" ? -1 : +1;
      const points = inSpan.length ? inSpan : map;
      const monotone = points.every((p, i) => i === 0 || dir * (p.bpm - points[i - 1].bpm) >= -EPS);
      const final = points.at(-1);
      const reaches = final && Math.abs(final.bpm - shape.target_bpm) <= EPS;
      detail.push({
        section: sectionId, kind: shape.kind,
        conformant: Boolean(monotone && reaches),
        monotone, final_bpm: final?.bpm, target_bpm: shape.target_bpm,
      });
    } else if (shape.kind === "rubato") {
      const base = map.filter((p) => p.beat < span.start - EPS).at(-1)?.bpm ?? map[0]?.bpm;
      const within = inSpan.every((p) => Math.abs(p.bpm - base) <= shape.deviation_bpm + EPS);
      const last = inSpan.at(-1);
      const returns = last && Math.abs(last.bpm - base) <= EPS;
      detail.push({
        section: sectionId, kind: "rubato",
        conformant: Boolean(within && returns),
        base_bpm: base, deviation_bpm: shape.deviation_bpm,
      });
    } else {
      detail.push({ section: sectionId, kind: shape.kind, conformant: false, reason: "unknown kind" });
    }
  }
  const conformant = detail.filter((d) => d.conformant).length;
  return { score: detail.length ? conformant / detail.length : 1, targets: detail.length, detail };
}

// Harmonic fidelity: for each section wired to a progression, the perf
// notes sounding within that section's span must cover every chord's
// pitch-class set at least once per progression cycle. Pitch classes only
// (voicing is interpretation; content is conformance).
const CHORD_PC = { "": [0, 4, 7], m: [0, 3, 7], maj7: [0, 4, 7, 11], m7: [0, 3, 7, 10], 7: [0, 4, 7, 10], dim: [0, 3, 6], aug: [0, 4, 8] };
const chordPitchClasses = (symbol) => {
  const m = /^([A-G])(#|b)?(.*)$/.exec(symbol);
  if (!m) return null;
  const root = pitchToMidi(`${m[1]}${m[2] ?? ""}0`) % 12;
  return (CHORD_PC[m[3] || ""] ?? CHORD_PC[""]).map((t) => (root + t) % 12);
};

export function harmonicFidelity(schema, perf) {
  const progsById = new Map((schema.material?.harmony?.progressions ?? []).map((p) => [p.id, p]));
  const barBeats = beatsPerBar(schema.globals?.meter);
  const spans = new Map();
  let bar = 0;
  const sections = new Map((schema.form?.sections ?? []).map((s) => [s.id, s]));
  const repetition = schema.form?.repetition ?? {};
  for (const id of schema.form?.order ?? []) {
    const s = sections.get(id);
    if (!s) continue;
    const bars = s.bars ?? 4;
    const reps = repetition[id]?.min ?? 1;
    for (let r = 0; r < reps; r++) {
      const prev = spans.get(id);
      spans.set(id, {
        start: Math.min(prev?.start ?? Infinity, bar * barBeats),
        end: Math.max(prev?.end ?? -Infinity, (bar + bars) * barBeats),
      });
      bar += bars;
    }
  }
  const detail = [];
  for (const [sectionId, span] of spans) {
    const section = sections.get(sectionId);
    const prog = progsById.get(section?.harmony);
    if (!prog) continue;
    const inSpan = (perf.notes ?? []).filter((n) => n.onset_beat >= span.start - EPS && n.onset_beat < span.end - EPS);
    const pcs = new Set(inSpan.map((n) => n.pitch % 12));
    const chords = [];
    for (const chord of prog.chords ?? []) {
      const expected = chordPitchClasses(chord);
      if (!expected) { chords.push({ chord, covered: false, reason: "unparseable chord symbol" }); continue; }
      const missing = expected.filter((pc) => !pcs.has(pc));
      chords.push({ chord, covered: missing.length === 0, ...(missing.length ? { missing_pcs: missing } : {}) });
    }
    const covered = chords.filter((c) => c.covered).length;
    detail.push({ section: sectionId, progression: prog.id, score: chords.length ? covered / chords.length : 1, chords });
  }
  const score = detail.length ? detail.reduce((a, d) => a + d.score, 0) / detail.length : 1;
  return { score, sections: detail.length, detail };
}

export const scorePerformance = (schema, perf) => {
  const motif = motifRecall(schema, perf);
  const structure = structureFidelity(schema, perf);
  const tempoShapes = tempoShapeConformance(schema, perf);
  const harmony = harmonicFidelity(schema, perf);
  return {
    motif_recall: Math.round(motif.score * 1000) / 1000,
    structure_fidelity: Math.round(structure.score * 1000) / 1000,
    tempo_shapes: Math.round(tempoShapes.score * 1000) / 1000,
    harmonic_fidelity: Math.round(harmony.score * 1000) / 1000,
    per_motif: motif.detail,
    structure,
    tempo_shape_detail: tempoShapes.detail,
    harmony_detail: harmony.detail,
  };
};

// Reference performance: every declared motif played once, in id order, on a
// single part. The benchmark floor — a trivially faithful rendition by
// construction; recall below 1.0 on this input means the metric is broken,
// not the performance. Not a musically meaningful render.
export const referencePerformance = (schema, { at = "2026-08-22T00:00:00Z" } = {}) => {
  const notes = [];
  let beat = 0;
  for (const motif of schema.material?.motifs ?? []) {
    const pitches = motif.pitches ?? [];
    const durations = motif.durations ?? pitches.map(() => 1);
    pitches.forEach((p, i) => {
      notes.push({
        part: "p.ref", pitch: pitchToMidi(p), pitch_name: p,
        onset: beat * 0.5, duration: (durations[i] ?? 1) * 0.5,
        onset_beat: beat, duration_beats: durations[i] ?? 1, velocity: 80,
      });
      beat += durations[i] ?? 1;
    });
  }
  return {
    muse_perf_version: "0.1.0",
    metadata: {
      source: { schema_id: schema.metadata?.id ?? "unknown", rendition_id: "r.reference" },
      interpreter: { model: "reference-performance-v0", at },
    },
    tempo_map: [{ time: 0, beat: 0, bpm: 120 }],
    parts: [{ id: "p.ref", name: "Reference", instrument: { name: "piano", program: 0 } }],
    notes,
  };
};

// --- CLI ---
const invokedDirectly = process.argv[1] && path.resolve(process.argv[1]) === new URL(import.meta.url).pathname;
if (invokedDirectly) {
  const [schemaPath, perfPath] = process.argv.slice(2);
  if (!schemaPath || !perfPath) {
    console.error("usage: node benchmark/metrics.mjs <schema.muse.json> <performance.json>");
    process.exit(1);
  }
  const schema = JSON.parse(await readFile(schemaPath, "utf8"));
  const perf = JSON.parse(await readFile(perfPath, "utf8"));
  console.log(JSON.stringify(scorePerformance(schema, perf), null, 2));
}
