// Live-Gemini fixture pin (issue #119, per
// tests/open_20260822-215600_live-gemini-fixture.md): the committed
// model-produced performance document must keep validating and scoring 1.0
// against its source schema — schema or metric drift should fail loudly,
// not silently strand the reference shape. No network, no live key.
// Standalone runner; folded into npm test.
import { readFile, readdir } from "node:fs/promises";
import Ajv from "ajv/dist/2020.js";
import addFormats from "ajv-formats";
import { checkPerfRefs } from "../tools/semantics.mjs";
import { scorePerformance } from "../benchmark/metrics.mjs";

const dir = new URL("../schema/", import.meta.url);
const ajv = new Ajv({ allErrors: true, strict: false });
addFormats(ajv);
for (const f of (await readdir(dir)).filter((f) => f.endsWith(".schema.json")))
  ajv.addSchema(JSON.parse(await readFile(new URL(f, dir), "utf8")));
const validate = ajv.getSchema("https://muse.dev/schema/performance.schema.json");

const fixture = JSON.parse(await readFile(new URL("../interpreter/fixtures/live-gemini.muse.perf.json", import.meta.url), "utf8"));
const source = JSON.parse(await readFile(new URL("../examples/full.muse.json", import.meta.url), "utf8"));

let passed = 0, failed = 0;
const check = (name, cond) => {
  if (cond) { passed++; console.log(`ok   ${name}`); }
  else { failed++; console.error(`FAIL ${name}`); }
};

check("fixture validates against performance schema", validate(fixture) || (console.error(validate.errors), false));
check("fixture passes reference integrity", checkPerfRefs(fixture).length === 0);

const report = scorePerformance(source, fixture);
for (const m of ["motif_recall", "structure_fidelity", "tempo_shapes", "harmonic_fidelity"])
  check(`conformance pin: ${m} === 1`, report[m] === 1);

const interp = fixture.metadata?.interpreter ?? {};
check("provenance pin: metadata.interpreter stamped with model + at",
  typeof interp.model === "string" && interp.model.length > 0 && typeof interp.at === "string" && !Number.isNaN(Date.parse(interp.at)));

console.log(`${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
