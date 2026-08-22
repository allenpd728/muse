// Tests for schema/muse.schema.json (issue #11; residual coverage per
// tests/open_20260822-021920_root-schema.md, issue #38).
// Standalone runner: `node tests/root-schema.test.mjs`; also folded into npm test.
import { copyFile, mkdtemp, readFile, readdir, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";
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

// --- Residual coverage (issue #38) ---

// Fixture-upgrade regression: every shipped fixture and example stays
// root-conformant as section schemas tighten.
const readJson = async (p) => JSON.parse(await readFile(p, "utf8"));
const fixtureDoc = await readJson(new URL("../tools/fixtures/valid.muse.json", import.meta.url));
check("tools/fixtures/valid.muse.json stays root-conformant", validate(fixtureDoc));
const examplesDir = new URL("../examples/", import.meta.url);
for (const f of (await readdir(examplesDir)).filter((x) => x.endsWith(".muse.json")).sort())
  check(`examples/${f} stays root-conformant`, validate(await readJson(new URL(f, examplesDir))));

// Versioning drift guard: muse_version lives at the root only — if a section
// schema ever declares its own, this fails loudly instead of drifting.
const sectionDeclaresVersion = [];
for (const f of await readdir(dir)) {
  if (f === "muse.schema.json" || !f.endsWith(".schema.json")) continue;
  const s = JSON.parse(await readFile(new URL(f, dir), "utf8"));
  if (s.properties && "muse_version" in s.properties) sectionDeclaresVersion.push(f);
}
check("no section schema declares its own muse_version", sectionDeclaresVersion.length === 0);
check("root requires muse_version", root.required.includes("muse_version"));

// Edge pinned: zero sanctioned renditions is legal (renditions schema has no
// minItems — a work may sanction none).
check("renditions: [] (no sanctioned renditions) valid", validate({ muse_version: "0.1.0", metadata: doc.metadata, globals: doc.globals, renditions: [] }));

// Sibling-registration pin: a missing section schema must surface a readable
// CLI error, not a silent pass. The CLI's permissive catch only guards the
// directory scan; the compile then fails naming the unresolvable ref.
{
  const tmp = await mkdtemp(path.join(tmpdir(), "muse-schema-"));
  try {
    for (const f of await readdir(dir))
      if (f !== "metadata.schema.json") await copyFile(new URL(f, dir), path.join(tmp, f));
    const r = spawnSync(process.execPath, ["tools/validate.mjs", "examples/minimal.muse.json", path.join(tmp, "muse.schema.json")], { encoding: "utf8" });
    check("missing section schema: CLI exits 1", r.status === 1);
    check("missing section schema: readable schema error naming the ref",
      (r.stderr ?? "").includes("schema error") && (r.stderr ?? "").includes("metadata.schema.json"));
  } finally {
    await rm(tmp, { recursive: true, force: true });
  }
}

console.log(`${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
