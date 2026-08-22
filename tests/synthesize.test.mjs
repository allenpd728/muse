// Tests for importer/synthesize.mjs (issue #19): IR → .muse.json per the
// scope doc — flattened globals, marked heuristic inferences, one default
// rendition, and the output must validate against the root schema.
// Standalone runner: `node tests/synthesize.test.mjs`; folded into npm test.
import { readFile } from "node:fs/promises";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { midiToIR } from "../importer/midi.mjs";
import { synthesize } from "../importer/synthesize.mjs";

let passed = 0, failed = 0;
const check = (name, cond) => {
  if (cond) { passed++; console.log(`ok   ${name}`); }
  else {
    failed++;
    console.error(`FAIL ${name}`);
  }
};

// Flat IR with a repeated interval/duration pattern (C-D-E twice, then
// transposed F-G-A), a tempo change, and one 3/4 meter.
const ir = {
  tempoMap: [{ beat: 0, bpm: 100 }, { beat: 4, bpm: 80 }],
  meterMap: [{ beat: 0, beats: 3, unit: 4 }],
  keyMap: [],
  parts: [{
    id: "track.1", name: "Lead", program: 40,
    notes: [
      { midi: 60, onsetBeat: 0, durationBeats: 1, velocity: 100 },
      { midi: 62, onsetBeat: 1, durationBeats: 1, velocity: 100 },
      { midi: 64, onsetBeat: 2, durationBeats: 1, velocity: 100 },
      { midi: 65, onsetBeat: 4, durationBeats: 1, velocity: 100 },
      { midi: 67, onsetBeat: 5, durationBeats: 1, velocity: 100 },
      { midi: 69, onsetBeat: 6, durationBeats: 1, velocity: 100 },
    ],
  }],
};
const out = synthesize(ir, { title: "synthesis test", source: "inline" });

check("opening tempo becomes globals.tempo.bpm", out.globals.tempo.bpm === 100);
check("varying tempo map becomes globals.tempo.range", JSON.stringify(out.globals.tempo.range) === "[80,100]");
check("opening meter flattened", out.globals.meter.beats === 3 && out.globals.meter.unit === 4);
check("duration_bars derived from content", out.globals.duration_bars >= 2);
check("repeated pattern extracted as motif", out.material?.motifs?.length >= 1
  && out.material.motifs[0].pitches.join() === "C4,D4,E4");
check("inference marked, not silent", out.extensions?.importer?.inferred?.some((e) => e.path === "material.motifs"));
check("one default rendition", out.renditions.length === 1 && out.renditions[0].id === "r.default"
  && out.renditions[0].name === "Default" && out.renditions[0].params.tempo_bpm === 100);
check("rendition instrumentation from part names", out.renditions[0].params.instrumentation.join() === "Lead");
check("provenance records the import", out.metadata.provenance.length === 1
  && out.metadata.provenance[0].event === "import" && out.metadata.provenance[0].ai === false);
check("no style invented on the default rendition", out.renditions[0].style === undefined);

// No repeated content → no motifs, no form guess, no extensions.
const flat = synthesize({ ...ir, parts: [{ id: "t", name: "T", notes: [{ midi: 60, onsetBeat: 0, durationBeats: 1 }] }] }, { source: "flat" });
check("no heuristic content → no motifs/form/extensions", flat.material === undefined && flat.form === undefined && flat.extensions === undefined);

// Constant tempo → no range emitted.
const constant = synthesize({ ...ir, tempoMap: [{ beat: 0, bpm: 96 }] }, { source: "constant" });
check("constant tempo omits range", constant.globals.tempo.bpm === 96 && constant.globals.tempo.range === undefined);

// Output validates against the root schema (DoD: passes npm test).
const tmp = fileURLToPath(new URL("./synthesize-out.tmp.muse.json", import.meta.url));
const { writeFile, rm } = await import("node:fs/promises");
await writeFile(tmp, JSON.stringify(out, null, 2));
const r = spawnSync(process.execPath, ["tools/validate.mjs", tmp], { encoding: "utf8" });
check("synthesized document validates against schema/muse.schema.json", r.status === 0);
if (r.status !== 0) console.error(r.stderr);
await rm(tmp, { force: true });

// --- Residual pins (issue #57, spec: tests/open_20260822-115500_synthesis.md) ---

// Section detection: genuinely repeated multi-bar block → form with the
// inference marked in extensions.importer.inferred.
const quarter = (midi, onset) => ({ midi, onsetBeat: onset, durationBeats: 1, velocity: 90 });
const repeatedBlock = {
  tempoMap: [{ beat: 0, bpm: 100 }],
  meterMap: [{ beat: 0, beats: 4, unit: 4 }],
  keyMap: [],
  parts: [{
    id: "t", name: "T",
    notes: [
      quarter(60, 0), quarter(64, 1), quarter(67, 2), quarter(72, 3),   // bar 1
      quarter(60, 4), quarter(64, 5), quarter(67, 6), quarter(72, 7),   // bar 2 = bar 1
    ],
  }],
};
const blocked = synthesize(repeatedBlock, { source: "block" });
check("repeated multi-bar block produces form.sections", blocked.form?.sections?.length >= 1);
check("section inference marked in extensions", blocked.extensions?.importer?.inferred?.some((e) => e.path === "form.sections"));

// Key map flattening: opening key wins; mid-piece change dropped + marked.
const keyChange = synthesize({
  ...repeatedBlock,
  keyMap: [{ beat: 0, tonic: "C", mode: "major" }, { beat: 4, tonic: "G", mode: "major" }],
}, { source: "keychange" });
check("opening key becomes globals.key", keyChange.globals.key?.tonic === "C" && keyChange.globals.key?.mode === "major");
check("mid-piece key change dropped and marked", keyChange.extensions?.importer?.inferred?.some((e) => e.path === "globals.key"));

// Atonal key: no mode emitted (globals.schema anyOf requires mode unless atonal).
const atonal = synthesize({ ...repeatedBlock, keyMap: [{ beat: 0, tonic: "atonal" }] }, { source: "atonal" });
check("atonal key emits tonic only, no mode", atonal.globals.key?.tonic === "atonal" && !("mode" in atonal.globals.key));

// Cross-part recurrence: a pattern played once per part still counts.
const crossPart = synthesize({
  tempoMap: [{ beat: 0, bpm: 100 }],
  meterMap: [],
  keyMap: [],
  parts: [
    { id: "a", name: "A", notes: [quarter(60, 0), quarter(62, 1), quarter(64, 2)] },
    { id: "b", name: "B", notes: [quarter(67, 0), quarter(69, 1), quarter(71, 2)] },
  ],
}, { source: "crosspart" });
check("pattern repeated across parts extracted as motif", (crossPart.material?.motifs?.length ?? 0) >= 1);

// Empty IR: validates, tempo defaults to 120 and is marked inferred.
const empty = synthesize({ tempoMap: [], meterMap: [], keyMap: [], parts: [] }, { source: "empty" });
check("empty IR defaults tempo to 120 and marks it", empty.globals.tempo.bpm === 120
  && empty.extensions?.importer?.inferred?.some((e) => e.path === "globals.tempo.bpm"));

// Long-pattern dedup — pinned as implemented: a shorter repeated pattern is
// dropped when it shares its full interval/duration key with the trailing
// segment of a longer kept pattern (keys are suffix-compared). A longer
// motif whose tail echoes a shorter motif's intervals suppresses the shorter
// one even when they are musically distinct figures.
const tailEcho = synthesize({
  tempoMap: [{ beat: 0, bpm: 100 }],
  meterMap: [],
  keyMap: [],
  parts: [{
    id: "t", name: "T",
    // F-G-A-D (intervals 2,2,5) twice, then C-D-E (2,2) twice — the 3-note
    // motif's key is a suffix of the 4-note key.
    notes: [65, 67, 69, 74, 65, 67, 69, 74, 60, 62, 64, 60, 62, 64].map((m, i) => quarter(m, i)),
  }],
}, { source: "tailecho" });
const tailMotifs = tailEcho.material?.motifs ?? [];
check("shorter pattern sharing the longer key's tail is dropped",
  !tailMotifs.some((m) => m.pitches.join() === "C4,D4,E4")
  && tailMotifs.some((m) => m.pitches.join() === "F4,G4,A4,D5"));

// The same 3-note figure on its own (no longer pattern whose tail matches)
// extracts normally — the suppression above is purely key-suffix mechanics.
const solo = synthesize({
  tempoMap: [{ beat: 0, bpm: 100 }],
  meterMap: [],
  keyMap: [],
  parts: [{
    id: "t", name: "T",
    notes: [60, 62, 64, 60, 62, 64].map((m, i) => quarter(m, i)),
  }],
}, { source: "solo" });
check("uncontained 3-note pattern extracts on its own", (solo.material?.motifs ?? []).some((m) => m.pitches.join() === "C4,D4,E4"));

// --- Theme assembly + uses wiring (issue #92) ---

// IR designed so extraction yields overlapping motifs: the ABCD figure and
// its BCD suffix both recur, so the kept set contains chainable motifs.
const chainIr = {
  tempoMap: [{ beat: 0, bpm: 100 }],
  meterMap: [{ beat: 0, beats: 4, unit: 4 }],
  keyMap: [],
  parts: [{
    id: "t", name: "T",
    // A B C D | A B C D | B C D | B C D  (quarter notes)
    notes: [60, 62, 64, 65, 60, 62, 64, 65, 62, 64, 65, 62, 64, 65].map((m, i) => quarter(m, i)),
  }],
};
const chained = synthesize(chainIr, { source: "chain" });
const chainedThemes = chained.material?.themes ?? [];
check("overlapping motifs assemble into ≥1 theme", chainedThemes.length >= 1);
check("theme references real motif ids (no dangling refs)", (() => {
  const motifIds = new Set((chained.material?.motifs ?? []).map((m) => m.id));
  return chainedThemes.every((t) => t.phrases.every((p) => p.motifs.every((r) => motifIds.has(r.split("#")[0]))));
})());
check("section uses wired when themes exist",
  (chained.form?.sections?.[0]?.uses ?? []).length >= 1);
check("theme assembly marked in extensions.importer.inferred",
  (chained.extensions?.importer?.inferred ?? []).some((i) => i.path === "material.themes")
  && (chained.extensions?.importer?.inferred ?? []).some((i) => i.path === "form.sections[].uses"));
{
  const { mkdtemp, writeFile, rm } = await import("node:fs/promises");
  const { tmpdir } = await import("node:os");
  const path = await import("node:path");
  const tmp = await mkdtemp(path.join(tmpdir(), "muse-synth-"));
  try {
    const p = path.join(tmp, "chained.muse.json");
    await writeFile(p, JSON.stringify(chained));
    const r = spawnSync(process.execPath, ["tools/validate.mjs", p, "schema/muse.schema.json"], { encoding: "utf8" });
    check("assembled doc validates against the root schema", r.status === 0);
  } finally {
    await rm(tmp, { recursive: true, force: true });
  }
}

// No overlap → no themes, sections fall back to the bare motif pool.
const noChain = synthesize({
  tempoMap: [{ beat: 0, bpm: 100 }],
  meterMap: [{ beat: 0, beats: 4, unit: 4 }],
  keyMap: [],
  parts: [{
    id: "t", name: "T",
    // Two unrelated figures, each repeated: C-E-G twice, D-F-A twice.
    notes: [60, 64, 67, 60, 64, 67, 62, 65, 69, 62, 65, 69].map((m, i) => quarter(m, i)),
  }],
}, { source: "nochain" });
check("no overlap → no themes, uses wired to bare motif pool",
  (noChain.material?.themes ?? []).length === 0
  && (noChain.form?.sections?.[0]?.uses ?? []).every((u) => u.ref.startsWith("motif.")));

// Determinism: same IR → same themes (modulo provenance/id freshness).
const again = synthesize(chainIr, { source: "chain" });
check("theme assembly deterministic",
  JSON.stringify(again.material?.themes) === JSON.stringify(chained.material?.themes));

console.log(`${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
