// Tests for the WebAudio playback core (issue #97, per docs/scope-listener.md
// task 1): buffer math + transport state machine, exercised in node against
// a stub AudioContext — the render math itself is player/render.mjs's own
// test coverage's business.
import { describe, test, expect } from "vitest";
import { buildBuffer, renderToBuffer, createTransport } from "./player.js";

// Minimal AudioContext stand-in: real Float32Array buffers, a clock we
// control, sources that record start/stop.
const stubContext = () => {
  const ctx = {
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
      stopped: 0,
      connect() {},
      start(when, offset) { this.started.push([when, offset]); },
      stop() { this.stopped++; },
    }),
    resume() { this.state = "running"; },
  };
  return ctx;
};

const perf = {
  tempo_map: [{ time: 0, beat: 0, bpm: 120 }],
  parts: [{ id: "p", name: "P", instrument: { name: "piano", program: 0 } }],
  notes: [{ part: "p", pitch: 60, onset: 0, duration: 0.5, onset_beat: 0, duration_beats: 1, velocity: 100 }],
};

describe("playback core", () => {
  test("buildBuffer copies channels with right shape", () => {
    const ctx = stubContext();
    const left = new Float32Array(100).fill(0.5);
    const right = new Float32Array(100).fill(-0.25);
    const buffer = buildBuffer(ctx, [left, right], 8000);
    expect(buffer.numberOfChannels).toBe(2);
    expect(buffer.length).toBe(100);
    expect(buffer.duration).toBeCloseTo(100 / 8000);
    expect(buffer.getChannelData(0)[0]).toBeCloseTo(0.5);
    expect(buffer.getChannelData(1)[0]).toBeCloseTo(-0.25);
  });

  test("renderToBuffer renders a perf doc end to end", () => {
    const ctx = stubContext();
    const buffer = renderToBuffer(ctx, perf, { sampleRate: 8000 });
    expect(buffer.length).toBeGreaterThan(0);
    // A rendered note is not silence.
    expect(buffer.getChannelData(0).some((v) => v !== 0)).toBe(true);
  });

  test("transport: play tracks position with the context clock", () => {
    const ctx = stubContext();
    const buffer = buildBuffer(ctx, [new Float32Array(8000)], 8000); // 1s
    const states = [];
    const t = createTransport(buffer, ctx, { onstatechange: (s) => states.push(s) });
    t.play();
    ctx.currentTime = 0.4;
    expect(t.state().playing).toBe(true);
    expect(t.state().position).toBeCloseTo(0.4);
  });

  test("transport: pause holds position, resume continues", () => {
    const ctx = stubContext();
    const buffer = buildBuffer(ctx, [new Float32Array(8000)], 8000);
    const t = createTransport(buffer, ctx);
    t.play();
    ctx.currentTime = 0.3;
    t.pause();
    expect(t.state().position).toBeCloseTo(0.3);
    ctx.currentTime = 1.0; // time passes while paused
    expect(t.state().position).toBeCloseTo(0.3);
    t.play();
    ctx.currentTime = 1.2;
    expect(t.state().position).toBeCloseTo(0.5);
  });

  test("transport: seek clamps and continues from the target", () => {
    const ctx = stubContext();
    const buffer = buildBuffer(ctx, [new Float32Array(8000)], 8000);
    const t = createTransport(buffer, ctx);
    t.play();
    t.seek(0.7);
    expect(t.state().position).toBeCloseTo(0.7);
    ctx.currentTime = 0.3;
    expect(t.state().position).toBeCloseTo(1.0); // clamps at duration
    t.seek(99);
    expect(t.state().position).toBeCloseTo(1.0);
  });

  test("transport: stop resets to zero", () => {
    const ctx = stubContext();
    const buffer = buildBuffer(ctx, [new Float32Array(8000)], 8000);
    const t = createTransport(buffer, ctx);
    t.play();
    ctx.currentTime = 0.5;
    t.stop();
    expect(t.state()).toMatchObject({ playing: false, position: 0, ended: false });
  });
});
