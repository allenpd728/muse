// Tests for schema/muse.schema.json (issue #11).
// Standalone runner: `node tests/root-schema.test.mjs`; also folded into npm test.
import { readFile, readdir } from "node:fs/promises";
import Ajv from "ajv/dist/2020.js";
import addFormats from "ajv-formats";

const dir = new URL("../schema/", import.meta.url);
const root = JSON.parse(await readFile(new URL("muse.schema.json", dir), "utf8"));
// ajv must resolve section $refs by their https:// ids — register every sibling.
const ajv = new Ajv({ allErrors: true, strict: false });
addFormats(ajv);
for (const f of await readdir(dir))
  if (f !== "muse.schema.json" && f.endsWith(".schema.json"))
    ajv.addSchema(JSON.parse(await readFile(new URL(f, dir), "utf8")));
const validate = ajv.compile(root);

let passed = 0, failed = 0;
const check = (name, cond) => {
  if (cond) { passed++; console.log(`ok   ${name}`); }
  else {
    failed++;
    console.error(`FAIL ${name}`);
    console.error(JSON.stringify(validate.errors, null, 2));
  }
};

// Composed document: full §2/§2.x snippets spanning every section schema — the
// DoD's "composed document" sense.
const doc = {
  muse_version: "0.1.0",
  metadata: {
    id: "01J00000000000000000000000",
    title: "Composed test doc",
    composer: { name: "harness" },
    created: "2026-08-22T00:00:00Z",
    license: { renditions: "presets-only", attribution: "required", commercial: true },
    provenance: []
  },
  globals: {
    tempo: { bpm: 96, range: [84, 112], feel: "straight" },
    meter: { beats: 4, unit: 4 },
    key: { tonic: "D", mode: "dorian" },
    duration_bars: 64
  },
  material: {
    motifs: [{ id: "motif.a", kind: "pitch_rhythm", pitches: ["D4", "F4"], durations: [0.5, 0.5], contour: "up-up", tags: ["primary"] }],
    themes: [{ id: "theme.1", phrases: [{ motifs: ["motif.a"] }], cadence: "half" }],
    rhythms: [{ id: "groove.1", pattern: [1, 0, 0.75], grid: "8n" }],
    harmony: { progressions: [{ id: "prog.verse", chords: ["Dm7"], bars_per_chord: 1 }], vocabulary: "diatonic-plus-bVII" }
  },
  form: {
    sections: [{ id: "verse.1", role: "verse", bars: 16, uses: [{ ref: "theme.1", variation: "plain" }], harmony: "prog.verse", energy: 0.4 }],
    order: ["verse.1"],
    repetition: { "verse.1": { min: 2, max: 4 } }
  },
  constraints: {
    must_contain: ["motif.a"],
    must_not: [{ kind: "modulation_beyond", semitones: 3 }],
    tempo_lock: { "verse.1": [92, 104] },
    register: { "theme.1": ["C4", "A5"] },
    structure: { form_deviation: "none" }
  },
  renditions: [{ id: "cover.breakbeat", name: "Breakbeat cover", style: { genre: "breakbeat", era: "1995", references: ["jungle", "lo-fi"] }, params: { density: 0.8 } }],
  extensions: { "engine.audiocraft": { cfg: 3.5 } }
};

check("composed document valid through root $refs", validate(doc));
check("missing muse_version rejected", !validate({ ...doc, muse_version: undefined }));
check("missing metadata rejected", !validate({ muse_version: "0.1.0", globals: doc.globals }));
check("missing globals rejected", !validate({ muse_version: "0.1.0", metadata: doc.metadata }));
check("optional members undeclared valid", validate({ muse_version: "0.1.0", metadata: doc.metadata, globals: doc.globals }));
check("non-semver muse_version rejected", !validate({ muse_version: "0.1", metadata: doc.metadata, globals: doc.globals }));
check("unknown top-level member rejected", !validate({ muse_version: "0.1.0", metadata: doc.metadata, globals: doc.globals, blobs: [] }));
check("section error surfaces through root (form.energy 2)", !validate({ muse_version: "0.1.0", metadata: doc.metadata, globals: doc.globals, form: { sections: [{ id: "s", role: "verse", energy: 2 }], order: ["s"] } }));

console.log(`${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
