// Tests for schema/extensions.schema.json (issue #35, per
// tests/open_20260822-003000_extensions-schema.md).
// Standalone runner: `node tests/extensions.test.mjs`; also folded into npm test.
import { readFile } from "node:fs/promises";
import Ajv from "ajv/dist/2020.js";

const schema = JSON.parse(await readFile(new URL("../schema/extensions.schema.json", import.meta.url), "utf8"));
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

check("spec §2.7 example validates", validate({ "engine.audiocraft": { cfg: 3.5 } }));
check("empty object validates", validate({}));
check("multiple namespaces validate", validate({
  "engine.audiocraft": { cfg: 3.5 },
  "composer.my_tool": { seed: 42 },
  "importer": { inferred: [] },
}));
check("arbitrary content types validate", validate({
  "engine.a": { nested: { deep: [1, { x: true }] } },
  "engine.b": [1, 2, 3],
  "engine.c": "free text",
  "engine.d": 42,
  "engine.e": null,
}));
check("namespace with dots/underscores/hyphens validates", validate({
  "engine.audiocraft_v2": {},
  "composer.my-tool.v3": {},
}));
check("uppercase namespace key rejected", !validate({ "Engine.Audiocraft": {} }));
check("namespace starting with separator rejected", !validate({ ".engine": {} }));
check("namespace with space rejected", !validate({ "engine audiocraft": {} }));
check("empty namespace key rejected", !validate({ "": {} }));
check("non-object root (array) rejected", !validate([1, 2]));
check("non-object root (string) rejected", !validate("engine.audiocraft"));

console.log(`${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
