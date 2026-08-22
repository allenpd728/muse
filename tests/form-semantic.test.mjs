// Residual + semantic checks for schema/form.schema.json (issue #32, spec §2.4).
// The DoD schema cases live in tests/form.test.mjs; this suite covers the
// semantic invariants that JSON Schema cannot express (same class as the
// harness cross-ref lint) plus root-schema $ref integration.
// Standalone runner: `node tests/form-semantic.test.mjs`; folded into npm test.


let passed = 0, failed = 0;
const ok = (name, cond) => {
  if (cond) { passed++; console.log(`ok   ${name}`); }
  else { failed++; console.error(`FAIL ${name}`); }
};

// --- Semantic invariants (code, not ajv) ---
function formErrors(form) {
  const errs = [];
  const sections = form?.sections ?? [];
  const ids = sections.map((s) => s?.id);
  const idSet = new Set(ids);
  if (idSet.size !== ids.length) errs.push("duplicate section ids");
  for (const oid of form?.order ?? []) if (!idSet.has(oid)) errs.push(`order references undefined section: ${oid}`);
  for (const k of Object.keys(form?.repetition ?? {})) {
    if (!idSet.has(k)) errs.push(`repetition references undefined section: ${k}`);
    const r = form.repetition[k];
    if (r && r.min > r.max) errs.push(`repetition min > max for ${k}`);
  }
  return errs;
}

const good = {
  sections: [
    { id: "verse.1", role: "verse" },
    { id: "chorus.1", role: "chorus" },
  ],
  order: ["verse.1", "chorus.1", "verse.1"],
  repetition: { "verse.1": { min: 2, max: 4 } },
};

ok("good form has no semantic errors", formErrors(good).length === 0);
ok("duplicate section ids flagged", formErrors({ sections: [{ id: "v", role: "verse" }, { id: "v", role: "chorus" }], order: ["v"] }).length > 0);
ok("order referencing undefined section flagged", formErrors({ sections: [{ id: "v", role: "verse" }], order: ["ghost"] }).length > 0);
ok("repetition referencing undefined section flagged", formErrors({ sections: [{ id: "v", role: "verse" }], order: ["v"], repetition: { ghost: { min: 1, max: 2 } } }).length > 0);
ok("repetition min > max flagged", formErrors({ sections: [{ id: "v", role: "verse" }], order: ["v"], repetition: { v: { min: 4, max: 2 } } }).length > 0);
ok("repetition min == max (fixed count) allowed", formErrors({ sections: [{ id: "v", role: "verse" }], order: ["v"], repetition: { v: { min: 3, max: 3 } } }).length === 0);

// --- Root-schema integration: a real document with a form block validates
// through muse.schema.json via the CLI (which resolves all $refs). ---
import { spawnSync } from "node:child_process";
import { writeFile, rm, mkdtemp } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";

const fullDoc = {
  muse_version: "0.1.0",
  metadata: {
    id: "01J9QR4T8V0W2X6Y8Z0A2C4E6G",
    title: "t",
    composer: { name: "c" },
    created: "2026-08-22T00:00:00Z",
    license: { renditions: "presets-only" },
    provenance: [],
  },
  globals: { tempo: { bpm: 96 }, meter: { beats: 4, unit: 4 }, key: { tonic: "D", mode: "dorian" }, duration_bars: 8 },
  form: good,
};
const dir = await mkdtemp(path.join(tmpdir(), "muse-form-int-"));
const docPath = path.join(dir, "doc.muse.json");
await writeFile(docPath, JSON.stringify(fullDoc));
const r = spawnSync(process.execPath, ["tools/validate.mjs", docPath], { encoding: "utf8" });
await rm(dir, { recursive: true, force: true });
ok("document with form validates through root schema (CLI)", r.status === 0);
if (r.status !== 0) console.error(r.stderr);

console.log(`${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
