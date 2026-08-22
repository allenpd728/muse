// Integration tests for schema/globals.schema.json (issue #30): validation
// through the root schema $ref, the tools/semantics.mjs lint, and the pinned
// edge cases from the open spec.
import { readFile } from "node:fs/promises";
import Ajv from "ajv/dist/2020.js";
import addFormats from "ajv-formats";
import { checkSemantics } from "../tools/semantics.mjs";

const ROOT = new URL("../schema/muse.schema.json", import.meta.url);
const readJson = async (u) => JSON.parse(await readFile(u, "utf8"));

// Same sibling-pre-registration technique as tools/validate.mjs.
const ajv = new Ajv({ allErrors: true, strict: false });
addFormats(ajv);
const sectionNames = await import("node:fs/promises").then((fs) =>
  fs.readdir(new URL("../schema/", import.meta.url)),
);
for (const f of sectionNames) {
  if (f.endsWith(".schema.json") && f !== "muse.schema.json") {
    const s = await readJson(new URL("../schema/" + f, import.meta.url));
    if (s.$id && !ajv.getSchema(s.$id)) ajv.addSchema(s);
  }
}
const validateRoot = ajv.compile(await readJson(ROOT));

const meta = {
  id: "01J5X8K2M4N6P8Q0R2T4V6X8Z0",
  title: "globals integration",
  composer: { name: "t" },
  created: "2026-08-22T00:00:00Z",
  license: { renditions: "closed" },
  provenance: [],
};
// muse_version must be full semver under the root schema (spec §2 shows "0.1"
// — the strictness mismatch is for the #37 integration review, so this test
// uses valid semver and pins the strict behavior as-is).
const doc = (globals) => ({ muse_version: "0.1.0", metadata: structuredClone(meta), globals });

let passed = 0, failed = 0;
const check = (name, cond) => {
  if (cond) { passed++; console.log(`ok   ${name}`); }
  else { failed++; console.error(`FAIL ${name}`, JSON.stringify(validateRoot.errors, null, 2)); }
};

// Root-schema $ref integration — globals validated through muse.schema.json.
check("globals valid through root $ref", validateRoot(doc({
  tempo: { bpm: 96, range: [84, 112], feel: "straight" },
  meter: { beats: 4, unit: 4 },
  key: { tonic: "D", mode: "dorian" },
  duration_bars: 64,
})));
check("globals schema violation fails through root $ref", !validateRoot(doc({ tempo: { feel: "x" } })));

// Semantic lint lives in tools/semantics.mjs (one home for code-only rules).
check("inverted tempo.range caught by semantics lint", checkSemantics(doc({ tempo: { bpm: 1, range: [112, 84] } })).length === 1);
check("ordered range passes semantics lint", checkSemantics(doc({ tempo: { bpm: 1, range: [84, 112] } })).length === 0);

// Pinned edge cases (intent documented in the closed spec).
check("equal range bounds (fixed tempo) accepted", validateRoot(doc({ tempo: { bpm: 96, range: [96, 96] } })));
check("1-element meter.beats array rejected (additive needs 2+)", !validateRoot(doc({ meter: { beats: [4], unit: 4 } })));
check("non-power-of-2 meter.unit accepted", validateRoot(doc({ meter: { beats: 4, unit: 3 } })));

console.log(`${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
