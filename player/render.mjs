// Player V1 CLI + WAV wrapper (issue #24, per docs/scope-batch3.md).
// The pure renderer (render, droppedTechniques) lives in render-core.mjs —
// browser-safe for the listener (#97/#98). This file adds the node-only
// pieces: 16-bit PCM WAV encoding (Buffer) and the CLI.
import { render } from "./render-core.mjs";
export { render, droppedTechniques } from "./render-core.mjs";

export function renderWav(perfDoc, { sampleRate = 44100 } = {}) {
  const channels = render(perfDoc, { sampleRate });
  const nCh = channels.length;
  const frames = channels[0].length;
  const dataSize = frames * nCh * 2;
  const buf = Buffer.alloc(44 + dataSize);
  buf.write("RIFF", 0); buf.writeUInt32LE(36 + dataSize, 4); buf.write("WAVE", 8);
  buf.write("fmt ", 12); buf.writeUInt32LE(16, 16); buf.writeUInt16LE(1, 20);
  buf.writeUInt16LE(nCh, 22); buf.writeUInt32LE(sampleRate, 24);
  buf.writeUInt32LE(sampleRate * nCh * 2, 28); buf.writeUInt16LE(nCh * 2, 32);
  buf.writeUInt16LE(16, 34);
  buf.write("data", 36); buf.writeUInt32LE(dataSize, 40);
  for (let i = 0; i < frames; i++)
    for (let c = 0; c < nCh; c++)
      buf.writeInt16LE(Math.max(-32768, Math.min(32767, Math.round(channels[c][i] * 32767))), 44 + (i * nCh + c) * 2);
  return buf;
}

// --- CLI ---
import path from "node:path";
const invokedDirectly = process.argv[1] && path.resolve(process.argv[1]) === new URL(import.meta.url).pathname;
if (invokedDirectly) {
  const { readFile, writeFile } = await import("node:fs/promises");
  const [perfPath, outPath] = process.argv.slice(2);
  if (!perfPath || !outPath) {
    console.error("usage: node player/render.mjs <doc.muse.perf.json> <out.wav>");
    process.exit(1);
  }
  const perf = JSON.parse(await readFile(perfPath, "utf8"));
  await writeFile(outPath, renderWav(perf));
  const secs = (perf.notes ?? []).reduce((m, n) => Math.max(m, n.onset + n.duration), 0).toFixed(2);
  console.error(`rendered ${perfPath} → ${outPath} (${(perf.notes ?? []).length} notes, ~${secs}s)`);
}
