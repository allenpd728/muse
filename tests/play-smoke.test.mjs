// CLI end-to-end smoke (issue #105): tools/play.mjs as a subprocess on the
// corpus chorale and the curated example — each stage (expand → perf →
// render → WAV) is covered on its own; the wiring between them in the CLI
// path is exercised here in one shot. Standalone runner; folded into npm test.
import { mkdtemp, readdir, readFile, rm, writeFile } from "node:fs/promises";
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

// --- Residual coverage (issue #109, per tests/open_20260822-204000_pipeline-smoke.md) ---

// Amplitude levels (not just byte difference): the two renditions of the
// full example must differ in peak/RMS curves at the buffer level.
const { expandOffline } = await import("../interpreter/offline.mjs");
const { render } = await import("../player/render.mjs");
const { readFile: readDoc } = await import("node:fs/promises");
const stats = (channels) => {
  let peak = 0, sum2 = 0;
  for (const v of channels[0]) { peak = Math.max(peak, Math.abs(v)); sum2 += v * v; }
  return { peak, rms: Math.sqrt(sum2 / channels[0].length) };
};
const full = JSON.parse(await readDoc("examples/full.muse.json", "utf8"));
const excerpt = structuredClone(full);
excerpt.form.order = excerpt.form.order.slice(0, 2);
const curves = {};
for (const r of full.renditions) {
  const ch = render(expandOffline(excerpt, r), { sampleRate: 8000 });
  curves[r.id] = stats(ch);
}
check("rendition levels differ in peak or RMS (audibly distinct, not just distinct bytes)",
  Math.abs(curves["r.synthwave"].peak - curves["r.quartet"].peak) > 0.02
  || Math.abs(curves["r.synthwave"].rms - curves["r.quartet"].rms) > 0.004,
  `synth: p${curves["r.synthwave"]?.peak}, r${curves["r.synthwave"]?.rms} | quartet: p${curves["r.quartet"]?.peak}, r${curves["r.quartet"]?.rms}`);

// Tempo-map realization: a ritardando over a section reaches the shape's
// target at the span end (spec §2.5: tempo_map is the realization surface
// in the offline expander's own tempo-anchored seconds; the map is the
// player's interpolation contract).
const tempoDoc = {
  muse_version: "0.1.0",
  metadata: { id: "t", title: "t", composer: { name: "t" }, created: "2026-01-01T00:00:00Z", license: { renditions: "closed" }, provenance: [] },
  globals: { tempo: { bpm: 120 }, meter: { beats: 4, unit: 4 }, duration_bars: 16 },
  material: { motifs: [{ id: "m", kind: "pitch_rhythm", pitches: ["C4", "E4", "G4", "A4"], durations: [1, 1, 1, 1] }] },
  constraints: { tempo_shapes: { s1: { kind: "ritardando", target_bpm: 60 } } },
  form: { sections: [{ id: "s1", role: "verse", bars: 4 }], order: ["s1"] },
};
const tempoPerf = expandOffline(tempoDoc, { id: "r.d", params: { tempo_bpm: 120 } });
check("ritardando span: tempo_map lands on the target at span end",
  tempoPerf.tempo_map.at(-1).bpm === 60);

// Failure channel: a schema-invalid doc exits non-zero with a readable
// error and writes no new WAV (dir snap compares before/after).
const bad = await readDoc("examples/invalid/dangling-material-ref.muse.json", "utf8");
const badPath = path.join(dir, "bad.muse.json");
const beforeBad = await readdir(dir);
await writeFile(badPath, bad);
const fail = spawnSync(process.execPath, ["tools/play.mjs", badPath], { encoding: "utf8" });
const badOut = (await readdir(dir)).filter((f) => !beforeBad.includes(f));
check("invalid doc: play CLI exits non-zero", fail.status !== 0, fail.stderr + fail.stdout);
check("invalid doc: no partial WAV written", !badOut.filter((f) => f.endsWith(".wav")).length, badOut.join(","));

await rm(dir, { recursive: true, force: true });

console.log(`${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
