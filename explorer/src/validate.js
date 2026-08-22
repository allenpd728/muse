// Validation panel logic: same schemas and lint code as the repo tooling.
// Schemas are bundled statically via Vite JSON imports; $ids are https://
// URLs, so siblings are pre-registered before the root compiles (same trick
// as tools/validate.mjs).
import Ajv from "ajv/dist/2020.js";
import addFormats from "ajv-formats";
import { checkSemantics } from "@muse-tools/semantics.mjs";
import { danglingRefs } from "@muse-tools/refs.mjs";

import rootSchema from "../../schema/muse.schema.json";
import metadataSchema from "../../schema/metadata.schema.json";
import globalsSchema from "../../schema/globals.schema.json";
import materialSchema from "../../schema/material.schema.json";
import formSchema from "../../schema/form.schema.json";
import constraintsSchema from "../../schema/constraints.schema.json";
import renditionsSchema from "../../schema/renditions.schema.json";
import extensionsSchema from "../../schema/extensions.schema.json";

const SECTIONS = [
  metadataSchema, globalsSchema, materialSchema, formSchema,
  constraintsSchema, renditionsSchema, extensionsSchema,
];

let compiled;
const validator = () => {
  if (!compiled) {
    const ajv = new Ajv({ allErrors: true, strict: false });
    addFormats(ajv);
    for (const s of SECTIONS) if (s.$id && !ajv.getSchema(s.$id)) ajv.addSchema(s);
    compiled = ajv.compile(rootSchema);
  }
  return compiled;
};

// Returns [{ channel, message }] — channel is schema | refs | semantics,
// matching the harness's rejection-channel convention.
export function validateDocument(doc) {
  const out = [];
  const validate = validator();
  if (!validate(doc))
    for (const e of validate.errors ?? [])
      out.push({ channel: "schema", message: `${e.instancePath || "(root)"} ${e.message}` });
  for (const d of danglingRefs(doc))
    out.push({ channel: "refs", message: `${d.path}: unresolved ref "${d.ref}"` });
  for (const s of checkSemantics(doc))
    out.push({ channel: "semantics", message: s });
  return out;
}
