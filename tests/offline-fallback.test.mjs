// Tests for #91's residual coverage (issue #101, spec:
// tests/open_20260822-154601_offline-fallback.md). Pinned behaviors of the
// offline interpreter's two fallback levels on minimal synthetic docs.
// Standalone: `node tests/offline-fallback.test.mjs`; folded into npm test.
import { expandOffline } from "../interpreter/offline.mjs";

let passed = 0, failed = 0;
const check = (name, cond, detail) => {
  if (cond) { passed++; console.log(`ok   ${name}`); }
  else { failed++; console.error(`FAIL ${name}${detail ? ` — ${detail}` : ""}`); }
};

const motifPool = { motifs: [{ id: "motif.a", kind: "pitch_rhythm", pitches: ["C4", "E4", "G4"], durations: [1, 1, 1] }] };
const baseDoc = (extra = {}) => ({
  muse_version: "0.1.0",
  metadata: { id: "test", title: "t", composer: { name: "t" }, created: "2026-01-01T00:00:00Z", license: { renditions: "closed" }, provenance: [] },
  globals: { tempo: { bpm: 100 }, meter: { beats: 4, unit: 4 }, duration_bars: 8 },
  material: motifPool,
  ...extra,
});
const rendition = { id: "r.default", params: { tempo_bpm: 100 } };

// Level 1: a section with no uses realizes from the bare motif pool
// (the motif-pool fallback, without the doc being form-less).
const sectionless = expandOffline(baseDoc({
  form: { sections: [{ id: "s1", role: "custom", bars: 4 }], order: ["s1"] },
}), rendition);
check("section without uses realizes from the bare motif pool",
  sectionless.notes.some((n) => n.part === "p.lead"));
check("level 1 fallback plays at notated pitch (no +12)",
  !sectionless.notes.some((n) => n.part === "p.lead" && n.pitch === 72 /* C5 */)
  && sectionless.notes.some((n) => n.part === "p.lead" && n.pitch === 60 /* C4 */),
  sectionless.notes.filter((n) => n.part === "p.lead").map((n) => n.pitch).join(","));

// Level 2: a document with no form synthesizes section.default (bars 32).
const formless = expandOffline(baseDoc(), rendition);
check("form-less document synthesizes section.default and still sounds",
  formless.notes.length > 0);
check("form-less fallback also plays at notated pitch",
  formless.notes.some((n) => n.part === "p.lead" && n.pitch === 60));

// Uses-driven realization transposes +12; fallback sections in the same
// document stay at notated pitch (both policies in one doc).
const mixed = expandOffline(baseDoc({
  material: {
    ...motifPool,
    themes: [{ id: "theme.1", phrases: [{ motifs: ["motif.a"] }] }],
  },
  form: {
    sections: [
      { id: "used", role: "verse", bars: 4, uses: [{ ref: "theme.1" }] },
      { id: "bare", role: "custom", bars: 4 },
    ],
    order: ["used", "bare"],
  },
}), rendition);
check("uses-driven section transposes +12 (C5 = 72 present)",
  mixed.notes.some((n) => n.part === "p.lead" && n.pitch === 72));
check("fallback section in the same doc stays at notated pitch",
  mixed.notes.some((n) => n.part === "p.lead" && n.pitch === 60 && n.onset_beat >= 16));

// Bed interaction: a fallback section with no harmony gets no p.bed notes.
check("fallback section without harmony: no bed notes (all lead)",
  sectionless.notes.every((n) => n.part !== "p.bed"));

// Repetition guard: a doc whose form declares repetition for a real section
// must never receive the synthetic section.default.
const withRep = expandOffline(baseDoc({
  form: {
    sections: [{ id: "s1", role: "custom", bars: 2 }],
    order: ["s1"],
    repetition: { s1: { min: 3, max: 3 } },
  },
}), rendition);
check("repetition on a real section suppresses section.default",
  !withRep.notes.some((n) => n.onset_beat >= 2 * 4 * 3));
check("repetition honored on the real section (3 occurrences)",
  withRep.notes.filter((n) => n.part === "p.lead").length === 9);
// Form with sections but empty order AND no repetition still drives
// existing section ids, not section.default.
const emptyOrder = expandOffline(baseDoc({
  form: { sections: [{ id: "s1", role: "custom", bars: 2 }] },
}), rendition);
check("sections present but order empty: section ids used, no section.default",
  emptyOrder.notes.length > 0 && emptyOrder.notes.every((n) => n.onset_beat < 2 * 4));

// Tempo-shape decision pin (spec's open item): a tempo_shape keyed to
// section.default *does* fire in the fallback path — the fallback
// synthesizes the section under that exact id, and the shape realization
// keys on section ids uniformly, so the constraint follows the material
// into synthetic space. Decided as the sane behavior (a composer who knows
// the fallback convention can constrain it); pinned so a future change is
// deliberate.
const shapedDefault = expandOffline(baseDoc({
  constraints: { tempo_shapes: { "section.default": { kind: "ritardando", target_bpm: 60 } } },
}), rendition);
check("tempo_shapes on section.default fires (decided: constraints follow into synthetic sections)",
  shapedDefault.tempo_map.some((t) => t.bpm === 60));
// Keyed to a real section works (positive pin).
const shapedReal = expandOffline(baseDoc({
  form: { sections: [{ id: "s1", role: "custom", bars: 4 }], order: ["s1"] },
  constraints: { tempo_shapes: { s1: { kind: "ritardando", target_bpm: 60 } } },
}), rendition);
check("tempo_shapes on a real section produces a ramp to target_bpm",
  shapedReal.tempo_map.some((t) => t.bpm === 60));

// WAV smoke: one corpus chorale renders through the play path to a
// non-silent WAV (renderWav over the offline expansion).
const { readFileSync } = await import("node:fs");
const { renderWav, render } = await import("../player/render.mjs");
const chorale = JSON.parse(readFileSync("benchmark/corpus/bwv269.muse.json", "utf8"));
const wavPerf = expandOffline(chorale, { id: "r.default", params: {} });
check("corpus chorale expands to non-zero notes", wavPerf.notes.length > 0);
const channels = render(wavPerf, { sampleRate: 8000 });
check("corpus chorale renders non-silent audio",
  channels[0].some((v) => v !== 0));
const wav = renderWav(wavPerf, { sampleRate: 8000 });
check("corpus chorale WAV is a valid RIFF",
  wav.subarray(0, 4).toString() === "RIFF" && wav.length > 44);

console.log(`${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
