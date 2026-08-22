// A/B crossfade pins (issue #99, docs/scope-listener.md task 3): position
// mapping across tempos and the equal-power gain law.
import { describe, test, expect } from "vitest";
import { positionToBar, barToPosition, crossfadeGains, planSwitch } from "./crossfade.js";

const doc = { globals: { meter: { beats: 4, unit: 4 }, tempo: { bpm: 96 } } };
const compound = { globals: { meter: { beats: [3, 3, 2], unit: 8 } } }; // 4 beats/bar

describe("position ⇄ bar mapping", () => {
  test("positionToBar converts seconds to fractional bars at the rendition tempo", () => {
    // 10s at 120bpm = 20 beats = 5 bars (4/4)
    expect(positionToBar(doc, 10, 120)).toBe(5);
    // 10s at 60bpm = 10 beats = 2.5 bars
    expect(positionToBar(doc, 10, 60)).toBe(2.5);
  });
  test("barToPosition inverts positionToBar", () => {
    expect(barToPosition(doc, 5, 120)).toBe(10);
    expect(barToPosition(doc, 2.5, 60)).toBe(10);
  });
  test("compound meter arrays resolve to beats per bar", () => {
    // [3,3,2]/8 = 8 eighths = 4 beats per bar — same as 4/4
    expect(positionToBar(compound, 10, 120)).toBe(5);
  });
  test("missing meter falls back to 4 beats per bar", () => {
    expect(positionToBar({ globals: {} }, 10, 120)).toBe(5);
  });
});

describe("crossfade gains", () => {
  test("endpoints: full A at t=0, full B at t=1", () => {
    expect(crossfadeGains(0)[0]).toBeCloseTo(1, 10);
    expect(crossfadeGains(0)[1]).toBeCloseTo(0, 10);
    expect(crossfadeGains(1)[0]).toBeCloseTo(0, 10);
    expect(crossfadeGains(1)[1]).toBeCloseTo(1, 10);
  });
  test("midpoint is equal-power (both ≈ 0.707)", () => {
    const [a, b] = crossfadeGains(0.5);
    expect(a).toBeCloseTo(Math.SQRT1_2, 5);
    expect(b).toBeCloseTo(Math.SQRT1_2, 5);
  });
  test("total power is constant across the fade", () => {
    for (const t of [0, 0.25, 0.5, 0.75, 1]) {
      const [a, b] = crossfadeGains(t);
      expect(a * a + b * b).toBeCloseTo(1, 10);
    }
  });
  test("out-of-range clamps", () => {
    expect(crossfadeGains(-0.5)[0]).toBeCloseTo(1, 10);
    expect(crossfadeGains(1.5)[1]).toBeCloseTo(1, 10);
  });
});

describe("switch planning", () => {
  test("bar position maps across different tempos", () => {
    // 10s at 100bpm = 16.67 beats = 4.167 bars; at 88bpm the same bar is 11.36s
    const { bar, targetSeconds } = planSwitch(doc, 10, 100, 88);
    expect(bar).toBeCloseTo(positionToBar(doc, 10, 100), 10);
    expect(targetSeconds).toBeCloseTo(barToPosition(doc, bar, 88), 10);
    expect(targetSeconds).toBeGreaterThan(10); // slower rendition: same bar, more seconds
  });
  test("same tempo maps position 1:1", () => {
    const { targetSeconds } = planSwitch(doc, 7.5, 96, 96);
    expect(targetSeconds).toBeCloseTo(7.5, 10);
  });
  // Spec: tests/open_20260822-161506_listener-ab.md residual pins.
  test("exact integer bar position is exact (no off-by-one at seams)", () => {
    // 4/4 at 120bpm: bar 4 lands at exactly 8s in both directions.
    const { bar, targetSeconds } = planSwitch(doc, 8, 120, 100);
    expect(bar).toBe(4);
    expect(targetSeconds).toBeCloseTo(barToPosition(doc, 4, 100), 10);
    expect(Number.isInteger(bar)).toBe(true);
  });
  test("zero position maps to zero regardless of tempo", () => {
    const { bar, targetSeconds } = planSwitch(doc, 0, 96, 60);
    expect(bar).toBe(0);
    expect(targetSeconds).toBe(0);
  });
  test("position past the piece end still maps (clamping is the transport's job, not the math's)", () => {
    const { bar } = planSwitch(doc, 1000, 96, 88);
    expect(bar).toBeCloseTo(positionToBar(doc, 1000, 96), 10);
    expect(bar).toBeGreaterThan(0);
  });
  test("multi-hop cycling preserves the bar across three tempos (Chamber lineage)", () => {
    // A→B→C→A across 100/88/72: the bar coordinate is the invariant.
    const ab = planSwitch(doc, 10, 100, 88);
    const bc = planSwitch(doc, ab.targetSeconds, 88, 72);
    const ca = planSwitch(doc, bc.targetSeconds, 72, 100);
    expect(ab.bar).toBeCloseTo(positionToBar(doc, 10, 100), 10);
    expect(bc.bar).toBeCloseTo(ab.bar, 10);
    expect(ca.bar).toBeCloseTo(ab.bar, 10);
    expect(ca.targetSeconds).toBeCloseTo(10, 10);
  });
});
