// Listener end-to-end smoke (issue #105): the expand → render → transport
// seam the Listen tab wires together, headless via a stub AudioContext (the
// pattern from player.test.js). The DOM mount itself stays manual.
import { describe, test, expect } from "vitest";
import { expandOffline } from "../../../interpreter/offline.mjs";
import { renderToBuffer, createTransport } from "./player.js";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

const stubContext = () => ({
  sampleRate: 8000,
  currentTime: 0,
  state: "running",
  destination: {},
  createBuffer: (numChannels, frames, sampleRate) => ({
    numberOfChannels: numChannels,
    length: frames,
    sampleRate,
    duration: frames / sampleRate,
    _channels: Array.from({ length: numChannels }, () => new Float32Array(frames)),
    getChannelData(i) { return this._channels[i]; },
    copyToChannel(data, i) { this._channels[i].set(data); },
  }),
  createBufferSource: () => ({
    buffer: null,
    started: [],
    connect() {},
    start() { this.started.push(true); },
    stop() {},
  }),
  resume() { this.state = "running"; },
});

const doc = JSON.parse(
  readFileSync(fileURLToPath(new URL("../../../examples/full.muse.json", import.meta.url)), "utf8"),
);

// Demo-excerpt truncation (same rule as tools/play.mjs --bars): the smoke
// covers the expand→render→transport wiring, not the full 64-bar render.
const excerpt = structuredClone(doc);
{
  const kept = [];
  let bars = 0;
  for (const id of excerpt.form.order) {
    if (bars >= 4) break;
    kept.push(id);
    bars += excerpt.form.sections.find((s) => s.id === id)?.bars ?? 4;
  }
  excerpt.form.order = kept;
}

describe("listener smoke (expand → render → transport)", () => {
  test("selecting a rendition produces a non-empty buffer and a playing transport", { timeout: 20000 }, () => {
    const ctx = stubContext();
    const rendition = doc.renditions.find((r) => r.id === "r.synthwave");
    const perf = expandOffline(excerpt, rendition);
    expect(perf.notes.length).toBeGreaterThan(0);

    const buffer = renderToBuffer(ctx, perf);
    expect(buffer.length).toBeGreaterThan(0);
    expect(buffer.duration).toBeGreaterThan(0.5);

    const transport = createTransport(buffer, ctx, { onstatechange: () => {} });
    transport.play();
    expect(transport.state().playing).toBe(true);
    transport.stop();
    expect(transport.state().playing).toBe(false);
  });
});
