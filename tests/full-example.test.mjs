// Tests for examples/full.muse.json (issue #40, spec: tests/open_20260822-023000_full-example.md).
// Standalone runner: `node tests/full-example.test.mjs`. Folded into `npm test`
// by the harness's tests/*.test.mjs scan.
import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { danglingRefs } from "../tools/test.mjs";

let passed = 0, failed = 0;
const ok = (name, cond, detail) => {
  if (cond) { passed++; console.log(`ok   ${name}`); }
  else { failed++; console.error(`FAIL ${name}${detail ? ` — ${detail}` : ""}`); }
};

const DOC_PATH = "examples/full.muse.json";
const doc = JSON.parse(readFileSync(DOC_PATH, "utf8"));

// Validates against the root schema via the real CLI.
let cli;
try {
  execFileSync(process.execPath, ["tools/validate.mjs", DOC_PATH, "schema/muse.schema.json"], { encoding: "utf8" });
  cli = { code: 0 };
} catch (e) {
  cli = { code: e.status ?? 1, stderr: e.stderr };
}
ok("full example validates against root schema", cli.code === 0, cli.stderr);

// Exercises every top-level section of the spec (§2).
const SECTIONS = ["muse_version", "metadata", "globals", "material", "form", "constraints", "renditions", "extensions"];
for (const s of SECTIONS) ok(`document has top-level ${s}`, doc[s] !== undefined);

// Harness cross-refs clean (form uses/harmony + constraints.must_contain).
const dx = danglingRefs(doc);
ok("harness danglingRefs reports nothing", dx.length === 0, JSON.stringify(dx));

// Every id-referencing field resolves, including seams the harness does not
// scan: theme phrase motif refs (transform-suffixed) and constraints keys.
const baseRef = (ref) => String(ref).split("#")[0];
const materialIds = new Set();
for (const key of ["motifs", "themes", "rhythms"])
  for (const item of doc.material?.[key] ?? []) materialIds.add(item.id);
const progIds = new Set((doc.material?.harmony?.progressions ?? []).map((p) => p.id));
const sectionIds = new Set((doc.form?.sections ?? []).map((s) => s.id));

const unresolved = [];
for (const t of doc.material?.themes ?? [])
  for (const p of t.phrases ?? [])
    for (const m of p.motifs ?? [])
      if (!materialIds.has(baseRef(m))) unresolved.push(`material.themes[${t.id}] phrase ref ${m}`);
ok("theme phrase motif refs resolve (transform-stripped)", unresolved.length === 0, unresolved.join(", "));

const unresolvedKeys = [];
for (const key of Object.keys(doc.constraints?.register ?? {}))
  if (!materialIds.has(key)) unresolvedKeys.push(`constraints.register key ${key}`);
for (const key of Object.keys(doc.constraints?.tempo_lock ?? {}))
  if (!sectionIds.has(key)) unresolvedKeys.push(`constraints.tempo_lock key ${key}`);
ok("constraints register/tempo_lock keys resolve to material/section ids", unresolvedKeys.length === 0, unresolvedKeys.join(", "));

// Seams: a motif referenced in form, constrained in constraints, present under
// a rendition — the example must exercise the cross-section joins, not just
// each section in isolation.
const usedBaseRefs = new Set(
  (doc.form?.sections ?? []).flatMap((s) => (s.uses ?? []).map((u) => baseRef(u.ref)))
);
ok("a form-used theme contains a must_contain motif",
  [...usedBaseRefs].some((r) => {
    const theme = (doc.material?.themes ?? []).find((t) => t.id === r);
    const phraseMotifs = (theme?.phrases ?? []).flatMap((p) => (p.motifs ?? []).map(baseRef));
    return (doc.constraints?.must_contain ?? []).some((m) => phraseMotifs.includes(baseRef(m)));
  }));
ok("every form.order entry names a defined section",
  (doc.form?.order ?? []).every((id) => sectionIds.has(id)));
ok("repetition keys name defined sections",
  Object.keys(doc.form?.repetition ?? {}).every((id) => sectionIds.has(id)));

console.log(`${passed} passed, ${failed} failed`);
process.exit(failed === 0 ? 0 : 1);
