// WAV download pins (issue #100, docs/scope-listener.md task 4): the
// browser-safe encodeWav path — same encoder the node CLI wraps.
import { describe, test, expect } from "vitest";
import { render, encodeWav } from "../../../player/render-core.mjs";

const perf = {
  tempo_map: [{ time: 0, beat: 0, bpm: 120 }],
  parts: [{ id: "p", name: "P", instrument: { name: "piano", program: 0 } }],
  notes: [{ part: "p", pitch: 60, onset: 0, duration: 0.5, onset_beat: 0, duration_beats: 1, velocity: 100 }],
};

const view = (bytes) => new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);

describe("encodeWav (browser-safe)", () => {
  const bytes = encodeWav(render(perf, { sampleRate: 8000 }), { sampleRate: 8000 });
  const v = view(bytes);

  test("produces a Uint8Array (no Buffer dependency)", () => {
    expect(bytes).toBeInstanceOf(Uint8Array);
    expect(Buffer.isBuffer(bytes)).toBe(false);
  });

  test("RIFF/WAVE header with correct sizes", () => {
    expect(String.fromCharCode(...bytes.subarray(0, 4))).toBe("RIFF");
    expect(String.fromCharCode(...bytes.subarray(8, 12))).toBe("WAVE");
    expect(v.getUint32(4, true)).toBe(bytes.length - 8);
    expect(String.fromCharCode(...bytes.subarray(36, 40))).toBe("data");
    expect(v.getUint32(40, true)).toBe(bytes.length - 44);
  });

  test("stereo 16-bit PCM at the requested rate", () => {
    expect(v.getUint16(22, true)).toBe(2);
    expect(v.getUint16(34, true)).toBe(16);
    expect(v.getUint32(24, true)).toBe(8000);
  });

  test("PCM body matches the rendered channels (clipped to int16)", () => {
    const channels = render(perf, { sampleRate: 8000 });
    const frames = channels[0].length;
    expect(bytes.length).toBe(44 + frames * 2 * 2);
    // Spot-check the first non-zero frame region.
    let sawNonZero = false;
    for (let i = 0; i < frames; i++) {
      const expected = Math.max(-32768, Math.min(32767, Math.round(channels[0][i] * 32767)));
      expect(v.getInt16(44 + i * 4, true)).toBe(expected + 0); // +0/-0 normalize
      if (expected !== 0) sawNonZero = true;
    }
    expect(sawNonZero).toBe(true);
  });

  test("encodeWav(render(...)) equals the node renderWav path byte-for-byte", async () => {
    const { renderWav } = await import("../../../player/render.mjs");
    const viaNode = renderWav(perf, { sampleRate: 8000 });
    const viaCore = encodeWav(render(perf, { sampleRate: 8000 }), { sampleRate: 8000 });
    expect(Buffer.from(viaCore).equals(viaNode)).toBe(true);
  });
});
