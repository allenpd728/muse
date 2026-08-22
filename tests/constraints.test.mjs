// Tests for schema/constraints.schema.json (issue #8, spec §2.5).
// Standalone runner: `node tests/constraints.test.mjs`; also folded into npm test.
import { readFile } from "node:fs/promises";
import Ajv from "ajv/dist/2020.js";

const schema = JSON.parse(await readFile(new URL("../schema/constraints.schema.json", import.meta.url), "utf8"));
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

const specSnippet = {
  must_contain: ["motif.a"],
  must_not: [{ kind: "modulation_beyond", semitones: 3 }],
  tempo_lock: { "chorus.1": [92, 104] },
  register: { "theme.1": ["C4", "A5"] },
  structure: { form_deviation: "none" }
};

check("spec §2.5 snippet valid", validate(specSnippet));
check("empty constraints valid (all blocks optional)", validate({}));
check("must_contain empty string rejected", !validate({ must_contain: [""] }));
check("must_contain non-string rejected", !validate({ must_contain: [42] }));
check("must_not predicate missing kind rejected", !validate({ must_not: [{ semitones: 3 }] }));
check("modulation_beyond missing semitones rejected", !validate({ must_not: [{ kind: "modulation_beyond" }] }));
check("modulation_beyond semitones 0 rejected", !validate({ must_not: [{ kind: "modulation_beyond", semitones: 0 }] }));
check("modulation_beyond negative semitones rejected", !validate({ must_not: [{ kind: "modulation_beyond", semitones: -2 }] }));
check("unknown predicate kind preserved (extensibility)", validate({ must_not: [{ kind: "engine_x.rule", threshold: 0.5 }] }));
check("tempo_lock one-element range rejected", !validate({ tempo_lock: { "chorus.1": [92] } }));
check("tempo_lock three-element range rejected", !validate({ tempo_lock: { "chorus.1": [92, 104, 120] } }));
check("tempo_lock zero bpm rejected", !validate({ tempo_lock: { "chorus.1": [0, 104] } }));
check("tempo_lock negative bpm rejected", !validate({ tempo_lock: { "chorus.1": [-5, 104] } }));
check("register one-element pair rejected", !validate({ register: { "theme.1": ["C4"] } }));
check("register three-element pair rejected", !validate({ register: { "theme.1": ["C4", "A5", "C6"] } }));
check("every form_deviation enum value accepted", ["none", "reorder", "abridge"]
  .every((v) => validate({ structure: { form_deviation: v } })));
check("unknown form_deviation rejected", !validate({ structure: { form_deviation: "free" } }));
check("structure unknown member rejected", !validate({ structure: { form_deviation: "none", surprise: true } }));
check("unknown top-level property rejected", !validate({ must_contain: ["motif.a"], coda: {} }));

console.log(`${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);