// End-to-end corpus + CLI tests (issue #20; residual coverage issue #60).
// Corpus fixtures import to validating .muse.json through the real CLI; the
// corpus set is enumerated from the fixtures directory, not hardcoded — adding
// a chorale is adding a file. Standalone runner; folded into npm test.
import { readdir, readFile, writeFile, mkdtemp, rm } from "node:fs/promises";
import { existsSync as existsSyncFs } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";

const CLI = "importer/cli.mjs";
const FIXTURES = "importer/fixtures";
// Corpus = every importable fixture in the directory (no hardcoded list).
const CORPUS = (await readdir(FIXTURES)).filter((f) => /\.(mid|midi|musicxml|mxl)$/i.test(f)).sort();

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
const run = (args) => spawnSync(process.execPath, [CLI, ...args], { encoding: "utf8" });

for (const file of CORPUS) {
  const out = path.join(dir, file.replace(/\.\w+$/, ".muse.json"));
  const r = run([path.join(FIXTURES, file), "-o", out]);
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
await writeFile(renamed, midiBytes);
const rr = run([renamed, "-o", path.join(dir, "renamed.muse.json")]);
check("format detected by magic bytes, not extension", rr.status === 0, rr.stderr);

// Unknown format exits 1 with a readable error.
const garbage = path.join(dir, "garbage.bin");
await writeFile(garbage, Buffer.from([1, 2, 3, 4]));
const gr = run([garbage, "-o", path.join(dir, "g.muse.json")]);
check("unknown format exits 1 with error", gr.status === 1 && /cannot detect format/.test(gr.stderr), gr.stderr);

// --- Residual coverage (issue #60) ---
const noArgs = run([]);
check("no args: usage + exit 1", noArgs.status === 1 && /usage:/.test(noArgs.stderr));

const noOut = run([path.join(FIXTURES, "midi-sample.mid")]);
check("missing -o: usage + exit 1", noOut.status === 1 && /usage:/.test(noOut.stderr));

const missingInput = run([path.join(dir, "nope.mid"), "-o", path.join(dir, "x.json")]);
check("missing input file: readable error + exit 1", missingInput.status === 1 && /cannot read/.test(missingInput.stderr));

const badOutDir = run([path.join(FIXTURES, "midi-sample.mid"), "-o", path.join(dir, "nope-dir", "x.json")]);
check("non-existent output directory: readable error + exit 1", badOutDir.status === 1 && /cannot write/.test(badOutDir.stderr));
check("non-existent output directory: no partial artifact", !existsSyncFs(path.join(dir, "nope-dir")));

// .midi extension fallback (bytes are MIDI, extension is the long form).
const longExt = path.join(dir, "sample.midi");
await writeFile(longExt, midiBytes);
check(".midi extension detected as MIDI", run([longExt, "-o", path.join(dir, "long.muse.json")]).status === 0);

// Uncompressed .musicxml corpus entry imports (extension fallback for non-zip).
const xmlOut = path.join(dir, "xml.muse.json");
const xr = run([path.join(FIXTURES, "bwv269.musicxml"), "-o", xmlOut]);
check("uncompressed .musicxml imports", xr.status === 0, xr.stderr);

// Corpus growth is directory-enumerated: at least the seeded set is present.
check("corpus enumerates seeded fixtures", CORPUS.includes("bwv269.mxl") && CORPUS.includes("bwv269.musicxml") && CORPUS.includes("midi-sample.mid"));

await rm(dir, { recursive: true, force: true });

console.log(`${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
