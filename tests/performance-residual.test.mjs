// Residual coverage for schema/performance.schema.json (issue #62, spec:
// tests/closed_…_performance-schema.md). Covers the pins the task suite leaves:
// harness perf-channel decision, §7-example conformance, tempo_map ordering,
// controller set sealed. Standalone runner; folded into npm test.
import { readFile, readdir } from "node:fs/promises";
import Ajv from "ajv/dist/2020.js";
import addFormats from "ajv-formats";

const dir = new URL("../schema/", import.meta.url);
const ajv = new Ajv({ allErrors: true, strict: false });
addFormats(ajv);
for (const f of (await readdir(dir)).filter((f) => f.endsWith(".schema.json")))
  ajv.addSchema(JSON.parse(await readFile(new URL(f, dir), "utf8")));
const validate = ajv.getSchema("https://muse.dev/schema/performance.schema.json");

const fixture = JSON.parse(await readFile(new URL("../tools/fixtures/valid.muse.perf.json", import.meta.url), "utf8"));
const clone = () => structuredClone(fixture);

let passed = 0, failed = 0;
const check = (name, cond) => {
  if (cond) { passed++; console.log(`ok   ${name}`); }
  else {
    failed++;
    console.error(`FAIL ${name}`);
    console.error(JSON.stringify(validate.errors, null, 2));
  }
};

// §7 example ⇔ schema conformance (comments stripped, placeholder resolved).
const specExample = {
  muse_perf_version: "0.1.0",
  metadata: {
    source: { schema_id: "muse:work:01J9QR4T8V0W2X6Y8Z0A2C4E6G", rendition_id: "r.synthwave" },
    interpreter: { model: "example", at: "2026-08-22T00:00:00Z" },
  },
  tempo_map: [{ time: 0.0, beat: 0, bpm: 96 }],
  parts: [{ id: "p.lead", name: "Lead", instrument: { name: "violin", program: 40, sample_set: "vsco2-ce" }, mix: { gain: 0.8, pan: 0.0, reverb_send: 0.3 } }],
  notes: [{ part: "p.lead", pitch: 62, pitch_name: "D4", onset: 0.0, duration: 0.3125, onset_beat: 0, duration_beats: 0.5, velocity: 90, articulation: "tenuto", controllers: { pitch_bend: [] } }],
  dynamics: [{ time: 0.0, part: "p.lead", level: 0.6 }],
};
check("spec §7 example validates (conformance pin)", validate(specExample));

// tempo_map ordering: the schema accepts any order; interpolation is the
// player's concern (#24). Pin the current behavior.
check("unsorted tempo_map accepted (interpolation is player-side)", validate({
  ...clone(),
  tempo_map: [{ time: 5, beat: 10, bpm: 100 }, { time: 0, beat: 0, bpm: 96 }],
}));

// controllers: sealed set — unknown names rejected (renderer contract in #24
// intersects these keys; opening the set is a deliberate spec edit, not drift).
check("unknown controller name rejected (sealed set)", !validate({
  ...clone(),
  notes: [{ ...clone().notes[0], controllers: { aftertouch_curve: [] } }],
}));

// Harness perf channel (decision from the spec's open question):
// tools/test.mjs now lints examples/performance/*.muse.perf.json via
// checkPerfRefs, mirroring the danglingRefs channel for .muse.json. Direct
// assertion here (not a subprocess) — spawning the full harness from inside
// a test suite is the wrong granularity.
import { checkPerfRefs } from "../tools/semantics.mjs";
check("harness perf channel: fixture passes checkPerfRefs", checkPerfRefs(fixture).length === 0);

console.log(`${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
