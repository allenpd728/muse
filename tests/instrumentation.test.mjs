// Tests for schema v0.3 structured instrumentation (issue #85, per
// tests/open_20260822-142000_instrumentation-v03.md).
// Standalone runner: `node tests/instrumentation.test.mjs`; also folded into npm test.
import { readFile, readdir } from "node:fs/promises";
import Ajv from "ajv/dist/2020.js";
import addFormats from "ajv-formats";

const dir = new URL("../schema/", import.meta.url);
const schemas = {};
const ajv = new Ajv({ allErrors: true, strict: false });
addFormats(ajv);
for (const f of (await readdir(dir)).filter((f) => f.endsWith(".schema.json"))) {
  schemas[f] = JSON.parse(await readFile(new URL(f, dir), "utf8"));
  ajv.addSchema(schemas[f]);
}
const validate = ajv.getSchema("https://muse.dev/schema/renditions.schema.json");

const full = JSON.parse(await readFile(new URL("../examples/full.muse.json", import.meta.url), "utf8"));
const spec = await readFile(new URL("../SCHEMA_SPEC.md", import.meta.url), "utf8");

let passed = 0, failed = 0;
const check = (name, cond) => {
  if (cond) { passed++; console.log(`ok   ${name}`); }
  else {
    failed++;
    console.error(`FAIL ${name}`);
    console.error(JSON.stringify(validate.errors, null, 2));
  }
};

const rendition = (instrumentation) => [{ id: "r.x", name: "X", params: { instrumentation } }];

// Acceptance: structured and free-text entries.
check("structured entry validates", validate(rendition([{ name: "Violin I", program: 48 }])));
check("free-text entries still validate (anyOf keeps strings legal)",
  validate(rendition(["analog synth", "drum machine"])));
check("mixed free-text + structured validates",
  validate(rendition(["drum machine", { name: "Violin I", techniques: { divisi: "allowed" } }])));
check("full techniques surface validates", validate(rendition([{
  name: "Flute", program: 73,
  doubles: [{ name: "Piccolo", program: 72 }],
  techniques: { divisi: "required", mute: ["harmon"], bowing: ["arco"], breath: ["flutter_tongue"], production: ["gated"] },
}])));

// Rejection paths.
check("structured entry missing name rejected", !validate(rendition([{ program: 48 }])));
check("program outside 0-127 rejected", !validate(rendition([{ name: "X", program: 128 }])));
check("divisi outside enum rejected", !validate(rendition([{ name: "X", techniques: { divisi: "mandatory" } }])));
check("unknown property on structured entry rejected (sealed)",
  !validate(rendition([{ name: "X", vendor: "acme" }])));
check("unknown technique key rejected", !validate(rendition([{ name: "X", techniques: { strumming: ["down"] } }])));
check("unknown technique name within a known key ACCEPTED (additive vocabulary, ignore-and-record)",
  validate(rendition([{ name: "X", techniques: { bowing: ["jet_whistle"] } }])));
check("double missing name rejected", !validate(rendition([{ name: "X", doubles: [{ program: 72 }] }])));

// Spec ↔ schema parity: §2.6 technique keys match the schema's techniques
// properties (same inspection pattern as the role-vocabulary parity pin).
{
  const schemaKeys = Object.keys(
    schemas["renditions.schema.json"].items.properties.params.properties.instrumentation.items
      .anyOf[1].properties.techniques.properties
  ).sort();
  // The §2.6 vocabulary paragraph bolds the key names (divisi is written
  // **\`divisi\`** with nested backticks): divisi, mutes, bowing,
  // breath/attack, production — normalize to schema keys.
  const specKeys = [...spec.matchAll(/\*\*`?(divisi|mutes|bowing|breath\/attack|production)`?\*\*/g)]
    .map((m) => m[1])
    .map((k) => (k === "mutes" ? "mute" : k === "breath/attack" ? "breath" : k))
    .sort();
  check("spec §2.6 technique keys match schema techniques properties",
    JSON.stringify([...new Set(specKeys)]) === JSON.stringify(schemaKeys));
}

// Full-example guards: r.chamber keeps exercising the v0.3 surface.
{
  const chamber = full.renditions.find((r) => r.id === "r.chamber");
  const structured = (chamber?.params?.instrumentation ?? []).filter((e) => typeof e === "object");
  check("r.chamber present with structured entries", structured.length >= 1);
  check("r.chamber exercises divisi",
    structured.some((e) => e.techniques?.divisi !== undefined));
  check("r.chamber exercises mute or bowing",
    structured.some((e) => (e.techniques?.mute ?? []).length > 0 || (e.techniques?.bowing ?? []).length > 0));
  check("r.synthwave and r.quartet stay free-text",
    ["r.synthwave", "r.quartet"].every((id) =>
      (full.renditions.find((r) => r.id === id)?.params?.instrumentation ?? []).every((e) => typeof e === "string")));
}

console.log(`${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
