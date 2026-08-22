#!/usr/bin/env node
// Validate a .muse.json document against a JSON Schema.
// Usage: node tools/validate.mjs <document> [schema]
// Exit 0 if valid, 1 if invalid or on error.
import { readFile } from "node:fs/promises";
import path from "node:path";
import Ajv from "ajv/dist/2020.js";
import addFormats from "ajv-formats";

const [docPath, schemaPath = "schema/muse.schema.json"] = process.argv.slice(2);
if (!docPath) {
  console.error("usage: node tools/validate.mjs <document> [schema]");
  process.exit(1);
}

const readJson = async (p) => JSON.parse(await readFile(p, "utf8"));

let doc, schema;
try {
  doc = await readJson(docPath);
  schema = await readJson(schemaPath);
} catch (e) {
  console.error(`error: ${e.message}`);
  process.exit(1);
}

const ajv = new Ajv({ allErrors: true, strict: false });
addFormats(ajv);

let validate;
try {
  validate = ajv.compile(schema);
} catch (e) {
  console.error(`schema error: ${e.message}`);
  process.exit(1);
}

if (validate(doc)) {
  console.log(`valid: ${path.basename(docPath)}`);
  process.exit(0);
}
console.error(`invalid: ${path.basename(docPath)}`);
for (const err of validate.errors ?? []) {
  console.error(`  ${err.instancePath || "/"} ${err.message}`);
}
process.exit(1);
