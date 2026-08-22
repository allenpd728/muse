// Tests for examples/minimal.muse.json (issue #39, per
// tests/open_20260822-021329_minimal-example.md).
// Standalone runner: `node tests/minimal.test.mjs`; also folded into npm test.
import { readFile, readdir } from "node:fs/promises";
import Ajv from "ajv/dist/2020.js";
import addFormats from "ajv-formats";

const dir = new URL("../schema/", import.meta.url);
const ajv = new Ajv({ allErrors: true, strict: false });
addFormats(ajv);
for (const f of (await readdir(dir)).filter((f) => f.endsWith(".schema.json")))
  ajv.addSchema(JSON.parse(await readFile(new URL(f, dir), "utf8")));
const validate = ajv.getSchema("https://muse.dev/schema/muse.schema.json");

const minimal = JSON.parse(await readFile(new URL("../examples/minimal.muse.json", import.meta.url), "utf8"));

let passed = 0, failed = 0;
const check = (name, cond) => {
  if (cond) { passed++; console.log(`ok   ${name}`); }
  else {
    failed++;
    console.error(`FAIL ${name}`);
    console.error(JSON.stringify(validate.errors, null, 2));
  }
};

check("minimal example validates against root", validate(minimal));

// Required-field mutation: removing any root-required field fails validation.
for (const field of ["muse_version", "metadata", "globals"]) {
  const mutated = { ...minimal, [field]: undefined };
  check(`removing ${field} fails validation`, !validate(JSON.parse(JSON.stringify(mutated))));
}

// Project provenance rule: the minimal example carries an AI disclosure.
check("provenance present with an ai: true entry",
  Array.isArray(minimal.metadata.provenance) &&
  minimal.metadata.provenance.length > 0 &&
  minimal.metadata.provenance.some((e) => e.ai === true));

// Minimality guard: only the required top-level sections — content sections
// belong in examples/full.muse.json. Accretion requires editing this test.
check("top-level keys are exactly muse_version/metadata/globals",
  JSON.stringify(Object.keys(minimal).sort()) ===
  JSON.stringify(["globals", "metadata", "muse_version"]));
// Sparse globals is the example's intent (schema allows key/tempo.range —
// adding them changes intent, so pin the sparse set).
check("globals stays sparse (tempo, meter, duration_bars only)",
  JSON.stringify(Object.keys(minimal.globals).sort()) ===
  JSON.stringify(["duration_bars", "meter", "tempo"]));

console.log(`${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
