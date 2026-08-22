// Filename sanitization pins for the WAV download (issue #104, spec:
// tests/closed_…_listener-wav.md). The download name is
// `${(doc.metadata?.title ?? "muse").replace(/\s+/g, "-")}.${renditionId}.wav`.
// Extracted as wavFilename() so the policy is testable.
import { describe, test, expect } from "vitest";
import wavFilename from "./wav-filename.js";

describe("wavFilename", () => {
  test("spaces collapse to hyphens", () => {
    expect(wavFilename({ title: "Night Circuit" }, "r.synthwave"))
      .toBe("Night-Circuit.r.synthwave.wav");
  });

  test("missing title falls back to muse", () => {
    expect(wavFilename({}, "r.default")).toBe("muse.r.default.wav");
    expect(wavFilename({ title: null }, "r.default")).toBe("muse.r.default.wav");
  });

  test("empty title falls back to muse", () => {
    expect(wavFilename({ title: "" }, "r.x")).toBe("muse.r.x.wav");
  });

  test("whitespace-only title falls back to muse", () => {
    expect(wavFilename({ title: "   " }, "r.x")).toBe("muse.r.x.wav");
  });

  test("multiple consecutive spaces collapse to one hyphen", () => {
    expect(wavFilename({ title: "A  B   C" }, "r.x")).toBe("A-B-C.r.x.wav");
  });
});
