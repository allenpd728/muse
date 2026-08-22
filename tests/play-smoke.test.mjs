// CLI end-to-end smoke (issue #105): tools/play.mjs as a subprocess on the
// corpus chorale and the curated example — each stage (expand → perf →
// render → WAV) is covered on its own; the wiring between them in the CLI
// path is exercised here in one shot. Standalone runner; folded into npm test.
import { mkdtemp, readdir, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";

let passed = 0, failed = 0;
const check = (name, cond, detail) => {
  if (cond) { passed++; console.log(`ok   ${name}`); }
  else {
    failed++;
    console.error(`FAIL ${name}`);
    if (detail) console.error(detail);
  }
};

const dir = await mkdtemp(path.join(tmpdir(), "muse-smoke-"));

const riffSummary = (bytes) => {
  const dv = new DataView(bytes.buffer, bytes.byteOffset, bytes.length);
  if (bytes.subarray(0, 4).toString("ascii") !== "RIFF") return { header: false };
  // PCM int16 body: count non-silent frames.
  const bodyStart = 44;
  let nonSilent = 0;
  for (let i = bodyStart; i + 1 < bytes.length - 4; i += 4) {
    if (Math.abs(dv.getInt16(i, true)) > 10) nonSilent++;
  }
  return { header: true, samples: (bytes.length - 44) / 4, nonSilent };
};

for (const [doc, rendition, bars] of [
  ["benchmark/corpus/bwv269.muse.json", "r.default", "4"],
  ["examples/full.muse.json", "r.synthwave", "8"],
]) {
  const r = spawnSync(process.execPath, ["tools/play.mjs", doc, rendition, "--bars", String(bars), "--out", dir], { encoding: "utf8", timeout: 60000 });
  const wavs = (await readdir(dir)).filter((f) => f.endsWith(".wav"));
  const base = path.basename(doc).replace(/\.muse\.json$/, "");
  const expected = `${base}.${rendition}.wav`;
  const wav = wavs.find((f) => f === expected);
  const someWav = wavs.length === 1 ? wavs[0] : wav;
  check(`${base}: play CLI exits 0`, r.status === 0, r.stderr);
  check(`${base}: WAV produced`, !!someWav);
  const bytes = await readFile(path.join(dir, someWav));
  const summary = riffSummary(bytes);
  check(`${base}: valid RIFF header`, summary.header);
  check(`${base}: non-silent audio`, summary.nonSilent > 0);
  check(`${base}: duration floor (~1s at 22.05kHz = 4410 samples/s)`, summary.samples >= 4410);
}

await rm(dir, { recursive: true, force: true });

console.log(`${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
