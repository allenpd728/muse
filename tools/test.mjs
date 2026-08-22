#!/usr/bin/env node
// Test harness for the validator + cross-reference integrity (Batch 1 #3).
// 1. Fixture self-tests prove the harness works in both directions.
// 2. Every examples/*.muse.json must validate and resolve all refs.
// 3. Every examples/invalid/*.muse.json must be rejected.
// Exit 0 if all assertions pass, 1 otherwise.
import { existsSync } from "node:fs";
import { readFile, readdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";

const SCHEMA = "schema/muse.schema.json";
const FIXTURES = "tools/fixtures";

let pass = 0, fail = 0;
const ok = (name) => { pass++; console.log(`ok ${pass + fail} - ${name}`); };
const bad = (name, detail) => {
  fail++;
  console.log(`not ok ${pass + fail} - ${name}`);
  if (detail) console.log(detail.split("\n").map((l) => `  ${l}`).join("\n"));
};

// Validate a document via the real CLI (exit code + stderr are the contract).
const runCli = (docPath) => {
  const r = spawnSync(process.execPath, ["tools/validate.mjs", docPath, SCHEMA], { encoding: "utf8" });
  return { code: r.status ?? 1, stdout: r.stdout ?? "", stderr: r.stderr ?? "" };
};

const readJson = async (p) => JSON.parse(await readFile(p, "utf8"));

// --- Cross-reference integrity (code, not ajv) ---
// Material ids: motifs, themes, rhythms entries carry `id`; refs may carry
// transform suffixes (`motif.a#seq(+2)`) that strip to the base id.
const materialIds = (doc) => {
  const ids = new Set();
  for (const key of ["motifs", "themes", "rhythms"])
    for (const item of doc?.material?.[key] ?? []) if (item?.id) ids.add(item.id);
  return ids;
};
const progressionIds = (doc) =>
  new Set((doc?.material?.harmony?.progressions ?? []).map((p) => p?.id).filter(Boolean));

const baseRef = (ref) => String(ref).split("#")[0];

export function danglingRefs(doc) {
  const ids = materialIds(doc);
  const progs = progressionIds(doc);
  const out = [];
  for (const s of doc?.form?.sections ?? []) {
    if (s?.harmony && !progs.has(s.harmony))
      out.push({ path: `form.sections[${s.id}].harmony`, ref: s.harmony });
    for (const u of s?.uses ?? [])
      if (u?.ref && !ids.has(baseRef(u.ref)))
        out.push({ path: `form.sections[${s.id}].uses`, ref: u.ref });
  }
  for (const ref of doc?.constraints?.must_contain ?? [])
    if (!ids.has(baseRef(ref))) out.push({ path: "constraints.must_contain", ref });
  return out;
}

const listJson = async (dir) =>
  (await readdir(dir)).filter((f) => f.endsWith(".muse.json")).sort();

// --- Main ---

// Unit tests import danglingRefs() without running the harness (see
// tests/test-harness.test.mjs, per tests/open_20260822-013951_test-harness.md).
const invokedDirectly =
  !!process.argv[1] &&
  path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (invokedDirectly) {
const name = (p) => path.basename(p);

// 1. Fixtures: a valid doc, a schema-invalid doc, and a schema-valid doc with
// dangling refs (the valid doc minus one material id — proves removing a
// referenced id turns the harness red).
const fx = {
  valid: await readJson(path.join(FIXTURES, "valid.muse.json")),
  invalid: path.join(FIXTURES, "invalid.muse.json"),
  dangling: await readJson(path.join(FIXTURES, "dangling-ref.muse.json")),
};

const vReq = runCli(path.join(FIXTURES, "valid.muse.json"));
vReq.code === 0 && danglingRefs(fx.valid).length === 0
  ? ok("fixture valid.muse.json passes schema + refs")
  : bad("fixture valid.muse.json passes schema + refs", vReq.stderr);

const iReq = runCli(fx.invalid);
iReq.code === 1
  ? ok("fixture invalid.muse.json rejected by schema")
  : bad("fixture invalid.muse.json rejected by schema");

const d = await readJson(path.join(FIXTURES, "dangling-ref.muse.json"));
const dx = danglingRefs(d);
dx.length > 0
  ? ok("fixture dangling-ref.muse.json reports dangling refs")
  : bad("fixture dangling-ref.muse.json reports dangling refs");

// 2-3. Examples (once later Batch 1 tasks land them).
const examplesDir = "examples";
const mustPass = async (dir) => {
  for (const f of await listJson(dir)) {
    const p = path.join(dir, f);
    const doc = await readJson(p);
    const cli = runCli(p);
    const dx = danglingRefs(doc);
    cli.code === 0 && dx.length === 0
      ? ok(`${p} valid`)
      : bad(`${p} valid`, cli.stderr || dx.map((x) => `${x.path}: ${x.ref}`).join("\n"));
  }
};
const mustReject = async (dir) => {
  for (const f of await listJson(dir)) {
    const p = path.join(dir, f);
    const doc = await readJson(p).catch(() => null);
    const cli = runCli(p);
    const dx = doc ? danglingRefs(doc) : [];
    const rejected = cli.code !== 0 || dx.length > 0;
    let detail = cli.stdout || "schema accepted; refs resolved";
    if (rejected && existsSync(p.replace(/\.muse\.json$/, ".expected.json"))) {
      const expected = await readJson(p.replace(/\.muse\.json$/, ".expected.json"));
      const errorText = cli.stderr + dx.map((x) => `${x.path}: ${x.ref}`).join("\n");
      const missing = (expected.messages ?? []).filter((m) => !errorText.includes(m));
      if (missing.length > 0) {
        bad(`${p} rejected`, `expected error text missing: ${missing.join(", ")}`);
        continue;
      }
    }
    rejected ? ok(`${p} rejected`) : bad(`${p} rejected`, detail);
  }
};

if (existsSync(examplesDir)) {
  await mustPass(examplesDir);
  if (existsSync(path.join(examplesDir, "invalid"))) await mustReject(path.join(examplesDir, "invalid"));
} else {
  console.log("# examples/ not present yet — fixture checks only");
}

// Standalone test suites fold in when present (e.g. tests/validate-cli.test.mjs).
for (const f of (await readdir("tests")).filter((x) => x.endsWith(".test.mjs")).sort()) {
  const r = spawnSync(process.execPath, [path.join("tests", f)], { encoding: "utf8" });
  process.stdout.write(r.stdout ?? "");
  process.stderr.write(r.stderr ?? "");
  r.status === 0 ? ok(`tests/${f} suite passes`) : bad(`tests/${f} suite passes`);
}

console.log(`# ${pass} passed, ${fail} failed`);
process.exit(fail === 0 ? 0 : 1);
}
