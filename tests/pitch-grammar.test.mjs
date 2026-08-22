// Tests for the shared pitch grammar (issue #44, residual coverage issue #52):
// schema/material.schema.json $defs/pitch (referenced by material.motifs[].pitches
// and constraints.register bounds) must accept exactly the language that
// importer/ir.mjs pitchToMidi parses. Standalone runner + npm test pickup.
import { readFile } from "node:fs/promises";
import Ajv from "ajv/dist/2020.js";
import { pitchToMidi } from "../importer/ir.mjs";

const ajv = new Ajv({ allErrors: true, strict: false });
const material = JSON.parse(await readFile(new URL("../schema/material.schema.json", import.meta.url), "utf8"));
const validatePitch = ajv.compile(material.$defs.pitch);

// constraints.schema.json references material's $defs/pitch across files —
// pre-register material first (same technique as tests/constraints.test.mjs).
ajv.addSchema(material);
const constraints = JSON.parse(await readFile(new URL("../schema/constraints.schema.json", import.meta.url), "utf8"));
const validateConstraints = ajv.compile(constraints);

let passed = 0, failed = 0;
const check = (name, cond) => {
  if (cond) { passed++; console.log(`ok   ${name}`); }
  else {
    failed++;
    console.error(`FAIL ${name}`);
  }
};

const ACCEPT = [
  "C4", "D4", "E4", "F4", "G4", "A4", "B4", // all seven naturals
  "F#4", "Bb3",                             // sharps and flats
  "C-1",                                    // negative octave (C-1 = MIDI 0, in range)
];
// Grammar pins form, not the MIDI 0-127 range — the schema accepts C10,
// while the importer's pitchToMidi additionally range-checks (a parse-layer
// choice; an out-of-range MIDI note number is meaningless in IR).
const SCHEMA_ONLY = ["C10"];
const REJECT = [
  "c4",      // lowercase letter
  "F##4",    // double accidental
  "F#",      // missing octave
  "4",       // octave only
  "",        // empty
  "H4",      // German H convention is a spec amendment, not silently accepted
];

for (const p of ACCEPT) {
  let importerOk = true;
  try { pitchToMidi(p); } catch { importerOk = false; }
  check(`schema accepts "${p}"`, validatePitch(p));
  check(`importer accepts "${p}" (parity)`, importerOk);
}
for (const p of SCHEMA_ONLY) {
  let importerOk = true;
  try { pitchToMidi(p); } catch { importerOk = false; }
  check(`schema accepts "${p}" (grammar pins form, not MIDI range)`, validatePitch(p));
  check(`importer range-rejects "${p}" (parse-layer range check)`, !importerOk);
}
for (const p of REJECT) {
  let importerOk = true;
  try { pitchToMidi(p); } catch { importerOk = false; }
  check(`schema rejects "${p}"`, !validatePitch(p));
  check(`importer rejects "${p}" (parity)`, !importerOk);
}

// Parity pin beyond the table: the two grammars must agree on whatever either
// side is later tempted to accept.
check("register bound cross-file $ref resolves through constraints.schema.json",
  validateConstraints({ register: { "motif.a": ["C4", "A5"] } })
  && !validateConstraints({ register: { "motif.a": ["banana", "A5"] } }));

console.log(`${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
