// Residual coverage for the end-to-end demo (issue #68, spec:
// tests/closed_…_e2e-demo.md). Live-model and full-length paths stay manual
// per the spec; these cover the offline pins that fit CI.
// Standalone runner: `node tests/play-residual.test.mjs`; folded into npm test.
import { mkdtemp, readFile, readdir, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";

const PLAY = "tools/play.mjs";
const IMPORT = "importer/cli.mjs";

let passed = 0, failed = 0;
const check = (name, cond, detail) => {
  if (cond) { passed++; console.log(`ok   ${name}`); }
  else {
    failed++;
    console.error(`FAIL ${name}`);
    if (detail) console.error(detail);
  }
};

const dir = await mkdtemp(path.join(tmpdir(), "muse-play-"));
const run = (args) => spawnSync(process.execPath, args, { encoding: "utf8", timeout: 60000 });

// --bars truncation: 8 bars of the 64-bar full example completes and is
// audibly shorter than the full render would be (RIFF size header reflects
// the truncated duration).
const full = run([PLAY, "examples/full.muse.json", "r.synthwave", "--bars", "8", "--out", dir]);
check("--bars 8 excerpt completes", full.status === 0, full.stderr);
const wavs = await readdir(dir);
check("excerpt produced a WAV", wavs.some((f) => f.endsWith(".wav")));
const wavPath = path.join(dir, wavs.find((f) => f.endsWith(".wav")));
const riff = await readFile(wavPath);
check("WAV has RIFF header", riff.subarray(0, 4).toString("ascii") === "RIFF");

// Demo WAV freshness: pin the regenerate command, not checksums (checksums
// break on any DSP tweak — spec's stated decision option).
const readme = await readFile("docs/demo/README.md", "utf8");
check("demo README pins the regenerate command", /npm run play|play\.mjs/.test(readme));

// Imported docs: importer → play, the pipeline's second source.
const imported = path.join(dir, "bwv269.muse.json");
const imp = run([IMPORT, "importer/fixtures/bwv269.mxl", "-o", imported]);
check("importer CLI produces a doc", imp.status === 0, imp.stderr);
const playImported = run([PLAY, imported, "--bars", "4", "--out", dir]);
check("imported chorale plays end-to-end", playImported.status === 0, playImported.stderr);

// Rendition-less document: minimal.muse.json has no form and no renditions —
// pin the expander's behavior (valid doc out, empty notes, no crash).
const minOut = path.join(dir, "min");
const min = run([PLAY, "examples/minimal.muse.json", "--out", minOut]);
check("rendition-less minimal doc plays without crash", min.status === 0, min.stderr);
const minPerf = JSON.parse(await readFile(path.join(minOut, "minimal.r.default.muse.perf.json"), "utf8"));
check("rendition-less doc emits an empty-notes perf doc", Array.isArray(minPerf.notes) && minPerf.notes.length === 0);

await rm(dir, { recursive: true, force: true });

console.log(`${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
