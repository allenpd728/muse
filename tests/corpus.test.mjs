// Tests for benchmark/corpus/*.muse.json (issue #78, per
// tests/open_20260822-134500_benchmark-corpus.md).
// Standalone runner: `node tests/corpus.test.mjs`; also folded into npm test.
import { readFile, readdir } from "node:fs/promises";
import { spawnSync } from "node:child_process";
import { danglingRefs } from "../tools/test.mjs";
import { checkSemantics } from "../tools/semantics.mjs";

const corpusDir = new URL("../benchmark/corpus/", import.meta.url);
const files = (await readdir(corpusDir)).filter((f) => f.endsWith(".muse.json")).sort();
const docs = new Map();
for (const f of files) docs.set(f, JSON.parse(await readFile(new URL(f, corpusDir), "utf8")));

let passed = 0, failed = 0;
const check = (name, cond) => {
  if (cond) { passed++; console.log(`ok   ${name}`); }
  else { failed++; console.error(`FAIL ${name}`); }
};

// Corpus stays validating on schema evolution: same three channels as the
// harness's example loop — schema (via the real CLI), cross-refs, semantics.
for (const f of files) {
  const r = spawnSync(process.execPath, ["tools/validate.mjs", `benchmark/corpus/${f}`], { encoding: "utf8" });
  check(`${f} validates against root schema`, r.status === 0);
  check(`${f} cross-refs resolve`, danglingRefs(docs.get(f)).length === 0);
  check(`${f} semantics clean`, checkSemantics(docs.get(f)).length === 0);
}

// Provenance invariant: every entry carries an import event with ai: false.
for (const f of files) {
  const prov = docs.get(f).metadata?.provenance ?? [];
  check(`${f} has import provenance with ai: false`,
    prov.some((e) => e.event === "import" && e.ai === false));
}

// README table accuracy: one table row per corpus file.
{
  const readme = await readFile(new URL("../benchmark/corpus/README.md", import.meta.url), "utf8");
  const rows = readme.split("\n").filter((l) => l.startsWith("| `") && l.includes(".muse.json"));
  check("README entry table row count == corpus file count", rows.length === files.length);
  check("README lists every corpus file",
    files.every((f) => readme.includes(f)));
}

// Re-import determinism smoke (chorale subset — Haydn needs heap flags per
// README): re-import two sources; output still validates and is content-
// identical modulo the provenance timestamp.
{
  const { execFileSync } = await import("node:child_process");
  const { mkdtemp, rm } = await import("node:fs/promises");
  const { tmpdir } = await import("node:os");
  const path = await import("node:path");
  const tmp = await mkdtemp(path.join(tmpdir(), "muse-corpus-"));
  try {
    for (const name of ["bwv269", "bwv316"]) {
      const out = path.join(tmp, `${name}.muse.json`);
      execFileSync(process.execPath, ["importer/cli.mjs", `benchmark/corpus/sources/${name}.mxl`, "-o", out]);
      const reimported = JSON.parse(await readFile(out, "utf8"));
      const v = spawnSync(process.execPath, ["tools/validate.mjs", out], { encoding: "utf8" });
      check(`${name} re-import validates`, v.status === 0);
      // Per-import freshness — provenance `at`, metadata.created, the work
      // ULID — differs by design; nothing else may.
      const strip = (d) => JSON.stringify(d, (k, val) =>
        (k === "at" || k === "created" || (k === "id" && typeof val === "string" && val.startsWith("muse:work:")) ? undefined : val));
      check(`${name} re-import content identical modulo id/timestamps`,
        strip(reimported) === strip(docs.get(`${name}.muse.json`)));
    }
  } finally {
    await rm(tmp, { recursive: true, force: true });
  }
}

console.log(`${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
