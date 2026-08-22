// End-to-end corpus + CLI tests (issue #20): every corpus fixture imports to
// a validating .muse.json through the real CLI. The corpus is the public-domain
// Bach chorale (bwv269.mxl) plus the MIDI fixtures; expected outputs are the
// invariants below, not golden files — structure over snapshot.
// Standalone runner: `node tests/import-cli.test.mjs`; folded into npm test.
import { readdir, readFile, mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";

const CLI = "importer/cli.mjs";
const FIXTURES = "importer/fixtures";
const CORPUS = ["bwv269.mxl", "midi-sample.mid"]; // public-domain / generated fixtures

let passed = 0, failed = 0;
const check = (name, cond, detail) => {
  if (cond) { passed++; console.log(`ok   ${name}`); }
  else {
    failed++;
    console.error(`FAIL ${name}`);
    if (detail) console.error(detail);
  }
};

const dir = await mkdtemp(path.join(tmpdir(), "muse-import-"));

for (const file of CORPUS) {
  const out = path.join(dir, file.replace(/\.\w+$/, ".muse.json"));
  const r = spawnSync(process.execPath, [CLI, path.join(FIXTURES, file), "-o", out], { encoding: "utf8" });
  check(`${file}: CLI exits 0`, r.status === 0, r.stderr);

  const doc = JSON.parse(await readFile(out, "utf8"));
  check(`${file}: output is a .muse.json document`, doc.muse_version && doc.metadata && doc.globals);
  check(`${file}: provenance records the import`, doc.metadata.provenance.some((e) => e.event === "import" && e.ai === false));

  // The CLI validates before writing; re-validate the written artifact so a
  // CLI regression can't leave a bad file on disk.
  const v = spawnSync(process.execPath, ["tools/validate.mjs", out], { encoding: "utf8" });
  check(`${file}: written output validates`, v.status === 0, v.stderr);
}

// Format detection by magic bytes: a .mid renamed to .dat still imports as MIDI.
const midiBytes = await readFile(path.join(FIXTURES, "midi-sample.mid"));
const renamed = path.join(dir, "renamed.dat");
await (await import("node:fs/promises")).writeFile(renamed, midiBytes);
const rr = spawnSync(process.execPath, [CLI, renamed, "-o", path.join(dir, "renamed.muse.json")], { encoding: "utf8" });
check("format detected by magic bytes, not extension", rr.status === 0, rr.stderr);

// Unknown format exits 1 with a readable error.
const garbage = path.join(dir, "garbage.bin");
await (await import("node:fs/promises")).writeFile(garbage, Buffer.from([1, 2, 3, 4]));
const gr = spawnSync(process.execPath, [CLI, garbage, "-o", path.join(dir, "g.muse.json")], { encoding: "utf8" });
check("unknown format exits 1 with error", gr.status === 1 && /cannot detect format/.test(gr.stderr), gr.stderr);

await rm(dir, { recursive: true, force: true });

console.log(`${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
