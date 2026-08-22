// IR → .muse.json synthesis (issue #19, per docs/scope-importer.md).
// Flattening: globals take opening tempo/meter/key; tempo.range = observed
// [min,max] across the map when it varies. Mid-piece meter/key changes are
// dropped from globals (spec v0 has no per-section overrides — scope doc).
// Heuristic inferences (motifs, sections) are marked in
// extensions.importer.inferred — never silently guessed.
import { midiToPitch, normalizeIR, validateIR } from "./ir.mjs";

// Motif heuristic: length ≥ 3 notes, ≥ 2 occurrences, transposition counts
// as recurrence — so the search key is the interval contour + duration grid,
// not absolute pitches.
const motifKey = (seq) =>
  seq.map((n, i) => (i === 0 ? `d${n.durationBeats}` : `${n.midi - seq[i - 1].midi},d${n.durationBeats}`)).join("|");

const extractMotifs = (parts, { minLen = 3, minOccurrences = 2 } = {}) => {
  const counts = new Map(); // key -> { count, firstSeq }
  for (const part of parts) {
    const notes = part.notes;
    for (let len = minLen; len <= notes.length; len++) {
      for (let start = 0; start + len <= notes.length; start++) {
        const seq = notes.slice(start, start + len);
        const key = `${len}:${motifKey(seq)}`;
        const hit = counts.get(key) ?? { count: 0, firstSeq: seq };
        hit.count++;
        counts.set(key, hit);
      }
    }
  }
  // Prefer longest patterns; drop a pattern fully contained in a longer kept one.
  const hits = [...counts.entries()]
    .filter(([, v]) => v.count >= minOccurrences)
    .sort((a, b) => Number(b[0].split(":")[0]) - Number(a[0].split(":")[0]));
  const kept = [];
  for (const [key, v] of hits) {
    if (!kept.some((k) => k[0].endsWith(key.slice(key.indexOf(":"))))) kept.push([key, v]);
  }
  return kept.slice(0, 8).map(([, v], i) => ({
    id: `motif.${i + 1}`,
    kind: "pitch_rhythm",
    pitches: v.firstSeq.map((n) => midiToPitch(n.midi)),
    durations: v.firstSeq.map((n) => n.durationBeats),
  }));
};

// Section detection: exact repeated multi-bar pitch content blocks, per part.
const detectSections = (parts, beatsPerBar) => {
  const occurrences = new Map(); // contentKey -> count
  const barCount = (notes) => Math.max(1, Math.ceil(Math.max(0, ...notes.map((n) => n.onsetBeat + n.durationBeats)) / beatsPerBar));
  for (const part of parts) {
    const bars = barCount(part.notes);
    for (let start = 0; start < bars; start++) {
      const inBar = part.notes.filter((n) => n.onsetBeat >= start * beatsPerBar && n.onsetBeat < (start + 1) * beatsPerBar);
      if (inBar.length < 2) continue;
      const key = inBar.map((n) => `${n.midi}@${(n.onsetBeat - start * beatsPerBar).toFixed(3)}+${n.durationBeats}`).join("|");
      occurrences.set(key, (occurrences.get(key) ?? 0) + 1);
    }
  }
  return [...occurrences.values()].some((c) => c >= 2);
};

// Opening meter → beats per bar (quarter-note units).
const beatsPerBarOf = (meter) => {
  if (!meter) return 4;
  const beats = Array.isArray(meter.beats) ? meter.beats.reduce((a, b) => a + b, 0) : meter.beats;
  return beats * (4 / meter.unit);
};

export function synthesize(ir, { title = "Imported work", source = "unknown" } = {}) {
  const errors = validateIR(ir);
  if (errors.length) throw new Error(`invalid IR: ${errors.join("; ")}`);
  const doc = normalizeIR(ir);
  const inferred = [];

  const openingTempo = doc.tempoMap[0]?.bpm ?? 120;
  if (!doc.tempoMap.length) inferred.push({ path: "globals.tempo.bpm", reason: "no tempo in source; defaulted to 120" });
  const bpms = doc.tempoMap.map((t) => t.bpm);
  const tempo = { bpm: openingTempo };
  if (bpms.length > 1 && Math.min(...bpms) !== Math.max(...bpms)) tempo.range = [Math.min(...bpms), Math.max(...bpms)];

  const globals = { tempo, duration_bars: 1 };
  if (doc.meterMap.length) {
    globals.meter = { beats: doc.meterMap[0].beats, unit: doc.meterMap[0].unit };
    if (doc.meterMap.length > 1) inferred.push({ path: "globals.meter", reason: "mid-piece meter changes dropped (spec v0 has no per-section overrides)" });
  }
  if (doc.keyMap.length) {
    globals.key = doc.keyMap[0].mode ? { tonic: doc.keyMap[0].tonic, mode: doc.keyMap[0].mode } : { tonic: doc.keyMap[0].tonic };
    if (doc.keyMap.length > 1) inferred.push({ path: "globals.key", reason: "mid-piece key changes dropped (spec v0)" });
  }
  const lastBeat = Math.max(0, ...doc.parts.flatMap((p) => p.notes.map((n) => n.onsetBeat + n.durationBeats)));
  globals.duration_bars = Math.max(1, Math.ceil(lastBeat / beatsPerBarOf(globals.meter)));

  const motifs = extractMotifs(doc.parts);
  const material = {};
  if (motifs.length) {
    material.motifs = motifs;
    inferred.push({ path: "material.motifs", reason: `heuristic extraction: ${motifs.length} repeated interval/duration pattern(s) (≥3 notes, ≥2 occurrences, transposition counts)` });
  }

  let form;
  if (detectSections(doc.parts, beatsPerBarOf(globals.meter))) {
    form = {
      sections: [{ id: "section.1", role: "custom", bars: globals.duration_bars }],
      order: ["section.1"],
    };
    inferred.push({ path: "form.sections", reason: "repeated bar content detected; collapsed to one custom section — role and structure need cleanup" });
  }

  const out = {
    muse_version: "0.1.0",
    metadata: {
      id: `muse:work:${ulid()}`,
      title,
      composer: { name: "unknown (imported)" },
      created: new Date().toISOString(),
      license: { renditions: "closed" },
      provenance: [{ event: "import", actor: "importer", at: new Date().toISOString(), ai: false, notes: `source: ${source}` }],
    },
    globals,
    renditions: [{
      id: "r.default",
      name: "Default",
      params: { tempo_bpm: openingTempo, instrumentation: doc.parts.map((p) => p.name) },
      author: { name: "unknown (imported)" },
    }],
    extensions: inferred.length ? { importer: { inferred } } : undefined,
  };
  if (Object.keys(material).length) out.material = material;
  if (form) out.form = form;
  if (!out.extensions) delete out.extensions;
  return out;
}

// Minimal ULID (Crockford base32, time-seeded) — enough for import provenance,
// not a general id service.
function ulid() {
  const C = "0123456789ABCDEFGHJKMNPQRSTVWXYZ";
  const time = Date.now();
  let id = "";
  let t = time;
  for (let i = 0; i < 10; i++) { id = C[t % 32] + id; t = Math.floor(t / 32); }
  const rand = new Uint8Array(16);
  globalThis.crypto.getRandomValues(rand);
  return id + [...rand].map((b) => C[b % 32]).join("");
}
