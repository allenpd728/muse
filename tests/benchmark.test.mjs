// Tests for benchmark/metrics.mjs (issue #72): conformance metrics harness.
// Standalone runner: `node tests/benchmark.test.mjs`; also folded into npm test.
import { mkdtemp, readFile, writeFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { motifRecall, structureFidelity, scorePerformance, referencePerformance, tempoShapeConformance, harmonicFidelity } from "../benchmark/metrics.mjs";
import { expandOffline } from "../interpreter/offline.mjs";

const full = JSON.parse(await readFile(new URL("../examples/full.muse.json", import.meta.url), "utf8"));

let passed = 0, failed = 0;
const check = (name, cond) => {
  if (cond) { passed++; console.log(`ok   ${name}`); }
  else { failed++; console.error(`FAIL ${name}`); }
};

// A tiny schema + perf builders for controlled cases.
const schema = (motifs, extra = {}) => ({
  material: { motifs },
  form: { sections: [{ id: "s1", role: "verse", bars: 4 }], order: ["s1"] },
  constraints: { must_contain: motifs.map((m) => m.id) },
  globals: { meter: { beats: 4, unit: 4 } },
  ...extra,
});
const motif = { id: "motif.a", kind: "pitch_rhythm", pitches: ["D4", "F4", "A4", "G4"], durations: [0.5, 0.5, 1, 1] };
const note = (pitches, durs, beat0 = 0) => {
  let b = beat0;
  return pitches.map((p, i) => ({ part: "p1", pitch: p, pitch_name: "X4", onset: b * 0.5, duration: durs[i] * 0.5, onset_beat: b, duration_beats: durs[i], velocity: 80, ...((b += durs[i]), {}) }));
};
const perf = (notes) => ({ notes, parts: [{ id: "p1" }] });

// Motif recall — exact, and each tolerated transform family.
const s1 = schema([motif]);
check("exact recall", motifRecall(s1, perf(note([62, 65, 69, 67], [0.5, 0.5, 1, 1]))).score === 1);
check("transposition counts as recall", (() => {
  const r = motifRecall(s1, perf(note([64, 67, 71, 69], [0.5, 0.5, 1, 1]))); // +2
  return r.score === 1 && r.detail[0].match === "exact";
})());
check("augmentation counts as recall (uniformly scaled durations)",
  motifRecall(s1, perf(note([62, 65, 69, 67], [1, 1, 2, 2]))).score === 1);
check("diminution counts as recall",
  motifRecall(s1, perf(note([62, 65, 69, 67], [0.25, 0.25, 0.5, 0.5]))).score === 1);
check("inversion counts as recall", (() => {
  const r = motifRecall(s1, perf(note([62, 59, 55, 57], [0.5, 0.5, 1, 1]))); // inv about D4
  return r.score === 1 && r.detail[0].match === "inversion";
})());
check("retrograde counts as recall", (() => {
  const r = motifRecall(s1, perf(note([67, 69, 65, 62], [1, 1, 0.5, 0.5]))); // reversed pitches + durations
  return r.score === 1 && r.detail[0].match === "retrograde";
})());
check("wrong contour does not recall",
  motifRecall(s1, perf(note([62, 66, 69, 67], [0.5, 0.5, 1, 1]))).score === 0);
check("wrong durations (non-uniform) do not recall",
  motifRecall(s1, perf(note([62, 65, 69, 67], [0.5, 1, 0.5, 1]))).score === 0);
check("must_contain transform suffix strips to base id", (() => {
  const s = schema([motif]); s.constraints.must_contain = ["motif.a#seq(+2)"];
  return motifRecall(s, perf(note([62, 65, 69, 67], [0.5, 0.5, 1, 1]))).score === 1;
})());
check("unknown must_contain id scores 0 with reason", (() => {
  const s = schema([motif]); s.constraints.must_contain = ["motif.ghost"];
  const r = motifRecall(s, perf(note([62, 65, 69, 67], [0.5, 0.5, 1, 1])));
  return r.score === 0 && r.detail[0].reason;
})());
check("no must_contain → all declared motifs are targets", (() => {
  const s = schema([motif, { id: "motif.b", kind: "pitch", pitches: ["C4", "E4", "G4"] }]);
  delete s.constraints.must_contain;
  const r = motifRecall(s, perf([...note([62, 65, 69, 67], [0.5, 0.5, 1, 1]), ...note([60, 64, 67], [1, 1, 1], 4)]));
  return r.score === 1 && r.targets === 2;
})());
check("partial recall reports per-motif detail", (() => {
  const s = schema([motif, { id: "motif.b", kind: "pitch", pitches: ["C4", "E4", "G4"] }]);
  const r = motifRecall(s, perf(note([62, 65, 69, 67], [0.5, 0.5, 1, 1])));
  return r.score === 0.5 && r.detail.find((d) => d.id === "motif.b").found === false;
})());

// Structure fidelity.
check("in-bounds form scores 1", structureFidelity(schema([motif]), perf(note([62, 65, 69, 67], [4, 4, 4, 4]))).score === 1);
check("short form penalized", (() => {
  const r = structureFidelity(schema([motif]), perf(note([62, 65, 69, 67], [1, 1, 1, 1])));
  return r.score < 1 && r.actual_bars === 1;
})());
check("repetition bounds respected", (() => {
  const s = schema([motif]); s.form.repetition = { s1: { min: 2, max: 4 } };
  const good = structureFidelity(s, perf(note([62, 65, 69, 67], [8, 8, 8, 8])));   // 8 bars ∈ [8,16]
  const bad = structureFidelity(s, perf(note([62, 65, 69, 67], [4, 4, 4, 4])));    // 4 bars < 8
  return good.score === 1 && bad.score < 1;
})());
check("abridge sanctions shorter forms", (() => {
  const s = schema([motif]); s.constraints.structure = { form_deviation: "abridge" };
  return structureFidelity(s, perf(note([62, 65, 69, 67], [1, 1, 1, 1]))).score === 1;
})());
check("overlong form penalized even under abridge", (() => {
  const s = schema([motif]); s.constraints.structure = { form_deviation: "abridge" };
  return structureFidelity(s, perf(note([62, 65, 69, 67], [8, 8, 8, 8]))).score < 1;
})());
check("no form declared scores 1", structureFidelity({ material: {} }, perf([])).score === 1);

// End-to-end: offline-expanded full example scores clean.
{
  const perfDoc = expandOffline(full, full.renditions[0]);
  const r = scorePerformance(full, perfDoc);
  check("full example synthwave: motif_recall 1", r.motif_recall === 1);
  check("full example synthwave: structure_fidelity 1 (repetition min honored)",
    r.structure_fidelity === 1);
  check("full example synthwave: tempo_shapes conformance 1 (cadenza rit. realized)",
    r.tempo_shapes === 1);
}

// Tempo-shape conformance (v0.3, issue #84): the semantic half of the
// constraints.tempo_shapes contract.
{
  const shapeSchema = (shape) => ({
    material: {},
    form: { sections: [{ id: "s1", role: "verse", bars: 4 }], order: ["s1"] },
    constraints: { tempo_shapes: { s1: shape } },
    globals: { meter: { beats: 4, unit: 4 } },
  });
  const ramp = (from, to, beats) => ({
    tempo_map: [{ time: 0, beat: 0, bpm: from }, { time: beats * 0.5, beat: beats, bpm: to }],
    notes: [],
  });
  check("ritardando: monotone ramp to target conforms",
    tempoShapeConformance(shapeSchema({ kind: "ritardando", target_bpm: 72 }), ramp(96, 72, 16)).score === 1);
  check("accelerando: monotone ramp up to target conforms",
    tempoShapeConformance(shapeSchema({ kind: "accelerando", target_bpm: 120 }), ramp(96, 120, 16)).score === 1);
  check("ritardando: ramp not reaching target fails", (() => {
    const r = tempoShapeConformance(shapeSchema({ kind: "ritardando", target_bpm: 72 }), ramp(96, 80, 16));
    return r.score === 0 && r.detail[0].conformant === false;
  })());
  check("ritardando: non-monotone ramp fails", (() => {
    const wobble = { tempo_map: [{ time: 0, beat: 0, bpm: 96 }, { time: 4, beat: 8, bpm: 100 }, { time: 8, beat: 16, bpm: 72 }], notes: [] };
    return tempoShapeConformance(shapeSchema({ kind: "ritardando", target_bpm: 72 }), wobble).score === 0;
  })());
  check("rubato: bounded deviation returning to base conforms", (() => {
    const rub = { tempo_map: [
      { time: 0, beat: 0, bpm: 100 }, { time: 4, beat: 8, bpm: 96 }, { time: 8, beat: 16, bpm: 100 },
    ], notes: [] };
    return tempoShapeConformance(shapeSchema({ kind: "rubato", deviation_bpm: 6 }), rub).score === 1;
  })());
  check("rubato: deviation beyond band fails", (() => {
    const rub = { tempo_map: [
      { time: 0, beat: 0, bpm: 100 }, { time: 4, beat: 8, bpm: 88 }, { time: 8, beat: 16, bpm: 100 },
    ], notes: [] };
    return tempoShapeConformance(shapeSchema({ kind: "rubato", deviation_bpm: 6 }), rub).score === 0;
  })());
  check("rubato: not returning to base tempo fails", (() => {
    const rub = { tempo_map: [
      { time: 0, beat: 0, bpm: 100 }, { time: 4, beat: 8, bpm: 96 }, { time: 8, beat: 16, bpm: 96 },
    ], notes: [] };
    return tempoShapeConformance(shapeSchema({ kind: "rubato", deviation_bpm: 6 }), rub).score === 0;
  })());
  check("no tempo_shapes → score 1 (vacuous)",
    tempoShapeConformance(schema([motif]), perf([])).score === 1);
}

// Rhythm-only motif recall (issue #90): duration-grid match, normalized.
{
  const rhythmMotif = { id: "motif.r", kind: "rhythm", durations: [0.25, 0.25, 0.5] };
  const s = schema([rhythmMotif]);
  check("rhythm-only motif recalls on duration grid",
    motifRecall(s, perf(note([60, 62, 64], [0.25, 0.25, 0.5]))).score === 1);
  check("rhythm grid tolerates uniform scaling (aug/dim)",
    motifRecall(s, perf(note([60, 62, 64], [0.5, 0.5, 1]))).score === 1);
  check("rhythm grid rejects wrong durations",
    motifRecall(s, perf(note([60, 62, 64], [0.5, 0.25, 0.25]))).score === 0);
  check("rhythm grid matches anywhere in the note stream",
    motifRecall(s, perf([...note([70], [2], 0), ...note([60, 62, 64], [0.25, 0.25, 0.5], 2)])).score === 1);
}

// Harmonic fidelity (issue #90): chord pitch-class coverage per section.
{
  const harmSchema = {
    material: { harmony: { progressions: [{ id: "prog.1", chords: ["Dm7", "G7"], bars_per_chord: 1 }] } },
    form: { sections: [{ id: "s1", role: "verse", bars: 2, harmony: "prog.1" }], order: ["s1"] },
    globals: { meter: { beats: 4, unit: 4 } },
  };
  const fullCoverage = perf(note([50, 53, 57, 60, 55, 59, 62, 65], [1, 1, 1, 1, 1, 1, 1, 1])); // D F A C + G B D F
  check("all chords covered → harmonic fidelity 1",
    harmonicFidelity(harmSchema, fullCoverage).score === 1);
  check("missing chord tone drops the chord's coverage", (() => {
    const noC = perf(note([50, 53, 57, 55, 59, 62, 65], [1, 1, 1, 1, 1, 1, 1])); // no C (pc 0)
    const r = harmonicFidelity(harmSchema, noC);
    return r.score === 0.5 && r.detail[0].chords.find((c) => c.chord === "Dm7").covered === false;
  })());
  check("voicing irrelevant — pitch classes in any octave count",
    harmonicFidelity(harmSchema, perf(note([38, 41, 45, 48, 43, 47, 50, 53], [1, 1, 1, 1, 1, 1, 1, 1]))).score === 1);
  check("section without harmony progression is skipped (vacuous)",
    harmonicFidelity(schema([motif]), perf([])).score === 1);
}

// DoD: ≥2 corpus entries scored end-to-end — reference performance (the
// benchmark floor) scores recall 1.0; dropping a motif scores below.
{
  let scored = 0;
  for (const name of ["bwv269.muse.json", "bwv316.muse.json"]) {
    const corpus = JSON.parse(await readFile(new URL(`../benchmark/corpus/${name}`, import.meta.url), "utf8"));
    const r = scorePerformance(corpus, referencePerformance(corpus));
    check(`corpus ${name}: reference performance recall 1.0`, r.motif_recall === 1);
    const corrupted = referencePerformance(corpus);
    corrupted.notes = corrupted.notes.filter((n) => n.onset_beat > 0 || n.pitch !== corrupted.notes[0].pitch);
    const c = scorePerformance(corpus, corrupted);
    check(`corpus ${name}: corrupted performance recall < 1`, c.motif_recall < 1);
    scored++;
  }
  check("≥2 corpus entries scored", scored >= 2);
}

// CLI contract: JSON report with the promised fields.
{
  const tmp = await mkdtemp(path.join(tmpdir(), "muse-bench-"));
  try {
    const perfDoc = expandOffline(full, full.renditions[0]);
    const p = path.join(tmp, "perf.json");
    await writeFile(p, JSON.stringify(perfDoc));
    const r = spawnSync(process.execPath, ["benchmark/metrics.mjs", "examples/full.muse.json", p], { encoding: "utf8" });
    check("CLI exits 0", r.status === 0);
    const report = JSON.parse(r.stdout);
    check("CLI report has motif_recall / structure_fidelity / per-motif detail",
      "motif_recall" in report && "structure_fidelity" in report && Array.isArray(report.per_motif));
  } finally {
    await rm(tmp, { recursive: true, force: true });
  }
}

console.log(`${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
