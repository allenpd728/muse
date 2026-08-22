// Tests for schema/globals.schema.json (issue #5, spec §2.2).
// Standalone runner: `node tests/globals.test.mjs`; also folded into npm test.
import { readFile } from "node:fs/promises";
import Ajv from "ajv/dist/2020.js";

const schema = JSON.parse(await readFile(new URL("../schema/globals.schema.json", import.meta.url), "utf8"));
const ajv = new Ajv({ allErrors: true, strict: false });
const validate = ajv.compile(schema);

let passed = 0, failed = 0;
const check = (name, cond) => {
  if (cond) { passed++; console.log(`ok   ${name}`); }
  else {
    failed++;
    console.error(`FAIL ${name}`);
    console.error(JSON.stringify(validate.errors, null, 2));
  }
};

// Range ordering is a semantics JSON Schema cannot express (no cross-value
// numeric comparison in draft 2020-12) — checked in code, same class as the
// harness's cross-ref lint.
const orderedRanges = (doc) =>
  !doc?.tempo?.range || doc.tempo.range[0] <= doc.tempo.range[1];

const specSnippet = {
  tempo: { bpm: 96, range: [84, 112], feel: "straight" },
  meter: { beats: 4, unit: 4 },
  key: { tonic: "D", mode: "dorian" },
  duration_bars: 64,
};

check("spec §2.2 snippet valid", validate(specSnippet) && orderedRanges(specSnippet));
check("simple meter {beats:4,unit:4} valid", validate({ meter: { beats: 4, unit: 4 } }));
check("additive meter {beats:[3,3,2],unit:8} valid", validate({ meter: { beats: [3, 3, 2], unit: 8 } }));
check("meter with zero beats rejected", !validate({ meter: { beats: 0, unit: 4 } }));
check("key tonic+mode valid", validate({ key: { tonic: "D", mode: "dorian" } }));
check("key 'atonal' without mode valid", validate({ key: { tonic: "atonal" } }));
check("key named tonic without mode rejected", !validate({ key: { tonic: "D" } }));
check("tempo without bpm rejected", !validate({ tempo: { feel: "straight" } }));
check("unknown member rejected", !validate({ tuning: { cents: 0 } }));
const invDoc = { tempo: { bpm: 96, range: [112, 84] } };
check(
  "inverted tempo range rejected semantically",
  validate(invDoc) === true && orderedRanges(invDoc) === false
);

console.log(`${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
