// Tests for #67's role-vocabulary follow-up (issue #69, spec:
// tests/open_20260822-131000_role-vocabulary.md). Pins the §2.4 spec ↔
// schema parity, the cross-tradition example, and the importer's emitted
// role. Standalone: `node tests/role-vocabulary.test.mjs`; folded into npm test.
import { readFileSync } from "node:fs";
import { synthesize } from "../importer/synthesize.mjs";

let passed = 0, failed = 0;
const check = (name, cond, detail) => {
  if (cond) { passed++; console.log(`ok   ${name}`); }
  else { failed++; console.error(`FAIL ${name}${detail ? ` — ${detail}` : ""}`); }
};

const spec = readFileSync("SCHEMA_SPEC.md", "utf8");
const formSchema = JSON.parse(readFileSync("schema/form.schema.json", "utf8"));
const fullExample = JSON.parse(readFileSync("examples/full.muse.json", "utf8"));

const schemaEnum = new Set(formSchema.properties.sections.items.properties.role.enum);
check("schema role enum present", schemaEnum.size > 0);

// Spec ↔ schema parity: §2.4's backtick-quoted role tokens must set-equal
// the schema enum. The vocabulary list lives between the "role vocabulary"
// paragraph and the "A section's role" follow-up.
const section24 = spec.slice(spec.indexOf("**`role` vocabulary.**"), spec.indexOf("A section's role is semantic intent"));
const specTokens = new Set([...section24.matchAll(/`([a-z_]+)`/g)].map((m) => m[1]).filter((t) => t !== "role"));
check("spec §2.4 role tokens parse", specTokens.size > 0, [...specTokens].join(","));
const onlyInSchema = [...schemaEnum].filter((r) => !specTokens.has(r));
const onlyInSpec = [...specTokens].filter((r) => !schemaEnum.has(r));
check("spec ↔ schema role sets equal", onlyInSchema.length === 0 && onlyInSpec.length === 0,
  `schema-only: ${onlyInSchema.join(",")} spec-only: ${onlyInSpec.join(",")}`);

// Cross-tradition example: full.muse.json keeps at least one role outside
// the song-form group (currently cadenza).
const songForm = ["verse", "pre_chorus", "chorus", "refrain", "bridge", "hook", "intro", "outro", "interlude", "coda", "solo", "custom"];
const roles = (fullExample.form?.sections ?? []).map((s) => s.role);
check("full example uses a non-song-form role", roles.some((r) => !songForm.includes(r)), roles.join(","));

// Importer synthesis emits role "custom", which must be in the enum.
const out = synthesize({
  tempoMap: [{ beat: 0, bpm: 100 }], meterMap: [{ beat: 0, beats: 4, unit: 4 }], keyMap: [],
  parts: [{ id: "t", name: "T", notes: [
    { midi: 60, onsetBeat: 0, durationBeats: 1 }, { midi: 64, onsetBeat: 1, durationBeats: 1 },
    { midi: 60, onsetBeat: 4, durationBeats: 1 }, { midi: 64, onsetBeat: 5, durationBeats: 1 },
  ] }],
}, { source: "role-test" });
const emittedRole = out.form?.sections?.[0]?.role;
check("synthesis emits a role in the schema enum", emittedRole !== undefined && schemaEnum.has(emittedRole), emittedRole);

console.log(`${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
