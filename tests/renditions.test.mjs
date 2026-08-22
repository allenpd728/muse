// Tests for schema/renditions.schema.json (issue #9, spec §2.6).
// Standalone runner: `node tests/renditions.test.mjs`; also folded into npm test.
import { readFile } from "node:fs/promises";
import Ajv from "ajv/dist/2020.js";

const schema = JSON.parse(await readFile(new URL("../schema/renditions.schema.json", import.meta.url), "utf8"));
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

const specSnippet = [
  {
    id: "r.synthwave",
    name: "Midnight Drive",
    style: { genre: "synthwave", era: "1984", references: ["arpeggiated bass", "gated reverb drums"] },
    params: { tempo_bpm: 100, instrumentation: ["analog synth", "drum machine"], density: 0.7, swing: 0.0 },
    author: { name: "someone" },
  },
  {
    id: "r.quartet",
    name: "Late Set",
    style: { genre: "jazz quartet", era: "1959" },
    params: { tempo_bpm: 88, instrumentation: ["piano", "upright bass", "brushes", "tenor sax"], swing: 0.62 },
  },
];

check("both spec §2.6 example renditions validate", validate(specSnippet));
check("bare rendition (id + name only) valid", validate([{ id: "r.x", name: "X" }]));
check("empty array valid", validate([]));
check("missing id rejected", !validate([{ name: "X" }]));
check("missing name rejected", !validate([{ id: "r.x" }]));
check("empty-string id rejected", !validate([{ id: "", name: "X" }]));
check("density outside 0..1 rejected", !validate([{ id: "r.x", name: "X", params: { density: 1.5 } }]));
check("negative tempo_bpm rejected", !validate([{ id: "r.x", name: "X", params: { tempo_bpm: -10 } }]));
check("unknown rendition member rejected", !validate([{ id: "r.x", name: "X", reference_track: "song.wav" }]));
check("unknown style member rejected", !validate([{ id: "r.x", name: "X", style: { artist: "someone famous" } }]));
check("author without name rejected", !validate([{ id: "r.x", name: "X", author: { id: "u.1" } }]));

console.log(`${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
