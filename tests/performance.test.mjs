// Tests for schema/performance.schema.json + checkPerfRefs (issue #22, per
// docs/scope-batch3.md and spec §7).
// Standalone runner: `node tests/performance.test.mjs`; also folded into npm test.
import { readFile, readdir } from "node:fs/promises";
import { spawnSync } from "node:child_process";
import Ajv from "ajv/dist/2020.js";
import addFormats from "ajv-formats";
import { checkPerfRefs } from "../tools/semantics.mjs";

const dir = new URL("../schema/", import.meta.url);
const ajv = new Ajv({ allErrors: true, strict: false });
addFormats(ajv);
for (const f of (await readdir(dir)).filter((f) => f.endsWith(".schema.json")))
  ajv.addSchema(JSON.parse(await readFile(new URL(f, dir), "utf8")));
const validate = ajv.getSchema("https://muse.dev/schema/performance.schema.json");

const fixture = JSON.parse(await readFile(new URL("../tools/fixtures/valid.muse.perf.json", import.meta.url), "utf8"));
const clone = () => JSON.parse(JSON.stringify(fixture));

let passed = 0, failed = 0;
const check = (name, cond) => {
  if (cond) { passed++; console.log(`ok   ${name}`); }
  else {
    failed++;
    console.error(`FAIL ${name}`);
    console.error(JSON.stringify(validate.errors, null, 2));
  }
};

// DoD: hand-built performance doc validates — through ajv directly and
// through the real CLI contract.
check("hand-built fixture validates", validate(clone()));
check("checkPerfRefs clean on fixture", checkPerfRefs(clone()).length === 0);
{
  const r = spawnSync(process.execPath, ["tools/validate.mjs", "tools/fixtures/valid.muse.perf.json", "schema/performance.schema.json"], { encoding: "utf8" });
  check("CLI validates fixture (exit 0)", r.status === 0);
}

// DoD rejection: out-of-range velocity.
check("velocity 128 rejected", !validate((() => { const d = clone(); d.notes[0].velocity = 128; return d; })()));
check("velocity -1 rejected", !validate((() => { const d = clone(); d.notes[0].velocity = -1; return d; })()));
check("non-integer velocity rejected", !validate((() => { const d = clone(); d.notes[0].velocity = 90.5; return d; })()));

// DoD rejection: dangling part refs (code check, both surfaces).
check("dangling notes[].part flagged", checkPerfRefs((() => { const d = clone(); d.notes[0].part = "p.ghost"; return d; })()).some((e) => e.includes("p.ghost")));
check("dangling dynamics[].part flagged", checkPerfRefs((() => { const d = clone(); d.dynamics[1].part = "p.ghost"; return d; })()).some((e) => e.includes("p.ghost")));
check("dynamics without part (global) not flagged", checkPerfRefs((() => { const d = clone(); delete d.dynamics[1].part; return d; })()).length === 0);

// Shape invariants.
check("missing muse_perf_version rejected", !validate((() => { const d = clone(); delete d.muse_perf_version; return d; })()));
check("non-semver muse_perf_version rejected", !validate((() => { const d = clone(); d.muse_perf_version = "0.1"; return d; })()));
check("missing metadata.interpreter rejected", !validate((() => { const d = clone(); delete d.metadata.interpreter; return d; })()));
check("empty tempo_map rejected", !validate((() => { const d = clone(); d.tempo_map = []; return d; })()));
check("empty parts rejected", !validate((() => { const d = clone(); d.parts = []; return d; })()));
check("negative onset rejected", !validate((() => { const d = clone(); d.notes[0].onset = -0.1; return d; })()));
check("zero duration rejected", !validate((() => { const d = clone(); d.notes[0].duration = 0; return d; })()));
check("pitch 128 rejected", !validate((() => { const d = clone(); d.notes[0].pitch = 128; return d; })()));
check("pitch_name grammar shared with schema pitch def (banana rejected)",
  !validate((() => { const d = clone(); d.notes[0].pitch_name = "banana"; return d; })()));
check("unknown articulation rejected", !validate((() => { const d = clone(); d.notes[0].articulation = "sforzando"; return d; })()));
check("mix gain > 1 rejected", !validate((() => { const d = clone(); d.parts[0].mix.gain = 1.5; return d; })()));
check("dynamics level > 1 rejected", !validate((() => { const d = clone(); d.dynamics[0].level = 1.2; return d; })()));
check("unknown top-level member rejected", !validate((() => { const d = clone(); d.bogus = 1; return d; })()));
check("optional controllers validate", validate((() => { const d = clone(); d.notes[0].controllers = { pressure: [0.5, 0.7] }; return d; })()));
check("empty notes array valid (rest-only performance)", validate((() => { const d = clone(); d.notes = []; return d; })()));

console.log(`${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
