// Tests for schema/metadata.schema.json (issue #28, spec §2.1).
// Standalone runner: `node tests/metadata.test.mjs`; also folded into npm test.
import { readFile } from "node:fs/promises";
import Ajv from "ajv/dist/2020.js";
import addFormats from "ajv-formats";

const schema = JSON.parse(await readFile(new URL("../schema/metadata.schema.json", import.meta.url), "utf8"));
const ajv = new Ajv({ allErrors: true, strict: false });
addFormats(ajv); // schema uses format: date-time
const validate = ajv.compile(schema);
// Form schema loaded for the §2.8 convention-not-enforcement pin (issue #51).
// form.schema.json refs material's materialRef — pre-register the sibling first.
ajv.addSchema(JSON.parse(await readFile(new URL("../schema/material.schema.json", import.meta.url), "utf8")));
const formSchema = JSON.parse(await readFile(new URL("../schema/form.schema.json", import.meta.url), "utf8"));
const validateForm = ajv.compile(formSchema);

let passed = 0, failed = 0;
const check = (name, cond) => {
  if (cond) { passed++; console.log(`ok   ${name}`); }
  else {
    failed++;
    console.error(`FAIL ${name}`);
    console.error(JSON.stringify(validate.errors, null, 2));
  }
};

const base = {
  id: "01J5X8K2M4N6P8Q0R2T4V6X8Z0",
  title: "Test work",
  composer: { name: "Composer" },
  created: "2026-08-21T00:00:00Z",
  license: { renditions: "presets-only", attribution: "required", commercial: true },
  provenance: [],
};
const patched = (patch) => {
  const doc = structuredClone(base);
  for (const [k, v] of Object.entries(patch)) doc[k] = v;
  return doc;
};

// Happy paths
check("base document valid", validate(structuredClone(base)));
check("ULID id (26-char Crockford base32) valid", validate(structuredClone(base)));
check("UUID id valid", validate(patched({ id: "3f6b2a10-7c4d-4e5f-9a8b-0c1d2e3f4a5b" })));
check("optional fields absent: composer.id, attribution, commercial, provenance detail", validate(patched({
  composer: { name: "C" },
  license: { renditions: "closed" },
})));
check("full provenance entry valid", validate(patched({
  provenance: [{ event: "generated", actor: "openhands", at: "2026-08-22T00:00:00Z", ai: true, notes: "x" }],
})));

// Enum + required fields
check("license.renditions outside enum rejected", !validate(patched({ license: { renditions: "remix-free" } })));
for (const field of ["id", "title", "composer", "created", "license", "provenance"]) {
  const doc = structuredClone(base);
  delete doc[field];
  check(`missing required field '${field}' rejected`, !validate(doc));
}
check("license missing renditions rejected", !validate(patched({ license: {} })));

// id grammar
check("25-char id rejected (ULID boundary)", !validate(patched({ id: base.id.slice(0, 25) })));
check("27-char id rejected", !validate(patched({ id: base.id + "0" })));
for (const ch of ["I", "L", "O", "U"]) {
  check(`ULID with excluded char '${ch}' rejected`, !validate(patched({ id: ch + base.id.slice(1) })));
}

// Prefixed form (issue #43 / spec §2.1+§2.8; residual coverage issue #51)
check("muse:work: + ULID valid (spec §2.1 example form)", validate(patched({ id: `muse:work:${base.id}` })));
check("muse:work: + UUID valid (prefix composes with both id kinds)", validate(patched({ id: "muse:work:3f6b2a10-7c4d-4e5f-9a8b-0c1d2e3f4a5b" })));
check("wrong namespace prefix rejected", !validate(patched({ id: `muse:track:${base.id}` })));
check("prefixed ULID wrong length rejected", !validate(patched({ id: `muse:work:${base.id.slice(0, 25)}` }))
  && !validate(patched({ id: `muse:work:${base.id}0` })));
check("prefixed lowercase ULID rejected", !validate(patched({ id: `muse:work:${base.id.toLowerCase()}` })));
check("prefixed malformed UUID rejected", !validate(patched({ id: "muse:work:3f6b2a10-7c4d-4e5f-9a8b" })));
check("double prefix rejected", !validate(patched({ id: `muse:work:muse:work:${base.id}` })));

// Formats and lengths
check("created not RFC 3339 rejected", !validate(patched({ created: "2026-08-21" })));
check("empty title rejected", !validate(patched({ title: "" })));
check("empty composer.name rejected", !validate(patched({ composer: { name: "" } })));

// Strictness
check("unknown top-level property rejected", !validate(patched({ extra: true })));
check("unknown license property rejected", !validate(patched({ license: { renditions: "closed", extra: true } })));
check("provenance item missing event rejected", !validate(patched({ provenance: [{ actor: "x" }] })));

// §2.8 convention-not-enforcement pin (issue #51): internal ids are dotted
// slugs by convention only — the schemas deliberately do not enforce it.
check("non-slug section id validates (§2.8 convention, not enforcement)",
  validateForm({ sections: [{ id: "verse one!", role: "verse" }], order: ["verse one!"] }));

console.log(`${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
