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

console.log(`${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
