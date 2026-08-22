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

// Residual coverage (issue #34, spec tests/open → closed_…_renditions-schema.md)
check("swing 0 and 1 accepted", validate([{ id: "r.x", name: "X", params: { swing: 0 } }])
  && validate([{ id: "r.x", name: "X", params: { swing: 1 } }]));
check("swing outside 0..1 rejected", !validate([{ id: "r.x", name: "X", params: { swing: 1.5 } }])
  && !validate([{ id: "r.x", name: "X", params: { swing: -0.1 } }]));
check("style as string rejected (must be object)", !validate([{ id: "r.x", name: "X", style: "synthwave" }]));
check("params as string rejected (must be object)", !validate([{ id: "r.x", name: "X", params: "loud" }]));
check("references entry non-string rejected", !validate([{ id: "r.x", name: "X", style: { references: [1984] } }]));
check("references entry empty string rejected", !validate([{ id: "r.x", name: "X", style: { references: [""] } }]));
check("instrumentation entry non-string rejected", !validate([{ id: "r.x", name: "X", params: { instrumentation: [7] } }]));
check("instrumentation entry empty string rejected", !validate([{ id: "r.x", name: "X", params: { instrumentation: [""] } }]));
check("unwrapped rendition object rejected (root is array)", !validate({ id: "r.x", name: "X" }));
check("string item rejected", !validate(["not a rendition"]));
check("null item rejected", !validate([null]));
check("numeric era rejected (era is a string; change is a spec question)", !validate([{ id: "r.x", name: "X", style: { era: 1984 } }]));
// §2.6 hard rule is semantic: the schema deliberately does not pattern-match
// artist references — semantics.mjs owns that lint.
check("artist-phrased reference passes schema (semantic lint's job)", validate([{ id: "r.x", name: "X", style: { references: ["in the style of someone famous"] } }]));

console.log(`${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
