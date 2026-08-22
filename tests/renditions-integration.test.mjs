// Integration test for schema/renditions.schema.json (issue #34): a document
// whose `renditions` violates the section schema must fail through the root
// schema's $ref wiring — proves composition, not just the standalone file.
import { readFile, readdir } from "node:fs/promises";
import Ajv from "ajv/dist/2020.js";
import addFormats from "ajv-formats";

const readJson = async (u) => JSON.parse(await readFile(u, "utf8"));

// Same sibling-pre-registration technique as tools/validate.mjs.
const ajv = new Ajv({ allErrors: true, strict: false });
addFormats(ajv);
for (const f of await readdir(new URL("../schema/", import.meta.url))) {
  if (f.endsWith(".schema.json") && f !== "muse.schema.json") {
    const s = await readJson(new URL("../schema/" + f, import.meta.url));
    if (s.$id && !ajv.getSchema(s.$id)) ajv.addSchema(s);
  }
}
const validateRoot = ajv.compile(await readJson(new URL("../schema/muse.schema.json", import.meta.url)));

const base = {
  muse_version: "0.1.0",
  metadata: {
    id: "01J5X8K2M4N6P8Q0R2T4V6X8Z0",
    title: "renditions integration",
    composer: { name: "t" },
    created: "2026-08-22T00:00:00Z",
    license: { renditions: "closed" },
    provenance: [],
  },
  globals: { tempo: { bpm: 96 } },
};

let passed = 0, failed = 0;
const check = (name, cond) => {
  if (cond) { passed++; console.log(`ok   ${name}`); }
  else {
    failed++;
    console.error(`FAIL ${name}`);
    console.error(JSON.stringify(validateRoot.errors, null, 2));
  }
};

const good = { ...base, renditions: [{ id: "r.x", name: "X", params: { swing: 0.5 } }] };
const bad = { ...base, renditions: [{ id: "r.x", name: "X", params: { swing: 1.5 } }] };

check("valid renditions pass through root schema", validateRoot(good));
check("invalid renditions rejected through root schema ($ref wiring)", !validateRoot(bad));

console.log(`${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
